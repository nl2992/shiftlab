# Known-onset sequential-test reference

2026-10-28. Registered before execution. **Purpose:** determine whether the noisy
delay-budget-risk lower bound leaves a large gap even in the easier known-onset sequential
testing problem. This is a classical reference calculation, not a candidate method, novelty claim,
or efficacy experiment.

## Contract and scope

Use `T=120`, `nu=61`, `B=20`, `epsilon=1/10`, `alpha=1/20`, query cost `c=1/100`, switch
cost `k=1/10`, and fixed delay `d in {1,5,20}`. Under the global null, labels are iid
Bernoulli(1/2); under the alternative, labels at event times `s>=nu` are iid
Bernoulli(1/2+epsilon). A queried common outcome reveals `Y_s`, with losses `Y_s` and
`1-Y_s`. Promotion is one-way and has global-null probability at most alpha. Regret is against
the one-switch-at-nu comparator, which pays k. Queries count against a pathwise cap B and arrive
after d rounds.

Give the learner the onset nu. An independent activation lottery may either do nothing or issue
the full fixed cohort of B consecutive labels at event times `nu,...,nu+B-1`; all B requests are
charged on activated paths. Once labels arrive, the learner may promote at a label release based
on the number of positives so far, or stop testing. No rollback is included. This is a reference
class benchmark, not a globally ordered upper bound for the original unknown-onset problem:
revealing nu helps, but restricting acquisition to a fixed cohort can hurt relative to adaptive
querying.

At the release of the nth label, the decision round is `t_n=nu+n+d-1`. Promotion then saves
`v_n=2*epsilon*(T-t_n+1)` units of future gross regret relative to never promoting. Its
incremental value relative to the comparator's switch charge is `v_n-k`. For a count-state
stopping policy, let `y[n,s]` be the null probability of reaching n arrived labels with s
positives and remaining active; let `x[n,s]` be the null probability of promoting there. The
likelihood ratio is `L[n,s]=((1/2+epsilon)/(1/2))^s*((1/2-epsilon)/(1/2))^(n-s)`. The finite LP
maximizes

`sum_(n,s) L[n,s]*(v_n-k)*x[n,s] - c*B*y[0,0]`

subject to null promotion risk `sum x[n,s] <= alpha`, `0<=x[n,s]<=y[n,s]`, and the count-state
flow constraints under Bernoulli(1/2), with the remaining active mass either continuing or
abandoning. At n=B continuation is prohibited. Include activation `0<=y[0,0]<=1`; the inactive
mass is the no-query policy. The resulting policy must be checked for coordinatewise monotonicity
of promotion in the label sequence. Such monotonicity makes iid Bernoulli(1/2) least favorable
among the full-history conditional nulls `P(Y_s=1|past, predictable query)<=1/2` by uniform
coupling. If the numerical optimizer's recovered policy is not monotone or cannot be certified,
the result is only an iid-null benchmark and must not be described as satisfying the registered
conditional-null contract.

The finite occupancy LP is solved numerically; no exact rational optimality certificate is claimed.
The recovered policy is checked over every one of the `2^20` binary label sequences and every
single-coordinate increase. Promotion probability is coordinatewise nondecreasing, so coupling
the conditional-null labels with iid Bernoulli(1/2) uniforms proves that the full-history
conditional null has promotion risk no greater than the boundary iid risk. An independent forward
recursion under both the null and alternative reproduces the LP null risk and alternative cost.

The exact reference class is standard constrained sequential testing / optimal stopping. It does not
establish an unknown-onset rule, adaptively useful query allocation, a new theorem, or a novel
algorithm. Compare its net excess with the information lower bound, but treat the known-onset
reference as a diagnostic rather than an equally informed baseline. Persistent iid benefit is
assumed throughout; this does not certify value after a regime reversal.

## Verification protocol

Implement the finite occupancy LP, save parameters, source hash, optimal net excess and null risk,
and reconstruct the behavioral action probabilities. Verify flow residuals, activation and hard
cap, global-null risk, and monotonicity over every prefix state. Independently evaluate the
recovered policy under null and alternative by forward recursion. Compare against the no-query
policy and the lower bound for each delay. If the solver output cannot be rationally reconstructed,
report numerical solver tolerances and do not call the numerical point an exact optimum.

Run only this analytic comparison. No synthetic sweep, data evaluation, or algorithm selection is
authorized by this registration.

## Numerical result and interpretation

The LP activates with probability one and uses the full cap. Its numerical optimum within this
fixed-cohort, count-state class spends null risk `0.05` for each delay. Net excesses are `10.21139`,
`10.38263`, and `11.00358` for delays 1, 5, and 20; noisy-information net lower bounds are
`8.32892`, `8.55787`, and `9.41644`. Thus the class-specific gaps are `1.88247`, `1.82476`, and
`1.58714`. LP flow residuals and inequality violations are zero at solver precision; an
independent null forward recursion matches the LP risk, and the alternative forward cost matches
the LP objective. Ruff and `git diff --check` pass.

These values do not show that the lower bound is loose for the unrestricted learner: a full
adaptive-query policy may do better than this fixed cohort. They do show that the repeated
one-label alpha-spending rule is not the strongest known-onset sequential test in this restricted
class. The result does not identify a novel method or validate the bound as tight. Next, either
derive a matching lower bound for the fixed-cohort stopping problem or compare a standard
unknown-onset sequential test with adaptive query scheduling under the same hard-cap contract;
do not advance to efficacy or real-data evaluation.
