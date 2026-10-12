"""Extract the campaign-history payload (const CHD) from the KP+TD UC spotting workbook.

The DATA sheet is 134MB, so KP/KPTD rows are cached in _refresh/cache/ch_rows.pkl and
only re-read when the workbook's path/mtime/size change.

Usage: python _refresh/extract_chd.py [--source PATH] [--out PATH] [--no-cache]
Prints one status line: OK chd <json chars> <summary> | ERR chd <reason>
"""
import argparse
import collections
import io
import os
import pickle
import re
import sys
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'chd'
COLS = {'year': 'Year', 'month': 'Month', 'vaccine': 'Vaccine', 'camp': 'Campaign',
        'prov': 'Province', 'dist': 'District', 'uc': 'UC_NAME',
        'tgt_adm': 'AdmTarget', 'tgt_mp': 'Adm_MPTarget', 'cov': 'AdmCovered',
        'na': 'Adm_StillNA', 'ref': 'Adm_StillREF', 'sm': 'Adm_TotalStillMissed',
        'zd': 'Adm_ZeroDoze'}
MONTHS = [('jan', 1), ('feb', 2), ('mar', 3), ('apr', 4), ('may', 5), ('jun', 6),
          ('jul', 7), ('aug', 8), ('sept', 9), ('sep', 9), ('oct', 10), ('nov', 11), ('dec', 12)]
MONNAME = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
           7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'}
MONIDX = {v: k for k, v in MONNAME.items()}


def num(x):
    if x is None:
        return 0
    if isinstance(x, (int, float)):
        return int(round(x))
    try:
        return int(round(float(str(x).replace(',', '').strip())))
    except ValueError:
        return 0


def lab_month(lab):
    l = str(lab).lower()
    for t, m in MONTHS:
        if t in l:
            return m
    return None


def ctype(lab):
    u = str(lab).upper()
    if 'SNID' in u or 'SIA' in u:
        return 'SNID'
    if u.startswith('NID') or ' NID' in u:
        return 'NID'
    if 'OBR' in u:
        return 'OBR'
    if u.startswith('CR') or 'CR ' in u:
        return 'CR'
    return 'SIA'


def district_order(repo):
    """District order + division map, taken verbatim from the dashboard so CHD.ds matches ZD/DATA."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    order, div = [], {}
    for dv, d in re.findall(r'"dv":\s*"([^"]+)",\s*"d":\s*"([^"]+)"', s):
        if d not in div:
            order.append(d)
            div[d] = dv.upper()
    if 'WAZIR-S' not in div:
        order.append('WAZIR-S')
        div['WAZIR-S'] = 'DIKHAN'
    return order, div


def read_rows(rec, sheet, cache_path, use_cache=True):
    if use_cache and os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            c = pickle.load(f)
        if c.get('src') == srcutil.file_id(rec):
            return c['header'], c['rows'], True
    t0 = time.time()
    import openpyxl
    wb = openpyxl.load_workbook(rec['path'], read_only=True, data_only=True)
    if sheet not in wb.sheetnames:
        raise SystemExit('ERR chd sheet %r missing (has %s)' % (sheet, wb.sheetnames))
    it = wb[sheet].iter_rows(values_only=True)
    hdr = list(next(it))
    rows = [r for r in it if len(r) > 5 and r[5] in ('KP', 'KPTD')]
    wb.close()
    srcutil.say('# chd: read %d KP/KPTD rows from %s in %.0fs' % (len(rows), rec['name'], time.time() - t0))
    if use_cache:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'wb') as f:
            pickle.dump({'src': srcutil.file_id(rec), 'header': hdr, 'rows': rows}, f)
    return hdr, rows, False


def build(hdr, rows, repo):
    missing = [v for v in COLS.values() if v not in hdr]
    if missing:
        raise SystemExit('ERR chd DATA sheet is missing columns %s - layout changed, update COLS' % missing)
    ix = {k: hdr.index(v) for k, v in COLS.items()}
    order, div = district_order(repo)

    G = collections.defaultdict(lambda: [0, 0, 0, 0, 0, 0, set(), []])
    for r in rows:
        d = str(r[ix['dist']]).strip()
        u = re.sub(r'\s+', ' ', str(r[ix['uc']]).strip())
        if d not in div or not u:
            continue
        tmp = num(r[ix['tgt_mp']])
        tgt = tmp if tmp > 0 else max(num(r[ix['tgt_adm']]), 0)
        k = (int(r[ix['year']]), str(r[ix['camp']]).strip(), d, u)
        g = G[k]
        g[0] += tgt
        g[1] += num(r[ix['cov']])
        g[2] += num(r[ix['na']])
        g[3] += num(r[ix['ref']])
        g[4] += num(r[ix['sm']])
        g[5] += num(r[ix['zd']])
        g[6].add(str(r[ix['vaccine']]).strip())
        if r[ix['month']]:
            g[7].append(MONIDX.get(str(r[ix['month']]).strip()[:3].title(), 0))

    C = collections.defaultdict(lambda: {'rows': {}, 'vax': set(), 'mos': []})
    for (y, lab, d, u), g in G.items():
        c = C[(y, lab)]
        if sum(g[0:6]) > 0:
            c['rows'][(d, u)] = list(g[0:6])
        c['vax'] |= g[6]
        c['mos'] += g[7]

    cams = []
    for (y, lab), c in C.items():
        mo = lab_month(lab)
        if mo is None:
            cc = [m for m in c['mos'] if m]
            mo = collections.Counter(cc).most_common(1)[0][0] if cc else 0
        cams.append({'y': y, 'mo': mo, 'n': lab, 't': ctype(lab),
                     'v': '+'.join(sorted(c['vax'])), 'rows': c['rows']})
    cams.sort(key=lambda x: (x['y'], x['mo'], x['n']))

    ucs = {(d, u) for c in cams for (d, u) in c['rows']}
    ucs = sorted(ucs, key=lambda x: (order.index(x[0]), x[1]))
    uidx = {k: i for i, k in enumerate(ucs)}

    out = {'ds': order, 'dv': [div[d] for d in order],
           'u': [[u, order.index(d)] for d, u in ucs],
           'c': [{'y': c['y'], 'm': c['mo'], 'n': c['n'], 't': c['t'], 'v': c['v'],
                  'r': [[uidx[k]] + list(v) for k, v in sorted(c['rows'].items(), key=lambda x: uidx[x[0]])]}
                 for c in cams]}
    first, last = cams[0], cams[-1]
    summary = '%d campaigns %s-%s, %d districts, %d UCs, %d UC rows' % (
        len(cams), '%s%s' % (MONNAME.get(first['mo'], ''), first['y']),
        '%s%s' % (MONNAME.get(last['mo'], ''), last['y']),
        len(order), len(ucs), sum(len(c['r']) for c in out['c']))
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    ap.add_argument('--no-cache', action='store_true')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    ds = cfg['auto'][DS]
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(ds)
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR chd no spotting workbook found under %s' % ds['roots'])
    cache_path = os.path.join(srcutil.HERE, ds.get('cache', 'cache/ch_rows.pkl').replace('/', os.sep))
    hdr, rows, cached = read_rows(rec, ds['sheet'], cache_path, use_cache=not a.no_cache)
    srcutil.say('# chd: %s (%d rows, cache=%s)' % (rec['name'], len(rows), 'hit' if cached else 'rebuilt'))
    out, summary = build(hdr, rows, cfg['repo'])
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'chd.json')
    srcutil.write_text(dest, js)
    print('SRC chd %s' % rec['path'])
    print('OK chd %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
