# Promotion-grid uncertainty analysis

The independent simulation stream (seed) is the replication unit. Mean intervals are two-sided 95% Student-t intervals across seeds; rate intervals are 95% Wilson intervals. These are descriptive intervals and are not adjusted for selecting among scenarios or strategies.

| Scenario | Strategy | Promotion rate (Wilson 95% CI) | Expected net gain (t 95% CI) | Realized net gain (t 95% CI) | Post-deployment nongain (Wilson 95% CI) |
|---|---|---:|---:|---:|---:|
| benign_nuisance | empirical_bernstein_equal_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | empirical_bernstein_rank_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | empirical_bernstein_validation_power_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| benign_nuisance | sequential_equal_alpha_grid_gate | 13/30 [0.274, 0.608] | -26.478 [-81.382, 28.427] | -21.655 [-78.685, 35.375] | 4/30 [0.053, 0.297] |
| benign_nuisance | sequential_grid_gate | 15/30 [0.332, 0.668] | -24.299 [-80.579, 31.980] | -21.458 [-79.488, 36.571] | 4/30 [0.053, 0.297] |
| benign_nuisance | sequential_validation_power_grid_gate | 14/30 [0.302, 0.639] | -25.640 [-81.764, 30.484] | -22.123 [-80.100, 35.853] | 4/30 [0.053, 0.297] |
| benign_nuisance | validation_always_promote | 30/30 [0.886, 1.000] | -67.084 [-149.871, 15.702] | -66.050 [-151.478, 19.378] | 11/30 [0.219, 0.545] |
| boundary_local_harm | empirical_bernstein_equal_grid_gate | 25/30 [0.664, 0.927] | 227.403 [186.537, 268.269] | 227.525 [185.552, 269.498] | 0/30 [0.000, 0.114] |
| boundary_local_harm | empirical_bernstein_rank_grid_gate | 30/30 [0.886, 1.000] | 269.949 [254.252, 285.646] | 270.550 [252.348, 288.752] | 0/30 [0.000, 0.114] |
| boundary_local_harm | empirical_bernstein_validation_power_grid_gate | 27/30 [0.744, 0.965] | 244.719 [210.217, 279.221] | 244.422 [208.877, 279.966] | 0/30 [0.000, 0.114] |
| boundary_local_harm | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| boundary_local_harm | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| boundary_local_harm | sequential_equal_alpha_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| boundary_local_harm | sequential_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| boundary_local_harm | sequential_validation_power_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| boundary_local_harm | validation_always_promote | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| harmful_adaptation | empirical_bernstein_equal_grid_gate | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| harmful_adaptation | empirical_bernstein_rank_grid_gate | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| harmful_adaptation | empirical_bernstein_validation_power_grid_gate | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| harmful_adaptation | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| harmful_adaptation | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| harmful_adaptation | sequential_equal_alpha_grid_gate | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| harmful_adaptation | sequential_grid_gate | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| harmful_adaptation | sequential_validation_power_grid_gate | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| harmful_adaptation | validation_always_promote | 30/30 [0.886, 1.000] | 279.176 [272.990, 285.362] | 275.150 [267.294, 283.006] | 0/30 [0.000, 0.114] |
| recurring_regimes | empirical_bernstein_equal_grid_gate | 22/30 [0.556, 0.858] | 201.895 [154.155, 249.634] | 200.597 [152.564, 248.629] | 0/30 [0.000, 0.114] |
| recurring_regimes | empirical_bernstein_rank_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| recurring_regimes | empirical_bernstein_validation_power_grid_gate | 26/30 [0.703, 0.947] | 229.284 [192.201, 266.368] | 228.690 [190.895, 266.485] | 0/30 [0.000, 0.114] |
| recurring_regimes | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| recurring_regimes | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| recurring_regimes | sequential_equal_alpha_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| recurring_regimes | sequential_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| recurring_regimes | sequential_validation_power_grid_gate | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| recurring_regimes | validation_always_promote | 30/30 [0.886, 1.000] | 267.196 [251.126, 283.267] | 267.483 [249.304, 285.663] | 0/30 [0.000, 0.114] |
| residual_variance | empirical_bernstein_equal_grid_gate | 1/30 [0.006, 0.167] | 4.321 [-4.516, 13.157] | 5.065 [-5.294, 15.424] | 0/30 [0.000, 0.114] |
| residual_variance | empirical_bernstein_rank_grid_gate | 1/30 [0.006, 0.167] | 3.354 [-3.506, 10.215] | 4.298 [-4.493, 13.089] | 0/30 [0.000, 0.114] |
| residual_variance | empirical_bernstein_validation_power_grid_gate | 1/30 [0.006, 0.167] | 4.321 [-4.516, 13.157] | 5.065 [-5.294, 15.424] | 0/30 [0.000, 0.114] |
| residual_variance | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| residual_variance | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| residual_variance | sequential_equal_alpha_grid_gate | 28/30 [0.787, 0.982] | 97.418 [85.084, 109.751] | 99.887 [84.229, 115.544] | 0/30 [0.000, 0.114] |
| residual_variance | sequential_grid_gate | 29/30 [0.833, 0.994] | 100.337 [90.064, 110.609] | 103.518 [89.454, 117.582] | 0/30 [0.000, 0.114] |
| residual_variance | sequential_validation_power_grid_gate | 28/30 [0.787, 0.982] | 97.418 [85.084, 109.751] | 99.887 [84.229, 115.544] | 0/30 [0.000, 0.114] |
| residual_variance | validation_always_promote | 30/30 [0.886, 1.000] | 104.787 [97.070, 112.504] | 108.283 [96.017, 120.550] | 0/30 [0.000, 0.114] |
| stationary | empirical_bernstein_equal_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | empirical_bernstein_rank_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | empirical_bernstein_validation_power_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | fixed_horizon_grid_gate | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | never_promote | 0/30 [0.000, 0.114] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0/30 [0.000, 0.114] |
| stationary | sequential_equal_alpha_grid_gate | 16/30 [0.361, 0.698] | 25.504 [15.981, 35.028] | 29.940 [18.140, 41.740] | 0/30 [0.000, 0.114] |
| stationary | sequential_grid_gate | 20/30 [0.488, 0.808] | 30.958 [22.097, 39.819] | 34.400 [23.104, 45.696] | 0/30 [0.000, 0.114] |
| stationary | sequential_validation_power_grid_gate | 18/30 [0.423, 0.754] | 28.427 [19.089, 37.764] | 33.537 [21.513, 45.560] | 0/30 [0.000, 0.114] |
| stationary | validation_always_promote | 30/30 [0.886, 1.000] | 45.381 [41.623, 49.139] | 46.483 [38.884, 54.083] | 0/30 [0.000, 0.114] |

## Paired policy differences

Expected deployment net-gain differences are paired by scenario and seed. Intervals are unadjusted 95% Student-t intervals.

| Scenario | Comparison | Mean paired difference (95% CI) |
|---|---|---:|
| benign_nuisance | sequential rank − never | -24.299 [-80.579, 31.980] |
| benign_nuisance | sequential rank − always | 42.785 [-20.372, 105.943] |
| benign_nuisance | sequential equal − never | -26.478 [-81.382, 28.427] |
| benign_nuisance | sequential equal − always | 40.607 [-22.955, 104.169] |
| benign_nuisance | sequential validation-power − never | -25.640 [-81.764, 30.484] |
| benign_nuisance | sequential validation-power − always | 41.444 [-21.904, 104.792] |
| benign_nuisance | empirical-Bernstein rank − never | 0.000 [0.000, 0.000] |
| benign_nuisance | empirical-Bernstein rank − always | 67.084 [-15.702, 149.871] |
| benign_nuisance | empirical-Bernstein equal − never | 0.000 [0.000, 0.000] |
| benign_nuisance | empirical-Bernstein equal − always | 67.084 [-15.702, 149.871] |
| benign_nuisance | empirical-Bernstein validation-power − never | 0.000 [0.000, 0.000] |
| benign_nuisance | empirical-Bernstein validation-power − always | 67.084 [-15.702, 149.871] |
| benign_nuisance | sequential rank − equal | 2.178 [-3.025, 7.382] |
| benign_nuisance | sequential rank − validation-weighted | 1.341 [-1.402, 4.084] |
| benign_nuisance | empirical-Bernstein rank − equal | 0.000 [0.000, 0.000] |
| benign_nuisance | empirical-Bernstein rank − validation-weighted | 0.000 [0.000, 0.000] |
| boundary_local_harm | sequential rank − never | 267.196 [251.126, 283.267] |
| boundary_local_harm | sequential rank − always | 0.000 [0.000, 0.000] |
| boundary_local_harm | sequential equal − never | 267.196 [251.126, 283.267] |
| boundary_local_harm | sequential equal − always | 0.000 [0.000, 0.000] |
| boundary_local_harm | sequential validation-power − never | 267.196 [251.126, 283.267] |
| boundary_local_harm | sequential validation-power − always | 0.000 [0.000, 0.000] |
| boundary_local_harm | empirical-Bernstein rank − never | 269.949 [254.252, 285.646] |
| boundary_local_harm | empirical-Bernstein rank − always | 2.752 [-2.877, 8.381] |
| boundary_local_harm | empirical-Bernstein equal − never | 227.403 [186.537, 268.269] |
| boundary_local_harm | empirical-Bernstein equal − always | -39.793 [-82.930, 3.343] |
| boundary_local_harm | empirical-Bernstein validation-power − never | 244.719 [210.217, 279.221] |
| boundary_local_harm | empirical-Bernstein validation-power − always | -22.478 [-56.447, 11.492] |
| boundary_local_harm | sequential rank − equal | 0.000 [0.000, 0.000] |
| boundary_local_harm | sequential rank − validation-weighted | 0.000 [0.000, 0.000] |
| boundary_local_harm | empirical-Bernstein rank − equal | 42.546 [0.175, 84.917] |
| boundary_local_harm | empirical-Bernstein rank − validation-weighted | 25.230 [-7.970, 58.429] |
| harmful_adaptation | sequential rank − never | 279.176 [272.990, 285.362] |
| harmful_adaptation | sequential rank − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | sequential equal − never | 279.176 [272.990, 285.362] |
| harmful_adaptation | sequential equal − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | sequential validation-power − never | 279.176 [272.990, 285.362] |
| harmful_adaptation | sequential validation-power − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | empirical-Bernstein rank − never | 279.176 [272.990, 285.362] |
| harmful_adaptation | empirical-Bernstein rank − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | empirical-Bernstein equal − never | 279.176 [272.990, 285.362] |
| harmful_adaptation | empirical-Bernstein equal − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | empirical-Bernstein validation-power − never | 279.176 [272.990, 285.362] |
| harmful_adaptation | empirical-Bernstein validation-power − always | 0.000 [0.000, 0.000] |
| harmful_adaptation | sequential rank − equal | 0.000 [0.000, 0.000] |
| harmful_adaptation | sequential rank − validation-weighted | 0.000 [0.000, 0.000] |
| harmful_adaptation | empirical-Bernstein rank − equal | 0.000 [0.000, 0.000] |
| harmful_adaptation | empirical-Bernstein rank − validation-weighted | 0.000 [0.000, 0.000] |
| recurring_regimes | sequential rank − never | 267.196 [251.126, 283.267] |
| recurring_regimes | sequential rank − always | 0.000 [0.000, 0.000] |
| recurring_regimes | sequential equal − never | 267.196 [251.126, 283.267] |
| recurring_regimes | sequential equal − always | 0.000 [0.000, 0.000] |
| recurring_regimes | sequential validation-power − never | 267.196 [251.126, 283.267] |
| recurring_regimes | sequential validation-power − always | 0.000 [0.000, 0.000] |
| recurring_regimes | empirical-Bernstein rank − never | 267.196 [251.126, 283.267] |
| recurring_regimes | empirical-Bernstein rank − always | 0.000 [0.000, 0.000] |
| recurring_regimes | empirical-Bernstein equal − never | 201.895 [154.155, 249.634] |
| recurring_regimes | empirical-Bernstein equal − always | -65.302 [-116.072, -14.531] |
| recurring_regimes | empirical-Bernstein validation-power − never | 229.284 [192.201, 266.368] |
| recurring_regimes | empirical-Bernstein validation-power − always | -37.912 [-77.713, 1.889] |
| recurring_regimes | sequential rank − equal | 0.000 [0.000, 0.000] |
| recurring_regimes | sequential rank − validation-weighted | 0.000 [0.000, 0.000] |
| recurring_regimes | empirical-Bernstein rank − equal | 65.302 [14.531, 116.072] |
| recurring_regimes | empirical-Bernstein rank − validation-weighted | 37.912 [-1.889, 77.713] |
| residual_variance | sequential rank − never | 100.337 [90.064, 110.609] |
| residual_variance | sequential rank − always | -4.450 [-13.552, 4.652] |
| residual_variance | sequential equal − never | 97.418 [85.084, 109.751] |
| residual_variance | sequential equal − always | -7.369 [-19.777, 5.038] |
| residual_variance | sequential validation-power − never | 97.418 [85.084, 109.751] |
| residual_variance | sequential validation-power − always | -7.369 [-19.777, 5.038] |
| residual_variance | empirical-Bernstein rank − never | 3.354 [-3.506, 10.215] |
| residual_variance | empirical-Bernstein rank − always | -101.433 [-111.951, -90.914] |
| residual_variance | empirical-Bernstein equal − never | 4.321 [-4.516, 13.157] |
| residual_variance | empirical-Bernstein equal − always | -100.467 [-112.417, -88.516] |
| residual_variance | empirical-Bernstein validation-power − never | 4.321 [-4.516, 13.157] |
| residual_variance | empirical-Bernstein validation-power − always | -100.467 [-112.417, -88.516] |
| residual_variance | sequential rank − equal | 2.919 [-5.733, 11.571] |
| residual_variance | sequential rank − validation-weighted | 2.919 [-5.733, 11.571] |
| residual_variance | empirical-Bernstein rank − equal | -0.966 [-2.942, 1.010] |
| residual_variance | empirical-Bernstein rank − validation-weighted | -0.966 [-2.942, 1.010] |
| stationary | sequential rank − never | 30.958 [22.097, 39.819] |
| stationary | sequential rank − always | -14.423 [-22.969, -5.877] |
| stationary | sequential equal − never | 25.504 [15.981, 35.028] |
| stationary | sequential equal − always | -19.877 [-28.703, -11.051] |
| stationary | sequential validation-power − never | 28.427 [19.089, 37.764] |
| stationary | sequential validation-power − always | -16.955 [-26.184, -7.725] |
| stationary | empirical-Bernstein rank − never | 0.000 [0.000, 0.000] |
| stationary | empirical-Bernstein rank − always | -45.381 [-49.139, -41.623] |
| stationary | empirical-Bernstein equal − never | 0.000 [0.000, 0.000] |
| stationary | empirical-Bernstein equal − always | -45.381 [-49.139, -41.623] |
| stationary | empirical-Bernstein validation-power − never | 0.000 [0.000, 0.000] |
| stationary | empirical-Bernstein validation-power − always | -45.381 [-49.139, -41.623] |
| stationary | sequential rank − equal | 5.454 [-2.403, 13.311] |
| stationary | sequential rank − validation-weighted | 2.532 [-4.516, 9.579] |
| stationary | empirical-Bernstein rank − equal | 0.000 [0.000, 0.000] |
| stationary | empirical-Bernstein rank − validation-weighted | 0.000 [0.000, 0.000] |

The certificate's shadow-period statistical guarantee does not guarantee later deployment benefit. `false_promotion_post_nongain` is an out-of-period reversal diagnostic, not a test type-I error. See `promotion_grid_comparison.md` for the experiment protocol and assumptions.
