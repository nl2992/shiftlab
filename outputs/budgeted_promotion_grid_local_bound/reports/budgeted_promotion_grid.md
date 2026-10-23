# Repeated-candidate promotion under a hard label budget

This benchmark evaluates 7 scenarios with 60 independent seeds each on `cuda`. It crosses 3 predeclared query designs, 2 estimators, 3 candidate-level alpha allocations, and hard label caps (0.1, 0.2). Every query design and candidate gate sees the same seed-specific DGP; all candidate tests within one stream share queried labels. Each stream has 13 frozen candidates.

Candidates are trained on the training slice and ordered using the fully labeled validation slice. Validation also fixes the candidate alpha weights and the acquisition score model. Monitor labels are revealed only when queried. The three query designs are uniform, residual-variance weighting, and a decision-value heuristic; propensities remain predictable from the current covariates and pre-monitor fits, with a positive floor. For each budget level the same maximum number of labels is available to every query and alpha method. The monitor stops before the next event when no label remains affordable, so actual label counts never exceed the hard cap; realized counts and processed horizons are reported because policies need not spend the entire cap.

The grid compares prediction-powered `h_tk + I_t/q_t (Z_tk-h_tk)` with direct inverse-propensity `I_t Z_tk/q_t`, both shifted by the amortized switching charge. Here `Z` is incumbent cost minus candidate cost, `h` is a pre-monitor fitted expected-cost contrast, and the deployment horizon is `H`. With `|Z|,|h| <= M=max(FN,FP)`, the global-mode bounds are `M(2/q_min-1)+k_switch/H` and `M/q_min+k_switch/H`; local-mode bounds are computed per candidate and event from estimator support. Each candidate receives a level from validation-rank spending, equal Bonferroni allocation, or validation-power weights, fixed before monitor outcomes and summing to at most alpha. Decision-local bounds support only the pointwise conditional null given current covariates. Rejecting that null does not certify positive average net gain, so a crossing in this mode is a conditional-null diagnostic and is not a promotion authorization. The global-null control replaces all candidates with incumbent copies; its zero-crossing result is a degenerate implementation diagnostic, not evidence of calibration.

The synthetic evaluator alone accesses true outcome probabilities and unqueried future labels. It scores expected and realized post-promotion value on the untouched remainder of the stream, subtracting the switching charge once. This assumes policy actions do not alter outcomes; the result does not identify policy value under performative feedback. The repeated query/alpha/scenario grid is descriptive: cellwise intervals are not adjusted for choosing a method, and no winner is selected from the evaluation results.

## Results

| Scenario | Label cap | Query policy | Estimator | Alpha allocation | E-process crossing (95% CI) | Pointwise-null candidate crossing (95% CI) | Mean oracle future net gain (95% t CI) | Mean labels / cap |
|---|---:|---|---|---|---:|---:|---:|---:|
| stationary | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| stationary | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| stationary | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| stationary | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| stationary | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| stationary | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| stationary | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| stationary | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| stationary | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| stationary | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| stationary | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| stationary | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| stationary | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| stationary | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| stationary | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| stationary | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| stationary | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| stationary | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| stationary | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| stationary | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| stationary | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| stationary | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| stationary | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| stationary | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| stationary | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| benign_nuisance | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| benign_nuisance | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| benign_nuisance | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| benign_nuisance | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| benign_nuisance | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| benign_nuisance | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| benign_nuisance | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| benign_nuisance | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| benign_nuisance | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 151.5 / 160 |
| benign_nuisance | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 151.5 / 160 |
| benign_nuisance | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 151.5 / 160 |
| benign_nuisance | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 151.5 / 160 |
| benign_nuisance | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 151.5 / 160 |
| benign_nuisance | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 151.5 / 160 |
| benign_nuisance | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.8 / 320 |
| benign_nuisance | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.8 / 320 |
| benign_nuisance | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.8 / 320 |
| benign_nuisance | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.8 / 320 |
| benign_nuisance | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.8 / 320 |
| benign_nuisance | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.8 / 320 |
| benign_nuisance | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 150.2 / 160 |
| benign_nuisance | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 150.2 / 160 |
| benign_nuisance | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 150.2 / 160 |
| benign_nuisance | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 150.2 / 160 |
| benign_nuisance | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 150.2 / 160 |
| benign_nuisance | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 150.2 / 160 |
| benign_nuisance | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 310.9 / 320 |
| benign_nuisance | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 310.9 / 320 |
| benign_nuisance | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 310.9 / 320 |
| benign_nuisance | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 310.9 / 320 |
| benign_nuisance | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 310.9 / 320 |
| benign_nuisance | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 310.9 / 320 |
| boundary_local_harm | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| boundary_local_harm | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| residual_variance | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| residual_variance | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| residual_variance | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| residual_variance | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| residual_variance | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| residual_variance | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| residual_variance | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| residual_variance | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| residual_variance | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| residual_variance | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| residual_variance | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| residual_variance | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| residual_variance | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| residual_variance | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| residual_variance | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| residual_variance | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| residual_variance | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| residual_variance | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| residual_variance | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| residual_variance | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| residual_variance | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| residual_variance | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| residual_variance | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| residual_variance | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| residual_variance | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| recurring_regimes | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| harmful_adaptation | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 159.4 / 160 |
| harmful_adaptation | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 159.4 / 160 |
| harmful_adaptation | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 159.4 / 160 |
| harmful_adaptation | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 159.4 / 160 |
| harmful_adaptation | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 159.4 / 160 |
| harmful_adaptation | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 159.4 / 160 |
| harmful_adaptation | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| candidate_family_null | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| candidate_family_null | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| candidate_family_null | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| candidate_family_null | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| candidate_family_null | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| candidate_family_null | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| candidate_family_null | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| candidate_family_null | 20% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| candidate_family_null | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 156.3 / 160 |
| candidate_family_null | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 156.3 / 160 |
| candidate_family_null | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 156.3 / 160 |
| candidate_family_null | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 156.3 / 160 |
| candidate_family_null | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 156.3 / 160 |
| candidate_family_null | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 156.3 / 160 |
| candidate_family_null | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.4 / 320 |
| candidate_family_null | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.4 / 320 |
| candidate_family_null | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.4 / 320 |
| candidate_family_null | 20% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.4 / 320 |
| candidate_family_null | 20% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.4 / 320 |
| candidate_family_null | 20% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.4 / 320 |
| candidate_family_null | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.8 / 160 |
| candidate_family_null | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.8 / 160 |
| candidate_family_null | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.8 / 160 |
| candidate_family_null | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.8 / 160 |
| candidate_family_null | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.8 / 160 |
| candidate_family_null | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.8 / 160 |
| candidate_family_null | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.5 / 320 |
| candidate_family_null | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.5 / 320 |
| candidate_family_null | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.5 / 320 |
| candidate_family_null | 20% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.5 / 320 |
| candidate_family_null | 20% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.5 / 320 |
| candidate_family_null | 20% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 314.5 / 320 |

The `candidate_family_null` scenario makes every candidate an exact copy; a familywise certificate there is a direct implementation diagnostic. In other scenarios, the pointwise-null diagnostic counts any certified candidate whose evaluator-known conditional mean net gain is nonpositive for every realized monitor covariate. Future harmful promotion is a separate metric: a candidate can pass its shadow test and later lose value after a regime change.

## Reproduction

`uv run shiftlab-dive-budgeted-promotion --seeds 60 --seed-offset 24102026 --n 3200 --device cuda --bound-mode decision_local --output outputs/budgeted_promotion_grid_local_bound`

Detailed seed-level rows, aggregate metrics, figure, configuration, environment, and hashes are stored with this report.

## Paired analysis at the 20% cap

The secondary contrasts resample the 60 matched seed pairs and compare direct IPW with prediction-powered under rank spending, rank spending with equal and validation-power allocation under direct IPW, and adaptive query policies with uniform under direct IPW/rank. The 95% percentile intervals are descriptive and unadjusted across contrasts; the full 77-contrast table is in `metrics/budgeted_promotion_paired_contrasts.parquet`.

| Scenario | Contrast | Query | Mean paired net-gain difference (95% bootstrap CI) |
|---|---|---|---:|
| boundary_local_harm | direct_ipw_minus_prediction_powered | uniform | 0.000 [0.000, 0.000] |
| boundary_local_harm | direct_ipw_minus_prediction_powered | variance | 0.000 [0.000, 0.000] |
| boundary_local_harm | direct_ipw_minus_prediction_powered | decision_value | 0.000 [0.000, 0.000] |
| recurring_regimes | direct_ipw_minus_prediction_powered | uniform | 0.000 [0.000, 0.000] |
| recurring_regimes | direct_ipw_minus_prediction_powered | variance | 0.000 [0.000, 0.000] |
| recurring_regimes | direct_ipw_minus_prediction_powered | decision_value | 0.000 [0.000, 0.000] |
| harmful_adaptation | direct_ipw_minus_prediction_powered | uniform | 0.000 [0.000, 0.000] |
| harmful_adaptation | direct_ipw_minus_prediction_powered | variance | 0.000 [0.000, 0.000] |
| harmful_adaptation | direct_ipw_minus_prediction_powered | decision_value | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_equal | uniform | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_validation_power | uniform | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_equal | variance | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_validation_power | variance | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_equal | decision_value | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_validation_power | decision_value | 0.000 [0.000, 0.000] |
| recurring_regimes | rank_minus_equal | uniform | 0.000 [0.000, 0.000] |
| recurring_regimes | rank_minus_validation_power | uniform | 0.000 [0.000, 0.000] |
| recurring_regimes | rank_minus_equal | variance | 0.000 [0.000, 0.000] |
| recurring_regimes | rank_minus_validation_power | variance | 0.000 [0.000, 0.000] |
| recurring_regimes | rank_minus_equal | decision_value | 0.000 [0.000, 0.000] |
| recurring_regimes | rank_minus_validation_power | decision_value | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_equal | uniform | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_validation_power | uniform | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_equal | variance | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_validation_power | variance | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_equal | decision_value | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_validation_power | decision_value | 0.000 [0.000, 0.000] |
| boundary_local_harm | variance_minus_uniform | variance | 0.000 [0.000, 0.000] |
| boundary_local_harm | decision_value_minus_uniform | decision_value | 0.000 [0.000, 0.000] |
| recurring_regimes | variance_minus_uniform | variance | 0.000 [0.000, 0.000] |
| recurring_regimes | decision_value_minus_uniform | decision_value | 0.000 [0.000, 0.000] |
| harmful_adaptation | variance_minus_uniform | variance | 0.000 [0.000, 0.000] |
| harmful_adaptation | decision_value_minus_uniform | decision_value | 0.000 [0.000, 0.000] |

## Global versus decision-local bounds

The global run uses the weaker history-conditional average-gain null. The local run's crossings test a pointwise conditional null and cannot certify positive aggregate net benefit. Therefore these paired results are a power diagnostic only, not a comparison of valid promotion gates for the same aggregate estimand. Intervals are paired t intervals over 60 independent seeds and unadjusted across the full grid.

| Scenario | Query | Global crossing | Local crossing | Local minus global (95% CI) | Mean local/global bound ratio |
|---|---|---:|---:|---:|---:|
| stationary | uniform | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.105 |
| stationary | variance | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.093 |
| stationary | decision_value | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.093 |
| benign_nuisance | uniform | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.107 |
| benign_nuisance | variance | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.093 |
| benign_nuisance | decision_value | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.093 |
| boundary_local_harm | uniform | 0.183 | 0.000 | -0.183 [-0.284, -0.083] | 0.105 |
| boundary_local_harm | variance | 0.200 | 0.000 | -0.200 [-0.304, -0.096] | 0.093 |
| boundary_local_harm | decision_value | 0.217 | 0.000 | -0.217 [-0.324, -0.109] | 0.093 |
| residual_variance | uniform | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.105 |
| residual_variance | variance | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.093 |
| residual_variance | decision_value | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.093 |
| recurring_regimes | uniform | 0.250 | 0.000 | -0.250 [-0.363, -0.137] | 0.105 |
| recurring_regimes | variance | 0.233 | 0.000 | -0.233 [-0.344, -0.123] | 0.093 |
| recurring_regimes | decision_value | 0.283 | 0.000 | -0.283 [-0.401, -0.166] | 0.093 |
| harmful_adaptation | uniform | 0.217 | 0.000 | -0.217 [-0.324, -0.109] | 0.115 |
| harmful_adaptation | variance | 0.017 | 0.000 | -0.017 [-0.050, 0.017] | 0.077 |
| harmful_adaptation | decision_value | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.077 |
| candidate_family_null | uniform | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.000 |
| candidate_family_null | variance | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.000 |
| candidate_family_null | decision_value | 0.000 | 0.000 | 0.000 [0.000, 0.000] | 0.000 |

The complete 252-cell paired table is `metrics/budgeted_promotion_bound_mode_contrasts.parquet`. The local test crossed zero times in all 15,120 local rows, while respecting every pathwise label cap. Its mean event bound was 6.9% of the global bound. This is a negative transfer from the one-candidate calibration: tighter support bounds alone did not create useful promotion power in a family with sparse action disagreement.
