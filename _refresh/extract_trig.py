"""Extract the EOC control-room trigger tables (const TRIG).

Usage: python _refresh/extract_trig.py [--source PATH] [--out PATH]
Prints one status line: OK trig <json chars> <summary> | ERR trig <reason>

Source: EOC portal > Control Room Trigger Feedback (https://www.eoc.gov.pk/trigger/feedback/),
campaign SNID Nov 2026, province KP, district roll-up tables. The portal is behind a
login, so the tables are not a Downloads export: `_refresh/cache/trig_<date>.json` holds
the three tables exactly as the signed-in portal printed them (a blank cell is stored
as 0), and this extractor validates and reshapes that snapshot.

Three tables are kept, because they are the only feedback-bearing triggers:

  mpqa   SNID Nov-26  UC micro-plan score below 90%
                      cols: need improvement | serious issues
  icm    SNID Nov-26  poorly covered area | missed area flagged by the monitors
  admin  SNID Nov-26  UC coverage below 70% | above 115%

A UC can be flagged for both ICM results, so the ICM snapshot rows carry a sixth field,
the count met by both, and total is the distinct flagged UCs (flagA + flagB - both).
The other three compliance triggers on the portal (missed children covered, still NA,
still refusal) carry no feedback and are not extracted.

Each table row is [district, flagA, flagB, total, feedback] ([... , both] for ICM).
The extractor asserts flagA + flagB == total (ICM: flagA + flagB - both == total) for
every row, feedback never exceeds total, and both totals equal the column sums. The
MPQA table is additionally
reconciled against the MPQA payload we already hold from the portal's own export: the
per-district needs-improvement and serious counts must match exactly, which is what
proves the scrape is the same round and not a stale page.

Payload: {"src","asof","note","t":[{"id","l","camp","rule","cols":[a,b],
          "tot":[a,b,total,feedback],
          "d":{district:[a,b,total,feedback]}}]}
"""
import argparse
import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import _epicache  # noqa: E402

LABELS = [
    ('mpqa', 'MPQA trigger'),
    ('icm', 'ICM trigger'),
    ('admin', 'Admin coverage trigger'),
]


def norm_map():
    """District keys of the dashboard, keyed by a case/space-insensitive form."""
    zd = _epicache.embedded_const(REPO, 'ZD', array=True)
    keys = sorted({r['d'] for r in zd if r.get('d')})
    return {k.upper().replace(' ', ''): k for k in keys}


def load(path):
    with io.open(path, encoding='utf-8') as f:
        return json.load(f)


def build(snap):
    names = norm_map()
    out = []
    for tid, label in LABELS:
        t = snap['tables'][tid]
        rows, seen = {}, set()
        overlap = 0
        for r in t['rows']:
            both = 0
            if len(r) == 6:
                raw, a, b, tot, fb, both = r
                overlap += both
            else:
                raw, a, b, tot, fb = r
            key = raw.upper().replace(' ', '')
            if key not in names:
                raise SystemExit('ERR trig unknown district %r in %s' % (raw, tid))
            d = names[key]
            if d in seen:
                raise SystemExit('ERR trig %s lists %s twice' % (tid, d))
            seen.add(d)
            if a + b - both != tot:
                raise SystemExit('ERR trig %s %s: %d+%d-both %d != %d'
                                 % (tid, d, a, b, both, tot))
            if both > min(a, b):
                raise SystemExit('ERR trig %s %s: both %d exceeds a flag column'
                                 % (tid, d, both))
            if fb > tot:
                raise SystemExit('ERR trig %s %s: feedback %d > total %d' % (tid, d, fb, tot))
            rows[d] = [a, b, tot, fb]
        ta, tb, ttot, tfb = t['tot'][1:]
        if ta != sum(v[0] for v in rows.values()) or tb != sum(v[1] for v in rows.values()):
            raise SystemExit('ERR trig %s: Total row %d/%d does not match the district sums %d/%d'
                             % (tid, ta, tb, sum(v[0] for v in rows.values()),
                                sum(v[1] for v in rows.values())))
        if ttot != sum(v[2] for v in rows.values()) or tfb != sum(v[3] for v in rows.values()):
            raise SystemExit('ERR trig %s: Total row %d/%d does not match the district sums %d/%d'
                             % (tid, ttot, tfb, sum(v[2] for v in rows.values()),
                                sum(v[3] for v in rows.values())))
        out.append({'id': tid, 'l': label, 'camp': t['camp'], 'rule': t['rule'],
                    'cols': t['cols'], 'tot': [ta, tb, ttot, tfb],
                    'd': dict(sorted(rows.items()))})
    return out


def cross_check_mpqa(tabs):
    """The MPQA trigger must agree with the MPQA export we already trust."""
    emp = _epicache.embedded_const(REPO, 'MPQA')
    if not emp or not emp.get('d'):
        return 'MPQA payload absent - cross-check skipped'
    t = next(x for x in tabs if x['id'] == 'mpqa')
    bad = []
    for d, v in t['d'].items():
        e = emp['d'].get(d)
        if e is None:
            bad.append('%s missing from MPQA payload' % d)
        elif [v[0], v[1]] != [e[3], e[4]]:
            bad.append('%s trigger %d/%d vs export %d/%d' % (d, v[0], v[1], e[3], e[4]))
    for d, e in emp['d'].items():
        if d not in t['d'] and (e[3] or e[4]):
            bad.append('%s in MPQA payload but not in trigger table' % d)
    if bad:
        raise SystemExit('ERR trig MPQA trigger disagrees with the export: ' + '; '.join(bad))
    return 'MPQA %d/%d matches the export' % (t['tot'][0], t['tot'][1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--source')
    ap.add_argument('--out', default=os.path.join(HERE, 'out', 'trig.json'))
    a = ap.parse_args()
    src = a.source
    if not src:
        hits = sorted(glob.glob(os.path.join(HERE, 'cache', 'trig_*.json')))
        if not hits:
            raise SystemExit('ERR trig no cache snapshot found')
        src = hits[-1]
    snap = load(src)
    try:
        tabs = build(snap)
        note = cross_check_mpqa(tabs)
    except SystemExit as e:
        print(str(e))
        return 1
    payload = {'src': snap['src'], 'asof': snap['asof'], 'note': snap['note'], 't': tabs}
    txt = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with io.open(a.out, 'w', encoding='utf-8', newline='') as f:
        f.write(txt)
    summary = ' | '.join('%s %s %d UCs %d feedback' % (t['id'], t['camp'], t['tot'][2], t['tot'][3])
                         for t in tabs)
    print('OK trig %d %s | %s' % (len(txt), summary, note))
    return 0


if __name__ == '__main__':
    sys.exit(main())
