# Joint utility-risk abstraction: derivation and novelty screen

**Date:** 2026-10-29. **Status:** standard finite-horizon bound derived; no new algorithm,
compact representation, or novelty claim established. This continues the latest G1 checkpoint in
`docs/budgeted_switching_research_goals.md` after the exact posterior-alias and risk-slack screens.

## Contract being approximated

Use the finite two-law game already implemented in `causal_switching_game.py`. The learner's
behavioral strategy is shared across laws. Under the alternative law, its expected bounded
economic reward is the objective. Under the causal null, the worst history-adaptive opponent's
probability of ever promoting is the constraint. The exact analysis tree includes event time,
deployment/promotion flag, remaining query rights, pending labels, learner-visible history, and the
null opponent's private history. The implemented controller may use only learner-visible
information: its abstraction map must respect those information sets, and it must never expose the
opponent's private outcomes to the learner.

Let the resulting full-history state be `x`, the learner action be `a`, alternative stage reward
`r(x,a) in [0,1]`, and alternative transition kernel `P_1`. Let `K_0(x,a)` be the set of
push-forward next-state distributions admitted by the null opponent. Assume the null ambiguity is
rectangular conditional on the augmented state. For a partition map `phi`, define the pushed-
forward kernels on abstract blocks.

For any two states `x,x'` in one block and any learner action `a`, impose:

    |r(x,a)-r(x',a)| <= eps_r
    TV(P_1^phi(.|x,a), P_1^phi(.|x',a)) <= eps_1
    d_H^TV(K_0^phi(x,a), K_0^phi(x',a)) <= eps_0,

where `d_H^TV` is Hausdorff distance induced by total variation. The partition also preserves the
promotion-absorbing flag and all hard resource/pending-feedback coordinates exactly.

## Bound for a fixed abstract controller

For any horizon-H controller that chooses the same action at states in the same block, coupling
the alternative trajectories one step at a time gives

    |V_1^phi(x)-V_1^phi(x')|
      <= H eps_r + eps_1 H(H-1)/2.

At each stage, reward mismatch contributes at most `eps_r`; a transition mismatch at stage `t`
changes at most `H-t-1` future rewards, each in `[0,1]`. Summing yields the displayed bound.

For the null reachability objective, first take the union of null transition sets over all private
opponent histories compatible with one learner-visible controller memory state. This is a
conservative ambiguity set for an implementable controller. Backward induction over the resulting
robust Bellman recursion gives

    |R_0^phi(x)-R_0^phi(x')| <= H eps_0,

provided the null kernel sets are rectangular and the promotion event is encoded as an absorbing
state. At each step, the two null maximizations differ by at most their Hausdorff-TV distance;
the continuation reachability value lies in `[0,1]`.

If the abstract null kernel set is the union of all concrete pushed-forward sets in a block, then
every lifted controller that respects learner information sets is conservatively safe: its
concrete worst-case null risk is no larger than its abstract risk. This is only one-sided. An
optimal full-history policy with risk
exactly `alpha` may have no abstract representative feasible at `alpha`; a margin or a risk-reducing
mixture is needed. Mixing toward never-promote incurs utility loss proportional to the mixture
weight and can be large when `alpha` is small.

## What this resolves—and what it does not

This supplies the joint local error quantities missing from a utility-only approximate-POMDP
argument: `eps_1` controls alternative value, while `eps_0` controls null risk. It also explains
why a scalar “positive risk slack” is insufficient: slack is useful only after a uniform risk error
bound is available. The alias counterexample in
`switching_alt_belief_risk_alias_counterexample_v1.md` remains consistent with this result because
posterior-only merging does not satisfy the null-kernel condition.

The bound is a direct finite-horizon approximate-bisimulation/coupling argument for a constrained
game. It is not a method contribution by itself. In the current ShiftLab contract, the controller
cannot condition on the null player's private history, while the robust risk analysis must account
for it. Forming the conservative ambiguity-set union and checking its Hausdorff distance across
all compatible hidden histories can be as hard as constructing the original tree. A useful
algorithm still needs a polynomial-size representation that computes or upper-bounds both errors
without enumerating that tree, together with a nonvacuous risk-feasible utility bound against the
full-history sequence-form oracle. No such representation is established here.

## Kill test and next gate

Do not code a generic abstraction or run efficacy experiments from this derivation. The next G1
step is to test whether the repository's two-law game admits a finite-dimensional *joint* predictive
state (alternative reward belief plus a certified upper envelope for null reachability) whose
update is closed under pending releases and request-time budget consumption. Compare its state
count and value/risk error against robust finite-state controllers and the sequence-form oracle on
a growing family. Kill this route if computing the risk envelope is exponential in horizon, if the
required null-set enlargement consumes the available alpha slack, or if the resulting scheme is
just standard constrained-POMDP state discretization.

Historical promotion evidence remains distinct from a forecast of current-regime utility after a
reversal.
