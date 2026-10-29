# Bayesian quickest detection with finite sampling rights: timing prior audit

2026-10-28. **Status:** source-level model, optimality recursions, and proof appendices inspected;
this closes the generic single-change sampling-timing premise, not the full ShiftLab target.

## Primary source and results

Jun Geng, Erhan Bayraktar and Lifeng Lai, [“Bayesian Quickest Change-Point Detection with Sampling
Right Constraints”](https://arxiv.org/abs/1309.5396), arXiv:1309.5396 (2013). The paper models an
unknown change point with a geometric prior and minimizes a linear combination of average
detection delay and false-alarm probability. It studies a limited number `N` of sampling rights.
After each observation, it updates the posterior change probability, chooses the next sampling
interval using a finite recursion, and stops at a posterior threshold. Theorem 1 gives the optimal
sampling interval recursion; Theorem 2 establishes a threshold stopping structure. The proofs
use dynamic programming and optimal stopping. The paper also treats stochastic sampling rights
and gives a corresponding optimal recursion in Theorem 3.

Thus unknown-onset *one-stream* query timing with a finite number of rights and sequential
stopping is already established in a Bayesian quickest-detection model. It is not enough to
describe adaptive sampling times, posterior-dependent query timing, or joint sampling/stopping
as the new mechanism.

## Contract relation

The prior's main limited-rights model has one observation stream, a geometric change prior,
immediate observations, and a delay/false-alarm scalar objective. ShiftLab has a specified
finite horizon, a hard total cap charged at request time, fixed delayed releases that may leave
multiple queries pending, query cost, repeated reversible deployments with switching cost, and a
finite-horizon probability-of-any-false-promotion guarantee for a conditional-mean null. The
Bayesian prior is model-based and does not provide that worst-case conditional-null guarantee.
The stochastic sampling-right version is still a standard belief-state recursion; adding it as a
generic planner would not be a methodological contribution.

Relative to this particular recursion, delay greater than one allows multiple requests to be
outstanding before earlier labels arrive. That is a difference from Geng et al.'s observation
filtration, but it is not an unoccupied gap: Chick, Forster and Pertile already model a fixed
pipeline delay, ongoing allocations and terminal adoption after the pending outcomes arrive (see
the exact mapping in `switching_delayed_comparator_audit_v1.md`). The residual contract is
recurrent reversible deployment under the robust finite-horizon conditional-null risk, beyond
their stationary one-time adoption model and beyond a constrained planner with pending ages.

## Consequence

The active G1 target should no longer be framed as generic single-stream budgeted sequential
testing, delayed pipelined sampling, or one-shot economic adoption. Those have direct
optimal-control antecedents. The residual candidate is a scalable method for recurrent reversible
deployment under a time-uniform conditional-null guarantee, with a strict finite-sample advantage
over the best episode-wise sequential-design composition and a nontrivial computational or
approximation guarantee relative to the exact causal constrained-planning oracle on small
instances. The oracle is an upper bound on achievable utility in its matched model, not a baseline
that a feasible candidate can beat. If this residual reduces to standard state augmentation plus
test resets, revise the hypothesis rather than claiming algorithmic novelty. Keep promotion
validity and current-regime forecasts separate after reversals.
