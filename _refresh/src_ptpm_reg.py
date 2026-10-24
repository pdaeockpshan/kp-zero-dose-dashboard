# -*- coding: utf-8 -*-
"""Register the PTP field-monitoring dataset (ptpm) in _refresh/sources.json, after the ptp entry."""
import io
import json
import os

R = r'C:\Users\HD\Documents\kp-zero-dose-dashboard'
P = os.path.join(R, '_refresh', 'sources.json')
note = (
    "Three HRMP checklist exports in the Raw IDIMS folder, one payload: PTPs-STPs_Monitoring_"
    "Checklist-176 (one row per monitoring visit), PTPs-STPs_Spot_Survey_Checklist-52 (one row per "
    "spot survey) and PTPs-STPs_Logistic_Check_List-51 (one row per logistics check). Aggregated to "
    "district x year and district x month on the same district index and the same month-slot "
    "arithmetic as const PTP, so the PTP tab can drive both grids from one period picker. Posts join "
    "on ptp_loc = the coverage panel's Site_ID (250 of 258 monitored, 450 of 460 surveyed, 358 of 365 "
    "logistics-checked posts are on the Oct-2026 panel; the remainder are counted as off-panel, not "
    "dropped). The field data stops where these exports stop (21-Apr-2025) and the reporting panel "
    "runs to Oct-2026, so no monitoring period overlaps the current reporting period and the block "
    "says so instead of drawing an empty 2026. Monitoring months come from date_conducted; the spot "
    "and logistics exports have no conduct date, so their months are entry months. Published: "
    "checklist/survey/logistics counts, distinct posts reached, teams present and teams monitored. "
    "Held out: every name, email, designation, CNIC-derived field, free-text remarks and the "
    "per-row latitude/longitude (public site); the integer answer codes shift, docs_avail, app_loc, "
    "post_identity, team_identity, security_pres, sup_visit, secu_assist1, site_type and "
    "incoming_type, which no caption in the export or in the three .twbx workbooks beside them "
    "decodes; teams_trained, teams_adult, teams_local, teams_zero_dose, teams_local_lang, "
    "carr_tall_avail, vial_maint and vacc_match, which agree with teams_monitored in 99.2-99.8% of "
    "rows because the form mirrors one answer across them; total_team and transit_teams, sane in "
    "15,094 rows but 202 teams at a post where 2 were present and 141 where 1 was in the rest; the "
    "up_to_10/above_10/*_fm/nofm family (233 of 20,219 rows, all site_type 9) alongside the "
    "up_to_5/nofm_5 family (19,986 rows, all site_type 1) - two survey designs in one table that "
    "must not be blended; and the 15 logistics item families (ilr, ilrn, ref, cab, bann, jack, pcap, "
    "id, paper, stand, cooler, vcarr, humber, chair, other x total/available/workable/nrepair/"
    "nreplace), whose abbreviations are undefined and whose available exceeds total in 846 family "
    "rows. The extractor aborts unless each source's month cells add back to its year cells and to "
    "its kept-row count, no month cell exceeds its year cell on any column, every read row is either "
    "kept or dropped under a named reason, and no post is monitored under two districts.")

s = json.load(io.open(P, encoding='utf-8'))
entry = {'label': 'PTP field monitoring: HRMP checklist, spot-survey and logistics exports (const PTPM)',
         'const': 'PTPM', 'extractor': 'extract_ptpm.py',
         'roots': [r'C:\Users\HD\Dropbox\Joint Database\3. HRMP\Raw IDIMS FIles'],
         'patterns': ['PTPs-STPs_Monitoring_Checklist*.csv', 'PTPs-STPs_Spot_Survey_Checklist*.csv',
                      'PTPs-STPs_Logistic_Check_List*.csv'],
         'exclude': ['~$*'],
         'portal': 'IDIMS > HRMP field monitoring exports (raw folder, not re-pulled since 21-Apr-2025)',
         'note': note}
assert 'ptpm' not in s['auto']
raw = json.dumps(entry, ensure_ascii=False, indent=1, sort_keys=True).split('\n')
body = ['  "ptpm": {'] + [' ' + l for l in raw[1:-1]] + ['  }']
lines = io.open(P, encoding='utf-8', newline='').read().split('\n')
i = [n for n, l in enumerate(lines) if l.startswith('  "ptp": {')]
assert len(i) == 1, i
j = i[0]
while not lines[j].startswith('  }'):
    j += 1
lines[j] = lines[j] + ',\n' + '\n'.join(body)
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
s2 = json.load(io.open(P, encoding='utf-8'))
print('OK ptpm registered; auto keys = %s' % sorted(s2['auto']))
print('note chars %d' % len(s2['auto']['ptpm']['note']))
