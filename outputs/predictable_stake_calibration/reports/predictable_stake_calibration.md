# Predictable variance-adaptive betting calibration

This CUDA/CPU calibration compares the fixed five-stake bounded e-process with a predictable plug-in Kelly stake over 2000 paired streams per cell, a 600-event horizon, and pathwise caps of 10%, 20%, and 30%.

The adaptive rule normalizes every observed inverse-propensity gain by the same global support bound, then chooses the next stake as `clip(max(0, smoothed_mean) / smoothed_second_moment, 0, 0.5)`. Its smoothed prior has strength 4, normalized mean 0.05, and second moment 0.25. This is a plug-in approximation to the Kelly fraction from a quadratic expansion of expected log wealth. The stake depends only on prior observations. Under the history-conditional null `E[X_t | F_(t-1)] <= 0`, each factor `1 + lambda_t X_t / B` is nonnegative and has conditional expectation at most one for any predictable `lambda_t` in `[0,1]`; Ville's inequality therefore controls crossings. Variance adaptation is a power strategy within a standard valid betting construction, not a new validity theorem.

`aggregate_zero` has equally likely strata with expected gains +0.12 and -0.12, respectively. `broad_positive` has outcome probability 0.56 in both strata. `high_cost_only_positive` has neutral low-cost and +0.12 high-cost conditional gain. Query randomization is independent with the stated propensity until the pathwise cap is reached. Both methods receive identical query draws and outcomes. The low/high cost and propensity grid varies estimator variance while preserving the global bound for each cell.

| Scenario | High cost | Query cap | Betting rule | Crossings / streams (95% Wilson CI) | Mean labels / cap |
|---|---:|---:|---|---:|---:|
| aggregate_zero | 1 | 10% | fixed_mixture | 33/2000 (0.012, 0.023) | 57.0/60 |
| aggregate_zero | 1 | 10% | predictable_variance_adaptive | 47/2000 (0.018, 0.031) | 57.0/60 |
| aggregate_zero | 1 | 20% | fixed_mixture | 33/2000 (0.012, 0.023) | 116.1/120 |
| aggregate_zero | 1 | 20% | predictable_variance_adaptive | 44/2000 (0.016, 0.029) | 116.1/120 |
| aggregate_zero | 1 | 30% | fixed_mixture | 52/2000 (0.020, 0.034) | 175.8/180 |
| aggregate_zero | 1 | 30% | predictable_variance_adaptive | 61/2000 (0.024, 0.039) | 175.8/180 |
| aggregate_zero | 2 | 10% | fixed_mixture | 31/2000 (0.011, 0.022) | 57.0/60 |
| aggregate_zero | 2 | 10% | predictable_variance_adaptive | 34/2000 (0.012, 0.024) | 57.0/60 |
| aggregate_zero | 2 | 20% | fixed_mixture | 31/2000 (0.011, 0.022) | 115.9/120 |
| aggregate_zero | 2 | 20% | predictable_variance_adaptive | 35/2000 (0.013, 0.024) | 115.9/120 |
| aggregate_zero | 2 | 30% | fixed_mixture | 42/2000 (0.016, 0.028) | 175.4/180 |
| aggregate_zero | 2 | 30% | predictable_variance_adaptive | 56/2000 (0.022, 0.036) | 175.4/180 |
| aggregate_zero | 5 | 10% | fixed_mixture | 20/2000 (0.006, 0.015) | 57.1/60 |
| aggregate_zero | 5 | 10% | predictable_variance_adaptive | 24/2000 (0.008, 0.018) | 57.1/60 |
| aggregate_zero | 5 | 20% | fixed_mixture | 35/2000 (0.013, 0.024) | 116.2/120 |
| aggregate_zero | 5 | 20% | predictable_variance_adaptive | 45/2000 (0.017, 0.030) | 116.2/120 |
| aggregate_zero | 5 | 30% | fixed_mixture | 46/2000 (0.017, 0.031) | 175.6/180 |
| aggregate_zero | 5 | 30% | predictable_variance_adaptive | 51/2000 (0.019, 0.033) | 175.6/180 |
| broad_positive | 1 | 10% | fixed_mixture | 146/2000 (0.062, 0.085) | 57.1/60 |
| broad_positive | 1 | 10% | predictable_variance_adaptive | 160/2000 (0.069, 0.093) | 57.1/60 |
| broad_positive | 1 | 20% | fixed_mixture | 247/2000 (0.110, 0.139) | 116.1/120 |
| broad_positive | 1 | 20% | predictable_variance_adaptive | 240/2000 (0.106, 0.135) | 116.1/120 |
| broad_positive | 1 | 30% | fixed_mixture | 421/2000 (0.193, 0.229) | 175.4/180 |
| broad_positive | 1 | 30% | predictable_variance_adaptive | 377/2000 (0.172, 0.206) | 175.4/180 |
| broad_positive | 2 | 10% | fixed_mixture | 133/2000 (0.056, 0.078) | 57.0/60 |
| broad_positive | 2 | 10% | predictable_variance_adaptive | 168/2000 (0.073, 0.097) | 57.0/60 |
| broad_positive | 2 | 20% | fixed_mixture | 236/2000 (0.105, 0.133) | 116.0/120 |
| broad_positive | 2 | 20% | predictable_variance_adaptive | 245/2000 (0.109, 0.138) | 116.0/120 |
| broad_positive | 2 | 30% | fixed_mixture | 390/2000 (0.178, 0.213) | 175.5/180 |
| broad_positive | 2 | 30% | predictable_variance_adaptive | 370/2000 (0.169, 0.203) | 175.5/180 |
| broad_positive | 5 | 10% | fixed_mixture | 93/2000 (0.038, 0.057) | 57.3/60 |
| broad_positive | 5 | 10% | predictable_variance_adaptive | 126/2000 (0.053, 0.075) | 57.3/60 |
| broad_positive | 5 | 20% | fixed_mixture | 180/2000 (0.078, 0.103) | 116.2/120 |
| broad_positive | 5 | 20% | predictable_variance_adaptive | 197/2000 (0.086, 0.112) | 116.2/120 |
| broad_positive | 5 | 30% | fixed_mixture | 272/2000 (0.122, 0.152) | 175.4/180 |
| broad_positive | 5 | 30% | predictable_variance_adaptive | 257/2000 (0.115, 0.144) | 175.4/180 |
| high_cost_only_positive | 1 | 10% | fixed_mixture | 61/2000 (0.024, 0.039) | 57.2/60 |
| high_cost_only_positive | 1 | 10% | predictable_variance_adaptive | 84/2000 (0.034, 0.052) | 57.2/60 |
| high_cost_only_positive | 1 | 20% | fixed_mixture | 89/2000 (0.036, 0.054) | 116.1/120 |
| high_cost_only_positive | 1 | 20% | predictable_variance_adaptive | 99/2000 (0.041, 0.060) | 116.1/120 |
| high_cost_only_positive | 1 | 30% | fixed_mixture | 130/2000 (0.055, 0.077) | 175.5/180 |
| high_cost_only_positive | 1 | 30% | predictable_variance_adaptive | 123/2000 (0.052, 0.073) | 175.5/180 |
| high_cost_only_positive | 2 | 10% | fixed_mixture | 59/2000 (0.023, 0.038) | 57.2/60 |
| high_cost_only_positive | 2 | 10% | predictable_variance_adaptive | 88/2000 (0.036, 0.054) | 57.2/60 |
| high_cost_only_positive | 2 | 20% | fixed_mixture | 122/2000 (0.051, 0.072) | 115.8/120 |
| high_cost_only_positive | 2 | 20% | predictable_variance_adaptive | 134/2000 (0.057, 0.079) | 115.8/120 |
| high_cost_only_positive | 2 | 30% | fixed_mixture | 171/2000 (0.074, 0.099) | 175.5/180 |
| high_cost_only_positive | 2 | 30% | predictable_variance_adaptive | 174/2000 (0.075, 0.100) | 175.5/180 |
| high_cost_only_positive | 5 | 10% | fixed_mixture | 73/2000 (0.029, 0.046) | 57.1/60 |
| high_cost_only_positive | 5 | 10% | predictable_variance_adaptive | 100/2000 (0.041, 0.060) | 57.1/60 |
| high_cost_only_positive | 5 | 20% | fixed_mixture | 168/2000 (0.073, 0.097) | 116.0/120 |
| high_cost_only_positive | 5 | 20% | predictable_variance_adaptive | 181/2000 (0.079, 0.104) | 116.0/120 |
| high_cost_only_positive | 5 | 30% | fixed_mixture | 219/2000 (0.097, 0.124) | 175.7/180 |
| high_cost_only_positive | 5 | 30% | predictable_variance_adaptive | 211/2000 (0.093, 0.120) | 175.7/180 |

Paired crossing-rate differences are adaptive minus fixed; intervals are unadjusted across cells. The exact aggregate-null cells are the type-I diagnostic. Positive alternatives compare power at the same label cap. This finite experiment does not establish uniform dominance; selection of a final method requires a locked independent confirmation and comparison with published empirical-Bernstein confidence sequences.

Figure: `figures/predictable_stake_calibration.png`. Paired contrasts and the run manifest are in the adjacent metrics and report folders.

Reproduce with `uv run python scripts/calibrate_predictable_variance_stakes.py --streams 2000 --horizon 600 --seed 28102026 --device cuda --output outputs/predictable_stake_calibration_reproduction`.
