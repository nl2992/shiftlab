# Exact one-step mixture-growth acquisition comparison

**Protocol lock:** 2026-10-23, before the fresh seed block. This evaluates a project-derived
acquisition rule. It is not a claim of a new e-process theorem or long-horizon power optimum.

## Rule and derivation

Let a fixed-stake mixture e-process have component stakes `eta_j`, prior weights `w_j`, and
component wealths `M_{j,t-1}` immediately before event `t`. Its predictable posterior weights are

`rho_{j,t-1} = w_j M_{j,t-1} / sum_l w_l M_{l,t-1}`,

so the next mixture e-value ratio for a corrected observation `Z_tilde` is exactly

`1 + eta_bar_t * Z_tilde / B`, where `eta_bar_t = sum_j rho_{j,t-1} eta_j`.

For a current covariate `x`, let `h=h(x)` be the outcome-free paired-loss proxy, let `p(x)` be the
pre-monitor classifier's estimated probability of outcome 1, and let `z_0(x), z_1(x)` be the
known policy-cost contrasts for the two possible outcomes. Under query probability `q`, the
prediction-powered value is `h` if unqueried and `h+(z_y-h)/q` if queried. The fitted one-step
objective is

`g_t(q|x) = (1-q) log(1 + eta_bar_t h/B) + q sum_y p_y(x) log(1 + eta_bar_t [h+(z_y-h)/q]/B)`.

The acquisition rule maximizes `g_t(q|x) - nu * k(x) * q` over `[q_min,q_max]`. For each outcome,
write `a=1+eta_bar_t h/B` and `b_y=eta_bar_t(z_y-h)/B`. The second derivative of
`q log(a+b_y/q)` is `-b_y^2 / (q (a q+b_y)^2)`, so the objective is concave whenever all betting
factors are positive. A scalar dual multiplier `nu` is fitted on pre-monitor validation data to
match the target expected label spend. During monitoring, `eta_bar_t` is recomputed from past
queried outcomes only. All inputs to `q_t` are therefore available before the current query and
outcome.

The exact one-step maximization is a more direct objective than the existing
`evidence_growth_proxy`, which maximizes a stake-weighted component-log surrogate. It still only
optimizes a myopic, outcome-model-based objective; it does not promise long-run detection power.
The positive known propensity, bounded prediction-powered increment, and predictable e-process
stake preserve the same conditional-mean e-process validity argument. A common hard dollar cap
stops monitoring before the next event whenever the maximum tariff cannot be paid.

## Frozen comparison

- 60 independent paired seeds per scenario, seed offset `28302026`, `n=3200`, `d=16`, CUDA.
- Scenarios: stationary control, benign nuisance shift, and boundary-local harm.
- Compare exact-mixture-growth acquisition against uniform, residual-variance, decision-value,
  cost-variance, and cost-stabilized acquisition.
- All methods use the same 20% target dollar budget, propensity bounds `[0.10,0.80]`, common
  fixed-mixture e-process bound based on `q_min=0.10`, alpha `0.05`, tariff support, and per-seed
  random query numbers. All receive the same pathwise hard dollar cap.
- Fit the outcome model, loss proxy, and dual multiplier only on pre-monitor training/validation
  observations. The live mixture's posterior stake is computed from its own past evidence.
- Primary contrast: paired difference in fixed-mixture detection probability versus uniform on
  boundary-local harm, reported both across all generated harmful streams and among those whose
  onset was reached before budget stopping. Safety outcomes are false escalations on population-null
  controls. Also report dollar spend, labels, processed horizon, RMSE, and the established query
  policy comparisons. Seeds, not time steps, are the units for uncertainty intervals.
- No tuning or winner selection on this evaluation block. If all methods rarely detect harm, treat
  the benchmark as underpowered and plan a new independent study.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget `
  --seeds 60 `
  --seed-offset 28302026 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.10 `
  --q-max 0.80 `
  --common-eprocess-bound `
  --device cuda `
  --scenarios stationary benign_nuisance boundary_local_harm `
  --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy `
  --output outputs/exact_mixture_growth_matched_60
```

The six-method run contains 1,080 method-scenario-seed rows. The runner records the resolved device,
hard-budget audit, Parquet metrics, paired-seed analyses, figures, and artifact hashes.
