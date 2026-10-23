# Development grid: robust exact mixture-growth allocation

This development-only grid used 30 paired stream seeds per scenario, CUDA request `cuda`, and probability radii [0.0, 0.05, 0.1, 0.2, 0.4]. The six established methods were run on the same streams as reference baselines. Every candidate shared stream seeds, query uniforms, target dollar budget, propensity bounds, common e-process bound, and hard per-stream dollar cap.

For each covariate, the algorithm maximizes the worst-case one-step expected log mixture-e-value increment over a fixed interval around the pre-monitor classifier's outcome probability, less a dual label-cost price. This is a model-robust objective only for the declared interval; the true post-shift probability may lie outside it. The query probability remains predictable and the e-process guarantee conditions are unchanged.

|Radius|Scenario|Detections / uniform|Paired detection difference (95% bootstrap)|False escalations|RMSE / uniform|RMSE difference (95% bootstrap)|Spend / uniform|Labels / uniform|Mean evaluator-only interval coverage|
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
|0.00|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0125 / 0.0366|-0.0242 [-0.0324, -0.0154]|711.48 / 704.58|484.5 / 469.0|0.000|
|0.00|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0179 / 0.0378|-0.0199 [-0.0282, -0.0116]|720.95 / 721.01|369.9 / 363.7|0.000|
|0.00|boundary_local_harm|0/30 / 1/30|-0.033 [-0.100, +0.000]|0 / 0|0.0154 / 0.0476|-0.0323 [-0.0444, -0.0206]|720.32 / 704.58|492.5 / 469.0|0.000|
|0.05|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0126 / 0.0366|-0.0241 [-0.0325, -0.0154]|711.55 / 704.58|484.5 / 469.0|0.693|
|0.05|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0191 / 0.0378|-0.0187 [-0.0278, -0.0096]|720.83 / 721.01|369.9 / 363.7|0.635|
|0.05|boundary_local_harm|0/30 / 1/30|-0.033 [-0.100, +0.000]|0 / 0|0.0153 / 0.0476|-0.0324 [-0.0444, -0.0209]|720.33 / 704.58|492.5 / 469.0|0.649|
|0.10|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0128 / 0.0366|-0.0239 [-0.0322, -0.0149]|711.53 / 704.58|484.6 / 469.0|0.833|
|0.10|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0189 / 0.0378|-0.0189 [-0.0279, -0.0099]|720.85 / 721.01|369.9 / 363.7|0.745|
|0.10|boundary_local_harm|0/30 / 1/30|-0.033 [-0.100, +0.000]|0 / 0|0.0153 / 0.0476|-0.0323 [-0.0443, -0.0208]|720.21 / 704.58|492.6 / 469.0|0.759|
|0.20|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0117 / 0.0366|-0.0249 [-0.0334, -0.0160]|710.40 / 704.58|484.0 / 469.0|0.947|
|0.20|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0185 / 0.0378|-0.0193 [-0.0280, -0.0103]|720.63 / 721.01|370.0 / 363.7|0.852|
|0.20|boundary_local_harm|0/30 / 1/30|-0.033 [-0.100, +0.000]|0 / 0|0.0153 / 0.0476|-0.0324 [-0.0446, -0.0207]|720.53 / 704.58|492.9 / 469.0|0.853|
|0.40|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0137 / 0.0366|-0.0229 [-0.0314, -0.0141]|708.30 / 704.58|484.1 / 469.0|0.997|
|0.40|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|0.0201 / 0.0378|-0.0178 [-0.0261, -0.0091]|720.71 / 721.01|370.5 / 363.7|0.938|
|0.40|boundary_local_harm|0/30 / 1/30|-0.033 [-0.100, +0.000]|0 / 0|0.0161 / 0.0476|-0.0315 [-0.0441, -0.0194]|720.27 / 704.58|494.1 / 469.0|0.932|

## Development selection

Selected probability radius: **0.20** (0/30 boundary-harm detections; uniform 1/30). The predeclared rule maximizes detections under a pooled 5% null false-escalation guardrail, then minimizes boundary stream-mean RMSE and maximizes processed events.
A fresh evaluation is required because the selected candidate exceeded uniform on the primary detection count or showed a bootstrap RMSE improvement. This remains exploratory until that independent block is completed.

Reproduce with `uv run python scripts/grid_search_robust_growth.py --output outputs/robust_growth_grid_development --seeds 30 --seed-offset 28602026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda`.
