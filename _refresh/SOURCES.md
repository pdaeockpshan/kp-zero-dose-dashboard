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
| `adv` | `ADV` | `advance_reports_*.xls*` in `D:\AMAZON DATA` + `C:\Users\HD\Downloads` | (HTML table, first sheet) | **Every** matching file is loaded, newest export wins per campaign (so D:-drive and Downloads copies of the same file are harmless). 32 campaigns 2023-2026 incl. the current cycle, 27 619 UC rows; rendered on its own "Recorded & Covered 2023-26" page under Zero Dose. District-level (no-UC) exports and unreadable fragments are skipped with a WARN. The Sept-2026-era export leaves the reported column empty and puts the tracked children in the covered column - those campaigns are repaired (reported read from the second column, covered = unknown, shown as `-`). A campaign name without a readable month/year aborts the extract - add it to `sources.json → auto.adv.config.campaigns`. |

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
| `epi` | `EPI`, `EPIM`, `EMETA` | IDIMS facility-wise report | Export `Consolidated_Facility_Wise_Vaccination*.xls`, rebuild with `_epi_jansep_patch.py`, then `inject`. UC-level `EPI` is YTD-only; `EPIM` is district x month by design. |
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
  (LF-normalised, because git pushes with `autocrlf`). The GitHub token comes from
  `git credential fill`, is piped into curl over stdin, and is never printed.

## Adding a dataset

1. Add an entry to `sources.json` (`auto` with an `extractor`, or `manual` with a `howto`).
2. Write `_refresh/extract_<id>.py`: discover the source with `srcutil.newest(cfg['auto'][id])`,
   build the object, write `srcutil.dumps(obj)` to `--out`, print
   `SRC <id> <path>` and `OK <id> <chars> <summary>`.
3. `python _refresh/refresh.py run --only <id> --force --dry-run` - the payload should come
   back byte-identical if nothing in the source changed. That is the faithfulness test.
