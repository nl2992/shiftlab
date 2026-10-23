# Promotion-grid uncertainty analysis

The independent simulation stream (seed) is the replication unit. Mean intervals are two-sided 95% Student-t intervals across seeds; rate intervals are 95% Wilson intervals. These are descriptive intervals and are not adjusted for selecting among scenarios or strategies.

| Scenario | Strategy | Promotion rate (Wilson 95% CI) | Expected net gain (t 95% CI) | Realized net gain (t 95% CI) | Post-deployment nongain (Wilson 95% CI) |
|---|---|---:|---:|---:|---:|
| benign_nuisance | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | sequential_grid_gate | 15/30 [0.332, 0.668] | -24.299 [-80.579, 31.980] | -21.458 [-79.488, 36.571] | 4/30 [0.053, 0.297] |
| benign_nuisance | validation_always_promote | 30/30 [0.886, 1.000] | -65.826 [-148.527, 16.875] | -64.550 [-149.860, 20.760] | 11/30 [0.219, 0.545] |
| boundary_local_harm | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| boundary_local_harm | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| boundary_local_harm | sequential_grid_gate | 30/30 [0.886, 1.000] | 269.013 [252.740, 285.286] | 268.983 [250.483, 287.484] | 0/30 [0.000, 0.114] |
| boundary_local_harm | validation_always_promote | 30/30 [0.886, 1.000] | 269.013 [252.740, 285.286] | 268.983 [250.483, 287.484] | 0/30 [0.000, 0.114] |
| harmful_adaptation | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| harmful_adaptation | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| harmful_adaptation | sequential_grid_gate | 30/30 [0.886, 1.000] | 279.128 [272.972, 285.284] | 274.850 [267.026, 282.674] | 0/30 [0.000, 0.114] |
| harmful_adaptation | validation_always_promote | 30/30 [0.886, 1.000] | 279.128 [272.972, 285.284] | 274.850 [267.026, 282.674] | 0/30 [0.000, 0.114] |
| recurring_regimes | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| recurring_regimes | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| recurring_regimes | sequential_grid_gate | 30/30 [0.886, 1.000] | 269.013 [252.740, 285.286] | 268.983 [250.483, 287.484] | 0/30 [0.000, 0.114] |
| recurring_regimes | validation_always_promote | 30/30 [0.886, 1.000] | 269.013 [252.740, 285.286] | 268.983 [250.483, 287.484] | 0/30 [0.000, 0.114] |
| residual_variance | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| residual_variance | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| residual_variance | sequential_grid_gate | 29/30 [0.833, 0.994] | 101.366 [90.962, 111.770] | 104.218 [90.086, 118.351] | 0/30 [0.000, 0.114] |
| residual_variance | validation_always_promote | 30/30 [0.886, 1.000] | 105.816 [98.009, 113.624] | 108.983 [96.677, 121.290] | 0/30 [0.000, 0.114] |
| stationary | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | sequential_grid_gate | 21/30 [0.521, 0.833] | 33.049 [24.224, 41.875] | 37.332 [25.699, 48.964] | 0/30 [0.000, 0.114] |
| stationary | validation_always_promote | 30/30 [0.886, 1.000] | 45.333 [41.632, 49.034] | 46.183 [38.585, 53.782] | 0/30 [0.000, 0.114] |

## Paired policy differences

Expected deployment net-gain differences are paired by scenario and seed. Positive sequential-minus-always values favor sequential certification. Intervals are unadjusted 95% Student-t intervals.

| Scenario | Comparison | Mean paired difference (95% CI) |
|---|---|---:|
| benign_nuisance | sequential − never | -24.299 [-80.579, 31.980] |
| benign_nuisance | sequential − always | 41.527 [-21.449, 104.503] |
| boundary_local_harm | sequential − never | 269.013 [252.740, 285.286] |
| boundary_local_harm | sequential − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | sequential − never | 279.128 [272.972, 285.284] |
| harmful_adaptation | sequential − always | 0.000 [0.000, 0.000] |
| recurring_regimes | sequential − never | 269.013 [252.740, 285.286] |
| recurring_regimes | sequential − always | 0.000 [0.000, 0.000] |
| residual_variance | sequential − never | 101.366 [90.962, 111.770] |
| residual_variance | sequential − always | -4.450 [-13.552, 4.652] |
| stationary | sequential − never | 33.049 [24.224, 41.875] |
| stationary | sequential − always | -12.284 [-20.717, -3.850] |

The certificate's shadow-period statistical guarantee does not guarantee later deployment benefit. `false_promotion_post_nongain` is an out-of-period reversal diagnostic, not a test type-I error. See `promotion_grid_comparison.md` for the experiment protocol and assumptions.
