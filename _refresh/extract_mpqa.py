"""Extract the micro-plan quality assessment (MPQA) scoring summary (const MPQA).

Usage: python _refresh/extract_mpqa.py [--source PATH] [--out PATH]
Prints one status line: OK mpqa <json chars> <summary> | ERR mpqa <reason>

Source: EOC dashboard > Campaign > Pre Campaign > Micro Plan Scoring, exported as
`Micro_Plan_Scoring__<date>_<time>.xls` (an HTML table) into Downloads. The portal
re-saves the same table under a new timestamp, so the same round can appear as two
byte-identical files; the newest that parses wins.

WHAT MPQA IS (owner, 25-Oct-2026): the UC list is a **targeted sample** - picked at
random among low-performing UCs or UCs flagged on some other indicator - and scoring
every UC of a district is **not a requirement**. So "assigned / campaign UCs" is a
sampling share, never a coverage target, and the pass / needs-improvement / serious
shares describe deliberately problem-selected micro-plans, so they are not a
province-wide micro-plan quality rate either. The one figure that is an obligation is
completing the assigned list (reported / assigned).

Two shapes of the same round are read and reconciled:

District summary (as first seen 24-Oct-2026) - three stacked header rows, one row per
district and a `Total` row:
  Province | District | #UCs Planned | #UCs Assessed | %UCs Assessed |
  then, under "MPQA Assessed Results Breakdown", six columns in pairs of # and %:
  >=90 Pass | >= 70 & <90 Need Improvement | <70 Serious Issues

UC detail (as first seen 25-Oct-2026) - 26 columns, one row per assigned UC:
  Province | District | Tehsil | UC | UC Code | MPQA Reported | Desk Review % |
  Field Validation % | Over-all % | then 10 "Desk Review Score" and 7 "Field
  Validation Score" item columns.
`MPQA Reported` is `Yes`, `No` or (seen once, TANK/SARANGZOONA) `Partial`, and a
Partial row can carry a desk-review value with no Over-all %.

Reconciliation, asserted per district and on the totals: assigned = Yes + Partial,
pass = Over-all >= 90, needs improvement = 70-89, serious = < 70 **plus** any reported
row with no Over-all % (the portal bands the Partial row into serious issues). Only
the UC detail passes the item columns through as far as the three headline scores:
the export's header row lists 20 checklist questions over 17 score columns, so an item
label cannot be tied to a column with certainty and the per-item scores are not
published.

Only the counts are kept - the percentages are recomputed by the dashboard from
them (the repo convention). The extractor aborts unless, for every row and for the
Total row, pass + need + serious equals the assessed count, assessed never exceeds
planned, and the recomputed percentages land on the portal's printed values. The
portal prints no campaign tag, so the round label is taken from the dashboard's own
SND scope the same way the NEAP payload does it, and the district names are checked
against that scope.

Exports of this report name from other rounds (2024-10-09 district-wise with
per-item score columns, 2024-10-14 and 2025-12-12 UC-wise) are refused rather than
blended into this payload.

Payload: {"src","asof","gen","camp","n","thr":[90,70],"band":[labels],
          "tot":[5 counts], "st":["reported","partial","assigned, not yet reported"],
          "d":{district:[assigned,reported,pass,need,serious]},
              - the portal's "Planned" and "Assessed" columns, which are really
                UCs assigned for MPQA and UCs reported
          "u":{"src","asof","t":[tehsils],"r":[[district,tehsilIdx,uc,code,state,
              desk,field,overall],...]}}
              - "u" is absent when no same-round UC export is in Downloads
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
# ... and for the UC-level shape (the first nine cells of its top header row)
UC_HEAD = ['provincename', 'districtname', 'tehsilname', 'ucname', 'uccode',
           'mpqareported', 'deskreview', 'fieldvalidation', 'overall']
# MPQA Reported -> payload state code
SMAP = {'Yes': 0, 'Partial': 1, 'No': 2}
STATE = ['reported', 'partial', 'assigned, not yet reported']
BLANK = ('', '-', 'N/A', 'NA')


def norm_head(h):
    return [re.sub(r'[^a-z0-9]', '', c.lower()) for c in h]


def rows_of(path):
    raw = srcutil.read_text(path)
    rows = cells_html(path) if '<tr' in raw[:4000].lower() else cells_csv(path)
    return [r for r in rows if any(c for c in r)]


def find_head(rows, want):
    for i, r in enumerate(rows[:8]):
        if norm_head(r)[:len(want)] == want:
            return i
    return None


def parse(path):
    """-> body rows of the district-summary MPQA export, or None for any other shape."""
    rows = rows_of(path)
    if not rows:
        return None
    hi = find_head(rows, HEAD)
    if hi is None:
        return None
    if len(rows) < hi + 3 or len(rows[hi + 1]) < 3:
        return None
    sub = [re.sub(r'\s+', ' ', c).strip() for c in rows[hi + 1]]
    if 'Pass' not in sub[0] or 'Serious' not in sub[-1]:
        return None
    body = [r for r in rows[hi + 3:] if len(r) >= 11]
    return body if body else None


def pct_of(v):
    """One score column of the UC export -> float, int when whole, None when blank."""
    t = ('' if v is None else str(v)).replace(',', '').strip()
    if t in BLANK:
        return None
    try:
        x = float(t)
    except ValueError:
        raise SystemExit('ERR mpqa UC export score column is %r, want a percentage' % v)
    return int(x) if x == int(x) else round(x, 2)


def uc_rows(path):
    """-> (tehsil list, UC rows) of the UC-level MPQA export, or None for any other shape.

    The export's item columns are read but never published: its header lists 20
    checklist questions over 17 score columns, so no item label can be tied to a
    column with certainty. Only identity, the reported state and the three headline
    scores survive."""
    rows = rows_of(path)
    hi = find_head(rows, UC_HEAD)
    if hi is None or len(rows) < hi + 4:
        return None
    body = [r for r in rows[hi + 3:] if len(r) >= 9]
    if not body:
        return None
    base = os.path.basename(path)
    out, tehsils = [], []
    for r in body:
        prov, dn, tn, uc, code, rep = [x.strip() for x in r[:6]]
        if prov.upper() not in ('KP', 'KHYBER PAKHTUNKHWA'):
            raise SystemExit('ERR mpqa %s row %r is not a KP district' % (base, prov))
        dn = RENAME.get(dn.upper(), dn)
        if rep not in SMAP:
            raise SystemExit('ERR mpqa %s gives MPQA Reported %r for %s, want Yes / No / Partial'
                             % (base, rep, uc))
        desk, fieldv, over = [pct_of(x) for x in r[6:9]]
        if rep == 'No' and any(x is not None for x in (desk, fieldv, over)):
            raise SystemExit('ERR mpqa %s is not reported yet carries scores %s' % (uc, [desk, fieldv, over]))
        if rep == 'Yes' and over is None:
            raise SystemExit('ERR mpqa %s is reported with no Over-all %%' % uc)
        if tn not in tehsils:
            tehsils.append(tn)
        out.append({'d': dn, 't': tehsils.index(tn), 'u': uc, 'c': code, 's': SMAP[rep],
                    'dk': desk, 'fv': fieldv, 'ov': over})
    codes = [x['c'] for x in out]
    if len(set(codes)) != len(codes):
        dup = [c for c in set(codes) if codes.count(c) > 1]
        raise SystemExit('ERR mpqa %s repeats UC code(s) %s' % (base, dup[:5]))
    if not all(x['c'] for x in out):
        raise SystemExit('ERR mpqa %s has a UC row with no UC code' % base)
    return tehsils, out


def band_of(ov):
    if ov is None:
        return 'ns'
    if ov >= THR[0]:
        return 'pas'
    if ov >= THR[1]:
        return 'ni'
    return 'si'


def reconcile(d, tot, urows, base):
    """Cross-check the UC export against the district summary, asserted both ways.

    The portal bands a reported row that has no Over-all % (the Partial rows) into the
    serious bucket, so serious = under-70 + no-score; that rule is what makes the two
    files agree, and it is asserted here rather than assumed."""
    per = {}
    for x in urows:
        g = per.setdefault(x['d'], dict(pl=0, rp=0, pas=0, ni=0, si=0, ns=0))
        g['pl'] += 1
        if x['s'] == 2:
            continue
        g['rp'] += 1
        g[band_of(x['ov'])] += 1
    only_d, only_u = sorted(set(d) - set(per)), sorted(set(per) - set(d))
    if only_d or only_u:
        raise SystemExit('ERR mpqa %s and the district summary disagree: %s only in the summary, '
                         '%s only in the UC export' % (base, only_d[:5], only_u[:5]))
    for dn in sorted(d):
        g, mine = per[dn], None
        mine = [g['pl'], g['rp'], g['pas'], g['ni'], g['si'] + g['ns']]
        if mine != d[dn]:
            raise SystemExit('ERR mpqa %s: district summary %s, UC export %s (planned, reported, '
                             'pass, need, serious)' % (dn, d[dn], mine))
    calc = [sum(per[x][k] for x in per) for k in ('pl', 'rp', 'pas', 'ni')]
    calc.append(sum(per[x]['si'] + per[x]['ns'] for x in per))
    if calc != tot:
        raise SystemExit('ERR mpqa totals: district summary %s, UC export %s' % (tot, calc))
    return per


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


def build(path, repo, uc_path=None):
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
           'thr': THR, 'band': BAND, 'd': d, 'tot': tot, 'st': STATE}
    if uc_path:
        got = uc_rows(uc_path)
        if got is None:
            raise SystemExit('ERR mpqa %s is not the UC-level MPQA export'
                             % os.path.basename(uc_path))
        tehsils, urows = got
        if len(urows) != tot[0]:
            raise SystemExit('ERR mpqa %s lists %d UCs, the district summary plans %d'
                             % (os.path.basename(uc_path), len(urows), tot[0]))
        reconcile(d, tot, urows, os.path.basename(uc_path))
        urec = srcutil.stat_rec(uc_path)
        out['u'] = {'src': os.path.basename(uc_path),
                    'asof': datetime.datetime.fromtimestamp(urec['mtime']).strftime('%d-%b-%Y %H:%M'),
                    't': tehsils,
                    'r': [[x['d'], x['t'], x['u'], x['c'], x['s'], x['dk'], x['fv'], x['ov']]
                          for x in urows]}
    pending = tot[0] - tot[1]
    summary = ('%s, %d districts, %s of %s assigned UCs reported (%s%%) - %s pass, %s needs '
               'improvement, %s serious issues%s'
               % (camp or 'SND', len(d), format(tot[1], ','), format(tot[0], ','),
                  round(pct(tot[1], tot[0]), 1), format(tot[2], ','), format(tot[3], ','),
                  format(tot[4], ','),
                  ('' if not uc_path else ', %d still to report' % pending)))
    return out, summary


def first_of(cands, shape):
    """Newest candidate that parses as `shape`, or None."""
    for rec in cands:
        p = rec['path']
        if os.path.exists(p) and shape(p) is not None:
            return rec
    return None


def uc_partner(cands, d_rec):
    """The UC-level export of the district summary's own round, or None.

    Matching is by export date, not by row counts: a same-round pair that fails to
    reconcile aborts the run rather than quietly falling back to the summary alone,
    while an older UC export is skipped because it describes a different assigned list."""
    day = datetime.date.fromtimestamp(d_rec['mtime'])
    near = [r for r in cands if os.path.exists(r['path'])
            and datetime.date.fromtimestamp(r['mtime']) == day and uc_rows(r['path']) is not None]
    return min(near, key=lambda r: abs(r['mtime'] - d_rec['mtime'])) if near else None


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
    # whichever file --source points at may be either shape; each role finds its own
    d_rec = first_of(cands, parse)
    if d_rec is None:
        raise SystemExit('ERR mpqa no district-wise MPQA summary among %d candidate files'
                         % len(cands))
    u_rec = uc_partner(cands, d_rec)
    mpqa, summary = build(d_rec['path'], cfg['repo'], u_rec['path'] if u_rec else None)
    js = srcutil.dumps(mpqa)
    dest = a.out or os.path.join(srcutil.OUT, 'mpqa.json')
    srcutil.write_text(dest, js)
    print('SRC mpqa district %s' % d_rec['path'])
    if u_rec:
        print('SRC mpqa UC      %s' % u_rec['path'])
    print('OK mpqa %d %s' % (len(js), summary))


if __name__ == '__main__':
    main()
