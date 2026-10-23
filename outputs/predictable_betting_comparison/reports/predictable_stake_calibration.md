# Matched comparison of predictable betting rules

This CUDA/CPU calibration compares a fixed five-stake bounded e-process, a predictable plug-in Kelly stake, and the published predictable plug-in empirical-Bernstein (PM-EB) process over 2000 paired streams per cell, a 600-event horizon, and pathwise caps of 10%, 20%, and 30%.

The adaptive rule normalizes every observed inverse-propensity gain by the same global support bound, then chooses the next stake as `clip(max(0, smoothed_mean) / smoothed_second_moment, 0, 0.5)`. Its smoothed prior has strength 4, normalized mean 0.05, and second moment 0.25. This is a plug-in approximation to the Kelly fraction from a quadratic expansion of expected log wealth. The stake depends only on prior observations. Under the history-conditional null `E[X_t | F_(t-1)] <= 0`, each factor `1 + lambda_t X_t / B` is nonnegative and has conditional expectation at most one for any predictable `lambda_t` in `[0,1]`; Ville's inequality therefore controls crossings. Variance adaptation is a power strategy within a standard valid betting construction, not a new validity theorem.

PM-EB maps normalized gains `R_t=X_t/B` to `Z_t=(R_t+1)/2` and tests `E[Z_t | F_(t-1)] <= 1/2`. Its log increment is `lambda_t(Z_t-1/2) - 4(Z_t-mu_hat_(t-1))^2 psi_E(lambda_t)`, where `psi_E(lambda)=(-log(1-lambda)-lambda)/4`. The predictable stake is `min(1/2, sqrt(2 log(2/alpha)/(sigma_hat^2_(t-1) t log(1+t))))`; smoothed mean and variance estimates update after each observation. This published construction is included as an established baseline, not a novelty claim.

`aggregate_zero` has equally likely strata with expected gains +0.12 and -0.12, respectively. `broad_positive` has outcome probability 0.56 in both strata. `high_cost_only_positive` has neutral low-cost and +0.12 high-cost conditional gain. Query randomization is independent with the stated propensity until the pathwise cap is reached. All three methods receive identical query draws and outcomes. The low/high cost and propensity grid varies estimator variance while preserving the global bound for each cell.

| Scenario | High cost | Query cap | Betting rule | Crossings / streams (95% Wilson CI) | Mean labels / cap |
|---|---:|---:|---|---:|---:|
| aggregate_zero | 1 | 10% | fixed_mixture | 29/2000 (0.010, 0.021) | 57.3/60 |
| aggregate_zero | 1 | 10% | predictable_variance_adaptive | 39/2000 (0.014, 0.027) | 57.3/60 |
| aggregate_zero | 1 | 10% | predictable_plug_in_eb | 4/2000 (0.001, 0.005) | 57.3/60 |
| aggregate_zero | 1 | 20% | fixed_mixture | 40/2000 (0.015, 0.027) | 116.1/120 |
| aggregate_zero | 1 | 20% | predictable_variance_adaptive | 47/2000 (0.018, 0.031) | 116.1/120 |
| aggregate_zero | 1 | 20% | predictable_plug_in_eb | 10/2000 (0.003, 0.009) | 116.1/120 |
| aggregate_zero | 1 | 30% | fixed_mixture | 52/2000 (0.020, 0.034) | 175.6/180 |
| aggregate_zero | 1 | 30% | predictable_variance_adaptive | 53/2000 (0.020, 0.034) | 175.6/180 |
| aggregate_zero | 1 | 30% | predictable_plug_in_eb | 17/2000 (0.005, 0.014) | 175.6/180 |
| aggregate_zero | 2 | 10% | fixed_mixture | 23/2000 (0.008, 0.017) | 57.2/60 |
| aggregate_zero | 2 | 10% | predictable_variance_adaptive | 31/2000 (0.011, 0.022) | 57.2/60 |
| aggregate_zero | 2 | 10% | predictable_plug_in_eb | 2/2000 (0.000, 0.004) | 57.2/60 |
| aggregate_zero | 2 | 20% | fixed_mixture | 37/2000 (0.013, 0.025) | 116.1/120 |
| aggregate_zero | 2 | 20% | predictable_variance_adaptive | 36/2000 (0.013, 0.025) | 116.1/120 |
| aggregate_zero | 2 | 20% | predictable_plug_in_eb | 8/2000 (0.002, 0.008) | 116.1/120 |
| aggregate_zero | 2 | 30% | fixed_mixture | 41/2000 (0.015, 0.028) | 175.5/180 |
| aggregate_zero | 2 | 30% | predictable_variance_adaptive | 45/2000 (0.017, 0.030) | 175.5/180 |
| aggregate_zero | 2 | 30% | predictable_plug_in_eb | 12/2000 (0.003, 0.010) | 175.5/180 |
| aggregate_zero | 5 | 10% | fixed_mixture | 28/2000 (0.010, 0.020) | 56.9/60 |
| aggregate_zero | 5 | 10% | predictable_variance_adaptive | 34/2000 (0.012, 0.024) | 56.9/60 |
| aggregate_zero | 5 | 10% | predictable_plug_in_eb | 0/2000 (0.000, 0.002) | 56.9/60 |
| aggregate_zero | 5 | 20% | fixed_mixture | 25/2000 (0.008, 0.018) | 116.0/120 |
| aggregate_zero | 5 | 20% | predictable_variance_adaptive | 33/2000 (0.012, 0.023) | 116.0/120 |
| aggregate_zero | 5 | 20% | predictable_plug_in_eb | 5/2000 (0.001, 0.006) | 116.0/120 |
| aggregate_zero | 5 | 30% | fixed_mixture | 42/2000 (0.016, 0.028) | 175.4/180 |
| aggregate_zero | 5 | 30% | predictable_variance_adaptive | 47/2000 (0.018, 0.031) | 175.4/180 |
| aggregate_zero | 5 | 30% | predictable_plug_in_eb | 13/2000 (0.004, 0.011) | 175.4/180 |
| broad_positive | 1 | 10% | fixed_mixture | 143/2000 (0.061, 0.084) | 57.0/60 |
| broad_positive | 1 | 10% | predictable_variance_adaptive | 162/2000 (0.070, 0.094) | 57.0/60 |
| broad_positive | 1 | 10% | predictable_plug_in_eb | 59/2000 (0.023, 0.038) | 57.0/60 |
| broad_positive | 1 | 20% | fixed_mixture | 250/2000 (0.111, 0.140) | 116.1/120 |
| broad_positive | 1 | 20% | predictable_variance_adaptive | 248/2000 (0.110, 0.139) | 116.1/120 |
| broad_positive | 1 | 20% | predictable_plug_in_eb | 107/2000 (0.044, 0.064) | 116.1/120 |
| broad_positive | 1 | 30% | fixed_mixture | 409/2000 (0.187, 0.223) | 175.4/180 |
| broad_positive | 1 | 30% | predictable_variance_adaptive | 347/2000 (0.158, 0.191) | 175.4/180 |
| broad_positive | 1 | 30% | predictable_plug_in_eb | 209/2000 (0.092, 0.119) | 175.4/180 |
| broad_positive | 2 | 10% | fixed_mixture | 120/2000 (0.050, 0.071) | 57.1/60 |
| broad_positive | 2 | 10% | predictable_variance_adaptive | 147/2000 (0.063, 0.086) | 57.1/60 |
| broad_positive | 2 | 10% | predictable_plug_in_eb | 34/2000 (0.012, 0.024) | 57.1/60 |
| broad_positive | 2 | 20% | fixed_mixture | 247/2000 (0.110, 0.139) | 116.2/120 |
| broad_positive | 2 | 20% | predictable_variance_adaptive | 265/2000 (0.118, 0.148) | 116.2/120 |
| broad_positive | 2 | 20% | predictable_plug_in_eb | 116/2000 (0.049, 0.069) | 116.2/120 |
| broad_positive | 2 | 30% | fixed_mixture | 360/2000 (0.164, 0.197) | 175.7/180 |
| broad_positive | 2 | 30% | predictable_variance_adaptive | 332/2000 (0.150, 0.183) | 175.7/180 |
| broad_positive | 2 | 30% | predictable_plug_in_eb | 185/2000 (0.081, 0.106) | 175.7/180 |
| broad_positive | 5 | 10% | fixed_mixture | 81/2000 (0.033, 0.050) | 57.0/60 |
| broad_positive | 5 | 10% | predictable_variance_adaptive | 112/2000 (0.047, 0.067) | 57.0/60 |
| broad_positive | 5 | 10% | predictable_plug_in_eb | 9/2000 (0.002, 0.009) | 57.0/60 |
| broad_positive | 5 | 20% | fixed_mixture | 183/2000 (0.080, 0.105) | 116.1/120 |
| broad_positive | 5 | 20% | predictable_variance_adaptive | 194/2000 (0.085, 0.111) | 116.1/120 |
| broad_positive | 5 | 20% | predictable_plug_in_eb | 73/2000 (0.029, 0.046) | 116.1/120 |
| broad_positive | 5 | 30% | fixed_mixture | 275/2000 (0.123, 0.153) | 175.4/180 |
| broad_positive | 5 | 30% | predictable_variance_adaptive | 260/2000 (0.116, 0.145) | 175.4/180 |
| broad_positive | 5 | 30% | predictable_plug_in_eb | 143/2000 (0.061, 0.084) | 175.4/180 |
| high_cost_only_positive | 1 | 10% | fixed_mixture | 49/2000 (0.019, 0.032) | 57.0/60 |
| high_cost_only_positive | 1 | 10% | predictable_variance_adaptive | 75/2000 (0.030, 0.047) | 57.0/60 |
| high_cost_only_positive | 1 | 10% | predictable_plug_in_eb | 13/2000 (0.004, 0.011) | 57.0/60 |
| high_cost_only_positive | 1 | 20% | fixed_mixture | 107/2000 (0.044, 0.064) | 116.1/120 |
| high_cost_only_positive | 1 | 20% | predictable_variance_adaptive | 107/2000 (0.044, 0.064) | 116.1/120 |
| high_cost_only_positive | 1 | 20% | predictable_plug_in_eb | 50/2000 (0.019, 0.033) | 116.1/120 |
| high_cost_only_positive | 1 | 30% | fixed_mixture | 144/2000 (0.061, 0.084) | 175.5/180 |
| high_cost_only_positive | 1 | 30% | predictable_variance_adaptive | 131/2000 (0.055, 0.077) | 175.5/180 |
| high_cost_only_positive | 1 | 30% | predictable_plug_in_eb | 60/2000 (0.023, 0.038) | 175.5/180 |
| high_cost_only_positive | 2 | 10% | fixed_mixture | 73/2000 (0.029, 0.046) | 57.2/60 |
| high_cost_only_positive | 2 | 10% | predictable_variance_adaptive | 95/2000 (0.039, 0.058) | 57.2/60 |
| high_cost_only_positive | 2 | 10% | predictable_plug_in_eb | 17/2000 (0.005, 0.014) | 57.2/60 |
| high_cost_only_positive | 2 | 20% | fixed_mixture | 140/2000 (0.060, 0.082) | 116.1/120 |
| high_cost_only_positive | 2 | 20% | predictable_variance_adaptive | 150/2000 (0.064, 0.087) | 116.1/120 |
| high_cost_only_positive | 2 | 20% | predictable_plug_in_eb | 56/2000 (0.022, 0.036) | 116.1/120 |
| high_cost_only_positive | 2 | 30% | fixed_mixture | 177/2000 (0.077, 0.102) | 175.7/180 |
| high_cost_only_positive | 2 | 30% | predictable_variance_adaptive | 176/2000 (0.076, 0.101) | 175.7/180 |
| high_cost_only_positive | 2 | 30% | predictable_plug_in_eb | 76/2000 (0.030, 0.047) | 175.7/180 |
| high_cost_only_positive | 5 | 10% | fixed_mixture | 63/2000 (0.025, 0.040) | 57.1/60 |
| high_cost_only_positive | 5 | 10% | predictable_variance_adaptive | 94/2000 (0.039, 0.057) | 57.1/60 |
| high_cost_only_positive | 5 | 10% | predictable_plug_in_eb | 12/2000 (0.003, 0.010) | 57.1/60 |
| high_cost_only_positive | 5 | 20% | fixed_mixture | 140/2000 (0.060, 0.082) | 116.0/120 |
| high_cost_only_positive | 5 | 20% | predictable_variance_adaptive | 152/2000 (0.065, 0.088) | 116.0/120 |
| high_cost_only_positive | 5 | 20% | predictable_plug_in_eb | 60/2000 (0.023, 0.038) | 116.0/120 |
| high_cost_only_positive | 5 | 30% | fixed_mixture | 211/2000 (0.093, 0.120) | 175.4/180 |
| high_cost_only_positive | 5 | 30% | predictable_variance_adaptive | 213/2000 (0.094, 0.121) | 175.4/180 |
| high_cost_only_positive | 5 | 30% | predictable_plug_in_eb | 98/2000 (0.040, 0.059) | 175.4/180 |

Paired Kelly-minus-fixed and PM-EB-minus-fixed crossing-rate differences are stored with paired 95% t intervals, unadjusted across cells. The exact aggregate-null cells are the type-I diagnostic. Positive alternatives compare power at the same label cap. This finite experiment does not establish uniform dominance; any selected method requires a locked independent confirmation.

Figure: `figures/predictable_stake_calibration.png`. Paired contrasts and the run manifest are in the adjacent metrics and report folders.

Reproduce with `uv run python scripts/calibrate_predictable_variance_stakes.py --streams 2000 --horizon 600 --seed 29102026 --device cuda --output outputs/predictable_betting_comparison_reproduction`.
