# Eventwise-scout support-bound attribution audit

**Date:** 2026-11-04. **Status:** code-level mathematical audit; no rerun or changed empirical
claim. This audit rechecks whether the eventwise-propensity scout's synthetic advantage isolates a
new support-bound mechanism.

## Finding

In the registered abrupt-drift confirmation, the query policy is `uniform` and the target query
rate is `b`, where `b` is the label-budget rate. `AdaptiveQueryPolicy.probabilities` returns the
constant propensity `q_t=b` for this policy. However, `_fit_candidate_family` records the generic
floor as `q_min=b/2`. The confirmation protocol explicitly says it uses the uniform-query design.

For the eventwise scout, the conditional certification increment and bound are

```text
X_t = Q_t * gain_t / q_t - switch_rate
U_t = max(fn_cost, fp_cost) / q_t + switch_rate.
```

For the minimum/global-bound scout, the same query flags, inverse-propensity gain estimate,
context counts, candidate selection, and fixed-mixture betting rule are used, but its bound is

```text
U_global = max(fn_cost, fp_cost) / q_min + switch_rate.
```

Under this confirmation's constant uniform `q_t=b`, setting the minimum floor to the *known actual
propensity* `q_min=b` makes `U_global=U_t` at every event. The scout-stage statistics are already
the same: both use the same uniforms, queried labels, Horvitz–Thompson weights `1/b`, context
counts, and independent scout/certification split. Consequently the selected context policies and
certification factors coincide (up to floating-point summation order). The purported eventwise
versus minimum-bound method contrast is therefore an exact known-propensity correction to a
conservative baseline, not a distinct algorithm on this design.

The pooled-rank and nested-volume arms also use the global process bound based on `q_min=b/2`.
Their reported differences from eventwise scout therefore mix policy-selection differences with
this twofold support-bound discrepancy. The registered results remain accurate for the code and
protocol that ran; they do not isolate the eventwise mechanism against a globally bounded process
using the same certified propensity information.

The same issue is confirmed in the full Markov-context and temporal-context manifests. Both list
`query_policy: uniform`, the same four arms (`rank`, `rank_context_volume`, minimum-bound scout,
and eventwise-bound scout), and the shared `_fit_candidate_family` implementation. The Markov
confirmation covers 72 positive-signal cells and 600 seed clusters; the temporal confirmation
covers 32 cells and 600 seed clusters. Thus their registered eventwise-minus-rank and
eventwise-minus-nested-volume contrasts also combine contextual selection with the loose global
floor. They remain valid descriptions of the frozen implementations and grids, but do not isolate
the eventwise support mechanism. This extension applies to these uniform-query confirmation
artifacts; it should not be generalized to variance-query runs without checking their realized
propensity paths and registered floor.

The saved row-level outputs also permit a paired arm check. In all 43,200 Markov pairs and 19,200
temporal pairs, the minimum-bound and eventwise arms have identical selected candidate IDs,
selected candidates by context, scout selection gains, queried-label counts, and processed-event
counts. The arms differ in their certification process weights and decisions: eventwise process
bounds are about one half the minimum-bound values, while total promotions are 3,570 versus 1,631
for Markov and 1,018 versus 240 for temporal. This directly localizes the observed contrast to the
certification bound on these streams rather than to different contextual selections. These totals
are descriptive counts from the archived confirmation rows, not a new inference procedure.

## Reproduction trail

- `src/shiftlab/dive/budgeted_promotion.py` sets `q_min = budget_rate / 2` when fitting query
  policies, uses `outcome_bound / q_min + switch_rate` for the global-bound scout, and uses
  `outcome_bound / cert_propensities + switch_rate` for the eventwise scout.
- `src/shiftlab/dive/query.py` returns `target_rate` at every event for `method == "uniform"`.
- `src/shiftlab/dive/budgeted_promotion_context_drift_confirmation.py` freezes
  `query_policies=("uniform",)`; the protocol records a uniform-query design.
- `outputs/scout_context_policy_eventwise_markov_confirmation_600/reports/manifest.json` and
  `outputs/scout_context_policy_eventwise_temporal_confirmation_600/reports/manifest.json` record
  the uniform-query configurations and confirmation grids.
- Their `metrics/eventwise_*_confirmation_streams.parquet` files were paired on scenario, seed,
  query policy, and budget rate to compare selection and certification fields.

These are direct code-path comparisons. No stochastic rerun is needed to establish the algebraic
equivalence for a fixed uniform propensity.

## Consequence and next gate

Do not cite eventwise-versus-minimum-bound or eventwise-versus-pooled-rank/nested-volume contrasts
from the old uniform-query runs as evidence of an eventwise-bound gain. The corrected fresh-seed
development now answers the narrower candidate-selection question: with `q_min=q_t=budget_rate`,
the eventwise and minimum-bound scout arms had identical expected utility and promotion decisions;
the contextual scout exceeded pooled rank by `+9.7148` and nested context-volume by `+8.0688` on
the positive-signal grid (descriptive bootstrap intervals only). See
`outputs/scout_context_known_uniform_markov_development_v1/` and its frozen protocol.

A separate 1,000-stream-per-cell null calibration for the exact-floor eventwise rule passed all 36
registered Markov-context cells: 95 false promotions over 36,000 rows, zero cap violations, and
maximum simultaneous cellwise upper limit `0.02051`. Its scope is only the registered synthetic
conditional-mean null and process family. The disjoint 600-seed positive-signal confirmation then
passed both registered primary comparisons: eventwise scout minus rank `+8.5961` (one-sided
familywise lower limit `+7.6906`) and minus nested context-volume `+7.4721` (lower limit `+6.6029`).
It reproduced the eventwise/minimum-bound equivalence on all 43,200 scout pairs. These are confirmed
synthetic results against internal baselines, not a SOTA comparison. The remaining literature gate
is a source-faithful anytime-valid OPE confidence-sequence comparator for the selected fixed
context-mapping estimand, signed bounded gain, query propensity, budget, and switching charge.

The fixed-query support-bound correction is standard and does not itself constitute a novelty
claim. Any surviving contribution would need to come from the contextual selection procedure or a
different, nonuniform predictable-query setting, and then beat the strongest matched comparator.
