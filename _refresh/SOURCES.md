# Dashboard data sources and how to refresh them

Every number in the dashboard is embedded in the HTML as a single-line JSON literal
(`const ZD = [...];`, `const CHD = {...};` …). A "refresh" means: find the newest export
for a dataset, re-extract it to JSON, and swap that literal in **all four variants**.

```
python _refresh/refresh.py status          # what is stale, and where the newest export is
python _refresh/refresh.py run             # re-extract stale sources + swap + stamp + version note
python _refresh/refresh.py run --dry-run   # same, but write nothing
python _refresh/refresh.py publish         # commit + push + verify the Pages build
python _refresh/refresh.py run --publish   # both in one go
```

Run from anywhere; paths are absolute. Python 3.12 + `openpyxl` is the only dependency.

## The four variants

| file | role |
| --- | --- |
| `index.html` | live site (GitHub Pages source, `VSHOWN=false`) |
| `preview.html` | byte-identical copy of `index.html` |
| `public/index.html` | byte-identical copy (sanitised build) |
| `Zero_Dose_Digitization_Dashboard.html` | internal copy, `VSHOWN=true` (validator names visible) |

The first three must stay md5-identical; `refresh.py` asserts that before writing and
refuses to write anything unless every variant passed its asserts. Line endings stay CRLF.

## AUTO - `refresh.py run` handles these end to end

| id | const | source file (newest match wins) | sheet(s) | notes |
| --- | --- | --- | --- | --- |
| `chd` | `CHD` | `C:\Users\HD\Dropbox\Joint Database\1 Spotting\kp+td uc spotting*.xlsx` | `DATA` | 134 MB. KP/KPTD rows are cached in `_refresh/cache/ch_rows.pkl` and only re-read when the workbook's path/mtime/size change (~70 s when it does). 86 campaigns, 1 553 UCs, 75 777 UC rows. |
| `snd` | `SND` | `D:\AMAZON DATA\**\Final Scope*.xlsx` (also `*Scope*SNID*.xlsx`) | `District`, `UC Wise` | Campaign name/start date/districts-on-5-days live in `sources.json → auto.snd.config`. **When a new campaign is announced, edit `name` and `start` there** - the tab, hero chip, countdown popup and Evening Review day dates all follow `SND.n` / `SND.st`. |
| `icm` | `ICMD` | `C:\Users\HD\Downloads\ICM Sheet*.xlsx` (also `D:\AMAZON DATA`) | `Sheet0` | `config.asof = null` keeps the as-of date already embedded; set it to `YYYY-MM-DD` when a new monitoring round is loaded. |
| `adv` | `ADV` | `advance_reports_*.xls*` in `D:\AMAZON DATA` + `C:\Users\HD\Downloads` | (HTML table, first sheet) | **Every** matching file is loaded, newest export wins per campaign (so D:-drive and Downloads copies of the same file are harmless). Some 2026-10 re-exports are small `.xls` shells whose table sits in a sibling `<name>_files/sheet001.htm` - read from there; the newest layout carries explicit ZERO DOSE REPORTED / ZERO DOSE COVERED columns, and shell HTML pads names with doubled spaces (collapsed on read). 42 campaigns 2022-2026, 34 243 UC rows; rendered on its own "Recorded & Covered 2022-26" page under PEI SYNERGY. District-level (no-UC) exports and unreadable fragments are skipped with a WARN. Where the export leaves the reported column empty, the campaigns also tracked on the ZD reported & covered page (NID Apr 26, SNID May 2026, SNID Sept 2026) are filled from the dashboard's own `ZD` payload instead (incl. UCs missing from the export rows); other such campaigns keep the tracked children as reported with coverage unknown (shown as `-`). A campaign name without a readable month/year aborts the extract - add it to `sources.json → auto.adv.config.campaigns`. |
| `pcm` | `PCM` | `PCHS Data*.xlsx` + `POST CAMPAIGN MONITORING*.xlsx` in `D:\AMAZON DATA`, plus the ICM/LQAS/coverage columns of the `chd` spotting workbook (reuses its cache) | see below | One payload, rendered on the "Monitoring analysis" tab under Campaigns. Sources: ICM mark-checks during the round (2017-2026 trend), PCHS household checks Jan-Aug 2026, PCM Sept-2026 onward, LQAS lots + missed-children reasons (72 campaigns since Sep 2017) and administrative campaign coverage (85 campaigns) from the spotting workbook DATA sheet. 88 campaign x-slots; same-month campaigns get distinguishing labels (`CR Jul 2019 · BANNU`/`· NORTH`) and the case-variant NIDApr19 pair is merged. Payload shape: `tr` trend rows carry the ICM recall columns `rc`/`rv` (recall-checked / verified, ICM only); `cv` carries the coverage register chain per campaign - target, vaccinated, zero-dose subset, recorded missed, still missed, recorded NA, still NA (8 columns, 85 campaigns); `ad` joins the ADV advance-report zero-dose chain where campaign/month/year match (28 slots, 2023+, `cov` null when every covered cell is blank). The Sept-26 PCM file has a two-row header (merged group row + real names) - the extractor prefers row 1. Surveyor name/designation columns are **never** extracted (public site). Same-day NA coverage is not collected in any of these sources - the dashboard shows NA recovery by round end instead. Staleness tracks the newest matching file only - drop a new PCHS or PCM file into `D:\AMAZON DATA` and run `--only pcm --force`. |
| `epm` | `EMETA` | `Consolidated_Facility_Wise_Vaccination*.xls*` single-month exports under `D:\AMAZON DATA` (+ `C:\Users\HD\Downloads`) | (HTML table) | EPI month index. 33 months, Jan 2024 – Sep 2026. The pre-2026 months come from 24 single-month exports (2024 district-level - `Distcode`, no `Uncode`; 2025 UC-wise; period header `<h5>YYYY-MM - YYYY-MM</h5>` must name one month); the 2026 months (Jan-Sep, with partial-month reporting %) are not on disk yet, so the extractor keeps whatever the embedded `EMETA` already carries and only extends it. Parse results cache per file in `_refresh/cache/epi25mon.pkl` (bad old-shape Downloads copies are cached as errors and WARN-skipped - delete the pkl to reparse). |
| `epim` | `EPIM` | same single-month exports as `epm` | (HTML table) | District x month routine-coverage rows. Same merge-with-embedded design: embedded 2026 months kept verbatim, pre-2026 months parsed from the monthly exports (2024 district-level, 2025 UC-wise; the shared cache filters on `Uncode` or `Distcode`), 37 districts x 33 months, 1 221 rows total. Unknown district names abort the extract. |
| `rca` | `ERCA` | `RCA_Report*.xls` under `D:\AMAZON DATA\EPI DATA` + `C:\Users\HD\Downloads` | (HTML table, streamed) | Rapid coverage assessments rendered on the "Field monitoring" tab under EPI Synergy. Visit-level 67-column rows (per-antigen vaccinated/checked pairs) aggregated to month x district; newest export wins per month x district. 113k visits / 1.04m children checked, Feb 2025 – Oct 2026. Each row also carries `og` = monitor-organization visit/child counts for that district-month (cells[12], spelling-normalized — Govt/GOVT./GOV merge and WHO-POLIO + WHO-PEI are merged into one `WHO-POLIO/PEI` organization at build stage; aggregate-safe, no names), and the payload carries `u` = per-UC whole-period aggregation (cells[3], 1.4k UC rows with visits/children/BCG/Penta-3/MR-1 and first-last month) for the focus-UC table; UC names are as monitors typed them, so spelling variants can appear. Cached per file in `_refresh/cache/rcamon.pkl` — the cache value shape changed when `og`/`u` were added (16-Oct-2026); if payloads ever come back without them, delete the pkl and re-run with `--force`. Monitor name/ID/designation columns are **never** read into the payload (public site). `RCA_Report (36).xls` (16-Oct-2026) is a NATIONAL export (GB/Punjab/Sindh/ICT districts, 593 rows), not the KP series - excluded in `sources.json`. |
| `esup` | `ESUP` | `Supervisory_Checklist_Report*.xls*` under the same roots | (HTML table, streamed) | Supervisory checklists for the same tab: fixed-site + outreach-session visits aggregated to month x district x site type (newest file wins per triple), with 16 checklist quality indicators (share of visits answering yes). 102.6k visits (62.6k fixed + 39.9k outreach); the meaningful series is fixed from Feb 2025, outreach monthly from Jan 2026 plus a Feb 2025 batch (a handful of stray Aug-Dec 2024 visits come along). Indicator columns are located by header label, and questions an older export lacks are simply absent from its contribution (only site/date columns are required). Cached per file in `_refresh/cache/esumon.pkl`. Monitor names/CNICs/designations and vaccinator names are **never** read into the payload. |
| `neap` | `NEAP` | `NEAP*.xls`/`.csv` in `C:\Users\HD\Downloads` | (HTML table) | Pre-campaign readiness for the upcoming round, rendered on the Pre-campaign tab. The portal saves **two shapes under one `NEAP (n)` counter**: district-wise (~35 KB, one row per district) and UC-wise (~1.3 MB, Province/District/Tehsil/UC before the same 14 indicators). The district payload comes from the newest district-wise file; `u` carries the newest UC-wise file (per row: district name, tehsil index, UC name, 14 values) for the drill-down table. A file matching neither shape is skipped; unknown districts abort. UC names are as reported to the portal. |
| `nact` | `NACT` | `SNID*ACTIVITY*CALENDAR*.xlsx` in `C:\Users\HD\Downloads` | `Nov - 26 SNIDs` (Gantt grid) | SNID Nov-26 activity countdown calendar, rendered as the "Activity timeline" card on the Pre-campaign tab and summarised in the core-team briefing (planned window vs NEAP status per DPEC/AIC/training/microplan activity). Day numbers sit in row 2 (C..AC = Oct 5..31, AD..AS = Nov 1..16), activities 1-28 in rows 4..31, windows are cell fills: accent4 = main bars, FF00B0F0 = secondary, FFFF0000 = post-campaign review, accent2 = catch-up / LQAS-PCM days, accent6 = campaign week; white + orange = grid base / Sundays (asserted, so a layout change aborts). Grid notes ride along as activity notes. The B1 header supplies title/vaccine/dates; the campaign month is asserted against `auto.snd.config.start`, so a stale calendar cannot land after the scope moves to the next round. |
| `ind` | `INDIC` | `Indicators*.csv` in `C:\Users\HD\Downloads` | (portal CSV export) | Campaign data pack on Campaigns → Campaign overview / Post-campaign. 85 campaigns (2017 → SNID May 2026), 75 792 UC rows, 1 873 UCs, 37 districts (incl. legacy `WAZIR-S`); district aggregates exist for all 85 campaigns, raw UC rows only for 2025+ (`ucmin`), and each of the five cards (Admin / ICM / Market survey / LQAS / PCM) has a district/UC toggle. Percent columns are recomputed from their count pairs; Same Day coverage and ICM Seen % are UC means. The export still ends at SNID May 2026 — the Sept-2026 admin round is supplied by `inda`. |
| `inda` | `INDA` | `cov_SNID Sept*.xls` in `C:\Users\HD\Downloads\ZD_Dashboard\_portal` | (HTML table, first sheet) | Admin coverage and missed children for **SNID Sept 2026**, merged into the data pack's Admin picker only (the compiled `INDIC` export has no Sept rows; the other four tables stay at May-2026). 1 402 UC rows, 37 districts incl. BAR SWAT (28 UCs missing from `INDIC`, appended). Values come from the same UC-wise coverage workbook as the Missed children tab: Administrative Target ← household target, Total Adm Covered / Adm HH Coverage ← HH children vaccinated, Adm Rec NA / Refusal ← record NA / record refusal, Adm Recorded Missed ← record total, Adm Still NA / Refusal / Missed ← still NA / still refusal / still total, Admin Zero Dose ← ZD reported, Reported AFP ← AFP. The portal's "Total Adm Covered" is not derivable from the workbook, so for Sept it equals the total children vaccinated (same definition as the Missed children tab); MP target, same-day coverage, guest, HRMP-mobile and school stay blank. Drop a new export in the legacy `_portal` and run `--only inda --force`. |

District names in the scope workbook must exist in the dashboard's own `ZD` payload
(that is where divisions come from, so the global Division/District/Tehsil/UC filters keep
working). Unknown names abort the extract with the list; `--allow-unknown-districts`
overrides. `WAZIR-S LOWER/UPPER` casing is fixed via `config.rename`.

## MANUAL - login-gated portals, never auto-fetched

No script here reads your passwords, session cookies or browser sessions, and none of
these portals is ever requested over HTTP. You export the file (or use the in-dashboard
import); then the payload goes in with `inject`, which does the same asserts, stamp bump,
version note and publish as `run`:

```
python _refresh/refresh.py inject --const ZD --from C:\path\to\zd.json --publish
```

| id | const | portal | what to do |
| --- | --- | --- | --- |
| `zd` | `DATA`, `DORDER`, `NOTES`, `DHIST`, `RLOG`, `WMETA` | IDIMS / SMC Tracker | Drop the newest `Comparison_Report_YYYY-MM-DD.xlsx` into `D:\AMAZON DATA` **and** `C:\Users\HD\Downloads`, then harvest from the legacy pipeline (below). |
| `zdcov` | `ZD` | IDIMS zero dose reported/covered | Update `D:\AMAZON DATA\ZERO DOSE REPORTED AND COVERED.xlsx` and/or the `_portal\cov_<campaign>.xls` overlays in the legacy folder, then harvest. Not produced by the Comparison Report. |
| `val` | `VAL`, `VCH`, `VUC`, `VCAMP` | SMC Tracker form 200 combined export | Save the combined CSV as `_portal\val_<campaign>.csv` in the legacy folder (one file per campaign - each file *replaces* every master row of the campaigns it contains), then harvest. **Never mirror these CSVs into this repo's `_portal/`** - it is published on Pages and they carry child-level PII. |
| `epi` | `EPI` | IDIMS facility-wise report | Export `Consolidated_Facility_Wise_Vaccination*.xls`, rebuild with `_epi_jansep_patch.py`, then `inject`. UC-level `EPI` is YTD-only (Jan-Sep 2026 until 2026 monthly exports exist) - `EMETA`/`EPIM` moved to AUTO above and refresh on their own. |
| `cq` | `CQ` | NEOC | Export to `_portal/camp_quality.json`, or use the NEOC import block on the Intra-campaign tab (writes `localStorage['kpNEOC.icm.v1']`, never the repo). |
| `mism` | `MIS`, `MISM` | EOC dashboard coverage export | One `_portal/cov_<campaign>.xls` per campaign (the `.xls` is really an HTML table), then harvest. Not derived from the `val_*.csv` validation exports. |
| `surv` | `SURVM`, `AFP` | EOC surveillance / AFP line-list | Refresh `_portal/surv_district.json`, `afp_last.json`, `polio_cases.json`. |
| `dprof` | `DPROF` | EOC dashboard | Refresh `_portal/dprofile.json`. |
| `neoc` | (none - localStorage) | NEOC | In-dashboard import only: paste the table, import a CSV/TSV/HTML export, or run the copied snippet in your own NEOC console. |

`status` lists the newest file it can see for each manual dataset too, so a waiting export
is obvious even when the refresh itself has to be done by hand.

> **Known and accepted:** `_portal/` is part of the published Pages tree, and the four
> `val_*.csv` files in it (two current, two under `_prev/`) carry child-level PII - child
> and father names, EPI card numbers, monitor names, surveyor emails. This is the same data
> the public build strips out of `VCH`. Reviewed with the owner on 12-Oct-2026 and left in
> place deliberately; do not add more, and do not treat the existing ones as an oversight.

### Harvesting from the legacy pipeline

`C:\Users\HD\Downloads\ZD_Dashboard\_pipeline\zd_refresh.py` is the pre-October build
system. It **rebuilds the whole page from `dashboard_template.html`** (937 KB), which does
not contain the Campaign history, SNID scope, Evening review, ICM/NEOC, countdown popup or
mobile layout work, and it also predates the Jan-Sep EPI patch. Never run it against this
repo and never copy its HTML over ours.

It is still the only producer of `DATA`/`NOTES`/`VAL`/`VCH`, so the safe pattern is: let it
rebuild **in its own folder**, then harvest only the JSON payloads out of the result.

1. Snapshot its current output (`Zero_Dose_Digitization_Dashboard.html`) - it is the
   baseline for the diff in step 4.
2. Put the new exports where it looks for them: `Comparison_Report_*.xlsx` in
   `C:\Users\HD\Downloads`, validation overlays in `ZD_Dashboard\_portal\val_<campaign>.csv`.
3. Run it with the no-change check disabled:
   `python -c "g={'FORCE':True,'__name__':'__main__'}; exec(compile(open('zd_refresh.py',encoding='utf-8').read(),'zd_refresh.py','exec'), g)"`
   from `_pipeline`. It prints one `ZD_RESULT {…}` line with every headline number.
   It writes only into `ZD_Dashboard\` - the repo is untouched.
4. Diff baseline vs rebuilt with all payload literals masked, and split the changes into
   *data* (apply) and *reverts* (drop). In October 2026 the reverts were `EPI`, `EMETA`,
   the `Jan 2026 - Sep 2026` labels and a CSS block; the data was `DATA`, `DORDER`,
   `NOTES`, `VAL`, `VCH`, `VUC`, `VCAMP`, `DHIST`, `RLOG`, `WMETA` plus six prose strings
   (`report of DD-Mon-YYYY`, `N children validated`, `on N forms in N UCs`,
   `entries … to DD-Mon-YYYY`, the digitization report-date note, the PPT slide line).
5. Before applying, prove the harvest is faithful: every payload that should not have
   changed must still be byte-identical to what the repo carries, `DHIST`/`RLOG` must be
   append-only, and each prose anchor must occur the expected number of times in each
   variant. `VCH` needs one extra step - see below.

`VCH` is the only payload that differs per variant. The pipeline emits it twice, from
`cfg['val_show_names']`: the internal build keeps `nm`/`fn` and the real `cd`/`mo`, the
public build drops `nm` and `fn` and blanks `cd` and `mo`. Since it only writes the
internal file, derive the public one - drop those two keys, blank those two fields, and
re-serialise with the pipeline's own `json.dumps(o, ensure_ascii=False).replace('</','<\/')`.
Verify the rule by re-deriving today's public payload from today's internal one and
requiring a byte-exact match, and assert the result contains no names before writing.

## What `run` guarantees

* **Two-phase**: every variant is mutated in memory; nothing is written until all asserts
  pass (payload parses as JSON, `const X` appears exactly once, all line endings CRLF,
  the identical group still matches).
* **Size guard**: a payload that would shrink below 20 % or grow past 500 % of its current
  size aborts the run (catches truncated or empty exports). `--force` overrides.
* **No-op detection**: if the regenerated JSON is byte-identical to what is embedded,
  nothing is written and the timestamps are left alone (`NO_CHANGE`).
* **Stamps**: the hero `Updated …` chip and the header `Last updated …` stamp are both set
  to the current PKT time (must occur exactly twice per variant), and one line is appended
  to `version.txt` and `public/version.txt`. `--no-stamp` skips both.
* **Provenance**: `_refresh/state.json` records, per dataset, the source path/mtime/size,
  the payload SHA-1, its char count, the summary line and the stamp applied. `status`
  compares against it to decide what is stale.
* **Publish** is opt-in (`--publish` or the separate `publish` command). It stages only the
  four variants, the two version files and `_refresh/state.json`, pushes, then polls
  `/pages/builds/latest` and compares the live `content-length` with the local file
  (raw or LF-normalised - the huge HTML blobs are stored byte-for-byte and keep CRLF
  even with `autocrlf`). The GitHub token comes from
  `git credential fill`, is piped into curl over stdin, and is never printed.

## Adding a dataset

1. Add an entry to `sources.json` (`auto` with an `extractor`, or `manual` with a `howto`).
2. Write `_refresh/extract_<id>.py`: discover the source with `srcutil.newest(cfg['auto'][id])`,
   build the object, write `srcutil.dumps(obj)` to `--out`, print
   `SRC <id> <path>` and `OK <id> <chars> <summary>`.
3. `python _refresh/refresh.py run --only <id> --force --dry-run` - the payload should come
   back byte-identical if nothing in the source changed. That is the faithfulness test.
