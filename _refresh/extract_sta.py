# -*- coding: utf-8 -*-
"""Extract the search-team payload (const STA) from the two search-team .twbx workbooks.

Sources (both in Joint Database/3. HRMP, both pulled 28-Sep-2026 per their own file dates):
  Search Team Activity Peshawar.twbx        Extract table, 26,806 rows, one per activity report
  Search Team Monitoring Check LIst.twbx    Extract table, 10,853 rows, one per checklist

These two workbooks are the same IDIMS forms as Search_Team_Activity-157 and
Search_Team_Monitoring_Checklist-158 in the Raw IDIMS folder, re-exported five months later, and each
older export is contained in the workbook that superseded it: 15,281 of 15,282 activity ids and
6,001 of 6,001 checklist ids are in the workbook, which also holds 11,505 and 4,851 rows the April
export cannot have because they were entered after it. So the workbook is the source of record, and the
older export is only consulted for the ids it holds that the workbook lost - one activity row and no
checklist row. That carry is asserted to stay tiny or the run aborts, because a large divergence would
mean a different cut of the form rather than a later pull, and two different cuts must not be unioned.

The owner named this file as the search-team zero-dose and antigen source, and the form does carry it,
though not where the column names suggest. The bare dose columns (zero_dose, bcg, opv_0..3, penta_1..3,
pneumo_1..3, rota_1..2, ipv_1..2, mr_1..2, td, new_born_0_28_days, ipv_booster) are blank in all 26,806
rows. The target_<antigen> / coverage_<antigen> pair is filled for 21 antigens and those are child
counts, not percentages, so this payload publishes the pair per antigen and nothing about the bare
dose columns.

The pair does not always reconcile, and the void rule is applied row by row rather than in aggregate:
a row whose coverage exceeds its target, or whose pair holds a negative or an unreadable number,
contributes neither number to any published cell, and the voided row count is published beside the pair
(zdV, o3V, bV, naV, rfV) so the reader can see how much was refused. On the 26,225 kept activity rows
that removes 585 zero-dose rows, 1,360 OPV-3 rows and 579 BCG rows - between 2% and 8% of what the form
recorded - and the surviving province figures are 43,554 zero-dose children targeted against 25,868
found, 61,127 against 43,216 for OPV-3, and 36,455 against 22,732 for BCG.

Because every kept row satisfies covered <= target, so does every sum, and no ladder column can
disagree with itself in aggregate. What can still fail is the column as a measure, and one does: td
writes a coverage number in 8,752 rows and a target in exactly one (18,500 covered against a target of
3 across the whole pull). A fifth of its rows contradict themselves, where the worst a used column
manages is ipv_1 at 7.8%, so td is withheld whole by a computed rule - more than a fifth of the rows
that recorded the pair contradicted themselves - and named in agvoid with its four numbers, so a refused
column is visible rather than silent. Before the row rule is applied penta_3 looks like the same kind of
failure, 98,489 covered against 64,302 target; after it the survivors reconcile at 61,063 against
43,180, so penta_3 is published and only td is not. That is the whole difference between a column with
a broken definition and a column with 1,355 bad rows.

un_recorded_<antigen>_coverage is held out: it is a third number that reconciles with the pair in 0 of
the rows checked (zero-dose 1,511, BCG 1,599, OPV-3 2,142 province-wide), except in the ipv_booster
column family - named without the _coverage suffix - where coverage + un_recorded equals target in
18,780 of the 18,936 rows that recorded it. ipv_booster therefore stays in the ladder, sparse as it is
(266 rows carry a booster target, summing 1,143 against 447 covered), and the rest of that family never
appears.

Aggregated to district x year and district x month on the same district index, year list and month-slot
arithmetic as const PTP, const PTPM and const MTM, so the PTP tab drives all four grids from one period
picker.

District identity: const PTP's raw codes, matched case-insensitively - which matters here, because the
workbook writes WAZIR-S LOWER where the April export wrote WAZIR-S Lower, and the panel's own raw code
is WAZIR-S Lower (display SW Wazir Belt), a different district from WAZIR-S (South Waziristan unsplit).
A spelling that resolves to two panel districts is dropped under a named reason, never guessed; none
does.

Months: the month the entry was made (date_created), the same uniform rule const MTM states. The form's
own activity date (date_mon) disagrees with the entry month in 4,131 of the 26,225 kept activity rows,
is unreadable in one, and runs into 2027 in two checklists, so it is reported as divergence counts and
never used to re-date a row.

Teams: team_no is numbered inside a district, not across KP (24 distinct numbers in the activity form
but 56 once scoped to their district, 26 against 55 in the checklist), so team counts are district-scoped
unions and the province figure is the sum of those. The form carries no province-wide team id, so a team
numbered 7 in two districts counts twice - and says so.

Coverage: the activity form files in 5 districts (Peshawar, SW Wazir Belt, Bannu, D.I. Khan and Lakki
Marwat) and the checklist in 8, the extra three being one Shangla, one Malakand and one SW Mehsud Belt
checklist. Five further district spellings appear in the checklist workbook only as the nine archived
rows, so they are dropped under a named reason and are not evidence of search-team monitoring there.

The monitoring checklist joins the activity form on (district, team_no, month): 163 of the 233
activity-side team-months have a checklist behind them, of the 267 checklist-side ones. That link is
published as matched counts per district, never as a rate over unmatched months, because a checklist
filed in a district-month with no activity report - or an activity team-month with no checklist - is
itself the finding.

Checklist compliance: 32 item columns answer 1, 0 or nothing - unlike the PTP monitoring export's
undecoded 1/2/3 codes, which is why those rates could not be published and these can. Twenty-five carry
answers; seven (the team, logistics, vaccination, cold-chain, assistant, data-recording and modality
fields) are left blank by all 10,843 live checklists, so they are discovered from this pull rather than
assumed from the April export, named in the payload and left out of the grid. Yes/no/not-recorded is
published per item per district-year and the UI states a rate over answered rows only.

EPI comparison: the activity form's OPV-3 and zero-dose counts are set against const EPIM's district x
month OPV-3 and BCG doses for the months both registers cover (2024-01 to 2026-09). They are two
registers of the same districts, not a numerator and a denominator - one counts children a search team
found and covered, the other doses administered through facilities - so the block publishes both
numbers and lets the UI show their ratio as a labelled comparison, never as a coverage rate.

Row accounting: a row is kept only under named reasons and the run aborts unless workbook rows minus
the named drops plus the carried rows equals the rows kept. That is 26,806 - 582 + 1 = 26,225 activity
rows and 10,853 - 10 + 0 = 10,843 checklists, the drops being the rows the source itself archived and
repeated unique_ids. The single carried activity row is the one id the April export holds and the
workbook lost; the carry aborts if it ever exceeds 5% of the older export.

Held out of the payload, and named in the UI caption: reporter names, the address they sign with, the
id and the update id, the vaccinator and monitor name columns, the focal-person name column; position
coordinates and their accuracy, because this is a public site; every free-text note including the
archive reason; the reporting body and the post columns (they say who filed the form, not what the
programme did); the bare dose columns, for the reason above; the un_recorded family; any ladder column
the computed rule refuses - on this pull td, and its numbers are published in agvoid rather than hidden;
the seven checklist fields no row ever answered; and the ladder's month split, because a target recorded
against a month the team did not work is exactly the error the row rule exists to catch.

Usage: python _refresh/extract_sta.py [--out PATH]
Prints OK sta <json chars> <summary>, then the totals, the voids, the drops and the gaps.
"""
import argparse
import collections
import csv
import io
import json
import os
import re
import sys
import tempfile
import zipfile

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dashpatch
import srcutil

DS = 'sta'
HRMP = r'C:\Users\HD\Dropbox\Joint Database\3. HRMP'
RAW = os.path.join(HRMP, 'Raw IDIMS FIles')
WB = {'sact': os.path.join(HRMP, 'Search Team Activity Peshawar.twbx'),
      'smon': os.path.join(HRMP, 'Search Team Monitoring Check LIst.twbx')}
OLD = {'sact': 'Search_Team_Activity-157', 'smon': 'Search_Team_Monitoring_Checklist-158'}
PULL = 202609  # both workbooks were pulled 28-Sep-2026; dates past this are counted, never re-dated
MONS = {m: i + 1 for i, m in enumerate(
    ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])}

FORMS = ['sact', 'smon']
LABEL = {'sact': 'Search team activity', 'smon': 'Search team monitoring checklist'}
ROWIS = {'sact': 'activity reports', 'smon': 'monitoring checklists'}
TEAMCOL = 'team_no'
ACTCOL = 'date_mon'

# One row-count column per form, so a period view can say which form filed the rows it shows.
# Each pair is target / covered / voided, the voided column being the rows that contradicted
# themselves and therefore contributed to neither of the other two.
MEAS = ['actR', 'monR',
        'zdT', 'zdC', 'zdV', 'o3T', 'o3C', 'o3V', 'bT', 'bC', 'bV',
        'naR', 'naC', 'naV', 'rfR', 'rfC', 'rfV',
        'sp', 'sc', 'afp', 'aef']
IDX = {k: i for i, k in enumerate(MEAS)}
RKEY = {'sact': 'actR', 'smon': 'monR'}
FORM_MEAS = {'sact': [k for k in MEAS if k != 'monR'], 'smon': ['monR']}
PAIR = {'sact': collections.OrderedDict([
    ('zdT', ('target_zero_dose', 'coverage_zero_dose')),
    ('o3T', ('target_opv_3', 'coverage_opv_3')),
    ('bT', ('target_bcg', 'coverage_bcg')),
    ('naR', ('target_na', 'covered_na')),
    ('rfR', ('target_refusal', 'covered_refusal'))]), 'smon': collections.OrderedDict()}
PAIRL = {'zdT': 'Zero-dose children found and recorded',
         'o3T': 'Children given a third OPV dose',
         'bT': 'Children given BCG',
         'naR': 'Children recorded not available and followed up',
         'rfR': 'Children recorded as a refusal and followed up'}
SOLO = {'sact': collections.OrderedDict([('sp', 'session_plan'), ('sc', 'session_conducted'),
                                         ('afp', 'afp_count'), ('aef', 'aefi_count')]),
        'smon': collections.OrderedDict()}
SOLOL = {'sp': 'Sessions planned', 'sc': 'Sessions conducted',
         'afp': 'AFP cases found', 'aef': 'AEFI events reported'}
# one caption per grid column, so the payload never has to derive one from a name
ML = {'actR': 'Activity reports', 'monR': 'Monitoring checklists'}
for _m, _l in PAIRL.items():
    _b = _m[:-1]
    _p = _m[-1]
    for _s in ('T', 'C', 'V') if _p == 'T' else ('R', 'C', 'V'):
        ML[_b + _s] = {'T': _l + ' (target)', 'R': _l + ' (recorded)', 'C': _l + ' (covered)',
                       'V': 'rows that recorded it and contradicted themselves'}[_s]
for _m, _l in SOLOL.items():
    ML[_m] = _l

# The antigen ladder: district x year with the same cut per month, so the period picker narrows it.
# Published as target / covered / voided rows; the column is dropped whole if it fails the two tests
# in the header, and a withheld column is dropped from both books, so a month never shows a number the
# year refuses.
LADDER = [('zero_dose', 'Zero-dose children'), ('new_born', 'New-born (0-28 days)'),
          ('bcg', 'BCG'), ('opv_0', 'OPV 0 birth dose'), ('opv_1', 'OPV 1'), ('opv_2', 'OPV 2'),
          ('opv_3', 'OPV 3'), ('penta_1', 'Pentavalent 1'), ('penta_2', 'Pentavalent 2'),
          ('penta_3', 'Pentavalent 3'), ('pneumo_1', 'Pneumococcal 1'), ('pneumo_2', 'Pneumococcal 2'),
          ('pneumo_3', 'Pneumococcal 3'), ('rota_1', 'Rotavirus 1'), ('rota_2', 'Rotavirus 2'),
          ('ipv_1', 'IPV 1'), ('ipv_2', 'IPV 2'), ('mr_1', 'Measles-rubella 1'),
          ('mr_2', 'Measles-rubella 2'), ('ipv_booster', 'IPV booster'), ('td', 'TD')]
LKEY = [a for a, _ in LADDER]
LIDX = {a: i for i, a in enumerate(LKEY)}
LAB = dict(LADDER)
# the one column family whose un_recorded partner carries a different suffix
UNREC = {'ipv_booster': 'un_recorded_ipv_booster'}
for _a in LKEY:
    UNREC.setdefault(_a, 'un_recorded_%s_coverage' % _a)
LADDER_VOID = collections.OrderedDict()  # filled from the data, never assumed

# every checklist item column; which of them no row ever answered is computed, not hardcoded
ITEMS = [('two_member', 'Two members present'), ('id_cards', 'Team carrying ID cards'),
         ('moterbije_helmet', 'Motorcycle helmets'), ('opv_vaccine', 'OPV vials carried'),
         ('ipv_vaccine', 'IPV vials carried'), ('routine_vaccine', 'Routine vaccines carried'),
         ('safety_boxes', 'Safety boxes'), ('aefi_report', 'AEFI report available'),
         ('epi_vaccination', 'EPI vaccination cards'), ('hrmp_vaccination', 'HRMP vaccination cards'),
         ('returning_un', 'Returning children recorded'), ('administering_all',
                                                           'Administering to all eligible'),
         ('cool_packs', 'Cool packs frozen'), ('foam_pad', 'Foam pad in carrier'),
         ('protecting_vials', 'Vials protected from light'), ('assisting_skilled',
                                                              'Assistant skilled'),
         ('verifying_children', 'Verifying children against list'), ('controlling_crowd',
                                                                    'Crowd controlled at the post'),
         ('secure_filled', 'Registers secure and filled'), ('accurate_data', 'Data recorded accurately'),
         ('microplan_available', 'Micro-plan available'), ('team_visiting', 'Team visiting households'),
         ('cap', 'Caps issued'), ('jacket', 'Jackets issued'),
         ('panadol_paracetamol', 'Paracetamol available'),
         # these seven are on the form and every row leaves them blank; they stay in the candidate list
         # so the run discovers that from the data instead of trusting an earlier export
         ('search_team', 'Search team field'), ('logistics', 'Logistics field'),
         ('vaccination', 'Vaccination field'), ('cold_chain', 'Cold chain field'),
         ('team_assistant', 'Team assistant field'), ('data_recording', 'Data recording field'),
         ('operational_modality', 'Operational modality field')]
IKEY = [c for c, _ in ITEMS]
IIDX = {c: i for i, c in enumerate(IKEY)}
ILAB = dict(ITEMS)
TEAMCOLS = {'sact': TEAMCOL, 'smon': TEAMCOL}

# tokens that may never reach the payload's published strings (the hold list is exempt: naming what is
# refused is the point of it)
BANNED = ['email', 'user_id', 'update_by', 'vacc_name', 'mon_name', 'fp_name', 'org_name',
          'designation', 'latitude', 'longitude', 'altitude', 'accuracy', 'remarks', 'comments',
          'note_', 'surveyor', 'archive_reason', 'tehsil']
EPI_FROM, EPI_TO = 202401, 202609  # const EPIM's own span, which starts after this form's
EK = ['sactTm', 'sactUc', 'smonTm', 'smonUc']
TK = ['EPI OPV-3 doses', 'EPI BCG doses', 'search-team OPV-3 covered', 'search-team zero-dose covered',
      'search-team activity reports']


def num(x):
    """The leading whole or decimal number in a cell, or None when there is none."""
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(',', '')
    if not s or s in ('\\N', 'NULL', 'None', 'NA', 'nan'):
        return None
    m = re.match(r'^(-?\d+(?:\.\d+)?)', s)
    return float(m.group(1)) if m else None


def mkey(s):
    """'2025-04-21 09:33:08', '21-Apr-2025  09:33:08' or '2024-01' -> 202401, else None."""
    for tok in str(s or '').strip().split():
        p = tok.split('-')
        if len(p) < 2:
            continue
        if len(p[0]) == 4 and p[0].isdigit() and p[1].isdigit():
            y, m = int(p[0]), int(p[1])
            if 1 <= m <= 12:
                return y * 100 + m
        if len(p) == 3 and p[1] in MONS and len(p[2]) == 4 and p[2].isdigit():
            return int(p[2]) * 100 + MONS[p[1]]
    return None


def sval(v):
    """Hyper values as the text the older export used, so one set of readers serves both."""
    if v is None:
        return ''
    if isinstance(v, bool):
        return '1' if v else '0'
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return str(v)


def read_wb(path):
    """The workbook's own Extract table as a header plus list[dict] of text values."""
    from tableauhyperapi import HyperProcess, Connection, Telemetry
    if not os.path.exists(path):
        raise SystemExit('ERR sta %s is not where the payload says it is' % path)
    with zipfile.ZipFile(path) as z:
        hy = [n for n in z.namelist() if n.lower().endswith('.hyper')]
        if len(hy) != 1:
            raise SystemExit('ERR sta %s carries %d data tables, expected 1 - the payload presumes '
                             'one row per form' % (os.path.basename(path), len(hy)))
        tmp = tempfile.mkdtemp()
        f = os.path.join(tmp, 'x.hyper')
        with io.open(f, 'wb') as w:
            w.write(z.read(hy[0]))
    try:
        with HyperProcess(Telemetry.DO_NOT_SEND_USAGE_DATA_TO_TABLEAU) as hp:
            with Connection(hp.endpoint, f) as c:
                with c.execute_query('SELECT * FROM "Extract"."Extract"') as r:
                    names = [col.name.unescaped for col in r.schema.columns]
                    rows = [{n: sval(v) for n, v in zip(names, list(x))} for x in r]
    finally:
        try:
            os.remove(f)
            os.rmdir(tmp)
        except OSError:
            pass
    return names, rows


def read_old(form):
    """The 21-Apr-2025 export of the same form, only to carry the ids the workbook lost."""
    d = srcutil.newest({'patterns': [OLD[form] + '*.csv'], 'roots': [RAW], 'exclude': ['~$*']})
    if not d:
        return [], ''
    with io.open(d['path'], encoding='utf-8-sig', errors='replace', newline='') as fh:
        rows = [{(k or '').strip().lstrip(''): (v or '') for k, v in r.items()}
                for r in csv.DictReader(fh)]
    return rows, os.path.basename(d['path'])


def pair(r, cols, dq, why):
    """-> (status, target, covered) where status is ok, blank or void.

    blank means the row records nothing for this pair and is simply absent from the counts. void means
    the row recorded numbers that cannot both be true - covered above target, a negative, or a cell
    that is not a number - and contributes to neither figure, only to the voided column."""
    tr, cr = str(r.get(cols[0]) or '').strip(), str(r.get(cols[1]) or '').strip()
    if not tr and not cr:
        return 'blank', 0, 0
    t, c = num(tr), num(cr)
    if (tr and t is None) or (cr and c is None):
        dq['%s: a cell that is not a number' % why] += 1
        return 'void', 0, 0
    if (t or 0) < 0 or (c or 0) < 0:
        dq['%s: a negative in the pair' % why] += 1
        return 'void', 0, 0
    if (c or 0) > (t or 0):
        dq['%s: covered above target' % why] += 1
        return 'void', 0, 0
    return 'ok', int(round(t or 0)), int(round(c or 0))


def solo(r, col, dq, why):
    """A plain count: blank is 0, a fraction is rounded and counted, a negative voids the cell."""
    s = str(r.get(col) or '').strip()
    v = num(s)
    if v is None:
        if s:
            dq['%s: a cell that is not a number' % why] += 1
        return 0
    if v < 0:
        dq['%s is negative' % why] += 1
        return None
    if v != int(v):
        dq['%s is not a whole number' % why] += 1
    return int(round(v))


def collect(form, rows, alias, years):
    """One form's keepable rows into district x year and district x month cells, the ladder, the
    checklist items and the team/UC books, each at both grains. Every key is a const PTP district
    code. The row void rule fires before either book is written, so the month split is the same sum
    cut finer rather than a second measure - checks() proves the months add back to the years."""
    z = lambda: [0] * len(MEAS)  # noqa: E731
    cells, mcells = collections.defaultdict(z), collections.defaultdict(z)
    lad = collections.defaultdict(lambda: [[0, 0, 0, 0] for _ in LKEY])
    ladM = collections.defaultdict(lambda: [[0, 0, 0, 0] for _ in LKEY])
    itc = collections.defaultdict(lambda: [[0, 0, 0] for _ in IKEY])
    itcM = collections.defaultdict(lambda: [[0, 0, 0] for _ in IKEY])
    tsets, usets, keys = collections.defaultdict(set), collections.defaultdict(set), \
        collections.defaultdict(set)
    kM = collections.defaultdict(set)
    dq, kept = collections.Counter(), 0
    for r in rows:
        kept += 1
        dn = str(r.get('district_name') or '').strip()
        dc, yi = alias[dn.lower()], years.index(mkey(r['date_created']) // 100)
        ym = mkey(r['date_created'])
        slot = yi * 12 + ym % 100 - 1
        v = [0] * len(MEAS)
        v[IDX[RKEY[form]]] = 1
        if form == 'sact':
            for m, cols in PAIR[form].items():
                st, t, c = pair(r, cols, dq, m)
                if st == 'ok':
                    v[IDX[m]], v[IDX[m] + 1] = t, c
                elif st == 'void':
                    v[IDX[m] + 2] = 1
            for m, col in SOLO[form].items():
                s = solo(r, col, dq, m)
                if s is not None:
                    v[IDX[m]] = s
            if v[IDX['sc']] > v[IDX['sp']]:
                dq['sessions conducted exceed sessions planned'] += 1
            ca = mkey(r.get(ACTCOL))
            if ca is not None and ca > PULL:
                dq['activity date after the pull was taken'] += 1
            if ca is None:
                dq['activity date cannot be read'] += 1
            elif ca != ym:
                dq['activity month and entry month differ'] += 1
            for ag in LKEY:
                st, t, c = pair(r, ('target_' + ag, 'coverage_' + ag), dq, 'ladder ' + ag)
                cell = lad[(dc, yi)][LIDX[ag]]
                mcell = ladM[(dc, slot)][LIDX[ag]]
                if st != 'blank':
                    cell[0] += 1
                    mcell[0] += 1
                if st == 'ok':
                    cell[1] += t
                    cell[2] += c
                    mcell[1] += t
                    mcell[2] += c
                elif st == 'void':
                    cell[3] += 1
                    mcell[3] += 1
        else:
            for col in IKEY:
                cell = itc[(dc, yi)][IIDX[col]]
                mcell = itcM[(dc, slot)][IIDX[col]]
                s = str(r.get(col) or '').strip()
                if s == '1':
                    cell[0] += 1
                    mcell[0] += 1
                elif s == '0':
                    cell[1] += 1
                    mcell[1] += 1
                elif s:
                    cell[2] += 1
                    mcell[2] += 1
                    dq['%s answers something other than yes or no' % col] += 1
                else:
                    cell[2] += 1
                    mcell[2] += 1
        uc = str(r.get('uc_name') or '').strip()
        if uc:
            usets[dc].add(uc)
        tc = str(r.get(TEAMCOLS[form]) or '').strip()
        if tc:
            tsets[dc].add(tc)
            keys[dc].add((tc, ym))
            kM[(dc, slot)].add(tc)
        for key, book in (((dc, yi), cells), ((dc, slot), mcells)):
            c = book[key]
            for i in range(len(MEAS)):
                c[i] += v[i]
    yms = sorted({k[1] for k in mcells})
    return dict(cells=cells, mcells=mcells, lad=dict(lad), ladM=dict(ladM), itc=dict(itc),
                itcM=dict(itcM), tsets=tsets, usets=usets,
                keys=keys, kM=dict(kM), kept=kept, dq=dq,
                districts=len({k[0] for k in cells}),
                teams=sum(len(s) for s in tsets.values()),
                ucs=sum(len(s) for s in usets.values()),
                teams_any=len({t for s in tsets.values() for t in s}),
                ucs_any=len({u for s in usets.values() for u in s}),
                first=years[yms[0] // 12] * 100 + yms[0] % 12 + 1 if yms else 0,
                last=years[yms[-1] // 12] * 100 + yms[-1] % 12 + 1 if yms else 0)


def build(repo):
    html = srcutil.read_text(os.path.join(repo, 'index.html'))
    ptp = json.loads(dashpatch.get_payload(html, 'PTP'))
    epim = json.loads(dashpatch.get_payload(html, 'EPIM'))
    years = ptp['yr']
    didx = {d: i for i, d in enumerate(ptp['ds'])}
    if len(ptp['dr']) != len(ptp['ds']) or len(ptp['dv']) != len(ptp['ds']):
        raise SystemExit('ERR sta const PTP ds/dr/dv are no longer parallel arrays')
    # case-insensitive on the panel's own raw codes; a spelling that resolves to two panel districts is
    # removed from the alias map and reported, never guessed onto one
    low = collections.defaultdict(set)
    for i, raw in enumerate(ptp['dr']):
        low[str(raw).lower()].add((ptp['ds'][i], ptp['dv'][i]))
    alias, ambig = {}, []
    for k, v in low.items():
        if len(v) == 1:
            alias[k] = v.pop()[0]
        else:
            ambig.append(k)

    per, srcs = {}, {}
    for form in FORMS:
        names, rows = read_wb(WB[form])
        need = ['unique_id', 'district_name', 'uc_name', 'date_created', 'is_archive',
                TEAMCOLS[form], ACTCOL]
        need += sorted({col for cols in PAIR[form].values() for col in cols})
        need += sorted(SOLO[form].values())
        if form == 'sact':
            need += ['target_' + a for a in LKEY] + ['coverage_' + a for a in LKEY]
        else:
            need += IKEY
        miss = sorted({c for c in need if c not in names})
        if miss:
            raise SystemExit('ERR sta %s has no %s column - the workbook changed shape'
                             % (os.path.basename(WB[form]), ', '.join(miss)))
        read = len(rows)
        seen, kept_rows, drop = set(), [], collections.Counter()
        for r in rows:
            uid = str(r.get('unique_id') or '').strip()
            if uid and uid in seen:
                drop['repeated unique_id'] += 1
                continue
            if uid:
                seen.add(uid)
            if str(r.get('is_archive') or '').strip() == '1':
                drop['archived by the source'] += 1
                continue
            dn = str(r.get('district_name') or '').strip()
            if dn.lower() not in alias:
                drop['district not on the KP district index'] += 1
                continue
            ym = mkey(r.get('date_created'))
            if ym is None:
                drop['no readable entry date'] += 1
                continue
            if ym // 100 not in years:
                drop['year outside the panel window'] += 1
                continue
            kept_rows.append(r)
        # the older export, only for the ids this pull does not hold
        oldrows, oldfile = read_old(form)
        oldids = {str(r.get('unique_id') or '').strip() for r in oldrows}
        carried, odrop = [], collections.Counter()
        for r in oldrows:
            uid = str(r.get('unique_id') or '').strip()
            if not uid or uid in seen:
                continue
            if str(r.get('is_archive') or '').strip() == '1':
                odrop['carried row archived by the source'] += 1
                continue
            if str(r.get('district_name') or '').strip().lower() not in alias:
                odrop['carried district not on the KP index'] += 1
                continue
            if mkey(r.get('date_created')) is None:
                odrop['carried row has no readable entry date'] += 1
                continue
            if mkey(r['date_created']) // 100 not in years:
                odrop['carried year outside the panel window'] += 1
                continue
            carried.append(r)
        if len(carried) > max(20, 0.05 * len(oldrows)):
            raise SystemExit('ERR sta %s: %d of the %d ids in %s are missing from the workbook - that '
                             'is a different cut of the form, not a later pull, so the two must not be '
                             'unioned' % (form, len(carried), len(oldrows), oldfile))
        kept_rows.extend(carried)
        srcs[form] = {'wb': os.path.basename(WB[form]), 'wb_rows': read, 'wb_ids': len(seen),
                      'older': oldfile, 'older_rows': len(oldrows), 'older_ids': len(oldids),
                      'shared': len(oldids & seen), 'older_only': len(oldids - seen),
                      'workbook_only': len(seen - oldids), 'carried': len(carried),
                      'carried_drop': dict(odrop)}
        per[form] = collect(form, kept_rows, alias, years)
        per[form]['drop'], per[form]['read'], per[form]['carried'] = drop, read, len(carried)
    return ptp, epim, per, srcs, didx, years, alias, ambig


def ladder_voids(per):
    """The one test a ladder column has to pass, run on the province totals.

    Every kept row already satisfies covered <= target, so the sums do too and the aggregate cannot
    disagree. What can fail is the column itself: a form field that is filled with a coverage number
    and almost never with a target contradicts itself in a third of its rows, and no total built from
    it means anything. The cut is a fifth of the rows that recorded the pair - the worst a used column
    manages is ipv_1 at 7.8% and td sits at 33.3% - and it is computed from this pull, not assumed."""
    tot = collections.defaultdict(lambda: [0, 0, 0, 0])  # rows, target, covered, voided
    for cells in per['sact']['lad'].values():
        for x, v in enumerate(cells):
            for i in range(4):
                tot[x][i] += v[i]
    out = collections.OrderedDict()
    for x, ag in enumerate(LKEY):
        n, t, c, vd = tot[x]
        if n and vd * 5 > n:
            out[ag] = ['the coverage column is filled where the target column is not', t, c, vd, n]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--source', help='accepted for refresh.py run; the workbooks are named in full')
    a = ap.parse_args()
    cfg = srcutil.load_sources()
    repo = cfg['repo']
    ptp, epim, per, srcs, didx, years, alias, ambig = build(repo)

    dists = sorted({k[0] for f in FORMS for k in per[f]['cells']}, key=lambda d: didx[d])

    rows = []
    for dn in dists:
        ycs, mcs = [], []
        for j in range(len(years)):
            v = [0] * len(MEAS)
            for f in FORMS:
                c = per[f]['cells'].get((dn, j))
                if c:
                    v = [x + y for x, y in zip(v, c)]
            if any(v):
                ycs.append([j, v])
        for slot in sorted({k[1] for f in FORMS for k in per[f]['mcells'] if k[0] == dn}):
            v = [0] * len(MEAS)
            for f in FORMS:
                c = per[f]['mcells'].get((dn, slot))
                if c:
                    v = [x + y for x, y in zip(v, c)]
            if any(v):
                mcs.append([slot, v])
        rows.append([didx[dn], ycs, mcs])

    LADDER_VOID.update(ladder_voids(per))
    lad = []
    for (dn, j), cells in sorted(per['sact']['lad'].items()):
        for x, ag in enumerate(LKEY):
            if ag in LADDER_VOID or not any(cells[x]):
                continue
            lad.append([didx[dn], j, x] + cells[x])
    alm = []
    for (dn, slot), cells in sorted(per['sact']['ladM'].items()):
        for x, ag in enumerate(LKEY):
            if ag in LADDER_VOID or not any(cells[x]):
                continue
            alm.append([didx[dn], slot, x] + cells[x])

    # an item no row ever answered is not a measure; it is a blank form field
    ans = collections.Counter()
    for cells in per['smon']['itc'].values():
        for x, v in enumerate(cells):
            ans[IKEY[x]] += v[0] + v[1]
    never = [c for c in IKEY if not ans[c]]
    dropi = set(IKEY) - set(never)
    itc = []
    for (dn, j), cells in sorted(per['smon']['itc'].items()):
        for x, col in enumerate(IKEY):
            if col not in dropi or not any(cells[x]):
                continue
            itc.append([didx[dn], j, x] + cells[x])
    itm = []
    for (dn, slot), cells in sorted(per['smon']['itcM'].items()):
        for x, col in enumerate(IKEY):
            if col not in dropi or not any(cells[x]):
                continue
            itm.append([didx[dn], slot, x] + cells[x])

    ev = []
    for dn in dists:
        one = [didx[dn]]
        for f in FORMS:
            one.append(len(per[f]['tsets'].get(dn, ())))
            one.append(len(per[f]['usets'].get(dn, ())))
        ev.append(one)

    lnk = []
    for dn in dists:
        ka, kb = per['sact']['keys'].get(dn, set()), per['smon']['keys'].get(dn, set())
        if ka or kb:
            lnk.append([didx[dn], len(ka), len(kb), len(ka & kb)])
    # one month of these is a distinct-team count, because the month is already fixed by the key
    lnkm = []
    for dn in dists:
        for slot in sorted({k[1] for k in per['sact']['kM'] if k[0] == dn}
                           | {k[1] for k in per['smon']['kM'] if k[0] == dn}):
            ka = per['sact']['kM'].get((dn, slot), set())
            kb = per['smon']['kM'].get((dn, slot), set())
            lnkm.append([didx[dn], slot, len(ka), len(kb), len(ka & kb)])

    spans, gaps, firsts, lasts = {}, {}, {}, {}
    for f in FORMS:
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

    # the EPI register, summed over the months both sources cover
    ed = collections.defaultdict(lambda: [0, 0, 0, 0])  # opv3, bcg, months, rows
    edM = collections.defaultdict(lambda: [0, 0])       # opv3, bcg for one month
    for r in epim:
        ym = mkey(r.get('mo'))
        if ym is None or not (EPI_FROM <= ym <= EPI_TO):
            continue
        g = ed[r.get('ed')]
        g[0] += r.get('opv3') or 0
        g[1] += r.get('bcg') or 0
        g[2] += 1
        g[3] += 1
        gm = edM[(r.get('ed'), ym)]
        gm[0] += r.get('opv3') or 0
        gm[1] += r.get('bcg') or 0
    if EPI_FROM // 100 not in years or EPI_TO // 100 not in years:
        raise SystemExit('ERR sta const PTP has no year for the EPI comparison window')
    tri, trim, emons = [], [], set()
    zv = [0] * len(MEAS)
    for dn in dists:
        e = ed.get(dn)
        if not e:
            continue
        v = [0] * len(MEAS)
        bym = {}
        for (cd, slot), c in per['sact']['mcells'].items():
            if cd != dn:
                continue
            ym = years[slot // 12] * 100 + slot % 12 + 1
            if EPI_FROM <= ym <= EPI_TO:
                v = [x + y for x, y in zip(v, c)]
                emons.add(ym)
                bym[ym] = c
        if any(v):
            tri.append([didx[dn], e[0], e[1], v[IDX['o3C']], v[IDX['zdC']], v[IDX['actR']]])
            for ym in sorted(set(bym) | {m for (d2, m) in edM if d2 == dn}):
                slot = years.index(ym // 100) * 12 + ym % 100 - 1
                c = bym.get(ym, zv)
                gm = edM.get((dn, ym), [0, 0])
                trim.append([didx[dn], slot, gm[0], gm[1],
                             c[IDX['o3C']], c[IDX['zdC']], c[IDX['actR']]])
    emons = sorted(emons)

    n = {}
    for f in FORMS:
        r = per[f]
        n[f] = {'read': r['read'], 'kept': r['kept'], 'carried': r['carried'],
                'districts': r['districts'], 'teams': r['teams'], 'ucs': r['ucs'],
                'teams_any': r['teams_any'], 'ucs_any': r['ucs_any'],
                'drop': dict(r['drop']), 'dq': dict(r['dq'])}
    for k in MEAS:
        n[k] = sum(c[IDX[k]] for f in FORMS for c in per[f]['cells'].values())
    n['rows'] = sum(per[f]['kept'] for f in FORMS)
    n['district_rows'] = len(rows)
    n['ladder'] = collections.OrderedDict()
    for x, ag in enumerate(LKEY):
        t = [0, 0, 0, 0]
        for cells in per['sact']['lad'].values():
            for i in range(4):
                t[i] += cells[x][i]
        n['ladder'][ag] = t
    n['items'] = collections.OrderedDict()
    for x, col in enumerate(IKEY):
        t = [0, 0, 0]
        for cells in per['smon']['itc'].values():
            for i in range(3):
                t[i] += cells[x][i]
        n['items'][col] = t
    n['link'] = [sum(r[1] for r in lnk), sum(r[2] for r in lnk), sum(r[3] for r in lnk)]

    checks(per, rows, lad, alm, itc, itm, ev, lnk, lnkm, tri, trim, years, ptp, n, dists, srcs, never)
    out = {'gen': dashpatch.pkt_stamp(),
           'asof': '28-Sep-2026 (both workbook pulls)',
           'src': {f: srcs[f]['wb'] for f in FORMS},
           'older': {f: srcs[f]['older'] for f in FORMS},
           'vint': srcs,
           'yr': years, 'win': '%d-%d' % (years[0], years[-1]),
           'mk': MEAS, 'mkl': [ML[k] for k in MEAS],
           'ek': EK,
           'lk': ['team-months with an activity report', 'team-months with a checklist',
                  'team-months with both'],
           'tk': TK,
           'ag': LKEY, 'agl': [LAB[a] for a in LKEY],
           'agvoid': collections.OrderedDict(
               (a, LADDER_VOID[a]) for a in LKEY if a in LADDER_VOID),
           'ik': IKEY, 'ikl': [ILAB[c] for c in IKEY],
           'iyes': [c for c in IKEY if c not in set(never)],
           'inever': never,
           'epi': {'per': '%d-%02d to %d-%02d' % (EPI_FROM // 100, EPI_FROM % 100,
                                                  EPI_TO // 100, EPI_TO % 100),
                   'months': ['%d-%02d' % (m // 100, m % 100) for m in emons],
                   'src': 'const EPIM (district x month facility EPI register)'},
           'pairs': [{'id': m, 'label': PAIRL[m], 'source': 'IDIMS ' + srcs['sact']['wb']}
                     for m in PAIR['sact']],
           'forms': [{'id': f, 'label': LABEL[f], 'row': ROWIS[f], 'cols': FORM_MEAS[f],
                      'span': spans[f], 'first': firsts[f], 'last': lasts[f], 'gap': gaps[f],
                      'rows': n[f]['kept'], 'districts': n[f]['districts'],
                      'teams': n[f]['teams'], 'ucs': n[f]['ucs']} for f in FORMS],
           'spans': spans, 'first': firsts, 'last': lasts, 'gap': gaps,
           'ds': dists, 'dv': [ptp['dv'][didx[x]] for x in dists],
           'd': rows, 'al': lad, 'alM': alm, 'it': itc, 'itM': itm, 'ev': ev,
           'lnk': lnk, 'lnkM': lnkm, 'tri': tri, 'triM': trim, 'n': n,
           'hold': ['the reporter names, the address they sign with, the entry and update ids, and the '
                    'vaccinator, monitor and focal-person name columns',
                    'position coordinates and their accuracy (a public site)',
                    'every free-text note, including why a row was archived',
                    'the reporting body and the post columns - who filed the form, not what it did',
                    'the bare dose columns (zero_dose, bcg, opv_*, penta_*, pneumo_*, rota_*, ipv_*, '
                    'mr_*, td, new_born, ipv_booster): blank in all 26,806 activity rows',
                    'un_recorded_<antigen>_coverage - a third number that reconciles with the pair in '
                    'none of the rows checked',
                    '; '.join('%s: %s - %s covered against %s target, %s of %s rows that recorded it '
                              'contradicted themselves'
                              % (a, w[0], format(w[2], ','), format(w[1], ','), w[3], w[4])
                              for a, w in LADDER_VOID.items())
                    or 'no ladder column had to be withheld for its arithmetic',
                    'checklist fields no row ever answered: ' + ', '.join(never) if never else
                    'no checklist field was left completely unanswered'],
           'note': 'district x year and district x month counts of the two search-team IDIMS forms as '
                   'pulled into the owner\'s two Tableau workbooks on 28-Sep-2026, which contain the '
                   '21-Apr-2025 export of the same forms in full apart from the ids counted in carried; '
                   'keyed on the same district index and month slots as const PTP, const PTPM and const '
                   'MTM, so the PTP period picker drives all four grids; every month is the month the '
                   'entry was made, never the activity date, which disagrees with it in a sixth of the '
                   'rows; the dose data this form carries is the target/covered pair per antigen, '
                   'because its bare dose columns are empty; a pair whose covered exceeds its target, '
                   'or holds a negative or an unreadable cell, contributes to neither figure and is '
                   'counted in the voided column beside them; a ladder column failing the same test in '
                   'aggregate, or in most of its rows, is withheld and named with its numbers; teams '
                   'and union councils are counted inside their own district and the province figure is '
                   'the sum of those, because team numbers repeat across districts; the EPI comparison '
                   'puts two registers of the same districts side by side and is not a coverage rate; '
                   'rows and checklists are counts of forms, not of children'}
    sweep(out, ptp)
    js = srcutil.dumps(out)
    srcutil.write_text(a.out or os.path.join(srcutil.OUT, 'sta.json'), js)
    print('OK sta %d %s' % (len(js), ' '.join('%s %s->%s' % (f, spans[f], format(n[f]['kept'], ','))
                                              for f in FORMS)))
    print('VINT sta %s' % json.dumps(srcs, ensure_ascii=False))
    print('TOTALS sta reports %s checklists %s districts %s rows %s'
          % (format(n['actR'], ','), format(n['monR'], ','), n['district_rows'],
             format(n['rows'], ',')))
    for m in PAIR['sact']:
        print('PAIR sta %-4s target %s covered %s voided rows %s (%s)'
              % (m, format(n[m], ','), format(n[MEAS[IDX[m] + 1]], ','),
                 format(n[MEAS[IDX[m] + 2]], ','), PAIRL[m]))
    for m, col in SOLO['sact'].items():
        print('SOLO sta %-3s %s = %s (%s)' % (m, col, format(n[m], ','), SOLOL[m]))
    print('LADDER sta %d of %d antigens published over %d district-year cells'
          % (len(LKEY) - len(LADDER_VOID), len(LKEY), len(lad)))
    for a_, why in LADDER_VOID.items():
        print('VOID sta %s: %s - target %s covered %s voided %d of %d rows that recorded it'
              % (a_, why[0], format(why[1], ','), format(why[2], ','), why[3], why[4]))
    print('ITEMS sta %d answered of %d checklist columns over %s checklists'
          % (len(out['iyes']), len(IKEY), format(n['monR'], ',')))
    if never:
        print('NEVER sta %s' % ', '.join(never))
    print('LINK sta %s activity team-months, %s checklist team-months, %s with both'
          % tuple(n['link']))
    print('EPI  sta triangulated against %d months of const EPIM for %d districts'
          % (len(emons), len(tri)))
    if ambig:
        print('AMBIG sta panel raw codes resolving to two districts: %s' % ', '.join(ambig))
    for f in FORMS:
        print('BREADTH sta:%s districts %s teams %s (numbers %s) ucs %s (names %s)'
              % (f, per[f]['districts'], per[f]['teams'], per[f]['teams_any'],
                 per[f]['ucs'], per[f]['ucs_any']))
        print('      sta:%s %s' % (f, sorted({k[0] for k in per[f]['cells']})))
        print('DROP sta:%s %s' % (f, per[f]['drop']))
        print('DQ   sta:%s %s' % (f, dict(per[f]['dq'])))
        print('GAP  sta:%s %s' % (f, gaps[f]))
    return out


def sweep(obj, ptp):
    """The cell arrays must be pure numbers, the district list must be the one the dashboard already
    publishes, and no withheld field name may reach a published string. Checked on the data, not on
    hold: naming what is refused is the point of that list."""
    for part in ('d', 'al', 'alM', 'it', 'itM', 'ev', 'lnk', 'lnkM', 'tri', 'triM'):
        s = json.dumps(obj[part])
        if not re.fullmatch(r'[\[\],:\s\-0-9]+', s):
            raise SystemExit('ERR sta the %s arrays hold something other than numbers' % part)
    for f in obj['forms']:
        for key in ('label', 'row', 'span', 'id'):
            v = str(f[key])
            if any(b in v.lower() for b in BANNED) or '@' in v:
                raise SystemExit('ERR sta the %s field of form %s reads %r' % (key, f['id'], v))
    if not all(x in set(ptp['ds']) for x in obj['ds']):
        raise SystemExit('ERR sta a district outside const PTP reached the payload')
    for key in ('mk', 'mkl', 'ek', 'lk', 'tk', 'ag', 'agl', 'ik', 'ikl', 'inever'):
        s = json.dumps(obj[key], ensure_ascii=False).lower()
        hit = [b for b in BANNED if b in s]
        if hit or '@' in s:
            raise SystemExit('ERR sta the %s field mentions %s' % (key, ', '.join(hit) or '@'))
    for p in obj['pairs']:
        s = (p['label'] + p['id'] + p['source']).lower()
        if any(b in s for b in BANNED) or '@' in s:
            raise SystemExit('ERR sta the %s pair label leaks a withheld field' % p['id'])
    s = json.dumps(obj['n'], ensure_ascii=False).lower()
    hit = [b for b in BANNED if b in s]
    if hit or '@' in s:
        raise SystemExit('ERR sta the row-accounting block mentions %s' % ', '.join(hit) or '@')


def checks(per, rows, lad, alm, itc, itm, ev, lnk, lnkm, tri, trim, years, ptp, n, dists, srcs, never):
    """Abort rather than publish a payload whose cells do not add back."""
    def roll(what, cols, ys, ms):
        """A district x year cell has to be the sum of that district's month cells in that year: the
        period picker narrows these grids by reading the month book, so the finer cut is checked
        against the coarser one rather than assumed to agree with it."""
        seen = {(r[0], r[1], r[2]) for r in ys}
        acc = collections.defaultdict(list)
        for r in ms:
            j = r[1] // 12
            if not 0 <= j < len(years):
                raise SystemExit('ERR sta %s month slot %s falls outside the panel window'
                                 % (what, r[1]))
            if (r[0], j, r[2]) not in seen:
                raise SystemExit('ERR sta %s %s %s has month cells in %s with no year cell behind them'
                                 % (what, ptp['ds'][r[0]], cols[r[2]], years[j]))
            acc[(r[0], j, r[2])].append(r[3:])
        for r in ys:
            g = acc.get((r[0], r[1], r[2]), [])
            sm = [sum(c[i] for c in g) for i in range(len(r) - 3)]
            if sm != list(r[3:]):
                raise SystemExit('ERR sta %s %s %s year %s reads %s but its month cells add to %s'
                                 % (what, ptp['ds'][r[0]], cols[r[2]], years[r[1]], list(r[3:]), sm))
    for f in FORMS:
        r = per[f]
        rs = sum(c[IDX[RKEY[f]]] for c in r['cells'].values())
        ms = sum(c[IDX[RKEY[f]]] for c in r['mcells'].values())
        if not (rs == ms == r['kept']):
            raise SystemExit('ERR sta %s cells do not add back to its kept rows: year %s month %s '
                             'kept %s' % (f, rs, ms, r['kept']))
        if r['read'] - sum(r['drop'].values()) + r['carried'] != r['kept']:
            raise SystemExit('ERR sta %s read %s - drops %s + carried %s != kept %s'
                             % (f, r['read'], sum(r['drop'].values()), r['carried'], r['kept']))
        if r['kept'] != r['read'] - sum(r['drop'].values()) + srcs[f]['carried']:
            raise SystemExit('ERR sta %s the carry reported to the payload is not the carry used' % f)
    for didx_i, ycs, mcs in rows:
        dn = ptp['ds'][didx_i]
        for slot, v in mcs:
            y = [c for c in ycs if c[0] == slot // 12]
            if not y:
                raise SystemExit('ERR sta %s has month cell slot %s with no year cell' % (dn, slot))
            for i, k in enumerate(MEAS):
                if v[i] > y[0][1][i]:
                    raise SystemExit('ERR sta %s month %s exceeds its year cell on %s (%s > %s)'
                                     % (dn, k, slot, v[i], y[0][1][i]))
        for j, yv in ycs:
            sm = [v for s, v in mcs if s // 12 == j]
            for i, k in enumerate(MEAS):
                s = sum(x[i] for x in sm)
                if s != yv[i]:
                    raise SystemExit('ERR sta %s year %s does not equal its month cells on %s '
                                     '(%s != %s)' % (dn, years[j], k, s, yv[i]))
    for m in PAIR['sact']:
        cov, vd = MEAS[IDX[m] + 1], MEAS[IDX[m] + 2]
        if n[cov] > n[m]:
            raise SystemExit('ERR sta province covered %s exceeds target %s on %s'
                             % (n[cov], n[m], m))
        if n[vd] > n[m] + n[cov]:
            raise SystemExit('ERR sta %s voids more rows than the form has targets or coverage' % m)
    if n['sc'] > n['sp']:
        raise SystemExit('ERR sta sessions conducted %s exceed planned %s' % (n['sc'], n['sp']))
    for x, ag in enumerate(LKEY):
        t = n['ladder'][ag]
        if ag in LADDER_VOID:
            if not any(t):
                raise SystemExit('ERR sta %s is withheld but has no numbers to explain why' % ag)
            continue
        if t[2] > t[1]:
            raise SystemExit('ERR sta ladder %s covered %s exceeds target %s after the voids'
                             % (ag, t[2], t[1]))
        if t[0] and t[3] * 5 > t[0]:
            raise SystemExit('ERR sta ladder %s contradicts itself in a fifth of its rows but was '
                             'not withheld' % ag)
    al = collections.defaultdict(lambda: [0, 0, 0, 0])
    for r in lad:
        for i in range(4):
            al[r[2]][i] += r[3 + i]
    for x, ag in enumerate(LKEY):
        if ag not in LADDER_VOID and al[x] != n['ladder'][ag]:
            raise SystemExit('ERR sta ladder %s published cells do not add back to the totals' % ag)
    roll('ladder', LKEY, lad, alm)
    roll('checklist item', IKEY, itc, itm)
    for e in ev:
        for i, k in enumerate(EK):
            f = k[:-2]
            if e[i + 1] > per[f]['kept']:
                raise SystemExit('ERR sta %s claims more %s than the form has rows'
                                 % (ptp['ds'][e[0]], k))
    for r in lnk:
        if r[3] > min(r[1], r[2]) or r[1] > per['sact']['kept'] or r[2] > per['smon']['kept']:
            raise SystemExit('ERR sta %s team-month link counts do not bound' % ptp['ds'][r[0]])
    if sum(r[1] for r in lnk) != n['link'][0] or sum(r[3] for r in lnk) != n['link'][2]:
        raise SystemExit('ERR sta the team-month link does not add back to its district rows')
    lm = collections.defaultdict(lambda: [0, 0, 0])
    for r in lnkm:
        if not 0 <= r[1] // 12 < len(years):
            raise SystemExit('ERR sta team-month month slot %s falls outside the panel window' % r[1])
        for i in range(3):
            lm[r[0]][i] += r[2 + i]
    if {r[0] for r in lnkm} != {r[0] for r in lnk}:
        raise SystemExit('ERR sta the team-month months list a different district set than the '
                         'whole-window block')
    for r in lnk:
        if lm[r[0]] != list(r[1:]):
            raise SystemExit('ERR sta %s team-months add over the months to %s, not to the '
                             'whole-window %s' % (ptp['ds'][r[0]], lm[r[0]], list(r[1:])))
    for r in tri:
        if r[3] > r[1]:
            raise SystemExit('ERR sta %s search-team OPV-3 covered %s exceeds the whole EPI register '
                             'of %s - the comparison is being read the wrong way round'
                             % (ptp['ds'][r[0]], r[3], r[1]))
    tm = collections.defaultdict(lambda: [0] * 5)
    for r in trim:
        if not 0 <= r[1] // 12 < len(years):
            raise SystemExit('ERR sta EPI comparison month slot %s falls outside the panel window'
                             % r[1])
        for i in range(5):
            tm[r[0]][i] += r[2 + i]
    if {r[0] for r in trim} != {r[0] for r in tri}:
        raise SystemExit('ERR sta the EPI comparison months list a different district set than the '
                         'window block')
    for r in tri:
        if tm[r[0]] != list(r[1:]):
            raise SystemExit('ERR sta %s EPI comparison months add to %s, not to the window %s'
                             % (ptp['ds'][r[0]], tm[r[0]], list(r[1:])))
    for dn in dists:
        if dn not in set(ptp['ds']):
            raise SystemExit('ERR sta a district outside const PTP reached the payload')
    it = collections.defaultdict(lambda: [0, 0, 0])
    for r in itc:
        for i in range(3):
            it[r[2]][i] += r[3 + i]
    for x, col in enumerate(IKEY):
        t = n['items'][col]
        answered = col not in set(never)
        if answered and it[x] != t:
            raise SystemExit('ERR sta checklist item %s published cells do not add back' % col)
        if not answered and any(t[:2]):
            raise SystemExit('ERR sta checklist item %s is called never-answered but has answers' % col)
        if answered and t[0] + t[1] == 0:
            raise SystemExit('ERR sta checklist item %s answers nothing but was kept' % col)
    for k, v in n['items'].items():
        if sum(v) > per['smon']['kept']:
            raise SystemExit('ERR sta checklist item %s is counted more times than checklists kept' % k)


if __name__ == '__main__':
    main()
