"""Extend the dashboard's EMETA (const EMETA) with the 2025 monthly EPI-MIS exports.

Every Consolidated_Facility_Wise_Vaccination*.xls under the configured roots is a
single-month UC-wise export; its month is read from the file's own
"<h5>YYYY-MM - YYYY-MM</h5>" period header. The parsed per-district aggregates are
cached in _refresh/cache/epi25mon.pkl keyed by file id, so only new files pay the
pandas parse cost.

The months already embedded in index.html (2026) are kept verbatim; months parsed
from the exports are added (a re-parse of the same month replaces that month's
rows, newest file wins). Partial/reporting-rate flags stay on the 2026 months.

Usage: python _refresh/extract_emeta.py [--out PATH]
Prints: SRC epm <newest file> | OK epm <json chars> <summary> | ERR epm <reason>
"""
import argparse
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _epicache
import srcutil

DS = 'epm'
DASH = '\u2013'
PER = 'Jan 2025 ' + DASH + ' Sep 2026'


def embedded_emeta(repo):
    """Parse const EMETA out of index.html (brace-matched: months hold nested objects)."""
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('const EMETA = ')
    if i < 0:
        raise SystemExit('ERR %s const EMETA not found in index.html' % DS)
    j = i + len('const EMETA = ')
    depth, instr, esc = 0, False, False
    for k in range(j, len(s)):
        c = s[k]
        if instr:
            if esc:
                esc = False
            elif c == '\\':
                esc = True
            elif c == '"':
                instr = False
        elif c == '"':
            instr = True
        elif c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if not depth:
                return json.loads(s[j:k + 1].replace('<\\/', '</'))
    raise SystemExit('ERR %s const EMETA literal not terminated' % DS)


def build(cfg):
    e = cfg['auto'][DS]
    files = srcutil.discover(e)
    if not files:
        raise SystemExit('ERR %s no Consolidated files under %s' % (DS, e['roots']))
    cache = _epicache.load()
    parsed, nnew, warned = [], 0, set()

    def skip(rec, msg, cacheable):
        cache[fid_rec[0]] = cacheable
        if rec['name'] not in warned:
            print('WARN %s skipped %s (%s)' % (DS, rec['name'], msg))
            warned.add(rec['name'])

    for rec in files:
        fid = srcutil.file_id(rec)
        fid_rec = [fid]
        if fid in cache:
            rec_o = cache[fid]
            if not isinstance(rec_o, dict):
                skip(rec, rec_o if rec_o else 'no single-month period header', rec_o)
                continue
        else:
            print('# epm parsing %s ...' % rec['name'])
            try:
                rec_o = _epicache.read_consolidated(rec)
            except Exception as ex:
                skip(rec, 'cannot parse: %s' % str(ex).split(chr(10))[0][:120],
                     'ERR: %s' % str(ex).split(chr(10))[0][:120])
                continue
            if rec_o is None:
                skip(rec, 'no single-month period header', False)
                continue
            cache[fid] = rec_o
            nnew += 1
        if rec_o:
            parsed.append((rec, rec_o))
    _epicache.store(cache)

    by_mo = {}
    for rec, rec_o in sorted(parsed, key=lambda x: x[0]['mtime']):  # newest file wins
        by_mo[rec_o['mo']] = rec_o['ed']
    if not by_mo:
        raise SystemExit('ERR %s no single-month exports found' % DS)

    meta = embedded_emeta(cfg['repo'])
    have = {m['mo'] for m in meta.get('months') or []}
    mos = sorted(set(by_mo) - have)
    newm = [{'mo': mo, 'l': _lab(mo), 'pt': False, 'rp': None} for mo in mos]
    months = sorted((meta.get('months') or []) + newm, key=lambda m: m['mo'])
    if not months:
        raise SystemExit('ERR %s no months' % DS)
    meta['months'] = months
    meta['from'] = months[0]['mo']
    meta['to'] = months[-1]['mo']
    meta['per'] = _per(months[0]['mo'], months[-1]['mo'])
    partial = [m for m in months if m.get('pt')]
    meta['partial'] = partial[-1]['l'] if partial else meta.get('partial')
    n25 = sum(1 for m in months if m['mo'] < '2026')
    meta['src'] = ('epi_months_2025-01_2026-09 (2025: %d monthly UC-wise exports; '
                   '2026: Jan-Sep YTD, month view from the earlier build)' % n25)
    out = meta
    tot = sum(len(v) for v in by_mo.values())
    summary = '%d months (%d new: %s..%s), %d district-months from %d exports (%d parsed now)' % (
        len(months), len(mos), mos[0] if mos else '-', mos[-1] if mos else '-', tot,
        len(by_mo), nnew)
    return out, summary


def _lab(mo):
    names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    y, m = mo.split('-')
    return '%s %s' % (names[int(m) - 1], y)


def _per(m0, m1):
    return '%s %s %s %s' % (_lab(m0).split()[0], m0[:4], DASH, _lab(m1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')  # interface parity: every match is loaded
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    out, summary = build(cfg)
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'emeta.json')
    srcutil.write_text(dest, js)
    print('OK %s %d %s' % (DS, len(js), summary))


if __name__ == '__main__':
    main()
