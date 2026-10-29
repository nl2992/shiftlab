# Robust optimal stopping boundary for first promotion

**Date:** 2026-10-29. **Status:** primary-source scope audit; the first-promotion Bellman split
is standard, while the coupled two-law constrained problem remains unresolved.

## Primary source inspected

Bayraktar and Yao, “On the Robust Optimal Stopping Problem,” arXiv:1301.0091, especially the
problem statement and Theorem 5.1. They study a stopper maximizing worst-case expected payoff
over a family of probability laws, with an adverse evaluator selecting the law. Under their
regularity and weak-stability-under-pasting conditions, the upper Snell envelope provides a
dynamic programming principle and an optimal stopping time; the controller-stopper game has a
value. The result is a continuous-time, path-dependent robust stopping theorem for non-dominated
model uncertainty. This is a theorem-scope audit, not a transfer of their proof to ShiftLab.

## Relation to the first-promotion subproblem

The pre-promotion decision is indeed an optimal stopping/acquisition problem: continue observing
or promote, with a continuation cost supplied by the alternative-model switching problem. Calling
that decomposition a new stopping algorithm would therefore be misleading. Robust Snell-envelope
methods are relevant prior art for stopping under model uncertainty.

The source does not directly solve the ShiftLab objective. Its basic criterion is a worst-case
expected payoff under a model family for the same stopping problem. ShiftLab minimizes expected
cost under an alternative economic HMM subject to a separate global upper bound on the probability
of any promotion under a history-adaptive causal null. The learner's policy is shared across both
laws; the null adversary sees queried outcomes that can still be pending for the learner; requests
consume a pathwise hard budget; and promotion continuation has recurrent reversible switching
costs. The value-function recursion from robust stopping alone does not establish exact state
compression, duality, or a scalable approximation with separate objective and null-risk guarantees
for this coupled criterion.

## G1 decision

This audit closes “robust optimal stopping plus a continuation value” as a novelty claim. It does
not show that the complete two-law problem is already solved, and the remaining mismatch is not
evidence of novelty. The exact sequence-form solver is still the correctness oracle. A future
method must prove a nontrivial compactness, approximation, or policy-value result for the
alternative-cost / causal-null-risk frontier, preserving pending-label information asymmetry and
the request-time cap, and compare it with robust stopping, safe sequential testing, delayed-POMDP
planning, and the exact oracle on small instances. Until then G1 is open; G2–G5 remain held.

Promotion validity remains separate from a current-regime forecast: the stopping theorem and the
null-risk guarantee say nothing about whether the challenger is still beneficial after a regime
reversal.

## Source

- Bayraktar and Yao, [*On the Robust Optimal Stopping Problem*](https://arxiv.org/abs/1301.0091),
  arXiv:1301.0091, version 10 (2016), especially Theorem 5.1 and the weak-stability-under-pasting
  conditions used for its dynamic programming result.
