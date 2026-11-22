# B=4 uniform-premium proof attempt

Status: `PROVED` for the exact scope below; independently adversarially reviewed.

## Theorem

For `B=4`, `d=1`, `c=k=0`, `alpha=1/10`, `r in (1/200,1/100)`, and `g in (2/5,1/2)`, seek a uniform theorem
`rho_Gamma(T)>=0.15` for every `T>=16`.

## Dual null mixture and transcript density

Take `Q=(IID+nu_1+nu_2+nu_3+nu_4)/5`, where `nu_j` forces queried label `j` to zero and makes all others fair.
For a prefix h of m released labels with z zeros,

`Q(h)=2^-m(5-m+2z)/5`, hence `P_A(h)/Q(h)=5D_m/(5-m+2z)`.

The stationary spin moments are `E[X_vX_w]=rho^(w-v)` and, for ordered times, `E[X_vX_wX_xX_y]=rho^(w-v+y-x)`; odd moments vanish. The four-spin identity follows by writing the chain as its initial fair spin times independent transition signs. Expanding
`D_m=E[product_i (1+a s_i X_{u_i})]`
therefore gives for m<=3
`D_m=1+g sum_{i<j}s_i s_j(-r)^(u_j-u_i)`.
For m=4, there is one additional fourth-order term:

`D_4=1+g sum_{i<j}s_i s_j(-r)^(u_j-u_i)+g^2 s_1s_2s_3s_4(-r)^(u_2-u_1+u_4-u_3)`.

The formula follows by expanding four emission factors; all odd stationary spin moments vanish. For m=4,
`D_4>=1-delta`, `D_4<=1+delta`, with
`delta=g(3r+2r^2+r^3)+g^2r^2`; for m=2,3 use the sharper positive upper envelopes
`D_2<=1+gr` and `D_3<=1+g(2r+r^2)`.

## Continuation envelope

Use the one-query identity and Bellman potential from M6. Every remaining adaptive query adds at most
`v1=gr/[2(1-r)]` to the no-query action value.

For a history with m labels and latest sign y_m, the no-more-query value is at most `G_y+E_m`, where
`G_0=gr/(1-r^2)`, `G_1=gr^2/(1-r^2)`, and `E_m` bounds all older-label and interaction terms. Set
`D_*=1-delta`. Candidate absolute error tails are:

- m=2: `g r^2/(1-r)`;
- m=3: `[g(r^2+r^3)+g^2r^2]/(1-r)`;
- m=4: `[g(r^2+r^3+r^4)+g^2(2r^2+2r^3)]/(1-r)`.

Thus `E_m=[G_0 delta + error_m]/D_*`. With at most `4-m` remaining labels, use
`V<=4v1` for m=0, `G_y+3v1` for m=1, and `G_y+E_m+(4-m)v1` for m=2,3,4.

For every `n>=u_m+1`, expansion of the posterior action value gives
`w_n = [g sum_i s_i rho^(n-u_i) + g^2 sum_{i<j<k}s_i s_j s_k rho^(u_j-u_i+n-u_k)]/D_m`,
where the second sum is present only for m=3,4. Only the one- and three-emission terms survive after multiplying the likelihood by `X_n`; the three-emission terms use the four-spin moment above. For m=4, their four exponents and minimum powers (with `n>=u4+1`) are:

| Label subset | Exponent | Minimum power |
|---|---|---:|
| 123 | `u2-u1+n-u3` | `r^3` |
| 124 | `u2-u1+n-u4` | `r^2` |
| 134 | `u3-u1+n-u4` | `r^3` |
| 234 | `u3-u2+n-u4` | `r^2` |

Their total absolute tail is bounded by `g^2(2r^2+2r^3)/(1-r)`. Earlier single-emission terms contribute `g(r^2+r^3+r^4)/(1-r)`. The corresponding m=2,3 tails are in the table above. The pair terms satisfy `sum_{i<j}r^(u_j-u_i)<=3r+2r^2+r^3`; the four-spin term is at most `g²r²`. Thus `D_m>=D_*` for all m, with the listed sharper upper bounds for m=2,3.

For the denominator correction, if `D_m>=1`, then `G_y/D_m<=G_y`; if `D_m<1`, then `(1-D_m)/D_m<=delta/D_*`, so `G_y/D_m<=G_y+G_0 delta/D_*`. Combining this with `(L+R)^+<=L^++|R|` gives exactly `E_m=(G_0 delta+error_m)/D_*`.

## Candidate uniform constants

The exact endpoint audit (`b4_constant_audit.py`) uses `r=1/100`, `g=1/2`. It gives

- `D_*=1969749/2000000`;
- normalized error envelopes `E_2/(gr)=168170000/6565173417`,
  `E_3/(gr)=18410000/596833947`, `E_4/(gr)=710570200/19695520251`;
- causal coefficient max `62875/29997 = 2.096042938`;
- IID coefficient max `25150/9999 = 2.515251526`.

The maxima occur at m=1, y_1=0. The script uses the upper endpoint bounds `D_m<=1`, `1`, `1+gr`,
`1+g(2r+r^2)`, `1+delta` for m=0..4 and exact enumeration of every label string. All normalized envelope
terms are increasing in r,g and D_* remains positive; this should extend the bounds over the full rectangle.

The first-promotion leaves are disjoint. Before promotion the gain is zero, and with zero costs the gain on each
leaf is bounded by its post-promotion continuation `V(h)`. Thus for every deterministic plan
`gain(pi)<=sum_h P_A(h)V(h)<=R_Q(pi) max_h P_A(h)V(h)/Q(h)`; IID uses `D_m V(h)` in the same way. Each `nu_j`
is causal because query index is public and the conditional label probabilities are in `{0,1/2}`. A feasible
causal plan has `R_Q<=alpha`; a feasible IID plan has IID risk at most alpha. The bounds extend to randomized
plans by mixing deterministic plans against the fixed nulls. Consequently
`VOI_causal<=2.10 alpha gr` and `VOI_IID<=2.52 alpha gr`.

## IID witness

Query at 1; promote at 2 iff the first label is zero; otherwise never promote. On the promotion branch, query at
5,8,11 and use optimal actions. The IID risk and alternative branch probability are both 1/2, so its gain/risk
ratio is the conditional branch gain. The prior magnitude at time 5 is `a r^4`. At times 8 and 11 the prior
magnitude is pathwise at most `r^3<a`; the expected absolute prior magnitude divided by `a` is `r^3` at both
times, since `E|psi_S(x)|=a` whenever `|x|<a` and the posterior propagates three steps. The one-query increments
telescope through the adaptive-information potential, so their gains add without double counting. Taking only the
first future lag from each query gives

`zeta_T/(gr)>= 5/2-(r^4+2r^3)/2 > 2.49`, for every `T>=16`.

Mixing with never-promote using weight `2 alpha` gives `VOI_IID>=2.49 alpha gr`. Therefore
`Gamma>=0.39 alpha gr` and `rho_Gamma>=0.39/2.52=13/84>0.15`.

## Open audit obligations

1. Verify the m=4 posterior expansion and its four interaction exponents against the exact HMM filter.
2. Verify the continuation Bellman envelope when past labels and adaptive schedules are conditioned upon.
3. Verify every pathwise coefficient over the whole parameter rectangle and first-promotion leaf reduction.
4. Verify the IID witness's successive conditional marginal gains and finite-horizon timing.

The independent adversarial review accepts the mathematics for this exact B=4 scope. It independently checked 3,510
exact rational HMM transcript/posterior/tail cases, the Bellman envelope on 175 starting states (17,204 recursive
states), the witness prior ratios `(r^4,r^3,r^3)`, and the exact coefficient maxima. Review independence is
same-family, not external or cross-family. No general-budget or broader model claim follows.
