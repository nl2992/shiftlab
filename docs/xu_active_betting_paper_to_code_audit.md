# Xu active betting: paper-to-code audit

**Scope:** formula-level transfer of Xu, Karampatziakis, and Mineiro, “Active, anytime-valid
risk controlling prediction sets” (NeurIPS 2024), to a one-sided paired decision-harm score. This
is a comparator implementation, not a new method or a completed empirical comparison.

**Primary source:** [arXiv:2406.10490, full text](https://arxiv.org/pdf/2406.10490), also published
in [NeurIPS 2024 proceedings](https://papers.nips.cc/paper_files/paper/2024/file/87e5a550db03b5c2c721981dc107f231-Paper-Conference.pdf).
The formula and assumptions below were checked against Sections 2.1–2.2 and 3, especially
Equations (6) and (8), Proposition 3, Proposition 5, and Corollary 1.

## Source construction and sign convention

The paper writes the active predictor-based factor for a risk `R_t(beta) in [0,1]` as

```text
1 + lambda_t * (theta - rhat_t(X_t,beta)
                - L_t/q_t(X_t) * (R_t(beta)-rhat_t(X_t,beta)))
```

where `L_t | X_t,F_{t-1} ~ Bernoulli(q_t(X_t))`. Its paper convention tests the high-risk null
`E[R_t(beta) | F_{t-1}] >= theta`; the factor accumulates evidence when the risk is below the
threshold. The source requires predictable query probabilities and stakes, a propensity floor
`q_t(X_t) >= q_min,t`, and bounded risk. Its nonnegativity restriction is

```text
lambda_t <= 1 / (1/q_min,t - theta), equivalently
q_min,t >= lambda_t / (1 + lambda_t*theta).
```

The source mostly develops its validity and optimal-allocation results in an IID stream. It does
not claim that the paper’s application-level theorem by itself covers temporal distribution shift.

## Paired-cost transfer

Let `Z_t = c(pi_t(X_t),Y_t) - c(pi_ref(X_t),Y_t) - epsilon`, with known support
`Z_t in [-B,B]`. Positive `Z_t` is excess harm. Define the Xu-oriented risk and predictor

```text
z_t       = Z_t/(2B)
R^Xu_t   = 1/2 - z_t
rhat^Xu_t= 1/2 - h_t/(2B),  where h_t predicts Z_t before the label/query coin.
```

Then `R^Xu_t in [0,1]`, and the desired harm null
`E[Z_t | F_{t-1}] <= 0` is exactly the Xu high-risk null
`E[R^Xu_t | F_{t-1}] >= 1/2`. Substitution into the source factor gives

```text
F_t = 1 + lambda_t * ( h_t/(2B)
                      + L_t/q_t(X_t) * (Z_t-h_t)/(2B) ).
```

This sign matters: using the source expression with the untransformed positive-harm `Z_t` would
bet in the opposite direction. Conditional on the current covariates and past, averaging over the
query coin gives

```text
E[F_t | X_t,F_{t-1}] = 1 + lambda_t * Z_t/(2B).
```

Conditioning on `X_t`, the potential paired outcome, and the past, then averaging over the query
coin gives `E[F_t | X_t,Y_t,F_{t-1}] = 1 + lambda_t*Z_t/(2B)`. Averaging over the current
covariate and outcome gives

```text
E[F_t | F_{t-1}] = 1 + lambda_t*E[Z_t | F_{t-1}]/(2B) <= 1.
```

The second identity uses the paired conditional null as stated; the query-coin identity alone does
not establish it. Thus products of these nonnegative factors are test supermartingales under that
null, provided the score support, predictability, label-query randomization, and paired-outcome
identification conditions hold. Xu’s weak source inequality allows a zero factor exactly at the
support/floor endpoint. The code accepts that endpoint; negative values within `1e-12` are clamped
to zero as floating-point round-off, while a factor below `-1e-12` raises an error. Wealth is
accumulated in log space, with zero wealth represented as log wealth `-infinity`.

For `theta=1/2`, the Xu stake floor specializes to
`lambda_t <= 1/(1/q_min - 1/2)`, equivalently
`q_min >= lambda_t/(1+lambda_t/2)`. At `q=1`, the proxy cancels and the factor becomes
`1 + lambda_t*Z_t/(2B)`, the full-feedback Xu factor under the affine score map. The product
process also has a q=1 unit test, and the exact propensity/stake cap is tested at a zero-factor
support endpoint.

## Predictor and query allocation

The paper’s Proposition 5 gives the fixed-stake, fixed-predictor lower-bound-optimal query policy
`q*(x) proportional to sqrt(E[(R-rhat)^2 | X=x])`, subject to its expected-label-budget and
probability-bound constraints. Since `R-rhat = -(Z-h)/(2B)`, the paired-cost residual second
moment differs only by a common scale; it induces the same normalized allocation. Corollary 1
also gives a joint closed-form solution for query policy and stake when its feasibility conditions
hold. The present formula-level arm does not implement that joint solution or claim its regret
bound.

`xu_variance_query_policy` delegates to the existing `AdaptiveQueryPolicy(method="variance",
variance_power=0.5)`. The existing helper calibrates a multiplier on a pre-monitor validation slice,
then clips probabilities to `[q_min,q_max]`; it is a finite-sample, clipped implementation of the
square-root score, not the exact unconstrained paper optimizer. The caller must choose a minimum
propensity at or above the stake-implied floor. Costs, hard-budget stopping, and post-shift expected
label spend remain task-level concerns.

## Implementation map and tests

- `xu_paired_betting_factor`: affine sign/support map, predictable proxy term, and queried
  Horvitz–Thompson residual correction.
- `xu_minimum_query_probability` / `xu_maximum_stake`: equivalent forms of the source stake-floor
  restriction for `theta=1/2`.
- `XuActivePairedEProcess`: multiplies validated factors and refuses to receive a skipped label.
- `xu_variance_query_policy`: reuses the repository’s existing square-root residual-moment query
  helper, with the required floor check.
- `tests/test_xu_active_betting.py`: checks the source equation after transformation, query/no-query
  unbiased identity, positive factors, `q=1` reduction, reciprocal floor/stake formulas, and wrapper
  configuration.

This arm is a faithful transfer of the source factor’s form and propensity condition, not a faithful
reproduction of Xu’s complete RCPS algorithm: it tests a single fixed paired-cost null rather than
constructing the paper’s sequence of calibration parameters. It also does not prove counterfactual
reference-policy costs identifiable. For dependent deployment streams, validity rests on the stated
conditional-mean null and filtration, not Xu et al.’s IID-specific application theorem.
