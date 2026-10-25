# History-predictable direct-IPW bound: proof and implementation check

**Status:** mathematical audit and exact finite-support check, 2026-10-25. This is
not a new monitoring algorithm and does not establish power or empirical
superiority. The repository already contains history-predictable query policies
and predictable-bound e-processes for prediction-powered monitoring; see
[`history_predictable_bound_calibration_protocol.md`](history_predictable_bound_calibration_protocol.md)
and [`predictable_query_bound_replay_protocol.md`](predictable_query_bound_replay_protocol.md).

## Decision-gain increment

Let `G_t` be the gross per-label benefit of a frozen candidate over its reference,
with `|G_t| <= C`. Before the event's query randomization, let `q_t` be measurable
with respect to the past filtration `F_(t-1)` and satisfy `0 < q_t <= 1`. Let
`I_t | F_(t-1), G_t ~ Bernoulli(q_t)`, so query randomization is independent of
the current potential gain conditional on the past. For a fixed switching charge
`kappa >= 0`, define

```text
X_t = I_t G_t / q_t - kappa
B_t = C / q_t + kappa.
```

Under the same-filtration null `E[G_t | F_(t-1)] <= kappa`,
`E[X_t | F_(t-1)] = E[G_t | F_(t-1)] - kappa <= 0`. The support is valid:
when queried, `|G_t/q_t - kappa| <= C/q_t + kappa`; when not queried,
`|X_t| = kappa <= B_t`. Since `B_t` is positive and `F_(t-1)`-measurable,
for any fixed stake `lambda in [0,1]`,

```text
E[1 + lambda X_t / B_t | F_(t-1)] <= 1,
1 + lambda X_t / B_t >= 0.
```

Thus each betting factor is a nonnegative supermartingale factor, and a fixed
convex mixture of such factors gives an e-process with Ville threshold `1/alpha`.
This is the standard bounded-mean construction. It relies on one immediate
feedback update per event, a frozen candidate/reference pair, predictable
positive query probabilities, outcome-independent query randomization, a valid
bound `C`, and the conditional-mean null stated for exactly `F_(t-1)`. If the
label mechanism is delayed, informative, or changes the policy being evaluated,
this argument alone does not apply.

## Why current-context eventwise scaling needs another null

If `q_t` or `B_t` depends on a current context omitted from the null filtration,
then `E[X_t | F_(t-1)] <= 0` does not in general imply
`E[X_t/B_t | F_(t-1)] <= 0`. A finite counterexample has `C=1`, `kappa=1/2`,
`G=1` with probability `3/4`, and `G=-1` with probability `1/4`, so
`E[G]=kappa`. Choose current-context propensities `q=1` for `G=1` and `q=0.1`
for `G=-1`, then randomize queries conditional on that context. Here
`E[X/B]=3/14 > 0`, despite the marginal null. This is why current-context
eventwise bounds require a context-conditional null (or a separate proof); a
history-only propensity avoids this issue because `B_t` is past-measurable.

## Exact implementation check

`tests/test_dive_eprocess.py::test_history_predictable_direct_ipw_bound_has_valid_exact_factors`
enumerates the query and gain outcomes under several past states, predictable
propensities, stakes, and boundary/sub-null gain distributions. It checks the
support and exact conditional expected factors. A companion test verifies the
current-context counterexample above. These are finite algebra checks, not a
Monte Carlo calibration and not a substitute for proving that a real feedback
process meets the stated assumptions.

The existing `EvidenceDirectedQueryPolicy` already supplies a history-only
propensity based on prior monitor wealth and remaining realized budget. The next
empirical step, if pursued, should therefore be a direct-IPW decision-harm
comparison using that existing policy, matched hard label caps, a fresh
null-calibration block, then a disjoint power/utility confirmation. It should be
described as a new application/benchmark of standard predictable betting, not as
a novel e-process theorem. The history-predictable PPI results do not by
themselves establish performance for direct-IPW decision harm.
