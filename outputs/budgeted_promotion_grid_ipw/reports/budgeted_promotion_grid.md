# Repeated-candidate promotion under a hard label budget

This benchmark evaluates 7 scenarios with 60 independent seeds each on `cuda`. It crosses 3 predeclared query designs, 2 estimators, 3 candidate-level alpha allocations, and hard label caps (0.1, 0.2). Every query design and candidate gate sees the same seed-specific DGP; all candidate tests within one stream share queried labels. Each stream has 13 frozen candidates.

Candidates are trained on the training slice and ordered using the fully labeled validation slice. Validation also fixes the candidate alpha weights and the acquisition score model. Monitor labels are revealed only when queried. The three query designs are uniform, residual-variance weighting, and a decision-value heuristic; propensities remain predictable from the current covariates and pre-monitor fits, with a positive floor. For each budget level the same maximum number of labels is available to every query and alpha method. The monitor stops before the next event when no label remains affordable, so actual label counts never exceed the hard cap; realized counts and processed horizons are reported because policies need not spend the entire cap.

The grid compares prediction-powered `h_tk + I_t/q_t (Z_tk-h_tk)` with direct inverse-propensity `I_t Z_tk/q_t`, both shifted by the amortized switching charge. Here `Z` is incumbent cost minus candidate cost, `h` is a pre-monitor fitted expected-cost contrast, and the deployment horizon is `H`. With `|Z|,|h| <= M=max(FN,FP)`, the respective process bounds are `M(2/q_min-1)+k_switch/H` and `M/q_min+k_switch/H`. Each candidate receives a level from validation-rank spending, equal Bonferroni allocation, or validation-power weights. The weights are fixed before monitor outcomes and sum to at most alpha, giving a union-bound familywise guarantee if each bounded e-process's conditional-mean null and predictable-query assumptions hold. The report's pointwise-null candidate diagnostic classifies a candidate as null only when its evaluator-known conditional expected net gain is nonpositive at every realized monitor covariate. The global-null control replaces all candidates with incumbent copies; any certificate in that scenario is the direct familywise implementation diagnostic, not the proof.

The synthetic evaluator alone accesses true outcome probabilities and unqueried future labels. It scores expected and realized post-promotion value on the untouched remainder of the stream, subtracting the switching charge once. This assumes policy actions do not alter outcomes; the result does not identify policy value under performative feedback. The repeated query/alpha/scenario grid is descriptive: cellwise intervals are not adjusted for choosing a method, and no winner is selected from the evaluation results.

## Results

| Scenario | Label cap | Query policy | Estimator | Alpha allocation | Promote (95% CI) | Any pointwise-null candidate certified (95% CI) | Mean oracle future net gain (95% t CI) | Mean labels / cap |
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
| boundary_local_harm | 20% | uniform | direct_ipw | rank | 0.183 [0.106, 0.299] | 0.000 [0.000, 0.060] | 52.212 [22.968, 81.456] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | equal | 0.067 [0.026, 0.159] | 0.000 [0.000, 0.060] | 21.312 [0.391, 42.234] | 311.8 / 320 |
| boundary_local_harm | 20% | uniform | direct_ipw | validation_power | 0.117 [0.058, 0.222] | 0.000 [0.000, 0.060] | 35.743 [9.779, 61.708] | 311.8 / 320 |
| boundary_local_harm | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| boundary_local_harm | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | direct_ipw | rank | 0.200 [0.118, 0.318] | 0.000 [0.000, 0.060] | 58.469 [27.776, 89.163] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | direct_ipw | equal | 0.017 [0.003, 0.089] | 0.000 [0.000, 0.060] | 5.421 [-5.427, 16.270] | 313.9 / 320 |
| boundary_local_harm | 20% | variance | direct_ipw | validation_power | 0.067 [0.026, 0.159] | 0.000 [0.000, 0.060] | 19.402 [0.388, 38.416] | 313.9 / 320 |
| boundary_local_harm | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| boundary_local_harm | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | direct_ipw | rank | 0.217 [0.131, 0.336] | 0.000 [0.000, 0.060] | 66.083 [33.121, 99.045] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | direct_ipw | equal | 0.017 [0.003, 0.089] | 0.000 [0.000, 0.060] | 5.316 [-5.322, 15.954] | 312.0 / 320 |
| boundary_local_harm | 20% | decision_value | direct_ipw | validation_power | 0.067 [0.026, 0.159] | 0.000 [0.000, 0.060] | 20.748 [0.419, 41.078] | 312.0 / 320 |
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
| recurring_regimes | 20% | uniform | direct_ipw | rank | 0.250 [0.158, 0.372] | 0.000 [0.000, 0.060] | 79.701 [43.401, 116.000] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | equal | 0.133 [0.069, 0.242] | 0.000 [0.000, 0.060] | 43.029 [14.196, 71.862] | 311.8 / 320 |
| recurring_regimes | 20% | uniform | direct_ipw | validation_power | 0.150 [0.081, 0.261] | 0.000 [0.000, 0.060] | 48.120 [17.852, 78.387] | 311.8 / 320 |
| recurring_regimes | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| recurring_regimes | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 313.9 / 320 |
| recurring_regimes | 20% | variance | direct_ipw | rank | 0.233 [0.144, 0.354] | 0.000 [0.000, 0.060] | 72.599 [37.883, 107.314] | 313.9 / 320 |
| recurring_regimes | 20% | variance | direct_ipw | equal | 0.083 [0.036, 0.181] | 0.000 [0.000, 0.060] | 26.734 [3.524, 49.944] | 313.9 / 320 |
| recurring_regimes | 20% | variance | direct_ipw | validation_power | 0.100 [0.047, 0.201] | 0.000 [0.000, 0.060] | 32.718 [6.978, 58.458] | 313.9 / 320 |
| recurring_regimes | 10% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 10% | decision_value | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 153.3 / 160 |
| recurring_regimes | 20% | decision_value | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | direct_ipw | rank | 0.283 [0.185, 0.408] | 0.000 [0.000, 0.060] | 89.224 [52.016, 126.432] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | direct_ipw | equal | 0.033 [0.009, 0.114] | 0.000 [0.000, 0.060] | 11.238 [-4.667, 27.143] | 312.0 / 320 |
| recurring_regimes | 20% | decision_value | direct_ipw | validation_power | 0.083 [0.036, 0.181] | 0.000 [0.000, 0.060] | 25.610 [3.364, 47.857] | 312.0 / 320 |
| harmful_adaptation | 10% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 10% | uniform | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 154.2 / 160 |
| harmful_adaptation | 20% | uniform | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | rank | 0.217 [0.131, 0.336] | 0.000 [0.000, 0.060] | 62.961 [31.691, 94.230] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 311.8 / 320 |
| harmful_adaptation | 20% | uniform | direct_ipw | validation_power | 0.017 [0.003, 0.089] | 0.000 [0.000, 0.060] | 5.484 [-5.490, 16.458] | 311.8 / 320 |
| harmful_adaptation | 10% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | direct_ipw | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | direct_ipw | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 10% | variance | direct_ipw | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 155.2 / 160 |
| harmful_adaptation | 20% | variance | prediction_powered | rank | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | prediction_powered | equal | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | prediction_powered | validation_power | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.060] | 0.000 [0.000, 0.000] | 320.0 / 320 |
| harmful_adaptation | 20% | variance | direct_ipw | rank | 0.017 [0.003, 0.089] | 0.000 [0.000, 0.060] | 5.930 [-5.936, 17.796] | 320.0 / 320 |
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

`uv run shiftlab-dive-budgeted-promotion --seeds 60 --seed-offset 24102026 --n 3200 --device cuda --output outputs/budgeted_promotion_grid_ipw`

Detailed seed-level rows, aggregate metrics, figure, configuration, environment, and hashes are stored with this report.

## Paired analysis at the 20% cap

The secondary contrasts resample the 60 matched seed pairs and compare direct IPW with prediction-powered under rank spending, rank spending with equal and validation-power allocation under direct IPW, and adaptive query policies with uniform under direct IPW/rank. The 95% percentile intervals are descriptive and unadjusted across contrasts; the full 77-contrast table is in `metrics/budgeted_promotion_paired_contrasts.parquet`.

| Scenario | Contrast | Query | Mean paired net-gain difference (95% bootstrap CI) |
|---|---|---|---:|
| boundary_local_harm | direct_ipw_minus_prediction_powered | uniform | 52.212 [25.330, 82.944] |
| boundary_local_harm | direct_ipw_minus_prediction_powered | variance | 58.469 [30.092, 89.553] |
| boundary_local_harm | direct_ipw_minus_prediction_powered | decision_value | 66.083 [35.251, 99.205] |
| recurring_regimes | direct_ipw_minus_prediction_powered | uniform | 79.701 [45.268, 116.980] |
| recurring_regimes | direct_ipw_minus_prediction_powered | variance | 72.599 [40.449, 107.735] |
| recurring_regimes | direct_ipw_minus_prediction_powered | decision_value | 89.224 [53.992, 126.658] |
| harmful_adaptation | direct_ipw_minus_prediction_powered | uniform | 62.961 [33.781, 94.779] |
| harmful_adaptation | direct_ipw_minus_prediction_powered | variance | 5.930 [0.000, 17.790] |
| harmful_adaptation | direct_ipw_minus_prediction_powered | decision_value | 0.000 [0.000, 0.000] |
| boundary_local_harm | rank_minus_equal | uniform | 30.900 [7.960, 57.796] |
| boundary_local_harm | rank_minus_validation_power | uniform | 16.469 [-1.044, 38.268] |
| boundary_local_harm | rank_minus_equal | variance | 53.048 [25.873, 83.003] |
| boundary_local_harm | rank_minus_validation_power | variance | 39.068 [10.834, 69.066] |
| boundary_local_harm | rank_minus_equal | decision_value | 60.766 [31.204, 93.312] |
| boundary_local_harm | rank_minus_validation_power | decision_value | 45.334 [20.279, 74.751] |
| recurring_regimes | rank_minus_equal | uniform | 36.672 [4.029, 73.566] |
| recurring_regimes | rank_minus_validation_power | uniform | 31.581 [0.248, 64.440] |
| recurring_regimes | rank_minus_equal | variance | 45.865 [14.747, 80.742] |
| recurring_regimes | rank_minus_validation_power | variance | 39.881 [9.676, 71.685] |
| recurring_regimes | rank_minus_equal | decision_value | 77.986 [41.638, 117.664] |
| recurring_regimes | rank_minus_validation_power | decision_value | 63.614 [28.124, 100.531] |
| harmful_adaptation | rank_minus_equal | uniform | 62.961 [33.972, 93.675] |
| harmful_adaptation | rank_minus_validation_power | uniform | 57.476 [28.764, 88.125] |
| harmful_adaptation | rank_minus_equal | variance | 5.930 [0.000, 17.790] |
| harmful_adaptation | rank_minus_validation_power | variance | 5.930 [0.000, 17.790] |
| harmful_adaptation | rank_minus_equal | decision_value | 0.000 [0.000, 0.000] |
| harmful_adaptation | rank_minus_validation_power | decision_value | 0.000 [0.000, 0.000] |
| boundary_local_harm | variance_minus_uniform | variance | 6.257 [-25.185, 39.124] |
| boundary_local_harm | decision_value_minus_uniform | decision_value | 13.871 [-21.456, 50.717] |
| recurring_regimes | variance_minus_uniform | variance | -7.102 [-46.503, 33.526] |
| recurring_regimes | decision_value_minus_uniform | decision_value | 9.524 [-36.231, 55.854] |
| harmful_adaptation | variance_minus_uniform | variance | -57.031 [-91.202, -23.795] |
| harmful_adaptation | decision_value_minus_uniform | decision_value | -62.961 [-94.847, -33.849] |
