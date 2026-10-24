"""Extract the PTP field-monitoring payload (const PTPM) from the three HRMP checklist exports.

Sources (all in the HRMP Raw IDIMS folder, all exported 21-Apr-2025):
  PTPs-STPs_Monitoring_Checklist-176   one row per monitoring visit to a transit point
  PTPs-STPs_Spot_Survey_Checklist-52   one row per spot survey at a transit point
  PTPs-STPs_Logistic_Check_List-51     one row per logistics check of a post's equipment

They are aggregated to district x year and district x month, keyed on the same district index and the
same month-slot arithmetic as const PTP, so the PTP tab can put both grids on one period picker.

Post identity: the checklist exports carry `ptp_loc`, which is the coverage panel's Site_ID - 250 of
258 monitored posts, 450 of 460 surveyed posts and 358 of 365 logistics-checked posts are on the
Oct-2026 panel. The rest are counted as off-panel instead of dropped, because a post can be maintained
off the panel and still be visited.

Window: monitoring ran Sep-2024 to Apr-2025 and the other two exports Nov-2021 to Apr-2025, so the
field data stops 18 months before the reporting panel does. No period here overlaps Oct-2026; the UI
has to say that rather than draw an empty 2026.

Held out of the payload deliberately:
  person and place detail        surveyor_name, Surveyor Email, designation, fk_user_id, org_name,
                                 ptp_name, latitude/longitude/altitude/accuracy and every *_remarks
                                 and comments field - this is a public site.
  shift, docs_avail, app_loc,
  post_identity, team_identity,
  security_pres, sup_visit,
  secu_assist1, site_type,
  incoming_type                  integer answer codes with no caption in the export or in the three
                                 .twbx workbooks that ship beside it; nothing local decodes them.
  teams_trained ... vacc_match   eight attribute columns that agree with teams_monitored row for row
                                 to within 0.3-0.8% - the form mirrors one answer across them, so
                                 publishing them would create eight indicators out of one.
  total_team, transit_teams      sane in 15,094 rows and absurd in the rest (202 teams at a post
                                 where 2 were present, 141 where 1 was); held until IDIMS confirms.
  up_to_10, above_10, up_to_5,
  up_to_5_fm, *_fm, nofm, nofm_5,
  nofm_10, vnfm, vnfm_5, other   two survey designs in one table: the up_to_10 family is filled in
                                 233 of 20,219 rows (all site_type 9) and the up_to_5 family in
                                 19,986 (all site_type 1), and no label defines either.
  the 15 logistics item families (ilr, ilrn, ref, cab, bann, jack, pcap, id, paper, stand, cooler,
                                 vcarr, humber, chair, other, each x total/available/workable/
                                 nrepair/nreplace) - abbreviations with no caption, and available
                                 exceeds total in 846 family rows, so the three tiers are not a
                                 hierarchy and cannot be summed across families.

What is published is counts only: checklists, surveys, logistics checks, the distinct posts each one
reached, and the teams the monitor recorded as present and as monitored.

Usage: python _refresh/extract_ptpm.py [--out PATH]
Prints one SRC line per source and OK ptpm <json chars> <summary>.
"""
import argparse
import csv
import datetime
import fnmatch
import io
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

DS = 'ptpm'
MONS = {m: i + 1 for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}
STEMS = {'mon': 'PTPs-STPs_Monitoring_Checklist',
         'spot': 'PTPs-STPs_Spot_Survey_Checklist',
         'log': 'PTPs-STPs_Logistic_Check_List'}
LABEL = {'mon': 'monitoring checklists', 'spot': 'spot surveys', 'log': 'logistics checks'}
# monitoring keys its period on the date the visit was conducted; the other two only carry the
# timestamp the entry was made, so their month is an entry month and the caption says so.
DATECOL = {'mon': 'date_conducted', 'spot': None, 'log': None}
MEAS = {'mon': ['mchk', 'mpst', 'moff', 'mtm', 'mtp'],
        'spot': ['schk', 'spst', 'soff', 'ssick', 'sref', 'smiss', 'sload'],
        'log': ['lchk', 'lpst', 'loff']}
COLMAP = {'mon': {'mtm': 'teams_monitored', 'mtp': 'present_teams'},
          'spot': {'ssick': 'sick_5', 'sref': 'refused_5', 'smiss': 'ptp_missed_5',
                   'sload': 'over_loading_5'},
          'log': {}}
CHK = {'mon': 'mchk', 'spot': 'schk', 'log': 'lchk'}
PST = {'mon': 'mpst', 'spot': 'spst', 'log': 'lpst'}
OFF = {'mon': 'moff', 'spot': 'soff', 'log': 'loff'}
MK = MEAS['mon'] + MEAS['spot'] + MEAS['log']
IDX = {k: i for i, k in enumerate(MK)}


def num(x):
    x = (x or '').strip().replace(',', '')
    if not x or x == '\\N':
        return None
    m = re.match(r'^(-?\d+(?:\.\d+)?)', x)
    return float(m.group(1)) if m else None


def mkey(s):
    """'2024-08-28' or '28-Aug-2024  14:52:40' -> 202408, else None."""
    for tok in (s or '').strip().split():
        p = tok.split('-')
        if len(p) != 3:
            continue
        if len(p[0]) == 4 and p[0].isdigit() and p[1].isdigit():
            return int(p[0]) * 100 + int(p[1])
        if p[1] in MONS and len(p[2]) == 4 and p[2].isdigit():
            return int(p[2]) * 100 + MONS[p[1]]
    return None


def roster_posts(cfg):
    """{post id: IDIMS district spelling} from the same coverage export const PTP is built from."""
    rec = srcutil.newest(cfg['auto']['ptp'])
    if not rec or not os.path.exists(rec['path']):
        raise SystemExit('ERR ptpm no PTP coverage export found, so the post roster the monitoring '
                         'rows join to cannot be built')
    out = {}
    with io.open(rec['path'], encoding='utf-8-sig', errors='replace', newline='') as fh:
        for r in csv.DictReader(fh, delimiter='\t'):
            if (r.get('Province') or '').strip() != 'KP':
                continue
            pid = (r.get('Site_ID') or '').strip() or (r.get('ID') or '').strip()
            if pid:
                out.setdefault(pid, (r.get('District') or '').strip())
    if len(out) < 500:
        raise SystemExit('ERR ptpm the coverage export yields only %d post ids - the roster join '
                         'would be meaningless' % len(out))
    return out, os.path.basename(rec['path'])


def collect(path, src, alias, years, roster):
    """One export into district x year and district x month cells, plus the post bookkeeping."""
    with io.open(path, encoding='utf-8-sig', errors='replace') as fh:
        h = next(csv.reader(fh))
    ix = {c: i for i, c in enumerate(h)}
    dcols = COLMAP[src]
    need = ['district_name', 'ptp_loc', 'unique_id', 'date_created'] + list(dcols.values())
    if DATECOL[src]:
        need.append(DATECOL[src])
    miss = sorted({c for c in need if c not in ix})
    if miss:
        raise SystemExit('ERR ptpm %s has no %s column - the export changed shape'
                         % (os.path.basename(path), ', '.join(miss)))

    z = lambda: [0] * len(MK)  # noqa: E731
    cells, mcells = defaultdict(z), defaultdict(z)
    pY, pM = defaultdict(set), defaultdict(set)
    ever, everoff, pdist = defaultdict(set), defaultdict(set), defaultdict(set)
    read = kept = 0
    drop, dq = Counter(), Counter()
    seen = set()
    with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
        rd = csv.reader(fh)
        next(rd, None)  # the header is not a row; counting it would post a district that does not exist
        for row in rd:
            if len(row) != len(h):
                drop['short row'] += 1
                continue
            read += 1
            uid = row[ix['unique_id']].strip()
            if uid in seen:
                drop['repeated unique_id'] += 1
                continue
            seen.add(uid)
            dn = (row[ix['district_name']] or '').strip()
            a = alias.get(dn) or alias.get(dn.upper())
            if not a:
                drop['district not on the PTP tab'] += 1
                continue
            ym = mkey(row[ix[DATECOL[src]]]) if DATECOL[src] else None
            if ym is None:
                ym = mkey(row[ix['date_created']])
            if ym is None:
                drop['no readable date'] += 1
                continue
            if ym // 100 not in years:
                drop['year outside the PTP window'] += 1
                continue
            if DATECOL[src]:
                ce = mkey(row[ix['date_created']])
                if ce is not None and ce != ym:
                    dq['visit month and entry month differ'] += 1
            kept += 1
            pid = (row[ix['ptp_loc']] or '').strip()
            on = pid in roster
            yi = years.index(ym // 100)
            yk, mk = (a[0], yi), (a[0], yi * 12 + ym % 100 - 1)
            for k in MEAS[src]:
                if k == CHK[src]:
                    v = 1
                elif k in (PST[src], OFF[src]):
                    continue
                else:
                    raw = num(row[ix[dcols[k]]])
                    v = 0 if raw is None else int(round(raw))
                    if raw is not None and raw != v:
                        dq['%s is not a whole number' % dcols[k]] += 1
                cells[yk][IDX[k]] += v
                mcells[mk][IDX[k]] += v
            pY[yk].add((on, pid))
            pM[mk].add((on, pid))
            (ever if on else everoff)[a[0]].add(pid)
            if on:
                pdist[pid].add(a[0])
                if roster[pid].upper() != dn.upper():
                    dq['post recorded under a district the panel places elsewhere'] += 1
    # distinct posts belong to the cell, not to the rows: a post visited three times in a month is
    # one post reached, and that is the only reason the sets are kept alongside the sums.
    for book, tgt in ((pY, cells), (pM, mcells)):
        for key, ps in book.items():
            tgt[key][IDX[PST[src]]] = len({p for on, p in ps if on})
            tgt[key][IDX[OFF[src]]] = len({p for on, p in ps if not on})
    moved = {pid for pid, ds in pdist.items() if len(ds) > 1}
    yms = sorted({k[1] for k in mcells})
    return dict(cells=cells, mcells=mcells, ever=ever, everoff=everoff, read=read, kept=kept,
                drop=drop, dq=dq, posts=len(pdist), moved=len(moved),
                first=years[yms[0] // 12] * 100 + yms[0] % 12 + 1,
                last=years[yms[-1] // 12] * 100 + yms[-1] % 12 + 1)


def build(paths, repo):
    """paths = {src: path}; the district index, month slots and post roster all come from const PTP."""
    html = srcutil.read_text(os.path.join(repo, 'index.html'))
    ptp = json.loads(dashpatch.get_payload(html, 'PTP'))
    years = ptp['yr']
    didx = {d: i for i, d in enumerate(ptp['ds'])}
    raw_of = dict(zip(ptp['ds'], ptp['dr']))
    # IDIMS upper-cases some district units and not others, and the checklist exports use the same
    # spellings as the coverage export; accept a case variant only where it cannot be ambiguous.
    alias = {}
    seen = defaultdict(set)
    for i, raw in enumerate(ptp['dr']):
        alias.setdefault(raw, (ptp['ds'][i], ptp['dv'][i]))
        seen[raw.lower()].add(ptp['ds'][i])
    for raw, dsp in list(alias.items()):
        if len(seen[raw.lower()]) == 1:
            alias.setdefault(raw.lower(), dsp)
    cfg = srcutil.load_sources()
    roster, rname = roster_posts(cfg)

    per, srcs, asof = {}, {}, {}
    for src in ('mon', 'spot', 'log'):
        r = collect(paths[src], src, alias, years, roster)
        per[src] = r
        srcs[src] = os.path.basename(paths[src])
        asof[src] = datetime.datetime.fromtimestamp(
            os.path.getmtime(paths[src]), dashpatch.PKT).strftime('%d-%b-%Y')

    dists = sorted({k[0] for src in per for k in per[src]['cells']}, key=lambda d: didx[d])
    # cells are stored as sparse [slot, values] pairs, in slot order, exactly as const PTP does it
    rows = []
    for dn in dists:
        ycs, mcs = [], []
        for j in range(len(years)):
            v = [0] * len(MK)
            for src in per:
                c = per[src]['cells'].get((dn, j))
                if c:
                    v = [a + b for a, b in zip(v, c)]
            if any(v):
                ycs.append([j, v])
        for slot in sorted({k[1] for src in per for k in per[src]['mcells'] if k[0] == dn}):
            v = [0] * len(MK)
            for src in per:
                c = per[src]['mcells'].get((dn, slot))
                if c:
                    v = [a + b for a, b in zip(v, c)]
            if any(v):
                mcs.append([slot, v])
        rows.append([didx[dn], ycs, mcs])

    ev = []
    for dn in dists:
        ev.append([didx[dn]] + [len(per[src]['ever'].get(dn, ())) for src in ('mon', 'spot', 'log')]
                  + [len(per[src]['everoff'].get(dn, ())) for src in ('mon', 'spot', 'log')]
                  # a post visited by both a monitor and a surveyor is one post reached, so the union
                  # is stored rather than added up in the UI from the three columns beside it
                  + [len(set().union(*[per[s]['ever'].get(dn, set()) for s in per]))])

    # month slots inside a source's own span that carry no checklist anywhere in KP: the source's
    # holes, published so the grid can dash them instead of showing a district-level zero.
    spans, gaps, lasts, firsts, anypost = {}, {}, {}, {}, set()
    for src in per:
        r = per[src]
        firsts[src], lasts[src] = r['first'], r['last']
        spans[src] = '%04d-%02d..%04d-%02d' % (firsts[src] // 100, firsts[src] % 100,
                                              lasts[src] // 100, lasts[src] % 100)
        have = sorted({years[k[1] // 12] * 100 + k[1] % 12 + 1 for k in r['mcells']})
        due, y, m = [], firsts[src] // 100, firsts[src] % 100
        while y * 100 + m <= lasts[src]:
            if y in years:
                due.append(y * 100 + m)
            m += 1
            if m == 13:
                y, m = y + 1, 1
        gaps[src] = ['%d-%02d' % (s // 100, s % 100) for s in due if s not in set(have)]
        for dn in r['ever']:
            anypost |= r['ever'][dn]

    n = {'roster_posts': len(roster), 'roster_src': rname}
    for src in per:
        r = per[src]
        n[src] = {'read': r['read'], 'kept': r['kept'], 'posts': r['posts'],
                  'moved': r['moved'], 'off_posts': sum(len(v) for v in r['everoff'].values()),
                  'drop': dict(r['drop']), 'dq': dict(r['dq'])}
    for k in MK:
        n[k] = sum(c[IDX[k]] for src in per for c in per[src]['cells'].values())
    n['reached_any'] = len(anypost)

    checks(per, rows, ev, years, ptp, n)
    pkt = dashpatch.pkt_stamp()
    return {'gen': pkt, 'asof': '%s (all three exports)' % max(asof.values()),
            'src': srcs, 'yr': years, 'win': '%d-%d' % (years[0], years[-1]),
            'mk': MK, 'spans': spans, 'first': firsts, 'last': lasts, 'gap': gaps,
            'ek': ['d', 'mon', 'spot', 'log', 'monOff', 'spotOff', 'logOff', 'any'],
            'ds': dists, 'dv': [ptp['dv'][didx[x]] for x in dists],
            'd': rows, 'ev': ev,
            'n': n,
            'hold': ['surveyor_name', 'Surveyor Email', 'designation', 'fk_user_id', 'org_name',
                     'ptp_name', 'latitude', 'longitude', 'altitude', 'accuracy', '*_remarks',
                     'comments', 'shift', 'docs_avail', 'app_loc', 'post_identity', 'team_identity',
                     'security_pres', 'sup_visit', 'secu_assist1', 'site_type', 'incoming_type',
                     'total_team', 'transit_teams', 'teams_trained', 'teams_adult', 'teams_local',
                     'teams_zero_dose', 'teams_local_lang', 'carr_tall_avail', 'vial_maint',
                     'vacc_match', 'up_to_10', 'above_10', 'up_to_10_fm', 'above_10_fm', 'fm',
                     'nofm', 'nofm_10', 'up_to_5', 'up_to_5_fm', 'vnfm', 'vnfm_5', 'other',
                     'logistics item families'],
            'note': 'district x year and district x month counts of HRMP field checks at permanent '
                    'transit points, keyed on the same district index and month slots as the PTP '
                    'reporting payload; posts joined to the panel on ptp_loc = Site_ID; checklists '
                    'and surveys are counts of visits, not of children; monitoring months are visit '
                    'months, survey and logistics months are entry months; the item, answer-code and '
                    'person columns in hold are not published'}


def checks(per, rows, ev, years, ptp, n):
    """Abort rather than publish a payload whose cells do not add back."""
    kept = {src: per[src]['kept'] for src in per}
    for src, k in kept.items():
        rs = sum(c[IDX[CHK[src]]] for c in per[src]['cells'].values())
        ms = sum(c[IDX[CHK[src]]] for c in per[src]['mcells'].values())
        if not (rs == ms == k):
            raise SystemExit('ERR ptpm %s cells do not add back to its kept rows: year %s month %s '
                             'kept %s' % (src, rs, ms, k))
        if sum(per[src]['drop'].values()) + k != per[src]['read']:
            raise SystemExit('ERR ptpm %s read %s != kept %s + dropped %s'
                             % (src, per[src]['read'], k, sum(per[src]['drop'].values())))
    for didx, ycs, mcs in rows:
        dn = ptp['ds'][didx]
        # distinct-post columns are sets, not sums: a post visited in January and again in February is
        # one post for the year and two cells for the months, so those columns are bounded, not added.
        setc = set(IDX[x] for x in list(PST.values()) + list(OFF.values()))
        for slot, v in mcs:
            y = [c for c in ycs if c[0] == slot // 12]
            if not y:
                raise SystemExit('ERR ptpm %s has month cell slot %s with no year cell' % (dn, slot))
            yv = y[0][1]
            for i, k in enumerate(MK):
                if v[i] > yv[i]:
                    raise SystemExit('ERR ptpm %s month %s exceeds its year cell on %s (%s > %s)'
                                     % (dn, k, slot, v[i], yv[i]))
        for j, yv in ycs:
            sm = [v for s, v in mcs if s // 12 == j]
            for i, k in enumerate(MK):
                s = sum(x[i] for x in sm)
                if i in setc:
                    if not (yv[i] <= s):
                        raise SystemExit('ERR ptpm %s year %s claims %s posts on %s but its month '
                                         'cells hold %s' % (dn, years[j], yv[i], k, s))
                elif s != yv[i]:
                    raise SystemExit('ERR ptpm %s year %s does not equal its month cells on %s '
                                     '(%s != %s)' % (dn, years[j], k, s, yv[i]))
            if yv[IDX[PST['mon']]] > n['mon']['posts']:
                raise SystemExit('ERR ptpm %s year %s claims more monitored posts than exist'
                                 % (dn, years[j]))
    for e in ev:
        if not (max(e[1], e[2], e[3]) <= e[7] <= e[1] + e[2] + e[3]):
            raise SystemExit('ERR ptpm %s reached-post union out of range: %s' % (ptp['ds'][e[0]], e))
    if sum(e[7] for e in ev) < n['reached_any']:
        raise SystemExit('ERR ptpm the per-district unions add to fewer posts than KP holds (%s < %s)'
                         % (sum(e[7] for e in ev), n['reached_any']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--source', help='accepted for refresh.py run; routed to a slot by filename')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    repo = cfg['repo']
    paths = {}
    for src, stem in STEMS.items():
        one = dict(entry)
        one['patterns'] = [stem + '*.csv']
        rec = srcutil.newest(one)
        path = a.source if (a.source and fnmatch.fnmatch(os.path.basename(a.source),
                                                         stem + '*.csv')) else (rec or {}).get('path')
        if not path or not os.path.exists(path):
            raise SystemExit('ERR ptpm no %s export under %s' % (stem, entry['roots']))
        paths[src] = path
        print('SRC ptpm:%s %s' % (src, path))
    ptpm = build(paths, repo)
    js = srcutil.dumps(ptpm)
    srcutil.write_text(a.out or os.path.join(srcutil.OUT, 'ptpm.json'), js)
    print('OK ptpm %d %s' % (len(js), ' '.join(
        '%s %s->%s' % (s, ptpm['spans'][s], format(ptpm['n'][s]['kept'], ','))
        for s in ('mon', 'spot', 'log'))))
    print('ROSTER ptpm %d panel posts, reached by any source %d, union over districts %d '
          '(mon %d spot %d log %d)'
          % (ptpm['n']['roster_posts'], ptpm['n']['reached_any'], sum(e[7] for e in ptpm['ev']),
             sum(e[1] for e in ptpm['ev']), sum(e[2] for e in ptpm['ev']),
             sum(e[3] for e in ptpm['ev'])))
    for s in ('mon', 'spot', 'log'):
        print('DROP ptpm:%s %s  DQ %s' % (s, ptpm['n'][s]['drop'], ptpm['n'][s]['dq']))
        print('GAP ptpm:%s %s' % (s, ptpm['gap'][s]))


if __name__ == '__main__':
    main()
