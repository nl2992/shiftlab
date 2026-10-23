# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.
All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported over evaluator-labeled alternatives and over onsets reached before budget stopping. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are listed separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|717.45|708.71|0.988|373.8|0.969|0.0507|0/0|6|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|benign_nuisance|cost_variance_proxy|717.45|716.19|0.998|369.4|0.652|0.0493|0/0|6|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|benign_nuisance|decision_value_proxy|717.45|716.04|0.998|362.8|0.626|0.0501|0/0|6|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|benign_nuisance|uniform_proxy|717.45|716.17|0.998|361.5|0.756|0.0434|0/0|6|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|benign_nuisance|variance_proxy|717.45|716.20|0.998|361.7|0.590|0.0511|0/0|6|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|stationary|cost_stabilized_proxy|717.45|703.23|0.980|511.8|0.984|0.0376|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|stationary|cost_variance_proxy|717.45|707.24|0.986|491.3|0.976|0.0418|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|stationary|decision_value_proxy|717.45|710.47|0.990|472.9|0.940|0.0402|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|stationary|uniform_proxy|717.45|704.44|0.982|469.3|0.983|0.0365|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|
|stationary|variance_proxy|717.45|706.57|0.985|470.5|0.974|0.0427|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / n/a|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20364022 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --scenarios stationary benign_nuisance --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy --common-eprocess-bound --output outputs/hard_budget_multiscale_null_controls_validated_60`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale detections / reached|Multiscale-only / fixed-only|Multiscale false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0073 [-0.0010, 0.0161]|-7.46 [-12.06, -2.85]|12.3 [10.1, 14.4]|0.213 [0.205, 0.221]|0 / 0 / 6|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|0.0059 [-0.0028, 0.0142]|0.01 [-0.26, 0.29]|7.9 [7.0, 8.9]|-0.103 [-0.119, -0.088]|0 / 0 / 6|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0067 [-0.0005, 0.0147]|-0.13 [-0.38, 0.12]|1.3 [0.2, 2.4]|-0.130 [-0.150, -0.109]|0 / 0 / 6|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0078 [-0.0007, 0.0160]|0.02 [-0.23, 0.27]|0.2 [-0.7, 1.1]|-0.165 [-0.179, -0.152]|0 / 0 / 6|0 / 0|0 / 60|
|stationary|cost_stabilized_proxy|0.0011 [-0.0040, 0.0062]|-1.21 [-4.71, 2.29]|42.5 [40.0, 45.0]|0.001 [-0.004, 0.005]|0 / 0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0053 [-0.0023, 0.0133]|2.80 [-0.90, 6.50]|22.0 [19.3, 24.6]|-0.008 [-0.013, -0.003]|0 / 0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0037 [-0.0028, 0.0102]|6.03 [1.67, 10.39]|3.6 [0.7, 6.6]|-0.043 [-0.057, -0.030]|0 / 0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0062 [-0.0007, 0.0134]|2.13 [-1.42, 5.69]|1.2 [-1.3, 3.7]|-0.009 [-0.014, -0.004]|0 / 0 / 0|0 / 0|0 / 60|
