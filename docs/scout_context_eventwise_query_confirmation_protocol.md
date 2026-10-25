# Confirm eventwise scouting with variance-weighted queries

**Status:** frozen 2026-10-25 after the registered 72-cell query-policy null calibration passed
and before this positive-signal confirmation. This is a synthetic-grid confirmation, not a novelty
or deployment claim.

## Question and estimand

Does the eventwise-propensity-bound scout paired with variance-weighted predictable querying
improve evaluator-known expected postpromotion net decision gain over established selection rules
under the same query policy? The primary estimand is the equal-cell mean paired difference in
`expected_postpromotion_net_gain`, with each seed resampled as a cluster across every cell and
method.

The primary comparisons are `variance_eventwise_minus_rank` and
`variance_eventwise_minus_nested_volume`. Each one-sided 97.5% seed-cluster bootstrap lower limit
uses the prespecified Bonferroni allocation for approximate simultaneous 95% familywise coverage.
The primary gate passes only if both lower limits exceed zero. Secondary contrasts compare the
variance-query eventwise scout with the minimum-propensity scout under variance querying and with
the eventwise scout under uniform querying. Do not use secondary contrasts to replace a failed
primary gate. No cellwise significance claims are planned.

## Frozen design

- 600 independent seed clusters, `21300000–21300599`, disjoint from query-policy development
  (`20930000–20930059`) and null calibration (`21210000–21210999`). Each cluster is paired across
  profiles, query policies, caps, and methods.
- 48 positive-signal cells: context prevalence `{0.10, 0.50, 0.90}` × Markov persistence
  `{0, 0.80}` × signal `{0.05, 0.10}` × proxy error `{0, 0.25}` × hard label cap `{0.20, 0.40}`.
- Query policies `uniform` and `variance`, using common seed-specific query uniforms. Four rules
  under each policy: pooled rank, nested context-volume, minimum-propensity scout, and
  eventwise-propensity-bound scout. The decision-value policy is excluded because it was exactly
  equivalent to variance on every development stream; it is not a distinct tested treatment in
  this confirmation.
- Keep direct-IPW estimation, fixed-mixture certification, FN cost 5, FP cost 1, switching cost
  0.05, alpha 0.05, the registered train/validation/scout/certification split, `n=3,200`, and
  `d=16` fixed. Query propensities are fitted before monitoring and do not depend on certification
  labels or evidence.
- Expected output: 230,400 method-cell-seed-query rows, with unique keys, positive support,
  evaluator-known finite utilities, zero cap violations, paired contrasts, cell metrics, protocol
  and source hashes, environment, and artifact checksums. Use CUDA with six workers. No figure is
  planned; use PaperBanana for any later visual.

## Prerequisite and interpretation

The prerequisite is the passed
[`scout_context_eventwise_query_null_calibration_protocol.md`](scout_context_eventwise_query_null_calibration_protocol.md)
and its manifest at
`outputs/scout_context_eventwise_query_null_calibration_1000/reports/manifest.json`. The runner
must verify that the calibration covers both query policies, all context prevalences, persistence
values, proxy-error levels, and budgets before executing confirmation.

The e-process remains the standard bounded-betting construction with predictable
`B_t=C/q_t+kappa`. This experiment does not establish validity under delayed/informative feedback,
history-adaptive query probabilities, conditional-null misspecification, or real data. A failed
primary gate leaves the calibrated eventwise method as an unselected comparator; do not retune on
this block. A passed gate supports an advantage only on this frozen synthetic family and makes no
novelty claim.

## Reproduction

```powershell
uv run shiftlab-dive-scout-markov-eventwise-confirm `
  --seeds 600 --seed-offset 21300000 --n 3200 --d 16 --device cuda --workers 6 `
  --bootstrap-seed 21300600 --query-policies uniform variance --persistences 0 0.8 `
  --null-calibration-manifest outputs/scout_context_eventwise_query_null_calibration_1000/reports/manifest.json `
  --protocol docs/scout_context_eventwise_query_confirmation_protocol.md `
  --output outputs/scout_context_eventwise_query_confirmation_600
```
