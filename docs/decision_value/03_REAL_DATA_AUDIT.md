# 03 Real-data audit for the decision-value programme

Date 2026-10-30. Author: Agent C. Status: audit plus development-window screen. Nothing here is confirmatory. Machine-readable inventory: `manifests/datasets.json`. Code: `scripts/decision_value/audit_real_data.py`. No raw or licensed data was copied; CRSP was not opened; per-step outputs are under `outputs/decision_value/real_data/dev/` (gitignored).

Settings: **A** = every model's loss is computable from one realised outcome (fully observed prediction replay). **B** = logged bandit; only the logged action's outcome is seen, paired losses need known propensities. Costs are never observed in any local dataset except the Binance spot fee; label delays are never observed except in Criteo Attribution (where almost nothing matures). All delays and switching/query costs below are therefore imposed sensitivity values.

## 1. Eligibility table

| Dataset | Rows | Setting | Label | Why |
|---|---:|---|---|---|
| OPSD DE load (hourly 2015-2020-09) | 50,401 | A | **FULLY_OBSERVED_REAL** | Exact UTC clock, published TSO forecast column, 2020-01..09 locked and unopened. Release clock is external (ENTSO-E Art. 6(2)), not in file. |
| Monash electricity_hourly (321 clients, 2012-2014) | 26,304 h | A | **FULLY_OBSERVED_REAL** (simulated clock) | Regular hourly, no missing, no analytical use in repo; 2014 unseen. Timezone unspecified. |
| Binance ETHUSDT 1h (2025-01..2026-09) | ~15.3k bars | A | **FULLY_OBSERVED_REAL** | Exact clock, one-bar label delay, only externally grounded fee (0.100%). Near-martingale target. 2026 locked. |
| EIA EBA (CISO, ERCO, NYIS processed; all BAs raw) | 52,606 processed | A | EXPOSED_DEVELOPMENT_ONLY | All 2019 to 2026-10-19 windows examined; prospective post-2026-10-19 data is the only clean option. |
| Elec2 | 45,312 | A | EXPOSED_DEVELOPMENT_ONLY, RETROSPECTIVE_ONLY | No trustworthy clock (528 duplicate date-period groups, 5 date decreases); C1/C2 replay used rows 22,656-25,655. |
| Gas sensor | 13,910 | A | EXPOSED_DEVELOPMENT_ONLY | Batches 6-10 exposed; recorded switching headroom 0.972% (DOC-ONLY). No clock. |
| NOAA ISD 2023 (3 stations) | 41,194 | A | EXPOSED_DEVELOPMENT_ONLY | Whole year used; irregular reports. |
| Monash M4 / weather | 383,332 | A | RETROSPECTIVE_ONLY | Fixed-origin forecasting; no wall-clock. |
| CRSP CIZ (licensed) | 32.8M | A | RETROSPECTIVE_ONLY (also exposed) | Dates are not causal labels or publication times; 2020-2025 test split exposed. Not opened here. |
| Open Bandit (full, Random + BTS) | 1.37M Random, 12.36M BTS | **B** | **LOGGED_BANDIT_REAL** (exposed at aggregate level) | True propensity scores, UTC timestamps, 7 days. Clicks ~0.35%. |
| Upworthy | 45,266 arms | B (fixed horizon) | LOGGED_BANDIT_REAL, INELIGIBLE for sequential monitoring | Aggregate counts, no feedback clock, holdout already opened. |
| Hillstrom | 64,000 | B, no time axis | INELIGIBLE | Randomised but no timestamps; eval split exposed. |
| CriteoPrivateAds | 103.9M | A + simulated delays | REAL_WITH_SIMULATED_FEEDBACK | Delay field is a publisher simulation; displays at day 00:00; days 26-30 are publisher validation. 34 GB: not feasible for a CPU-only screen here. |
| Criteo Attribution | 16.47M | A, real conversion timestamps | RETROSPECTIVE_ONLY | Only 3.31% of labels mature inside the 30.9-day stream; CC BY-NC-SA. |
| Folktables ACS | 143,285 | none | INELIGIBLE | Yearly cross-sections, no within-year order. |
| WILDS CivilComments | 448,000 | none | INELIGIBLE | Domains, not time. |
| FRED/ALFRED | 630 | A | INELIGIBLE | 25-37 events per series. |
| Criteo BLBF sample | 412 | B | NOT_ACCESSIBLE | Full 35 GB archive not acquired. |
| Criteo uplift / CUVET | 0 local | - | NOT_ACCESSIBLE | Raw not retained; no timestamps anyway. |

## 2. Selected tasks

**Setting A (ranked).**
1. **OPSD German day-ahead load.** Best combination of size (729 dev days, 274 reserved), an external incumbent (the TSO forecast) and a frozen challenger family, and a genuinely unopened window.
2. **Monash electricity_hourly aggregate.** Unexposed, 3 years of regular hourly data with a natural level shift in 2012 (client set grows). Weak point: no release clock, timezone unspecified; incumbent beats the refit challenger here, so it tests whether a monitor correctly refuses to switch.
3. **Binance ETHUSDT 1h direction.** Cleanest clock and a real fee for the switching-cost axis; serves as a **near-null control** (no learnable signal, so measured headroom should equal time-shuffled headroom).

Development-only extras: EIA (CISO, ERCO), Elec2 (the one task with strong structured, persistent headroom, but untrusted chronology). Gas is not rerun (exposed, 0.972% recorded).

**Setting B.** Open Bandit full archive, Random policy logs (uniform item choice, propensity 1/80, 1.37M rows): paired comparison of two deterministic target policies is unbiased by IPS (`Z_t = r_t (1[a_t=pi_1(x_t)] - 1[a_t=pi_0(x_t)]) / p_t`). Click rate ~0.35% makes this variance-dominated; propensities are known exactly, but there is no untouched window and click release times are unknown. Treat as a Setting B feasibility stream, not a confirmatory dataset. I did not compute headroom for it (the paired losses are not observed, only estimated; a hindsight DP over IPS noise would be uninformative).

## 3. Frozen task definitions and reserved windows

Windows are definitions to freeze before any confirmation run. Hash the script and this file when freezing.

| Task | Fit | Validation (tuning only) | Development | **Reserved (do not read outcomes)** |
|---|---|---|---|---|
| OPSD | 2015-01-01..2016-12-31 | 2017 | 2018-01-01..2019-12-31 (729 days kept) | **2020-01-01..2020-09-30 Europe/Berlin = rows with utc_timestamp >= 2019-12-31T23:00, 6,577 hourly rows, ~274 days**. Disclosed forking path: spring-2020 demand disturbance is public knowledge. |
| Monash elec | 2012-01-01..2012-12-31 | 2013-01-01..2013-03-31 | 2013-04-01..2013-12-31 (275 days) | **2014-01-01..2014-12-31: 8,760 hourly points per series (26,304 total, only counted, not parsed)** |
| Binance ETH 1h | 2025-01-01..2025-06-30 | none (C=1 fixed) | 2025-07-01..2025-12-31 (4,415 bars) | **2026-01-01..2026-09-30, 6,552 calendar bars, 9 zips never opened**; further months fetched later can extend it |
| Elec2 (dev only) | rows 0-18,123 | - | rows 25,656-36,249 | rows 36,250-45,311 (9,062) low trust; chronology unverified |
| EIA (dev only) | 2023-01-08..2023-12-31 | 2024-01-01..2024-06-30 | 2024-07-01..2025-06-30 | none locally; prospective option: hourly data after 2026-10-19 under a new dated vintage |

**Decision protocol (A).** Incumbent pi_0 = model frozen on the fit window. Challenger pi_1 = same specification refit daily on the trailing 365 days using only labels released under delay d (day D is forecast at D-1 10:00 local; training uses days <= D-d, sensitivity d in {2, 7}). Features are calendar plus the same hour at D-2 and D-7 (both released before the decision). For OPSD the published TSO day-ahead forecast is an additional external candidate. Daily step loss = mean absolute error in percent of the fit-window mean load. The paired comparison uses one realised outcome, so both action losses are identifiable (Setting A).

**Pre-registration items still to freeze (not done here):** go/no-go headroom threshold, primary switching cost, monitor/threshold hyperparameters, label-cost and query-budget grid, the exact pair list, and whether the 2020 OPSD window is opened once only.

## 4. Development-window dynamic headroom

Command (single process, 78 s total):
```
cd branch-research-monitoring-to-decision-value-2026-10-30
../shift-research-starter/.venv/Scripts/python.exe -I scripts/decision_value/audit_real_data.py \
  --data-root "C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/data"
```
Outputs: `outputs/decision_value/real_data/dev/<task>/{per_step_losses.csv,summary.json}` and `all_dev_headroom_summary.json`. Seed 20261030. Quantities: cumulative loss; best static cost `min(L0, L1+c_s)`; best dynamic cost by 2-state DP started in the incumbent with cost c_s per change; `H_T` = static - dynamic. "Shuffled p95" is the 95th percentile of `H_T` over 100 time-permutations of the paired losses (destroys persistence, keeps marginals), so `H_T - p95` is headroom attributable to temporal structure rather than noise. All numbers are hindsight upper bounds for any online policy: no label delay on switching, no query cost.

Loss units: OPSD/Monash/EIA percent-of-mean-load per day (mean per-step loss about 3.4-6.6); Binance and Elec2 0/1 per step. Because units differ, c_s = 20 is about 6 days of OPSD loss but 20 bars of Binance loss.

**OPSD (T = 729 days).** Static best is "always challenger" in every pair.

| Pair (incumbent vs challenger) | gain | c_s=0 H_T | c_s=1 H_T (shuf p95) | c_s=5 H_T (shuf p95) | c_s=20 H_T (shuf p95) | switches at c_s=5 |
|---|---:|---:|---:|---:|---:|---:|
| frozen ridge vs sliding ridge d=2 | 6.3% | 176.7 (7.1%) | 83.2 (47.9) | 23.6 (4.7) | 7.4 (4.3) | 6 |
| frozen ridge vs sliding ridge d=7 | 6.5% | 178.5 (7.1%) | 82.2 (48.2) | 23.3 (7.2) | 5.4 (5.4) | 4 |
| frozen ridge vs TSO forecast | 11.7% | 664.7 (28.2%) | 511.3 (449.7) | 324.4 (208.1) | 131.4 (57.7) | 29 |
| TSO forecast vs sliding ridge d=2 | -6.1% | 783.0 (33.2%) | 642.1 (579.1) | 465.6 (320.4) | 230.3 (106.3) | 32 |

Percentages are H_T / best static cost. Loss-difference lag-1 autocorrelation 0.35-0.46. The frozen-vs-sliding pair has headroom well above noise at c_s = 1 and 5 (23.6 vs 4.7), but at c_s = 20 it is 0.3% of cost and indistinguishable from noise. The TSO pairs have large persistent headroom (regime alternation between the two forecasters), so they are the stronger testbed for monitoring-to-decision value, with the caveat that the TSO forecast is an external model.

**Monash electricity (T = 275 days).** Incumbent (frozen) is better: sliding refit is worse by 2.0% (d=2) and 2.7% (d=7). Static best = never switch. H_T: c_s=0: 39.3 (3.3%); c_s=1: 10.8 (0.9%, shuffled p95 7.4); c_s=5: 0.66 (shuffled p95 0); c_s=20: 0. Headroom is largely noise-level once any switching cost is applied. Verdict: a clean "do-nothing is right" negative control, not a headroom task.

**Binance (T = 4,415 bars).** Frozen logit 0.479 error, sliding 0.487 (-1.75%); autocorrelation of loss difference 0.00. H_T: c_s=0 883; c_s=1 277 (shuffled median 283, p95 302); c_s=5 61 (shuffled 62); c_s=20 2 (p95 24). Measured headroom equals the time-shuffled value, i.e. it is pure noise-chasing. This is the required near-null control: any method that claims decision value here is fitting noise.

**EIA (development only, exposed).** CISO: sliding is 0.2% worse; H_T c_s=1: 74.3 (shuffled p95 61.8), c_s=5: 22.1 (21.0), c_s=20: 0. ERCO: sliding 3.3% better; H_T c_s=1: 109.5 (90.9), c_s=5: 36.1 (26.5), c_s=20: 18.3 (15.7). Mostly noise-level; not a candidate headroom task.

**Elec2 (development only, row order, exposed benchmark).** Frozen 0.350 vs sliding 0.258 error (26.3% gain); loss-difference autocorrelation 0.61. H_T: c_s=0: 919 (33.6%); c_s=1: 668 (shuffled p95 146); c_s=5: 415 (3); c_s=20: 187 (3). Large, persistent, structured headroom even at high switching cost, but with an untrusted clock and a heavily used public benchmark. Useful as a positive control for the headroom statistic, not as evidence.

### Reading
- OPSD has genuine structured headroom at moderate costs (c_s up to 5 in loss units of about 3.4 per day) and that headroom is where a monitor could add value over static choice. At c_s = 20 only the TSO pairs retain it.
- Elec2 is the only pair with large headroom at c_s = 20, and Binance is a clean noise control. Monash electricity is a negative control (never switch is right).
- Static-best is always one of the two models here, so "headroom over static" is the relevant quantity; challenger gain alone (e.g. OPSD d=2: 6.3%, Elec2 26%) would overstate what switching captures, as the Gas result (12.3% gain vs 0.972% headroom) already showed.

## 5. Limitations
- **Delays are imposed, not measured.** No Setting A dataset supplies label-release times (Binance's one-bar delay is exact by construction; OPSD relies on external regulation not stored in the file; the OPSD snapshot may contain revised values and `publisher_checksum_verified` is false).
- **Costs are imposed sensitivity values**; the only grounded cost is the Binance fee, which was not used in the headroom calculation (units are 0/1). No dataset has a query-cost source; labels are free everywhere, so any label budget is an imposed information constraint.
- Dev windows OPSD 2018-2019 and EIA are already exposed (descriptive); the numbers above are screening statistics, not results. The OPSD and Monash dev windows were also used for ridge penalty and design choices in this audit's single pass; no iteration on dev outcomes was done beyond this run.
- Headroom is hindsight, ignores label delay on the switch decision and query cost, so it upper-bounds any online monitor. The time-shuffle benchmark removes persistence, not distribution; it is a heuristic noise reference with 100 permutations.
- Challenger design is simple (ridge, logistic) and not tuned; different challengers change headroom.
- Elec2 stream order and Monash timezone are unverified; OPSD 2020 is a disclosed forking path. The 2026 Binance count is calendar-derived, not verified from files.
- Open Bandit and the Criteo sets were audited from metadata and existing reports only; no new headroom computed. Criteo licenses (CC BY-NC-SA) restrict use.
- Dynamic headroom depends on loss scale: c_s values of {0,1,5,20} are not comparable across tasks without the per-step loss scale given above.

## 6. Continue / pivot / stop
**Continue** on OPSD as the single confirmatory-capable Setting A task (reserved 2020 window, structured headroom, external incumbent), with Monash electricity and Binance as control streams and Open Bandit Random logs as a Setting B feasibility case. **Pivot** if the pre-registered OPSD go/no-go threshold is not met on development numbers. No dataset in the inventory offers measured label delays or application costs, so real-data claims must be stated as "behaviour on a real stream under imposed delay and cost", not as application savings.
