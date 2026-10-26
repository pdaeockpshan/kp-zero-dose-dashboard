# -*- coding: utf-8 -*-
"""Register the mobile and migrant team dataset (mtm) in _refresh/sources.json, after the ptpm entry.
Running it again replaces the entry, so a note edit can be re-applied without hand-editing the JSON."""
import io
import json
import os

R = r'C:\Users\HD\Documents\kp-zero-dose-dashboard'
P = os.path.join(R, '_refresh', 'sources.json')
note = (
    "Six HRMP mobile-team exports in the same Raw IDIMS folder as the three PTP field-check forms, "
    "pulled together on 21-Apr-2025 and never re-pulled: Migrant_and_Mobile_Populations_Mapping_Form-174 "
    "(one row per mapping record), Nomads_immunization_team_activity_-130 and "
    "Search_Team_Activity-157 and Special_Biker_Teams__Coverage-178 (one row per team activity or "
    "coverage report) and Monitoring_checklist_Nomads_immunization_team_-137 and "
    "Search_Team_Monitoring_Checklist-158 (one row per monitoring checklist). Aggregated to district x "
    "year and district x month on the same district index, year list and month-slot arithmetic as const "
    "PTP and const PTPM, so the PTP tab drives all three grids from one period picker. One spelling in "
    "the mapping form is not on the KP district index (KOLAIPALAS, 2 rows) and is dropped under a named "
    "reason rather than guessed onto a district. Every month is the month the entry was made: only three "
    "of the six carry a separate activity date, and those disagree with the entry month in 12.8% of "
    "search-team and 8% of biker rows. Team numbers repeat across districts - the nomad form holds 23 "
    "distinct numbers province-wide but 63 once scoped to their district, the biker form 29 against 82 - "
    "so team counts are district-scoped unions and the province figure is the sum of those; the export "
    "carries no province-wide team id. Published: rows filed, as one column per form rather than one "
    "shared total so a period view can say which form filed them, mapping records by household origin "
    "(origin_country 1 is Pakistan-origin and 2 Afghan-origin, proven by orgin_dist_pak being blank in "
    "31,694 of 31,694 Afghan-origin rows and filled in 83,206 of 83,207 Pakistan-origin ones), sessions "
    "planned against sessions conducted, children missed as not available or as a refusal, under-two "
    "zero-dose recorded, EPI cards issued, biker refusals and not-availables recorded against still "
    "open, and AFP and AEFI tallies. Held out: every name, email, user id, designation, coordinate, "
    "free-text remark and settlement or area name (public site); every target_*, coverage_* and "
    "un_recorded_*_coverage column, which is the same field family the PTP panel holds out under the "
    "open IDIMS report-definition question - in these exports they are child counts rather than "
    "percentages, but coverage exceeds target in 4,245 of 103,143 search rows and one target_ipv_1 is "
    "-3, so nothing is published on them until the definition is confirmed; the bare dose columns, "
    "empty in every live search-team row and sitting in the nomad form beside three mutually "
    "inconsistent OPV tallies (vacc_opv 203,129 against opv_does1+2+3 192,307 against target_opv "
    "245,337); no_of_families and no_of_child, whose median is 3 but where 906 rows carry more than 100 "
    "children, up to 7,640 in one mapping record, a tail holding 20% of the province sum; mmp_types, "
    "hrmp_type, riadmin, duration (max 100,000,000), mob_pop_card_issued (max 3,134 in one session), "
    "team_planned (0, 1 and 8) and every checklist item column, all integer answer codes with no "
    "caption - and in the two monitoring checklists items_checked, data_Recording, vaccination and "
    "search_team are blank in every row. The extractor aborts unless each form's month cells add back "
    "to its year cells and to its kept-row count, no cell exceeds its year cell on any column, every "
    "read row is kept or dropped under a named reason, the origin split adds back to the mapping rows, "
    "the province sessions-conducted total does not exceed sessions-planned, the biker still-open "
    "tallies do not exceed their recorded columns, and the emitted cell arrays contain nothing but "
    "numbers. A negative in a published count column voids that one cell and is counted rather than "
    "fatal or silently added: one search-team row at Peshawar writes session_conducted -2, the visit "
    "happened so the row and its other columns stand, and the column is the sum of the usable values.")

s = json.load(io.open(P, encoding='utf-8'))
lines = io.open(P, encoding='utf-8', newline='').read().split('\n')


def take_out():
    """Re-registering edits the note, so drop the block that is already there first. The block is
    the one inserted below: it starts at '  "mtm": {' and the line before it is the ptpm close with a
    comma added, which goes back the way it came."""
    if 'mtm' not in s['auto']:
        return
    i = lines.index('  "mtm": {')
    j = i
    while not lines[j].startswith('  }'):
        j += 1
    assert lines[i - 1] == '  },', repr(lines[i - 1])
    del lines[i:j + 1]
    lines[i - 1] = '  }'


take_out()
entry = {'label': 'HRMP mobile and migrant teams: the six unmapped IDIMS forms (const MTM)',
         'const': 'MTM', 'extractor': 'extract_mtm.py',
         'roots': [r'C:\Users\HD\Dropbox\Joint Database\3. HRMP\Raw IDIMS FIles'],
         'patterns': ['Migrant_and_Mobile_Populations_Mapping_Form-174*.csv',
                      'Nomads_immunization_team_activity_-130*.csv',
                      'Monitoring_checklist_Nomads_immunization_team_-137*.csv',
                      'Search_Team_Activity-157*.csv',
                      'Search_Team_Monitoring_Checklist-158*.csv',
                      'Special_Biker_Teams__Coverage-178*.csv'],
         'exclude': ['~$*'],
         'portal': 'IDIMS > HRMP mobile and migrant team exports (raw folder, not re-pulled since '
                   '21-Apr-2025)',
         'note': note}
raw = json.dumps(entry, ensure_ascii=False, indent=1, sort_keys=True).split('\n')
body = ['  "mtm": {'] + [' ' + l for l in raw[1:-1]] + ['  }']
i = [n for n, l in enumerate(lines) if l.startswith('  "ptpm": {')]
assert len(i) == 1, i
j = i[0]
while not lines[j].startswith('  }'):
    j += 1
lines[j] = lines[j] + ',\n' + '\n'.join(body)
io.open(P, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
s2 = json.load(io.open(P, encoding='utf-8'))
print('OK mtm registered; auto keys = %s' % sorted(s2['auto']))
print('note chars %d' % len(s2['auto']['mtm']['note']))
