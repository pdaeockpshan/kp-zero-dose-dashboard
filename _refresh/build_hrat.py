# -*- coding: utf-8 -*-
"""Build the online HRA compilation template spec (const HRAT).

Usage: python _refresh/build_hrat.py [--template PATH] [--formulas PATH] [--out PATH]
Prints: SRC hrat <slot> <path> | NOTE hrat <what> | OK hrat <chars> <summary> | ERR hrat <reason>

WHAT THIS IS. The owner keeps `HRA UC LEVEL TEMPLATE.xlsx` (D:\\AMAZON DATA\\HRA TEMPLATE) and
compiles it after every campaign: 72 columns A..BT, five blocks with the block title merged across
row 1, each indicator with its scoring rule printed inside its own row-2 header, and one UC per row
from row 3. Staff fill the raw columns; the score, subtotal, percentage, maximum, rank and Risk
columns compute from formulas. This builder turns that file into a payload so the dashboard can put
the same sheet on screen and hand it back as a workbook. The column order is read from the template
and nothing here re-sequences a column.

THE TWO SOURCES, AND WHY BOTH ARE NAMED.
  * the template file gives the order, the block spans, the header text, the printed rules and the
    number formats. It carries no formulas at all - it is a blank sheet.
  * a filled workbook gives the formulas. Most cannot supply them: the 26-Oct-2026 Mardan round
    arrives with its eleven epidemiology score columns pasted as values. So every other candidate is
    probed for how many of the 39 formula-bearing columns it actually holds in its first rows, the
    count per file is printed, and the builder aborts unless one file covers all 39. The 26-Mar-2026
    province sheet is the one that does.

WHAT THE PAYLOAD CARRIES. Per column: letter, header text verbatim, block index, input kind (code,
count, rate, percent, yes/no, a named vocabulary, or computed), the workbook's number format, and
for computed columns the formula text. `hrat_eval.js` evaluates those formulas on screen and the
export writes the same strings back, so the page and the file cannot drift apart. Formulas are read
off row 3 of the source sheet and its literal row number becomes `{r}`, so one text serves any row.

DEVIATIONS, EACH RECORDED IN `warn` AND NAMED ON THE PAGE RATHER THAN SILENT:
  * `IF(AI3>=10,3,0)` - the NPEV isolation rate is a percent column and its workbook rule compares it
    with a bare 10, so a UC entered the way the format displays it (0.1667) can never reach the
    threshold and only one typed as 16.67 scores. The printed rule beside the column says >10%, so
    the threshold is read as a percentage and the rewrite is reported. No other rule compares a
    percent column with a bare number. Measured on the compiled rows: of the pasted marks that tell
    the two readings apart, the September division follows the printed rule on every single one
    (59 of 59), and in the province sheet the marks that follow the bare 10 are the ones that came
    out of that formula itself (107 rows scoring a 100% isolation rate as 0).
  * `3*COUNT(...)` in the two block percentages and the total maximum charges nothing for a cell
    holding text, so a Y/N answer (the silent-UC indicator) or a hand-typed `38%` scores a mark but
    drops out of the denominator - the row is graded over three marks fewer than the card it filled
    in and its percentage comes out high. A sheet still being compiled counts the same cells with
    COUNTA, which charges every filled cell and is what "three marks per indicator" means, so COUNT
    is rewritten to COUNTA where the two texts are otherwise identical and the file that says so is
    named.
  * the rank is anchored to `$BR$3:$BR$38` whatever the sheet's length, which is why that file's own
    Rank column prints #N/A from row 39 down; a later division's copy anchors to its own row count.
    Neither anchors to the rows actually compiled. The payload stores the ranked column, the
    direction and the anchor it read; the grid ranks the rows loaded and the export writes the range
    over the rows it writes.
  * Excel reads a blank cell as 0, so an unanswered indicator whose rule is `IF(<raw>=0,3,0)` pays
    the best mark of 3 while COUNT on that same blank cell shrinks the block maximum. The count of
    marks the province sheet earned this way is measured, not argued: it is in the payload as `blank`
    and named on the page. The grid evaluates the formula exactly as Excel does, because the page,
    the file it hands back and the divisions' own workbooks have to agree; what it adds is that count
    per row, so a mark earned from an empty cell is visible instead of silent. The three
    if-applicable columns are already guarded with ISBLANK in the workbook and stay blank on both
    sides.
"""
import argparse
import datetime
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch  # noqa: E402
import srcutil  # noqa: E402
from openpyxl import load_workbook  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

DS = 'hrat'
SHEET_HINT = 'UC Level HRA Template'
ROW0 = 3                       # the row the formulas are read from
NIND = 27                      # indicators on the criteria card
NFORMULA = NIND + 4 + 4 + 4    # scores, block subtotals, block percentages, tail aggregate columns
RANGE = re.compile(r'\$?([A-Z]{1,3})\$?(?:\d+|\{r\}):\$?([A-Z]{1,3})\$?(?:\d+|\{r\})')
CELLREF = re.compile(r'\$?([A-Z]{1,3})\$?(?:\d+|\{r\})')
REF = re.compile(r'(\$?)([A-Z]{1,3})(\$?)(\d+)')

# The vocabulary each input box offers, keyed by column letter. The order and the rules are read
# from the files; only what a cell may contain is declared here, and it is then checked against the
# values the divisions really typed (a value outside it is printed, never dropped).
# E and AK are answered Y/N; M and BM are answered Yes/No - the card's own formulas test the word
# `"Yes"` on the last two, so their pickers must offer the word or every bordering UC scores safe.
# F is free text: its heading names three terrain types, no formula reads the cell, and the divisions
# answer it in their own words (Charsadda writes Yes/No down all 131 rows, Mardan writes Plain).
KIND = {
    'A': 'text', 'B': 'text', 'C': 'text', 'D': 'code', 'E': 'yn',
    'F': 'text', 'G': 'gcat', 'I': 'access', 'K': 'pct', 'M': 'yesno',
    'Q': 'cnt', 'S': 'cnt', 'U': 'cnt', 'W': 'cnt', 'Y': 'cnt', 'AA': 'pct',
    'AC': 'cnt', 'AE': 'rate', 'AG': 'pct', 'AI': 'pct', 'AK': 'yn',
    'AO': 'pct', 'AQ': 'cnt', 'AS': 'pct', 'AU': 'pct', 'AW': 'pct', 'AY': 'pct', 'BA': 'pct',
    'BE': 'cat', 'BG': 'pct', 'BI': 'pct', 'BK': 'pct', 'BM': 'yesno',
}
# indicators the card leaves blank when they do not apply - the grid must not force a number
OPTIONAL = {'AC', 'AO', 'AW'}
LISTS = {
    'yn': ['Y', 'N'],
    'yesno': ['Yes', 'No'],
    # The heading names three categories, but the province sheet writes G1/G2 and G2/G3 on two rows and
    # its own IF already grades both 1, so the picker offers the five the divisions actually type.
    'gcat': ['G1', 'G2', 'G3', 'G1/G2', 'G2/G3'],
    'access': ['Green', 'COMVI', 'Red', 'Black'],
    'cat': ['1', '2', '3', '4'],
}
ALIAS = {'No': 'N', 'NO': 'N', 'no': 'N', 'Yes': 'Y', 'YES': 'Y', 'yes': 'Y'}


def norm(v):
    if v is None:
        return ''
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return ' '.join(str(v).split())


def ci(letter):
    """'BT' -> 71 as a zero-based column index."""
    n = 0
    for ch in letter:
        n = n * 26 + ord(ch) - 64
    return n - 1


def clean(f):
    """Formula text: whitespace collapsed, `_xlfn.` dropped, the read row replaced by {r}.

    Only a relative row moves. `$BR$3:$BR$38` stays anchored because that is the defect the rank
    warning is about, and a quoted literal stays untouched because `"G3"` is a category name on this
    card, not a cell.
    """
    if not isinstance(f, str) or not f.startswith('='):
        return None
    s = ' '.join(f[1:].split()).replace('_xlfn.', '')
    out, i = [], 0
    while i < len(s):
        if s[i] == '"':
            j = s.find('"', i + 1)
            j = len(s) if j < 0 else j + 1
            out.append(s[i:j])
            i = j
            continue
        m = REF.match(s, i)
        if m:
            anchor, col, rowabs, row = m.groups()
            if rowabs or row != str(ROW0):
                out.append(m.group(0))
            else:
                out.append('%s%s%s' % (anchor, col, '{r}'))
            i = m.end()
            continue
        out.append(s[i])
        i += 1
    return ''.join(out)


def cells(formula):
    """Single-cell references -> column letters, ignoring the ends of any range."""
    s = RANGE.sub('RANGE', formula)
    return [m.group(1) for m in re.finditer(r'\$?([A-Z]{1,3})\$?\{r\}', s)]


def check_shape(f, where):
    """A formula is only usable if every reference sits on the row being computed.

    RANK is the one exception this sheet makes - a range over a single column - and exactly that is
    what the evaluator supports. Anything wider, or any fixed-row single cell, aborts the build.
    """
    body = RANGE.sub('RANGE', f)
    for tok in re.findall(r'[A-Z]{1,3}\$\d+', body):
        raise SystemExit('ERR hrat %s: %r is anchored to a fixed row, which the evaluator cannot '
                         'apply to another row' % (where, tok))
    for m in RANGE.finditer(f):
        if m.group(1) != m.group(2):
            raise SystemExit('ERR hrat %s: the range %s spans two columns'
                             % (where, m.group(0)))
    return True


def read_head(ws):
    n = ws.max_column
    return n, [norm(ws.cell(2, c).value) for c in range(1, n + 1)]


def group_spans(ws, n):
    """[(first letter, last letter, block title)] in sheet order, off row 1's merged cells.

    Five blocks carry a merged title across row 1. The four aggregate columns at the tail do not -
    each of them is a column of its own, with its label on row 2 - so they are kept as single-column
    spans rather than folded into the block before them, which is what preserves the order.
    """
    out = []
    for r in ws.merged_cells.ranges:
        if r.min_row == 1 and r.max_row == 1:
            out.append((get_column_letter(r.min_col), get_column_letter(r.max_col),
                        norm(ws.cell(1, r.min_col).value)))
    out.sort(key=lambda x: ci(x[0]))
    covered = set()
    for a, b, _ in out:
        covered.update(range(ci(a), ci(b) + 1))
    loose = [i for i in range(n) if i not in covered]
    if loose:
        out.extend((get_column_letter(i + 1), get_column_letter(i + 1),
                    norm(ws.cell(1, i + 1).value)) for i in loose)
        out.sort(key=lambda x: ci(x[0]))
        print('NOTE hrat columns %s carry no row-1 block title - kept as their own spans, in place'
              % ', '.join(get_column_letter(i + 1) for i in loose))
    return out


def block_of(spans, letter):
    i = ci(letter)
    for k, (a, b, _) in enumerate(spans):
        if ci(a) <= i <= ci(b):
            return k
    raise SystemExit('ERR hrat: %s falls outside every block' % letter)


def classify(headers, spans):
    """Split the 72 columns into the 27 scores, the four block pairs and the four tail columns.

    The four subtotal columns are headed "Score Achieved" and the five percentage columns
    "% Score Achieved", so those two exact labels are matched before the indicator rule, which reads
    any header starting with "Score" followed by the printed 0-3 vocabulary.
    """
    score, sub, pct, tail = [], [], [], {}
    for i, h in enumerate(headers):
        L = get_column_letter(i + 1)
        hl = h.lower()
        if hl == 'score achieved':
            sub.append(L)
        elif hl == '% score achieved':
            pct.append(L)
        elif hl == 'total score':
            tail['max'] = L
        elif hl == 'rank':
            tail['rank'] = L
        elif hl == 'risk':
            tail['risk'] = L
        elif hl.startswith('score ') or hl.startswith('score\n'):
            score.append(L)
    if len(score) != NIND:
        raise SystemExit('ERR hrat: %d indicator-score columns, want the %d of the card: %s'
                         % (len(score), NIND, ', '.join('%s %r' % (L, headers[ci(L)][:26])
                                                        for L in score[:31])))
    if len(sub) != 4:
        raise SystemExit('ERR hrat: %d Score Achieved columns, want one per scored block (%s)'
                         % (len(sub), ', '.join(sub)))
    if len(pct) != 5:
        raise SystemExit('ERR hrat: %d %% Score Achieved columns, want four block percentages plus '
                         'the overall (%s)' % (len(pct), ', '.join(pct)))
    if sorted(tail) != ['max', 'rank', 'risk']:
        raise SystemExit('ERR hrat: tail columns read as %s, want Total score, Rank and Risk'
                         % sorted(tail))
    # the overall percentage is the one column sitting right after the maximum
    overall = get_column_letter(ci(tail['max']) + 2)
    if overall not in pct:
        raise SystemExit('ERR hrat: %s, the column after Total score, is not a percentage column'
                         % overall)
    return score, sub, [p for p in pct if p != overall], overall, tail


def formulas_of(ws, want, where):
    """First live formula per computed column, scanning the rows below the header."""
    got = {}
    for r in range(ROW0, min(ws.max_row, ROW0 + 60) + 1):
        for L in want:
            if L in got:
                continue
            c = ci(L) + 1
            if c > ws.max_column:
                continue
            s = clean(ws.cell(r, c).value)
            if s and '{r}' in s:
                got[L] = s
        if len(got) == len(want):
            break
    miss = sorted(set(want) - set(got))
    if miss:
        raise SystemExit('ERR hrat: %s holds no formula in %s - the rules cannot be read from it'
                         % (where, ', '.join(miss)))
    return got


def probe(ws, want):
    """How many of the computed columns carry at least one live formula in the first rows."""
    have = set()
    for r in range(ROW0, min(ws.max_row, ROW0 + 60) + 1):
        for L in want:
            if L in have:
                continue
            i = ci(L) + 1
            if i <= ws.max_column and clean(ws.cell(r, i).value):
                have.add(L)
        if len(have) == len(want):
            break
    return have


def answered_cells(ws):
    """Non-empty cells in the answer columns, row 3 down.

    A blank card exported from this dashboard carries the whole roster and all 39 formulas, but nobody
    has typed an answer: its blanks describe an empty sheet, not a division's round, and reading the
    formula source from it would print 34,000 empty marks as if they were a finding.
    """
    n = 0
    for L, kind in KIND.items():
        if kind in ('text', 'code'):
            continue
        j = ci(L) + 1
        for r in range(ROW0, ws.max_row + 1):
            if ws.cell(row=r, column=j).value not in (None, ''):
                n += 1
    return n


def pick_formula_source(cands, want, tpl_name):
    """The candidate carrying every computed column as a live formula, with each skip named."""
    for c in cands:
        try:
            wb = load_workbook(c['path'], data_only=False)
        except Exception as e:
            print('SKIP hrat formulas %s: unreadable (%s)' % (c['name'], type(e).__name__))
            continue
        sheet = next((s for s in wb.sheetnames if SHEET_HINT in s), None)
        if sheet is None:
            print('SKIP hrat formulas %s: no sheet like %r' % (c['name'], SHEET_HINT))
            wb.close()
            continue
        have = probe(wb[sheet], want)
        if len(have) < len(want):
            print('SKIP hrat formulas %s [%s]: only %d of %d computed columns carry a formula'
                  % (c['name'], sheet, len(have), len(want)))
            wb.close()
            continue
        if not answered_cells(wb[sheet]):
            print('SKIP hrat formulas %s [%s]: all %d computed columns are live but no answer cell '
                  'holds a value - a blank card, not a compiled round'
                  % (c['name'], sheet, len(want)))
            wb.close()
            continue
        print('HOLD hrat formulas %s [%s]: all %d computed columns carry a live formula'
              % (c['name'], sheet, len(want)))
        return c, sheet, wb, wb[sheet]
    raise SystemExit('ERR hrat: no candidate carries all %d formulas (the template %s holds none by '
                     'design) - ask for a workbook whose score columns are still live'
                     % (len(want), tpl_name))


def rewrite_pct_thresholds(forms, score_cols, headers, warns):
    """Read a bare threshold on a percent column as a percentage, where the printed rule says one.

    Only `IF(AI{r}>=10,3,0)` qualifies on this card: every other percent rule already writes `90%`.
    """
    for L in score_cols:
        f = forms[L]
        for m in list(re.finditer(r'([A-Z]{1,3})\{r\}\s*(?:<=|>=|=|<|>)\s*(\d+(?:\.\d+)?)(?![%\d])',
                                  f)):
            letter, tok, num = m.group(1), m.group(0), float(m.group(2))
            if KIND.get(letter) != 'pct' or num <= 1.5:
                continue
            new = '%s%%' % tok
            forms[L] = f.replace(tok, new)
            f = forms[L]
            warns.append({'col': L, 'raw': letter, 'from': tok, 'to': new, 'why': (
                '%s is a percent column and the rule printed beside its score (%s) reads >%s%%, but '
                'the workbook formula compares %s - a cell holding a fraction can never reach it, so '
                'the threshold is read as a percentage'
                % (letter, headers[ci(L)][:44], ('%g' % num), tok))})
            print('NOTE hrat %s: %r read as %r' % (L, tok, new))


def first_form(ws, L, limit=60):
    """The first live formula down a column, read the same way as on the row the spec is built from."""
    i = ci(L) + 1
    if i > ws.max_column:
        return None
    for r in range(ROW0, min(ws.max_row, ROW0 + limit) + 1):
        s = clean(ws.cell(r, i).value)
        if s and '{r}' in s:
            return s
    return None


def band_of(f, where):
    m = re.fullmatch(r'IF\(([A-Z]{1,3})\{r\}>(\d+(?:\.\d+)?)%,"([^"]+)",'
                     r'IF\([A-Z]{1,3}\{r\}<(\d+(?:\.\d+)?)%,"([^"]+)","([^"]+)"\)\)', f)
    if not m:
        raise SystemExit('ERR hrat %s: the Risk formula is not the shape the model bands on: %r'
                         % (where, f))
    return {'col': m.group(1), 'hi': float(m.group(2)), 'lo': float(m.group(4)),
            'labels': [m.group(3), m.group(5), m.group(6)]}


COUNT_CALL = re.compile(r'(COUNT|COUNTA)\(([^()]*)\)')


def max_rule(f, where):
    """How a block percentage decides its own maximum, read off the formula it divides by.

    Two shapes appear on this card: a fixed number (`O{r}/12`, `BO{r}/15`) and three times a
    COUNT/COUNTA over the exact cells the sheet names. Anything else aborts, because a maximum that
    cannot be recomputed is a percentage that cannot be trusted.
    """
    den = f.rpartition('/')[2].strip()
    if not den:
        raise SystemExit('ERR hrat %s: a percentage formula with no division: %r' % (where, f))
    m = re.fullmatch(r'\(?\s*(\d+)\s*\*\s*(COUNT|COUNTA)\(([^()]*)\)\s*\)?', den)
    if m:
        cols = []
        for tok in m.group(3).split(','):
            cm = CELLREF.fullmatch(tok.strip())
            if cm is None:
                raise SystemExit('ERR hrat %s: the maximum counts %r, which is not a cell'
                                 % (where, tok))
            cols.append(cm.group(1))
        return {'per': int(m.group(1)), 'fn': m.group(2), 'cols': cols}
    m = re.fullmatch(r'\(?\s*(\d+)\s*\)?', den)
    if m:
        return {'per': int(m.group(1)), 'fn': None, 'cols': []}
    raise SystemExit('ERR hrat %s: a percentage divides by %r, which is neither a fixed number nor '
                     '3 x COUNT/COUNTA over named cells' % (where, den))


def rank_rule(f, where):
    m = re.fullmatch(r'RANK\.EQ\(([A-Z]{1,3})\{r\},\s*\$?([A-Z]{1,3})\$?(\d+):\$?[A-Z]{1,3}\$?(\d+),'
                     r'\s*(\d+)\)', f)
    if not m:
        raise SystemExit('ERR hrat %s: the Rank formula is not RANK.EQ(cell, one column, order): %r'
                         % (where, f))
    return {'col': m.group(1), 'against': m.group(2), 'from': int(m.group(3)), 'to': int(m.group(4)),
            'order': int(m.group(5))}


def validate_kinds(ws, read, seen_limit=3000):
    """Count the values the divisions typed that the declared vocabulary does not cover.

    `read` is the set of input columns a score formula actually compares. A column outside it - the
    drainage flag, the terrain text - changes no score, so its spread is printed and the grid offers
    what the divisions typed as suggestions. A column inside it is a different matter: if more than a
    fifth of its values sit outside the options the card names, the options here are wrong, not the
    data, and the build aborts rather than publishing a picker the divisions ignore.
    """
    odd, rows = {}, 0
    for row in ws.iter_rows(min_row=ROW0, values_only=True):
        rows += 1
        if rows > seen_limit:
            break
        for L, kind in KIND.items():
            i = ci(L)
            s = norm(row[i]) if i < len(row) else ''
            if s in ('', 'NA', '-', 'N/A', 'Env'):
                continue
            if kind in ('text', 'code'):
                continue
            if kind in ('yesno', 'yn'):
                ok = s in LISTS[kind] or s in ALIAS
            elif kind == 'cat':
                try:
                    n = float(s)
                    ok = n == int(n) and 1 <= n <= 4
                except ValueError:
                    ok = False
            elif kind in ('cnt', 'rate', 'pct'):
                try:
                    ok = float(s) >= 0 or kind in ('rate', 'pct')
                except ValueError:
                    ok = False
            else:
                ok = s in LISTS.get(kind, [])
            if not ok:
                odd.setdefault(L, []).append(s)
    for L in sorted(odd):
        print('NOTE hrat %s (%s%s): %d of its values sit outside the declared vocabulary, e.g. %s - '
              'the import keeps them as typed and lists them under the cell'
              % (L, KIND[L], ', scored' if L in read else ', not read by any score', len(odd[L]),
                 ', '.join(sorted(set(odd[L]))[:4])[:64]))
    hard = [L for L in odd if L in read and LISTS.get(KIND[L])
            and len(odd[L]) > 0.2 * max(rows, 1)]
    if hard:
        raise SystemExit('ERR hrat: columns %s are scored and more than a fifth outside their '
                         'declared options, so the vocabulary here is wrong, not the data'
                         % ', '.join(hard))
    return rows, {L: sorted(set(odd[L]))[:12] for L in sorted(odd)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--template')
    ap.add_argument('--formulas')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    cands = srcutil.discover(entry)
    if not cands:
        raise SystemExit('ERR hrat nothing found under %s for patterns %s'
                         % (entry['roots'], entry['patterns']))

    tpls = [c for c in cands if 'template' in c['name'].lower()]
    if a.template:
        tpls = [srcutil.stat_rec(a.template)] + [c for c in tpls
                                                 if c['path'] != os.path.abspath(a.template)]
    if not tpls:
        raise SystemExit('ERR hrat no *template*.xlsx among %d candidates - the column order is only '
                         'ever read from the owner\'s template file' % len(cands))
    tpl = tpls[0]
    wbt = load_workbook(tpl['path'], data_only=False)
    tsh = next((s for s in wbt.sheetnames if SHEET_HINT in s), None)
    if tsh is None:
        raise SystemExit('ERR hrat %s has no sheet like %r (it has %s)'
                         % (tpl['name'], SHEET_HINT, ', '.join(wbt.sheetnames)))
    wst = wbt[tsh]
    n, headers = read_head(wst)
    if any(not h for h in headers):
        raise SystemExit('ERR hrat: row 2 has %d empty headers (%s) - the order cannot be read'
                         % (sum(1 for h in headers if not h),
                            ', '.join(get_column_letter(i + 1) for i, h in enumerate(headers)
                                      if not h)[:40]))
    if wst.max_row >= ROW0:
        print('NOTE hrat %s is not blank below row %d (%d rows) - only its header is read'
              % (tpl['name'], ROW0, wst.max_row - ROW0 + 1))
    spans = group_spans(wst, n)
    score_cols, sub_cols, blk_pct, overall, tail = classify(headers, spans)
    want = score_cols + sub_cols + blk_pct + [tail['max'], overall, tail['rank'], tail['risk']]
    if len(want) != NFORMULA:
        raise SystemExit('ERR hrat: %d computed columns found, expected %d' % (len(want), NFORMULA))

    fcands = [c for c in cands if c['path'] != tpl['path']]
    if a.formulas:
        fcands = [srcutil.stat_rec(a.formulas)] + [c for c in fcands
                                                  if c['path'] != os.path.abspath(a.formulas)]
    src, fsh, _wbf, wsf = pick_formula_source(fcands, want, tpl['name'])
    fhead = read_head(wsf)[1]
    relabel = [(get_column_letter(i + 1), headers[i], fhead[i])
               for i in range(min(n, len(fhead)))
               if headers[i] != re.sub(r'\s*\d+$', '', fhead[i])]
    if relabel:
        print('NOTE hrat the formula workbook relabels %d headers - e.g. %s %r vs %r. The template '
              'wording is the one published and the exported sheet uses it'
              % (len(relabel), relabel[0][0], relabel[0][1][:38], relabel[0][2][:38]))

    forms = formulas_of(wsf, want, '%s [%s]' % (src['name'], fsh))

    warns = []
    rewrite_pct_thresholds(forms, score_cols, headers, warns)
    # The card's own `3*COUNT(...)` stays: two of the three filled workbooks in the family grade the
    # maximum with COUNT, and restating it as COUNTA moves rows across the 79%/60% band (Charsadda's
    # AGRA reads 79.17% Low Risk in its own card, 76% Medium here). A text answer in a scored percent
    # column still scores without charging the maximum in Excel too, and the import names those cells.
    for L, f in forms.items():
        check_shape(f, '%s %s' % (src['name'], L))

    # the rank is the one column that cannot be carried as text: its range is the rows present
    rk = rank_rule(forms[tail['rank']], '%s Rank' % src['name'])
    if rk['col'] != rk['against']:
        print('NOTE hrat Rank ranks %s against a range of %s - the range is rebuilt over the rows '
              'loaded, so it ranks %s either way' % (rk['col'], rk['against'], rk['col']))
    old = '$%s$%d:$%s$%d' % (rk['against'], rk['from'], rk['against'], rk['to'])
    warns.append({'col': tail['rank'], 'from': old, 'to': 'the rows on the sheet',
                  'why': ('%s anchors the rank to %s whatever the length of the sheet, so its own Rank '
                          'column prints #N/A from row %d down even though the sheet holds %d rows; a '
                          'later division\'s copy anchors to its own row count instead. Neither anchors '
                          'to the rows actually compiled. The grid ranks the rows loaded and names how '
                          'many that is, and the exported sheet writes the range over the rows it '
                          'writes' % (src['name'], old, rk['to'] + 1, wsf.max_row - ROW0 + 1))})
    band = band_of(forms[tail['risk']], '%s Risk' % src['name'])
    if band['col'] != overall:
        print('NOTE hrat the Risk formula reads %s, not the overall percentage %s - the band follows '
              'the column the sheet names' % (band['col'], overall))

    # one entry per row-1 block; scored blocks carry their own pair of aggregate columns and the
    # maximum rule read off their own percentage formula. `k` is the index into `spans`, which is
    # what every column's `g` field uses, so the two sides of the payload key off the same number.
    blocks = []
    for k, (a1, b1, title) in enumerate(spans):
        inside = [get_column_letter(i + 1) for i in range(ci(a1), ci(b1) + 1)]
        raws = [L for L in inside if L in KIND]
        scs = [L for L in inside if L in score_cols]
        sub = [L for L in sub_cols if L in inside]
        pc = [L for L in blk_pct if L in inside]
        if not scs:
            if raws:
                print('NOTE hrat block %r carries %d input columns and no score - the Profile block '
                      'stays descriptive' % (title, len(raws)))
            blocks.append({'k': k, 't': title, 'g': [a1, b1], 'raw': raws, 'sc': [],
                           'sub': None, 'pct': None, 'max': None})
            continue
        if len(sub) != 1 or len(pc) != 1:
            raise SystemExit('ERR hrat: block %r has %d subtotal / %d percentage columns'
                             % (title, len(sub), len(pc)))
        rule = max_rule(forms[pc[0]], '%s %s' % (src['name'], pc[0]))
        named = set(rule['cols'])
        if named - set(raws):
            raise SystemExit('ERR hrat: block %r counts %s in its maximum, which are not raw columns '
                             'of that block' % (title, ', '.join(sorted(named - set(raws)))))
        if rule['fn'] and len(rule['cols']) != len(raws):
            print('NOTE hrat block %r counts %d of its %d raw columns in its maximum - the card '
                  'leaves %s blank when they do not apply'
                  % (title, len(rule['cols']), len(raws),
                     ', '.join(sorted(set(raws) - named)) or 'none'))
        blocks.append({'k': k, 't': title, 'g': [a1, b1], 'raw': raws, 'sc': scs, 'sub': sub[0],
                       'pct': pc[0], 'max': rule})
    scored = [x for x in blocks if x['sc']]
    byk = {x['k']: x for x in blocks}
    if len(scored) != 4:
        raise SystemExit('ERR hrat: %d scored blocks, want four' % len(scored))
    if sum(len(x['sc']) for x in scored) != NIND:
        raise SystemExit('ERR hrat: the %d score columns do not sit inside the four scored blocks'
                         % NIND)

    # the overall maximum is what the sheet's own Total score formula adds up: one fixed addend per
    # literal block plus 3 per answered indicator. Assert both sides agree so the grid can never
    # compute a denominator different from the file it exports.
    stripped = re.sub(r'[^+]*COUNT[AS]?\([^()]*\)', '', forms[tail['max']])
    addends = sorted(int(t) for t in re.findall(r'\d+', stripped))
    lit = sorted(x['max']['per'] for x in scored if not x['max']['fn'])
    counted = [x for x in scored if x['max']['fn']]
    if addends != lit:
        raise SystemExit('ERR hrat: %s adds up %s but the block maxima fixed on this card are %s'
                         % (forms[tail['max']], addends, lit))
    if counted and set(x['max']['per'] for x in counted) != {3}:
        raise SystemExit('ERR hrat: a block counts its answered indicators at %s per indicator, not 3'
                         % sorted(set(x['max']['per'] for x in counted)))
    fixed = sum(lit)
    nmax = sum(len(x['max']['cols']) for x in counted)
    print('NOTE hrat maximum = %d fixed (blocks %s) + 3 per answered cell of the %d the count-based '
          'blocks name (%s), full card %d'
          % (fixed, lit, nmax, [x['t'] for x in counted], fixed + 3 * nmax))

    inds = []
    for L in score_cols:
        deps = cells(forms[L])
        if not deps:
            raise SystemExit('ERR hrat: score column %s reads no cell (%r)' % (L, forms[L]))
        blk = byk[block_of(spans, L)]
        for d in deps:
            if d not in blk['raw'] and d not in score_cols:
                raise SystemExit('ERR hrat: %s reads %s, which is not an input of block %r'
                                 % (L, d, blk['t']))
        inds.append({'sc': L, 'raw': sorted(set(deps)), 'blk': blk['k'], 'f': forms[L],
                     'rule': headers[ci(L)], 'name': headers[ci(deps[0])],
                     'opt': L in OPTIONAL or any(d in OPTIONAL for d in deps)})

    # the blank template carries no number format on any cell, so a column displays the way the
    # compiled sheet displays it; if the template ever gains formats they win.
    def fmt_of(i):
        t = norm(wst.cell(ROW0, i + 1).number_format)
        return t if t != 'General' else norm(wsf.cell(ROW0, i + 1).number_format)
    from_tpl = sum(1 for i in range(n) if norm(wst.cell(ROW0, i + 1).number_format) != 'General')
    print('NOTE hrat %d of %d columns carry a format in the template, the rest take the compiled '
          "sheet's (the blank template is all General)" % (from_tpl, n))

    # how much of the province's score comes from a cell nobody filled in: a score column with no
    # ISBLANK guard reads its raw cell through Excel's blank-is-zero rule, so an empty cell still
    # earns a mark. Measured here, counted per row in the grid, and named on the page.
    unguarded = [x for x in inds if 'ISBLANK' not in x['f']]
    if any(len(x['raw']) != 1 for x in unguarded):
        raise SystemExit('ERR hrat: %s reads more than one cell, so an empty-cell rule cannot be '
                         'counted from a single column'
                         % ', '.join(x['sc'] for x in unguarded if len(x['raw']) != 1))
    bcols, brows, bcells = {}, 0, 0
    for row in wsf.iter_rows(min_row=ROW0, values_only=True):
        hit = 0
        for x in unguarded:
            i = ci(x['raw'][0])
            typed = norm(row[i]) if i < len(row) else ''
            if typed:
                continue
            hit += 1
            bcols[x['sc']] = bcols.get(x['sc'], 0) + 1
        if hit:
            brows += 1
            bcells += hit
    print('NOTE hrat %d marks over %d rows sit on an empty cell in an unguarded rule (%d of %d score '
          'columns have no ISBLANK guard) - the grid scores them the way Excel does and counts them '
          'on the row' % (bcells, brows, len(unguarded), NIND))

    rows, odd = validate_kinds(wsf, {d for x in inds for d in x['raw']})
    now = datetime.datetime.now(dashpatch.PKT)
    stamp = '%02d-%s-%d' % (now.day, dashpatch.MONTHS[now.month - 1], now.year)
    payload = {
        'asof': stamp,
        'gen': '%s %02d:%02d' % (stamp, now.hour, now.minute),
        'src': ['%s [%s]' % (tpl['name'], tsh),
                '%s [%s] formulas' % (src['name'], fsh)],
        'sh': SHEET_HINT, 'r0': ROW0, 'n': n, 'nsc': NIND, 'rows': rows,
        'g': [{'a': a1, 'b': b1, 't': t} for a1, b1, t in spans],
        'c': [{'L': get_column_letter(i + 1), 'h': headers[i],
               'g': block_of(spans, get_column_letter(i + 1)),
               'k': KIND.get(get_column_letter(i + 1)) or
                    ('computed' if get_column_letter(i + 1) in forms else 'text'),
               'o': LISTS.get(KIND.get(get_column_letter(i + 1), ''), []),
               'opt': get_column_letter(i + 1) in OPTIONAL,
               'f': fmt_of(i),
               'x': forms.get(get_column_letter(i + 1))}
              for i in range(n)],
        'i': inds, 'B': blocks,
        'tail': dict(tail, ovr=overall, ovrF=forms[overall], maxF=forms[tail['max']],
                    subF={x['sub']: forms[x['sub']] for x in scored},
                    pctF={x['pct']: forms[x['pct']] for x in scored}),
        'fixed': fixed, 'perind': 3, 'nmax': nmax, 'full': fixed + 3 * nmax, 'band': band,
        'rank': {'col': rk['col'], 'order': rk['order'],
                 'anchor': [rk['against'], rk['from'], rk['to']]},
        'warn': warns, 'odd': odd, 'alias': ALIAS,
        'blank': {'cells': bcells, 'rows': brows, 'cols': bcols,
                  'sc': [x['sc'] for x in unguarded],
                  'guard': [x['sc'] for x in inds if 'ISBLANK' in x['f']]},
    }
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'hrat.json')
    srcutil.write_text(dest, js)
    print('SRC hrat template %s' % tpl['path'])
    print('SRC hrat formulas %s' % src['path'])
    print('OK hrat %d %d columns, %d indicators in %d blocks, max/rank/risk %s/%s/%s, %d rule(s) '
          'restated, %d rows profiled'
          % (len(js), n, NIND, len(scored), tail['max'], tail['rank'], tail['risk'],
             len(warns), rows))


if __name__ == '__main__':
    main()
