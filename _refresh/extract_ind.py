"""Extract the compiled campaign indicators file (const INDIC).

Usage: python _refresh/extract_ind.py [--source PATH] [--out PATH]
Prints one status line: OK ind <json chars> <summary> | ERR ind <reason>

Source: EOC dashboard campaign indicators export, saved as
`Indicators to be included in dashboard as record.csv` in Downloads.
Two header rows: row 0 = section groups, row 1 = column names (84 columns).
One row per UC per campaign (2017-2026, 85 campaigns, ~76k rows).

Sections (file column indices, row 1 names must match):
  geo 0-7, admin 8-28, ICM 29-46, market survey 47-57, LQAS 58-71, PCM 72-83.

Payload: district aggregates for every campaign (counts summed, percentages
recomputed from their count pairs -- formulas verified against the file) plus
raw UC rows for the 2025+ campaigns, so the dashboard can offer a district /
UC toggle without carrying all 76k rows. Missing cell = -1; a literal -1 in
the source is treated as missing (27 such cells, all in the Still NA/Refusal/
Missed columns), while other negative corrections are kept.
"""
import argparse
import csv
import datetime
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'ind'

# (source key, label, first col, last col)
SECS = [
    ('admin', 'Admin coverage and missed children', 8, 28),
    ('icm', 'Intra-campaign monitoring (ICM)', 29, 46),
    ('ms', 'Market survey', 47, 57),
    ('lqas', 'E-LQAS (lot quality)', 58, 71),
    ('pcm', 'Post-campaign monitoring (PCM)', 72, 83),
]

def lab(s):
    return re.sub(r'\s+', ' ', (s or '').strip())

# per-source: short type map and % formulas (section-relative indices).
# p = percent column, n = count column.
# pp: [outIdx, [numIdx,...], [denIdx,...]] -> 100*sum(num)/sum(den).
# other p columns are shown at district level as the mean of the UC values.
TYPE = {
    'admin': {2: 'p', 5: 'p', 6: 'p', 13: 'p', 14: 'p', 15: 'p'},
    'icm': {3: 'p', 11: 'p', 15: 'p'},
    'ms': {3: 'p'},
    'lqas': {3: 'p'},
    'pcm': {3: 'p'},
}
PP = {
    'admin': [[2, [1], [0]], [5, [4], [0]], [6, [4], [3]], [14, [12], [9]], [15, [12], [0]]],
    'icm': [[3, [2], [1]], [15, [16], [14]]],
    'ms': [[3, [2], [1]]],
    'lqas': [[3, [0], [0, 1, 2]]],
    'pcm': [[3, [2], [1]]],
}
# percent columns whose numerator/denominator are not in the file: shown at
# district level as the mean of the UC values ('Same Day coverage', 'ICM Seen %')
MEAN = {'admin': [13], 'icm': [11]}

ANCHORS = [('year', 'Year'), ('camp', 'Campaign'), ('div', 'Division'), ('dist', 'District'),
           ('teh', 'Tehsil'), ('uc', 'UC_NAME'), ('code', 'UCCode_GEOJan21'), ('lpu', '# of LP Ucs'),
           ('admin0', 'Administrative Target'), ('icm0', '# of ICM'), ('ms0', '# of MS'),
           ('lqas0', 'Pass'), ('pcm0', '# of PCM MS')]

# UC rows are embedded for these campaign years only (payload size)
UC_FROM_YEAR = 2025


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def num(v):
    t = ('' if v is None else str(v)).replace(',', '').replace('%', '').strip()
    # a literal -1 counts as not reported (same as the payload sentinel); other
    # negatives are kept - the portal emits them as corrections in the Still NA/
    # Refusal/Missed columns
    if t == '' or t in ('-', '-1', 'NA', 'N/A', 'NULL'):
        return None
    try:
        f = float(t)
    except ValueError:
        return None
    return int(f) if f == int(f) else f


def parse(path):
    with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
        rows = [r for r in csv.reader(fh) if any((c or '').strip() for c in r)]
    if len(rows) < 3:
        raise SystemExit('ERR ind file has %d rows' % len(rows))
    h0, h1 = rows[0], rows[1]
    if len(h1) < 84:
        raise SystemExit('ERR ind header has %d columns, want >= 84' % len(h1))
    h1 = list(h1) + [''] * (84 - len(h1))
    for key, want in ANCHORS:
        idx = {'year': 0, 'camp': 1, 'div': 2, 'dist': 3, 'teh': 4, 'uc': 5, 'code': 6, 'lpu': 7,
               'admin0': 8, 'icm0': 29, 'ms0': 47, 'lqas0': 58, 'pcm0': 72}[key]
        got = norm(h1[idx])
        if got != norm(want):
            raise SystemExit('ERR ind column %d is %r, want %r' % (idx, h1[idx], want))
    return h1, rows[2:]


def build(path):
    h1, body = parse(path)

    camps, cidx = [], {}
    dnames, didx = [], {}
    tehnames, tidx = [], {}
    ucs, uidx = [], {}
    rows_seen = set()

    sec_cols = {k: list(range(a, b + 1)) for k, _l, a, b in SECS}
    sec_lab = {k: [lab(h1[c]) for c in range(a, b + 1)] for k, _l, a, b in SECS}
    # per (section, campaign, district): sums + non-null counts per column
    dd_sum, dd_cnt = {}, {}
    # per campaign: uc rows per section
    uu = {}

    for r in body:
        if len(r) < 84:
            r = list(r) + [''] * (84 - len(r))
        cy, cl = r[0].strip(), r[1].strip()
        if not cl:
            continue
        ck = (cy, cl)
        if ck not in cidx:
            cidx[ck] = len(camps)
            camps.append({'l': cl, 'y': cy})
        ci = cidx[ck]
        d = r[3].strip()
        if not d:
            continue
        if d not in didx:
            didx[d] = len(dnames)
            dnames.append(d)
        di = didx[d]
        t = r[4].strip()
        if t not in tidx:
            tidx[t] = len(tehnames)
            tehnames.append(t)
        ti = tidx[t]
        uk = (di, ti, r[5].strip())
        if uk not in uidx:
            uidx[uk] = len(ucs)
            ucs.append([r[5].strip(), di, ti, r[6].strip()])
        ui = uidx[uk]
        rk = (ci, ui)
        if rk in rows_seen:
            raise SystemExit('ERR ind duplicate UC row %r in %s / %s' % (r[5], cl, d))
        rows_seen.add(rk)

        want_uc = int(cy) >= UC_FROM_YEAR if cy.isdigit() else False
        for k, _l, a, b in SECS:
            vals = [num(r[c]) for c in range(a, b + 1)]
            key = (k, ci, di)
            s, c = dd_sum.setdefault(key, {}), dd_cnt.setdefault(key, {})
            for j, v in enumerate(vals):
                if v is not None:
                    s[j] = s.get(j, 0) + v
                    c[j] = c.get(j, 0) + 1
            if want_uc and any(v is not None for v in vals):
                uu.setdefault((k, ci), []).append([ui, [(-1 if v is None else v) for v in vals]])

    n = len(camps)
    order = list(range(n))[::-1]            # file runs oldest -> newest; dropdown newest first
    remap = {old: new for new, old in enumerate(order)}
    camps = [camps[i] for i in order]

    S = {}
    for k, l, a, b in SECS:
        cols = sec_cols[k]
        mk = len(cols)
        typ = TYPE[k]
        pp = PP.get(k, [])
        # hide columns that are empty across the whole file
        total_cnt = {}
        for (kk, _ci, _di), c in dd_cnt.items():
            if kk != k:
                continue
            for j, v in c.items():
                total_cnt[j] = total_cnt.get(j, 0) + v
        hide = [j for j in range(mk) if total_cnt.get(j, 0) == 0]
        dd = {}
        for (kk, ci, di), s in dd_sum.items():
            if kk != k:
                continue
            c = dd_cnt[(kk, ci, di)]
            vals = []
            for j in range(mk):
                if j in c:
                    vals.append(int(s[j]) if s[j] == int(s[j]) else round(s[j], 2))
                else:
                    vals.append(-1)
            for j in MEAN.get(k, []):
                vals[j] = round(s[j] / c[j], 1) if c.get(j) else -1
            for out, nums, dens in pp:
                dn = sum(s.get(x, 0) for x in dens)
                if dn > 0:
                    v = 100.0 * sum(s.get(x, 0) for x in nums) / dn
                    vals[out] = round(v, 1) if typ.get(out) == 'p' else int(round(v))
                else:
                    vals[out] = -1
            dd.setdefault(remap[ci], {})[str(di)] = vals
        uuo = {}
        for (kk, ci), rows in uu.items():
            if kk == k:
                uuo[remap[ci]] = rows
        S[k] = {'l': l, 'k': [[sec_lab[k][j], typ.get(j, 'n')] for j in range(mk)],
                'h': hide, 'dd': dd, 'uu': uuo}

    ucmin = sorted(S['admin']['uu'].keys(), key=lambda x: int(x))
    mtime = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    ind = {'src': os.path.basename(path), 'asof': mtime.date().isoformat(), 'rows': len(body),
           'camps': camps, 'dn': dnames, 'teh': tehnames, 'ucs': ucs, 'S': S,
           'ucmin': ucmin}
    nu = sum(len(v) for v in S['admin']['uu'].values())
    summary = ('%d campaigns %s-%s, %d districts, %d UCs, %d rows; UC detail for %d campaigns (%d Admin UC rows)'
               % (len(camps), camps[-1]['y'], camps[0]['y'], len(dnames), len(ucs), len(body),
                  len(ucmin), nu))
    return ind, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    if a.source:
        cands = [srcutil.stat_rec(a.source)]
    else:
        cands = srcutil.discover(cfg['auto'][DS])
    if not cands:
        raise SystemExit('ERR ind no indicators export found under %s' % cfg['auto'][DS]['roots'])
    for rec in cands:
        p = rec['path']
        if not os.path.exists(p):
            continue
        ind, summary = build(p)
        js = srcutil.dumps(ind)
        dest = a.out or os.path.join(srcutil.OUT, 'indic.json')
        srcutil.write_text(dest, js)
        print('SRC ind %s' % p)
        print('OK ind %d %s' % (len(js), summary))
        return
    raise SystemExit('ERR ind no usable file among %d candidates' % len(cands))


if __name__ == '__main__':
    main()
