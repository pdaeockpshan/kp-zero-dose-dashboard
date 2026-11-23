"""Extend the dashboard's EPIM (const EPIM) with the 2023/2024/2025 monthly EPI-MIS exports.

Companion to extract_emeta.py: same discovery, same per-file cache. Rows for the
pre-2026 months are aggregated per EPI district from the monthly exports (2025
arrives UC-wise, 2024 as district-level summaries - the shared cache handles both)
and carry the full epi_ag panel. 2026 is rebuilt the same way now that every
2026 month has its own UC-wise export on disk (the embedded 2026 rows had been
frozen from an older build: core doses only, and a September that was a
part-report). A month with no on-disk export is still kept verbatim from the
embedded payload. The EPI district -> dashboard district(s) / division mapping is
taken from the embedded EPIM rows; an export district that is not in that mapping
aborts the extract.

Usage: python _refresh/extract_epim.py [--out PATH]
Prints: SRC epim <newest file> | OK epim <json chars> <summary> | ERR epim <reason>
"""
import argparse
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _epicache
import epi_ag
import srcutil

DS = 'epim'


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
        if isinstance(rec_o, dict):
            # One month can sit in several exports: the UC-wise one, and older district-level
            # downloads that disagree (Jan 2025: bcg 2,538 over its UCs, 2,119 in a summary).
            # UC-wise is the better copy when the two describe the same volume, but it is not
            # always the fuller read: Oct-2026 arrived first as a mid-month UC-wise download
            # (bcg 48,269) and later as the complete facility-wise month (bcg 100,728), so the
            # copy with the larger BCG total wins and the note says which and why.
            bcg = sum(v.get('bcg', 0) for v in rec_o['ed'].values())
            cand = (bool(rec_o.get('uc')), rec_o['ed'], rec['name'], bcg)
            have = by_mo.get(rec_o['mo'])
            if have is None:
                by_mo[rec_o['mo']] = cand
            else:
                hbcg = have[3]
                same = max(bcg, hbcg) and abs(bcg - hbcg) <= 0.01 * max(bcg, hbcg)
                if (same and cand[0] and not have[0]) or (not same and bcg > hbcg):
                    print('  note: %s replaces %s for %s (%s)'
                          % (rec['name'], have[2], rec_o['mo'],
                             'UC-wise, same volume' if same else 'fuller month: bcg %d vs %d'
                             % (bcg, hbcg)))
                    by_mo[rec_o['mo']] = cand
                elif rec['name'] != have[2]:
                    print('  note: %s also carries %s - keeping %s (bcg %d vs %d)'
                          % (rec['name'], rec_o['mo'], have[2], hbcg, bcg))
    _epicache.store(cache)
    if not by_mo:
        raise SystemExit('ERR %s no monthly exports found' % DS)

    old = embedded_epim(cfg['repo'])
    dmap = {}
    for r in old:
        dmap[r['ed']] = r
    # every month with an export is rebuilt from it; a month whose export is not on disk
    # keeps the embedded rows rather than disappearing from the year
    rows = [r for r in old if r['mo'] not in by_mo]
    unknown = sorted({ed for recs in by_mo.values() for ed in recs[1]} - set(dmap))
    if unknown:
        raise SystemExit('ERR %s districts not in the embedded EPIM mapping: %s' % (DS, unknown))
    added = 0
    for mo in sorted(by_mo):
        for ed in sorted(by_mo[mo][1]):
            v = by_mo[mo][1][ed]
            ref = dmap[ed]
            rows.append({'mo': mo, 'ed': ed, 'ds': ref['ds'], 'dv': ref['dv'],
                         'n': v['n'], 's': v['s'],
                         **{k: v[k] for k in epi_ag.KEYS if k in v}})
            added += 1
    rows.sort(key=lambda r: (r['mo'], r['ed']))
    extk = {a[0] for a in epi_ag.EXT}
    ext = len({k for r in rows for k in r if k in extk})
    summary = ('%d rows: %d rebuilt from %d monthly exports (%d months) + %d kept from the '
               'embedded payload, %d extra doses' % (
                   len(rows), added, len(by_mo), len(by_mo), len(rows) - added, ext))
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
