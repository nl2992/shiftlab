# POSG reduction boundary for delayed budgeted switching

**Date:** 2026-10-28. **Status:** G1 audit update. The generic finite game is
representable, but the audited prior results do not directly solve the full constrained
two-law problem. This leaves a narrow formal gap, not a novelty claim.

## Finding

The registered switching contract has two different criteria on the same learner policy:

\[
\min_{\pi\in\Pi} C_{\mathrm{alt}}(\pi)
\quad\text{subject to}\quad
\sup_{\nu\in\mathcal N} R_{\mathrm{null}}(\pi,\nu)\leq\alpha.
\]

Here \(C_{\mathrm{alt}}\) is expected cumulative decision, query and deployment cost under
the economic HMM; \(R_{\mathrm{null}}\) is probability of ever promoting under a separate
causal-null law. The learner cannot see queried outcomes until their scheduled release, while
the null adversary sees pending outcomes and may choose their conditional laws. Query budget
is reserved at request time. Reversals change current economic value, but do not erase historical
evidence or retroactively validate a forecast.

## What the closest results establish

Wen, Xia and Yu (2025), Theorem 3, study a finite-horizon partially observable zero-sum
semi-Markov game with a probability criterion. By augmenting the observable state with a joint
conditional distribution over hidden state and remaining payoff goal, they establish a Shapley
equation, game value and Nash equilibrium. This is direct prior art for probability/reachability
criteria with hidden state and strategic interaction. It does not, as stated, optimize expected
utility under a second economic law subject to a worst-case null reachability cap. It therefore
blocks novelty based on “partially observed adversarial risk” alone, while not proving equivalence
to the constrained two-law formulation above.

Carr et al. (RSS 2021) combine expected-value maximization with a safety specification in factored
POSGs, deriving safe reward-maximal policies under structural conditions. Their safety construction
uses full observability of safety-related features and an almost-sure avoid-bad-state objective.
That is not the same as an \(\alpha\)-level reachability constraint against a null adversary who
observes pending labels hidden from the learner. It still makes a generic “reward plus adversarial
safety in a POSG” framing inadequate.

RAO* (AAAI 2016) handles expected utility with a chance constraint in a single POMDP model. It
does not supply the separate alternative/null laws or the null player's history-adaptive kernel.
Its existence as a planning template means that state augmentation and chance-constrained planning
are not, by themselves, a contribution.

## Exact reduction boundary

For a finite horizon and finite alphabets, a realization-plan representation of the contract is
exact. One can also scalarize a fixed multiplier \(\lambda\geq0\):

\[
\min_{\pi\in\Pi}\; C_{\mathrm{alt}}(\pi)
 +\lambda\sup_{\nu\in\mathcal N}R_{\mathrm{null}}(\pi,\nu)-\lambda\alpha.
\]

This is not automatically a Shapley recursion in its original constrained form. However, for each
fixed Lagrange multiplier, a hidden root mode mixing the alternative and null worlds converts the
scalarized payoff into a finite-horizon one-sided partially observed stochastic game; the null
player acts only in the null branch and sees pending labels. Strong duality recovers the constrained
value. The construction and its information-set proof are recorded in
`switching_lagrangian_posg_reduction_v1.md`. Thus the generic objective does admit a standard
dynamic-programming representation after scalarization. Generic reachable histories and full
null states still grow exponentially, and no scalable advantage or new bound follows from
representability.

Thus the defensible current conclusion is: the exact finite constrained two-law problem is
representable by standard sequence-form optimization and, after scalarization, by a hidden-root
one-sided POSG. This closes the generic formulation as a novelty claim. The remaining G1 gate is
whether a structural restriction admits a nontrivial compression or approximation guarantee
beyond those standard methods; no such result is currently established.

## Required next test

Seek a declared structural family where a compact recursion or certified approximation improves
on the hidden-root one-sided-POSG dynamic program and sequence-form oracle. Preserve the learner's
nonanticipating information sets, pending-label visibility asymmetry, request-time hard budget,
shared policy across laws, repeated switching costs and absorbing any-promotion event. If no
structural compression retains the risk-relevant history with useful bounds, stop the generic
exact-game method. Any approximation must separately quantify objective error and null-risk
violation. The current-regime alternative-model forecast remains separate from the null-risk
certificate.

## Primary sources

- Wen, Xia and Yu, *Finite-Horizon Partially Observable Semi-Markov Games with Risk Probability
  Criteria*, arXiv:2508.17791 (2025), especially model and Theorem 3:
  https://arxiv.org/abs/2508.17791
- Carr et al., *Safe Policies for Factored Partially Observable Stochastic Games*, RSS 2021:
  https://www.roboticsproceedings.org/rss17/p079.pdf
- Santana, Thiébaux and Williams, *RAO*: An Algorithm for Chance-Constrained POMDPs, AAAI 2016:
  https://ojs.aaai.org/index.php/AAAI/article/view/10423
