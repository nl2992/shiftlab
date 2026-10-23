# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

The primary comparison uses each method's actual minimum propensity in its fixed e-process increment bound. Uniform queries at 0.10 and therefore receives a tighter bound than adaptive methods that can query at 0.05. The common-bound sensitivity at [eprocess_bound_sensitivity.md](eprocess_bound_sensitivity.md) gives all methods `q_min=0.05`; it found 0/30 detections for every method despite all 30 boundary-harm onsets being reached. Do not attribute the primary 4-versus-0 difference solely to allocation.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over all evaluator-labeled harmful streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Detection all / reached|False escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|360.70|352.13|0.976|185.2|0.954|0.0702|1/1|0.000 / 0.000|0.000|
|benign_nuisance|cost_variance_proxy|360.70|359.34|0.996|185.3|0.647|0.0625|1/1|0.000 / 0.000|0.000|
|benign_nuisance|decision_value_proxy|360.70|359.39|0.996|182.0|0.665|0.0816|1/1|0.000 / 0.000|0.000|
|benign_nuisance|uniform_proxy|360.70|359.43|0.996|180.8|0.765|0.0573|1/1|0.000 / 0.000|0.000|
|benign_nuisance|variance_proxy|360.70|359.37|0.996|181.8|0.589|0.0712|1/1|0.000 / 0.000|0.000|
|boundary_local_harm|cost_stabilized_proxy|360.70|350.89|0.973|255.0|0.976|0.0756|30/30|0.000 / 0.000|0.000|
|boundary_local_harm|cost_variance_proxy|360.70|352.50|0.977|245.7|0.975|0.0939|30/30|0.000 / 0.000|0.000|
|boundary_local_harm|decision_value_proxy|360.70|351.10|0.974|234.0|0.957|0.1052|30/30|0.000 / 0.000|0.000|
|boundary_local_harm|uniform_proxy|360.70|349.90|0.970|233.2|0.978|0.0739|30/30|0.133 / 0.133|0.000|
|boundary_local_harm|variance_proxy|360.70|352.22|0.977|235.5|0.971|0.0959|30/30|0.000 / 0.000|0.000|
|stationary|cost_stabilized_proxy|360.70|350.89|0.973|255.0|0.976|0.0503|0/0|n/a / n/a|0.000|
|stationary|cost_variance_proxy|360.70|352.50|0.977|245.7|0.975|0.0618|0/0|n/a / n/a|0.000|
|stationary|decision_value_proxy|360.70|353.17|0.979|235.2|0.947|0.0725|0/0|n/a / n/a|0.000|
|stationary|uniform_proxy|360.70|349.90|0.970|233.2|0.978|0.0518|0/0|n/a / n/a|0.000|
|stationary|variance_proxy|360.70|352.22|0.977|235.5|0.971|0.0674|0/0|n/a / n/a|0.000|

## Full-horizon consistency check

Using the same per-seed query random numbers, the full-monitor uniform baseline produced five boundary-harm alarms. Four occurred before hard-budget stopping and are reproduced at identical event indices; the fifth occurred at event 2,279 on a stream stopped at event 2,232, so it is correctly censored by the budget horizon.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --n 3200 --device cuda --output outputs/hard_budget_pilot_30`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Harm detected / reached / harmful|False escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0129 [-0.0012, 0.0280]|-7.31 [-11.72, -2.89]|4.4 [2.1, 6.7]|0.188 [0.172, 0.205]|0 / 1 / 1|0 / 30|
|benign_nuisance|cost_variance_proxy|0.0052 [-0.0070, 0.0146]|-0.10 [-0.43, 0.24]|4.5 [3.3, 5.7]|-0.119 [-0.141, -0.096]|0 / 1 / 1|0 / 30|
|benign_nuisance|decision_value_proxy|0.0243 [-0.0019, 0.0475]|-0.04 [-0.43, 0.35]|1.3 [0.3, 2.2]|-0.100 [-0.131, -0.070]|0 / 1 / 1|0 / 30|
|benign_nuisance|variance_proxy|0.0139 [0.0005, 0.0248]|-0.06 [-0.50, 0.37]|1.0 [-0.0, 2.1]|-0.176 [-0.199, -0.152]|0 / 1 / 1|0 / 30|
|boundary_local_harm|cost_stabilized_proxy|0.0018 [-0.0059, 0.0083]|0.99 [-2.39, 4.37]|21.7 [19.1, 24.4]|-0.002 [-0.009, 0.005]|0 / 30 / 30|0 / 30|
|boundary_local_harm|cost_variance_proxy|0.0201 [0.0050, 0.0348]|2.60 [-0.60, 5.80]|12.4 [9.2, 15.7]|-0.003 [-0.015, 0.008]|0 / 30 / 30|0 / 30|
|boundary_local_harm|decision_value_proxy|0.0314 [0.0090, 0.0516]|1.20 [-4.03, 6.42]|0.8 [-3.4, 5.0]|-0.021 [-0.036, -0.006]|0 / 30 / 30|0 / 30|
|boundary_local_harm|variance_proxy|0.0220 [0.0032, 0.0385]|2.32 [-0.96, 5.60]|2.2 [-0.8, 5.3]|-0.007 [-0.020, 0.006]|0 / 30 / 30|0 / 30|
|stationary|cost_stabilized_proxy|-0.0014 [-0.0078, 0.0066]|0.99 [-2.39, 4.37]|21.7 [19.1, 24.4]|-0.002 [-0.009, 0.005]|0 / 0 / 0|0 / 30|
|stationary|cost_variance_proxy|0.0100 [-0.0019, 0.0216]|2.60 [-0.60, 5.80]|12.4 [9.2, 15.7]|-0.003 [-0.015, 0.008]|0 / 0 / 0|0 / 30|
|stationary|decision_value_proxy|0.0207 [0.0066, 0.0354]|3.27 [-1.64, 8.18]|2.0 [-1.9, 5.9]|-0.031 [-0.046, -0.016]|0 / 0 / 0|0 / 30|
|stationary|variance_proxy|0.0157 [0.0018, 0.0270]|2.32 [-0.96, 5.60]|2.2 [-0.8, 5.3]|-0.007 [-0.020, 0.006]|0 / 0 / 0|0 / 30|
