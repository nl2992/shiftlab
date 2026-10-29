# Fixed-calendar paired queries with an unknown-onset e-detector

**Date:** 2026-10-28. **Status:** comparator derivation; no novelty claim and no experiment.

This closes one missing performance calculation for the contract-matched DAL-style baseline.
It studies a single persistent Bernoulli gain segment. It does not give recurrent-switch regret,
and its post-onset model is an explicit assumption rather than a forecast inferred from old
evidence.

## Protocol

Let `Y_t` be the queried indicator that policy 1 wins, with paired gain
`Z_t=2Y_t-1`. Under the global conditional null,
`P(Y_t=1 | F_(t-1), C_t, Q_t=1)<=1/2`. Set `L=ceil(T/B)` and query at
`q_i=1+(i-1)L<=T`; the number of requests is `N=ceil(T/L)<=B` pathwise. Every label has
fixed delay `d` and releases in query order.

For each possible onset `s`, let `E_(s,n)` be the likelihood-ratio product over the first `n`
queried outcomes initiated at or after `s`, comparing `Ber(1/2+epsilon)` to `Ber(1/2)`, and
set it to one before the first such outcome. Fix weights `w_s>0`, `sum_s w_s=1`, before data.
The mixture `M=sum_s w_s E_s` is an e-process under the conditional null. Promote once the
released-label mixture reaches `1/alpha`. Thus the probability of any promotion under the
global null is at most `alpha`, while a late persistent alternative can accumulate a *fresh*
onset-specific likelihood ratio. A pre-onset component's wealth is not interpreted as current
benefit.

## Detection bound after a persistent onset

Assume there is an onset `nu` and, for every queried event `t>=nu`,
`Y_t` are conditionally independent Bernoulli variables with parameter exactly
`1/2+epsilon`, where `0<epsilon<1/2`. Let

    K = kl(Ber(1/2+epsilon) || Ber(1/2))
      = (1/2+epsilon) log(1+2epsilon)
        +(1/2-epsilon) log(1-2epsilon),
    R = log((1+2epsilon)/(1-2epsilon)),
    A_nu = log(1/(alpha*w_nu)).

For any integer `n>=1`, if

    n*K - R*sqrt((n/2)*log(1/delta)) >= A_nu,

then promotion has occurred by the release of the `n`th queried post-onset label with probability
at least `1-delta`. Indeed, the onset-specific log likelihood ratio is a sum of `n` independent
increments in an interval of width `R`, has mean `nK`, and Hoeffding's inequality gives the
displayed lower-tail bound. Whenever that component reaches `1/(alpha*w_nu)`, the full mixture
is at least `1/alpha`.

The first post-onset query is no later than `L-1` rounds after `nu`; each further post-onset
query is `L` rounds later, and the final label is released after `d` rounds. Therefore the
calendar detection delay is at most `nL+d` with probability at least `1-delta` whenever the
condition holds and those requests/releases fit within the horizon. This bound exposes the
budget cost directly through `L`, and the unknown-onset penalty through `w_nu`.

For example, the fixed prior `w_s=6/(pi^2 s^2)` gives
`A_nu=log(pi^2 nu^2/(6 alpha))`; this is an onset-complexity penalty, not a tuned guarantee.
The condition is finite-sample and conservative. It may have no feasible `n` under a small
remaining budget or short segment, correctly indicating that this baseline offers no timely
detection guarantee there.

## Scope and comparison boundary

The e-process supplies a time-uniform false-promotion guarantee under the stated global
conditional null. The delay result instead assumes a persistent, specified Bernoulli alternative
after `nu`. It does not turn historical wealth into post-reversal evidence, guarantee a profitable
hold horizon, bound rollback loss after an abrupt reversal, or give dynamic regret. Under repeated
alternatives one must use fresh post-onset evidence for the decision about the current segment and
account separately for repeated null-risk events.

This derivation closes only the fixed-calendar e-detector's one-segment detection term. A full
economic regret bound still needs the comparator's exact action rule, query charges, switch
charges, false-promotion paths, and losses during every positive and negative segment. It is a
stronger baseline calculation, not an algorithmic contribution. In particular, it does not show
that adaptive acquisition improves on this baseline or on the exact finite causal planner.
G1 remains open; G2-G4 stay held.
