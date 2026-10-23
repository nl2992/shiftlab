# Robust mixture-growth acquisition: development protocol

**Protocol lock:** 2026-10-23, before the development run. This study tests a model-misspecification
robustification of exact one-step mixture-growth sampling. It is an exploratory baseline, not a
novelty claim.

## Objective and derivation

For a predictable stake `eta`, proxy `h(x)`, bounded outcome contrasts `z0(x), z1(x)`, and query
probability `q`, define

`L(q,p) = (1-q) log(1 + eta*h/B) + q*((1-p) log(1 + eta*(h+(z0-h)/q)/B) + p*log(1 + eta*(h+(z1-h)/q)/B))`.

The source classifier supplies `p_hat(x)`. For a fixed probability radius `delta`, the candidate
maximizes

`min_{p in [max(0,p_hat-delta), min(1,p_hat+delta)]} L(q,p) - nu*k(x)*q`

over `[q_min,q_max]`. Since `L` is affine in `p`, its minimum over the interval occurs at an
endpoint. For fixed `p`, `q log(a+b/q)` has second derivative
`-b^2/(q*(a*q+b)^2) <= 0` when the betting factor is positive. Therefore `L(q,p)` is concave in
`q`; the pointwise minimum of the two endpoint objectives is also concave. The validation-only
dual multiplier `nu` matches expected label spend on the calibration slice.

This construction maximizes a worst-case *one-step model-based log-growth objective* over the
declared interval. It does not guarantee that a post-shift conditional outcome probability lies in
that interval, nor does it guarantee better detection power. Because the chosen `q_t` is still
predictable and in the registered positive range, the pre-existing PPI/e-process validity argument
is unchanged under its original assumptions. The evaluator-only interval coverage statistic is
computed after allocation and is never exposed to the acquisition policy.

## Frozen development comparison

- Candidate radii: `delta in {0, .05, .10, .20, .40}`.
- 30 paired seeds per scenario, offset `28602026`, `n=3200`, `d=16`, CUDA.
- Scenarios: stationary control, benign nuisance shift, boundary-local harm.
- Baselines: uniform, variance, decision-value, cost-variance, cost-stabilized, and exact mixture-growth.
- All methods share each generated stream, per-seed query uniforms, 20% target dollar budget,
  `[0.10,0.80]` propensity range, common `q_min` e-process bound, and hard dollar cap.
- Primary selection: maximize boundary-harm detections subject to no more than 5% observed
  false escalations pooled over the two null scenarios; ties use lower boundary stream-mean RMSE,
  then longer processed horizon.
- Report paired seed-bootstrap intervals, false escalations, spend, labels, processed horizon,
  hard-cap violations, and evaluator-only probability-interval coverage for every radius.
- If the selected radius beats uniform on the primary detection count or has a paired-bootstrap
  RMSE interval below zero, evaluate it on 60 disjoint seeds starting at `28702026` against all
  six established baselines. Otherwise retain the result as a development-only negative result and
  do not claim efficacy.

## Reproduction

```powershell
uv run python scripts/grid_search_robust_growth.py `
  --output outputs/robust_growth_grid_development `
  --seeds 30 `
  --seed-offset 28602026 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.10 `
  --q-max 0.80 `
  --device cuda
```

## Observed results

The development selection chose radius `0.20` because all candidate radii had 0/30 harm detections and this radius had the lowest boundary stream-mean RMSE. The independent 60-seed comparison completed on CUDA using seeds `28702026` through `28702085` for each of the three scenarios; all seven methods shared the same streams and query uniforms.

On boundary-local harm, the robust method detected 0/60 streams. Uniform detected 4/60, variance sampling 4/60, decision-value 2/60, cost-variance 3/60, cost-stabilized 3/60, and exact mixture-growth 0/60. The paired robust-minus-uniform detection difference was −0.067 descriptively; zero discordant seeds favored robust and four favored uniform. Exact two-sided McNemar p=0.125. Detection events are sparse, so the report uses the exact paired test rather than a percentile bootstrap interval for this binary contrast. Every method reached the harmful regime in 60/60 streams, so the lower detection count is not explained by failing to reach the shift. No method escalated on either null block, and no budget-cap violation was reported; 0/60 is not a calibration proof.

The robust method's boundary stream-mean RMSE was 0.0163, compared with 0.0496 for uniform, 0.0472–0.0540 for the other adaptive heuristics, and 0.0151 for exact mixture-growth. The robust-minus-uniform paired RMSE difference was −0.0333 (95% CI [−0.0419, −0.0244]); versus exact mixture-growth it was +0.0011 ([+0.0002, +0.0024]), a small but statistically separated disadvantage. Robust sampling spent $11.87 more than uniform and processed 0.280 less of the stream on average, illustrating that this RMSE comparison is not matched on realized labels or processed horizon. It is therefore an estimator-efficiency observation, not a detection or overall utility gain.

The true conditional-probability interval covered 85.4% of boundary observations, 94.8% under stationarity, and 83.6% under benign nuisance shift. This is evaluator-only diagnostic information. The pre-shift probability interval was imperfect even in control conditions, and it missed some post-shift probabilities. The result does not show that interval robustification improves allocation or monitoring; under this setup the exact mixture-growth rule was better on boundary RMSE and no worse on detection.

The full development grid, independent metrics, figure, reports, environment record and checksums are in `outputs/robust_growth_grid_development/` and `outputs/robust_growth_grid_fresh_60/`. The methods and limitations are summarized in `docs/methods_and_assumptions.md`; the nearest published robust active-learning work is listed in `references/closest_competitors.md`. The experiment supports no novelty claim.

Reproduce the fresh comparison and analysis with:

```powershell
uv run shiftlab-dive-hard-budget `
  --output outputs/robust_growth_grid_fresh_60 `
  --seeds 60 `
  --seed-offset 28702026 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.10 `
  --q-max 0.80 `
  --robust-growth-probability-radius 0.20 `
  --common-eprocess-bound `
  --scenarios stationary benign_nuisance boundary_local_harm `
  --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy `
  --device cuda
uv run python scripts/analyze_robust_growth_fresh.py --output outputs/robust_growth_grid_fresh_60
```
