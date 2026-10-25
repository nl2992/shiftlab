# Eventwise-scout confirmation under persistent contexts

**Status:** frozen 2026-10-25 after the Markov eventwise null-calibration gate passed and before
positive-signal confirmation. This is a synthetic benchmark confirmation, not a novelty or deployment
claim.

The calibration prerequisite is the committed
[`scout_context_policy_eventwise_markov_null_results.md`](scout_context_policy_eventwise_markov_null_results.md)
and `outputs/scout_context_policy_eventwise_markov_eventwise_null_1000/reports/manifest.json`.
The confirmation runner verifies the recorded calibration status, method, family, and cap/null
checks before starting.

## Confirmatory question and estimand

Does the eventwise-propensity-bound target scout improve evaluator-known postpromotion net decision
gain over pooled rank and nested context-volume selection across the registered persistent-context
alternatives? The primary estimand is the equal-cell mean of paired differences in
`expected_postpromotion_net_gain` across 72 positive-signal cells, paired by the same independent
seed cluster across all cells. A seed is a cluster because outcomes, contexts, and actions are
matched across methods and cells.

The two primary comparisons are eventwise minus pooled rank and eventwise minus nested
context-volume. Use 10,000 percentile seed-cluster bootstrap draws. For each primary contrast,
report its two-sided 95% percentile interval and one-sided 97.5% bootstrap lower limit. The two
lower limits use Bonferroni allocation for an approximate simultaneous 95% familywise assessment.
The grid-level primary gate passes only if both lower limits exceed zero. Compare with the
minimum-propensity scout as a secondary mechanism contrast, with a two-sided 95% descriptive
interval; it is not part of the primary gate. No cellwise significance claims are planned.

## Frozen design

- 600 independent seed clusters, 20910000–20910599. This block is disjoint from prior recorded
  seeds, the positive-signal development block 20273000–20273059, and the Markov eventwise null
  calibration block 20300000–20300999. Smoke IDs 20272000–20272001 are not reused.
- 72 positive-signal cells: stationary context prevalence `{0.10, 0.50, 0.90}` × persistence
  `{0, 0.50, 0.80}` × signal `{0.05, 0.10}` × proxy error `{0, 0.25}` × hard label cap `{0.20, 0.40}`.
- Four methods share each stream and uniform-query realization: eventwise-propensity scout,
  minimum-propensity scout, pooled rank, and nested context-volume. Keep direct-IPW estimation,
  fixed-mixture certification, FN cost 5, FP cost 1, switching cost 0.05, alpha 0.05, registered
  split, `n=3,200`, and `d=16`.
- Require all 172,800 method-cell-seed rows and unique cell/budget/seed/method keys, positive query
  support, finite evaluator utility, and zero realized cap violations. Save expected and realized
  net gain, promotion and harmful-promotion rates, labels, processed horizon, matched contrasts,
  run environment, protocol and source hashes, and artifact checksums.
- Run on CUDA with six worker processes and seed-derived independent streams. No parameter or
  method changes are allowed after freezing. No figure is planned; use PaperBanana for any later
  visual.

The passed null calibration covers this method's registered event-conditional null, uniform query
process, fixed split, and immediate-feedback Markov contexts. Positive-signal confirmation does not
extend that guarantee to delayed/selective labels, adaptive propensities, nonstationary context, or
other outcome dependence. If either primary lower limit is nonpositive, retain the calibrated method
as an unselected comparator and do not tune on this block. Passing supports an advantage only on
this frozen grid; it is not a novelty claim.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-eventwise-confirm `
  --seeds 600 --seed-offset 20910000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_markov_confirmation_protocol.md `
  --output outputs/scout_context_policy_eventwise_markov_confirmation_600
```
