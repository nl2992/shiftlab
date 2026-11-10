# 02 - Dataset discovery (WS-A)

Written 2026-11-09. Rules: `DATASET_ELIGIBILITY_PROTOCOL.md`. Ledger: `DATASET_DISCOVERY_LEDGER.csv`; machine-readable: `DATASET_SOURCE_REGISTRY.json`; D1 table: `d1_summary.csv`; build records: `dev_builds/`.

## Process

1. Inventory of the 44 existing C4 recipes (the brief said 45; the directory holds 44 source modules plus two shared download helpers). The 26 registered sealed hashes and the 7 eligible fresh-window hashes were recomputed from the arrays and all match; oakland's fresh window was ineligible (27 episodes) and has no sealed array.
2. Socrata catalogue harvest (20 query phrases, up to 400 hits each, 2,646 distinct datasets; `harvest_socrata.py`). Datasets updated after 2026-07-01 with a created-like and a closed-like date column (262) were probed by count queries for the DEV (2023-07..2025-07) and CONFIRM (2025-07..2026-07) periods and the date range (`probe_socrata.py`). Counts only; no label statistic was requested.
3. Non-Socrata sources were found by direct portal/API checks (S3 listings, EPA AirData, NOAA GHCN, Toronto CKAN, Philadelphia Carto, openFDA, UK DfT) and local files; each was verified as stated in its ledger row. Wild-Time (arXiv, HuffPost, Yearbook) and WILDS image sets were not attempted (text/image featurisation is outside the frozen model pair; no local copy except a CivilComments mirror).
4. Recipes were written before building (`scripts/paper1_scale25/data/sources/`), built through `dev_build.py` (a wrapper around the unchanged `c4_build.build`), with raw data in `data/raw/scale25/` and sealed dev losses in `data/scale25_dev/` (neither committed). No CONFIRM data was fetched or built. Failures are kept (below).

## Counters (kept separate)

| counter | value |
|---|---|
| existing_recipes | 44 |
| new_discovered | 276 |
| new_discovered_distinct_parents | 276 |
| new_downloaded_dev | 13 |
| new_d0_eligible | 15 |
| new_dev_only | 4 |
| new_pending_review | 4 |
| new_ineligible | 253 |
| new_dev_built | 13 |
| new_dev_gate_pass | 12 |
| new_dev_gate_pass_with_confirm_window | 12 |
| existing_registered_gate_pass | 26 |
| existing_with_confirm_window | 10 |
| existing_confirm_unverified | 2 |

Notes on the counters: `new_discovered` counts ledger rows that are not duplicates of an existing recipe; most are Socrata datasets that failed the size rule (D0 criterion 4). `new_d0_eligible` includes the 15 sources with a written recipe; the 4 `pending-review` rows and 4 `dev-only` rows are not built. 'Downloaded' is the number of new sources whose DEV raw data was fetched (13 builds ran; 1 more failed during the build and is listed below).

## New sources by domain (discovered, all statuses)

| domain | rows |
|---|---|
| permits-enforcement | 108 |
| other-public-records | 51 |
| municipal-311 | 34 |
| public-works | 21 |
| finance-economics | 19 |
| public-safety | 10 |
| health | 8 |
| benchmark-stream | 6 |
| emergency-services | 5 |
| transport | 3 |
| environment | 3 |
| energy | 2 |
| public-records | 2 |
| advertising | 2 |
| census | 1 |
| text-nlp | 1 |

## New dev builds by domain

| domain | built | gate-pass |
|---|---|---|
| municipal-311 | 4 | 4 |
| emergency-services | 2 | 2 |
| transport | 2 | 2 |
| environment | 2 | 2 |
| energy | 1 | 1 |
| public-safety | 1 | 1 |
| finance-economics | 1 | 0 |
| public-works | 1 | 0 |

Families with at least one gate-pass dev build: emergency-services, energy, environment, municipal-311, public-safety, transport (6 families; 311 and public-safety/emergency counted separately).

## Failures (recorded, not repaired)

- `nyc_forestry_work_orders`: ValueError('This solver needs samples of at least 2 classes in the data, but the data contains only one class: np.int64(0)') (label rule not changed)
- `usac_erate_invoices`: built, failed the incumbent-error gate (validation incumbent error .505 > .5; disagreement .506). Not repaired.
- `uk_stats19_collisions`, `toronto_311`, `philly_permits`, `philly_incidents`: D0-ineligible by metadata (reasons in the ledger).
- `la_crime` publisher dataset has no rows after 2024-12, `miamidade_311` changed schema in 2024-26, `denver_311` has no per-year layers after 2023, `pittsburgh_311`/`nyc_collisions`/`nola_311`/`sf_building_permits`/`dallas_animal_shelter`/`minneapolis_311` fall under the 150k CONFIRM rule (counts in `03`).

## Limits and caveats

- The Socrata harvest is a sample of the catalogue (top hits per query), not an exhaustive crawl. ArcGIS Hub, CKAN, and non-US portals other than Edmonton/Winnipeg/Calgary/Toronto were not systematically crawled.
- Label horizons for new sources (7 days for 311, 600 s for police/EMS, 300 s for fire, 30 days for invoices/work orders) were fixed from domain conventions before building, not tuned.
- `epa_aqi_county` and `ghcn_us_rain` use a next-day label, so META delay is 1000 events (about one day), not 100; downstream code must read the per-file delay from the sealed array. `divvy_chicago` and `capitalbikeshare_dc` have labels known at unlock; the delay of 100 is a simulated labelling lag.
- Dev test-half summaries in `d1_summary.csv` are development data. `ghcn_us_rain` shows a large test-half incumbent error (about .48 vs .28 on validation), a strong shift within the window. No policy regret is computed here (WS-B).
- `data/scale25_dev/` is not covered by `.gitignore` in this worktree; it was never staged.
