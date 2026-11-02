"""Build the SNID Nov 2026 day-1 refresh from the 02-Nov-2026 Downloads exports.

Reads six files: the 10:43 coverage summary (district and UC wise), the 10:33 ICM
cluster export, the 10:35 team-monitoring export, the 10:37 supervisor export and
the 10:37 transit export. The two 10:36/10:35 files labelled "SNID May 2026" are
deliberately not read: the portal filter returned May for those two modules, so
Nov fixed-site monitoring is still missing.

Emits _refresh/nov26_refresh_2026-11-02.json with the four payloads the patcher
needs (CQ.adm, CQ.icm, NOCD tv/tr, ICMQ tm/aic) plus a readable report.

District totals in this file are the sum of the export's own rows; the UC plan
count is the number of UC rows the coverage export carries for the district.
"""
import io
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

ROOT = Path(__file__).resolve().parent.parent
DL = Path(r'C:\Users\HD\Downloads')
COV_DIST = DL / 'coverage_SNID Nov 2026_2026-11-02_104319.xls'
COV_UC = DL / 'coverage_SNID Nov 2026_2026-11-02_104311.xls'
CLUSTER = DL / 'icm_2026-11-02_10-33-10.xls'
TEAM = DL / 'icm_2026-11-02_10-35-45.xls'
SUP = DL / 'icm_supervisor_2026-11-02_10-37-14.xls'
TRANSIT = DL / 'icm_transit_2026-11-02_10-37-29.xls'
EXCLUDED = [DL / 'icm_2026-11-02_10-35-24.xls', DL / 'icm_fixed_2026-11-02_10-36-02.xls']

LABEL = 'SNID Nov 2026'
CAMP = 'NOV-26-1'
ASOF = '2026-11-02'
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

# coverage summary labels, matched on (last level, required parent tokens)
ADM_LOOKUP = {
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

TM_SRC = {
    'fem': '% Female', 'adu': '% Adult', 'idm': '% Name Matches ID',
    'mkq': '% Quilty of Markers', 'trn': '% Training',
    'cc1': '% Cold Chain- approved Vaccine carrier', 'cc2': '% Cold Chain- lid and seal properly',
    'cc3': '% Cold Chain- no water inside carrier', 'dry': '% Dry', 'vvm': '% Valid VVM',
    'lab': '% Intact Label', 'rec': '% Vial Properly Recapped',
    'mat': '% Vacc. Children matched with doses', 'tal': '% Tally Sheet filling',
    'vita': '% Team administered Vitamin-A', 'rmc': '% Record of Missed Children',
    'rtm': '% Location in Route Map', 'wkl': '% Proper Workload',
    'ask': '% Asking Newborn,NA,SC', 'afp': '% Asking for AFP&RI',
    'fmo': '% Marker Used for FM Only', 'fmf': '% Marking FM fully',
    'wst': '% Minimizing Vaccine Wastage',
}
AIC_SRC = {
    'vac': '% Vaccine Carrier', 'opv': '% OPV vials', 'fmk': '% Finger markers',
    'ccm': '% Cold Chain maintained', 'mpu': '% Microplan Updated',
    'vit': '% Supervisor carrying Vitamin-A', 'nid': '% Name and ID match',
    'chk': '% Checklist Completed', 'sup': '% Supervisor supported teams',
    'ipc': '% Quality of the IPC Skills of the supervisor with the teams',
}

# a column is "not asked" when almost every unit left it blank, or when it is
# filled but never anything but zero (the extractor's rule for the CSV rounds)
CARRIED_MIN = 0.5
ZERO_MIN_VALID = 20
ZERO_MAX_NONZERO = 0.05


def const(name):
    s = open(ROOT / 'index.html', encoding='utf-8', newline='').read()
    return json.loads(dashpatch.get_payload(s, name).replace('<\\/', '</'))


def raw_table(p):
    text = p.read_bytes().decode('utf-8', 'replace')
    return max(pd.read_html(io.StringIO(text), header=None), key=len)


def lab_table(p):
    text = p.read_bytes().decode('utf-8', 'replace')
    df = max(pd.read_html(io.StringIO(text), header=0), key=len)
    if str(df.iloc[0, 0]).strip().lower().startswith('campaign'):
        head = [str(x).strip() for x in df.iloc[0].tolist()]
        df = df.iloc[1:].copy()
        df.columns = head
    return df


def find_cols(t):
    out = {}
    cols = list(t.columns)
    for f, (last, parents) in ADM_LOOKUP.items():
        hits = [i for i, c in enumerate(cols)
                if (lambda parts: parts and parts[-1] == last and all(p in parts for p in parents))(
                    [str(x) for x in c if str(x) != 'nan'] if not isinstance(c, (int, str)) else [str(c)])]
        if len(hits) != 1:
            raise SystemExit('ADM_LOOKUP %s matched %d columns' % (f, len(hits)))
        out[f] = hits[0]
    return out


def dist(s):
    return RENAME.get(str(s).strip().upper(), str(s).strip())


def num(v):
    try:
        f = float(str(v).replace(',', '').replace('%', ''))
        if f != f or f in (float('inf'), float('-inf')):
            return None
        return f
    except Exception:
        return None


def pct(v):
    f = num(v)
    if f is None or f < 0 or f > 100:
        return None
    return f


def nov_rows(df, col):
    d = df[df[col].astype(str).str.strip().str.startswith('SNID Nov')].copy()
    dcol = 'District name' if 'District name' in d.columns else 'District'
    d = d[d[dcol].astype(str).str.strip() != 'Total']
    d['District'] = d[dcol].map(dist)
    return d


def build_adm():
    t = raw_table(COV_DIST)
    ci = find_cols(t)
    rows = t[t.iloc[:, 0].astype(str).str.strip() == 'KP']
    adm, order = {}, []
    for _, r in rows.iterrows():
        vals = r.tolist()
        name = dist(vals[2])
        if name in ('-', 'nan') or name in adm:
            continue
        o = {k: num(vals[ci[k]]) for k in ADM_LOOKUP if k != 'opvUsed'}
        if any(v is None for v in o.values()):
            continue
        used = num(vals[ci['opvUsed']])
        o['waste'] = round((used - o['vacc']) * 100 / used, 2) if used else 0
        adm[name] = {k: (int(v) if float(v) == int(v) else round(v, 2))
                     for k, v in o.items() if k != 'opvUsed'}
        order.append(name)
    plan = uc_plan()
    return {d: adm[d] for d in order}, plan


def uc_plan():
    t = raw_table(COV_UC)
    rows = t[t.iloc[:, 0].astype(str).str.strip() == 'KP']
    rows = rows[pd.to_numeric(rows.iloc[:, 5], errors='coerce').notna()]
    out = {}
    for _, r in rows.iterrows():
        d = dist(r.iloc[2])
        out.setdefault(d, set()).add(str(r.iloc[4]).strip())
    return {d: len(v) for d, v in out.items()}


def build_icm(adm_districts, plan):
    c = nov_rows(lab_table(CLUSTER), 'Campaign Name')
    for k, col in CLUSTER_FIELDS.items():
        c[k] = pd.to_numeric(c[col], errors='coerce').fillna(0)
    agg = c.groupby('District').agg(ucs=('UC Code', 'nunique'),
                                    **{k: (k, 'sum') for k in CLUSTER_FIELDS})
    if set(agg.index) != set(adm_districts):
        raise SystemExit('cluster districts disagree with coverage: %s'
                         % sorted(set(agg.index) ^ set(adm_districts)))
    if set(plan) != set(adm_districts):
        raise SystemExit('coverage plan districts disagree: %s'
                         % sorted(set(plan) ^ set(adm_districts)))
    out = {}
    for d in adm_districts:
        row = {k: int(agg.loc[d, k]) for k in CLUSTER_FIELDS}
        row['tuc'] = int(plan[d])
        row['ruc'] = int(agg.loc[d, 'ucs'])
        row['op'] = round((row['tdn'] + row['tm']) * 100 / row['mi'], 2) if row['mi'] else None
        out[d] = row
    return out


def build_noc(icm):
    t = nov_rows(lab_table(TEAM), 'Campaign name')
    t['v'] = pd.to_numeric(t['# Teams Monitored'], errors='coerce').fillna(0)
    tv = t.groupby('District')['v'].sum()
    tr = nov_rows(lab_table(TRANSIT), 'Campaign name')
    tr['v'] = pd.to_numeric(tr['# Sites Visited'], errors='coerce').fillna(0)
    trv = tr.groupby('District')['v'].sum()
    if set(tv.index) != set(icm):
        raise SystemExit('team export districts disagree: %s' % sorted(set(tv.index) ^ set(icm)))
    if not set(trv.index) <= set(icm):
        raise SystemExit('transit export has unknown districts: %s' % sorted(set(trv.index) - set(icm)))
    return ({d: int(tv[d]) for d in icm},
            {d: int(trv[d]) for d in trv.index},
            len(t), len(tr))


def iq_kind(df, kind, kmap, keys, weight_col):
    """(per-district rows, fill stats, dq, zc) for one monitoring instrument."""
    n_rows = {d: 0 for d in df['District']}
    cnt = {d: 0.0 for d in df['District']}
    acc = {d: {k: [0.0, 0.0] for k in kmap} for d in df['District']}
    fill = {k: [0, 0, 0] for k in kmap}  # valid, non-zero, cells
    bad = [0, 0]
    for _, r in df.iterrows():
        d = r['District']
        w = 1.0
        if weight_col:
            wv = num(r[weight_col])
            w = wv if wv and wv > 0 else 1.0
            cnt[d] += wv if wv and wv > 0 else 0
        n_rows[d] += 1
        row_bad = 0
        for k, col in kmap.items():
            if col not in df.columns:
                continue
            raw = str(r[col]).strip()
            if raw == '' or raw.upper() in ('-', 'NA', 'N/A', 'NAN', 'NONE', 'NULL'):
                fill[k][2] += 1
                continue
            v = pct(raw)
            if v is None:
                bad[0] += 1
                row_bad += 1
                fill[k][2] += 1
                continue
            fill[k][0] += 1
            fill[k][2] += 1
            if v > 0:
                fill[k][1] += 1
            a = acc[d][k]
            a[0] += v * w
            a[1] += w
        if row_bad:
            bad[1] += 1
    dead, zc = [], []
    for k, col in kmap.items():
        f = fill[k]
        if f[2] and (f[0] / f[2] < CARRIED_MIN or
                     (f[0] >= ZERO_MIN_VALID and f[1] / f[0] < ZERO_MAX_NONZERO)):
            dead.append(k)
            zc.append(k)
    rows = {}
    for d in df['District'].unique():
        vals = []
        for k in keys:
            if k not in kmap or k in dead:
                vals.append(-1)
            else:
                a = acc[d][k]
                vals.append(int(round(a[0] / a[1])) if a[1] else -1)
        rows[d] = [n_rows[d], int(round(cnt[d])) if weight_col else -1] + vals
    return rows, fill, bad, zc, len(df)


def build_icmq(icm, tmK, aicK):
    t = nov_rows(lab_table(TEAM), 'Campaign name')
    s = nov_rows(lab_table(SUP), 'Campaign name')
    tm, tf, tbad, tzc, tn = iq_kind(t, 'tm', TM_SRC, tmK, '# Teams Monitored')
    aic, af, abad, azc, an = iq_kind(s, 'aic', AIC_SRC, aicK, None)
    for name, rows in (('tm', tm), ('aic', aic)):
        if set(rows) != set(icm):
            raise SystemExit('%s districts disagree: %s' % (name, sorted(set(rows) ^ set(icm))))
    out = {'wt': {'tm': 'teams', 'aic': 'uc'}, 'n': {'tm': tn, 'aic': an}}
    out['tm'] = {d: tm[d] for d in icm}
    out['aic'] = {d: aic[d] for d in icm}
    if tzc:
        out.setdefault('zc', {})['tm'] = tzc
    if azc:
        out.setdefault('zc', {})['aic'] = azc
    if tbad[0] or abad[0]:
        out['dq'] = {}
        if tbad[0]:
            out['dq']['tm'] = tbad
        if abad[0]:
            out['dq']['aic'] = abad
    return out, tf, af


def main():
    cq = const('CQ')
    nocd = const('NOCD')
    icmq = const('ICMQ')
    pub_adm = cq['adm'][CAMP]
    pub_icm = cq['icm'][CAMP]
    tmK = [k for k, _ in icmq['tmK']]
    aicK = [k for k, _ in icmq['aicK']]
    adm_keys = list(next(iter(pub_adm.values())).keys())
    icm_keys = [k for k in next(iter(pub_icm.values())).keys() if k not in ('op', 'sv')]

    adm, plan = build_adm()
    icm = build_icm(list(adm), plan)
    tv, tr, tn, trn = build_noc(icm)
    q, tf, af = build_icmq(icm, tmK, aicK)

    if set(adm) != set(pub_adm) or len(adm) != 27:
        raise SystemExit('admin districts disagree with the published table')
    if set(icm) != set(pub_icm):
        raise SystemExit('cluster districts disagree with the published table')

    # published supervisor checklist stays: the UC export cannot reproduce it
    for d in icm:
        icm[d]['sv'] = pub_icm[d].get('sv')

    for d, a in adm.items():
        if a['vacc'] > a['target']:
            raise SystemExit('%s vaccinated above target' % d)
        if not (0 <= a['cov'] <= 100) or not (0 <= a['waste'] <= 100):
            raise SystemExit('%s coverage/wastage outside 0-100' % d)

    # report -----------------------------------------------------------------
    L = []
    L.append('SNID Nov 2026 day-1 refresh from the 02-Nov-2026 Downloads exports')
    L.append('excluded (campaign label says SNID May 2026): %s'
             % ', '.join(p.name for p in EXCLUDED))
    L.append('')
    L.append('admin coverage: %d districts, target %s, vaccinated %s, coverage %.2f%%, '
             'missed %s, NA %s, refusals %s, mobile %s'
             % (len(adm), format(sum(a['target'] for a in adm.values()), ','),
                format(sum(a['vacc'] for a in adm.values()), ','),
                sum(a['vacc'] for a in adm.values()) * 100 / sum(a['target'] for a in adm.values()),
                format(sum(a['missed'] for a in adm.values()), ','),
                format(sum(a['na'] for a in adm.values()), ','),
                format(sum(a['ref'] for a in adm.values()), ','),
                format(sum(a['mobile'] for a in adm.values()), ',')))
    changed = []
    for d in sorted(adm):
        diffs = {k: (pub_adm[d].get(k), adm[d][k]) for k in adm_keys if pub_adm[d].get(k) != adm[d][k]}
        if diffs:
            changed.append((d, diffs))
    L.append('admin districts changed vs published: %d' % len(changed))
    for d, diffs in changed:
        L.append('  %-14s %s' % (d, diffs))
    tot_old = [sum(pub_adm[d][k] for d in pub_adm) for k in ('target', 'vacc', 'missed', 'na', 'ref')]
    tot_new = [sum(adm[d][k] for d in adm) for k in ('target', 'vacc', 'missed', 'na', 'ref')]
    L.append('  totals target/vacc/missed/na/ref: %s -> %s' % (tot_old, tot_new))
    L.append('')
    L.append('ICM cluster: %d districts, %d clusters, %d houses, %d recall, %d missed, '
             '%d UCs reported of %d planned'
             % (len(icm), sum(r['cl'] for r in icm.values()), sum(r['hh'] for r in icm.values()),
                sum(r['rc'] for r in icm.values()), sum(r['mi'] for r in icm.values()),
                sum(r['ruc'] for r in icm.values()), sum(r['tuc'] for r in icm.values())))
    L.append('  published: %d clusters, %d houses, %d recall, %d missed, %d/%d UCs'
             % (sum(r['cl'] for r in pub_icm.values()), sum(r['hh'] for r in pub_icm.values()),
                sum(r['rc'] for r in pub_icm.values()), sum(r['mi'] for r in pub_icm.values()),
                sum(r['ruc'] for r in pub_icm.values()), sum(r['tuc'] for r in pub_icm.values())))
    for d in sorted(icm):
        p, n = pub_icm[d], icm[d]
        dd = {k: (p[k], n[k]) for k in icm_keys if p.get(k) != n[k]}
        if dd:
            L.append('  %-14s %s' % (d, dd))
    opn = [d for d, r in icm.items() if r['op'] is not None]
    L.append('  operational issue non-null: %d districts (published %d)'
             % (len(opn), sum(1 for r in pub_icm.values() if r.get('op') is not None)))
    L.append('')
    L.append('NOCD: team visits %s over %d districts (%d export rows); transit visits %s over %d districts (%d rows); fixed sites not imported (May export only)'
             % (format(sum(tv.values()), ','), len(tv), tn, format(sum(tr.values()), ','), len(tr), trn))
    L.append('')
    L.append('ICMQ: tm %d rows / aic %d rows; wt %s' % (tn, q['n']['aic'], q['wt']))
    L.append('  tm keys carried: %s' % [k for k in tmK if k in TM_SRC])
    L.append('  tm keys absent: %s' % [k for k in tmK if k not in TM_SRC])
    L.append('  aic keys carried: %s' % [k for k in aicK if k in AIC_SRC])
    L.append('  aic keys absent: %s' % [k for k in aicK if k not in AIC_SRC])
    L.append('  zc: %s' % q.get('zc'))
    L.append('  dq: %s' % q.get('dq'))
    for kind, fill, K in (('tm', tf, tmK), ('aic', af, aicK)):
        L.append('  %s fill (valid/total, non-zero/valid):' % kind)
        for k in K:
            f = fill.get(k)
            if f and f[2]:
                L.append('    %-4s %5d/%5d  nz %5d  %s'
                         % (k, f[0], f[2], f[1], 'NOT CARRIED' if k in (q.get('zc') or {}).get(kind, []) else ''))
    for kind, rows in (('tm', q['tm']), ('aic', q['aic'])):
        L.append('  %s province means:' % kind)
        for i, k in enumerate(tmK if kind == 'tm' else aicK):
            num_ = [(r[1] if kind == 'tm' else r[0], r[2 + i]) for r in rows.values() if r[2 + i] >= 0]
            if num_:
                a = sum(v * w for w, v in num_) / sum(w for w, _ in num_)
                L.append('    %-4s %.1f' % (k, a))
    report = '\n'.join(L) + '\n'
    (ROOT / '_refresh' / 'nov26_refresh_report.txt').write_text(report, encoding='utf-8')

    payload = {
        'campaign': {'v': CAMP, 'l': LABEL, 'day': 1, 'start': '2026-11-02',
                     'asof': '02-Nov-2026', 'read': ASOF},
        'asof': ASOF,
        'admKeys': adm_keys,
        'adm': {d: [adm[d][k] for k in adm_keys] for d in adm},
        'icmKeys': icm_keys,
        'icm': {d: [icm[d][k] for k in icm_keys] for d in icm},
        'op': {d: icm[d]['op'] for d in icm},
        'sv': {d: icm[d]['sv'] for d in icm},
        'tv': tv,
        'tr': tr,
        'icmq': q,
    }
    js = srcutil.dumps(payload)
    (ROOT / '_refresh' / 'nov26_refresh_2026-11-02.json').write_text(js, encoding='utf-8')
    print(report)
    print('WROTE nov26_refresh_2026-11-02.json %d chars' % len(js))


if __name__ == '__main__':
    main()
