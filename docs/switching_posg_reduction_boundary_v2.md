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

This is a robust constrained-game objective, not automatically a Shapley recursion: expected
alternative cost and null reachability are evaluated under distinct laws, and the same learner
policy must satisfy the constraint. To turn the scalarization into a tractable dynamic program
requires a valid information-state construction, rectangularity/duality conditions and a proof
that the policy class and pathwise budget are preserved. No such reduction has been established
in this audit. Generic sequence-form LP size remains exponential; no scalable advantage or new
bound follows from representability.

Thus the defensible current conclusion is: existing results cover adjacent pieces, but the audited
theorems do not establish the exact constrained two-law result. Neither “already solved” nor
“novel” is supported. The G1 gate stays open pending an explicit reduction or a theorem-level
separation; no prototype claim should be made yet.

## Required next test

Construct a growing finite family and attempt a reduction to (i) a constrained robust POMDP/POSG
with an augmented state and (ii) a sequence-form constrained stochastic game. Prove the learner's
nonanticipating information sets, pending-label visibility asymmetry, request-time hard budget,
shared policy across laws, repeated switching costs and absorbing any-promotion event are all
preserved. If the reduction is generic and exponentially large, treat it as a characterization,
not a method. Then seek a structural restriction under which a compact recursion is provably valid,
or stop the proposed exact-game method. Any approximation must separately quantify objective error
and null-risk violation. The current-regime alternative-model forecast remains a separate output
from the null-risk certificate.

## Primary sources

- Wen, Xia and Yu, *Finite-Horizon Partially Observable Semi-Markov Games with Risk Probability
  Criteria*, arXiv:2508.17791 (2025), especially model and Theorem 3:
  https://arxiv.org/abs/2508.17791
- Carr et al., *Safe Policies for Factored Partially Observable Stochastic Games*, RSS 2021:
  https://www.roboticsproceedings.org/rss17/p079.pdf
- Santana, Thiébaux and Williams, *RAO*: An Algorithm for Chance-Constrained POMDPs, AAAI 2016:
  https://ojs.aaai.org/index.php/AAAI/article/view/10423
