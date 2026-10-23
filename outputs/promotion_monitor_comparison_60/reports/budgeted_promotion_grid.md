# Repeated-candidate promotion under a hard label budget

This benchmark evaluates 7 scenarios with 60 independent seeds each on `cuda`. It crosses 1 predeclared query designs, 1 estimators, 6 monitoring rules, 1 candidate-level alpha allocations, and hard label caps (0.1, 0.2). Every query design and candidate gate sees the same seed-specific DGP; all candidate tests within one stream share queried labels. Each stream has 13 frozen candidates.

Candidates are trained on the training slice and ordered using the fully labeled validation slice. Validation also fixes candidate alpha weights and the acquisition score model. Monitor labels are revealed only when queried. This run uses query design(s) uniform; propensities are predictable from current covariates and pre-monitor fits, with a positive floor. For each budget level the same maximum number of labels is available to every configured method. The monitor stops before the next event when no label remains affordable, so actual label counts never exceed the hard cap; realized counts and processed horizons are reported because policies need not spend the entire cap.

The implementation supports prediction-powered `h_tk + I_t/q_t (Z_tk-h_tk)` and direct inverse-propensity `I_t Z_tk/q_t` estimates; this run uses direct_ipw. Both estimates are shifted by the amortized switching charge. Configured monitors are fixed_mixture, fixed_mixture_half_alpha, predictable_kelly, pm_eb, positive_betting, hedged_positive. The fixed-mixture half-alpha reference matches the half-weighted hedge branch's threshold. They use the same candidate-level alpha spending rule(s) rank and global bound. Here `Z` is incumbent cost minus candidate cost, `h` is a pre-monitor fitted expected-cost contrast, and the deployment horizon is `H`. With `|Z|,|h| <= M=max(FN,FP)`, the global-mode bounds are `M(2/q_min-1)+k_switch/H` and `M/q_min+k_switch/H`; local-mode bounds are computed per candidate and event from estimator support. Candidate alpha weights are fixed before monitor outcomes and sum to at most alpha. The fixed global bounds support the history-conditional mean-gain null. The global-null control replaces all candidates with incumbent copies; its zero-crossing result is a degenerate implementation diagnostic, not evidence of calibration.

The synthetic evaluator alone accesses true outcome probabilities and unqueried future labels. It scores expected and realized post-promotion value on the untouched remainder of the stream, subtracting the switching charge once. This assumes policy actions do not alter outcomes; the result does not identify policy value under performative feedback. The repeated query/alpha/scenario grid is descriptive: cellwise intervals are not adjusted for choosing a method, and no winner is selected from the evaluation results.

## Results

| Scenario | Label cap | Query policy | Estimator | Monitoring rule | Alpha allocation | Promotion rate (95% CI) | Pointwise-null crossing (95% CI) | Mean oracle future net gain (95% t CI) | Mean labels / cap |
|---|---:|---|---|---|---|---:|---:|---:|---:|
| stationary | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| stationary | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| stationary | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| stationary | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| stationary | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| stationary | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| stationary | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| stationary | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| stationary | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| stationary | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| stationary | 20% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| stationary | 20% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| benign_nuisance | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| benign_nuisance | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| boundary_local_harm | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| boundary_local_harm | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.200 [0.118, 0.318] | 0.000 [0.000, 0.060] | 56.104 [26.482, 85.726] | 311.6 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.050 [0.017, 0.137] | 0.000 [0.000, 0.060] | 14.718 [-2.019, 31.454] | 311.6 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.100 [0.047, 0.201] | 0.000 [0.000, 0.060] | 30.250 [6.349, 54.151] | 311.6 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | positive_betting | rank | 0.133 [0.069, 0.242] | 0.000 [0.000, 0.060] | 39.432 [12.984, 65.880] | 311.6 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | hedged_positive | rank | 0.017 [0.003, 0.089] | 0.000 [0.000, 0.060] | 5.250 [-5.256, 15.756] | 311.6 / 320 |
| residual_variance | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| residual_variance | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| residual_variance | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| residual_variance | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| residual_variance | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| residual_variance | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| residual_variance | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| residual_variance | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| residual_variance | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| residual_variance | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| residual_variance | 20% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| residual_variance | 20% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| recurring_regimes | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| recurring_regimes | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.350 [0.242, 0.476] | 0.000 [0.000, 0.060] | 96.724 [61.947, 131.500] | 311.6 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.167 [0.093, 0.280] | 0.000 [0.000, 0.060] | 47.750 [19.671, 75.829] | 311.6 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.167 [0.093, 0.280] | 0.000 [0.000, 0.060] | 47.750 [19.671, 75.829] | 311.6 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | positive_betting | rank | 0.233 [0.144, 0.354] | 0.000 [0.000, 0.060] | 65.260 [34.096, 96.424] | 311.6 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | hedged_positive | rank | 0.117 [0.058, 0.222] | 0.000 [0.000, 0.060] | 33.285 [9.273, 57.297] | 311.6 / 320 |
| harmful_adaptation | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| harmful_adaptation | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.267 [0.171, 0.390] | 0.000 [0.000, 0.060] | 76.132 [43.163, 109.101] | 311.6 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.067 [0.026, 0.159] | 0.000 [0.000, 0.060] | 19.156 [0.474, 37.837] | 311.6 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.067 [0.026, 0.159] | 0.000 [0.000, 0.060] | 18.783 [0.466, 37.099] | 311.6 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | positive_betting | rank | 0.133 [0.069, 0.242] | 0.000 [0.000, 0.060] | 37.785 [12.669, 62.902] | 311.6 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| candidate_family_null | 10% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.4 / 160 |
| candidate_family_null | 20% | uniform | direct_ipw | fixed_mixture | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | fixed_mixture_half_alpha | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | predictable_kelly | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | pm_eb | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | positive_betting | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | hedged_positive | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.6 / 320 |

The `candidate_family_null` scenario makes every candidate an exact copy; a familywise certificate there is a direct implementation diagnostic. In other scenarios, the pointwise-null diagnostic counts any crossing for a candidate whose evaluator-known conditional mean net gain is nonpositive at every realized monitor covariate. Future harmful promotion is a separate metric: a candidate can pass its shadow test and later lose value after a regime change.

## Reproduction

`uv run shiftlab-dive-budgeted-promotion --seeds 60 --seed-offset 25102026 --n 3200 --device cuda --bound-mode global --monitoring-rules fixed_mixture fixed_mixture_half_alpha predictable_kelly pm_eb positive_betting hedged_positive --query-policies uniform --estimators direct_ipw --alpha-allocations rank --budget-rates 0.1 0.2 --output outputs/promotion_monitor_comparison_60`

Detailed seed-level rows, aggregate metrics, figure, configuration, environment, and hashes are stored with this report.

## Paired analysis at the 20% cap

The secondary contrasts resample matched seed pairs within the predeclared design cells. They include estimator, alpha-allocation, query-policy, and monitoring-rule comparisons when those dimensions vary. The 95% percentile intervals are descriptive and unadjusted across contrasts; the full table is in `metrics/budgeted_promotion_paired_contrasts.parquet`.

| Scenario | Contrast | Query | Monitoring rule | Mean paired net-gain difference (95% bootstrap CI) |
|---|---|---|---|---:|
| boundary_local_harm | fixed_mixture_half_alpha_minus_fixed_mixture | uniform | fixed_mixture_half_alpha | -41.386 [-68.588, -17.773] |
| boundary_local_harm | predictable_kelly_minus_fixed_mixture | uniform | predictable_kelly | -25.854 [-47.115, -8.305] |
| boundary_local_harm | pm_eb_minus_fixed_mixture | uniform | pm_eb | -56.104 [-85.779, -28.840] |
| boundary_local_harm | positive_betting_minus_fixed_mixture | uniform | positive_betting | -16.672 [-34.361, -3.746] |
| boundary_local_harm | hedged_positive_minus_fixed_mixture | uniform | hedged_positive | -50.854 [-79.430, -24.717] |
| recurring_regimes | fixed_mixture_half_alpha_minus_fixed_mixture | uniform | fixed_mixture_half_alpha | -48.974 [-76.402, -23.845] |
| recurring_regimes | predictable_kelly_minus_fixed_mixture | uniform | predictable_kelly | -48.974 [-76.287, -24.565] |
| recurring_regimes | pm_eb_minus_fixed_mixture | uniform | pm_eb | -96.724 [-131.713, -63.792] |
| recurring_regimes | positive_betting_minus_fixed_mixture | uniform | positive_betting | -31.463 [-54.992, -11.595] |
| recurring_regimes | hedged_positive_minus_fixed_mixture | uniform | hedged_positive | -63.438 [-93.426, -34.897] |
| harmful_adaptation | fixed_mixture_half_alpha_minus_fixed_mixture | uniform | fixed_mixture_half_alpha | -56.976 [-87.268, -28.949] |
| harmful_adaptation | predictable_kelly_minus_fixed_mixture | uniform | predictable_kelly | -57.349 [-87.381, -29.054] |
| harmful_adaptation | pm_eb_minus_fixed_mixture | uniform | pm_eb | -76.132 [-108.881, -45.939] |
| harmful_adaptation | positive_betting_minus_fixed_mixture | uniform | positive_betting | -38.347 [-65.433, -14.621] |
| harmful_adaptation | hedged_positive_minus_fixed_mixture | uniform | hedged_positive | -76.132 [-109.889, -45.856] |
