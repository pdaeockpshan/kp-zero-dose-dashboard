"""Extract EPI-MIS rapid coverage assessments (const ERCA) from the RCA_Report exports.

Every RCA_Report*.xls under the configured roots is loaded; each export carries its
own date range (From/To in the header) and the union of all of them covers the
period. Rows are visit-level (one village/mohallah rapid coverage assessment with
the children checked and the per-antigen vaccinated counts); this extractor
aggregates them to month x EPI district and caches the aggregates per file id in
_refresh/cache/rcamon.pkl, so the 200-400 MB exports are streamed only once.
The newest file wins per (month, district). Monitor name / ID / designation
columns are never read into the payload (public site).

Usage: python _refresh/extract_rca.py [--out PATH]
Prints: SRC rca <newest file> | OK rca <json chars> <summary> | ERR rca <reason>
"""
import argparse
import os
import pickle
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _epicache
import srcutil

DS = 'rca'
CACHE = os.path.join(srcutil.HERE, 'cache', 'rcamon.pkl')
AGS = ('bcg', 'opv0', 'p1', 'p3', 'pcv3', 'ipv1', 'ipv2', 'rota2', 'mr1', 'mr2')
# column positions in the exported data rows (verified against the header labels):
# 0 Sr, 1 District, 2 Tehsil, 3 UC, 4 Village, 5-8 GPS, 9-12 monitor name/id/
# designation/organization, 13 Date of RCA, 14 Area Type, 15 Hard-to-reach,
# 16 High-risk, 17 Children Vaccinated (checked), 18.. antigen (Total, %) pairs.
AG_COL = {'bcg': 18, 'opv0': 22, 'p1': 34, 'p3': 38, 'pcv3': 44,
          'ipv1': 46, 'ipv2': 48, 'rota2': 32, 'mr1': 52, 'mr2': 54}
DATE_RE = re.compile(r'^(20\d\d-\d\d)-\d\d')
NUM_RE = re.compile(r'^\d+')
JUNK_D = ('', '0', '0.0', 'nan', 'none', 'null', 'total', 'longitude (x.y')


def load_cache():
    try:
        with open(CACHE, 'rb') as f:
            return pickle.load(f)
    except (OSError, EOFError, ValueError):
        return {}


def store_cache(cache):
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    tmp = CACHE + '.tmp'
    with open(tmp, 'wb') as f:
        pickle.dump(cache, f)
    os.replace(tmp, CACHE)


def stream_rows(path):
    buf = ''
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(4194304)
            if not chunk:
                break
            buf += chunk.decode('utf-8', 'replace')
            parts = buf.split('</tr>')
            buf = parts.pop()
            for pr in parts:
                if '<tr' in pr:
                    yield pr[pr.index('<tr'):]
    if '<tr' in buf:
        yield buf[buf.index('<tr'):]


def period(rec):
    with open(rec['path'], 'rb') as f:
        head = f.read(20000).decode('utf-8', 'replace')
    m = re.search(r'From\s*:\s*(20\d\d-\d\d-\d\d).{0,200}?To\s*:\s*(20\d\d-\d\d-\d\d)', head, re.S)
    return (m.group(1), m.group(2)) if m else None


def parse_file(rec, edn_ok):
    """One export -> {(mo, district): [v, k, ag..., hv, hk]} (aggregates only)."""
    rows = {}
    junk, n = 0, 0
    for pr in stream_rows(rec['path']):
        cells = [re.sub(r'<[^>]+>', '', c) for c in
                 re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', pr, re.S)]
        if len(cells) < 56:
            continue
        d = re.sub(r'\s+', ' ', cells[1]).strip()
        if not re.match(r'^\d+$', (cells[0] or '').strip()):
            continue
        dm = DATE_RE.match((cells[13] or '').strip())
        dn = d.lower()
        if not dm or dn in JUNK_D:
            junk += 1
            continue
        if dn not in edn_ok:
            raise SystemExit('ERR %s district %r not in the dashboard EPI mapping (%s)'
                             % (DS, d, rec['name']))
        mo = dm.group(1)
        k = int(NUM_RE.match(cells[17].strip() or '0').group(0)) if cells[17].strip() else 0
        ag = {}
        for a, col in AG_COL.items():
            s = cells[col].strip()
            ag[a] = int(NUM_RE.match(s).group(0)) if s and NUM_RE.match(s) else 0
        htr = (cells[15] or '').strip().lower() == 'yes'
        r = rows.setdefault((mo, dn), [0, 0] + [0] * len(AGS) + [0, 0])
        r[0] += 1
        r[1] += k
        for i, a in enumerate(AGS):
            r[2 + i] += ag[a]
        if htr:
            r[-2] += 1
            r[-1] += k
        n += 1
    print('# rca %s: %d visits, %d month-districts, %d junk rows skipped'
          % (rec['name'], n, len(rows), junk))
    return rows


def build(cfg):
    e = cfg['auto'][DS]
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no RCA_Report files under %s' % (DS, e['roots']))
    edm = _epicache.edmap(cfg['repo'])
    edn_ok = {k.lower() for k in edm}
    cache = load_cache()
    by = {}
    used = []
    for rec in files:  # newest mtime first: first writer wins per (month, district)
        fid = srcutil.file_id(rec)
        if fid not in cache:
            cache[fid] = parse_file(rec, edn_ok)
            store_cache(cache)
        rows = cache[fid]
        used.append(rec['name'])
        for key, v in rows.items():
            by.setdefault(key, v)
    store_cache(cache)
    if not by:
        raise SystemExit('ERR %s no rows parsed' % DS)

    out_rows = []
    for (mo, dn) in sorted(by):
        v = by[(mo, dn)]
        ed = next(k for k in edm if k.lower() == dn)
        ds, dv = edm[ed]
        out_rows.append({'mo': mo, 'ed': ed, 'ds': ds, 'dv': dv, 'v': v[0], 'k': v[1],
                         **{a: v[2 + i] for i, a in enumerate(AGS)},
                         'hv': v[-2], 'hk': v[-1]})
    nv = sum(r['v'] for r in out_rows)
    nk = sum(r['k'] for r in out_rows)
    asof = None
    for rec in files:
        pr = period(rec)
        if pr:
            asof = max(asof or pr[1], pr[1])
    if not asof:  # RCA exports carry no From/To header - use the newest file's date
        import datetime
        asof = datetime.date.fromtimestamp(files[0]['mtime']).isoformat()
    molab = lambda mo: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug',
                        'Sep', 'Oct', 'Nov', 'Dec'][int(mo[5:7]) - 1] + ' ' + mo[:4]
    summary = ('%d visits, %s children checked, %d districts, %s..%s (%d files: %s)'
               % (nv, format(nk, ','), len({r['ed'] for r in out_rows}),
                  out_rows[0]['mo'], out_rows[-1]['mo'], len(used), used[0]))
    out = {'src': 'EPI-MIS RCA reports (%d files: %s)' % (len(used), ', '.join(used)),
           'asof': asof, 'from': molab(out_rows[0]['mo']), 'to': molab(out_rows[-1]['mo']),
           'ag': list(AGS), 'rows': out_rows}
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')  # interface parity: every match is loaded
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    out, summary = build(cfg)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'erca.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %s' % (DS, len(js), summary))


if __name__ == '__main__':
    main()
