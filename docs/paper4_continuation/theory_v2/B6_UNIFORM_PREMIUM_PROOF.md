# B=6 uniform-premium proof

Status: `PROVED` for the exact scope below; independently adversarially reviewed. Review record: [`independent-review.md`](../../../prompts/26111216-4/independent-review.md). Exact arithmetic: [`b6_constant_audit.py`](../../../prompts/26111216-4/b6_constant_audit.py) and [`b6_constant_audit.txt`](../../../prompts/26111216-4/b6_constant_audit.txt).

## Candidate theorem

For `B=6`, `d=1`, `c=k=0`, `alpha=1/10`, `r in (1/200,1/100)`, `g in (2/5,1/2)`, the theorem states
`rho_Gamma(T)>=0.10` for every `T>=20`.

## General moment construction

Let `rho=-r`. For an ordered even subset `J=(j_1<...<j_{2q})`, the HMM spin moment is
`rho^sum_l(u_(j_(2l))-u_(j_(2l-1)))`; odd spin moments vanish. Thus the alternative prefix density factor
`D_m=E product_i(1+a s_i X_(u_i))` is the even-subset expansion. Its coefficientwise absolute upper envelope is

`delta_m=sum_{even J nonempty} g^(|J|/2) r^sum_l(j_(2l)-j_(2l-1))`,

including the two-, four-, and six-spin terms when available. Use `Q=(IID+nu_1+...+nu_6)/7`, where `nu_j`
forces the jth *queried* label to zero and sets every other queried-label probability to one half. Query index is
determined by public history and the learner's current query action, so each `nu_j` is an adapted causal-null
strategy. For a prefix with m labels and z zeros, `Q(h)=2^-m(7-m+2z)/7`, so the
causal likelihood ratio is `7D_m/(7-m+2z)`.

## Posterior envelope

After the latest release, expand the posterior action gain as a sum over odd subsets of the observed labels:

`w_n = [sum_{odd J, |J|<=5} g^((|J|+1)/2) s_J M_(J,n)]/D_m`,

where `M_(J,n)` is the ordered even-spin moment of the labels in `J` together with `X_n`. For a subset
`J=(j_1<...<j_(2q-1))`, its smallest possible exponent over increasing integer query times and `n>=u_m+1` is
`q(J)=sum_l(j_(2l)-j_(2l-1))+m-j_last+1`. Summing each geometric tail defines `posterior_error(m)` in
`b6_constant_audit.py`; every actual exponent is at least this value. The latest singleton positive tail is
`G_0=gr/(1-r^2)` or `G_1=gr^2/(1-r^2)`.
With `delta=delta_6`, `D_*=1-delta`, and `E_m=(G_0 delta+posterior_error(m))/D_*`,
`V_0(h)<=G_(y_m)+E_m` for m=2..6.

For adaptive continuation, the posterior mean query update is `psi_s(x)=(x+as)/(1+asx)` with sign probability
`(1+asx)/2`. It satisfies `E psi=x`, `E|psi|=max(|x|,a)`, and
`E[(a rho^j psi)^+]-(a rho^j x)^+=gr^j(1-|x|/a)^+/2`. Define
`F_t(x)=sum_(j=0)^(T-t)(a rho^j x)^+`. A query released at t+1 increases expected future potential by at most
`v1=gr/[2(1-r)]`; backward induction on remaining time, simultaneously for all budgets b, gives
`W_(t,b)(x)<=F_t(x)+b v1`, covering arbitrary adaptive schedules and rollback/re-promotion. At d=1 earlier-step
queries have released; same-step pending queries count against the remaining `6-m` labels. Hence use
`V<=6v1` for m=0, `G_y+5v1` for m=1, and `G_y+E_m+(6-m)v1` for m=2..6.

## Exact rational constants

The script `b6_constant_audit.py` enumerates all 127 histories at `(r,g)=(1/100,1/2)` and uses
`D_m<=1+delta_m`. It returns

- `D_*=19492937149/20000000000`;
- maximum causal coefficient `41125/13332 = 3.084683468 < 3.10`;
- maximum IID coefficient `11750/3333 = 3.525352535 < 3.54`.

Both maxima are m=1,label zero. All terms in `delta_m`, normalized tails, `G_y/(gr)`, and `v1/(gr)` have
nonnegative coefficients and increase in r,g; the denominator remains positive. Thus the endpoint enumeration
extends over the entire open rectangle.

For each deterministic plan, its first-promotion histories are disjoint leaves. Pre-promotion gain is zero and
each continuation is bounded by `V(h)`, hence
`gain(pi)<=sum_h P_A(h)V(h)<=R_Q(pi)max_h P_A(h)V(h)/Q(h)`; IID gives the analogous maximum `D_mV(h)`.
Every `nu_j` is causal and `R_Q<=alpha`. For randomized plans, condition on the learner's private random seed;
the same fixed null mixture gives the bound on every resulting deterministic tree, then averaging over seeds
preserves it. Thus
`VOI_causal<=3.10 alpha gr` and `VOI_IID<=3.54 alpha gr` uniformly in T.

## IID witness

Query at 1; promote at 2 iff the first label is zero; otherwise never promote. On the promotion branch, query at
5,8,11,14,17 and take optimal actions. Let `zeta_T` be the conditional branch gain (equivalently gain divided
by IID risk 1/2). The prior magnitude at time5 is `a r^4`; later query priors are at most `r^3<a`, and their
expected absolute magnitudes divided by `a` are `r^3`. The information increments telescope; retaining only the
first future lag from each query gives

`zeta_T/(gr)>=7/2-(r^4+4r^3)/2>3.49`, for `T>=20`.

Mixing with never-promote at weight `2alpha` yields `VOI_IID>=3.49 alpha gr`; so
`Gamma>=0.39 alpha gr` and `rho_Gamma>=0.39/3.54=13/118>0.10`.

## Independent review disposition

The fresh adversarial reviewer accepted the mathematics conditional on the stated HMM, one-query-per-step,
release-before-action, and causal-null assumptions. It independently confirmed the six-spin density term, subset
tails, null-mixture masses, Bellman/leaf argument, exact rational maxima, and witness. The proof note includes the
requested clarifications on `nu_j`, random seeds, and exponent lower bounds. This is same-family mathematical review,
not formal or external validation. No B>=7 or growing-budget theorem follows.
