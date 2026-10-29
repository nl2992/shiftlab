# Lagrangian reduction to a hidden-root one-sided game

**Date:** 2026-10-29. **Status:** exact finite-game equivalence; establishes a strong baseline,
not a novel algorithm or a scalable-complexity result.

## Contract

Use the finite-horizon, finite-alphabet contract in
[`switching_two_law_game_duality_v1.md`](switching_two_law_game_duality_v1.md). The learner
chooses queries and deployed models from its own actions and released labels. It reserves a hard
query budget at request time. A known economic HMM defines expected total cost (C(x)). A
separate history-adaptive causal-null player sees all generated labels, including pending labels,
and controls queried labels under the null. For learner realization plan (x), let

\[
R(x)=\max_{\nu\in\mathcal N}R(x,\nu),\qquad
V^*=\min_{x\in X}C(x)\quad\text{s.t.}\quad R(x)\leq\alpha.
\]

Assume (0<\alpha\leq1); the never-promote policy gives strict feasibility when
\(0<\alpha\), except that at \(\alpha=1\) the constraint is redundant. The finite behavioral
policy polytope is compact and convex.

## Proposition: exact scalarized one-sided game

For any \(\lambda\geq0\), define

\[
g(\lambda)=\min_{x\in X}\{C(x)+\lambda(R(x)-\alpha)\}.
\]

For \(\lambda>0\), construct a two-player zero-sum finite-horizon game with a hidden initial
mode \(Z\in\{A,N\}\), where the public learner never observes \(Z\). Set

\[
\Pr(Z=A)=\frac1{1+\lambda},\qquad
\Pr(Z=N)=\frac{\lambda}{1+\lambda}.
\]

In branch (A), the economic HMM generates outcomes and the learner incurs terminal cumulative
payoff \((1+\lambda)C\); the adversary has only a dummy action. In branch (N), the causal-null
player sees the full event history and selects each allowed conditional label law, while the
learner's terminal payoff is \((1+\lambda)\mathbf1\{\text{promotion}\}\). The learner minimizes
payoff and the null player maximizes it. Requests, delayed releases, pending queues, switching
actions, and the request-time budget are represented as ordinary state and event transitions.
The null action follows the learner's request in the event order, so the null player observes the
request and may also condition on pending outcomes.

For every common learner policy and null strategy, expected game payoff is
\[
\frac{1}{1+\lambda}(1+\lambda)C(x)
+\frac{\lambda}{1+\lambda}(1+\lambda)R(x,\nu)
= C(x)+\lambda R(x,\nu).
\]
Maximizing over \(\nu\) and minimizing over the learner therefore gives the inner problem in
\(g(\lambda)+\lambda\alpha\). Histories from branches (A) and (N) with the same learner
actions and released-label history belong to the same learner information set. Thus the hidden-root
construction enforces one shared nonanticipating policy across both laws. The null player, whose
state includes (Z=N) and all pending outcomes, retains the original stronger information.

Because the original finite constrained realization-plan problem is a linear program and is
strictly feasible for (0<\alpha), convex duality gives
\[
V^*=\sup_{\lambda\geq0}g(\lambda).
\]
If an optimal constrained policy lies on a face not attained by a single scalarized optimizer,
recovering it may require mixing among tied policies or solving the primal/dual LP; the value
identity alone is not a policy-recovery algorithm.

## Relation to prior work and limits

The hidden-root game is a one-sided partially observed stochastic game: the learner has imperfect
information over the root mode and hidden queued outcomes; the null player has full information in
its branch. Horák et al. develop strategy composition and value recursion for one-sided POSGs
([primary paper](https://arxiv.org/abs/2010.11243), Sections 6–7 and Proposition 6.2). The
finite-horizon version can be evaluated by backward induction on the expanded game tree. This
establishes that pending-label asymmetry does not prevent an exact dynamic-programming
representation after scalarization.

It does not establish a compact state or practical subexponential runtime. The augmented hidden
mode, HMM state, pending queue, budget, deployment state, and promotion flag are finite, but the
learner's reachable information histories and the null player's full histories can still grow
exponentially with horizon. Existing one-sided-POSG value recursion and the Lagrange multiplier
do not by themselves compress the robust risk/cost frontier. The reduced exact solver remains a
useful oracle-side computation, but no novelty follows from this representation.

## G1 decision

Close the unresolved question “does shared-policy two-law coupling prevent a scalarized
one-sided-game DP?” with **no**: the coupling is exactly represented by the hidden-root mode,
and the pending-label asymmetry matches the one-sided-information structure. Close the generic
Lagrangian/POSG construction as a novelty claim as well. A viable continuation must now specify
and prove a structural compression or approximation that improves on generic one-sided-POSG
planning and the sequence-form oracle, with separate bounds on economic objective error and null
risk. Otherwise revise or stop this algorithm hypothesis. G2–G5 remain held.

This reduction concerns historical promotion risk only. It does not make evidence collected before
a regime reversal certify current challenger value; the economic HMM continuation forecast remains
a separate quantity.
