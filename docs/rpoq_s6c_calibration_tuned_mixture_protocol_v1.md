# RPOQ S6c: calibration-tuned active/uniform mixture on CRSP, protocol (pre-registered)

**Branch:** `research/rpoq-s1-fatal-flaw-audit`. **Date:** 2026-10-29. **Extends:** [S6](rpoq_s6_crsp_allocation_headroom_protocol_v1.md), [S6b](rpoq_s6b_validation_selected_variance_protocol_v1.md); results so far in [`rpoq_s6_crsp_results_v1.md`](rpoq_s6_crsp_results_v1.md).

| Label | Value |
|---|---|
| Work type | Real-data replay (CRSP), exploratory. An addition to an existing allocation family (active-to-uniform path, as in Robust ASI), not a new algorithm |
| Claim level | None |
| Why this step | S6b matched uniform but did not beat it. A tuned path between uniform and the active rule is the standard way to hedge a misspecified variance model, and it is the one remaining implementable family suggested by the oracle gap |
| Development / confirmation split | **Development on the calibration split (2018–2019), confirmation once on the test split (2020–2025).** The test split is not used to choose anything |

## Candidate: ASI-MIX

Same stream, monitor, cohorts, budgets as S6. Propensity `q = ε · frac + (1 − ε) · q_VS`, where `q_VS` is the S6b validation-selected allocation (clipped as in S6) and `ε ∈ {0, 0.25, 0.5, 0.75, 1}`. `ε = 1` is uniform.

**Selection of ε:** per budget, replay the benefit direction on the **calibration split** for the same 10 cohorts with 5 development query seeds (seed offsets 100 to 104, disjoint from the test seeds), and take the `ε` with the highest mean log-wealth. Ties go to the larger `ε`. The chosen `ε` is frozen and the test split is run once with the S6 query seeds 0 to 19.

## Decision

Same bar as S6b: paired difference over uniform of at least **+0.5 log-wealth units** with a cohort-cluster 95% interval lower bound above 0, at **both** budgets, benefit direction. If the selected `ε` is 1 at a budget the candidate equals uniform there and fails the bar by construction; that outcome is reported as such.

## What this cannot show

Same limits as S6: imposed clock, costs and null; no error-controlled validity. No comparison with the repo's evidence-directed rule, Robust ASI proper, PPRM, Podkopaev–Ramdas or `comparecast`. The test split has been seen in S6 and S6b results, so it is not untouched; the tuning uses the calibration split only.

## Reproduction

`uv run python -m shiftlab.dive.rpoq_crsp_replay_c --panel <observations.parquet> --s6-runs outputs/rpoq_s6_crsp_headroom_v1/runs.csv`
