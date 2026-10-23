# Paired global-bound sensitivity: q_min 0.05 vs 0.20

This development-only analysis reuses the same 30 generated stream seeds. Uniform querying, observed labels, realized label spend, processed horizon, remaining budget, and cap status match exactly across the two runs. Only the valid prediction-powered support bound changes from 198.9 to 45.9 (factor 4.33).

|Scenario|Monitor|Detections q_min=.05|Detections q_min=.20|95% Wilson interval at .20|Median delay at .20|False alarms .05/.20|Paired exact McNemar p|
|---|---|---:|---:|---:|---:|---:|---:|
|benign_nuisance|fixed_mixture|0/30|0/30|not applicable|—|0/0|1|
|benign_nuisance|predictable_variance|0/30|0/30|not applicable|—|0/0|1|
|benign_nuisance|predictable_empirical_bernstein|0/30|0/30|not applicable|—|0/0|1|
|boundary_local_harm|fixed_mixture|0/30|19/30|[0.455, 0.781]|1129.0|0/0|3.81e-06|
|boundary_local_harm|predictable_variance|0/30|19/30|[0.455, 0.781]|1191.0|0/0|3.81e-06|
|boundary_local_harm|predictable_empirical_bernstein|0/30|0/30|[0.000, 0.114]|—|0/0|1|
|recurring_regimes|fixed_mixture|0/30|20/30|[0.488, 0.808]|2052.5|0/0|1.91e-06|
|recurring_regimes|predictable_variance|0/30|19/30|[0.455, 0.781]|2062.0|0/0|3.81e-06|
|recurring_regimes|predictable_empirical_bernstein|0/30|1/30|[0.006, 0.167]|2263.0|0/0|1|
|stationary|fixed_mixture|0/30|0/30|not applicable|—|0/0|1|
|stationary|predictable_variance|0/30|0/30|not applicable|—|0/0|1|
|stationary|predictable_empirical_bernstein|0/30|0/30|not applicable|—|0/0|1|

## Interpretation

At q_min=.20, the fixed mixture detected 19/30 boundary-local harmful streams and 20/30 recurring-regime streams; the predictable-variance comparator detected 19/30 in each. At q_min=.05, both detected 0/30 in both alternatives. The paired exact contrasts are significant for those four comparisons, but this exploratory reuse of 30 seeds is not independent confirmation. The PM-EB comparator detected 0/30 boundary-local streams and 1/30 recurring streams at q_min=.20.

Neither stationary nor benign-nuisance controls produced a false escalation in 30 streams for any monitor at either bound. The one-sided uncertainty remains substantial: 0/30 has a two-sided 95% Wilson upper endpoint of 11.35%, so these data do not demonstrate 5% calibration. The positive result identifies global-bound conservatism as a plausible power bottleneck under this design; it does not establish a new algorithm or general superiority.

All harmful onsets were reached, and the q_min contrast did not change labels queried, realized spend, processed events, budget remaining, or cap compliance. Median conditional detection delay at q_min=.20 was 1,129 events (boundary-local) and 2,052.5 events (recurring) for the fixed mixture; 1,191 and 2,062 for predictable variance.

## Reproduction

Run `uv run python scripts/analyze_monitor_bound_sensitivity.py` after both source diagnostics exist. The two source runs are generated with `scripts/diagnose_hard_budget_monitors.py`, using seed offset 39102026, 30 seeds, n=3200, CUDA, uniform_proxy, and q_min=.05 or .20.
