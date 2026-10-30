# Real-data protocol R0: does CRSP offer exploitable, stable context heterogeneity? (frozen before any run)

**Date:** 2026-10-30. **Data:** CRSP CIZ panel (WRDS; use confirmed by the user), pulled from the repo's `data-2026-10-22` release, kept outside Git. **Splits used:** train (fitting), validation 2015–2017 and calibration 2018–2019 (estimation). **The test split (2020–2025) is not read.** Exploratory; imposed clocks, costs and null. No claim.

## Why this precedes any allocation replay
Candidate A (restricted verdict, `SYNTHETIC_RESULTS.md`) can only help where signal-to-noise differs across observable contexts **and** the best contexts stay best. Its documented failure is a favourite losing its signal. R0 asks whether CRSP has that structure at all, using only development periods.

## Stream and contexts (declared before looking at outcomes)
- Same 10 disjoint cohorts of 300 train-universe PERMNOs and the same action pair, paired cost and train-only models as S6 (`docs/rpoq_s6_crsp_allocation_headroom_protocol_v1.md`); `Y = −Z` (benefit of the candidate over the reference, 5 bps costs), proxy `H` the train-only Ridge prediction.
- Two context definitions, both declared now: **size** = `log1p_dlycap` (feature 5) and **abs_return** = `|dlyret|` (feature 0), each cut into 8 bins by *train-split* quantiles. Both are reported; neither is chosen after seeing results.

## Quantities (per context bin, pooled over the 10 cohorts)
`μ̂ = mean(Y)`, `r̂ = mean((Y − H)²)`, `SNR = μ̂² / r̂`. Computed separately in validation and in calibration.

## Criteria
- **Heterogeneity present** for a context definition if, in **validation**, the highest bin SNR is at least 3× the median bin SNR and its `μ̂` has a bootstrap (cohort-cluster) 95% interval excluding 0.
- **Stable** if the Spearman correlation between the 8 validation bin SNRs and the 8 calibration bin SNRs is ≥ 0.5 **and** the validation top bin has a calibration `μ̂` of the same sign.
- **Mechanism has purchase on CRSP** only if both hold for at least one context definition. Otherwise R0 closes the real-data path for Candidate A, and this is reported as a negative result.
- No allocation rule is run in R0. A replay would require a new protocol, and the test split would remain exposed (it has been examined many times), so any such replay is labelled exploratory.

---

# Real-data protocol R1: exploratory allocation replay on the size context (frozen before any run)

**Date:** 2026-10-30. **Status:** exploratory. The 2020–2025 test split has been examined repeatedly (S6, S6b, S6c), so it is **not** a confirmation set. A pass is a descriptive screen only. **Gate:** R0 passed for the size context (`REAL_DATA_RESULTS.md`); the synthetic gate is only partially passed (A3: supported with restriction).

## Design (fixed before looking at R1 outcomes)
- Same 10 cohorts, action pair, paired cost, 5 bps, proxy, delay clock (label resolves the next date), hard budgets 5% and 20% of events, 20 query seeds (S6 seed scheme), benefit direction.
- **Contexts:** the 8 *size* bins of R0 (train-split quantile edges).
- **Estimates for the allocator:** per bin, `μ̂_k`, `r̂_k`, mean proxy `ĥ_k` and event share `p_k`, computed from the **validation and calibration splits pooled** (both pre-test). No burn-in is needed and no test data is used to choose anything.
- **Arms:** `uniform`; `neyman` (`q ∝ sqrt(r̂_k)`); `growth` (`allocate()` with `μ̂_k, ĥ_k, r̂_k`, bound `M = 0.202`); `random_conc` (all spare labels on one bin chosen uniformly at random per cohort and seed, independent of data). Every arm is rescaled so that `Σ p_k q_k = frac`, with `q ∈ [0.1·frac, 1]`.
- **Bets:** each arm is run with per-bin Kelly moments (`ctx`) and pooled moments (`common`); the plug-in Kelly bet and per-event bound cap are those of S6. Each arm is scored with its better bet type over all cohorts and seeds (a disclosed upward bias for every arm).

## Metrics and decision
- Mean final log-wealth per (cohort, arm), averaged over seeds; cohort-cluster bootstrap 95% intervals (2,000 resamples). Crossing rate at `α = 0.05` is secondary.
- **Primary:** `Δ = growth(best bet) − max{uniform, neyman, random_conc}(best bet)` at both budgets.
- **Supported on CRSP (exploratory):** `Δ ≥ +0.5` log-wealth units with lower bound > 0 at **both** budgets. Otherwise not supported. A negative `Δ` with an interval excluding 0 is reported as harm.

## What this cannot show
No error-controlled validity on real data; the next-date clock, 5 bps costs and conditional-mean null are imposed. Small-cap costs are not credible at 5 bps. The test split is exposed. The repo's evidence-directed rule, Robust ASI proper, PPRM, Podkopaev–Ramdas and `comparecast` are not run, so a win here would be over uniform, Neyman and a placebo only.

---

# Real-data protocol B1: repo evidence-directed benchmark on the CRSP stream (frozen before any run)

**Date:** 2026-10-30. **Purpose:** complete the benchmark landscape for one named published-style comparator, the repo's own evidence-directed query rule (`shiftlab.dive.query.EvidenceDirectedQueryPolicy`, imported unchanged). **No candidate of mine is evaluated.** Exploratory, descriptive, exposed test split, imposed clocks and costs, no validity claim.

## Design
- Same 10 cohorts, action pair, paired cost, delay clock, budgets (5%, 20%), 20 query seeds (same uniforms as S6/R1) and benefit direction as R1; **pooled Kelly bet only** (the arm's better bet type in R1 for uniform was pooled; per-bin bets add nothing without contexts).
- **Arms:** `uniform` (must reproduce S6/R1: 1.41 at 5%, 6.54 at 20%); `evidence_directed` with the repo default curve (`activation_fraction = 0`, `urgency_power = 1`, `budget_taper_power = 1`), `q_min = 0.25·frac` and `q_max = min(1, 2.5·frac)` (the repo's default `q_min = 0.05`, `q_max = 0.50` against a 0.20 label rate, kept in proportion). Propensity is recomputed each date from the previous log-evidence and the remaining budget fraction (predictable).
- **Metric:** mean final log-wealth per cohort over seeds, cohort-cluster bootstrap 95% interval for the paired difference `evidence_directed − uniform`. Crossing rate secondary. Realized spend reported.

## Reading rule (descriptive)
A difference whose interval excludes 0 is reported as such, in either direction. No pass/fail gate, because there is no candidate; the result is the benchmark's standing against uniform on this stream, for use in future comparisons. Interval caveat as before: anti-conservative.

## Not run, and why
PPRM (block structure and a different single-policy estimand), Podkopaev–Ramdas (predictive-risk monitoring, different estimand) and `comparecast` (full-feedback comparison of forecasters, no label budget) are not run here; the full-feedback arm of S6 is the nearest analogue to the last. They remain unrun benchmarks.

---

# Real-data protocol B2: spend-matched evidence-directed benchmark (frozen before any run)

**Date:** 2026-10-30. **Follows:** B1, where the repo's evidence-directed rule spent only 45–56% of uniform's labels. B2 removes that confound with **one** declared configuration and no grid: `q_min = frac` (the uniform rate) and `q_max = min(1, 2·frac)`, same default curve (`activation_fraction = 0`, `urgency_power = 1`, `budget_taper_power = 1`), same stream, seeds, pooled Kelly bet, budgets and metric as B1. With `q_min = frac` the rule can only query at or above the uniform rate, so it will tend to exhaust the cap earlier than uniform (the intrinsic trade-off of this rule); realized spend is reported for both arms. Descriptive, exploratory, exposed test split, anti-conservative intervals; no gate.
