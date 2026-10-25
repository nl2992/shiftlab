# Eventwise-scout confirmation under gradual and recurring contexts

**Status:** frozen 2026-10-25 after the independent temporal null-calibration family passed and
before positive-signal confirmation. This is a synthetic benchmark confirmation, not a novelty or
deployment claim.

The required calibration is the passed report at
[`scout_context_policy_eventwise_temporal_null_results.md`](scout_context_policy_eventwise_temporal_null_results.md)
and its manifest at
[`outputs/scout_context_policy_eventwise_temporal_null_1000/reports/manifest.json`](../outputs/scout_context_policy_eventwise_temporal_null_1000/reports/manifest.json).
The runner verifies the normalized manifest SHA-256
`1c81c4f6812d237d4a455ecdcf10fdfc8e824683e91139f04393b9243a5485e6`, passed status, exact method,
16-cell family, familywise gate, and null/cap checks before starting.

## Confirmatory question and estimand

Does the frozen eventwise-propensity-bound target scout improve evaluator-known expected
postpromotion net decision gain over pooled candidate rank and nested context-volume allocation
across the registered temporal-context alternatives? The primary estimand is the equal-cell mean of
paired differences in `expected_postpromotion_net_gain` across 32 positive-signal cells. The same
independent seed cluster is reused across all cells and methods to pair contexts, outcomes, and
candidate actions.

The two primary comparisons are eventwise minus pooled rank and eventwise minus nested
context-volume. Use 10,000 seed-cluster bootstrap draws. Report two-sided 95% percentile intervals
and one-sided 97.5% lower limits for the primary comparisons. Bonferroni allocation across the two
lower limits gives an approximate simultaneous 95% familywise assessment. The primary gate passes
only if both lower limits exceed zero. This is approximate bootstrap uncertainty, not an exact
finite-sample guarantee. Eventwise minus minimum-propensity scout is a secondary mechanism contrast
with a descriptive two-sided 95% interval. Do not make cellwise significance claims.

## Frozen design

- 600 independent seed clusters, 20920000–20920599. This block is disjoint from the temporal
  development block 20274000–20274059, temporal null-calibration block 20275000–20275999, and the
  prior Markov scout confirmation block 20910000–20910599.
- 32 positive-signal cells: four prevalence schedules × signal {0.05, 0.10} × proxy error
  {0, 0.25} × hard label cap {0.20, 0.40}. The schedules are gradual 0.10→0.90, gradual 0.90→0.10,
  recurring 0.10/0.90/0.10/0.90, and its phase-reversed counterpart.
- Four methods share each stream and uniform-query realization: eventwise-propensity scout,
  minimum-propensity scout, pooled rank, and nested context-volume. Keep direct-IPW estimation,
  fixed-mixture certification, FN cost 5, FP cost 1, switching cost 0.05, alpha 0.05, registered
  split, `n=3,200`, and `d=16`.
- Require all 76,800 method-cell-seed rows, unique cell/budget/seed/method keys, positive query
  support, finite evaluator utility, and zero realized cap violations. Save expected and realized
  net gain, promotions and harmful promotions, labels, processed horizon, contrasts, environment,
  protocol and source hashes, and artifact checksums.
- Run on CUDA with six worker processes. Do not change methods or parameters after freezing. No
  figure is planned; any later research visual must use PaperBanana.

This confirmation is gated by the passed independent event-conditional temporal null calibration.
It applies only to the registered synthetic schedules, fixed split and candidate set, uniform
query process, immediate complete labels, and specified costs. It does not extend to delayed or
selective labels, adaptive propensities, unregistered prevalence paths, other outcome dependence,
or real-world utility. If either primary lower limit is nonpositive, retain the calibrated method as
an unselected comparator and do not tune on this block. Passing supports an advantage only on this
frozen grid, not novelty or general safety.

## Reproduction

```powershell
uv run shiftlab-dive-scout-temporal-confirm `
  --seeds 600 --seed-offset 20920000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_temporal_confirmation_protocol.md `
  --calibration-manifest outputs/scout_context_policy_eventwise_temporal_null_1000/reports/manifest.json `
  --output outputs/scout_context_policy_eventwise_temporal_confirmation_600
```
