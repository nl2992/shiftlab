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
