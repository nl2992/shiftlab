# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|722.13|713.91|0.989|377.0|0.959|0.0405|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|722.13|720.94|0.998|373.3|0.657|0.0422|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|722.13|720.67|0.998|366.1|0.632|0.0568|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|722.13|720.95|0.998|369.9|0.694|0.0179|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|722.13|721.01|0.998|363.7|0.759|0.0378|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|722.13|720.74|0.998|365.6|0.590|0.0402|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|722.13|708.77|0.982|515.8|0.977|0.0489|30/30|30|0.033 / 0.033|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|722.13|713.30|0.988|499.8|0.973|0.0511|30/30|30|0.067 / 0.067|0.067 / 0.067|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|722.13|705.00|0.976|473.6|0.965|0.0543|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|722.13|720.32|0.997|492.5|0.702|0.0154|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|722.13|704.58|0.976|469.0|0.977|0.0476|30/30|30|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|722.13|710.69|0.984|477.2|0.973|0.0521|30/30|30|0.100 / 0.100|0.100 / 0.100|0.100 / 0.100|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|722.13|708.77|0.982|515.8|0.977|0.0361|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|722.13|713.30|0.988|499.8|0.973|0.0364|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|722.13|714.87|0.990|479.5|0.942|0.0405|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|722.13|711.48|0.985|484.5|0.919|0.0125|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|722.13|704.58|0.976|469.0|0.977|0.0366|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|722.13|710.69|0.984|477.2|0.973|0.0362|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 28602026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy --common-eprocess-bound --output outputs/robust_growth_grid_development/runs/established_baselines`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0026 [-0.0055, 0.0107]|-7.09 [-11.76, -2.43]|13.2 [10.9, 15.6]|0.200 [0.187, 0.212]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|cost_variance_proxy|0.0044 [-0.0039, 0.0120]|-0.07 [-0.36, 0.22]|9.5 [7.8, 11.3]|-0.102 [-0.132, -0.072]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|decision_value_proxy|0.0189 [0.0062, 0.0332]|-0.33 [-0.72, 0.05]|2.4 [0.6, 4.2]|-0.128 [-0.161, -0.095]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|exact_mixture_growth_proxy|-0.0199 [-0.0283, -0.0116]|-0.06 [-0.37, 0.25]|6.1 [2.9, 9.4]|-0.066 [-0.096, -0.035]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|variance_proxy|0.0024 [-0.0079, 0.0120]|-0.26 [-0.59, 0.07]|1.9 [0.4, 3.3]|-0.169 [-0.194, -0.144]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|cost_stabilized_proxy|0.0012 [-0.0069, 0.0094]|4.19 [-0.40, 8.79]|46.8 [43.2, 50.3]|-0.000 [-0.007, 0.006]|1 / 0 / 0 / 30|0 / 1|0 / 1|0 / 30|
|boundary_local_harm|cost_variance_proxy|0.0035 [-0.0087, 0.0155]|8.72 [2.86, 14.59]|30.8 [26.4, 35.1]|-0.005 [-0.013, 0.004]|2 / 2 / 1 / 30|0 / 0|0 / 1|0 / 30|
|boundary_local_harm|decision_value_proxy|0.0067 [-0.0059, 0.0178]|0.43 [-10.06, 10.91]|4.5 [-2.5, 11.6]|-0.012 [-0.027, 0.002]|1 / 1 / 1 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0323 [-0.0446, -0.0209]|15.74 [7.91, 23.57]|23.5 [17.6, 29.3]|-0.276 [-0.297, -0.255]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|variance_proxy|0.0044 [-0.0089, 0.0165]|6.12 [1.13, 11.10]|8.2 [4.5, 11.9]|-0.004 [-0.012, 0.003]|3 / 3 / 3 / 30|0 / 0|0 / 0|0 / 30|
|stationary|cost_stabilized_proxy|-0.0005 [-0.0075, 0.0063]|4.19 [-0.40, 8.79]|46.8 [43.2, 50.3]|-0.000 [-0.007, 0.006]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|cost_variance_proxy|-0.0002 [-0.0077, 0.0070]|8.72 [2.86, 14.59]|30.8 [26.4, 35.1]|-0.005 [-0.013, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|decision_value_proxy|0.0038 [-0.0048, 0.0120]|10.29 [3.59, 16.99]|10.5 [5.1, 15.9]|-0.036 [-0.052, -0.020]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|exact_mixture_growth_proxy|-0.0242 [-0.0326, -0.0152]|6.90 [-1.57, 15.37]|15.4 [8.8, 22.1]|-0.058 [-0.088, -0.028]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|variance_proxy|-0.0004 [-0.0080, 0.0066]|6.12 [1.13, 11.10]|8.2 [4.5, 11.9]|-0.004 [-0.012, 0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
