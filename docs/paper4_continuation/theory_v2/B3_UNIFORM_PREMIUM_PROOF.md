# B=3 uniform-premium proof

Status: `PROVED` for the exact scope below; independently adversarially reviewed. Review record: [`prompts/26111216-1/independent-review.md`](../../../prompts/26111216-1/independent-review.md). Exact arithmetic: [`constant_audit.py`](../../../prompts/26111216-1/constant_audit.py) and [`constant_audit.txt`](../../../prompts/26111216-1/constant_audit.txt).

## Target-first reduction

To prove `rho_Gamma>=0.18`, it suffices to prove the following three explicit bounds for every `T>=16` in the target rectangle:

1. `VOI_causal <= 1.61 alpha g r`;
2. `VOI_IID <= 2.02 alpha g r`;
3. a pure plan with IID risk at least `alpha` has gain/risk ratio `zeta >= 1.99 g r`; mixing it with never-promote makes it feasible at risk `alpha`.

Indeed, scaling that plan to risk `alpha` gives `VOI_IID>=alpha*zeta`, so `Gamma>=alpha(zeta-1.61gr)>=0.38 alpha gr`; dividing by the IID upper bound gives `rho_Gamma>=0.38/2.02>0.18`.

## Candidate dual certificate

Let `Q=(IID+nu_1+nu_2+nu_3)/4`, with `nu_j` forcing the j-th queried label to zero. Each component is an allowed causal null, so a causal-feasible plan has `R_Q<=alpha`. For a history `h` with `m` released labels and `z` zeros,

`Q(h)=2^(-m-2)(4-m+2z)`.

Under the alternative, for query times `u_1<...<u_m`,

`P_A(h)=2^-m D_m`, `D_m=1+g sum_{i<j}s_i s_j(-r)^(u_j-u_i)`.

Therefore the history likelihood ratio is

`P_A(h)/Q(h)=4 D_m/(4-m+2z)`.

The adaptive schedule does not alter this formula along a fixed realized path: each `u_i` is predictable from earlier signs and becomes fixed when that path is specified. More explicitly, a deterministic plan induces a tree whose leaves are its first-promotion histories (or a no-promotion leaf). Under `nu_j`, the probability of a fixed length-`m` history is `2^(-(m-1))` if `j<=m` and its jth sign is zero, and zero if `j<=m` and that sign is one; if `j>m`, it is `2^-m`. Averaging these with IID gives the displayed `Q(h)`. Summing over first-promotion leaves therefore gives exactly the plan's first-promotion risk under `Q`, and no factor for adaptive query times is missing. For `m<=3`, `|D_m-1|<=g(2r+r^2)`.

The four components of `Q` are valid causal nulls: `nu_j` sets conditional label probability to zero at the jth query and to one half at all other query indices. The query index is determined from the public past and current query action, so this is an adapted causal strategy in the stated null class. Consequently a causally feasible plan has `R_Q<=alpha`.

## Candidate post-promotion value envelope

For a query at time `u` with prior spin mean `x`, an observation with sign `xi` has probability `(1+a xi x)/2` and posterior spin mean `(x+a xi)/(1+a xi x)`. At a later time `u+j`, the expected gain increment in the convex action value `(a E[X_{u+j}|data])^+` is

`g r^j/2 * (1-|x|/a)^+ <= g r^j/2`.

Summing for `j>=1` gives at most `v1=gr/(2(1-r))` value per additional label. For adaptive query times, use the finite-horizon no-query potential `F_t(x)=sum_{j=0}^{T-t}(a(-r)^j x)^+`, where `x` is the current posterior spin mean. A query released one step later increases conditional expected potential by at most `v1`; backward induction on remaining time, simultaneously for all remaining query budgets, gives continuation value at most `F_t(x)+b v1`. Conditioning at each predictable query node handles random query times. The independent audit accepted this Bellman-envelope argument.

For a promotion history with `m>=1`, let `y_m` be its latest released label. The no-additional-label continuation should satisfy

`V_0(h) <= G_{y_m}+E`,

where `G_0=gr/(1-r^2)`, `G_1=gr^2/(1-r^2)`, and

`D_*=1-g(2r+r^2)`,
`E=[G_0*g(2r+r^2)+g(r^2+r^3)/(1-r)+g^2*r^2/(1-r)]/D_*`.

For `n>=u_m+1`, direct expansion of the emission likelihood gives

`w_n = g/D_m * [sum_i s_i(-r)^(n-u_i) + 1{m=3}g s_1s_2s_3(-r)^(u_2-u_1+n-u_3)]`.

Odd stationary spin moments vanish, and the four-spin moment is `(-r)^(u_2-u_1+n-u_3)`. The latest-label summand has positive-part tail exactly `G_{y_m}`. For `m=3`, older single-label terms have total absolute tail at most `g(r^2+r^3)/(1-r)` and the triple term at most `g^2r^2/(1-r)`; for `m=2`, the older-term tail is at most `gr^2/(1-r)`. Since `D_m>=D_*` and `G_{y_m}/D_m<=G_{y_m}+G_0g(2r+r^2)/D_*`, these bounds give the stated `E`. The independent audit verified the expansion and bounds for arbitrary integer query gaps. For `m=1`, the sharper exact bound is `V_0(h)<=G_{y_1}`. For `m=0`, the no-label baseline is zero. Including remaining labels yields

`V(h)<=3v1` if `m=0`,
`V(h)<=G_{y_1}+2v1` if `m=1`,
`V(h)<=G_{y_m}+E+(3-m)v1` if `m=2,3`.

The remaining-label count is at most `3-m`. At `d=1`, queries made at strictly earlier steps release before the current action; any same-step query belongs to the remaining-label continuation. This matches the model's release-before-action convention.

To obtain the continuation envelope rigorously, between queries the posterior spin mean evolves as `x -> -r x`. The no-more-query value satisfies the backward recursion represented by `F_t(x)`. If a query is made at step `t`, its label is released at `t+1`; conditioning on the current posterior `x`, the sum over all future action times of the expected increase in positive-part value is

`sum_{j=1}^{T-t} (g r^j/2)(1-|x|/a)^+ <= v1`.

Backward induction on `(remaining time, remaining query budget)` now gives `W_{t,b}(x)<=F_t(x)+b v1`: the no-query branch propagates `x` and uses the induction hypothesis with budget `b`; the query branch has one such information increment bounded by `v1` and then uses the induction hypothesis with budget `b-1`. A policy that waits for a label or chooses its next query time from observed labels is a mixture of these conditioned branches, so the same inequality applies at every predictable node. After promotion, there are at most `3-m` labels left, giving the three displayed cases. With zero switching and query costs, actions do not affect future observations, and the maximal current-stage gain is the positive part of the current posterior action value. The Bellman value `W_{t,b}` therefore allows every rollback and re-promotion schedule.

Combining the leafwise continuation bound with the likelihood ratios proves

`VOI_causal <= alpha * max_h [(P_A(h)/Q(h)) V(h)]`,

and the same argument under the single IID row proves

`VOI_IID <= alpha * max_h [D_m V(h)]`.

These inequalities first hold for deterministic plans; randomized plans are mixtures and preserve them by linearity.

## Numerical constants implied by the candidate bounds

On `r<=1/100`, `g<=1/2`:

- `D_*>=0.98995`;
- `E/(gr)<0.026`;
- `G_0/(gr)<1.00011`, `G_1/(gr)<0.01001`, and `v1/(gr)<0.50506`.
- Enumerating the possible `(m,z,y_m)` combinations with the path likelihood ratios gives a candidate causal coefficient below `1.61` and IID coefficient below `2.02`.

The exact rational audit is reproducible with `python prompts/26111216-1/constant_audit.py`; output is saved in `constant_audit.txt`. For uniformity, normalized `G_y`, `v1`, and `E` are increasing in `r,g`; bound `D_m` separately by `1`, `1`, `1+gr`, and `1+g(2r+r^2)` for `m=0,1,2,3`. Exact enumeration of all binary histories then gives whole-rectangle bounds `5360/3333 < 1.61` and `6700/3333 < 2.02`. Both maxima occur for `m=1,y=0` at the closed corner, so the open rectangle obeys the same strict bounds.

## IID witness

Query at time 1; promote at time 2 only if `Y_1=0`; after promotion query at times 5 and 8, and act optimally after each release. The IID risk is `1/2`. Conditional on `Y_1=0`, the prior at time 5 has magnitude `a r^4`; after the time-5 observation, the expected absolute posterior spin propagated to time 8 is `a r^3`. The one-query identity, applied successively, yields at least `gr` from the first label and at least `(gr/2)(1-r^4)` and `(gr/2)(1-r^3)` from the first future lag of the two later queries. Hence for every `T>=16`, `zeta_T >= gr[2-(r^4+r^3)/2] > 1.99gr`. Mixing this plan with never-promote to risk `alpha` proves `VOI_IID>=1.99 alpha gr`.

## Current result

Independent adversarial review accepted this proof for the stated target only. It found no counterexample or fatal gap and confirmed `T0=16`, `c_star=0.18`. No general-budget, other-delay, positive-cost, novelty, or empirical theorem is claimed.
