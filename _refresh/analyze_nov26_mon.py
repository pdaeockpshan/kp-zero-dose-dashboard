"""Aggregate the four SNID Nov 2026 monitoring exports to district grain.

Each export carries a second header row with the real per-column labels; it is
consumed as a header and dropped before summing. Cluster and supervisor
aggregates are compared with the published CQ.icm NOV-26-1 rows.
"""
import io, json, sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(__file__).resolve().parent.parent
DL = Path(r'C:\Users\HD\Downloads')
CLUSTER = DL / 'icm_2026-11-02_10-33-10.xls'
TEAM = DL / 'icm_2026-11-02_10-35-45.xls'
SUP = DL / 'icm_supervisor_2026-11-02_10-37-14.xls'
TRANSIT = DL / 'icm_transit_2026-11-02_10-37-29.xls'
RENAME = {'WAZIR-S LOWER': 'WAZIR-S Lower', 'WAZIR-S UPPER': 'WAZIR-S Upper'}

CLUSTER_FIELDS = {
    'cl': '# of Cluster', 'hh': '# of Houses Checked', 'door': '# Correct Door Marking',
    'nr': '# of No Response Houses', 'dw': '# Dont want to Participate Houses',
    'rc': 'Total Recall Children (0-59)', 'rv': 'Total Recall Vaccinated (0-59)',
    'mi': 'Total Missed', 'tdn': 'Team did not visit house',
    'tm': 'Team visited but missed child', 'na': 'Child Away (NA)', 'rf': 'Child Refusal',
    'gr': 'Guest Children by Recall', 'gv': 'Guest Children Vaccinated by Recall',
    'seen': 'Total Seen', 'fm': 'Total Finger marked',
    'nvfm': 'Not Vaccinated but Finger Marked', 'unv': 'No. of Children Found Unvaccinated',
    'pca': 'Poorly Covered Area (n)', 'ma': 'Missed Area (n)',
}
SUP_KEYS = ['% Vaccine Carrier', '% OPV vials', '% Finger markers', '% Cold Chain maintained',
            '% Microplan Updated', '% Supervisor carrying Vitamin-A', '% Name and ID match',
            '% Checklist Completed', '% Supervisor supported teams',
            '% Quality of the IPC Skills of the supervisor with the teams']


def table(p, header=0):
    text = p.read_bytes().decode('utf-8', 'replace')
    return max(pd.read_html(io.StringIO(text), header=header), key=len)


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


def num(v):
    try:
        f = float(str(v).replace(',', ''))
        return f if f == f else 0.0
    except Exception:
        return 0.0


def dist(s):
    return RENAME.get(str(s).strip().upper(), str(s).strip())


def take_header(df):
    head = [str(x).strip() for x in df.iloc[0].tolist()]
    body = df.iloc[1:].copy()
    body.columns = head
    return body


def prep(p, campaign_col=None):
    df = table(p)
    if str(df.iloc[0, 0]).strip().lower().startswith('campaign'):
        df = take_header(df)
    if campaign_col is None:
        campaign_col = df.columns[0]
    df = df[df[campaign_col].astype(str).str.strip().str.startswith('SNID Nov')]
    return df


def main():
    cq = load_cq()
    icm = cq['icm']['NOV-26-1']

    # ---- cluster -------------------------------------------------------
    c = prep(CLUSTER, 'Campaign Name')
    c = c[c['District'].astype(str) != 'Total'].copy()
    c['District'] = c['District'].map(dist)
    for k, col in CLUSTER_FIELDS.items():
        c[k] = pd.to_numeric(c[col], errors='coerce').fillna(0)
    agg = c.groupby('District').agg(ucs=('UC Code', 'nunique'), n=('District', 'size'),
                                    **{k: (k, 'sum') for k in CLUSTER_FIELDS})
    print('cluster rows', len(c), 'districts', len(agg), 'UC codes', c['UC Code'].nunique())
    diffs = 0
    for d in icm:
        if d not in agg.index:
            print(' MISSING', d); diffs += 1; continue
        for k in CLUSTER_FIELDS:
            if int(agg.loc[d, k]) != icm[d][k]:
                diffs += 1
        if int(agg.loc[d, 'ucs']) != icm[d]['tuc'] or int(agg.loc[d, 'ucs']) != icm[d]['ruc']:
            print(' ', d, 'UCs export', int(agg.loc[d, 'ucs']),
                  'published tuc/ruc', icm[d]['tuc'], icm[d]['ruc'])
    print('cluster count mismatches:', diffs)
    for k in CLUSTER_FIELDS:
        dd = [d for d in icm if int(agg.loc[d, k]) != icm[d][k]]
        if dd:
            print('  %-5s %2d districts  total %+d  (published %d -> export %d)' % (
                k, len(dd), int(agg[k].sum()) - sum(r[k] for r in icm.values()),
                sum(r[k] for r in icm.values()), int(agg[k].sum())))
    print('published totals cl/hh/rc/rv/mi:', [sum(r[k] for r in icm.values()) for k in ('cl', 'hh', 'rc', 'rv', 'mi')])
    print('export totals   cl/hh/rc/rv/mi:', [int(agg[k].sum()) for k in ('cl', 'hh', 'rc', 'rv', 'mi')])

    # ---- supervisor ----------------------------------------------------
    s = prep(SUP, 'Campaign name')
    s = s[s['District name'].astype(str) != 'Total'].copy()
    s['District'] = s['District name'].map(dist)
    q = s[SUP_KEYS].apply(pd.to_numeric, errors='coerce')
    means = q.groupby(s['District']).mean()
    print('\nsupervisor rows', len(s), 'districts', len(means))
    maxdev = 0
    for d in icm:
        if d not in means.index:
            print(' MISSING', d); continue
        pub = icm[d]['sv']
        got = means.loc[d].tolist()
        dev = max(abs((pub[i] if pub[i] is not None else 0) - (got[i] if got[i] == got[i] else 0)) for i in range(10))
        maxdev = max(maxdev, dev)
        if dev > 0.6:
            print(' ', d, 'max dev', round(dev, 2))
            print('     pub', pub)
            print('     exp', [round(x, 2) if x == x else None for x in got])
    print('max supervisor deviation from published sv:', round(maxdev, 2))
    print('blank rates:', {k: round(float(q[k].isna().mean()), 3) for k in SUP_KEYS})
    print('zero rates:', {k: round(float((q[k].fillna(-1) == 0).mean()), 3) for k in SUP_KEYS})

    # ---- team / transit ------------------------------------------------
    t = prep(TEAM)
    t = t[t['District name'].astype(str) != 'Total'].copy()
    t['District'] = t['District name'].map(dist)
    t['teams'] = pd.to_numeric(t['# Teams Monitored'], errors='coerce').fillna(0)
    tv = t.groupby('District')['teams'].sum()
    print('\nteam rows', len(t), 'districts', len(tv), 'teams total', int(tv.sum()),
          'UC names', t['UC name'].nunique())
    print('team columns:', t.columns.tolist())
    tr = prep(TRANSIT)
    tr = tr[tr['District name'].astype(str) != 'Total'].copy()
    tr['District'] = tr['District name'].map(dist)
    tr['sites'] = pd.to_numeric(tr['# Sites Visited'], errors='coerce').fillna(0)
    trv = tr.groupby('District')['sites'].sum()
    print('transit rows', len(tr), 'districts', len(trv), 'sites total', int(trv.sum()),
          'UC names', tr['UC name'].nunique())
    print('transit columns:', tr.columns.tolist())
    print('team districts missing:', sorted(set(icm) - set(tv.index)))
    print('transit districts missing:', sorted(set(icm) - set(trv.index)))
    print('team per district:', {d: int(v) for d, v in tv.items()})
    print('transit per district:', {d: int(v) for d, v in trv.items()})


if __name__ == '__main__':
    main()
