# Independent adversarial audit: B=4 proof

**Verdict: ACCEPT** for the exact B=4 theorem in `local-proof.md`, after adding the detailed derivations requested below. No counterexample or mathematical flaw was found.

## Accepted statement

For the symmetric stationary HMM with latent correlation `-r`, emissions `(1-a)/2,(1+a)/2`, `a=sqrt(g)`, `B=4`, `d=1`, `c=k=0`, `alpha=1/10`, `r in (1/200,1/100)`, and `g in (2/5,1/2)`, the proof gives
`rho_Gamma(T) >= 13/84 > 0.15` for every integer `T>=16`.
It covers arbitrary deterministic adaptive plans and randomized mixtures.

## Reviewed derivations

The history density is `D_m=E product_i(1+a s_i X_{u_i})`. Odd stationary spin moments vanish. For four ordered times,
`E[X_vX_wX_xX_y]=rho^(w-v+y-x)`, so `D_4` has precisely one fourth-order term
`g^2 s_1s_2s_3s_4 rho^(u_2-u_1+u_4-u_3)` in addition to pair terms. No density terms are omitted.

The posterior action gain at `n>=u_m+1` is
`w_n = [g sum_i s_i rho^(n-u_i) + g^2 sum_{i<j<k}s_i s_j s_k rho^(u_j-u_i+n-u_k)]/D_m`.
For m=4, the four triple subsets have minimum powers `r^3,r^2,r^3,r^2`; their absolute tail is at most `g^2(2r^2+2r^3)/(1-r)`. The earlier singleton tail is at most `g(r^2+r^3+r^4)/(1-r)`. Together with the stated `D_*` bound, this verifies all E_m envelopes, including the denominator correction.

The null mixture `Q=(IID+nu_1+...+nu_4)/5` is admissible and has
`Q(h)=2^-m(5-m+2z)/5`; adaptive timing contributes no probability factor along a deterministic-plan prefix. The first-promotion-leaf reduction bounds causal gain by `R_Q max_h(P_A(h)V(h)/Q(h))`, and IID gain by `R_IID max_h D_m V(h)`.

The adaptive continuation follows from the one-query posterior identity and finite-horizon potential `F_t(x)`. Backward induction on time simultaneously over remaining query budgets gives `W_{t,b}(x)<=F_t(x)+b v1`; this covers adaptive query timing and rollback/re-promotion. With `d=1`, prior-step queries have released by promotion; a simultaneous query is part of the remaining `4-m` labels.

The exact audit checked all 31 binary histories at the endpoint. It returned `D_*=1969749/2000000`, normalized `E_2=168170000/6565173417`, `E_3=18410000/596833947`, `E_4=710570200/19695520251`, maximum causal coefficient `62875/29997=2.096042937627096`, and maximum IID coefficient `25150/9999=2.5152515251525154`. Both maxima occur at m=1,label zero. The analytic normalized bounds are increasing in r,g, so the endpoint bounds hold on the full open rectangle.

The IID witness queries at `1,5,8,11`, promotes at `2` only if the first label is zero, and otherwise never promotes. Its risk and branch probability are both `1/2`. Its normalized gain/risk is at least `5/2-(r^4+2r^3)/2>2.49`; every retained first-lag reward is available by T=12. Mixing with never-promote at weight `2 alpha` gives the stated `Gamma>=0.39 alpha gr` and `rho_Gamma>=13/84`.

## Independent checks and assurance

The reviewer reports 3,510 exact rational checks of transcript densities, posterior formulas, and infinite tails across histories up to four labels, query gaps 1–4, and three parameter pairs. The adaptive Bellman bound was checked at 175 starting states over 17,204 recursive states; witness prior ratios `(r^4,r^3,r^3)` were independently recovered. These computations support the algebra; the analytic inequalities establish the continuum result.

This is a fresh adversarial review by a separate agent in the same model family; it is not external or cross-family review. Acceptance covers only the stated B=4 model and parameter region. It makes no general-budget, other-delay, positive-cost, novelty, or empirical claim.
