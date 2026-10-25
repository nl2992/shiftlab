# Predictable query policies for the eventwise target scout

**Status:** frozen before development execution, 2026-10-25. This is a matched synthetic
development screen. It is not null calibration, independent confirmation, a deployment claim, or a
novelty claim.

## Question

Does the eventwise-propensity-bound target scout retain decision utility when a predictable,
covariate-adaptive query policy replaces uniform querying? Compare uniform, variance-weighted, and
decision-value-weighted queries while holding each stream, query uniforms, candidate family,
scout/certification split, cost budget, and decision rules matched. Compare the eventwise propensity
bound with the existing minimum-propensity bound under each query policy.

The policy probabilities are fitted using pre-monitor data and computed from learner-visible
features, proxy predictions, residual variance, and uncertainty. They do not use current labels,
evaluator-only truth, or prior certification e-process outcomes. This protocol therefore tests
predictable covariate-adaptive propensities, not history-adaptive allocation.

## Registered estimand and development comparisons

The main endpoint is evaluator-known expected postpromotion net decision gain. Report equal-cell
paired contrasts for:

- eventwise-bound scout minus minimum-bound scout, separately for each query policy;
- eventwise-bound variance and decision-value query policies minus eventwise-bound uniform query.

Also report queried labels, mean eventwise support bound, processed horizon, promotion rates, and
harmful promotions. Positive-signal contrasts use the 48 positive-signal profile/cap cells with
equal cell weights and seed-cluster bootstrap intervals. These intervals are descriptive after
scanning methods and are not confirmation. Zero-signal promotion counts are diagnostic only.

## Frozen grid

- 60 matched seed clusters, `20930000`–`20930059`, reused across registered profiles for pairing.
- 36 profiles: target-context prevalence `{0.10, 0.50, 0.90}` × Markov persistence `{0, 0.80}` ×
  context-specific signal `{0, 0.05, 0.10}` × proxy error `{0, 0.25}`.
- Two realized query-label caps: 20% and 40% of the monitor stream.
- Three query policies: `uniform`, `variance`, and `decision_value`. Use common seed-specific
  uniform random numbers across these policies.
- Four decision rules per query policy: pooled rank, nested context-volume, minimum-propensity
  target scout, and eventwise-propensity-bound target scout. Direct-IPW gains, fixed-mixture
  certification, FN cost 5, FP cost 1, switching cost 0.05, alpha 0.05, `n=3,200`, `d=16`, and the
  existing scout/certification split remain fixed.
- Expected output: 51,840 stream-method rows, with unique scenario/cap/seed/query/method keys,
  positive propensity support, finite utility, no realized label-cap violations, and an exact
  check of every eventwise support bound against the recorded propensity path.
- Generate synthetic data on CUDA, using six worker processes. Save Parquet stream/cell metrics,
  paired contrast CSV, zero-signal summary CSV, environment, protocol and source hashes, and
  artifact checksums. No figure is planned; any figure must use PaperBanana.

## Mathematical scope

Let `G_t` be a selected candidate's paired cost improvement, `Q_t` the randomized label indicator,
`q_t` its learner-visible propensity known before the label, and `kappa` the per-event switching
charge. Conditional on the current observed features and the past, if
`E[G_t | F_{t-1}, X_t] <= kappa` and `Q_t` is independently drawn as Bernoulli(`q_t`), then

```text
E[Q_t G_t / q_t - kappa | F_{t-1}, X_t] = E[G_t | F_{t-1}, X_t] - kappa <= 0.
```

With `|G_t| <= C`, the increment lies within the predictable range
`B_t = C / q_t + kappa`. For any fixed betting fraction `lambda` in `[0, 1]`, the factor
`1 + lambda * (Q_t G_t / q_t - kappa) / B_t` is nonnegative and has conditional expectation at
most one. The fixed mixture over these factors is the standard bounded-betting e-process. The
development evaluates this known time-varying-bound construction under feature-based propensities;
it proposes no new validity theorem.

The assumption is an event-conditional decision-gain null for the selected policy. A marginal
aggregate null alone is insufficient when conditional harms can offset across contexts. Delayed or
informative label availability, serially dependent outcomes beyond the stated conditional null,
and query rules using prior certification outcomes are outside this design. Any candidate selected
from this grid requires fresh null calibration and a disjoint positive-signal confirmation under a
separately frozen protocol.

## Reproduction

```powershell
uv run shiftlab-dive-scout-query-development `
  --seeds 60 --seed-offset 20930000 --n 3200 --d 16 --device cuda --workers 6 `
  --protocol docs/scout_context_policy_eventwise_query_development_protocol.md `
  --output outputs/scout_context_policy_eventwise_query_development_60
```
