# Randomized-alpha-spending delayed switching baseline

2026-10-28. Register before execution. This is a deterministic analytic comparator calculation,
not a new algorithm, simulation, or efficacy experiment.

## Fixed contract cell

Use `T=120`, onset `nu=61`, query budget `B=20`, `epsilon=1/10`, global-null level
`alpha=1/20`, unit query cost `c=1/100`, deployment switch cost `k=1/10`, and fixed delays
`d in {1,5,20}`. Under the alternative, queried `Y_s` are independent Bernoulli(1/2) for
`s<nu` and Bernoulli(1/2+epsilon) for `s>=nu`; losses are `Y_s` and `1-Y_s`, so policy 1's
gross per-round gain is `2epsilon` after onset. Under every null, require the original full-history
conditional bound `P(Y_s=1 | full past, predictable query choice)<=1/2`.

## Policy

Fix `B` distinct nearly equally spaced query events over `1,...,T-d`, using
`q_j=ceil(j*(T-d)/B)`. Request all B labels regardless of prior results. At the release of each
queried label, if `Y=1` and policy 0 is still deployed, promote with a fresh independent coin of
probability `rho=2alpha/B`; after the first promotion, hold policy 1. Do not rollback in this
comparator. Every path uses exactly B requests, all released by T.

Under any causal conditional null, each queried attempt, conditional on no earlier promotion,
has promotion probability at most `rho/2`. Therefore

`P(any false promotion) <= 1-(1-rho/2)^B = 1-(1-alpha/B)^B <= alpha`.

For the stated IID-on-each-side alternative, let `p_j=1/2` if `q_j<nu` and
`p_j=1/2+epsilon` otherwise. The probability that policy 0 remains deployed at round t is exactly
`S_t=product_{j:q_j+d<=t}(1-rho*p_j)`. Hence gross decision regret against switching to policy 1
at `nu` is exactly

`2epsilon * sum_{t=nu}^T S_t`.

The net-cost excess adds `cB` and subtracts `k*product_j(1-rho*p_j)` because the learner saves its
switch cost on paths that never promote while the comparator pays one switch. These are exact
formulas in this registered model.

## Interpretation gate

Calculate this comparator and put it beside the existing noisy-information lower bound for the
same cells. The lower bound applies the full alpha constraint separately at each fixed onset; this
upper policy spends risk across repeated attempts. A wide interval may therefore reflect an onset-
mixture or lower-bound relaxation, or simply this baseline's intentionally weak one-label tests.
Do not call the interval an achievable frontier. No parameter tuning, alternative seed, or additional
model is authorized by this registration.

Reproduce with `python scripts/evaluate_switching_randomized_alpha_baseline.py`. Record exact
rational risks, regrets and costs under `outputs/switching_randomized_alpha_baseline_v1/`. The next
theory question is to sharpen the unknown-onset lower bound or optimize the safe sequential test
under the same contract, not launch another experiment.

## Analytic result (same registration)

The exact calculation gives false-promotion risk `0.0488301 <= 0.05` at every delay. Net-cost
excesses for delays 1, 5 and 20 are respectively `11.65140`, `11.65588` and `11.68697`; the
corresponding noisy-information net lower bounds are `8.32892`, `8.55787` and `9.41644`. Thus
the gaps are `3.32249`, `3.09801` and `2.27052`. The query charge is `0.20` throughout. The
script uses exact rational arithmetic for the randomized policy's risks, expected gross regrets
and costs; the binary-KL lower-bound inversion is numerical.

This is a valid but intentionally weak comparator, not an optimized policy or an attainable
frontier. The remaining gap can reflect looseness in the lower-bound relaxation (which grants the
full alpha allowance at each fixed onset) and/or low power from repeated one-label tests; this
calculation cannot separate those explanations. Nor does the false-promotion guarantee certify
that the challenger remains beneficial after an unobserved regime reversal: risk control under a
fixed conditional null and evidence about current-regime value are separate claims. No efficacy
experiment, algorithm novelty, or theorem-strengthening claim follows.
