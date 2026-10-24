"""Extract the micro-plan quality assessment (MPQA) scoring summary (const MPQA).

Usage: python _refresh/extract_mpqa.py [--source PATH] [--out PATH]
Prints one status line: OK mpqa <json chars> <summary> | ERR mpqa <reason>

Source: EOC dashboard > Campaign > Pre Campaign > Micro Plan Scoring, exported as
`Micro_Plan_Scoring__<date>_<time>.xls` (an HTML table) into Downloads. The portal
re-saves the same table under a new timestamp, so the same round can appear as two
byte-identical files; the newest that parses wins.

Shape (as first seen 24-Oct-2026): three stacked header rows, then one row per
district and a `Total` row.
  Province | District | #UCs Planned | #UCs Assessed | %UCs Assessed |
  then, under "MPQA Assessed Results Breakdown", six columns in pairs of # and %:
  >=90 Pass | >= 70 & <90 Need Improvement | <70 Serious Issues

Only the counts are kept - the percentages are recomputed by the dashboard from
them (the repo convention). The extractor aborts unless, for every row and for the
Total row, pass + need + serious equals the assessed count, assessed never exceeds
planned, and the recomputed percentages land on the portal's printed values. The
portal prints no campaign tag, so the round label is taken from the dashboard's own
SND scope the same way the NEAP payload does it, and the district names are checked
against that scope.

Older exports of the same report name (2024-10-09 district-wise, 2024-10-14 and
2025-12-12 UC-wise, with per-checklist-item score columns) are a different shape and
are refused here rather than blended into this payload.

Payload: {"src","asof","gen","camp","n","thr":[90,70],"band":[labels],
          "d":{district:[planned,assessed,pass,need,serious]},"tot":[5 counts]}
"""
import argparse
import datetime
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil
from extract_neap import RENAME, cells_csv, cells_html, snd_scope

DS = 'mpqa'
BAND = ['>=90 Pass', '70-89 Needs improvement', '<70 Serious issues']
THR = [90, 70]
# positionally-normalised header anchors for the district-summary shape
HEAD = ['provincename', 'districtname', 'ucsplanned', 'ucsassessed', 'ucsassessed']


def norm_head(h):
    return [re.sub(r'[^a-z0-9]', '', c.lower()) for c in h]


def rows_of(path):
    raw = srcutil.read_text(path)
    rows = cells_html(path) if '<tr' in raw[:4000].lower() else cells_csv(path)
    return [r for r in rows if any(c for c in r)]


def parse(path):
    """-> body rows of the district-summary MPQA export, or None for any other shape."""
    rows = rows_of(path)
    if not rows:
        return None
    hi = None
    for i, r in enumerate(rows[:8]):
        if norm_head(r)[:5] == HEAD:
            hi = i
            break
    if hi is None:
        return None
    if len(rows) < hi + 3 or len(rows[hi + 1]) < 3:
        return None
    sub = [re.sub(r'\s+', ' ', c).strip() for c in rows[hi + 1]]
    if 'Pass' not in sub[0] or 'Serious' not in sub[-1]:
        return None
    body = [r for r in rows[hi + 3:] if len(r) >= 11]
    return body if body else None


def val(v):
    t = ('' if v is None else str(v)).replace(',', '').strip()
    if t in ('', '-'):
        return None
    try:
        return float(t)
    except ValueError:
        raise SystemExit('ERR mpqa %r is not a number' % v)


def cnt(v, what, dn):
    x = val(v)
    if x is None or x != int(x) or x < 0:
        raise SystemExit('ERR mpqa %s for %s is %r, want a whole count' % (what, dn, v))
    return int(x)


def pct(a, b):
    return 0.0 if not b else 100.0 * a / b


def build(path, repo):
    body = parse(path)
    if body is None:
        raise SystemExit('ERR mpqa %s is not the district-wise MPQA summary'
                         % os.path.basename(path))
    scope, camp = snd_scope(repo)
    d, tot_row = {}, None
    for r in body:
        prov, dn = r[0].strip(), r[1].strip()
        if dn.upper() in ('', 'TOTAL', 'GRAND TOTAL'):
            if tot_row is not None:
                raise SystemExit('ERR mpqa %s has more than one total row' % os.path.basename(path))
            tot_row = r
            continue
        if prov.strip().upper() not in ('KP', 'KHYBER PAKHTUNKHWA'):
            raise SystemExit('ERR mpqa %s row %r is not a KP district' % (os.path.basename(path), prov))
        dn = RENAME.get(dn.upper(), dn)
        if dn in d:
            raise SystemExit('ERR mpqa %s lists %s twice' % (os.path.basename(path), dn))
        if dn not in scope:
            raise SystemExit('ERR mpqa district %r is not in the %s scope' % (dn, camp or 'SND'))
        planned = cnt(r[2], 'UCs planned', dn)
        assessed = cnt(r[3], 'UCs assessed', dn)
        b = [cnt(r[5 + 2 * j], BAND[j], dn) for j in range(3)]
        if assessed > planned:
            raise SystemExit('ERR mpqa %s assessed %d of %d planned' % (dn, assessed, planned))
        if sum(b) != assessed:
            raise SystemExit('ERR mpqa %s buckets %s add to %d, not the %d assessed'
                             % (dn, b, sum(b), assessed))
        # the portal's own printed percentages must agree with the counts
        printed = [val(r[4])] + [val(r[6 + 2 * j]) for j in range(3)]
        mine = [pct(assessed, planned)] + [pct(x, assessed) for x in b]
        for k, (p, m) in enumerate(zip(printed, mine)):
            if p is not None and abs(p - m) > 0.006:
                raise SystemExit('ERR mpqa %s percentage %d is %s on the portal, %s from the counts'
                                 % (dn, k, p, round(m, 2)))
        d[dn] = [planned, assessed] + b
    if tot_row is None:
        raise SystemExit('ERR mpqa %s has no Total row' % os.path.basename(path))
    tot = [cnt(tot_row[2], 'UCs planned (Total)', 'Total'), cnt(tot_row[3], 'UCs assessed (Total)', 'Total')]
    tot += [cnt(tot_row[5 + 2 * j], BAND[j] + ' (Total)', 'Total') for j in range(3)]
    calc = [sum(v[i] for v in d.values()) for i in range(5)]
    if tot != calc:
        raise SystemExit('ERR mpqa %s Total row %s does not match the district sum %s'
                         % (os.path.basename(path), tot, calc))
    if set(d) != scope:
        raise SystemExit('ERR mpqa %s covers %d of the %d scoped districts'
                         % (os.path.basename(path), len(d), len(scope)))
    mtime = datetime.datetime.fromtimestamp(os.stat(path).st_mtime)
    pkt = datetime.datetime.now()
    out = {'src': os.path.basename(path), 'asof': mtime.date().isoformat(),
           'gen': pkt.strftime('%d-%b-%Y %H:%M'), 'camp': camp or '', 'n': len(d),
           'thr': THR, 'band': BAND, 'd': d, 'tot': tot}
    summary = ('%s, %d districts, %s of %s planned UCs scored (%s%%) - %s pass, %s needs '
               'improvement, %s serious issues'
               % (camp or 'SND', len(d), format(tot[1], ','), format(tot[0], ','),
                  round(pct(tot[1], tot[0]), 1), format(tot[2], ','), format(tot[3], ','),
                  format(tot[4], ',')))
    return out, summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    cands = srcutil.discover(cfg['auto'][DS])
    if a.source:
        s_abs = os.path.normcase(os.path.abspath(a.source))
        cands = [srcutil.stat_rec(a.source)] + [
            c for c in cands if os.path.normcase(os.path.abspath(c['path'])) != s_abs]
    if not cands:
        raise SystemExit('ERR mpqa no Micro_Plan_Scoring files found under %s'
                         % cfg['auto'][DS]['roots'])
    # the portal re-saves one table under two timestamps, and identical mtimes would let
    # the credited filename flip between runs and re-stamp a payload that has not changed
    cands.sort(key=lambda r: (-r['mtime'], r['name']))
    tried = 0
    for rec in cands:
        p = rec['path']
        if not os.path.exists(p):
            continue
        tried += 1
        try:
            mpqa, summary = build(p, cfg['repo'])
        except SystemExit as e:
            if str(e).startswith('ERR mpqa %s is not' % os.path.basename(p)):
                # the family carries older UC-wise / item-score shapes; keep looking
                continue
            raise
        js = srcutil.dumps(mpqa)
        dest = a.out or os.path.join(srcutil.OUT, 'mpqa.json')
        srcutil.write_text(dest, js)
        print('SRC mpqa district %s' % p)
        print('OK mpqa %d %s' % (len(js), summary))
        return
    raise SystemExit('ERR mpqa no district-wise MPQA summary among %d candidate files' % tried)


if __name__ == '__main__':
    main()
