# Candidate D extraction theorem and adapter audit

**Date:** 2026-10-29. **Status:** conditional adapter match with a local extension;
not yet a verified ShiftLab implementation.

## Source result and assumptions

Horák et al., *Solving Zero-Sum One-Sided Partially Observable Stochastic
Games*, Theorem 4, states that when their HSVI procedure returns justified
lower and upper value functions with initial gap at most `epsilon`, Algorithms
5 and 6 yield an `epsilon`-Nash equilibrium. Algorithm 5 recursively chooses a
learner action distribution and convex combinations of lower-bound alpha
vectors, subject to a one-step value composition dominating the incoming
statewise gadget. Its model is discounted, infinite-horizon, zero-sum and
concurrent-move; Player 2 observes the full state while Player 1 receives
observations. See [the primary source, §10 and Theorem 4](https://arxiv.org/html/2010.11243v1),
particularly Algorithm 5, Proposition 10.7 and Corollary 10.8.

## Adapter mapping

`gadget_stage` implements the finite LP form of Algorithm 5's action-selection
step. Learner action probabilities are `policy1`; convex alpha mixtures are
represented by nonnegative `lambda[a1,o,i]` whose sum equals the probability of
`a1`; and the statewise value composition is constrained to dominate the
incoming gadget and to be no larger than the discounted continuation against
each available opponent action. The LP maximizes this composition at the
provided belief. The sequential toy checks the complete discounted game
against every first-stage opponent choice and every second-stage response,
state by state.

The child-belief update is a local extension of the paper pseudocode, which
uses an assumed stage-game opponent strategy. The adapter uses a full-support
reference response to ensure every structurally reachable observation branch
gets a controller node. This extension has a direct finite-horizon induction
argument under the following conditions: (i) at each node the LP returns a
learner distribution and child vectors satisfying the componentwise
state-by-state gadget inequality against every legal opponent action; (ii)
every positive-probability learner action and every observation reachable from
the current support under any legal opponent action receives a child node; and
(iii) each child controller guarantees its child vector at every supported
state. The induction step substitutes each child's value lower bound into the
one-step composition, then takes the minimum over the current opponent action.
The posterior is used only to choose among feasible compositions, so its
numerical probabilities do not enter this lower-bound argument. A full-support
reference update covers any actual response's reachable state-observation
support, given a common initial support and the same transition kernel.

This proves the belief-choice extension for a finite, exactly solved gadget
tree under those assumptions; it is a direct finite-horizon form of the
max-justification argument behind Proposition 10.7, not a new result. The
remaining adapter checks are implementation fidelity: the finite transformer
must materialize all reachable information histories; numerical LP residuals
must be propagated into the value error; and root HSVI lower-bound vectors must
be the incoming valid gadget. The sequential toy verifies these points only on
its small matching-pennies instance.

### Finite-horizon induction

For each history node `h`, let `rho_h(s)` be its incoming gadget. Suppose the
LP returns learner distribution `p_h` and child vectors `alpha_{h,a,o}` with,
for every state `s` and legal opponent action `b`,

`rho_h(s) <= sum_a p_h(a) [ r(s,a,b) + gamma * sum_{o,s'} P(o,s'|s,a,b) alpha_{h,a,o}(s') ]`.

At the terminal node take `rho=0`. Induct backward over the finite tree. By the
induction hypothesis, the extracted child controller's continuation payoff at
each `s'` is at least `alpha_{h,a,o}(s')` against every continuation response.
Substituting these bounds into the display shows that, for each current
opponent action `b`, the composed controller payoff is at least `rho_h(s)`;
minimizing over `b` preserves the inequality. Thus the root controller
guarantees the root gadget against any history-dependent opponent strategy.
The belief supplied to the LP appears only in its objective, not this
componentwise feasibility inequality, so any tie-breaking belief is valid.

For branch completeness, assume the reference opponent distribution assigns
positive probability to every legal action at every state. If a history can
occur under some actual opponent strategy from the common initial support,
the same learner actions, observations and state path have positive
probability under the full-support reference process. Its posterior therefore
includes every state possible under an actual response on that history, and
the recursive extraction constructs the required child. This support argument
and the induction are **PROVED** for the finite model under the stated
assumptions. In floating point, if every stage's maximum feasibility residual
is at most `eta`, the additive worst-case utility shortfall is at most
`eta * (1-gamma^H)/(1-gamma)` over `H` stages; reward rescaling in a transformed
instance must be included when translating this residual to the original
scalarized objective.

The finite-horizon time-augmented, absorbing-state, reward-rescaled mapping is
exact for a fixed instance if stage-`t` reward is multiplied by
`gamma^(-(t-1))`. The current adapter tests have not exercised that mapping or
its numerical conditioning. They also do not test scalarized two-law costs,
robust-null risk recovery, multiplier search, or post-promotion switching
continuation.

## Verification correction

The earlier residual field measured only whether state values exceeded the
incoming gadget. It now also checks action normalization and bounds,
nonnegative mixture weights, lambda normalization, child alpha-mixture
equalities, gadget lower bounds, and state-by-state/opponent-action upper
composition constraints. The full-game verifier checks the discounted
two-stage security value over state-dependent first-stage and
history-dependent second-stage opponent choices. Updated metrics and hashes
are recorded in `CANDIDATE_D_SEQUENTIAL_ADVERSARIAL_GADGET_RESULTS_V1.md`.

This strengthens only a small software test. It supplies no evidence of an
end-to-end advantage over the exact decomposed solver, Candidate B, or calendar
baselines. Candidate D remains an established-algorithm comparison candidate;
novelty and the full research goal remain open.
