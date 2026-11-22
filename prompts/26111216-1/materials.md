# Materials and notation

- `r=2t-1 in (0,1)` and the latent spin correlation is `rho=-r` because `t01=t10=(1+r)/2`.
- `a=1-2e=sqrt(g)`, `g=a^2`; an observed sign is `s_i=2y_i-1`.
- The observation spin satisfies `E[S_i|X_{u_i}]=a X_{u_i}`.
- For up to three labels at strictly increasing query times `u_i`, with `m<=3`, the path probability under the alternative is
  `P_A(s_1,...,s_m)=2^-m D_m`, where
  `D_m=1+g*sum_{i<j} s_i*s_j*(-r)^(u_j-u_i)`.
  This follows from the stationary spin moments: zero odd moments and pair moment `(-r)^gap`.
- The state posterior after a transcript determines the action value `w_s=a E[X_s|transcript]`. With zero query and switch costs, the post-promotion value is the sum of positive parts `sum_s (w_s)^+`.
- A causal null may set the outcome probability to zero at a predictable query index and to one half at other query nodes. The index is observable from the public query history.
- The first-promotion reduction M3 and B=2 theorem M4 are in source 01. Source 02 records that the earlier B=3 explicit-plan comparison did not upper-bound optimal branch slopes.

## Candidate new route

Use four nulls: IID(1/2), plus `nu_j` for `j=1,2,3`, where `nu_j` forces the j-th queried label to zero and makes other labels fair. Their equal mixture `Q` is a valid risk constraint. For a pre-promotion history of `m` released labels containing `z` zeros, its mass is

`Q(h)=2^(-m-2) * (4-m+2z)`.

The goal is a pathwise certificate comparing the alternative probability times the maximum post-promotion continuation value against `Q(h)`. A separate IID-row comparison bounds the IID denominator. No pathwise certificate has yet been accepted.
