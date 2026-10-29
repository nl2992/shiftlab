# Switching problem v1: contract and feasibility screen

> **Risk-frontier clarification:** [The risk audit](switching_risk_frontier_audit_v1.md) shows
> that a fixed predictive e-product gate is a strict restriction of the declared alpha-safe
> policy class. Future method comparisons must include calibrated randomized tests or prove
> why a narrower certificate-engine class is scientifically required. The objective is not
> redefined around the existing gate. The all-policy lower bounds below remain applicable.

2026-10-28. Status: proposed research model, not an established novel method.
G1 remains open pending the theorem-level prior-art comparisons in the novelty delta.

## Information and economics

Fix two policies before the stream. On round t, their losses are l_t(0), l_t(1) in [0,1].
A queried common outcome identifies both losses; unqueried realized losses are not otherwise
revealed to the learner. Actions do not affect outcomes. This excludes bandit counterfactuals.
Let Z_t=l_t(0)-l_t(1) in [-1,1]. Positive Z favors policy 1.

At the start of t, release previously queried labels whose declared availability is t; then
observe X_t, choose A_t in {0,1} and query Q_t in {0,1}, and incur the loss and costs. Query
randomization is conditionally independent of the current outcome given observed information.
Query t becomes visible at the start of t+d_t, with integer d_t>=1. Begin with constant known
d; do not claim informative-delay validity. Query selection may depend on X_t; conditional-mean
assumptions must then condition on X_t as well. Pending labels do not become free at the horizon.

Let H_t be exactly this observed history before the action/query coins. Decisions are measurable
with respect to H_t plus their private coins. Charge unit query cost c>=0 immediately and
switch cost k>0 for A_t != A_(t-1), with A_0=0. Require sum Q_t<=B pathwise, counting pending
queries immediately. Objective is minimizing

    J(A,Q)=E[sum_t l_t(A_t)+c sum_t Q_t+k sum_t 1{A_t!=A_(t-1)}].

The comparison class consists of deterministic policy-index paths with at most S switches,
starting at 0. The evaluator's oracle minimizes expected loss plus the same switching charge
over this class; it knows the mean-loss path and buys no labels. Regret includes the learner's
information cost. Oracle information is deliberately stronger, not silently matched to the
learner. A second comparison against equally informed algorithms uses identical B,c,k,d and
candidate access. These comparisons answer different questions.

## Risk target: do not confuse three guarantees

For initial feasibility analysis, define the global null as
E[Z_t | H_t]<=0 for every round (or the stronger full-history conditional null where required
by the proof). A one-direction false-promotion guarantee is

    sup_(P in null) P(exists t<=T: A_(t-1)=0 and A_t=1)<=alpha.

This controls switches under the global no-benefit null. It does not certify every switch in
a stream containing positive and negative regimes, and it does not include economic break-even.
Sequential direction-specific tests and alpha allocation could support a stronger statement,
but that is an unresolved proof obligation, not an automatic extension.

A future-horizon economic certificate at a switch time tau would instead bound the chance of
declaring E[sum_(s=tau)^(tau+h-1) Z_s | H_tau]>k when that inequality is false. Without a
constraint linking future and observed distributions, the future segment is unidentified.
Subtracting k/h from a past-sample confidence bound does not solve this.

For a viable economic version investigate a declared drift envelope, e.g. marginal means
mu_t with |mu_(t+1)-mu_t|<=v, with a justified conditional observation model. If mu_tau is
known, sum_(j=0)^(h-1) mu_(tau+j)>=h mu_tau-v h(h-1)/2. Delayed samples also require an age
penalty. This elementary envelope is supporting algebra, not a novelty claim. A useful method
must learn enough before the lower bound becomes economically vacuous, while reserving budget
for reversal. Arbitrary abrupt shifts fall outside this envelope; piecewise-stationary alternatives
need explicit segment/dwell assumptions and cannot expose change points to the learner.

## Feasibility proposition: unavoidable delayed loss

**Status:** proved elementary counterexample; originality is not claimed.
Take 0<Delta<=1, T>=nu+d-1 and two deterministic environments. Before nu both policies have
loss 1/2. From nu onward set l_t(0)=(1+Delta)/2, l_t(1)=(1-Delta)/2 in P_plus and reverse
these losses in P_minus. X_t is constant and all queries have delay d. If an algorithm has
false-promotion probability at most alpha in P_minus, then its expected gross decision regret
in P_plus against switching at nu is at least (1-alpha)Delta*d. Its expected net-cost excess
against that comparator is at least (1-alpha)Delta*d-k, including nonnegative query costs.
If using the best at-most-S oracle with S>=1, regret is no smaller than this comparator bound.

**Proof.** Couple private coins in both environments. Up to the action at nu+d-1 no label from
nu onward has arrived; all earlier labels and all covariates coincide. Hence the action histories
through these d rounds have the same law. P_minus satisfies the no-benefit null, so the chance
of any promotion before the end of this interval is at most alpha. On the complementary event
the learner stays at 0 throughout the interval and loses Delta per round relative to policy 1.
At all other rounds the comparator is pointwise no worse in P_plus, yielding the gross bound.
The learner's switching cost is nonnegative, while the comparator pays k once; query costs are
nonnegative. Subtracting at most k proves the net bound. The best oracle has no greater expected
cost than this feasible comparator. QED.

The result holds even with B=T and cannot be repaired by better label allocation. A claim of
uniformly eliminating pre-rollback delay loss is therefore untenable. It does not establish the
optimal B-dependent rate, a multi-switch bound, or an advantage of any proposed algorithm.

## Next derivation

The supporting [joint budget-and-delay obstruction](switching_budget_delay_lower_bound_v1.md)
gives an explicit finite-horizon regret lower bound under the same global-null safety constraint,
including adaptive query policies and nondetections. The [noisy information refinement](switching_noisy_information_lower_bound_v1.md)
adds a binary-KL finite-budget term for a Bernoulli alternative. Both are supporting lower bounds,
not the intended novel contribution. They rule out claims that acquisition can uniformly rescue
arbitrary short regimes or weakly distinguishable shifts.

Determine whether delay-adjusted future-value envelopes and pending-label-aware acquisition
yield a substantive rule beyond standard constrained sequential design. Compare that exact rule
with Cheng et al., The Challenger, active testing, and delayed-learning reductions before coding.
If the reduction is immediate or the feasible envelope is vacuous at realistic delays, revise
the hypothesis. No simulator win can close that theoretical novelty question.
