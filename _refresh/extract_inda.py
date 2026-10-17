# -*- coding: utf-8 -*-
"""Supplement the campaign data pack's Admin table with SNID Sept 2026.

The EOC compiled-indicators export (`Indicators to be included in dashboard as
record.csv`) still ends at SNID May 2026, so the data pack's campaign picker has
no Sept option. The EOC summary coverage report (`cov_SNID Sept 2026.xls`, the
same UC-wise workbook behind the Missed children & refusals tab) carries the
admin coverage and missed-children fields for that round.

Payload `const INDA`:
  camp  campaign label
  asof  coverage report date
  n     UC rows
  dn/teh/ucs  directory entries that do not exist in INDIC (BAR SWAT split)
  dd    district rows keyed by absolute district index (INDIC.dn + this dn)
  uu    [ucIndex, [21 admin values]] with ucIndex absolute (INDIC.ucs + this ucs)

Columns follow INDIC.S.admin.k. Fields the coverage report does not carry
(MP target, same-day coverage, guest, HRMP mobile, school) are -1 (= not
reported). Total Adm Covered and AdmTotalCoverage % use the report's household
children vaccinated, the same coverage definition as the Missed children tab.
"""
import argparse
import datetime
import os
import re
import sys

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'inda'
INDIC = os.path.join(srcutil.OUT, 'indic.json')

# workbook columns (0-based, flat read_html header)
COL_TGT, COL_HH = 6, 7
COL_RNA, COL_RRF, COL_RMISS = 9, 10, 11
COL_SNA, COL_SRF, COL_SLO, COL_STILL = 24, 25, 26, 27
COL_ZD, COL_AFP = 29, 31


def lab(s):
    return re.sub(r'\s+', ' ', str(s or '').strip())


def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s or '').lower())


def code(v):
    s = str(v).strip()
    return s[:-2] if s.endswith('.0') else s


def num(v):
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else f


def r1(v):
    return round(v, 1) if v is not None else -1


def load_indic():
    import json
    with open(INDIC, encoding='utf-8') as fh:
        return json.load(fh)


def read_book(path):
    t = pd.read_html(path)[0]
    t.columns = range(t.shape[1])
    return t


def admin_vals(rows):
    s = lambda c: sum((num(r[c]) or 0) for r in rows)
    tgt, hh, rmiss = s(COL_TGT), s(COL_HH), s(COL_RMISS)
    rna, rrf = s(COL_RNA), s(COL_RRF)
    sna, srf, still = s(COL_SNA), s(COL_SRF), s(COL_STILL)
    cover = 100.0 * hh / tgt if tgt else None
    return [
        tgt, hh, r1(cover), -1, hh, r1(cover), -1,
        rna, rrf, rmiss, sna, srf, still, -1,
        r1(100.0 * still / rmiss) if rmiss else -1,
        r1(100.0 * still / tgt) if tgt else -1,
        -1, -1, -1, s(COL_ZD), s(COL_AFP),
    ]


def build(path):
    ind = load_indic()
    dn = list(ind['dn'])
    teh = list(ind['teh'])
    ucs = [list(u) for u in ind['ucs']]
    dmap = {norm(x): i for i, x in enumerate(dn)}
    tmap = {norm(x): i for i, x in enumerate(teh)}
    cmap = {}
    for i, u in enumerate(ucs):
        cmap.setdefault(code(u[3]), i)

    t0 = read_book(path)
    t = t0[t0[2].astype(str).str.strip().isin(['', '-']) == False]
    t = t[t[5].astype(str).str.strip() != '']
    rows = [r for _, r in t.iterrows()]
    if not rows:
        raise SystemExit('ERR inda no UC rows in %s' % path)

    extra_d, extra_t, extra_u = [], [], []
    district_bucket, uc_rows = {}, []
    unmatched = []
    for r in rows:
        dname = lab(r[2])
        tname = lab(r[3])
        uname = lab(r[4])
        ucode = code(r[5])
        if norm(dname) in dmap:
            di = dmap[norm(dname)]
        else:
            if dname not in extra_d:
                extra_d.append(dname)
            di = len(dn) + extra_d.index(dname)
        if norm(tname) in tmap:
            ti = tmap[norm(tname)]
        else:
            if tname not in extra_t:
                extra_t.append(tname)
            ti = len(teh) + extra_t.index(tname)
        if ucode in cmap:
            ui = cmap[ucode]
        else:
            hit = next((i for i, u in enumerate(ucs)
                        if norm(u[0]) == norm(uname) and u[1] == di and u[2] == ti), None)
            if hit is None:
                key = (uname, di, ti, ucode)
                if key not in [tuple(x) for x in extra_u]:
                    extra_u.append([uname, di, ti, ucode])
                ui = len(ucs) + [tuple(x) for x in extra_u].index(key)
            else:
                ui = hit
                ucode = ucs[ui][3]
        district_bucket.setdefault(di, []).append(r)
        uc_rows.append((ui, r))

    # one row per UC; a duplicate absolute index means the directory already had it
    seen = {}
    for ui, r in uc_rows:
        if ui in seen:
            raise SystemExit('ERR inda duplicate UC row %r (%s)' % (ui, r[4]))
        seen[ui] = 1

    dd = {str(di): admin_vals(rs) for di, rs in sorted(district_bucket.items())}
    uu = [[ui, admin_vals([r])] for ui, r in uc_rows]

    mt = datetime.datetime.fromtimestamp(os.path.getmtime(path))
    p = {
        'camp': {'l': 'SNID Sept 2026', 'y': '2026'},
        'asof': mt.date().isoformat(),
        'src': os.path.basename(path),
        'n': len(uc_rows),
        'dn': extra_d,
        'teh': extra_t,
        'ucs': extra_u,
        'dd': dd,
        'uu': uu,
    }
    # invariants against the workbook totals row
    tot = [r for _, r in t0.iterrows()
           if lab(r[2]) == '-' and num(r[COL_TGT])]
    if tot:
        tr = tot[0]
        want = (num(tr[COL_TGT]), num(tr[COL_HH]), num(tr[COL_RNA]), num(tr[COL_RRF]),
                num(tr[COL_STILL]))
        got = (sum(v[0] for v in dd.values()), sum(v[1] for v in dd.values()),
               sum(v[7] for v in dd.values()), sum(v[8] for v in dd.values()),
               sum(v[12] for v in dd.values()))
        if want != got:
            raise SystemExit('ERR inda totals %r != workbook %r' % (got, want))
    summary = ('%d UCs, %d districts, target %s, vaccinated %s, still missed %s'
               % (len(uu), len(dd), format(sum(v[0] for v in dd.values()), ','),
                  format(sum(v[1] for v in dd.values()), ','),
                  format(sum(v[12] for v in dd.values()), ',')))
    return p, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    if a.source:
        rec = srcutil.stat_rec(a.source)
    else:
        rec = srcutil.newest(cfg['auto'][DS])
    if not rec:
        raise SystemExit('ERR inda no coverage report found under %s' % cfg['auto'][DS]['roots'])
    p = rec['path']
    if not os.path.exists(p):
        raise SystemExit('ERR inda source not found: %s' % p)
    payload, summary = build(p)
    js = srcutil.dumps(payload)
    dest = a.out or os.path.join(srcutil.OUT, 'inda.json')
    srcutil.write_text(dest, js)
    print('SRC inda %s' % p)
    print('OK inda %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
