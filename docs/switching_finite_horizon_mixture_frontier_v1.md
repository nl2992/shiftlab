# Finite-horizon onset-mixture tuning for the safe switching baseline

**Date:** 2026-10-29. **Status:** comparator refinement; not a new switching method.

This note tightens the all-onset detector comparator in
[`switching_uniform_calendar_e_detector_regret_v1.md`](switching_uniform_calendar_e_detector_regret_v1.md).
The original rule uses the infinite-horizon weights `w_j=1/[j(j+1)]` even though both the
calendar horizon and the number of query rights are known. A finite-horizon, loss-aware mixture
can improve its worst-onset *bound*. It does not adapt acquisition and does not pass G1.

## Contract and mixture

Use the same persistent Bernoulli alternative as the cited baseline: `Y_t~Ber(1/2+epsilon)` from
an unknown onset `nu` to `T`, and the global null satisfies
`P(Y_s=1 | full event-time past, query at s)<=1/2`. Query on
`q_j=ceil(j*T/B)`, `j=1,...,B`, with fixed release delay `d`; let
`L=ceil(T/B)` and `q_0=0`. At query index `n`, maintain

```text
E_n = sum_{j=1}^n w_j product_{i=j}^n [1 + 2*epsilon*(2*Y_{q_i}-1)]
      + sum_{j=n+1}^B w_j,
```

where `w_j>=0` and `sum_j w_j=1`. Each factor has conditional expectation at most one under the
full-history null. The deferred-start terms make `E_0=1` and preserve the supermartingale property.
Thus the first threshold crossing `E_n>=1/alpha` has null probability at most `alpha` by Ville's
inequality. Fixed ordered release delay preserves the query-index filtration argument in the
baseline proof.

For an onset `nu`, let `s(nu)=min{j:q_j>=nu}`. The component starting at `s=s(nu)` has weight
`w_s`. Under the alternative its log increments have mean

```text
kappa = kl_Ber(1/2+epsilon || 1/2)
```

and are bounded above by `a=log(1+2*epsilon)`. Its crossing of `log(1/(alpha*w_s))` forces the
mixture across `1/alpha`. Wald's stopped-sum argument therefore gives the calendar-time gross
regret bound

```text
R(nu;w) <= 2*epsilon * min{ T-nu+1,
                             d-1 + L*[log(1/(alpha*w_s))+a]/kappa }.
```

The query fee adds at most `cB`, as in the original baseline. For worst-case onset within query
cell `s`, the earliest onset is `q_(s-1)+1`, so define `H_s=T-q_(s-1)`. The maximum of the
displayed bound over all calendar cells is `2*epsilon*r(w)`, where

```text
r(w) = max_s min{ H_s,
                   d-1 + L*[log(1/(alpha*w_s))+a]/kappa }.
```

## Optimal mixture for this bound

For a proposed regret horizon `r`, a cell with `H_s<=r` is already covered by the trivial
remaining-horizon cap. Every other cell requires

```text
w_s >= g(r) = exp(a - kappa*(r-d+1)/L) / alpha.
```

Consequently a target `r` is feasible for this family of mixture bounds exactly when

```text
N(r) * g(r) <= 1,       N(r) = |{s : H_s > r}|.
```

The infimum feasible `r` is found by one-dimensional bisection. Assign `g(r)` to every active
cell; the remaining mass may be placed on any active cell. Starts with `H_s<=r` need no mass to
achieve this regret bound. The script reserves total mass `1e-12` across such inactive starts, so
its numerical feasibility check uses `N(r)g(r)<=1-1e-12`; this keeps every weight positive and
changes the displayed results by less than the reported precision. This is optimal only for the
stated worst-onset upper bound within the all-onset mixture family; it is not a minimax result over
all safe tests or query policies.

The calculation is implemented in
[`../scripts/optimize_switching_onset_mixture.py`](../scripts/optimize_switching_onset_mixture.py).
For `T=120, B=20, alpha=.05, d=1, epsilon=.49`, its worst-onset bound is `r=57.2246` rounds,
versus `62.8544` for uniform start weights and `74.9169` for the original infinite-horizon weights.
At `epsilon=.10`, all three bounds cap at the 120-round horizon: the registered moderate-signal
case still has no useful uniform-calendar guarantee. Query fees remain `20c` in every case.

## Research consequence

This is a stronger, properly horizon-aware comparator for future matched comparisons. It is a
reweighting of a standard e-detector, with no acquisition or deployment coupling. The high-signal
numerical improvement is a bound refinement only; the registered `epsilon=.10` cell remains
vacuous. G1 stays open, G2-G5 remain held, and no efficacy experiment or real-data analysis is
authorized by this result. Historical evidence from a positive segment still cannot certify
current benefit after an unobserved reversal; this theorem covers a single persistent positive
segment only.
