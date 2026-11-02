"""Reconcile the 10:43 Nov-26 coverage exports (district + UC) with CQ.adm.

Both exports share labels but the UC report has three extra location columns, so
columns are located by their header label rather than by position.
"""
import io, json, sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
DL = Path(r'C:\Users\HD\Downloads')
DIST = DL / 'coverage_SNID Nov 2026_2026-11-02_104319.xls'
UC = DL / 'coverage_SNID Nov 2026_2026-11-02_104311.xls'
RENAME = {'WAZIR-S LOWER': 'WAZIR-S Lower', 'WAZIR-S UPPER': 'WAZIR-S Upper'}

# field -> (last-level label, required parent tokens, optional forbidden tokens)
LOOKUP = {
    'kidsHH': ('Target Children in HH from MP (Planning)', ('Total',)),
    'housesP': ('No. of houses planned from MP', ()),
    'housesV': ('No. of houses visited', ()),
    'target': ('Overall Target', ()),
    'vacc': ('Overall Children Vaccinated', ('Total',)),
    'cov': ('% Overall Children Vaccinated among target', ()),
    'mobile': ('Mobile Children covered / MMP CD', ()),
    'na': ('Still NA Total', ()),
    'ref': ('Still Refusals Total', ()),
    'missed': ('Total Still Missed', ()),
    'opvUsed': ('OPV Doses Used', ('Total OPV Doses',)),
}


def load_cq():
    s = open(ROOT / 'index.html', encoding='utf-8', newline='').read()
    i = s.find('const CQ = {'); j = s.find('{', i)
    d, k, instr, esc = 0, j, False, False
    while k < len(s):
        ch = s[k]
        if instr:
            if esc: esc = False
            elif ch == chr(92): esc = True
            elif ch == '"': instr = False
        else:
            if ch == '"': instr = True
            elif ch == '{': d += 1
            elif ch == '}':
                d -= 1
                if d == 0: break
        k += 1
    return json.loads(s[j:k + 1])


def table(p):
    text = p.read_bytes().decode('utf-8', 'replace')
    return max(pd.read_html(io.StringIO(text), header=None), key=len)


def find_cols(t):
    cols = list(t.columns)
    out = {}
    for f, (last, parents) in LOOKUP.items():
        hits = []
        for i, c in enumerate(cols):
            parts = [str(x) for x in c if str(x) != 'nan']
            if parts and parts[-1] == last and all(p in parts for p in parents):
                hits.append(i)
        if len(hits) != 1:
            raise SystemExit('column %s matched %d times: %s' % (f, len(hits), hits))
        out[f] = hits[0]
    return out


def n(v):
    try:
        f = float(str(v).replace(',', ''))
        return int(f) if f == int(f) else round(f, 2)
    except Exception:
        return 0


def adm_row(vals, ci):
    o = {k: n(vals[ci[k]]) for k in LOOKUP if k != 'opvUsed'}
    used = n(vals[ci['opvUsed']])
    o['waste'] = round((used - o['vacc']) * 100 / used, 2) if used else 0
    return o


def main():
    cq = load_cq()
    pub = cq['adm']['NOV-26-1']

    dt = table(DIST)
    dci = find_cols(dt)
    print('district columns:', dci)
    dd = dt[dt.iloc[:, 0].astype(str).str.strip() == 'KP']
    dmap = {}
    for _, r in dd.iterrows():
        name = RENAME.get(str(r.iloc[2]).strip().upper(), str(r.iloc[2]).strip())
        dmap[name] = adm_row(r.tolist(), dci)
    print('district export:', len(dmap), 'districts')

    ut = table(UC)
    uci = find_cols(ut)
    print('UC columns:', uci)
    ud = ut[ut.iloc[:, 0].astype(str).str.strip() == 'KP']
    ud = ud[pd.to_numeric(ud.iloc[:, 5], errors='coerce').notna()]
    print('UC export: data rows', len(ud), 'districts', ud.iloc[:, 2].nunique(),
          'UC codes', ud.iloc[:, 5].nunique())
    umap = {}
    for _, r in ud.iterrows():
        name = RENAME.get(str(r.iloc[2]).strip().upper(), str(r.iloc[2]).strip())
        o = umap.setdefault(name, {k: 0 for k in LOOKUP})
        for k in LOOKUP:
            o[k] += n(r.tolist()[uci[k]])
    for name, o in umap.items():
        used = o.pop('opvUsed')
        o['waste'] = round((used - o['vacc']) * 100 / used, 2) if used else 0

    print('\nUC vs district export:')
    bad = 0
    for d in sorted(dmap):
        if d not in umap:
            print(' ', d, 'MISSING from UC export'); bad += 1; continue
        diffs = {k: (dmap[d][k], umap[d][k]) for k in dmap[d] if dmap[d][k] != umap[d][k]}
        if diffs:
            print(' ', d, diffs); bad += len(diffs)
    print('field mismatches:', bad)
    for k in ('kidsHH', 'housesP', 'housesV', 'target', 'vacc', 'na', 'ref', 'missed', 'mobile'):
        print('  %-8s district %12s   UC %12s' % (k, f"{sum(v[k] for v in dmap.values()):,}",
                                                  f"{sum(v[k] for v in umap.values()):,}"))
    print('  %-8s district %12.2f%%  UC %12.2f%%' % ('cov',
          sum(v['vacc'] for v in dmap.values()) * 100 / sum(v['target'] for v in dmap.values()),
          sum(v['vacc'] for v in umap.values()) * 100 / sum(v['target'] for v in umap.values())))

    print('\npublished vs 10:43 district export:')
    tot = {k: [0, 0] for k in ('target', 'vacc', 'na', 'ref', 'missed', 'mobile')}
    for d in sorted(set(pub) | set(dmap)):
        if d not in dmap or d not in pub:
            print(' ', d, 'ONLY IN', 'export' if d in dmap else 'published'); continue
        diffs = {k: (pub[d][k], dmap[d][k]) for k in dmap[d] if pub[d].get(k) != dmap[d][k]}
        for k in tot:
            tot[k][0] += pub[d][k]; tot[k][1] += dmap[d][k]
        if diffs:
            print(' ', d, diffs)
    print('totals published -> export:', tot)


if __name__ == '__main__':
    main()
