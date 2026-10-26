"""Register the search-team dataset (const STA) in _refresh/sources.json.

Text surgery, not a re-dump: sources.json is hand-kept with mixed indentation, so a uniform
json.dump would bury the real change in a 50 KB whitespace diff. This writes one entry after
the `mtm` entry inside `auto` and reprints nothing else; `--unpatch` restores the file byte
for byte (it asserts the cut is exactly what this script wrote).
"""
import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'sources.json')

HRMP = 'C:\\Users\\HD\\Dropbox\\Joint Database\\3. HRMP'

ENTRY = [
    ('label', 'HRMP search teams: the two forms as the owner pulled them (const STA)'),
    ('const', 'STA'),
    ('extractor', 'extract_sta.py'),
    ('roots', [HRMP]),
    ('patterns', ['Search Team Activity*.twbx', 'Search Team Monitoring Check*.twbx']),
    ('exclude', ['~$*']),
    ('portal', 'IDIMS > Search Team Activity Peshawar and Search Team Monitoring Check LIst, '
               'saved by the owner as Tableau workbooks (both pulled 28-Sep-2026) - no script '
               'fetches IDIMS and no credentials are read'),
    ('note',
     'The same two IDIMS search-team forms `auto.mtm` publishes from the 21-Apr-2025 CSV exports, read '
     'later and deeper out of the owner\'s own Tableau workbooks: `Search Team Activity Peshawar.twbx` '
     '(one row per activity report) and `Search Team Monitoring Check LIst.twbx` (one row per monitoring '
     'checklist, in the filename\'s own capitalisation). Vintage is proved rather than assumed and the '
     'proof travels in `vint`: of the 15,282 row ids in the April activity CSV, 15,281 also sit in the '
     'workbook and the 1 that does not is carried into these totals under its own id (`n.sact.carried`) '
     'instead of being lost, while the workbook adds 11,505 rows filed since April; checklists share '
     '6,001 of 6,001 ids, none missing, and add 4,851 newer rows. Two vintages of two forms, not two more '
     'forms, so nothing on this card is ever added to the mobile-team card above it and the caption says '
     'so. 26,806 activity rows read -> 26,225 kept (562 archived under the source\'s own `is_archive` '
     'flag, 20 repeated `unique_id`) plus the 1 carried id; 10,853 checklist rows read -> 10,843 kept (9 '
     'archived, 1 repeated id). Aggregated to district x year and district x month on the same district '
     'index, year list and month-slot arithmetic as `PTP`, `PTPM` and `MTM`, so the PTP tab\'s single '
     'Year -> month picker scopes all four grids; panel window 2016-2026, both forms spanning '
     '2023-09..2026-09 with no month hole in either (`gap` empty), so a dash anywhere is a district that '
     'did not file and never a source gap. What the owner pointed at is here and it is not what the column '
     'names suggest: the activity form carries a dose column for every antigen in the ladder and every '
     'one of them is blank in all 26,806 workbook rows. What the form actually holds is a target and a '
     'coverage figure per antigen, so the measure published is that pair - 21 pairs (zero-dose, new-born, '
     'BCG, OPV 0-3, Penta 1-3, Pneumo 1-3, Rota 1-2, IPV 1-2, IPV booster, TD) as children targeted, '
     'children covered, and the rows that wrote a pair contradicting themselves, each pair keeping its own '
     'void count instead of those rows being quietly dropped: 585 zero-dose, 1,360 OPV-3 and 579 BCG '
     'voided rows. The ladder is district x year only, never by month: a target for a month the team did '
     'not work is exactly what the void rule exists to catch. `td` is withheld outright by a computed '
     'rule - a pair is refused when more than a fifth of the rows that recorded it contradicted '
     'themselves, and td sits at 33.3% (8,752 of the 26,223 that recorded it) where the worst column '
     'that is published manages 7.8%: the form fills td\'s coverage side and almost never its target '
     'side, so across the whole pull 18,500 covered were written against a target of 3 and, once the '
     'row rule has voided the contradictions, the pair would publish as 3 targeted against nothing '
     'covered. It renders as a labelled `Withheld` row carrying those four numbers, not as a silent '
     'absence. That is also the answer the transit-point panel '
     'still holds open (#156): for these two forms the owner\'s workbook settles that the target/coverage '
     'family means targeted / covered / self-contradicting, so the pairs are published here while the PTP '
     'export\'s own `Coverage` columns stay held out - a divergence between two sources of one field '
     'family, named on both cards rather than resolved by picking the prettier number. Every published '
     'month is the month the entry was made: activity month and entry month differ in 4,131 rows, 1 '
     'row\'s activity date cannot be read at all, sessions conducted exceed sessions planned in 149, 4 '
     '`ipv_booster` cells are not numbers, and covered-above-target runs per antigen (largest ipv_1 at '
     '2,035) - all of it in `n.sact.dq` and said in the caption, while the checklist form disagrees with '
     'itself nowhere (`n.smon.dq` empty). The checklist\'s 32 item columns split into 25 answered by at '
     'least one row, published per district, and 7 no row ever answered (search_team, logistics, '
     'vaccination, cold_chain, team_assistant, data_recording, operational_modality); the last group is '
     'named in `inever` and never rendered as a 0. Team and UC counts are district-scoped unions summed '
     '(activity 56 team numbers and 96 UCs across districts against 24 and 95 distinct province-wide; '
     'checklist 55/93 against 26/92) because a team number repeats across districts and the export '
     'carries no province-wide team id. District spellings match the KP index case-insensitively where '
     'unambiguous - `WAZIR-S LOWER` on this form is the panel\'s SW Wazir Belt - and a spelling that '
     'matches two districts aborts the build instead of picking one; 8 district units carry search-team '
     'rows (Bannu, D.I. Khan, Lakki Marwat, Malakand, Peshawar, SW Mehsud Belt, SW Wazir Belt, Shangla) '
     'and activity reports sit in 5 of them. `tri` sets the two registers side by side over the 33 months '
     'both cover (2024-01 to 2026-09, from `const EPIM`, the facility EPI register): facility OPV-3 and '
     'BCG doses against the search team\'s covered sides plus the report count behind them, with the '
     'ratio published as search-team OPV-3 per 100 facility doses - two registers of the same districts, '
     'never a coverage percentage, and a search-team figure above 100 per 100 aborts the build rather than '
     'being published. `lnk` is the team-number linkage per district: 233 activity team-months, 267 '
     'checklist team-months, 163 on both forms, kept as counts because a district with 144 activity '
     'team-months and 118 matched is a different finding from one with a single checklist month and no '
     'activity at all, and one percentage would flatten both. Held out of the payload and named in the '
     'caption (`hold`, 9 groups): the reporter names, the address they sign with, the entry and update ids '
     'and the vaccinator/monitor/focal-person columns; position coordinates and their accuracy; every '
     'free-text note including why a row was archived; the reporting body and post columns; the bare dose '
     'columns blank in all 26,806 rows; `un_recorded_<antigen>_coverage` (a third number that reconciles '
     'with the pair in none of the rows checked); the ladder by month; `td`; the 7 never-answered '
     'checklist fields. No name, address, coordinate or remark reaches this file - the site is public. The '
     'extractor aborts unless the district x year and district x month cells add back to the kept-row count '
     'in every published column, no month cell exceeds its year cell, every read row is kept or dropped '
     'under a named reason, each antigen pair\'s three counts tie to the rows that recorded it, the ladder '
     'ties back to the pair counts, the item columns tie to `iyes` + `inever`, the linkage sums tie to '
     '`n.link`, and no district spelling is ambiguous. **Route - registered, not driven by `refresh.py '
     'run` yet.** `python _refresh/extract_sta.py` writes `_refresh/out/sta.json`, then `python '
     '_refresh/patch_sta_ui.py` puts the payload *and* the card into the master only (`const STA` after '
     '`const MTM`, the `cSTa` card between the mobile-team card and the district inventory, `staTab()`, '
     'the render block, six CSV buttons and the four corrections this makes to the `MTM` caption and its '
     'hint) and reverses all of it byte for byte with `--unpatch`. Being in `auto` is what makes '
     '`refresh.py status` watch both workbooks for staleness; it does not mean `run` can land the payload: '
     '`swap_payload` needs `const STA` in every variant and it is in the master alone until '
     '`push_master.py` carries the block to the other three - that sync counts as publishing and needs the '
     'owner\'s word, and until it lands `run` aborts at `check_identical` for every dataset because the '
     'master already differs from preview and `public`. `state.json` has no `sta` (or `mtm`) ledger entry, '
     'so a run never skips them as unchanged; both move onto the `run` route with the sync.'),
]


def block():
    lines = ['  "sta": {']
    for i, (k, v) in enumerate(ENTRY):
        comma = ',' if i < len(ENTRY) - 1 else ''
        if isinstance(v, list):
            lines.append('   "%s": [' % k)
            lines += ['    %s%s' % (json.dumps(x), ',' if j < len(v) - 1 else '')
                      for j, x in enumerate(v)]
            lines.append('   ]%s' % comma)
        else:
            lines.append('   "%s": %s%s' % (k, json.dumps(v), comma))
    return lines


def entry_span(lines, start):
    """Index of the line that closes the entry opened at `start` (its last field, no nesting)."""
    for i in range(start + 1, len(lines)):
        if lines[i] in ('  }', '  },'):
            return i
    raise AssertionError('no entry close found after line %d' % (start + 1))


def index_of(lines, key):
    hits = [i for i, l in enumerate(lines) if l == '  "%s": {' % key]
    assert len(hits) == 1, '%s entry found %d times' % (key, len(hits))
    return hits[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--unpatch', action='store_true')
    a = ap.parse_args()
    raw = io.open(SRC, encoding='utf-8', newline='').read()
    assert json.loads(raw), 'sources.json does not parse before the patch'
    lines = raw.split('\n')

    if a.unpatch:
        o = index_of(lines, 'sta')
        c = entry_span(lines, o)
        assert lines[c] == '  }', 'sta is not the last auto entry, the cut would be wrong'
        assert json.loads('\n'.join(lines))['auto']['sta']['const'] == 'STA'
        assert lines[o - 1] == '  },', 'the entry before sta does not end with a comma'
        out = lines[:o - 1] + ['  }'] + lines[c + 1:]
        txt = '\n'.join(out)
        cfg = json.loads(txt)
        assert 'sta' not in cfg['auto'], 'sta survived the unpatch'
        io.open(SRC, 'w', encoding='utf-8', newline='').write(txt)
        print('UNPATCHED sources.json -%d chars, auto ids back to %d'
              % (len(raw) - len(txt), len(cfg['auto'])))
        return 0

    if any(l == '  "sta": {' for l in lines):
        raise SystemExit('sta is already registered - edit the entry in place or run --unpatch first')
    o = index_of(lines, 'mtm')
    c = entry_span(lines, o)
    assert lines[c] == '  }', 'mtm is not the last auto entry, so the insertion point is wrong'
    out = lines[:c] + ['  },'] + block() + ['  }'] + lines[c + 1:]
    txt = '\n'.join(out)
    cfg = json.loads(txt)
    assert cfg['auto']['sta']['const'] == 'STA', 'sta not registered'
    assert list(cfg['auto'])[-1] == 'sta', 'sta is not the last auto entry'
    assert len(cfg['auto']) == len(json.loads(raw)['auto']) + 1, 'entry count moved by more than one'
    io.open(SRC, 'w', encoding='utf-8', newline='').write(txt)
    print('PATCHED sources.json +%d chars; auto ids %d; sta note %d chars, patterns %s'
          % (len(txt) - len(raw), len(cfg['auto']), len(cfg['auto']['sta']['note']),
             len(cfg['auto']['sta']['patterns'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
