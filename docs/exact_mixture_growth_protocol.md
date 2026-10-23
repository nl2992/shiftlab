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

The robustification grid adds an adaptive weight `w` and cost-neutral branch `q0(x)=b/k(x)`,
where `b` is the target expected label spend per event from validation. The final propensity is
`q_w(x)=(1-w)q0(x)+w q_exact(x)`. The neutral branch spends exactly `b` in conditional expectation
for each tariff, while `w` controls the adaptive contribution. For tariff support `[k_min,k_max]`,
the deviation from `b` is bounded by `w * max(|k_min*q_min-b|, |k_max*q_max-b|)`. This bound is
elementary and does not guarantee a realized label count or improve statistical power. The branch
requires `b/k(x)` to remain within the registered propensity bounds for every tariff.

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

## Separate cost-neutral robustness study

The preceding protocol remains the frozen evaluation of the original `w=1` exact-growth rule. A
separate development grid was locked in `docs/cost_neutral_growth_grid_protocol.md` and evaluated
weights `w in {0, .25, .50, .75, 1}` on 30 fresh paired seeds per scenario. Development selected
`w=0` under the predeclared rule: 3/30 boundary-harm detections, compared with 2/30 for uniform;
every other candidate weight had 0/30. The selected cost-neutral branch had worse boundary
stream-mean RMSE than uniform by 0.0136 (paired seed-bootstrap 95% interval [0.0041, 0.0218]).
This is an exploratory tie-break result, not a power claim.

The registered independent evaluation used 60 new seeds per scenario and compared the selected
branch with uniform and four established acquisition rules. On boundary-local harm, the selected
`w=0` branch detected 8/60 versus 4/60 for uniform; all 60 onsets were reached. Four paired streams
favored `w=0` and none favored uniform (exact two-sided McNemar p=0.125). Stream-mean RMSE was
0.0548 versus 0.0499 for uniform (difference +0.0049; paired seed-bootstrap 95% interval
[-0.0004, 0.0105]); it spent $3.42 more and queried 46.7 more labels on average. The other
cost-stabilized baseline also detected 8/60, so the outcome does not distinguish the selected
branch from that established method. There were no false escalations on either 60-seed null
control, and no hard-budget violations. This one synthetic alternative does not establish a
general detection advantage; the result is a detection-versus-estimation tradeoff.

The development and fresh metrics, reports, plots, nested run manifests, and checksums are in
`outputs/cost_neutral_growth_grid_development/` and
`outputs/cost_neutral_growth_grid_fresh_60/`. The fresh paired analysis is reproduced with
`uv run python scripts/analyze_cost_neutral_growth_fresh.py --output outputs/cost_neutral_growth_grid_fresh_60`.
