# 07a — Confirmation protocol C1: frozen v1 on the 22-dataset cohort (locked before any confirmation build)

Written 2026-11-10 on `research/paper1-eqsdp-scale25-2026-11-09`. The user chose "Confirm v1 on 22".
- No confirmation-window data for any dataset below has been fetched, built or inspected. Only metadata row counts were read (03).
- This file is committed before any confirmation build.
- `07_CONFIRMATION_PROTOCOL.md` remains the general template; this file is the concrete registration plan.

## 1. Frozen arms (no tuning after this commit)

| id | definition |
|---|---|
| **v1** | `P2_K2__E48_F60`: EQSDp λ.98 γ.3, cutoff H=1100, E48 setting 0, F60 setting 0 (doc 19 §1, `01_initial_state.json`) |
| **W+cut** (primary reference) | `s2wald_l0.98_g0.3_H1100` |
| EQ+cut (secondary reference) | `s2armr_H1100` |
| W+pair | `P4W__P2_K2__E48_F60` |
| panel raw | the 25 comparators of `scripts/qsg_methods_search/analyze_all.py` (ADAPTERS + CONTROLS), plus arm R `EQSDp_l0.98_g0.3` |
| panel + cutoff | each panel comparator wrapped in `scripts/paper1_scale25/baselines/paper_ports.CutoffWrapper` (H=1100). `model_selector_causal` stays unwrapped because the wrapper is unsafe for it (05) |
| ports | the paper-formula Model Picker and CAMS (`baselines/`), raw and with the cutoff |

**Why W+cut is the primary reference:** it is fixed in advance and is the strongest matched control on the development data (doc 18, doc 20, 06). It was the strongest per-dataset reference on 4 of 7 fresh windows. The per-dataset best-of-panel reference is selected after the results, so it is optimistic, and it is reported only descriptively.

## 2. Cohort and windows (from `DATASET_SOURCE_REGISTRY.json` / 03; fixed here)

Registration order, which fixes the ledger indices:

**Existing sources (10)**

| # | dataset | confirmation window |
|---|---|---|
| 1 | boston_311 | 2025-01-01..2026-01-01 |
| 2 | philly_311 | 2025-07-01..2026-07-01 |
| 3 | sacramento_311 | 2025-01-01..2026-01-01 |
| 4 | baltimore_311 | 2025-01-01..2025-05-01 |
| 5 | louisville_311 | 2025-01-01..2026-07-01 |
| 6 | chicago_311 | 2025-01-01..2026-01-01 |
| 7 | chicago_traffic_crashes | 2023-01-01..2025-01-01 |
| 8 | bts_ontime | 2025-07-01..2025-09-01 |
| 9 | dc_311 | 2026-01-01..2026-07-01 |
| 10 | sandiego_311 | 2026-01-01..2026-07-01 |

**New sources (12):** all use the confirmation window 2025-07-01..2026-07-01, subject to the publication limits recorded in 03.

| # | dataset | domain |
|---|---|---|
| 11 | edmonton_311 | municipal 311 |
| 12 | winnipeg_311 | municipal 311 |
| 13 | mc311_montgomery | municipal 311 |
| 14 | calgary_311 | municipal 311 |
| 15 | nyc_ems_response | emergency services |
| 16 | nyc_fire_response | emergency services |
| 17 | montgomery_police_dispatch | public safety |
| 18 | divvy_chicago | transport |
| 19 | capitalbikeshare_dc | transport |
| 20 | epa_aqi_county | environment |
| 21 | ghcn_us_rain | environment |
| 22 | eia930_pooled | energy |

**Build rules**
- Each build uses the dataset's own recipe, label and delay exactly as in its dev build: 100, or 1000 for epa_aqi_county and ghcn_us_rain.
- Each build retrains its model pair on the confirmation window. The split is 20/20/10, with the remaining 50% sealed as the test window. The C4 gates are applied to the validation statistics only.
- A dataset that cannot be fetched, has changed schema beyond its recipe, or fails a gate is **ineligible**. It is reported, gets no ledger index, and is not repaired or replaced.

**Registration:**
- `docs/paper1_scale25/confirm_registration_C1.json` records:
  - the window and hashes of every eligible build;
  - episodes, delay and build time;
  - the ledger index assigned in the order above, starting at 8 because indices 1–7 are the Nov-9 legacy rows.
- `ledger.register_attempt` rows are written for every eligible dataset and committed **before** any policy run.
- Seed base: 2026111001. Policy seeds: 10.

## 3. Before opening: development evaluation (descriptive, committed before registration)

- The core arms are run on the **dev** windows of the 12 new sources, all episodes, 10 seeds: v1, W+cut, EQ+cut, W+pair and arm R.
- This is only to report dev-versus-confirm agreement. **No dataset is added, dropped or reordered on the basis of it.**

## 4. Analysis (run once after opening)

Record definitions are those of `scripts/paper1_scale25/stats/certify.py`:
- J(d,p) = 100 × mean over episodes of the seed-averaged net/T;
- r_d = 100 × (J_ref,d − J_v1,d)/J_ref,d, with W+cut as the reference.

**Primary — cohort test (design A2, one test):**
- H0: mean_d r_d ≤ 0 over the K eligible datasets, using a one-sided dataset-level t-test at α = .05.
- Reported with the equal-dataset mean r, its 95% t-CI, the sign count, and ΔL/T. Accuracy constraint: ΔL/T ≤ +0.1 pp.
- Organisation-merged sensitivity: average within the pairs {nyc_ems, nyc_fire}, {divvy, capitalbikeshare} and {mc311_montgomery, montgomery_police_dispatch} first.

**Per-dataset certification (design B, union bound):**
- `primary_lower` at α_i = .05/(i(i+1)) for each attempt index i. The ledger rows are opened with `ledger.open_attempt`.
- `certify_cohort` is reported with the registered target (|S| ≥ 25, mean L ≥ 2.5). The pre-run expectation (09) is that this target is **not** reachable with K ≤ 22; it is reported as it falls.
- The counts reported are registered, opened, positive point, L > 0, and selected.

**Secondary:**
- v1 vs EQ+cut, and W+pair vs W+cut;
- the same cohort t-test;
- Holm across the two.

**Descriptive:**
- v1 vs each panel comparator, raw and with the cutoff: pooled t-CI, and per-dataset counts under the amendment-11 ≥ SOTA rule (1% non-inferiority against every comparator). This is given separately for the raw panel and the cutoff-equipped panel.
- v1 vs the per-dataset best-of-panel, labelled optimistic.
- Labels, switches, the decomposition, and results by domain.

**Reporting rules**
- No CVaR or tail criterion is used anywhere.
- The main table lists every eligible dataset, sorted by registration order.
- A dataset failing any of the above is still reported. No retuning, no substitution, and no change to the window or reference after this commit.
