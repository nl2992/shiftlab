# Development grid: cost-neutral exact mixture-growth acquisition

This development-only grid used 30 independent paired stream seeds for each scenario, CUDA request `cuda`, and adaptive weights [0.0, 0.25, 0.5, 0.75, 1.0]. The uniform baseline and each candidate used the same seed-generated streams, query random uniforms, 20% target dollar budget, `[0.10, 0.80]` propensity bounds, common `q_min` e-process bound, and hard per-stream dollar cap.

For each candidate, `w=1` is the original exact growth optimizer; `w=0` is the per-event cost-neutral branch `q0=b/k`; intermediate values are convex mixtures. The selection criterion was predeclared: maximize boundary-harm detections among weights with at most 5% observed false escalations pooled over the two population-null scenarios, then break ties by lower boundary-harm stream-mean RMSE and longer processed horizon. These are development results only; any selected weight requires a fresh independent evaluation.

| Adaptive weight | Scenario | Detection candidate / uniform | Paired detection difference (95% seed bootstrap) | False escalations candidate / uniform | Mean spend candidate / uniform | Mean processed events candidate / uniform | Stream-mean RMSE difference (95% seed bootstrap) |
|---:|---|---:|---:|---:|---:|---:|---:|
|0.00|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|704.00 / 702.49|2355.8 / 2354.3|+0.0030 [-0.0038, +0.0093]|
|0.00|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|700.83 / 715.77|2356.5 / 1819.2|-0.0053 [-0.0143, +0.0039]|
|0.00|boundary_local_harm|3/30 / 2/30|+0.033 [-0.067, +0.133]|0 / 0|704.00 / 702.49|2355.8 / 2354.3|+0.0136 [+0.0041, +0.0218]|
|0.25|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|702.25 / 702.49|2360.3 / 2354.3|-0.0103 [-0.0164, -0.0036]|
|0.25|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|715.01 / 715.77|2189.1 / 1819.2|-0.0151 [-0.0245, -0.0049]|
|0.25|boundary_local_harm|0/30 / 2/30|-0.067 [-0.167, +0.000]|0 / 0|713.93 / 702.49|2201.3 / 2354.3|-0.0152 [-0.0214, -0.0092]|
|0.50|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|701.44 / 702.49|2344.0 / 2354.3|-0.0179 [-0.0251, -0.0098]|
|0.50|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|715.83 / 715.77|1990.3 / 1819.2|-0.0153 [-0.0245, -0.0052]|
|0.50|boundary_local_harm|0/30 / 2/30|-0.067 [-0.167, +0.000]|0 / 0|715.49 / 702.49|2000.0 / 2354.3|-0.0211 [-0.0311, -0.0116]|
|0.75|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|703.84 / 702.49|2295.3 / 2354.3|-0.0235 [-0.0305, -0.0159]|
|0.75|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|715.99 / 715.77|1830.2 / 1819.2|-0.0232 [-0.0312, -0.0145]|
|0.75|boundary_local_harm|0/30 / 2/30|-0.067 [-0.167, +0.000]|0 / 0|715.41 / 702.49|1828.5 / 2354.3|-0.0264 [-0.0361, -0.0167]|
|1.00|stationary|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|704.69 / 702.49|2201.6 / 2354.3|-0.0242 [-0.0325, -0.0155]|
|1.00|benign_nuisance|0/30 / 0/30|+0.000 [+0.000, +0.000]|0 / 0|715.80 / 715.77|1679.1 / 1819.2|-0.0267 [-0.0372, -0.0164]|
|1.00|boundary_local_harm|0/30 / 2/30|-0.067 [-0.167, +0.000]|0 / 0|715.44 / 702.49|1685.3 / 2354.3|-0.0310 [-0.0429, -0.0190]|

## Development selection

Selected adaptive weight: **0.00** (3/30 boundary-harm detections in development).
This selection is exploratory and uses only these development streams; it is not a confirmatory performance claim.

Reproduce with `uv run python scripts/grid_search_cost_neutral_growth.py --output outputs/cost_neutral_growth_grid_development --seeds 30 --seed-offset 28402026 --n 3200 --d 16 --device cuda`.
