# Real-data inventory for a planned QSG/EQSDp real-data confirmation (C4)

Read-only audit, 2026-11-07, branch `research/qsg-methods-search-2026-11-07`. Method: `ls`/`du`,
`git check-ignore`, `np.load(allow_pickle=False)` key/shape listing of loss caches, `git grep` over
branch tips, and reading docs. No model loss or result was computed, no holdout was read, nothing was
downloaded. One metadata-only scan was run: the series_id strings in `data/raw/eia/EBA.zip` were
listed (no values read) to enumerate balancing authorities.

Exposure vocabulary: UNTOUCHED (no ShiftLab use found), EXPOSED-dev (used in development, tuning,
screening or descriptive diagnostics), EXPOSED-test-opened (a final/locked/test window was scored),
LOCKED-holdout-unopened (a holdout is registered and documented as unopened). "Found" means found by
grep over docs/scripts/outputs on the refs named; absence of a hit is not proof of non-use.

Bottom line: every dataset with a locally prepared loss stream is EXPOSED. The only candidates with
no ShiftLab outcome use are raw-only or not-yet-acquired sources (see table A, rows marked UNTOUCHED
or LOCKED, and section D). None of them has an authentic label-release clock; delays would be imposed.

## (a) Inventory table

Paths: `data/...` is gitignored raw/processed data present in this checkout unless "no local files".
`R` = ref. Gitignore: `data/raw/`, `data/interim/`, `data/processed/`, `data/manifests/` are ignored
(`.gitignore` lines 211-215). Committed under `data/`: `atlas_v2_losses/`, `sprint_fresh_losses/`,
`sprint_twin_losses/`, `reports/` (loss caches and aggregate reports only).

### A1. Prepared loss-stream caches (committed; l0/l1 0-1 losses, 2000 events per episode)

| dataset | where | local files | task type and size | exposure | evidence | license |
|---|---|---|---|---|---|---|
| Airlines (OpenML 1169) | loader `scripts/promising_directions/b3_real_data.py`; cache `data/atlas_v2_losses/airlines.npz` (HEAD); raw `data/raw/openml_airlines_1169/dataset_1169.pq` | yes: raw 539,383 rows; npz keys starts(50,), l0/l1 (50,2000) | binary delay, 50 episodes | EXPOSED-test-opened | `data/atlas_v2_losses/README.md`: "All nine were already exposed to the B3/B3+ programmes"; `docs/promising_directions/B3_PLUS_RESULTS.md`; `15b_FETCHED_DATA_ADMISSIBILITY.md` (locked 40% = rows [323629, n) later used by B3) | OpenML "Public" |
| UCI Bank Marketing (id 222) | same loader; `data/atlas_v2_losses/bank.npz`; raw `data/raw/uci_bank_marketing/` | yes: raw 41,188 rows; npz (8,2000) | binary, 8 episodes | EXPOSED-test-opened | same as above; B3 table in `B3_PLUS_RESULTS.md` | CC BY 4.0 |
| Criteo (click, uplift-style stream) | `data/atlas_v2_losses/criteo.npz`; raw `data/raw/criteo_attribution/criteo_attribution_dataset.tsv.gz` (623 MB) | yes; npz (50,2000) | binary click, 50 episodes | EXPOSED-test-opened | README; `15_REAL_DATA_ADMISSIBILITY.md` section 2.2 (aggregate maturity scan over full file) | CC BY-NC-SA 4.0 (noncommercial, share-alike) |
| ELEC2 (electricity-normalized) | `data/atlas_v2_losses/elec2.npz`; raw `data/raw/elec2/electricity-normalized.arff` | yes; 45,312 rows; npz (4,2000) | binary price direction, 4 episodes | EXPOSED-test-opened (nearly whole stream) | `15_REAL_DATA_ADMISSIBILITY.md` 2.2: "EXPOSED (nearly the whole stream)"; chronology untrusted per `elec2_candidate_audit.md` ("Do not reopen", R0) | OpenML "Public"; no manifest/receipt |
| OpenML LDPA | `data/atlas_v2_losses/openml_ldpa.npz` (keys l0,l1 (32,2000), delay, inc_err) | losses only; no raw dir | activity stream, 32 episodes | EXPOSED-test-opened | README (from B3+ new-case work); `B3_PLUS_SIXTH_CASE_SEARCH.md` (ldpa = SUCCESS, rollbacks observed) | OpenML (not pinned here) |
| Rialto | `data/atlas_v2_losses/rialto.npz`; raw `data/raw/rialto/` | yes; 82,250 rows; npz (16,2000) | 1-vs-9 image task, 16 episodes | EXPOSED-test-opened | README; B3 table | no declared licence (Losing mirror); research only |
| Spam (Katakis) | `data/atlas_v2_losses/spam.npz`; raw `data/raw/spam_katakis/spam.zip` | yes; 9,324 rows; npz (1,2000) | binary, 1 episode | EXPOSED-test-opened | README; B3 table | no declared licence |
| UCI Occupancy | `data/atlas_v2_losses/uci_occupancy.npz` (l0,l1 (4,2000), delay, inc_err) | losses only | binary, 4 episodes | EXPOSED-test-opened | README; `B3_PLUS_CASE_VALIDATION.md` (single-episode concentration) | UCI CC BY 4.0 |
| Weather (Elwell-Polikar, Offutt AFB) | `data/atlas_v2_losses/weather.npz`; raw `data/raw/weather_elwell_polikar/` | yes; 18,159 rows; npz (3,2000) | daily rain, 3 episodes | EXPOSED-test-opened | README; B3 table | no declared licence |
| Metro Interstate Traffic (UCI 492) | `data/sprint_fresh_losses/metro.npz`; builder `scripts/sota_sprint/fresh_real.py` | npz only (16,2000), int8; raw zip not local (`data/raw/sprint_fresh/` absent) | median-threshold traffic label, 48,204 rows, delay 24 | EXPOSED-test-opened | `docs/sota_sprint/fresh_real_protocol.md`; `data/sprint_fresh_losses/README.md`; scoped `REAL_DATA_AUDIT.md`: "five UCI streams and derived windows were used in Sprint 2" (R `origin/codex/scoped-method-research-results-2026-11-06`) | CC BY 4.0 |
| Beijing PM2.5 (UCI 381) | `data/sprint_fresh_losses/beijing_pm25.npz` (14,2000); also earlier `outputs/exhaustive_evaluation/real_development/beijing_*.npz` on main | npz only | 41,757 rows, delay 24 | EXPOSED-test-opened (twice: exhaustive-eval dev outputs on main plus Sprint 2) | as above | CC BY 4.0 |
| Bike Sharing hourly (UCI 275) | `data/sprint_fresh_losses/bike_hour.npz` (6,2000); `outputs/exhaustive_evaluation/real_development/bike_*.npz` on main; `docs/sprint2/family_p/p6_twin_bike_1000.json` | npz only | 17,379 rows, delay 24 | EXPOSED-test-opened | as above | CC BY 4.0 |
| Appliances Energy (UCI 374) | `data/sprint_fresh_losses/appliances.npz` (6,2000) | npz only | 19,735 rows, delay 144 | EXPOSED-test-opened | as above | CC BY 4.0 |
| Household Power (UCI 235) | `data/sprint_fresh_losses/household_power.npz` (20,2000) | npz only | 204,950 10-min rows, delay 144 | EXPOSED-test-opened | as above | CC BY 4.0 |
| Twin (exchangeable-null) streams of the 5 UCI sets | `data/sprint_twin_losses/twin_*.npz` (120 to 400 rows x 2000, plus split/ep) | yes | known-null construction, not independent data | EXPOSED (derived from the five above) | `data/sprint_twin_losses/README.md`; `docs/sota_sprint/p2_known_null_protocol.md` | CC BY 4.0 |

Two caveats on the Atlas nine: the loss caches do not carry raw features, so a new method can only be
replayed on the stored loss pair; and `15b_FETCHED_DATA_ADMISSIBILITY.md` once recorded "Exposure =
none" for airlines/bank/weather/spam/rialto/outdoor, which was true at that date (2026-11-01) and is
superseded by the B3 run that used their locked windows.

### A2. Raw or processed sources present locally without a prepared challenger stream

| dataset | where | local files | task and size | exposure | evidence | license / restrictions |
|---|---|---|---|---|---|---|
| EIA-930 balancing authorities CISO, ERCO | loader `src/shiftlab/data/real/eia.py`; run `scripts/run_eia_2026_out_of_time_confirmation.py`; raw `data/raw/eia/EBA.zip` (EBA.txt 4.39 GB, retrieved 2026-10-20, sha256 3a6143c4...936f); processed `data/processed/eia/` (4 versions) | yes | next-hour demand D[t+1], hourly 2019-01 to 2026-10-19 | CISO/ERCO: EXPOSED-test-opened | `papers/shiftguard_unified/eia_2026_out_of_time_confirmation_results.md` (2026 test scored 2026-10-26: 6,943 CISO, 6,797 ERCO rows); `docs/eia_real_data_validity_results.md` (WP4, all four paths "previously examined development windows"); `data/reports/eia_2026_holdout_readiness.json` lists 7 earlier result manifests on version e47bdef8b208f8e7d788 | US government data, public domain with attribution |
| EIA-930, the other 68 balancing authorities | same archive | yes (inside EBA.zip) | same series; my metadata scan found 70 BAs with both demand (D) and day-ahead forecast (DF) hourly series. Others: AEC AECI AVA AZPS BANC BHBA BPAT CAL CAR CENT CHPD CPLE CPLW DOPD DUK EPE FLA FMPP FPC FPL GCPD GVL HST IID IPCO ISNE JEA LDWP LGEE MIDA MIDW MISO NE NEVP NSB NW NWMT NY NYIS PACE PACW PGE PJM PNM PSCO PSEI SC SCEG SCL SE SEC SOCO SPA SRP SW SWPP TAL TEC TEN TEPC TEX TIDC TPWR TVA US48 WACM WALC WAUW | UNTOUCHED by outcome use (no doc, script or output names any of them; only test fixtures in `tests/data/test_eia_bulk.py` mention BA ids). Caveat: same archive snapshot and same pipeline as the exposed CISO/ERCO paths, and the EIA revision/publication times are unknown (stated in the results doc). Coverage per BA (start date, gaps) has NOT been checked. | public domain |
| OPSD hourly DE load (+ TSO day-ahead forecast) | loader `src/shiftlab/real_tasks/opsd_reserve.py`, `opsd_split_clock.py`, `src/shiftlab/data/real/opsd.py`; raw `data/raw/opsd/2020-10-06/hourly.csv` (130 MB, 50,401 rows, UTC 2014-12-31 to 2020-09-30) | yes | load-reserve replay | 2015-2017 train/val: unexposed to results; 2018-2019: EXPOSED-dev; 2020-01-01 to 2020-09-30: LOCKED-holdout-unopened | `docs/lane_b_burst_allocation/R1_task_specs.md` lines 120-123 (holdout "single confirmation look; opened once after the algorithm and all grids are frozen"); `R3_freeze_and_handoff_DRAFT.md`: "no holdout has been opened"; scoped `REAL_DATA_AUDIT.md`: holdout locked, no one-opening runner exists. The holdout choice was not blind (R1 forking-path section) | `datapackage.json` has no licenses field; ENTSO-E terms not pinned; treat as research use, no redistribution (R0) |
| Binance ETHUSDT 1h klines | loader `src/shiftlab/real_tasks/binance_momentum.py`, `binance_split_clock.py`, `src/shiftlab/data/real/binance.py`; raw `data/raw/binance/` now holds ETHUSDT-1h 2025-01 to 2026-09 plus BTCUSDT-2023-01 | yes (this checkout; the scoped report said absent in its worktree) | hourly momentum signal | dev 2025: EXPOSED-dev; 2026-01 to 2026-09 (6,552 bars): LOCKED-holdout-unopened | `R1_task_specs.md` line 281; `R3_freeze_and_handoff_DRAFT.md` "Neither task loader currently has an authorized locked mode ... no holdout has been opened" | publisher repo MIT; exchange terms retained; fee costs would be an external proxy |
| Gas Sensor Array Drift (UCI 224) | `data/raw/gas_sensor/uci-224.zip`; outputs `outputs/shiftguard_unified/real_data_development/gas_sensor_candidates_v1-v4` | yes | 13,910 rows, 10 ordered batches, no within-batch time | EXPOSED-test-opened (batches 6-10 are the holdout) | `15_REAL_DATA_ADMISSIBILITY.md` 2.2; R0 | CC BY 4.0 per UCI page, original description restricts commercial use |
| NOAA ISD (3 US stations, 2023) | `data/raw/noaa/`, processed `data/processed/noaa/` | yes | irregular reports, ~41k usable | EXPOSED-dev (feature diagnostics on whole year; constructed precip label only dev-screened) | `15_REAL_DATA_ADMISSIBILITY.md`; R0 | US government, attribution |
| FRED vintages | `data/raw/fred/` | yes | 25-37 releases per series | too small (R0 INELIGIBLE), descriptive use only | R0 | series-specific, API key |
| Monash TSF (M4 hourly etc., electricity_hourly, weather) | `data/raw/monash/` | yes | no wall-clock time | EXPOSED-dev (descriptive baselines) | R0 | CC BY 4.0; M4 hourly "no blanket license" |
| Folktables ACS 2017-2019 (CA FL NJ NY TX) | `data/raw/folktables/`, processed | yes | cross-sectional, year only | UNTOUCHED by switching/promotion; offline domain-shift diagnostics only | `15_REAL_DATA_ADMISSIBILITY.md` 2.2; R0 verdict INELIGIBLE for clocked stream | Census public data; code MIT |
| CRSP CIZ daily 2000-2025 | `data/raw/licensed/crsp/` (WRDS, year=2000..2025), `data/processed/crsp_ciz_next_day/` (2 versions) | yes, licensed | next-day return, retrospective panel | EXPOSED-test-opened (2020-2025 test used by multiple studies); a 100-sample pilot is committed at `outputs/shiftguard_unified/real_data_development/crsp_decision_policy_pilot_100_v1/` | `docs/switching_real_data_eligibility_v1.md` ("its 2020-2025 test period is already exposed by multiple studies"); `docs/crsp_study_execution.md`; `docs/sota_synthetic_search/16_REAL_DATA_RESULTS_CRSP.md` | WRDS subscription terms; keep out of Git/LFS, private-repo only, no redistribution, do not load into LLMs or attach observations to support requests (`docs/cross_device_data_access.md` lines 7-15, 129, 231). Market dates are not verified change labels or point-in-time publication times (AGENTS.md) |
| Open Bandit (full + small) | `data/raw/open_bandit_dataset_full.zip` (394 MB), `data/raw/open_bandit_small/`, `data/interim/open_bandit_full_all_v*/` | yes | logged-bandit clicks | EXPOSED-dev (7-day sequence, MOPE and DR-OPE runs) | `outputs/.../open_bandit_*`; `docs/switching_real_data_eligibility_v1.md` | CC BY 4.0 (publisher); not re-verified here |
| CriteoPrivateAds | `data/raw/criteo_privatead/` (32 GB, 288 files) | yes | delayed click/sale | EXPOSED-dev (cost baselines v1/v2) | `data/reports/dataset_paper_suitability.md`: "days 26-30 ... no untouched final holdout established" | CC BY-SA 4.0 (dataset card) |
| Criteo attribution (30-day) | `data/raw/criteo_attribution/` | yes | conversion with real delays | EXPOSED-dev (aggregate maturity scan over full file; only 3.31% of labels mature in-stream) | `15_REAL_DATA_ADMISSIBILITY.md`; `switching_real_data_eligibility_v1.md` | CC BY-NC-SA 4.0 |
| Hillstrom email | `data/raw/hillstrom/` | yes | randomized email | EXPOSED (evaluation split exposed) | `dataset_paper_suitability.md` | no explicit modern license; local only |
| Upworthy Research Archive | `data/raw/upworthy/` | yes | package-selection CTR, fixed horizon | EXPOSED-test-opened (project-relative holdout scored, `upworthy_policy_v1`); suitability sheet still says "confirmatory partition unopened" (stale/different partition) | `data/reports/dataset_paper_suitability.md` | Upworthy archive terms; not a model-replacement stream |
| WILDS CivilComments | `data/raw/wilds/civilcomments-hf` | yes | offline toxicity, no event time | EXPOSED (test partition, candidate-selection and PACE-gate studies) | `15_REAL_DATA_ADMISSIBILITY.md`; R0 INELIGIBLE | WILDS dataset-specific |
| Outdoor objects | `data/raw/outdoor_objects/` | yes | 4,000 rows, 40 classes | EXPOSED-dev, screened out (disagreement below 5%) | `15b_FETCHED_DATA_ADMISSIBILITY.md` | no declared licence |
| Project Gate | `data/raw/project_gate/` | yes | project risk | not assessed in docs I read; audit `data/reports/project_gate_source_audit.json` exists on other refs | unchecked | unchecked |

### A3. Prepared or run on other branches, not present as data in this checkout

| dataset | where | local files | task | exposure | evidence | license |
|---|---|---|---|---|---|---|
| Wild-Time HuffPost | R `origin/codex/scoped-method-research-results-2026-11-06`: `research/scoped_method/pilots/chronological_news_transfer_20261106/run/wildtime_huffpost/` (RESULTS.md, TEST_OPENED.json, source_eligibility.json, pretest_manifest.json) | no local data (`data/raw/wilds` has only civilcomments); raw was kept local on the other machine, not in Git | 11-category headline classification, 2012-2018; test 2018 = 3,877 rows, simulated +24 h release | EXPOSED-test-opened (opened once, 2026-11-06, for PFA-SR transfer) | `docs/scoped_method_research_2026-11-06/REAL_DATA_AUDIT.md`; `docs/scoped_method_research/11_REAL_DATA_CONFIRMATION.md` append-only update | CC0 (Wild-Time README); Kaggle source |
| Wild-Time arXiv | same ref: `research/scoped_method/pilots/wildtime_arxiv_f8_transfer_20261107/PROTOCOL.md` | none | 172-category title classification; M0 train 2007-2012, M1 2013-2016, val 2017, test 2018-2022 | LOCKED-holdout-unopened. Protocol "frozen before acquiring the official arXiv tensor archive or inspecting validation or test outcomes"; `FINAL_ASSESSMENT.md`: "Do not open the locked Wild-Time arXiv or other holdouts under this failed development gate." No result file found on any ref. Whether the archive was ever downloaded is not stated | `docs/scoped_method_research_2026-11-06/FINAL_ASSESSMENT.md` line 116 | CC0 (Wild-Time README) |
| UCI News Aggregator, MN-DS | same ref | none | news classification | LOCKED (failed validation eligibility gate, never opened) | `REAL_DATA_AUDIT.md`: "UCI News Aggregator and MN-DS failed the validation eligibility gate and remained locked" | not stated |
| Elexon BMRS (ATL actual / DATL day-ahead load, GB) | R same ref: `research/scoped_method/ELEXON_SOURCE_FEASIBILITY_20261107.md`, `audit_elexon_metadata.py` | none; only hashed API probe responses | total-load forecast vs actual; publishTime, startTime, revision fields; coverage seems to start about late 2023 | UNTOUCHED (metadata audit only, "no method outcomes were computed") | the feasibility doc | public API, no auth needed in probe; terms not recorded |
| Covertype, KDDCup99 subsets, Run_or_walk | `docs/promising_directions/results/b3_plus/screening/openml_covertype/` and related on main | not local | OpenML concept_drift tag | screened `USELESS_INELIGIBLE` (no defensible order); dev-window prechecks only | `B3_PLUS_SIXTH_CASE_SEARCH.md` | OpenML |
| INSECTS (abrupt, reoccurring) | `docs/promising_directions/results/b3_plus/screening/insects_*` | not local ("not on OpenML ... skipped" in 15b; later screened) | drift stream | EXPOSED-dev (reoccurring variant screened: `USELESS_NO_HEADROOM`; locked window never read) | `B3_PLUS_SIXTH_CASE_SEARCH.md` | Souza et al. 2020; not re-verified |
| Poker-hand | none | not local | | not temporal, not used | `B3_PLUS_SIXTH_CASE_SEARCH.md` | |
| OpenML imdb_drama (273), vehicle_sensit (357) | screening registry on main | not local | | `NOT_RUN`; declared chronology basis "none" | `B3_PLUS_SIXTH_CASE_SEARCH.md` | |
| NYC TLC taxi, Citi Bike | frozen task manifest in `docs/h2c_next/REAL_DATA_READINESS.md` | not local | trip duration | UNTOUCHED, never acquired (proxy 403 on 2026-10-30) | `docs/hg_v2/REAL_DATA_ACCESS_STATUS.md` | TLC open data |
| CUVET policy data | `data/reports/cuvet_policy_source_audit.json` | not local (remote train streamed) | | test unread, but train-only diagnostic done | `dataset_paper_suitability.md` | CC BY-NC-SA 4.0 |

## (b) Registry conclusions from prior work

`docs/scoped_method_research/10_REAL_DATA_REGISTRY.md` (R `origin/codex/scoped-method-research-results-2026-11-06`):
opens with "No source in this table supplied independent confirmation evidence during this execution."
- Existing UCI-derived streams: previously exposed, constructed model-pair streams, imposed (not
  observed) delays, overlapping source families. Development/retrospective only.
- Wild-Time HuffPost/arXiv: candidates; task timestamps do not establish point-in-time training,
  prediction chronology or authentic label-release times. HuffPost later opened once and was adverse
  to PFA-SR; arXiv unopened.
- OPSD load-reserve and Binance momentum: raw absent in that worktree, holdouts locked, need a
  one-opening runner and a method freeze; revisions and fee proxies are threats.
- UCI Online Retail II: candidate only, needs a prospective target and label-release process.
- The 14 exposed dataset-source clusters "are not 14 untouched independent domains" (cluster summary
  `corrected_real_14_source_clusters.json`; source-level intervals in `CORRECTED_REPLAY_AUDIT.md`).
- `11_REAL_DATA_CONFIRMATION.md`: C4 status FAIL; next action only if a distinct repair first passes
  a bounded synthetic/prior-art gate, then freeze registry and chronology, verify checksums/license,
  build and test a one-opening runner, "run on at least two independent eligible source domains".

`WILDTIME_FEASIBILITY.md` (2026-11-06): HuffPost and arXiv are "feasible as chronological
prediction-drift datasets" but not admissible as untouched confirmation of a delayed-label claim
without a label-release clock; two source clusters are too few for source-level uncertainty; Wild-Time
standard splits are random within year and must be rebuilt from raw records; pretrained-model
contamination is a risk (train from scratch). `REAL_DATA_AUDIT.md` adds Elexon and Online Retail II /
Beijing Multi-Site as possible sources whose target and schedule must be defined prospectively, and
notes UCI News Aggregator and MN-DS failed the validation gate.
(There is no file named `REAL_DATA_REGISTRY.md` outside `docs/scoped_method_research/`.)

Other eligibility docs on this branch:
- `docs/switching_real_data_eligibility_v1.md` (2026-10-28): "No currently audited dataset is eligible
  for an untouched real-data confirmation of the full algorithmic claim". CRSP is the closest
  development candidate; Criteo attribution, CriteoPrivateAds, Open Bandit and CivilComments ruled
  out or exposed.
- `docs/lane_b_burst_allocation/R0_real_data_eligibility.md`: OPSD ELIGIBLE-CANDIDATE (conditional on
  timing citation and licence pin), Binance DEVELOPMENT-ONLY locally (now more months present),
  FRED/elec2/Folktables INELIGIBLE, Gas/NOAA/Monash DEVELOPMENT-ONLY. Cross-cutting: label queries
  are free in every dataset, no verified change points, null `prediction_time`/`label_available_time`.
- `docs/promising_directions/15_REAL_DATA_ADMISSIBILITY.md`: "do not freeze a confirmatory real-data
  claim yet"; `15b`: airlines best switching structure, others one-switch controls.
- `docs/qsg_methods_search/publication_decision.md`: C4 NOT STARTED; "The 9 cached Atlas streams are
  development-exposed."

## (c) Independence notes (flagged, not decided)

1. Atlas nine: nine different public sources and domains, but all exposed; no independent use.
2. Sprint five UCI sets: five different UCI datasets, all CC BY 4.0 from one repository, built with one
   shared pipeline (same LR vs HGB pair, same median label, same episode plan). Related domains:
   energy/weather/traffic/bike hourly series (metro, Beijing, bike, appliances, household power).
   The scoped audit treats overlapping source families as non-independent.
3. EIA-930 balancing authorities: 70 BAs share one archive, one agency, one reporting methodology and
   correlated weather and calendar drivers. The scoped audit already says "CISO and ERCO are separate
   historical cases, not independent deployment replications". Whether distinct BAs count as
   independent datasets for a reviewer is an open question; CISO and ERCO are in any case exposed.
   Interconnected neighbours (e.g. PJM/MISO/TVA) are correlated through shared load and weather.
4. Wild-Time datasets: HuffPost and arXiv are separately governed sources (news vs preprints), but
   the same benchmark release, the same CC0 loader, and the scoped audit counts them as two source
   clusters, "too few for reliable source-cluster uncertainty". HuffPost is exposed; arXiv is locked.
5. OPSD (DE load, ENTSO-E) and EIA (US load) are both load-forecast tasks from regulated transparency
   platforms; Elexon (GB load) is a third of the same task type. Distinct operators and countries,
   same task family; the scoped audit lists OPSD, Elexon and Wild-Time arXiv together as follow-up
   candidates.
6. Binance ETH hourly is a single asset series; the BTC 1d month is too short. Months within the
   locked 2026 window are not independent of each other.
7. Within a dataset, episodes (2000-event windows) are not independent; the scoped audit requires
   source-level clustering ("Inference is clustered at source, not episode").
8. Criteo (atlas) and Criteo attribution/PrivateAds are the same publisher but different releases;
   Criteo atlas stream and attribution file may derive from the same campaign data (unverified).
9. Twin streams are derived from the five UCI sets and carry no independent information.

## (d) Candidates mentioned in docs but never prepared as a stream

- Wild-Time arXiv (protocol frozen, data not shown as acquired, holdout locked).
- UCI News Aggregator and MN-DS (failed validation gate, locked).
- Elexon BMRS ATL/DATL (feasibility only; GB; coverage onset about late 2023 unconfirmed).
- UCI Online Retail II (named in registry; needs prospective target).
- Beijing Multi-Site Air Quality (UCI 501; distinct from the PM2.5 set already exposed) (named in `REAL_DATA_AUDIT.md`).
- NYC TLC yellow taxi and Citi Bike (blocked by proxy 403; frozen task manifest exists).
- ENTSO-E Transparency direct (cited as OPSD upstream; `data/raw/lane_b_external_refs_2026-10-28/entsoe_load_publication_rule.*`).
- Other EIA balancing authorities (see A2; data local, no stream prepared).
- OpenML imdb_drama, vehicle_sensit, powersupply, sensor-stream, usenet, BETH, MaliciousURL (not locatable or intractable).
- ALFRED/FRED vintages with larger sample (R0: wrong size).
- Fee schedule snapshot for Binance (needed for switching costs; not in repo).
- Not mentioned anywhere in my reading, so "never considered" rather than "considered": UCI electricity
  (ElectricityLoadDiagrams), HuffPost beyond Wild-Time, Kaggle competition streams; `data/raw/monash`
  includes electricity_hourly but only as a development panel.
- HuffPost (non-Wild-Time) and NOAA weather beyond 2023: no mention found.

## Verification notes and limits

- Grep coverage: all 67 refs listed, but full-text greps were run on HEAD, main, the codex scoped
  branches, gave-r, drift2act, sprint branches and atlas branch only for selected keywords. A source
  could have been touched on a branch I did not grep (e.g. `origin/claude/sweet-lovelace-pznpjq`).
- I did not open `data/processed` or any holdout window and did not inspect loss values.
- `data/raw/sprint_fresh/` raw zips are not present locally; only the loss caches are.
- Binance local months extend to 2026-09; the R1 spec locked 2026-01..2026-09 as the holdout, so
  simply having the files is not a reason to open them.
