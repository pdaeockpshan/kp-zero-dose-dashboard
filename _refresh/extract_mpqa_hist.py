"""Build `const MPQAH` - MPQA results for every campaign round carried on the plate.

Usage: python _refresh/extract_mpqa_hist.py [--cache PATH] [--out PATH]
Prints one status line per round: OK mpqah <round> <chars> <summary> | ERR mpqah <reason>

Source: the EOC dashboard's two MPQA pages, read signed-in and saved by the agent to
`_refresh/cache/mpqa_hist_<date>.json` as {asof, harvested, src:{new,old}, rounds:{id:{d,u}}}:

  * MPQA (NEW)  https://www.eoc.gov.pk/analysis/mpqa/  - SNID Sept 2026 onward
  * MPQA (OLD)  https://www.eoc.gov.pk/analysis/microplanqualityassessment/ - May 2026 and earlier

The scoring format was revised between the two, so the pages carry different UC item
columns (17 questions on NEW, 21 on OLD) and neither can be read by the other's parser.
Only the first nine columns are shared - province, district, tehsil, UC, UC code, MPQA
Reported, desk %, field %, over-all % - and those are the only ones published, so the two
formats land in one shape without inventing a crosswalk between item columns.

The agent harvested, per round, the district-wise and UC-wise tables (dataview 2 and 3)
for: FEB-25, APR-25, MAY-25, SEP-25, OCT-25, DEC-25, FEB-26, APR-26, MAY-26 on OLD and
SEP-26, NOV-26 on NEW. That is every routine campaign from Feb-2025 to Nov-2026; the
plate offers earlier campaigns too and prints dashes for them.

Per round this extractor asserts, and refuses to emit on any mismatch:
  * every UC row's district has a district summary row, and every summary district has
    at least one UC row;
  * assigned (summary "#UCs Planned") equals the UC rows in the export;
  * reported (summary "#UCs Assessed") equals the rows whose MPQA Reported is Yes/Partial;
  * pass / needs improvement / serious recomputed from Over-all % equal the summary
    counts, with a reported row that has no Over-all % falling in serious (the portal's
    own banding of the partial rows);
  * UC codes are unique within a round.
`Cancelled from Planning` (seen in MAY-25, 36 UCs) counts as assigned and not reported,
and keeps its own state so the UC table can say so instead of calling it "No".

NOV-26 is cross-checked against the existing `const MPQA` payload (27 districts, 381
assigned UCs) and must match row for row; that payload still drives the pre-campaign card.

Payload: {"src","asof","gen","thr":[90,70],"band","st",
          "r":[{"c":campaign label in INDIC, "q":portal round id, "f":"new"|"old",
                "a":round as-of (harvest date), "n":[districts, UCs],
                "t":[assigned,reported,pass,need,serious],
                "d":{district:[assigned,reported,pass,need,serious]},
                "u":{ucCode:[state,overall]}}]}
State codes: 0 reported, 1 partial, 2 not reported, 3 cancelled from planning.
"""
import argparse
import datetime
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import srcutil
from extract_neap import RENAME

DS = 'mpqah'
THR = [90, 70]
BAND = ['>=90 Pass', '70-89 Needs improvement', '<70 Serious issues']
STATE = ['reported', 'partial', 'not reported', 'cancelled from planning']
SMAP = {'Yes': 0, 'Partial': 1, 'No': 2, 'Cancelled from Planning': 3}
# portal round id -> (campaign label in INDIC, format)
ROUNDS = [
    ('NOV-26-1', 'SNID Nov 2026', 'new'),
    ('SEP-26-1', 'SNID Sept 2026', 'new'),
    ('MAY-26-1', 'SNID May 2026', 'old'),
    ('APR-26-1', 'NID APR 2026', 'old'),
    ('FEB-26-1', 'NID FEB 2026', 'old'),
    ('DEC-25-1', 'NID DEC 2025', 'old'),
    ('OCT-25-1', 'NID OCT 2025', 'old'),
    ('SEP-25-1', 'SNID Sept 2025', 'old'),
    ('MAY-25-1', 'NID May 2025', 'old'),
    ('APR-25-1', 'NID APRIL 2025', 'old'),
    ('FEB-25-1', 'NID FEB 2025', 'old'),
]
BLANK = ('', '-', 'N/A', 'NA')


def num(v, what, who):
    t = ('' if v is None else str(v)).replace(',', '').strip()
    if t in BLANK:
        return None
    try:
        return float(t)
    except ValueError:
        raise SystemExit('ERR mpqah %s for %s is %r, want a number' % (what, who, v))


def whole(v, what, who):
    x = num(v, what, who)
    if x is None or x != int(x) or x < 0:
        raise SystemExit('ERR mpqah %s for %s is %r, want a whole count' % (what, who, v))
    return int(x)


def dash_name(dn):
    dn = dn.strip()
    return RENAME.get(dn.upper(), dn)


def band(ov):
    if ov is None:
        return 'ns'
    return 'pas' if ov >= THR[0] else 'ni' if ov >= THR[1] else 'si'


def build_round(rid, label, fmt, rec):
    """-> (payload record, summary). Aborts unless the two portal tables agree."""
    rows = [r for r in rec.get('d') or [] if len(r) >= 11]
    if not rows:
        raise SystemExit('ERR mpqah %s has no district rows' % rid)
    d = {}
    for r in rows:
        if r[0].strip().upper() not in ('KP', 'KHYBER PAKHTUNKHWA'):
            raise SystemExit('ERR mpqah %s row %r is not a KP district' % (rid, r[0]))
        dn = dash_name(r[1])
        if dn.upper() in ('', 'TOTAL', 'GRAND TOTAL'):
            continue
        if dn in d:
            raise SystemExit('ERR mpqah %s lists %s twice' % (rid, dn))
        planned = whole(r[2], 'UCs planned', dn)
        assessed = whole(r[3], 'UCs assessed', dn)
        b = [whole(r[5 + 2 * j], BAND[j], dn) for j in range(3)]
        if assessed > planned:
            raise SystemExit('ERR mpqah %s %s assessed %d of %d planned' % (rid, dn, assessed, planned))
        if sum(b) != assessed:
            raise SystemExit('ERR mpqah %s %s buckets %s add to %d, not the %d assessed'
                             % (rid, dn, b, sum(b), assessed))
        d[dn] = [planned, assessed] + b
    if not d:
        raise SystemExit('ERR mpqah %s has no district rows after the total' % rid)

    urows = [r for r in rec.get('u') or [] if len(r) >= 9]
    if not urows:
        raise SystemExit('ERR mpqah %s has no UC rows' % rid)
    u, per, seen = {}, {}, set()
    for r in urows:
        if r[0].strip().upper() not in ('KP', 'KHYBER PAKHTUNKHWA'):
            raise SystemExit('ERR mpqah %s UC row %r is not a KP district' % (rid, r[0]))
        dn = dash_name(r[1])
        code = r[4].strip()
        if not code:
            raise SystemExit('ERR mpqah %s has a UC row with no UC code (%s)' % (rid, r[3]))
        if code in seen:
            raise SystemExit('ERR mpqah %s repeats UC code %s' % (rid, code))
        seen.add(code)
        st = SMAP.get(r[5].strip())
        if st is None:
            raise SystemExit('ERR mpqah %s gives MPQA Reported %r for %s'
                             % (rid, r[5], r[3]))
        ov = num(r[8], 'Over-all %', code)
        if st == 2 and ov is not None:
            raise SystemExit('ERR mpqah %s %s is not reported yet carries %s%%' % (rid, code, ov))
        if st == 0 and ov is None:
            raise SystemExit('ERR mpqah %s %s is reported with no Over-all %%' % (rid, code))
        u[code] = [st, -1 if ov is None else (int(ov) if ov == int(ov) else round(ov, 2))]
        g = per.setdefault(dn, dict(pl=0, rp=0, pas=0, ni=0, si=0, ns=0))
        g['pl'] += 1
        if st in (0, 1):
            g['rp'] += 1
            g[band(ov)] += 1
    only_d, only_u = sorted(set(d) - set(per)), sorted(set(per) - set(d))
    if only_d or only_u:
        raise SystemExit('ERR mpqah %s: %s only in the summary, %s only in the UC export'
                         % (rid, only_d[:5], only_u[:5]))
    for dn in sorted(d):
        g = per[dn]
        mine = [g['pl'], g['rp'], g['pas'], g['ni'], g['si'] + g['ns']]
        if mine != d[dn]:
            raise SystemExit('ERR mpqah %s: %s summary %s, UC export %s (assigned, reported, '
                             'pass, need, serious)' % (rid, dn, d[dn], mine))
    tot = [sum(v[i] for v in d.values()) for i in range(5)]
    out = {'c': label, 'q': rid, 'f': fmt, 'n': [len(d), len(u)], 't': tot, 'd': d, 'u': u}
    summary = ('%s (%s) %d districts, %d UCs assigned, %d reported - %d pass, %d need, %d serious'
               % (rid, fmt, len(d), tot[0], tot[1], tot[2], tot[3], tot[4]))
    return out, summary, tot


def load_indic(repo):
    s = srcutil.read_text(os.path.join(repo, 'index.html'))
    i = s.find('INDIC = ')
    if i < 0:
        raise SystemExit('ERR mpqah const INDIC not found in index.html')
    line = s[i:s.index('\n', i)]
    ind = json.loads(line[len('INDIC = '):].rstrip().rstrip(';'))
    # Nov-26 is newer than the data pack, so its label lives on const CIN only
    i = s.find('CIN = ')
    if i >= 0:
        cin = json.loads(s[i + len('CIN = '):s.index('\n', i)].rstrip().rstrip(';'))
        if cin.get('camp', {}).get('l'):
            ind['camps'].append({'l': cin['camp']['l'], 'y': cin['camp'].get('y', '')})
    return ind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cache')
    ap.add_argument('--out')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    cache = a.cache
    if not cache:
        cands = sorted(os.listdir(os.path.join(cfg['repo'], '_refresh', 'cache')))
        cands = [c for c in cands if c.startswith('mpqa_hist_') and c.endswith('.json')]
        if not cands:
            raise SystemExit('ERR mpqah no _refresh/cache/mpqa_hist_*.json found')
        cache = os.path.join(cfg['repo'], '_refresh', 'cache', cands[-1])
    h = json.loads(srcutil.read_text(cache))
    got = h.get('rounds') or {}
    asof = h.get('asof') or ''
    ind = load_indic(cfg['repo'])
    camps = {c['l'] for c in ind['camps']}
    codes = {r[3] for r in ind['ucs']}

    recs, totals = [], {}
    for rid, label, fmt in ROUNDS:
        if rid not in got:
            raise SystemExit('ERR mpqah cache has no round %s' % rid)
        if label not in camps and rid != 'NOV-26-1':
            # Nov-26 is a future round: no plate row carries it yet, but its MPQA is the
            # one the pre-campaign card already uses, so it is carried for when it lands
            raise SystemExit('ERR mpqah %r is not a campaign label in INDIC' % label)
        rec, summary, tot = build_round(rid, label, fmt, got[rid])
        rec['a'] = asof
        match = sum(1 for c in rec['u'] if c in codes)
        print('OK mpqah %s %s (UC codes matched %d of %d in INDIC)'
              % (rid, summary, match, len(rec['u'])))
        recs.append(rec)
        totals[rid] = (rec, match)

    # NOV-26 must reproduce the published payload that drives the pre-campaign card
    nov, _ = totals['NOV-26-1']
    old_path = os.path.join(cfg['repo'], '_refresh', 'out', 'mpqa.json')
    if os.path.exists(old_path):
        old = json.loads(srcutil.read_text(old_path))
        if len(nov['d']) != len(old['d']):
            raise SystemExit('ERR mpqah NOV-26 has %d districts, const MPQA has %d'
                             % (len(nov['d']), len(old['d'])))
        for dn, vals in old['d'].items():
            want = [int(x) for x in vals]
            if nov['d'].get(dn) != want:
                raise SystemExit('ERR mpqah NOV-26 %s is %s on the portal, %s in const MPQA'
                                 % (dn, nov['d'].get(dn), want))
        nov_old_u = len(old.get('u', {}).get('r') or [])
        if nov_old_u and nov_old_u != len(nov['u']):
            raise SystemExit('ERR mpqah NOV-26 has %d UCs, const MPQA has %d'
                             % (len(nov['u']), nov_old_u))
        print('OK mpqah NOV-26 reproduces const MPQA row for row (%d districts, %d UCs)'
              % (len(nov['d']), len(nov['u'])))

    out = {'src': 'EOC MPQA pages (NEW from Sept-2026, OLD before)', 'asof': asof,
           'gen': datetime.datetime.now().strftime('%d-%b-%Y %H:%M'), 'thr': THR,
           'band': BAND, 'st': STATE, 'r': recs}
    js = srcutil.dumps(out)
    dest = a.out or os.path.join(srcutil.OUT, 'mpqah.json')
    srcutil.write_text(dest, js)
    t = [sum(r['t'][i] for r in recs) for i in range(5)]
    print('OK mpqah %d %d rounds, %s UCs assigned, %s reported across all rounds'
          % (len(js), len(recs), format(t[0], ','), format(t[1], ',')))


if __name__ == '__main__':
    main()
