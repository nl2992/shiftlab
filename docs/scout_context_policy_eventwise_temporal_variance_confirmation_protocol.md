# Eventwise-scout temporal variance-query confirmation protocol

**Status:** frozen 2026-10-25 after independent variance-query null calibration and before the
positive-signal seed block. This is a synthetic benchmark confirmation, not a novelty or deployment
claim.

## Prerequisite calibration

The required null calibration is
[`scout_context_policy_eventwise_temporal_variance_null_results.md`](scout_context_policy_eventwise_temporal_variance_null_results.md), with manifest
[`outputs/scout_context_policy_eventwise_temporal_variance_null_1000/reports/manifest.json`](../outputs/scout_context_policy_eventwise_temporal_variance_null_1000/reports/manifest.json).
The runner must verify the passed status, the 16-cell family and gate, variance query policy, exact
schedules, proxy-error rates, caps, and normalized manifest SHA-256
`e60dc80185335cd0328cc80a57fdec82ad23d611361db9773201cf64185b97a0` before it starts the
confirmation streams.

## Question and estimands

On registered gradual and recurring context schedules, does the eventwise-propensity-bound scout
under variance-weighted querying improve evaluator-known expected postpromotion net decision gain
over pooled rank and nested context-volume allocation? The primary endpoint is the equal-cell mean
of paired differences in `expected_postpromotion_net_gain` across the 32 positive-signal
profile/cap cells. Pair streams by seed, cell, and common query random numbers.

The two primary comparisons are variance-query eventwise scout minus variance-query pooled rank,
and variance-query eventwise scout minus variance-query nested context-volume. Use 10,000
seed-cluster bootstrap draws and report percentile two-sided 95% intervals plus one-sided 97.5%
lower limits for these two primary comparisons. Bonferroni allocation across the two lower limits
provides an approximate simultaneous 95% familywise assessment. The primary gate passes only when
both lower limits exceed zero. This bootstrap assessment is approximate, not an exact
finite-sample guarantee. The following are secondary, descriptive comparisons: variance-query
eventwise versus the variance-query minimum-propensity scout, eventwise variance versus eventwise
uniform querying, and schedule-specific estimates. Do not make cellwise significance claims.

## Frozen design

- Use 600 independent matched seed clusters, `21440000`–`21440599`, disjoint from temporal
  development (`21420000`–`21420059`), variance-query temporal null calibration
  (`21430000`–`21430999`), and the existing uniform-query temporal confirmation
  (`20920000`–`20920599`).
- Cross four deterministic prevalence schedules, signal strengths `{0.05, 0.10}`, proxy errors
  `{0, 0.25}`, and hard label caps `{0.20, 0.40}`: 32 positive-signal profile/cap cells.
- Compare four allocation methods under both uniform and variance query policies. Share query
  uniforms across those policies for common random numbers. This produces 153,600 expected
  method-cell-seed-query rows.
- Keep the direct-IPW estimator, fixed-mixture certification, FN cost 5, FP cost 1, switching cost
  0.05, alpha 0.05, registered split, `n=3200`, and `d=16`. Fit query multipliers only on the
  validation split and freeze them before monitoring. Oracle parameters and future outcomes remain
  evaluator-only.
- Require unique cell/cap/seed/query/method keys, positive propensity support, finite expected
  utility, and zero realized cap violations. Record expected and realized net gain, promotions and
  harmful promotions, label counts, horizon, protocol/calibration/source hashes, and artifact
  checksums. Run on CUDA with six workers.

This confirmation is restricted to the registered synthetic schedules, fixed split/candidate set,
predictable query policies, immediate complete feedback, and specified costs. It does not cover
delayed or selective labels, query probabilities adapted to certification evidence, other outcome
dependence, or real-world utility. A primary-gate failure leaves variance querying unconfirmed; do
not tune on this seed block. No novelty claim follows. No figure is planned; use PaperBanana for any
later research visual.

## Reproduction

```powershell
uv run shiftlab-dive-scout-temporal-confirm `
  --query-policies uniform variance `
  --seeds 600 --seed-offset 21440000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_temporal_variance_confirmation_protocol.md `
  --calibration-manifest outputs/scout_context_policy_eventwise_temporal_variance_null_1000/reports/manifest.json `
  --output outputs/scout_context_policy_eventwise_temporal_variance_confirmation_600
```
