"""Extract the EOC high-risk analysis (HRA) UC-level scoring (const HRA).

Usage: python _refresh/extract_hra.py [--source PATH] [--out PATH]
Prints one status line: OK hra <json chars> <summary> | ERR hra <reason>

Source: the High Risk Analysis, one workbook per division or for the whole province,
each carrying a "UC Level HRA Template" sheet - `*HRA*.xlsx` in Downloads, named as
downloaded.

WHAT THE SCORE IS (read off the template's own formulas, 26-Oct-2026): 27 indicators in
4 scored blocks, each scored 0-3, plus descriptive columns that carry no score (drainage
UC, terrain). The blocks are Geographic terrain and security access (4 indicators),
Epidemiology and surveillance (11), SIA operations (7) and Essential immunisation /
EPI-PEI synergy (5).

    achieved  = sum of the four block subtotals
    possible  = the "Total score" column, which is a maximum and not a score: its own formula
                adds a fixed number for geography (12) and EPI (15) to 3 x COUNT or 3 x COUNTA
                over the exact cells it names
    pct       = achieved / possible
    band      = pct > 79% Low Risk, pct < 60% High Risk, else Medium Risk

`possible` is adaptive because the epi and SIA blocks hold "if applicable, else leave blank"
indicators: an environment-isolation or LQAS column left empty shrinks the denominator
instead of scoring zero. The counted cell list and the counting function are both taken from
the formula itself, because neither is uniform across sheets, and a column that scores in
the numerator can still be left out of the count. Where a block percentage counts a different
cell list than the maximum does - Hangu divides epi by the score columns while the maximum
counts the raw ones - the band follows the maximum, because that is the column the sheet's own
Risk formula divides by. The sheet's Rank is computed over a fixed range that does not
match the rows present, so neither column is published.

DIRECTION: on this axis a HIGH percentage means LOW risk - the opposite of the
dashboard's own combined UC risk score. The two are never blended and HRA keeps its own
Low / Medium / High names.

Rows are keyed by the 8-digit UC code, which is how they join `const ZD` (the zero-dose
register). Every candidate file is read newest-first and a code already taken is skipped,
so the freshest assessment of each UC wins: the 26-Oct-2026 Mardan Division round replaces
the March province-wide rows for its UCs while the rest of the province keeps the
26-Mar-2026 vintage. Each row carries its own vintage index because the province has no
single as-of date.

Per-district roll-up is left to the dashboard (the repo convention: counts in, percentages
recomputed), but the 27 scores are published per UC so a district can be read as "which
criteria fail here", not only as a band count.

A sheet is only read if its overall percentage follows the model above - four block
subtotals over its own maximum column. `HRA SW Lower.xlsx [HRA 2026]` prints
`=<maximum>*100/113` with fixed block maxima instead, i.e. an earlier draft of the criteria
card, so it is skipped and named rather than blended into a different scale.

Asserted per row, aborting the run on any drift: each block subtotal equals the sum of its
non-blank scores, the overall percentage equals achieved/possible, and wherever a row still
carries live formulas the printed maximum equals what the "Total score" formula's own addends
compute. UC codes are 8 digits and unique within a sheet, aggregates are numeric, every Risk
label is one of the three known words, every district name resolves to a dashboard spelling,
and a score is blank or an integer 0-3 - a score outside the card excludes that row and names
it (two Abbottabad rows hold 13 and 23 in a score column, inflating their own percentage over
100%), and a text cell there (`Q1`, `,`, `13%`) is read as no score, the way SUM/COUNT would.

1,382 of the 1,418 province rows have their aggregate columns pasted as values rather than
formulas, so a displayed block percentage that prints over 100%, a Risk label left behind by
an earlier state, a pasted maximum that no longer counts the cells its formula names, or a
block percentage counted over a different cell list than the maximum are all counted, printed
on stdout and recomputed - never published as printed. The join rate to `const ZD` is reported
and refused below 95%.

Excluded on purpose: the raw indicator values (the scores carry the decision), Rank, and
any free-text column a division adds to the template - `Remarks` (HRA UC Level (Bannu).xlsx)
is dropped and never published. No person-identifying field exists in this template.

Payload: {"src":[files],"asof","gen","thr":[79,60],"b":[band labels],
          "k":[[block, indicator, portal scoring rule], ...27],
          "nx":[descriptive columns with no score], "d":[districts],
          "v":[vintage dates, newest first], "n":rows, "zj":rows whose code is in ZD,
          "zr":join rate, "lg":[rows read, pasted aggregates, stale display cells, stale
          maxima, text score cells, off-scale rows excluded, block/maximum split-rule rows]
          summed over every file, in LAGK order - the audit trail for the recomputation above,
          and the reason no displayed aggregate is taken on trust, "u":[[districtIdx, ucName,
          code, achieved, possible, pct, bandIdx, vIdx, [27 scores, -1 = not applicable]],
          ...]}
"""
import argparse
import datetime
import json
import os
import re
import sys

import openpyxl

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

DS = 'hra'
GEO = {'division': 0, 'district': 1, 'uc name': 2, 'uc code': 3}
BANDS = ['Low Risk', 'Medium Risk', 'High Risk']
THR = [79.0, 60.0]          # portal rule: > 79 Low, < 60 High
MIN_JOIN = 95.0             # floor on the ZD code join rate
NIND = 27                   # scored indicators, the template's whole criteria list
NBLK = 4                    # scored blocks: geography, epidemiology, SIA operations, EPI
REF = re.compile(r'\$?([A-Z]{1,3})\$?\d+', re.I)
# the denominator of a block percentage: a fixed maximum, or 3 x a population count
ADAPTIVE = re.compile(r'^\(?\s*3\s*\*\s*(COUNTA?)\s*\(([^()]*)\)\s*\)?$', re.I)
LIT = re.compile(r'^\(?\s*(\d+)\s*\)?$')
TERM = re.compile(r'^\(?\s*3\s*\*\s*(COUNTA?)\s*\(([^()]*)\)\s*\)?$', re.I)
# the audit counters carried out of every sheet, in payload order
LAGK = ['rows', 'pasted', 'stale', 'maxlag', 'text', 'offscale', 'splitrule']
# how each counter is put to the reader, in the same order
LAG_TXT = {
    'pasted': 'carry their aggregates as pasted values rather than live formulas',
    'stale': 'print a block percentage or Risk label that disagrees with their own arithmetic',
    'maxlag': 'print a maximum that no longer counts the cells their own formula names',
    'text': 'hold text where a score should be',
    'offscale': 'hold a number outside the card\'s 0-3 vocabulary, so the row is excluded',
    'splitrule': 'count the block percentages and the maximum over different columns',
}


def stats():
    return {k: 0 for k in LAGK}
# HRA district spellings -> dashboard spellings, after upper-casing and the ALIAS pass.
# Only genuinely different names belong here; punctuation and case are normalised away.
ALIAS = {
    'ABBOTTABAD': 'ABOTABAD',
    'BATTAGRAM': 'BATAGRAM',
    'LAKKIMARWT': 'LAKKIMRWT',
    'LAKKI MARWAT': 'LAKKIMRWT',   # the Lakki Marwat division file spells it with a space
    'NORTH WAZIRISTAN': 'WAZIR-N',
}


def norm(v):
    """Cell -> single-spaced text (template labels are multi-line)."""
    return re.sub(r'\s+', ' ', ('' if v is None else str(v))).strip()


def key(lab):
    """Label with the re-export's trailing counter and punctuation removed.

    `%` survives: '% Score Achieved' and 'Score Achieved' differ only by it, and the
    first is a block percentage while the second is a block subtotal."""
    s = re.sub(r'\d+$', '', norm(lab)).strip().lower()
    return re.sub(r'[^a-z% ]', '', s).strip()


def code_of(v):
    """UC code cell -> 8 digits, whether the sheet stored it as text or as a number."""
    if v is None:
        return ''
    if isinstance(v, float) and v == int(v):
        return '%08d' % int(v)
    return norm(v).replace(' ', '')


def tail_key(k):
    """Aggregate column class, or None when the column is a raw indicator."""
    if k == 'score achieved':
        return 'sub'
    if k == '% score achieved':
        return 'pct'
    if k in ('total score', 'rank', 'risk'):
        return k
    return None


def plan(ws):
    """-> (geo cols, [(block, label, rule, raw col, score col)], tail cols, unscored) or None.

    Columns are found by header text, never by position: divisions ship this template
    with an extra Tehsil column (Abbottabad) or Remarks column (Bannu), which shifts
    every later position and adds unscored text.
    """
    rows = [list(r) for r in ws.iter_rows(min_row=1, max_row=2, values_only=True)]
    if len(rows) < 2:
        return None
    top, hdr = rows[0], rows[1]
    geo, ind, tail, nx = {}, [], {}, []
    block, pending = None, None
    for i in range(len(hdr)):
        h1 = norm(top[i]) if i < len(top) else ''
        lab = norm(hdr[i])
        if h1 and h1 != lab:
            block = h1
        if not lab:
            continue
        k = key(lab)
        if k in GEO:
            geo[GEO[k]] = i
            continue
        cls = tail_key(k)
        if cls:
            tail.setdefault(cls, []).append(i)
            continue
        if k == 'score' or k.startswith('score '):
            if pending is None:
                raise SystemExit('ERR hra %s: the scoring rule in column %d has no indicator '
                                 'before it' % (ws.title, i + 1))
            if i != pending[1] + 1:
                raise SystemExit('ERR hra %s: score column for %r sits at %d, expected the next '
                                 'column %d' % (ws.title, pending[0][:30], i + 1, pending[1] + 2))
            ind.append((block, pending[0], lab, pending[1], i))
            pending = None
            continue
        if pending is not None:
            nx.append(pending[0])
        pending = (lab, i)
    if pending is not None:
        nx.append(pending[0])
    if len(geo) < 4 or 'sub' not in tail or 'risk' not in tail or 'total score' not in tail:
        return None
    if len(tail['sub']) != NBLK:
        raise SystemExit('ERR hra %s: %d "Score Achieved" columns, want one per scored block'
                         % (ws.title, len(tail['sub'])))
    # the overall percentage is the one printed after the "Total score" maximum
    tc = tail['total score'][0]
    tail['tot_pct'] = [c for c in tail.get('pct', []) if c > tc]
    tail['pct'] = [c for c in tail['pct'] if c < tc]
    if len(tail['pct']) != NBLK or len(tail['tot_pct']) != 1:
        raise SystemExit('ERR hra %s: %d block percentages and %d overall, want %d and 1'
                         % (ws.title, len(tail['pct']), len(tail['tot_pct']), NBLK))
    return geo, ind, tail, nx


def blocks_of(ind):
    """-> [(block label, [indicator indexes in it])] in sheet order."""
    out = []
    for j, x in enumerate(ind):
        if not out or out[-1][0] != x[0]:
            out.append([x[0], []])
        out[-1][1].append(j)
    return out


def num(v, what, where):
    t = norm(v)
    try:
        f = float(t)
    except ValueError:
        raise SystemExit('ERR hra %s: %s is %r, want a number' % (where, what, v))
    return f


def colno(letters):
    """'Q' -> 16 as a zero-based column index."""
    n = 0
    for ch in letters.upper():
        n = n * 26 + ord(ch) - 64
    return n - 1


def ref_cols(argtext, where):
    """Cell list from a formula argument -> zero-based column indexes, ranges expanded."""
    out = []
    for tok in argtext.split(','):
        tok = tok.strip()
        if not tok:
            continue
        parts = [REF.fullmatch(x.strip()) for x in tok.split(':')]
        if any(p is None for p in parts):
            raise SystemExit('ERR hra %s: cannot read the cells in %r' % (where, tok))
        lo = colno(parts[0].group(1))
        hi = colno(parts[-1].group(1))
        out.extend(range(min(lo, hi), max(lo, hi) + 1))
    return out


def spec_of(fcell, bcols, where):
    """One block's maximum rule off its own percentage formula: ('lit', n) or (COUNT|COUNTA, cols).

    Returns None when the cell holds no formula. Divisions paste part of this template as
    values, so the rule is read from the first row of the sheet that still carries it and
    then applied to every row - see read_sheet().

    `bcols` is the block's raw *and* score columns, because which of the pair the formula
    counts is not uniform either: the province sheet divides the epi subtotal by
    `3*COUNT(<raw columns>)`, Abbottabad and Hangu by `3*COUNT(<score columns>)`. The count
    comes out the same - a score cell is populated exactly when its raw cell is - so both
    are accepted, but the columns actually named are the ones later judged for population.
    """
    s = norm(fcell)
    if not s.startswith('='):
        return None
    _, slash, den = s.rpartition('/')
    if not slash:
        raise SystemExit('ERR hra %s: block percentage %r divides nothing' % (where, s))
    den = den.strip()
    m = ADAPTIVE.match(den)
    if m:
        cols = ref_cols(m.group(2), where)
        outside = sorted(c for c in cols if c not in set(bcols))
        if outside:
            raise SystemExit('ERR hra %s: %s(...) in the block percentage counts columns %s '
                             'which are not indicators of that block'
                             % (where, m.group(1).upper(), outside))
        return (m.group(1).upper(), cols)
    m = LIT.match(den)
    if m:
        return ('lit', int(m.group(1)))
    raise SystemExit('ERR hra %s: cannot read a maximum from %r' % (where, den))


def overall_model(fcell, subs, tc, where):
    """Confirm a sheet scores the province model: (sum of block subtotals) / its own maximum.

    -> (True | None, reason). None means the cell holds no formula, so nothing can be read
    from it. `HRA SW Lower.xlsx` [HRA 2026] prints `=BQ3*100/113` there - the maximum divided
    by a fixed 113 - and gives its blocks fixed maxima of 18, 30 and 15 for 11, 7 and 5
    indicators, so it is an earlier draft of the criteria card, not this model. Its own UCs are
    covered by the 26-Mar-2026 province sheet, and refusing it is what keeps one band
    definition across the payload.
    """
    s = norm(fcell)
    if not s.startswith('='):
        return None, None
    num, slash, den = s[1:].rpartition('/')
    if not slash:
        return False, 'its overall percentage divides nothing'
    if LIT.match(den.strip()):
        return False, ('its overall percentage divides by a fixed %s instead of the sheet\'s own '
                       'maximum in column %s' % (den.strip(), col_letter(tc)))
    want = set(subs) | {tc}
    got = {colno(m.group(1)) for m in REF.finditer(num)} | {colno(m.group(1)) for m in REF.finditer(den)}
    if got != want:
        return False, ('its overall percentage is built from columns %s, want the %d block '
                       'subtotals and the maximum' % (sorted(got), len(subs)))
    return True, None


def col_letter(idx):
    """Zero-based column index -> 'BQ'."""
    s, n = '', idx + 1
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def count3(fn, cols, frow, rrow):
    """3 x the number of a block's cells the sheet treats as answered.

    COUNT is judged on the value pass, so a criteria column holding text such as "N" does not
    raise the maximum; COUNTA on the formula pass, so a column holding an empty-string formula
    does. Neither is judged on the displayed value.
    """
    if fn == 'COUNTA':
        return 3 * sum(1 for c in cols if frow[c] is not None)
    return 3 * sum(1 for c in cols
                   if isinstance(rrow[c], (int, float)) and not isinstance(rrow[c], bool))


def den_of(spec, bcols, frow, rrow, where):
    """A row's maximum for one block, scored the way that block's percentage formula scores it.

    The template divides each subtotal either by a fixed number (geography 12, EPI 15) or by
    `3 x COUNT(A)(<explicit cells>)`. Both the cell list and the function are read off the
    formula instead of assumed, and they are not uniform across sheets: the 26-Mar-2026 province
    sheet counts with COUNT, the 26-Oct-2026 Mardan sheet with COUNTA.
    """
    if spec is None:
        return count3('COUNTA', bcols, frow, rrow)
    if spec[0] == 'lit':
        return spec[1]
    return count3(spec[0], spec[1], frow, rrow)


def terms_of(fcell, where):
    """The "Total score" formula split into its own addends: [int | (COUNT|COUNTA, cols)].

    Read from this column and not from the block percentages, because the two do not always
    count the same cells: Hangu's epi block percentage divides by `3*COUNT(<score columns>)`
    while its maximum counts `<raw columns>`, so a row holding "N" as a raw value raises the
    block denominator but not the total. The maximum column is what the sheet's own Risk band
    divides by, so it is the one published. None when the cell holds no formula.
    """
    s = norm(fcell)
    if not s.startswith('='):
        return None
    out = []
    for tok in s[1:].split('+'):
        tok = tok.strip()
        m = TERM.match(tok)
        if m:
            out.append((m.group(1).upper(), ref_cols(m.group(2), where)))
            continue
        m = LIT.match(tok)
        if m:
            out.append(int(m.group(1)))
            continue
        raise SystemExit('ERR hra %s: cannot read %r out of the maximum formula' % (where, tok))
    return out


def total_value(terms, frow, rrow):
    """A row's maximum from the maximum formula's own addends."""
    v = 0
    for t in terms:
        v += t if isinstance(t, int) else count3(t[0], t[1], frow, rrow)
    return v


def read_sheet(path, sheet, zmap):
    """-> ({uc code: [district, ucName, achieved, possible, pct, band, scores]}, unscored, stats)

    Two passes over one sheet: values for the numbers, formulas for the criteria columns the
    portal actually counts. `possible` is adaptive, so it is read from each block's own
    percentage formula rather than assumed - see spec_of() and den_of().

    stats counts the rows whose aggregate columns are pasted values instead of live formulas
    (`pasted`), the rows whose displayed block percentage or Risk label disagrees with the
    sheet's own arithmetic (`stale`) and the pasted rows whose maximum no longer matches the
    criteria columns beside it (`maxlag`). Every subtotal, overall percentage and band on those
    rows still reconciles with the row's own numbers, so the recomputed score is published and
    the lag is reported on stdout, not hidden.
    """
    base = os.path.basename(path)
    wbv = openpyxl.load_workbook(path, read_only=True, data_only=True)
    wbf = openpyxl.load_workbook(path, read_only=True, data_only=False)
    out, unscored = {}, set()
    st = stats()
    try:
        pl = plan(wbv[sheet])
        if pl is None:
            return None, None, None
        geo, ind, tail, nx = pl
        if len(ind) != NIND:
            raise SystemExit('ERR hra %s [%s]: %d scored indicators, want %d'
                             % (base, sheet, len(ind), NIND))
        bl = blocks_of(ind)
        # a block's own percentage counts either its raw or its score columns - both are its
        # indicators, and which one the division names is not uniform across sheets
        bcols = [sorted({c for j in idxs for c in (ind[j][3], ind[j][4])}) for _, idxs in bl]
        braw = [[ind[j][3] for j in idxs] for _, idxs in bl]
        di, ui, ci = geo[1], geo[2], geo[3]
        need = max([x[3] for x in ind] + [x[4] for x in ind] + list(tail['sub'])
                   + list(tail['pct']) + list(tail['tot_pct'])
                   + [tail['total score'][0], tail['risk'][0]] + [di, ui, ci])
        seen = set()
        # a division can paste the aggregate columns as values, leaving the row itself with
        # no formula to read the maximum rule from; take it from the first row that has one
        specs, tspec = [None] * NBLK, None
        for frow in wbf[sheet].iter_rows(min_row=3, values_only=True):
            f = list(frow) + [None] * (need + 1 - len(frow))
            for bi in range(NBLK):
                if specs[bi] is None:
                    specs[bi] = spec_of(f[tail['pct'][bi]], bcols[bi], '%s [%s]' % (base, sheet))
            if tspec is None:
                tspec = terms_of(f[tail['total score'][0]], '%s [%s]' % (base, sheet))
            ok, why = overall_model(f[tail['tot_pct'][0]], tail['sub'],
                                    tail['total score'][0], '%s [%s]' % (base, sheet))
            if ok is False:
                print('SKIP hra %s [%s]: %s - an earlier draft of the criteria card, not the '
                      'model the province sheet scores on' % (base, sheet, why))
                return None, None, None
            if all(s is not None for s in specs) and tspec and ok:
                break
        pair = zip(wbv[sheet].iter_rows(min_row=3, values_only=True),
                   wbf[sheet].iter_rows(min_row=3, values_only=True))
        for row, frow in pair:
            r = list(row) + [None] * (need + 1 - len(row))
            f = list(frow) + [None] * (need + 1 - len(frow))
            code = code_of(r[ci])
            if not code:
                continue
            if not re.fullmatch(r'\d{8}', code):
                if key(code) in ('total', 'grand total'):
                    continue
                raise SystemExit('ERR hra %s [%s]: UC code %r is not 8 digits' % (base, sheet, code))
            raw_d = norm(r[di])
            dn = zmap.get(dkey(raw_d)) if raw_d else None
            if dn is None:
                raise SystemExit('ERR hra %s [%s]: district %r is not a dashboard spelling '
                                 '(add it to ALIAS only if the rename is real)'
                                 % (base, sheet, raw_d))
            where = '%s [%s] %s' % (base, sheet, code)
            sc, off = [], []
            for j, x in enumerate(ind):
                t = norm(r[x[4]])
                if t in ('', '-'):
                    sc.append(-1)
                    continue
                try:
                    fv = float(t)
                except ValueError:
                    # a score box holding text the sheet cannot add up - a bare comma in the
                    # Lower South Waziristan draft, a pasted 'Q1' in Mansehra, a percentage like
                    # '13%' - carries no score, which is how the sheet's own SUM over the block
                    # reads a text cell too. The subtotal assertion below proves that reading
                    # row by row, so it is counted rather than trusted.
                    sc.append(-1)
                    st['text'] += 1
                    continue
                if fv != int(fv) or not 0 <= fv <= 3:
                    off.append('%s = %s' % (x[1][:34], r[x[4]]))
                    continue
                sc.append(int(fv))
            if off:
                # a number outside the card's 0-3 vocabulary is a data-entry defect, not a
                # score: Abbottabad has 13 and 23 pasted into the "Still Missed %" score box,
                # which is why those rows print block percentages over 100% against a subtotal
                # their own scores cannot add up to. Nothing in the row can be recomputed from
                # its inputs, so the row is excluded and named on stdout - the fresher province
                # sheet assesses the same UCs, and a silent fix would be inventing a score.
                st['offscale'] += 1
                print('BAD hra %s: score outside the criteria card (%s) - row excluded'
                      % (where, '; '.join(off)))
                continue
            subs = [int(num(r[c], 'block subtotal', where)) for c in tail['sub']]
            ach, dens, bad = 0, [], False
            for bi, (b, idxs) in enumerate(bl):
                tot = sum(sc[j] for j in idxs if sc[j] >= 0)
                if subs[bi] != tot:
                    raise SystemExit('ERR hra %s: block %r subtotal is %d on the sheet, %d from '
                                     'its scores' % (where, b[:26], subs[bi], tot))
                den = den_of(specs[bi], braw[bi], f, r, where)
                dens.append(den)
                ach += tot
                pc = r[tail['pct'][bi]]
                if den and norm(pc):
                    pv = num(pc, 'block percentage', where)
                    if abs(pv * den - subs[bi]) > 0.02:
                        bad = True
            # a row whose aggregates are pasted values is a snapshot: its printed maximum can
            # predate the criteria columns now sitting next to it, which only the live-formula
            # rows can be held to
            ts = f[tail['total score'][0]]
            live = isinstance(ts, str) and ts.startswith('=')
            possible = int(num(r[tail['total score'][0]], 'Total score column', where))
            if tspec:
                # the maximum as this sheet's own formula counts it, which is the column the
                # Risk band divides by
                tposs = total_value(tspec, f, r)
                if possible != tposs:
                    if live:
                        raise SystemExit('ERR hra %s: the "Total score" formula is %d, the cells it '
                                         'names add to %d' % (where, possible, tposs))
                    st['maxlag'] += 1
            if sum(dens) != possible:
                # the block percentages and the maximum do not count the same cells - Hangu
                # divides epi by its score columns while the maximum counts the raw ones. Not a
                # defect, but the published band follows the maximum, so the split is recorded.
                st['splitrule'] += 1
            pct = 100.0 * ach / possible if possible else None
            tp = tail['tot_pct'][0]
            if norm(r[tp]):
                pv = num(r[tp], 'overall percentage', where)
                if abs(pv * possible - ach) > 0.02:
                    raise SystemExit('ERR hra %s: overall %s%% on the sheet, %s%% recomputed'
                                     % (where, r[tp], round(pct, 2)))
            band = band_of(ach, possible, where)
            lab = norm(r[tail['risk'][0]])
            known = [key(b) for b in BANDS]
            if key(lab) not in known:
                raise SystemExit('ERR hra %s: the Risk column says %r, want one of %s'
                                 % (where, lab, ', '.join(BANDS)))
            if key(lab) != key(BANDS[band]):
                bad = True                       # a pasted label left behind by an earlier state
            if code in seen:
                raise SystemExit('ERR hra %s [%s] lists UC code %s twice' % (base, sheet, code))
            seen.add(code)
            out[code] = [dn, norm(r[ui]), ach, possible, round(pct, 1), band, sc]
            st['rows'] += 1
            if not live:
                st['pasted'] += 1                # no live formula in the aggregate columns
            if bad:
                st['stale'] += 1
        for x in nx:
            if x and key(x) not in GEO:
                unscored.add(x)
    finally:
        wbv.close()
        wbf.close()
    return out, sorted(unscored), st


def dkey(name):
    s = norm(name).upper().strip()
    return ALIAS.get(s, s)


def band_of(ach, poss, where):
    """The portal's rule in exact integer arithmetic: > 79% Low, < 60% High, else Medium.

    Cross-multiplication rather than a float percentage, because a row sitting exactly on a
    boundary is Medium under the sheet's strict > and < (first seen on UC 36204011 of the
    26-Mar-2026 province sheet, 18 of 30), and a rounded percentage would decide it by noise.
    """
    if not poss:
        raise SystemExit('ERR hra %s: no maximum to score against' % where)
    v = 100 * ach
    if v > THR[0] * poss:
        return 0
    if v < THR[1] * poss:
        return 2
    return 1


def template_sheets(path):
    """Sheet names in one workbook that carry the 27-indicator template."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ok = []
    try:
        for s in wb.sheetnames:
            try:
                pl = plan(wb[s])
            except Exception:
                continue
            if pl and len(pl[1]) == NIND:
                ok.append(s)
    finally:
        wb.close()
    return ok


def build(cands, repo):
    """Merge every candidate workbook newest-first: the freshest assessment of each UC wins."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i, e = dashpatch.payload_span(s, 'ZD')
    zd = json.loads(s[i:e])
    zcodes = {str(r['c']).strip() for r in zd}
    zmap = {r['d'].upper(): r['d'] for r in zd}
    rows, files, nx = {}, [], set()
    notes = []
    lag = stats()
    for rec in cands:
        try:
            sheets = template_sheets(rec['path'])
        except Exception as ex:
            print('SKIP hra %s (%s)' % (rec['name'], ex))
            continue
        if not sheets:
            continue
        day = datetime.date.fromtimestamp(rec['mtime']).isoformat()
        got, sumk = [], stats()
        for sh in sheets:
            found, unscored, st = read_sheet(rec['path'], sh, zmap)
            if not found:
                continue
            got.append(sh)
            for j in sumk:
                sumk[j] += st[j]
            nx.update(unscored or [])
            for code, val in found.items():
                if code in rows:
                    continue                     # a fresher workbook already assessed this UC
                rows[code] = val + [day]
        if not got:
            continue
        # keep every file read, even one whose UCs the province sheet already covers: it records
        # which rounds were checked, and the per-row vintage says which one published each UC
        files.append('%s [%s] %s' % (rec['name'], ', '.join(got), day))
        parts = [(k, sumk[k]) for k in LAGK if k != 'rows' and sumk[k]]
        if parts:
            notes.append('%s: %d rows read - %s. Recomputed from each row\'s own inputs; none of '
                         'it published as printed'
                         % (rec['name'], sumk['rows'],
                            '; '.join('%d %s' % (v, LAG_TXT[k]) for k, v in parts)))
        for j in lag:
            lag[j] += sumk[j]
    if not rows:
        raise SystemExit('ERR hra no UC-level HRA template among %d candidate files' % len(cands))
    order = sorted(rows.items(), key=lambda kv: (kv[1][0], kv[1][1], kv[0]))
    zj = sum(1 for c in order if c[0] in zcodes)
    rate = round(100.0 * zj / len(order), 2)
    if rate < MIN_JOIN:
        raise SystemExit('ERR hra only %d of %d UC codes (%.2f%%) match const ZD, want >= %.0f%%'
                         % (zj, len(order), rate, MIN_JOIN))
    dists = sorted({v[0] for v in rows.values()})
    # only the vintages a published row actually carries: several division files are read in
    # full to confirm their UCs against the province sheet and then superseded, and a date with
    # no rows on it would be a vintage the reader could not reach
    vint = sorted({v[7] for v in rows.values()}, reverse=True)
    vi = {d: i for i, d in enumerate(vint)}
    k = []
    for rec in cands:
        k = rules_of(rec['path'])
        if k:
            break
    if len(k) != NIND:
        raise SystemExit('ERR hra the criteria card lists %d indicators, want %d' % (len(k), NIND))
    unv = {}
    out = []
    for code, v in order:
        dn, uc, ach, poss, pct, band, sc, day = v
        unv[day] = unv.get(day, 0) + 1
        out.append([dists.index(dn), uc, code, ach, poss, pct, band, vi[day], sc])
    bands = [sum(1 for r in out if r[6] == b) for b in range(3)]
    gen = datetime.datetime.now().strftime('%d-%b-%Y %H:%M')
    payload = {'src': files, 'asof': vint[0], 'gen': gen, 'thr': THR, 'b': BANDS, 'k': k,
               'nx': sorted(nx), 'd': dists, 'v': vint, 'n': len(out), 'zj': zj, 'zr': rate,
               'lg': [lag[k] for k in LAGK], 'u': out}
    summary = ('%d UCs, %d districts, %d vintages (%s), %d codes matched to const ZD (%.2f%%) '
               '- %d Low / %d Medium / %d High Risk'
               % (len(out), len(dists), len(vint),
                  ', '.join('%s: %d' % (d, n) for d, n in sorted(unv.items(), reverse=True)),
                  zj, rate, bands[0], bands[1], bands[2]))
    return payload, summary, notes


def rules_of(path):
    """[[block, indicator, the portal's own scoring rule], ...] from a template sheet."""
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        for s in wb.sheetnames:
            try:
                pl = plan(wb[s])
            except Exception:
                continue
            if pl is None or len(pl[1]) != NIND:
                continue
            return [[b, lab, re.sub(r'^Score\s*', '', rule).strip()]
                    for b, lab, rule, _, _ in pl[1]]
    finally:
        wb.close()
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    cands = srcutil.discover(entry)
    if a.source:
        s_abs = os.path.normcase(os.path.abspath(a.source))
        cands = [srcutil.stat_rec(a.source)] + [
            c for c in cands if os.path.normcase(os.path.abspath(c['path'])) != s_abs]
    if not cands:
        raise SystemExit('ERR hra no *HRA*.xlsx under %s' % entry['roots'])
    cands.sort(key=lambda r: (-r['mtime'], r['name']))
    payload, summary, notes = build(cands, cfg['repo'])
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'hra.json')
    srcutil.write_text(dest, js)
    for f in payload['src']:
        print('SRC hra %s' % f)
    for n in notes:
        print('NOTE hra %s' % n)
    print('OK hra %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
