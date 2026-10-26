"""Document mtm and sta in _refresh/SOURCES.md and correct the ptp row's refresh claim.

SOURCES.md is hand-kept, so this is line surgery with asserts: two rows appended to the
AUTO table, one sentence replaced exactly once. `--unpatch` restores the file byte for byte.
"""
import argparse
import io
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
DOC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SOURCES.md')

ROUTE = ('**Registered in `auto`, not yet driven by `run`.** Being in `auto` is what makes '
         '`refresh.py status` watch the source for staleness and shows the embedded payload size; '
         '`run` cannot land this payload yet because `swap_payload` needs `const %s` in every '
         'variant and it exists in the master alone until `push_master.py` carries the block to the '
         'other three (that sync counts as publishing and needs the owner\'s word). Worse, while the '
         'master differs from `preview`/`public` the identical-group assert at the end of `run` and '
         '`inject` aborts *every* dataset before anything is written - `index.html`, `preview.html` '
         'and `public/index.html` diverged as of 26-Oct-2026 because the `MTM` (`capMTf`), `STA` '
         '(`capSTa`) and PTP coverage/wastage (`cntPTcov`) blocks are master-only, and '
         '`Zero_Dose_Digitization_Dashboard.html` is the internal `VSHOWN=true` build, regenerated '
         'from the master plus its own payloads. `state.json` has no `%s` entry either, '
         'so a run never skips it as unchanged, and the documented faithfulness test in '
         '"Adding a dataset" (`run --only <id> --force --dry-run` coming back byte-identical) is '
         'unavailable for both until the sync lands.')

MTM = ('| `mtm` | `MTM` | the six `*_combined_*.csv` HRMP exports in '
       '`C:\\Users\\HD\\Dropbox\\Joint Database\\3. HRMP\\Raw IDIMS FIles` (pulled together '
       '21-Apr-2025, never re-pulled) | CSV, one row per record | **HRMP mobile and migrant teams** '
       '- the card under the search-team block on the Permanent Transit Points tab. Six forms in one '
       'payload: `Migrant_and_Mobile_Populations_Mapping_Form-174` (mapping records), '
       '`Nomads_immunization_team_activity_-130` / `Search_Team_Activity-157` / '
       '`Special_Biker_Teams__Coverage-178` (team activity and coverage) and '
       '`Monitoring_checklist_Nomads_immunization_team_-137` / '
       '`Search_Team_Monitoring_Checklist-158` (checklists). Aggregated to district x year and '
       'district x month on the same district index, year list and month-slot arithmetic as `PTP`, so '
       'the tab\'s one Year-then-month picker drives every grid; 34 district units, panel window '
       '2016-2026, spans per form 2022-09..2025-04 (mapping 2024-08..2025-04, biker 2024-10..2025-04), '
       'so a 2026 period reads as a dash with that form\'s span in its tooltip and never a zero. Rows '
       'read then kept: mapping 114,954 -> 114,894 (33 districts, 1,050 district-UC pairs), nomad '
       'activity 16,414 -> 16,365 (9 districts), nomad checklists 4,729 -> 4,718 (11), search-team '
       'activity 15,300 -> 14,720 (5), search-team checklists and biker coverage in the same shape. '
       'Counts are one column per form, never one blended total, so a period view can say which form '
       'filed the rows it shows. Published: mapping records by household origin (`origin_country` 1 = '
       'Pakistan-origin, 2 = Afghan-origin - proved by `orgin_dist_pak` being blank in 31,694 of '
       '31,694 Afghan-origin rows and filled in 83,206 of 83,207 Pakistan-origin ones), sessions '
       'planned against conducted, children missed as not-available or as a refusal, under-two '
       'zero-dose recorded, EPI cards issued, biker refusals and not-availables recorded against still '
       'open, and AFP / AEFI tallies. Team numbers repeat across districts (nomad 23 distinct '
       'province-wide against 63 once scoped to their district, biker 29 against 82), so team counts '
       'are district-scoped unions summed and the province figure is that sum - the export carries no '
       'province-wide team id. Every published month is the month the entry was made: only three of '
       'the six forms carry a separate activity date and those disagree with the entry month in 12.8% '
       'of search-team and 8% of biker rows. One mapping spelling is not on the KP district index '
       '(KOLAIPALAS, 2 rows) and is dropped under a named reason rather than guessed onto a district. '
       'Held out and named in the caption: every name, email, user id, designation, coordinate, '
       'free-text remark and settlement or area name (public site); every `target_*` / `coverage_*` / '
       '`un_recorded_*_coverage` column - the same field family the PTP panel holds out under the open '
       'IDIMS report-definition question, and in these exports coverage exceeds target in 4,245 of '
       '103,143 search rows with one `target_ipv_1` at -3; the bare dose columns, empty in every live '
       'search-team row and, in the nomad form, sitting beside three mutually inconsistent OPV '
       'tallies (`vacc_opv` 203,129 against `opv_does1+2+3` 192,307 against `target_opv` 245,337); '
       '`no_of_families` / `no_of_child`, whose median is 3 but where 906 rows carry more than 100 '
       'children, up to 7,640 in one mapping record - a tail holding 20% of the province sum; and '
       'every integer answer code with no caption (`mmp_types`, `hrmp_type`, `riadmin`, `duration` '
       'max 100,000,000, `mob_pop_card_issued` max 3,134 in one session, `team_planned` 0/1/8 and the '
       'checklist item columns), four of which - `items_checked`, `data_Recording`, `vaccination`, '
       '`search_team` - are blank in every row of both checklists. A negative in a published count '
       'column voids that one cell and is counted rather than fatal or silently added: one Peshawar '
       'search row writes `session_conducted` -2, the visit happened, so the row and its other '
       'columns stand. The extractor aborts unless each form\'s month cells add back to its year cells '
       'and to its kept-row count, no cell exceeds its year cell, every read row is kept or dropped '
       'under a named reason, the origin split adds back to the mapping rows, the province '
       'sessions-conducted total does not exceed sessions-planned, the biker still-open tallies do not '
       'exceed their recorded columns, and the emitted cells hold nothing but numbers. **These two '
       'search-team forms are superseded in depth by `sta`** (below): the same IDsIMS forms, the '
       '21-Apr-2025 CSV re-read inside the owner\'s 28-Sep-2026 workbook pull, where they grow from '
       '14,720 to 26,225 kept activity rows. The two cards are cross-labelled and no figure is ever '
       'added across them. Route: `python _refresh/extract_mtm.py` -> `_refresh/out/mtm.json` (28,135 '
       'chars), card applied to the master by `python _refresh/patch_mtm_ui.py`. ' + ROUTE % ('MTM', 'mtm') + ' |')

STA = ('| `sta` | `STA` | `Search Team Activity Peshawar*.twbx` + `Search Team Monitoring Check '
       '*LIst*.twbx` in `C:\\Users\\HD\\Dropbox\\Joint Database\\3. HRMP` (both pulled 28-Sep-2026; '
       '`status` tracks the newer of the pair) | the data embedded in the two Tableau workbooks | '
       '**HRMP search teams, read from the owner\'s own workbooks** - the card under the mobile-team '
       'block on the Permanent Transit Points tab, and the block that answers the '
       'target-vs-coverage question the transit-point panel still holds open (#156). Two IDIMS forms, '
       'the same ones `mtm` publishes from the April CSVs, in a later and deeper pull, and the vintage '
       'proof rides in the payload (`vint`) instead of being assumed: 15,281 of the 15,282 row ids in '
       'the April activity CSV also sit in the workbook, the 1 that does not is carried into these '
       'totals under its own id (`n.sact.carried`) rather than lost, and the workbook adds 11,505 rows '
       'filed since April; checklists share 6,001 of 6,001 ids, none missing, and add 4,851 newer '
       'rows. Two vintages of two forms, not two more forms - so nothing here is ever added to the '
       'card above it and the caption says so. Rows: 26,806 activity read -> 26,225 kept (562 archived '
       'under the source\'s own `is_archive` flag, 20 repeated `unique_id`) plus the 1 carried id; '
       '10,853 checklist read -> 10,843 kept (9 archived, 1 repeated id). 8 district units carry '
       'search-team rows (Bannu, D.I. Khan, Lakki Marwat, Malakand, Peshawar, SW Mehsud Belt, SW '
       'Wazir Belt, Shangla) and activity reports sit in 5 of them; window 2016-2026 with both forms '
       'spanning 2023-09..2026-09 and no month hole in either (`gap` empty), so a dash is a district '
       'that did not file, never a source gap. Keyed on the same district index, year list and '
       'month-slot arithmetic as `PTP` / `PTPM` / `MTM`, so the tab\'s single Year-then-month picker '
       'scopes all four grids. **What the owner pointed at is here and it is not what the column names '
       'suggest:** the activity form has a dose column for every antigen in the ladder and every one of '
       'them is blank in all 26,806 workbook rows, so the measure the form actually carries is the '
       'target / coverage pair per antigen - 21 pairs (zero-dose, new-born, BCG, OPV 0-3, Penta 1-3, '
       'Pneumo 1-3, Rota 1-2, IPV 1-2, IPV booster, TD) published as children targeted, children '
       'covered and the rows that wrote a pair contradicting themselves, each pair keeping its own void '
       'count instead of those rows vanishing: 585 zero-dose, 1,360 OPV-3, 579 BCG voided rows. The '
       'ladder is district x year and never by month, because a target for a month the team did not '
       'work is exactly what the void rule exists to catch. `td` is withheld outright by a computed '
       'rule - a pair is refused when more than a fifth of the rows that recorded it contradicted '
       'themselves, and td sits at 33.3% (8,752 of the 26,223 that recorded it) where the worst column '
       'that is published manages 7.8%: the form fills td\'s coverage side and almost never its target '
       'side, so across the whole pull 18,500 covered were written against a target of 3 and, once the '
       'row rule has voided the contradictions, the pair would publish as 3 targeted against nothing '
       'covered. It renders as a labelled '
       '`Withheld` row carrying those four numbers, not as a silent absence. That is the answer for '
       'these two forms to the definition question the PTP panel holds open: the owner\'s workbook '
       'shows the family means targeted / covered / self-contradicting, so the pairs are published '
       'here while the PTP export\'s own `Coverage` columns stay held out - a divergence between two '
       'sources of one field family, named on both cards, not resolved by picking the prettier number. '
       'Every published month is the entry month: activity month and entry month differ in 4,131 rows, '
       '1 row\'s activity date cannot be read, sessions conducted exceed sessions planned in 149, 4 '
       '`ipv_booster` cells are not a number, and covered-above-target runs per antigen (largest '
       'ipv_1 at 2,035) - all of it in `n.sact.dq` and said in the caption, while the checklist form '
       'disagrees with itself nowhere (`n.smon.dq` empty). Of the checklist\'s 32 item columns, 25 are '
       'answered by at least one row and published per district; 7 no row ever answered (`search_team`, '
       '`logistics`, `vaccination`, `cold_chain`, `team_assistant`, `data_recording`, '
       '`operational_modality`) are named in `inever` and never rendered as a 0. Team and UC counts are '
       'district-scoped unions summed (activity 56 team numbers / 96 UCs across districts against 24 / '
       '95 distinct province-wide; checklist 55 / 93 against 26 / 92) because a team number repeats '
       'across districts and the export carries no province-wide team id. Spellings match the KP '
       'district index case-insensitively where unambiguous - `WAZIR-S LOWER` on this form is the '
       'panel\'s SW Wazir Belt - and a spelling that matches two districts aborts the build instead of '
       'picking one. The EPI comparison (`tri`) sets the two registers side by side over the 33 months '
       'both cover (2024-01 to 2026-09, from `const EPIM`, the facility EPI register): facility OPV-3 '
       'and BCG doses against the search team\'s covered sides plus the report count behind them, with '
       'the ratio published as **search-team OPV-3 per 100 facility doses** - two registers of the same '
       'districts, never a coverage percentage, and a figure above 100 per 100 aborts the build rather '
       'than being published. The team linkage (`lnk`) stays as counts - 233 activity team-months, 267 '
       'checklist team-months, 163 on both forms - because a district with 144 activity team-months and '
       '118 matched is a different finding from one with a single checklist month and no activity at '
       'all, and one percentage would flatten both. Held out of the payload and named in the caption '
       '(`hold`, 9 groups): reporter names, the address they sign with, entry and update ids and the '
       'vaccinator / monitor / focal-person columns; position coordinates and their accuracy; every '
       'free-text note including why a row was archived; the reporting body and post columns; the bare '
       'dose columns blank in all 26,806 rows; `un_recorded_<antigen>_coverage` (a third number that '
       'reconciles with the pair in none of the rows checked); the ladder by month; `td`; the 7 '
       'never-answered checklist fields. The extractor aborts unless the district x year and district x '
       'month cells add back to the kept-row count in every published column, no month cell exceeds its '
       'year cell, every read row is kept or dropped under a named reason, each pair\'s three counts '
       'tie to the rows that recorded it, the ladder ties back to the pair counts, the item columns tie '
       'to `iyes` + `inever`, the linkage sums tie to `n.link`, and no district spelling is ambiguous. '
       'Rendered as one card (`cSTa`) with six period-aware tables (forms, districts, antigen ladder, '
       'checklist items, team linkage, EPI comparison), six CSV downloads and a caption that carries '
       'the vintage proof, the void counts and the withheld pair; it also corrects four claims the '
       'mobile-team caption makes about these two forms. Route: `python _refresh/extract_sta.py` -> '
       '`_refresh/out/sta.json` (30,483 chars), then `python _refresh/patch_sta_ui.py` (master only, '
       '`--unpatch` reverses byte for byte). ' + ROUTE % ('STA', 'sta') + ' |')

PTP_OLD = ('**Not refresh-ledgered:** `state.json` has no `ptp` dataset entry, so `refresh.py run` '
           'does not treat it as an auto dataset - the extractor is run by hand, the payload swapped '
           'into the master\'s `const PTP = {...}` line, and the other three variants wait for '
           '`push_master.py` (that sync counts as publishing).')
PTP_NEW = ('**Refresh route:** `ptp` *is* registered in `sources.json -> auto` and `const PTP` sits in '
           'all four variants (the tab was synced on 23-Oct-2026), so `run --only ptp` is a valid swap '
           'target - but `state.json` has no `ptp` entry, so a run never skips it as unchanged and '
           're-extracts it every time, and `run`/`inject` still abort at the identical-group assert '
           'while the master carries unsynced blocks (see the `mtm` row). Today the extractor is run by '
           'hand and the payload swapped into the master\'s `const PTP = {...}` line.')


def apply(text, patched=True):
    if patched:
        assert text.count(PTP_OLD) == 1, 'the ptp refresh sentence is not there exactly once'
        out = text.replace(PTP_OLD, PTP_NEW)
        anchor = '| `afpd` | `AFPD` |'
        i = out.index(anchor)
        j = out.index('\n', i)
        assert out.count('\n| `mtm` |') == 0 and out.count('\n| `sta` |') == 0, 'rows already present'
        out = out[:j + 1] + MTM + '\n' + STA + '\n' + out[j + 1:]
        return out
    # reverse: drop the two rows, restore the sentence
    out = text
    for row in (MTM, STA):
        assert out.count(row + '\n') == 1, 'a row this script wrote is missing - not reversing blindly'
        out = out.replace(row + '\n', '')
    assert out.count(PTP_NEW) == 1, 'the corrected ptp sentence is missing'
    return out.replace(PTP_NEW, PTP_OLD)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    a = ap.parse_args()
    raw = io.open(DOC, encoding='utf-8', newline='').read()
    assert '\r' not in raw, 'SOURCES.md is kept LF - refusing to write CRLF'
    out = apply(raw, patched=not a.unpatch)
    io.open(DOC, 'w', encoding='utf-8', newline='').write(out)
    print('%s SOURCES.md %+d chars; AUTO table rows now %d'
          % ('PATCHED' if not a.unpatch else 'UNPATCHED', len(out) - len(raw),
             sum(1 for l in out.split('\n') if l.startswith('| `') and l.split('`')[1] in
                 ('chd', 'snd', 'ucc', 'fipv', 'icm', 'adv', 'pcm', 'epm', 'epim', 'rca', 'esup',
                  'sops', 'neap', 'mpqa', 'nact', 'ind', 'inda', 'ptp', 'ptpm', 'afpd', 'mtm', 'sta'))))
    return 0


if __name__ == '__main__':
    sys.exit(main())
