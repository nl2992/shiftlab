# Candidate D finite-horizon OS-POSG model-match audit

**Date:** 2026-10-29. **Status:** exact finite-game embedding is available;
published HSVI interface is only conditionally transferable; no size or runtime
advantage established. **Decision:** D1 passes as a mathematical reduction, not
as an efficiency or novelty result. Continue to a bounded implementation screen
only if a faithful solver and evaluator can be built without changing the game.

## Source-matched model

For fixed `lambda > 0`, the hidden-root game in
`docs/switching_lagrangian_posg_reduction_v1.md` starts in alternative mode with
probability `1/(1+lambda)` and causal-null mode with probability
`lambda/(1+lambda)`. The learner does not observe the mode. On the alternative
branch, the finite HMM generates outcomes and the other player has a dummy
action. On the null branch, the full-information player controls the conditional
label law. Scale alternative cumulative economic cost and null first-promotion
indicator by `(1+lambda)`. The learner's expected scalarized cost is then
`C(pi)+lambda R(pi)`; subtracting `lambda alpha` is constant in the policy.
At `lambda=0`, solve the alternative control problem directly.

The event order matters. In `causal_switching_game.py`, learner action and query
are selected first; after a query, the null selects a conditional probability
using the request and complete generated history. Represent each round as two
microstages: first the learner acts; then, only when needed, the full-information
player responds to the stored request and the environment draws the label. A
forced dummy learner action in the response microstage prevents an extra learner
decision. The label is hidden from the learner until its release time. At a
promotion decision, mark the risk event immediately and continue only for the
alternative economic branch. This turn-based expansion preserves the original
leader-follower event order, which a single simultaneous-action stage would not.

The hidden state is finite for each fixed instance: root mode; alternative HMM
state; pending labels and release times; current phase/time; stored current
request; remaining budget; deployed model; and first-promotion flag. The null
player's admissible behavior must still depend on its full remembered history,
not only this physical state. For a fixed learner policy, promotion probability
is multi-affine in the null's conditional probabilities, so a maximizing null
has an endpoint response at each information history (`0` or `1/2`); hence the
null action alphabet can be finite. This does not justify merging distinct
response histories. The learner's information is its own actions and released
labels; root mode, current HMM state, pending labels, and null moves remain
hidden. The opponent sees the complete state/action history, including pending
outcomes, as required.

## Connecting finite horizon to the cited HSVI theorem

Horák et al. define OS-POSGs with finite state/action/observation sets, one
imperfectly informed player, a fully informed opponent, simultaneous stage
actions, and discounted infinite-horizon reward. Their Theorem 4 says that the
output of their HSVI value algorithm plus the two strategy-extraction algorithms
is an epsilon-Nash equilibrium. The theorem does not directly state a
finite-horizon, request-then-response, constrained-risk result.

For a horizon `T`, split each round into the microstages above, augment state
with the stage index, and make the state absorbing with zero reward after the
last microstage. Pick any `gamma` in `(0,1)`. If the desired undiscounted reward
at microstage `j` is `r_j`, assign reward `gamma^(-(j-1)) r_j`; then the
discounted sum is exactly `sum_{j=1}^{2T} r_j`. Negate the scalarized cost so
that the learner is Horák's maximizing player and the causal null is the
minimizer of its payoff.
This is an exact finite-game embedding with bounded rewards for fixed `T`,
positive finite `gamma`, and bounded per-stage costs. It imports the strategy
security theorem only after the finite transformed game is passed faithfully to
the solver; it does not imply a useful uniform error or runtime bound in `T`.

The scaling is material: the largest transformed stage reward may grow as
`gamma^(-(2T-1))`, while HSVI's bounds and exploration use the discounted reward
range. Choosing `gamma` close to one controls that range but weakens discount
contraction. The paper supplies no finite-iteration complexity bound for this
particular transformed family. Its strategy-extraction procedure is an online
gadget/controller; expanding it to a table for exact full-history risk and
post-promotion cost verification may itself be exponential. These quantities
must be included in any runtime and memory comparison.

## Recovery lemma checks and limits

The branch recovery note's use of the finite-LP duality is valid for the exact
finite game. Its global assumption `C(pi) <= T` is stronger than the repository
contract when positive query and switching charges are added. It is unnecessary:
the multiplier bound only needs a feasible never-promote policy with cost at
most `T` (incumbent decision loss is at most one per round, with no query or
switch charges). Thus `g(0) >= 0` and `g(lambda) <= T-lambda alpha` still imply
that a maximizer lies in `[0,T/alpha]`. The endpoint policies need only satisfy
the stated scalarized near-optimality and exact risk bracket. Replace the global
cost bound with this weaker, model-matched condition.

For two policies with exact risks `r_- >= alpha >= r_+`, the root-mixture weight
sets the weighted risk to `alpha` and expected alternative cost is linear. For
any fixed causal-null strategy, risk under the mixture is the same weighted
average of risks under its component policies; taking the supremum is bounded
by the weighted sum of component worst-case risks. The lemma remains conditional:
it does not show that HSVI at any finite set of multipliers yields two policies
whose verified risks bracket `alpha`. Approximate risk intervals must certify
both sides of that bracket.

The posterior-alias counterexample remains intact because the imperfectly
informed player's action-observation history is retained and the fully informed
opponent remembers the full null history. Any implementation that uses only the
alternative belief as a strategy key would change the game. The signed
future-value/reversal counterexample also remains intact: the hidden-root
scalarized payoff charges the full alternative cumulative switching cost,
including post-promotion rollback and re-promotion, while null risk is absorbed
at first promotion. Do not substitute the promotion indicator for the later
alternative continuation cost.

## Decision

The finite-horizon game mapping is exact after the explicit microstage expansion
and reward rescaling. Horák et al.'s solver is a relevant established baseline,
not a new method. No bound shows its transformed belief search or extracted
controller is smaller than the exact decomposed sequence-form oracle. D2 remains
open pending a reproducible implementation/complexity audit; any pilot must
measure complete solve, extraction, multiplier search, exact risk verification,
and continuation evaluation. Do not open real data or claim G1/G2/G3 success.

## Primary-source check

Horák, Bošanský, Kovařík and Kiekintveld, *Solving Zero-Sum One-Sided Partially
Observable Stochastic Games*, arXiv:2010.11243v1, §§4, 9–10 and Theorem 4:
[arXiv HTML](https://arxiv.org/html/2010.11243v1). The paper explicitly assumes
simultaneous stage actions and discounted-sum rewards, defines the opponent's
strategy on full histories, and obtains epsilon-Nash strategies only after
strategy extraction from the value bounds.
