"""Extend the dashboard's EPIM (const EPIM) with the 2024/2025 monthly EPI-MIS exports.

Companion to extract_emeta.py: same discovery, same per-file cache. Rows for the
pre-2026 months are aggregated per EPI district from the monthly exports (2025
arrives UC-wise, 2024 as district-level summaries - the shared cache handles both);
the months already embedded in index.html (2026) are kept verbatim (they were
built from that year's exports, which are no longer on disk). The EPI district ->
dashboard district(s) / division mapping is taken from the embedded EPIM rows;
an export district that is not in that mapping aborts the extract.

Usage: python _refresh/extract_epim.py [--out PATH]
Prints: SRC epim <newest file> | OK epim <json chars> <summary> | ERR epim <reason>
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _epicache
import srcutil

DS = 'epim'
AG = ('bcg', 'opv0', 'p1', 'p3', 'pcv3', 'ipv1', 'ipv2', 'rota2', 'mr1', 'mr2', 'fi')


def embedded_epim(repo):
    import json
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const EPIM = ')
    if i < 0:
        raise SystemExit('ERR %s const EPIM not found in index.html' % DS)
    j = s.find('];', i)
    return json.loads(s[i + len('const EPIM = '):j + 1].replace('<\\/', '</'))


def build(cfg):
    e = cfg['auto'][DS]
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no Consolidated files under %s' % (DS, e['roots']))
    cache = _epicache.load()
    by_mo = {}
    nnew, warned = 0, set()
    for rec in files:
        fid = srcutil.file_id(rec)
        if fid in cache:
            rec_o = cache[fid]
        else:
            print('# epim parsing %s ...' % rec['name'])
            try:
                rec_o = _epicache.read_consolidated(rec)
            except Exception as ex:
                cache[fid] = 'ERR: %s' % str(ex).split(chr(10))[0][:120]
                if rec['name'] not in warned:
                    print('WARN epim skipped %s (cannot parse)' % rec['name'])
                    warned.add(rec['name'])
                continue
            cache[fid] = rec_o if rec_o is not None else False
            if rec_o is not None:
                nnew += 1
        if isinstance(rec_o, dict) and rec_o['mo'] < '2026':
            # 2026 months come from the embedded payload, not these files
            by_mo.setdefault(rec_o['mo'], {}).update(rec_o['ed'])
    _epicache.store(cache)
    if not by_mo:
        raise SystemExit('ERR %s no pre-2026 monthly exports found' % DS)

    old = embedded_epim(cfg['repo'])
    dmap = {}
    for r in old:
        dmap[r['ed']] = r
    rows = [r for r in old if r['mo'] >= '2026']
    unknown = sorted({ed for eds in by_mo.values() for ed in eds} - set(dmap))
    if unknown:
        raise SystemExit('ERR %s districts not in the embedded EPIM mapping: %s' % (DS, unknown))
    added = 0
    for mo in sorted(by_mo):
        for ed in sorted(by_mo[mo]):
            v = by_mo[mo][ed]
            ref = dmap[ed]
            rows.append({'mo': mo, 'ed': ed, 'ds': ref['ds'], 'dv': ref['dv'],
                         'n': v['n'], 's': v['s'],
                         **{k: v[k] for k in AG}})
            added += 1
    rows.sort(key=lambda r: (r['mo'], r['ed']))
    n25 = len({r['mo'] for r in rows if r['mo'] < '2026'})
    summary = '%d rows: %d embedded 2026 + %d new (pre-2026: %d months x %d districts)' % (
        len(rows), len(old), added, n25, len(dmap))
    return rows, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')  # interface parity: every match is loaded
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    out, summary = build(cfg)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'epim.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %s' % (DS, len(js), summary))


if __name__ == '__main__':
    main()
