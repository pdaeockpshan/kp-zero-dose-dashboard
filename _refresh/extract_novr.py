"""Extract the upcoming-campaign resource plan (const NOVR) from the RESOURCE PLAN csv.

Usage: python _refresh/extract_novr.py [--source PATH] [--out PATH]
Prints one status line: OK novr <json chars> <summary> | ERR novr <reason>
"""
import argparse
import csv
import datetime
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil

DS = 'novr'

# payload key order == csv column order after District
K = ['uc', 'tg', 'mtm', 'mtt', 'mtf', 'mta', 'mtu', 'mtfa', 'mtfu',
     'smm', 'smt', 'smf', 'sma', 'smu', 'smfa', 'smfu', 'cbm', 'cba']


def snd_districts(repo):
    """name -> target, from the dashboard's own SND payload (Final Scope)."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const SND = ')
    if i < 0:
        raise SystemExit('ERR novr const SND not found in index.html')
    j = s.find('\n', i)
    snd = json.loads(s[i + len('const SND = '):j].rstrip().rstrip(';'))
    return {r[0]: r[4] for r in snd['d']}, snd.get('n', '')


def num(c, where):
    t = ('' if c is None else str(c)).replace(',', '').strip()
    if t == '':
        return 0
    try:
        return int(t)
    except ValueError:
        raise SystemExit('ERR novr %s: %r is not an integer' % (where, c))


def build(src_path, cfg):
    raw = srcutil.read_bytes(src_path) if hasattr(srcutil, 'read_bytes') else open(src_path, 'rb').read()
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
    hi = None
    for i, r in enumerate(rows[:15]):
        if r and r[0].strip() == 'District':
            hi = i
            break
    if hi is None:
        raise SystemExit('ERR novr header row with leading "District" not found')
    hdr = [c.strip() for c in rows[hi]]
    if len(hdr) < 19:
        raise SystemExit('ERR novr header has %d columns, want >= 19' % len(hdr))
    if not any('UC' in c and 'Code' in c for c in hdr[1:2]):
        raise SystemExit('ERR novr column 1 is %r, want the UC Code column' % hdr[1])
    if not hdr[2].lower().startswith('admin target'):
        raise SystemExit('ERR novr column 2 is %r, want the Admin Target column' % hdr[2])

    dist, tots = {}, []
    for r in rows[hi + 1:]:
        if not r or all(('' if c is None else str(c).strip()) == '' for c in r):
            continue
        if len(r) < 19:
            r = list(r) + [''] * (19 - len(r))
        vals = [num(r[k + 1], 'row %r col %d' % (r[0], k + 1)) for k in range(18)]
        name = ('' if r[0] is None else str(r[0])).strip()
        if not name:
            tots.append(vals)
        else:
            if name in dist:
                raise SystemExit('ERR novr duplicate district row %r' % name)
            dist[name] = vals
    if not dist:
        raise SystemExit('ERR novr no district rows found')
    if len(tots) < 1:
        raise SystemExit('ERR novr no total row found')
    tot = tots[0]
    for k, t in enumerate(tots[1:]):
        if t != tot:
            raise SystemExit('ERR novr total rows disagree in column %d' % (k + 1))

    for k in range(18):
        ssum = sum(v[k] for v in dist.values())
        if ssum != tot[k]:
            raise SystemExit('ERR novr column %s: district sum %d != total row %d'
                             % (K[k], ssum, tot[k]))

    snd_t, snd_n = snd_districts(cfg['repo'])
    unknown = sorted(set(dist) - set(snd_t))
    missing = sorted(set(snd_t) - set(dist))
    if unknown or missing:
        raise SystemExit('ERR novr district names do not match the %s scope (add to rename/source): unknown=%s missing=%s'
                         % (snd_n or 'SND', unknown, missing))
    diffs = {n: dist[n][1] - snd_t[n] for n in dist if dist[n][1] != snd_t[n]}

    d = {}
    for n, v in dist.items():
        o = {}
        for k, key in enumerate(K):
            o[key] = v[k]
        d[n] = [o[key] for key in K]
    d = {n: d[n] for n in sorted(d, key=lambda n: -d[n][1])}

    mtime = datetime.datetime.fromtimestamp(os.stat(src_path).st_mtime)
    novr = {'src': os.path.basename(src_path), 'asof': mtime.date().isoformat(),
            'camp': snd_n, 'k': K, 'd': d, 'tot': tot}
    summary = ('%d districts, target %s, MT members %s, MT AICs %s, CBV %s, uc %d%s' % (
        len(d), format(tot[1], ','), format(tot[2], ','), format(tot[5], ','),
        format(tot[16], ','), tot[0],
        '' if not diffs else ', %d target diffs vs scope (%s)' % (
            len(diffs), ', '.join(sorted(diffs)[:3]))))
    return novr, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    rec = srcutil.stat_rec(a.source) if a.source else srcutil.newest(cfg['auto'][DS])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR novr no resource plan csv found under %s' % cfg['auto'][DS]['roots'])
    novr, summary = build(rec['path'], cfg)
    js = srcutil.dumps(novr)
    dest = a.out or os.path.join(srcutil.OUT, 'novr.json')
    srcutil.write_text(dest, js)
    print('SRC novr %s' % rec['path'])
    print('OK novr %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
