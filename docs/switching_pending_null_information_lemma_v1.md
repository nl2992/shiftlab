# Predictable betting survives pending-label information asymmetry

**Date:** 2026-10-29. **Status:** elementary validity lemma and novelty boundary.

Let the null player's filtration `H_t` contain all queried outcomes generated through event `t`,
including labels pending release to the learner. Let `G_t` be the learner's released-label/action
filtration, so `G_t` is a sub-filtration of `H_t`. At a predictable query time `tau_j`, let
`Y_j` be the queried binary outcome and assume the full-history conditional null
`E[Y_j | H_{tau_j-1}] <= 1/2`. Choose a stake `lambda_j in [0,1]` using only information
available to the learner before requesting the label. Then `lambda_j` is also measurable in the
null's richer pre-outcome filtration, and

```text
E[1 + lambda_j(2Y_j-1) | H_{tau_j-1}]
  = 1 + lambda_j(2 E[Y_j | H_{tau_j-1}] - 1) <= 1.
```

The factor is nonnegative. Consequently the product of these factors is a nonnegative
supermartingale in the generated-outcome filtration, and Ville's inequality controls the event
that it ever crosses `1/alpha` by `alpha`. With a known deterministic delay and in-order release,
the learner can update the same product when each label arrives; a promotion made only after the
released product crosses is a subset of the crossing event. The null's ability to condition on
pending labels does not invalidate the gate. The same argument holds for bounded `X_j in [-1,1]`
with `E[X_j|H_{tau_j-1}]<=0` and factor `1+lambda_j X_j`.

This lemma does not optimize query times, prove useful power, handle informative delay or
out-of-order release without an explicit filtration, or make old evidence certify benefit after a
reversal. It closes “account for pending-label information asymmetry by inventing a new safe
betting gate” as a novelty direction. Query acquisition still needs a theorem-level improvement
in net switching cost against matched active-sensing / sequential-design baselines.

The repository's fixed-calendar detector derivation already applies the related predictable
likelihood-ratio construction with fixed delay; this lemma makes explicit why the richer null
filtration is safe. See `switching_fixed_calendar_e_detector_bound_v1.md` and the causal-game
contract in `switching_two_law_game_duality_v1.md`.
