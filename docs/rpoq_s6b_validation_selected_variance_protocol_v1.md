# RPOQ S6b: validation-selected residual-variance allocation on CRSP, protocol (pre-registered)

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Extends:** [`rpoq_s6_crsp_allocation_headroom_protocol_v1.md`](rpoq_s6_crsp_allocation_headroom_protocol_v1.md).

| Label | Value |
|---|---|
| Work type | Real-data replay (CRSP), exploratory. A candidate **addition to an existing allocation rule** (Active Statistical Inference shape), not a new algorithm |
| Claim level | None for validity or deployment. Imposed clocks, costs and null |
| Frozen before | The full S6 results were read. This file was committed while the S6 run was still executing |
| Disclosure | A one-cohort, two-seed smoke run of the S6 harness (test split) was seen before this protocol. It showed the oracle far above uniform and the linear Neyman rule inconsistent. That motivated the candidate; the candidate's design below uses validation data only |

## Candidate: ASI-VS

Same stream, monitor, bets, budgets, cohorts and query seeds as S6. Only the allocation changes:

`q(x) ∝ sqrt(r̂(x))` with `r̂` chosen **per cohort, on the validation split only**, from a frozen candidate set, each fit on train rows only:

1. `lin`: Ridge on `(Z − H)²` (the S6 Neyman model; floored at 0).
2. `log`: Ridge on `log((Z − H)² + 1e-6)`, `r̂ = exp(pred) · exp(σ²/2)`, with `σ²` the train residual variance of the log fit.
3. `log_abs`: as `log`, with features augmented by `|x|` and `x²` (standardised).

Selection criterion (the ASI estimator-variance objective at the budget being evaluated, on validation): `V(model) = mean_val[(Z − H)² / q_i]` where `q_i` is the clipped, scaled propensity the model would use at that budget fraction. The model with the lowest `V` is used on test. Ties are impossible in practice; if equal, the earlier in the list.

## Outcomes and decision

Primary: mean final log-wealth in the **benefit** direction at each budget, paired differences of ASI-VS against (a) uniform and (b) the S6 linear Neyman rule, cohort-cluster bootstrap 95% interval (2,000 resamples), over the same 10 cohorts and 20 query seeds (common random numbers).

Practical threshold: improvement of at least **+0.5 log-wealth units** with a 95% interval lower bound above 0, against both comparators, at **both** budgets. Otherwise the candidate is not supported.

Also report: the harm direction (descriptive), crossing rates, the share of cohorts in which each variance model was selected, and the gap to the evaluator-only oracle.

## What this cannot show

No error-controlled validity on real data; the conditional-mean null and release clock are imposed. The repo's evidence-directed rule, Robust ASI, PPRM and Podkopaev–Ramdas baselines are not run here, so a win would be over uniform and linear-Neyman allocation only, which is not a win over the published benchmark set.

## Reproduction

`uv run python -m shiftlab.dive.rpoq_crsp_replay_b --panel <observations.parquet> --s6-runs outputs/rpoq_s6_crsp_headroom_v1/runs.csv`
