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
| `zd` | `ZD`, `DATA` | IDIMS / SMC Tracker | Drop the newest `Comparison_Report_YYYY-MM-DD.xlsx` into `D:\AMAZON DATA`. Rebuild the payload with the legacy pipeline (below) and `inject` it. |
| `epi` | `EPI`, `EPIM`, `EMETA` | IDIMS facility-wise report | Export `Consolidated_Facility_Wise_Vaccination*.xls`, rebuild with `_epi_jansep_patch.py`, then `inject`. UC-level `EPI` is YTD-only; `EPIM` is district x month by design. |
| `cq` | `CQ` | NEOC | Export to `_portal/camp_quality.json`, or use the NEOC import block on the Intra-campaign tab (writes `localStorage['kpNEOC.icm.v1']`, never the repo). |
| `mism` | `MISM` | EOC dashboard | Export the missed/refusal UC list to `_portal/`, rebuild, `inject`. |
| `surv` | `SURVM`, `AFP` | EOC surveillance / AFP line-list | Refresh `_portal/surv_district.json`, `afp_last.json`, `polio_cases.json`. |
| `dprof` | `DPROF` | EOC dashboard | Refresh `_portal/dprofile.json`. |
| `neoc` | (none - localStorage) | NEOC | In-dashboard import only: paste the table, import a CSV/TSV/HTML export, or run the copied snippet in your own NEOC console. |

`status` lists the newest file it can see for each manual dataset too, so a waiting export
is obvious even when the refresh itself has to be done by hand.

### The legacy pipeline is a trap

`C:\Users\HD\Downloads\ZD_Dashboard\_pipeline\zd_refresh.py` is the pre-October build
system. It **rebuilds the whole page from `dashboard_template.html`** (937 KB), which does
not contain the Campaign history, SNID scope, Evening review, ICM/NEOC, countdown popup or
mobile layout work. Never run it against this repo, and never copy its `index.html` over
this one - use it only to produce a `ZD`/`DATA`/`EPI` payload, then `inject`.

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
