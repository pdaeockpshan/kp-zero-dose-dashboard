# -*- coding: utf-8 -*-
"""Extract the HRMP mobile and migrant team payload (const MTM) from the six IDIMS exports.

Sources (all in the HRMP Raw IDIMS folder, all exported 21-Apr-2025, none re-pulled since):
  Migrant_and_Mobile_Populations_Mapping_Form-174   one row per mapping record
  Nomads_immunization_team_activity_-130            one row per nomad-team activity report
  Monitoring_checklist_Nomads_immunization_team_-137 one row per nomad-team monitoring checklist
  Search_Team_Activity-157                          one row per search-team activity report
  Search_Team_Monitoring_Checklist-158              one row per search-team monitoring checklist
  Special_Biker_Teams__Coverage-178                 one row per biker-team coverage report

Aggregated to district x year and district x month on the same district index, year list and month-slot
arithmetic as const PTP and const PTPM, so the PTP tab drives all three grids from one period picker.

Window: these forms were filed Sep-2022 to Apr-2025 and the export was taken 21-Apr-2025, so the whole
block stops 18 months before the reporting panel does. A period outside a form's own span renders a dash
with that span in its tooltip, never a zero - the same rule const PTPM follows.

Months: every form is keyed on its own `date_created` (the month the entry was made). Only three of the
six carry a separate activity date, and two of those disagree with the entry month in 12.8% and 8% of
rows, so one uniform rule is the only one that can be stated honestly. Rows whose activity date falls
after the export's own pull month are counted, never re-dated.

District identity: the display index, raw spellings and division map all come from const PTP. One
spelling in the mapping form is not on it - `KOLAIPALAS` (2 rows) - and those rows are dropped under a
named reason rather than guessed onto a district.

Row accounting: a row is dropped only under a named reason - archived by the source, a repeated
unique_id, a district spelling that is not on the KP index, an unreadable entry date, or a year outside
the panel window - and the extractor aborts unless read equals kept plus the named drops. A negative in
a published count column voids that one cell instead: one search-team row at Peshawar/BAZID KHEL writes
`session_conducted` = -2. The visit happened, so the row and its other columns stand, but a nonsense
cell is not subtracted from a published total, and the voided count is named in the caption.

Team identity: `team_no` is numbered inside a district, not across KP. Nomad teams show 23 distinct
numbers province-wide but 63 once scoped to their district, and biker teams 29 against 82, so the
published team counts are district-scoped unions and the province figure is the sum of those. The export
carries no province-wide team id, so a team numbered 7 in two districts counts twice - and says so.

Published measures are counts of what a form reported, never a rate:
  mapR/nomadR/nomonR/sactR/smonR/bikerR - rows kept by each of the six forms, one column each so a
      period view can say which form filed them (the forms cover different windows)
  pkf/afg                               mapping records by household origin (174)
  sp/sc                                 sessions planned and conducted (157)
  mna/mrf children missed as not available / as a refusal, z2 under-two zero-dose recorded,
         epc EPI cards issued (130)
  bn/bs children recorded not available and still not available, rn/rs refusals recorded and
         still open (178)
  afp/aef AFP cases found and AEFI events reported (130, 157, 178)

Held out of the payload deliberately, and named in the UI caption:
  every `target_*`, `coverage_*` and `un_recorded_*_coverage` column (157, 178) - the same field family
      the PTP panel holds out under the open IDIMS report-definition question (#156). In these exports
      they are child counts, not percentages (the largest value in any of them is 72), but they do not
      reconcile either: coverage exceeds target in 4,245 of 103,143 search rows and one `target_ipv_1`
      is -3. Nothing is published on a column whose definition is still in question.
  the bare dose columns (`zero_dose`, `bcg`, `opv_0..3`, `penta_*`, `pneumo_*`, `rota_*`, `ipv_*`,
      `mr_*`, `td`) - empty in all 14,737 live search rows, and in the nomad form they sit beside three
      mutually inconsistent OPV tallies (`vacc_opv` 203,129 against `opv_does1+2+3` 192,307 against
      `target_opv` 245,337), so which one is the dose count is not decidable from the file.
  `no_of_families` / `no_of_child` (174) - median 3 and 3, but 622 and 906 rows carry more than 100,
      up to 6,232 families and 7,640 children in one settlement record, and that tail holds 16% and 20%
      of the province sum. The count of settlements mapped is published; the population sum is not.
  `mmp_types` (1-10), `hrmp_type` (1-12), `riadmin`, `duration` (max 100,000,000 days),
      `mob_pop_card_issued` (max 3,134 in one session), `team_planned` (values 0, 1 and 8), and every
      checklist item column - integer answer codes with no caption in the export. In the two monitoring
      checklists `items_checked`, `data_Recording`, `vaccination` and `search_team` are blank in all
      rows, which is itself a sign the item block changed shape mid-window.
  person and place detail - `Surveyor Email`, `fk_user_id`, `update_by`, `vacc_name`, `mon_name`,
      `fp_name`, `aic_name`, `org_name`, `designation`, `area_name`, `hamlet_set_name`, `name_location`,
      `cast_tribe`, `settlement` fields, every `*_comments`/`remarks`/`note_*` free-text column and the
      per-row latitude/longitude/altitude/accuracy. This is a public site.
  the origin/previous/next province and district codes (130) - numeric ids whose caption columns are
      text names, so they are excluded rather than joined.

Usage: python _refresh/extract_mtm.py [--out PATH] [--source PATH]
Prints one SRC line per source, then OK mtm <json chars> <summary>.
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

DS = 'mtm'
MONS = {m: i + 1 for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}
PULL = 202504  # every one of these six files was exported 21-Apr-2025

STEMS = {'map': 'Migrant_and_Mobile_Populations_Mapping_Form-174',
         'nomad': 'Nomads_immunization_team_activity_-130',
         'nomon': 'Monitoring_checklist_Nomads_immunization_team_-137',
         'sact': 'Search_Team_Activity-157',
         'smon': 'Search_Team_Monitoring_Checklist-158',
         'biker': 'Special_Biker_Teams__Coverage-178'}
ORDER = ['map', 'nomad', 'nomon', 'sact', 'smon', 'biker']
LABEL = {'map': 'Migrant and mobile population mapping',
         'nomad': 'Nomad immunization team activity',
         'nomon': 'Nomad team monitoring checklist',
         'sact': 'Search team activity',
         'smon': 'Search team monitoring checklist',
         'biker': 'Special biker team coverage'}
ROWIS = {'map': 'mapping records',
         'nomad': 'team activity reports',
         'nomon': 'monitoring checklists',
         'sact': 'team activity reports',
         'smon': 'monitoring checklists',
         'biker': 'team coverage reports'}
TEAMCOL = {'nomad': 'teamno', 'nomon': 'team_no', 'sact': 'team_no', 'smon': 'team_no',
           'biker': 'team_no'}
ACTCOL = {'sact': 'date_mon', 'smon': 'date_mon', 'biker': 'date_mon'}

# One row-count column per form, not one shared "rep": a form table scoped by the period picker has
# to know which form filed which rows, and the six forms cover different windows.
MEAS = ['mapR', 'nomadR', 'nomonR', 'sactR', 'smonR', 'bikerR',
        'pkf', 'afg', 'sp', 'sc', 'mna', 'mrf', 'z2', 'epc', 'bn', 'bs', 'rn', 'rs', 'afp', 'aef']
IDX = {k: i for i, k in enumerate(MEAS)}
RKEY = {f: f + 'R' for f in ORDER}
FORM_MEAS = {'map': ['mapR', 'pkf', 'afg'],
             'nomad': ['nomadR', 'mna', 'mrf', 'z2', 'epc', 'afp', 'aef'],
             'nomon': ['nomonR'],
             'sact': ['sactR', 'sp', 'sc', 'afp', 'aef'],
             'smon': ['smonR'],
             'biker': ['bikerR', 'bn', 'bs', 'rn', 'rs', 'afp', 'aef']}
# measure -> the export column it is summed from (the six R columns are the rows themselves, pkf/afg
# come from a code whose caption columns prove the decode)
SRC = {'nomad': {'mna': 'missed_na', 'mrf': 'missed_refusal', 'z2': 'ri_zero_under_2',
                 'epc': 'epi_card_issued', 'afp': 'afp', 'aef': 'aefi'},
       'sact': {'sp': 'session_plan', 'sc': 'session_conducted', 'afp': 'afp_count',
                'aef': 'aefi_count'},
       'biker': {'bn': 'na_recorded', 'bs': 'still_na', 'rn': 'refusal_recorded',
                 'rs': 'still_refusal', 'afp': 'afp_count', 'aef': 'aefi_count'}}
EK = ['mapUc', 'nomadTm', 'nomadUc', 'nomonTm', 'nomonUc', 'sactTm', 'sactUc', 'smonTm', 'smonUc',
      'bikerTm', 'bikerUc']
# columns that may never appear in the payload, checked against the emitted JSON
BANNED = ['email', 'user_id', 'update_by', 'vacc_name', 'mon_name', 'fp_name', 'aic_name',
          'org_name', 'designation', 'area_name', 'hamlet', 'name_location', 'cast_tribe',
          'latitude', 'longitude', 'altitude', 'accuracy', 'remarks', 'comments', 'note_',
          'settlement']


def num(x):
    x = (x or '').strip().replace(',', '')
    if not x or x == '\\N':
        return None
    m = re.match(r'^(-?\d+(?:\.\d+)?)', x)
    return float(m.group(1)) if m else None


def mkey(s):
    """'21-Apr-2025  09:33:08' or '2025-04-21' -> 202504, else None."""
    for tok in (s or '').strip().split():
        p = tok.split('-')
        if len(p) != 3:
            continue
        if len(p[0]) == 4 and p[0].isdigit() and p[1].isdigit() and len(p[2]) >= 2:
            return int(p[0]) * 100 + int(p[1])
        if p[1] in MONS and len(p[2]) == 4 and p[2].isdigit():
            return int(p[2]) * 100 + MONS[p[1]]
    return None


def iv(r, col, dq):
    """Whole-number count from a column: blank is 0, a fraction is rounded and counted, a negative
    voids that one cell. Three rows in the search-team activity export carry a negative (one
    session_conducted of -2 at Peshawar/BAZID KHEL); the visit happened, so the row is kept and its
    other columns stand, but a nonsense cell is not added into a published sum - the column is the
    total of the usable values and the voided count is named in the caption."""
    v = num(r.get(col))
    if v is None:
        return 0
    if v < 0:
        dq['%s is negative' % col] += 1
        return None
    if v != int(v):
        dq['%s is not a whole number' % col] += 1
    return int(round(v))


def collect(path, form, alias, years):
    """One export into district x year and district x month cells plus the team and UC books."""
    with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
        h = next(csv.reader(fh))
    ix = {c: i for i, c in enumerate(h)}
    need = ['unique_id', 'district_name', 'uc_name', 'date_created', 'is_archive']
    smap = SRC.get(form, {})
    need += sorted(set(smap.values()))
    for opt in (TEAMCOL.get(form), ACTCOL.get(form)):
        if opt:
            need.append(opt)
    if form == 'map':
        need.append('origin_country')
    miss = sorted({c for c in need if c not in ix})
    if miss:
        raise SystemExit('ERR mtm %s has no %s column - the export changed shape'
                         % (os.path.basename(path), ', '.join(miss)))

    z = lambda: [0] * len(MEAS)  # noqa: E731
    cells, mcells = defaultdict(z), defaultdict(z)
    tsets, usets = defaultdict(set), defaultdict(set)
    read = kept = 0
    drop, dq = Counter(), Counter()
    seen = set()
    with io.open(path, encoding='utf-8-sig', errors='replace', newline='') as fh:
        rd = csv.reader(fh)
        next(rd, None)  # the header is not a row
        for row in rd:
            if len(row) != len(h):
                drop['row does not match its header'] += 1
                continue
            read += 1
            uid = row[ix['unique_id']].strip()
            if uid in seen:
                drop['repeated unique_id'] += 1
                continue
            seen.add(uid)
            if (row[ix['is_archive']] or '').strip() == '1':
                drop['archived by the source'] += 1
                continue
            dn = (row[ix['district_name']] or '').strip()
            a = alias.get(dn) or alias.get(dn.upper())
            if not a:
                drop['district not on the KP district index'] += 1
                continue
            ym = mkey(row[ix['date_created']])
            if ym is None:
                drop['no readable entry date'] += 1
                continue
            if ym // 100 not in years:
                drop['year outside the panel window'] += 1
                continue
            kept += 1
            r = dict(zip(h, row))
            if ACTCOL.get(form):
                ca = mkey(r.get(ACTCOL[form], ''))
                if ca is not None and ca > PULL:
                    dq['activity date after the export was taken'] += 1
                if ca is not None and ca != ym:
                    dq['activity month and entry month differ'] += 1
            v = [0] * len(MEAS)
            v[IDX[RKEY[form]]] = 1
            for k in smap:
                val = iv(r, smap[k], dq)
                if val is not None:
                    v[IDX[k]] = val
            if form == 'map':
                oc = (r.get('origin_country') or '').strip()
                if oc == '1':
                    v[IDX['pkf']] = 1
                elif oc == '2':
                    v[IDX['afg']] = 1
                else:
                    dq['origin country code is neither 1 nor 2'] += 1
            yi = years.index(ym // 100)
            for key, book in (((a[0], yi), cells), ((a[0], yi * 12 + ym % 100 - 1), mcells)):
                c = book[key]
                for i in range(len(MEAS)):
                    c[i] += v[i]
            uc = (r.get('uc_name') or '').strip()
            if uc:
                usets[a[0]].add(uc)
            tc = (r.get(TEAMCOL[form]) or '').strip() if TEAMCOL.get(form) else ''
            if tc:
                tsets[a[0]].add(tc)
            if form == 'biker' and 'team_n0' in ix:
                if (r.get('team_no') or '').strip() != (r.get('team_n0') or '').strip():
                    dq['team_no and team_n0 disagree'] += 1
            if form == 'sact':
                sp, sc = v[IDX['sp']], v[IDX['sc']]
                if sc > sp:
                    dq['sessions conducted exceed sessions planned'] += 1
                elif sc == sp:
                    dq['sessions conducted equal sessions planned'] += 1
            if form == 'biker':
                if v[IDX['bs']] > v[IDX['bn']]:
                    dq['still-not-available exceeds recorded not-available'] += 1
                if v[IDX['rs']] > v[IDX['rn']]:
                    dq['still-refusal exceeds recorded refusal'] += 1
    yms = sorted({k[1] for k in mcells})
    return dict(cells=cells, mcells=mcells, tsets=tsets, usets=usets, read=read, kept=kept,
                drop=drop, dq=dq, districts=len({k[0] for k in cells}),
                teams=sum(len(s) for s in tsets.values()), ucs=sum(len(s) for s in usets.values()),
                teams_any=len({t for s in tsets.values() for t in s}),
                ucs_any=len({u for s in usets.values() for u in s}),
                first=years[yms[0] // 12] * 100 + yms[0] % 12 + 1 if yms else 0,
                last=years[yms[-1] // 12] * 100 + yms[-1] % 12 + 1 if yms else 0)


def file_date(path):
    return datetime.datetime.fromtimestamp(os.path.getmtime(path),
                                           dashpatch.PKT).strftime('%d-%b-%Y')


def build(paths, repo):
    html = srcutil.read_text(os.path.join(repo, 'index.html'))
    ptp = json.loads(dashpatch.get_payload(html, 'PTP'))
    years, didx = ptp['yr'], {d: i for i, d in enumerate(ptp['ds'])}
    alias, seen = {}, defaultdict(set)
    for i, raw in enumerate(ptp['dr']):
        alias.setdefault(raw, (ptp['ds'][i], ptp['dv'][i]))
        seen[raw.lower()].add(ptp['ds'][i])
    for raw, dsp in list(alias.items()):
        if len(seen[raw.lower()]) == 1:
            alias.setdefault(raw.lower(), dsp)

    per = {f: collect(paths[f], f, alias, years) for f in ORDER}

    dists = sorted({k[0] for f in ORDER for k in per[f]['cells']}, key=lambda d: didx[d])
    rows = []
    for dn in dists:
        ycs, mcs = [], []
        for j in range(len(years)):
            v = [0] * len(MEAS)
            for f in ORDER:
                c = per[f]['cells'].get((dn, j))
                if c:
                    v = [a + b for a, b in zip(v, c)]
            if any(v):
                ycs.append([j, v])
        for slot in sorted({k[1] for f in ORDER for k in per[f]['mcells'] if k[0] == dn}):
            v = [0] * len(MEAS)
            for f in ORDER:
                c = per[f]['mcells'].get((dn, slot))
                if c:
                    v = [a + b for a, b in zip(v, c)]
            if any(v):
                mcs.append([slot, v])
        rows.append([didx[dn], ycs, mcs])

    ev = []
    for dn in dists:
        one = [didx[dn]]
        for e in EK:
            f = e[:-2]
            book = per[f]['usets'] if e.endswith('Uc') else per[f]['tsets']
            one.append(len(book.get(dn, ())))
        ev.append(one)

    spans, gaps, firsts, lasts = {}, {}, {}, {}
    for f in ORDER:
        r = per[f]
        firsts[f], lasts[f] = r['first'], r['last']
        spans[f] = '%04d-%02d..%04d-%02d' % (firsts[f] // 100, firsts[f] % 100,
                                            lasts[f] // 100, lasts[f] % 100)
        have = {years[k[1] // 12] * 100 + k[1] % 12 + 1 for k in r['mcells']}
        due, y, m = [], firsts[f] // 100, firsts[f] % 100
        while y * 100 + m <= lasts[f]:
            if y in years:
                due.append(y * 100 + m)
            m += 1
            if m == 13:
                y, m = y + 1, 1
        gaps[f] = ['%d-%02d' % (s // 100, s % 100) for s in due if s not in have]

    n = {}
    for f in ORDER:
        r = per[f]
        n[f] = {'read': r['read'], 'kept': r['kept'], 'districts': r['districts'],
               'teams': r['teams'], 'ucs': r['ucs'], 'teams_any': r['teams_any'],
               'ucs_any': r['ucs_any'], 'drop': dict(r['drop']), 'dq': dict(r['dq'])}
    for k in MEAS:
        n[k] = sum(c[IDX[k]] for f in ORDER for c in per[f]['cells'].values())
    n['rows'] = sum(per[f]['kept'] for f in ORDER)
    n['district_rows'] = len(rows)

    cfg = srcutil.load_sources()
    asof = {f: file_date(paths[f]) for f in ORDER}
    checks(per, rows, ev, years, ptp, n)
    out = {'gen': dashpatch.pkt_stamp(),
           'asof': '21-Apr-2025',
           'src': {f: os.path.basename(paths[f]) for f in ORDER},
           'filed': asof,
           'yr': years, 'win': '%d-%d' % (years[0], years[-1]),
           'mk': MEAS, 'ek': EK,
           'forms': [{'id': f, 'label': LABEL[f], 'row': ROWIS[f], 'cols': FORM_MEAS[f],
                      'span': spans[f], 'first': firsts[f], 'last': lasts[f],
                      'gap': gaps[f], 'rows': n[f]['kept'], 'districts': n[f]['districts'],
                      'teams': n[f]['teams'], 'ucs': n[f]['ucs']} for f in ORDER],
           'spans': spans, 'first': firsts, 'last': lasts, 'gap': gaps,
           'ds': dists, 'dv': [ptp['dv'][didx[x]] for x in dists],
           'd': rows, 'ev': ev, 'n': n,
           'hold': ['every target_* / coverage_* / un_recorded_*_coverage column',
                    'the bare dose columns (zero_dose, bcg, opv_*, penta_*, pneumo_*, rota_*, ipv_*, '
                    'mr_*, td)',
                    'no_of_families and no_of_child', 'mmp_types and hrmp_type codes', 'riadmin',
                    'duration', 'mob_pop_card_issued', 'team_planned', 'every checklist item column',
                    'Surveyor Email, fk_user_id, update_by', 'vacc_name, mon_name, fp_name, aic_name, '
                    'org_name, designation', 'area_name, hamlet_set_name, name_location, cast_tribe',
                    'every remarks, comments and note_ column', 'latitude, longitude, altitude, '
                    'accuracy', 'the origin, previous and next district and province codes'],
           'note': 'district x year and district x month counts of the six HRMP mobile and migrant '
                   'team forms that were pulled with the PTP field checks on 21-Apr-2025 and have not '
                   'been re-pulled since; keyed on the same district index and month slots as const '
                   'PTP and const PTPM; every month is the month the entry was made; teams and union '
                   'councils are counted inside their own district and the province figure is the sum '
                   'of those, because team numbers repeat across districts; rows, checklists and '
                   'records are counts of forms, not of children; nothing in the columns named in hold '
                   'is published, and no coverage percentage appears here'}
    sweep(out, ptp)
    return out


def sweep(obj, ptp):
    """The cell arrays must be pure numbers and the district list must be the one the dashboard
    already publishes, so no name, email, coordinate or free-text field can reach the payload.
    Checked on the data only: the hold list legitimately names the columns it refuses to publish."""
    for part in ('d', 'ev'):
        s = json.dumps(obj[part])
        if not re.fullmatch(r'[\[\],:\s\-0-9]+', s):
            raise SystemExit('ERR mtm the %s arrays hold something other than numbers' % part)
    for f in obj['forms']:
        for key in ('label', 'row', 'span', 'id'):
            v = str(f[key])
            if any(b in v.lower() for b in BANNED) or '@' in v:
                raise SystemExit('ERR mtm the %s field of form %s reads %r' % (key, f['id'], v))
    ds = json.dumps(obj['ds'])
    if not all(x in set(ptp['ds']) for x in obj['ds']):
        raise SystemExit('ERR mtm a district outside const PTP reached the payload: %s' % ds)
    ns = json.dumps(obj['n'], ensure_ascii=False).lower()
    hit = [b for b in BANNED if b in ns]
    if hit or '@' in ns:
        raise SystemExit('ERR mtm the row-accounting block mentions %s' % ', '.join(hit) or '@')


def checks(per, rows, ev, years, ptp, n):
    """Abort rather than publish a payload whose cells do not add back."""
    for f in ORDER:
        r = per[f]
        rs = sum(c[IDX[RKEY[f]]] for c in r['cells'].values())
        ms = sum(c[IDX[RKEY[f]]] for c in r['mcells'].values())
        if not (rs == ms == r['kept']):
            raise SystemExit('ERR mtm %s cells do not add back to its kept rows: year %s month %s '
                             'kept %s' % (f, rs, ms, r['kept']))
        if sum(r['drop'].values()) + r['kept'] != r['read']:
            raise SystemExit('ERR mtm %s read %s != kept %s + dropped %s'
                             % (f, r['read'], r['kept'], sum(r['drop'].values())))
    for dn in per['map']['cells']:
        y = per['map']['cells'][dn]
        if y[IDX['pkf']] + y[IDX['afg']] != y[IDX[RKEY['map']]]:
            raise SystemExit('ERR mtm %s origin split does not add back to its mapping rows' % (dn,))
    for didx, ycs, mcs in rows:
        dn = ptp['ds'][didx]
        for slot, v in mcs:
            y = [c for c in ycs if c[0] == slot // 12]
            if not y:
                raise SystemExit('ERR mtm %s has month cell slot %s with no year cell' % (dn, slot))
            for i, k in enumerate(MEAS):
                if v[i] > y[0][1][i]:
                    raise SystemExit('ERR mtm %s month %s exceeds its year cell on %s (%s > %s)'
                                     % (dn, k, slot, v[i], y[0][1][i]))
        for j, yv in ycs:
            sm = [v for s, v in mcs if s // 12 == j]
            for i, k in enumerate(MEAS):
                s = sum(x[i] for x in sm)
                if s != yv[i]:
                    raise SystemExit('ERR mtm %s year %s does not equal its month cells on %s '
                                     '(%s != %s)' % (dn, years[j], k, s, yv[i]))
    for e in ev:
        for i, k in enumerate(EK):
            f = k[:-2]
            if e[i + 1] > per[f]['kept']:
                raise SystemExit('ERR mtm %s claims more %s than the form has rows'
                                 % (ptp['ds'][e[0]], k))
    for f in ORDER:
        if TEAMCOL.get(f) and not per[f]['teams']:
            raise SystemExit('ERR mtm %s keeps rows but records no team number at all' % f)
    if n['sc'] > n['sp']:
        raise SystemExit('ERR mtm province sessions conducted %s exceed planned %s' % (n['sc'], n['sp']))
    if n['bs'] > n['bn'] or n['rs'] > n['rn']:
        raise SystemExit('ERR mtm biker still-open tallies exceed their recorded columns')
    if sum(e[1 + EK.index('mapUc')] for e in ev) != n['map']['ucs']:
        raise SystemExit('ERR mtm the per-district union-council counts do not add back to the '
                         'mapping form total')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--source', help='accepted for refresh.py run; routed to a slot by filename')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    entry = cfg['auto'][DS]
    paths = {}
    for f in ORDER:
        one = dict(entry)
        one['patterns'] = [STEMS[f] + '*.csv']
        rec = srcutil.newest(one)
        path = a.source if (a.source and fnmatch.fnmatch(os.path.basename(a.source),
                                                         STEMS[f] + '*.csv')) else (rec or {}).get('path')
        if not path or not os.path.exists(path):
            raise SystemExit('ERR mtm no %s export under %s' % (STEMS[f], entry['roots']))
        paths[f] = path
        print('SRC mtm:%s %s' % (f, path))
    mtm = build(paths, cfg['repo'])
    js = srcutil.dumps(mtm)
    srcutil.write_text(a.out or os.path.join(srcutil.OUT, 'mtm.json'), js)
    print('OK mtm %d %s' % (len(js), ' '.join(
        '%s %s->%s' % (f, mtm['spans'][f], format(mtm['n'][f]['kept'], ',')) for f in ORDER)))
    print('TOTALS mtm rows across the six forms %s, district rows %s, of the mapping form %s '
          '(Pakistan-origin %s Afghan-origin %s), sessions %s/%s, '
          'missed NA %s refusal %s, still NA %s refusal %s, under-2 zero-dose %s, EPI cards %s, '
          'AFP %s AEFI %s'
          % (format(mtm['n']['rows'], ','), mtm['n']['district_rows'],
             format(mtm['n']['map']['kept'], ','),
             format(mtm['n']['pkf'], ','), format(mtm['n']['afg'], ','),
             format(mtm['n']['sp'], ','), format(mtm['n']['sc'], ','),
             format(mtm['n']['mna'], ','), format(mtm['n']['mrf'], ','),
             format(mtm['n']['bs'], ','), format(mtm['n']['rs'], ','),
             format(mtm['n']['z2'], ','), format(mtm['n']['epc'], ','),
             format(mtm['n']['afp'], ','), format(mtm['n']['aef'], ',')))
    for f in ORDER:
        print('BREADTH mtm:%-6s districts %s teams %s (numbers %s) ucs %s (names %s)'
              % (f, mtm['n'][f]['districts'], mtm['n'][f]['teams'], mtm['n'][f]['teams_any'],
                 mtm['n'][f]['ucs'], mtm['n'][f]['ucs_any']))
        print('DROP mtm:%s %s  DQ %s' % (f, mtm['n'][f]['drop'], mtm['n'][f]['dq']))
        print('GAP mtm:%s %s' % (f, mtm['gap'][f]))


if __name__ == '__main__':
    main()
