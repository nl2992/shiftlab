# B=5 uniform-premium proof attempt

Status: `PROVED` for the exact scope below; independently adversarially reviewed.

## Theorem and reductions

For `B=5`, `d=1`, `c=k=0`, `alpha=1/10`, `r in (1/200,1/100)`, `g in (2/5,1/2)`, the theorem states
`rho_Gamma(T)>=0.13` for every `T>=16`.

Use `Q=(IID+nu_1+...+nu_5)/6`, with `nu_j` forcing query j to zero. For a prefix of m released labels with z zeros,
`Q(h)=2^-m(6-m+2z)/6`. Thus the causal pathwise ratio is `6D_m/(6-m+2z)`, and every causal-feasible plan
has `R_Q<=alpha`.

## HMM moments and posterior expansion

For ordered spin times `v_1<...<v_{2q}`,
`E[X_{v_1}...X_{v_{2q}}]=rho^((v2-v1)+...+(v_(2q)-v_(2q-1)))`, `rho=-r`; odd moments vanish. This follows by writing the chain as a fair initial spin times independent transition signs. Hence
`D_m=E[product_i(1+a s_i X_{u_i})]` is the sum over every even subset J of `[m]` of
`g^(|J|/2) product_{i in J}s_i` times its paired-gap moment. The exact absolute upper envelope is

`delta_m=sum_{even J nonempty} g^(|J|/2) r^(sum_{pairs}(j_(2l)-j_(2l-1)))` is a coefficientwise absolute upper envelope.

At m=0..5, the endpoint values produced by the script are
`[0, 0, 1/200, 201/20000, 30251/2000000, 4045301/200000000]`.
Set `delta=delta_5=4045301/200000000` and `D_*=1-delta=195954699/200000000`.

For n>=u_m+1, the exact posterior action gain is

`w_n = [g sum_{|J|=1} s_J rho^(n-u_J) + g^2 sum_{|J|=3} s_J rho^(u_(j2)-u_(j1)+n-u_(j3)) + 1{m=5}g^3 s_1...s_5 rho^(u2-u1+u4-u3+n-u5)]/D_m`.

The g^3 term is the six-spin moment from all five emissions and X_n; its minimum exponent is 3. For each odd
subset J of size 3 or 5, the exact minimum power in its tail is
`q(J)=sum_l(j_(2l)-j_(2l-1)) + m-j_last+1`; summing the associated geometric tails gives the script's
`posterior_error(m)`. The older singleton tail is the same formula for singleton subsets except the latest label.
For m=5, the five four-spin subsets in `D_5` have minimum powers `r^2,r^3,r^2,r^3,r^2` for subsets
`1234,1235,1245,1345,2345`. The ten triple-subset tail minima, in order
`123,124,125,134,135,145,234,235,245,345`, are `4,3,2,4,3,4,3,2,3,2`; the five-emission term's minimum is 3.
The latest singleton's positive-part tail is `G_0=gr/(1-r^2)` or `G_1=gr^2/(1-r^2)`. Since `D_m>=D_*`,

`V_0(h) <= G_(y_m)+E_m`, `E_m=(G_0*delta+posterior_error(m))/D_*` for m=2..5.

Indeed, when `D_m>=1`, `G_y/D_m<=G_y`; otherwise `(1-D_m)/D_m<=delta/D_*`, so
`G_y/D_m<=G_y+G_0 delta/D_*`. Then apply `(L+R)^+<=L^++|R|` to the latest singleton `L` and the remaining
terms `R`.

For completeness, if the prior spin mean at a query is `x`, sign `S` has probability `(1+a S x)/2` and posterior
mean `psi_S(x)=(x+aS)/(1+aSx)`. Then `E psi_S=x`, `E|psi_S|=max(|x|,a)`, and for every future lag j>=1,
`E[(a rho^j psi_S)^+]-(a rho^j x)^+ = gr^j/2 (1-|x|/a)^+`. Let
`F_t(x)=sum_{j=0}^{T-t}(a rho^j x)^+`. A query at t releases at t+1 and increases expected future no-query
potential by at most `v1=gr/[2(1-r)]`. Backward induction on remaining time, simultaneously for every remaining
query budget b, gives `W_{t,b}(x)<=F_t(x)+b v1`: the no-query branch keeps b, the query branch spends one and
adds at most v1. This conditions at each predictable adaptive query node. Actions do not affect observations, so
the Bellman value includes every rollback/re-promotion schedule. At d=1 all earlier-step labels have released;
a same-step pending query counts among the remaining `5-m` queries. Therefore the continuation bounds are
`V<=5v1` for m=0, `G_y+4v1` for m=1, and `G_y+E_m+(5-m)v1` for m=2..5.

For a deterministic learner, first-promotion leaves h are disjoint. Pre-promotion gain is zero and the gain on h
is at most `V(h)`, so `gain(pi)<=sum_h P_A(h)V(h) <= R_Q(pi) max_h P_A(h)V(h)/Q(h)`. Under IID the analogous
bound is `R_IID(pi) max_h D_mV(h)`. Each `nu_j` is causal because the query index is public and its conditional
probabilities are zero or one half; thus causal feasibility gives `R_Q<=alpha`. The inequalities extend to
randomized learners by linearity against the fixed null mixture.

## Exact endpoint certificate

`python prompts/26111216-3/b5_constant_audit.py` exactly enumerates every binary history, using `D_m<=1+delta_m`.
At `(r,g)=(1/100,1/2)` it gives

- `E_2/(gr)=1837970000/59374273797`;
- `E_3/(gr)=117670000/3249338367`;
- `E_4/(gr)=81259030000/1959351035301`;
- `E_5/(gr)=308466600/6597141533`;
- maximum causal coefficient `60400/23331 = 2.588830312 < 2.59`;
- maximum IID coefficient `30200/9999 = 3.020302031 < 3.03`.

Both maxima occur at m=1,label zero. The normalized error envelopes, `G_y/(gr)`, `v1/(gr)`, and `delta_m` have
positive-coefficient formulas increasing in r,g; `D_*` remains positive. Thus endpoint bounds are uniform on the
open rectangle. The first-promotion-leaf argument then gives `VOI_causal<=2.59 alpha gr` and
`VOI_IID<=3.03 alpha gr` for every horizon and every deterministic plan. Mixtures follow by linearity against the
fixed nulls.

## IID witness

Query at 1; promote at 2 iff the first label is zero; otherwise never promote. On the promotion branch, query at
5,8,11,14 and act optimally. Let `zeta_T` be this plan's gain divided by its IID promotion risk; its risk is 1/2.
Conditional on the first label, the prior at time5 has magnitude
`a r^4`; at later query times the prior magnitude is at most `r^3<a`, and the expected absolute prior divided by
`a` at times 8,11,14 is `r^3`. The posterior information increments telescope. Keeping only the first future lag
from each query yields, for T>=16,

`zeta_T/(gr) >= 3-(r^4+3r^3)/2 > 2.99`.

Mixing this plan with never-promote at weight `2 alpha` gives `VOI_IID>=2.99 alpha gr`. Hence
`Gamma>=0.40 alpha gr` and `rho_Gamma>=0.40/3.03=40/303>0.13`.

## Independent review disposition

The independent adversarial reviewer accepted the subset expansions, tail exponents, dual masses, endpoint
constants, uniformity, and witness, conditional on the established one-query/Bellman lemma and release-before-action
semantics. The proof note now includes the requested Bellman induction, first-promotion leaf summation, same-step
pending-query convention, and explicit witness definition. This is same-family review, not external or cross-family
review. It establishes only the stated B=5 scope.
