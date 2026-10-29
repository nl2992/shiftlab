# Uniform query calendar plus all-onset e-detector: finite regret bound

**Date:** 2026-10-29. **Status:** comparator theorem under a narrow one-change model; no novelty claim.

## Contract

There are two frozen policies with losses `(Y_t,1-Y_t)`, where `Y_t` is binary and a queried
common outcome reveals both losses. Policy 0 is the incumbent. Set `Z_t=2Y_t-1`, so positive
mean favors policy 1. The horizon is `T`, the pathwise query cap is `B` (`1<=B<=T`), each
query costs `c>=0`, each switch costs `k>=0`, and a query at event `s` is released at the start
of event `s+d` for fixed `d>=1`. Decisions use only labels released by then. Set the risk level
`0<alpha<1`.

Under the global conditional null, `P(Y_s=1 | full event-time past, query at s)<=1/2` at every
queried event. Under alternative `P_nu`, labels are independent, `Y_s~Ber(1/2)` before an
unknown onset `nu` and `Y_s~Ber(1/2+epsilon)` from `nu` through `T`, for known
`0<epsilon<1/2`. The comparator stays at 0 until `nu`, then switches once to 1, paying `k`.
This is a persistent one-change instance; it does not model rollback or repeated changes.

## Rule

Let `q_j=ceil(j*T/B)`, `j=1,...,B`; these are distinct query times, so the pathwise cap is met
exactly. Let `L=ceil(T/B)`, the largest calendar gap. At the release of the `n`th queried label,
maintain the all-onset mixture

```text
E_n = sum_{j=1}^n w_j product_{i=j}^n [1 + 2*epsilon*(2*Y_{q_i}-1)]
      + sum_{j=n+1}^infinity w_j,
w_j = 1/[j(j+1)].
```

Promote at the first release with `E_n>=1/alpha`, and never switch again. Each fixed-start product
is a nonnegative supermartingale under the causal conditional null; the mixture is therefore one
as well. Fixed ordered delay means the release history at the `n`th label contains no queried
outcome generated after `q_n`, so the same argument applies in the learner's release filtration.
Ville's inequality gives `P_null(any promotion)<=alpha`.

## Bound

Write

```text
kappa = kl_Ber(1/2+epsilon || 1/2),
a = log(1+2*epsilon),
s_nu = min{j : q_j>=nu},
h_nu = log(1/(alpha*w_{s_nu})) = log(s_nu*(s_nu+1)/alpha),
H_nu = T-nu+1.
```

Then the alternative's expected net-cost excess over the one-switch comparator satisfies

```text
E_nu[cost(learner)-cost(comparator)]
    <= c*B + 2*epsilon*min{H_nu, d-1 + L*(h_nu+a)/kappa}.
```

**Proof.** Consider the mixture component starting at the first scheduled query `q_{s_nu}` at or
after `nu`. After that query, its log increments are IID with mean `kappa` under `P_nu`, and each
increment is at most `a`. The component's crossing of `h_nu` forces the full mixture to cross
`1/alpha`, so the mixture crossing time is no later. If `tau` is the component's number of
post-onset labels to cross, Wald's identity at `tau wedge m` gives
`kappa*E[tau wedge m]=E[S_(tau wedge m)]<=h_nu+a`; taking `m` to infinity yields
`E[tau]<=(h_nu+a)/kappa`. The first post-onset query is at most `L-1` rounds after `nu`, each
subsequent query gap is at most `L`, and release costs another `d` rounds. Thus expected time
using the incumbent after onset is at most `d-1+L*(h_nu+a)/kappa`, capped by `H_nu`.
Promoting before `nu` incurs no decision-loss difference because both policies have mean loss
`1/2` there, and the learner pays at most the comparator's single switch charge. Query charges add
at most `cB`. This proves the bound. QED.

## What this says about the research gate

This is a valid, explicit comparator for a persistent Bernoulli gain with known `epsilon`. It
does not adapt query timing to evidence, and its `log(s_nu^2/alpha)` threshold makes the bound
vacuous in many moderate-signal, finite-budget cells. For the already registered
`T=120,B=20,nu=61,epsilon=.1,alpha=.05,d=1` cell, `L=6`, `s_nu=11`, and the expected-query
bound is about `400.33` although at most 10 scheduled labels remain after onset. The resulting
gross-regret upper bound is the trivial `12`, while the existing information lower bound is
`8.429`. Thus this analysis supplies no useful performance guarantee in that cell. It does not
resolve the gap to the
noisy-information lower bound in
[`switching_noisy_information_lower_bound_v1.md`](switching_noisy_information_lower_bound_v1.md)
or the full causal-game oracle. Unknown effect size, reverse-regime monitoring and repeated
switches are outside the theorem.

The construction itself combines a deterministic budget-feasible schedule with a standard
all-onset e-detector. Neither ingredient is claimed as new. Its purpose is to supply a clean
regret reference before evaluating a candidate acquisition rule. Any stronger baseline may spend
queries adaptively, but must retain the same pathwise cap, fixed-release chronology and causal-null
family. The result does not allow historical promotion wealth to certify current value after a
reversal; that claim still requires post-change evidence or an explicit persistence model.
