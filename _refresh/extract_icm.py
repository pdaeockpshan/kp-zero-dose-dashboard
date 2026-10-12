"""Extract the intra-campaign monitoring UC-wise payload (const ICMD).

Usage: python _refresh/extract_icm.py [--source PATH] [--out PATH] [--asof YYYY-MM-DD]
Prints one status line: OK icm <json chars> <summary> | ERR icm <reason>
"""
import argparse
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil
import dashpatch

DS = 'icm'

FIELDS = [
    ('dv', ('Division',)),
    ('d', ('District',)),
    ('t', ('Tehsil',)),
    ('uc', ('UC',)),
    ('cl', ('# of Cluster',)),
    ('hh', ('# of Houses Checked',)),
    ('rc', ('Total Recall Checked',)),
    ('rv', ('Total Recall Vaccinated',)),
    ('mi', ('Total Missed',)),
    ('nt', ('NT',)),
    ('tv', ('TVBMC',)),
    ('na', ('Child Away (NA)',)),
    ('rf', ('Child Refusal',)),
    ('gr', ('Guest Children by Recall',)),
    ('gv', ('Guest Children Vaccinated by Recall',)),
    ('seen', ('Total Seen',)),
    ('fm', ('Total Fingermarked',)),
    ('nvfm', ('Not Vaccinated but Finger',)),
    ('epi', ('# of Routine EPI doses',)),
    ('mon', ('# of Child vaccinated',)),
    ('pca', ('Poorly Covered Area',)),
    ('ma', ('Missed Area',)),
]
NUMERIC = [k for k, _ in FIELDS[4:]]


def num(v):
    if v is None or str(v).strip() == '':
        return 0
    try:
        f = float(str(v).replace(',', '').replace('%', ''))
    except ValueError:
        return 0
    return int(round(f)) if abs(f - round(f)) < 1e-9 else round(f, 2)


def col_index(H, prefixes):
    for p in prefixes:
        for i, h in enumerate(H):
            if h.startswith(p):
                return i
    return None


def build(src_path, cfg, asof=None):
    import openpyxl
    ds = cfg['auto'][DS]
    wb = openpyxl.load_workbook(src_path, read_only=True, data_only=True)
    sheet = ds.get('sheet')
    if sheet not in wb.sheetnames:
        sheet = wb.sheetnames[0]
    rows = list(wb[sheet].iter_rows(values_only=True))
    wb.close()
    if len(rows) < 3:
        raise SystemExit('ERR icm sheet %r has only %d rows' % (sheet, len(rows)))
    H = [str(c).strip() if c is not None else '' for c in rows[0]]
    idx = {}
    for k, pref in FIELDS:
        idx[k] = col_index(H, pref)
    missing = [k for k, i in idx.items() if i is None and k not in ('t',)]
    if missing:
        raise SystemExit('ERR icm columns not found: %s (header: %s)' % (missing, H))

    recs, total = [], None
    last = {'Division': '', 'District': '', 'Tehsil': ''}
    for r in rows[1:]:
        d = {H[i]: (r[i] if i < len(r) else None) for i in range(len(H)) if H[i]}
        camp = str(d.get('Campaign Name') or '').strip()
        if camp.lower() == 'total':
            total = d
            continue
        if not str(d.get('UC') or '').strip():
            continue
        for k in ('Division', 'District', 'Tehsil'):
            v = d.get(k)
            if v is None or str(v).strip() == '':
                d[k] = last[k]
            else:
                last[k] = str(v).strip()
                d[k] = last[k]
        d['UC'] = str(d['UC']).strip()
        d['Division'] = str(d['Division']).strip().upper()
        d['District'] = str(d['District']).strip()
        d['Tehsil'] = str(d['Tehsil']).strip()
        recs.append(d)
    if not recs:
        raise SystemExit('ERR icm no UC rows parsed')

    def val(d, k):
        i = idx[k]
        if k in ('dv', 'd', 't', 'uc'):
            return d.get({'dv': 'Division', 'd': 'District', 't': 'Tehsil', 'uc': 'UC'}[k], '')
        return num(d.get(H[i])) if i is not None else 0

    keys = [k for k, _ in FIELDS]
    u = [[val(d, k) for k in keys] for d in recs]
    tot = {}
    if total:
        for k in keys:
            if k in ('dv', 'd', 't', 'uc'):
                continue
            tot[k] = val(total, k)
    else:
        for k in NUMERIC:
            tot[k] = num(sum(val(d, k) for d in recs))

    if asof is None:
        asof = (cfg['auto'][DS].get('config') or {}).get('asof')
    if asof is None:
        cur = srcutil.read_text(os.path.join(cfg['repo'], 'index.html'))
        asof = json.loads(dashpatch.get_payload(cur, 'ICMD')).get('asof', '')
    out = {'src': os.path.basename(src_path),
           'camp': str(recs[0].get('Campaign Name') or '').strip(),
           'asof': asof, 'k': keys, 'u': u, 'tot': tot}
    dists = sorted({r[1] for r in u})
    summary = '%s, %d UCs in %d districts (%s), recall %d/%d' % (
        out['camp'], len(u), len(dists), '+'.join(dists), tot.get('rv', 0), tot.get('rc', 0))
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    ap.add_argument('--asof')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(cfg['auto'][DS])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR icm no ICM workbook found under %s' % cfg['auto'][DS]['roots'])
    out, summary = build(rec['path'], cfg, a.asof)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'icmd.json')
    srcutil.write_text(dest, js)
    print('SRC icm %s' % rec['path'])
    print('OK icm %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
