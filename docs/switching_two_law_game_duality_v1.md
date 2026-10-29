# Two-law switching objective: exact game reduction and novelty decision

**Date:** 2026-10-28. **Status:** formal G1 reduction. The finite optimization is an instance of
standard constrained extensive-form game optimization; this closes the generic two-law-game
formulation as a method contribution. It does not close the search for a structured scalable
algorithm under additional assumptions.

## Contract and theorem

Fix a finite horizon, finite action and observation alphabets, bounded known label delay, and a
pathwise query budget reserved at request time. The learner has perfect recall of its own past
choices and released labels, but does not observe pending outcomes. A causal-null opponent sees
the full event history, including pending outcomes, and selects each queried binary label's
conditional probability in \([0,1/2]\). The alternative model is a known finite-state HMM. Let
\(x\in X\) denote a learner realization plan on its nonanticipating information sets, and let
\(C(x)\) be alternative-model expected cumulative decision, query and switching cost. Let
\(R(x,\nu)\) be the probability of at least one promotion under null strategy \(\nu\).

**Proposition (finite constrained sequence-form representation).** The problem

\[
\min_{x\in X} C(x)\quad\text{subject to}\quad
\sup_{\nu\in\mathcal N}R(x,\nu)\leq\alpha
\]

is a finite linear program in learner realization probabilities and dual variables for null
opponent behavior. It preserves different alternative and null laws, shared learner behavior,
private delayed feedback, full-history null visibility, request-time budget reservation, and the
absorbing any-promotion event. Its generic size is linear in the expanded extensive-form tree,
which can itself grow exponentially with horizon.

## Proof sketch

The alternative expected cost is a sum over terminal histories weighted by alternative chance
probabilities and learner realization probabilities, so it is linear in \(x\). For each fixed
causal-null strategy \(\nu\), promotion probability is also linear in \(x\). Conditional label
probabilities enter this probability multilinearly; maximizing a multilinear function over the
product of intervals \([0,1/2]\) attains an optimum at endpoints. Thus it suffices to enforce
\(R(x,\nu)\leq\alpha\) for every deterministic endpoint strategy \(\nu\). These are linear
constraints over a finite set of opponent pure strategies. Equivalently, dualize the null player's
sequence-form best-response problem as in the repository's causal-game reference. The learner flow
constraints impose perfect recall and nonanticipation; the action set at every information set
removes query choices once the pathwise budget is spent. Pending labels are opponent-state
variables and are absent from the learner information set, so the construction does not leak them.

For \(0<\alpha\leq1\), the never-promote policy is strictly feasible for the risk inequality
whenever \(\alpha>0\). Since \(X\) is a compact polytope and the robust risk is a finite maximum
of linear functions, convex Slater duality also gives

\[
V^*=\sup_{\lambda\geq0}\;\min_{x\in X}
\left[C(x)+\lambda\left(\sup_{\nu\in\mathcal N}R(x,\nu)-\alpha\right)\right].
\]

For fixed \(\lambda\), the inner problem is a finite zero-sum extensive-form game: the learner
minimizes, the null opponent maximizes, and payoff is \(C(x)+\lambda R(x,\nu)-\lambda\alpha\).
This scalarization is not a compact-state dynamic program. The hidden-mode construction (sample
alternative or null at the root, hide the mode from the learner, and scale branch payoffs) is an
equivalent expected-payoff game, but it does not reduce history dependence or the expanded tree.

## Novelty consequence

Koller, Megiddo and von Stengel (1996) give sequence-form realization plans and linear programs
for two-player zero-sum extensive games with perfect recall; von Stengel (1996) gives the general
sequence-form formulation. The repository's `causal_switching_game.py` already implements the
corresponding finite reference and separately verifies its recovered policies. Consequently,
neither the duality above, a hidden root mode, nor the exact small-game oracle is the new algorithm.
The audited constrained-POMDP, robust-FSC, and risk-criterion POSG literature further closes
generic state augmentation and safety-game claims.

The current general finite-model formulation therefore fails the methodological novelty gate as
stated. The meaningful unresolved question is narrower: can a declared structural family yield a
policy representation or approximation whose memory/runtime grows sub-exponentially while
preserving the original causal-null risk and bounding cost against this full oracle? The existing
posterior-only compression screen fails because distinct histories with the same alternative
belief can have different risk allocation. A valid continuation must prove a compression that
retains that risk-relevant state, or stop this algorithm hypothesis. This decision does not convert
the negative result into a benchmark-paper contribution.

## Sources and implementation evidence

- Koller, Megiddo and von Stengel, *Efficient Computation of Equilibria for Extensive Two-Person
  Games*, Games and Economic Behavior 14 (1996):
  https://ai.stanford.edu/~koller/Papers/Koller%2Bal%3AGEB96.pdf
- von Stengel, *Efficient Computation of Behavior Strategies*, Games and Economic Behavior 14
  (1996): https://www.sciencedirect.com/science/article/pii/S0899825696900500
- Repository reference model: `src/shiftlab/dive/causal_switching_game.py` and
  `docs/switching_causal_game_reference_v1.md`. It shares learner information sets across the
  alternative and null traversals, enforces request-time budget through available actions, and
  records null risk against opponent realization sequences. The saved exact/rational verifiers
  check recovered policies in the registered small cells; they do not prove scalable performance.
