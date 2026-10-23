# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.
All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over all evaluator-labeled harmful streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Fixed detection all / reached|Multiscale detection all / reached|Fixed false escalation|Multiscale false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|717.45|703.23|0.980|511.8|0.984|0.0505|60/60|0.050 / 0.050|0.050 / 0.050|0.000|0.000|
|boundary_local_harm|cost_variance_proxy|717.45|707.24|0.986|491.3|0.976|0.0547|60/60|0.050 / 0.050|0.050 / 0.050|0.000|0.000|
|boundary_local_harm|decision_value_proxy|717.45|699.63|0.975|466.4|0.955|0.0596|60/60|0.067 / 0.067|0.050 / 0.050|0.000|0.000|
|boundary_local_harm|uniform_proxy|717.45|704.44|0.982|469.3|0.983|0.0517|60/60|0.083 / 0.083|0.067 / 0.067|0.000|0.000|
|boundary_local_harm|variance_proxy|717.45|706.57|0.985|470.5|0.974|0.0541|60/60|0.067 / 0.067|0.067 / 0.067|0.000|0.000|
|harmful_adaptation|cost_stabilized_proxy|717.45|703.23|0.980|511.8|0.984|0.0415|60/60|0.083 / 0.083|0.083 / 0.083|0.000|0.000|
|harmful_adaptation|cost_variance_proxy|717.45|707.24|0.986|491.3|0.976|0.0391|60/60|0.033 / 0.033|0.033 / 0.033|0.000|0.000|
|harmful_adaptation|decision_value_proxy|717.45|706.00|0.984|470.2|0.960|0.0366|60/60|0.000 / 0.000|0.000 / 0.000|0.000|0.000|
|harmful_adaptation|uniform_proxy|717.45|704.44|0.982|469.3|0.983|0.0367|60/60|0.050 / 0.050|0.050 / 0.050|0.000|0.000|
|harmful_adaptation|variance_proxy|717.45|706.57|0.985|470.5|0.974|0.0392|60/60|0.050 / 0.050|0.050 / 0.050|0.000|0.000|
|recurring_regimes|cost_stabilized_proxy|717.45|703.23|0.980|511.8|0.984|0.0442|60/60|0.033 / 0.033|0.017 / 0.017|0.000|0.000|
|recurring_regimes|cost_variance_proxy|717.45|707.24|0.986|491.3|0.976|0.0487|60/60|0.067 / 0.067|0.050 / 0.050|0.000|0.000|
|recurring_regimes|decision_value_proxy|717.45|693.61|0.967|462.2|0.972|0.0470|60/60|0.033 / 0.033|0.033 / 0.033|0.000|0.000|
|recurring_regimes|uniform_proxy|717.45|704.44|0.982|469.3|0.983|0.0409|60/60|0.067 / 0.067|0.067 / 0.067|0.000|0.000|
|recurring_regimes|variance_proxy|717.45|706.57|0.985|470.5|0.974|0.0476|60/60|0.083 / 0.083|0.067 / 0.067|0.000|0.000|
|residual_variance|cost_stabilized_proxy|717.45|703.23|0.980|511.8|0.984|0.0392|60/60|0.000 / 0.000|0.000 / 0.000|0.000|0.000|
|residual_variance|cost_variance_proxy|717.45|707.24|0.986|491.3|0.976|0.0378|60/60|0.000 / 0.000|0.000 / 0.000|0.000|0.000|
|residual_variance|decision_value_proxy|717.45|709.26|0.989|471.9|0.941|0.0390|60/60|0.000 / 0.000|0.000 / 0.000|0.000|0.000|
|residual_variance|uniform_proxy|717.45|704.44|0.982|469.3|0.983|0.0372|60/60|0.000 / 0.000|0.000 / 0.000|0.000|0.000|
|residual_variance|variance_proxy|717.45|706.57|0.985|470.5|0.974|0.0405|60/60|0.000 / 0.000|0.000 / 0.000|0.000|0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20364022 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --scenarios boundary_local_harm residual_variance recurring_regimes harmful_adaptation --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy --common-eprocess-bound --output outputs/hard_budget_multiscale_stakes_60`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale detections / reached|Multiscale-only / fixed-only|Multiscale false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|-0.0012 [-0.0082, 0.0064]|-1.21 [-4.71, 2.29]|42.5 [40.0, 45.0]|0.001 [-0.004, 0.005]|3 / 3 / 60|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0030 [-0.0058, 0.0119]|2.80 [-0.90, 6.50]|22.0 [19.3, 24.6]|-0.008 [-0.013, -0.003]|3 / 3 / 60|0 / 0|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0078 [-0.0012, 0.0173]|-4.81 [-10.42, 0.80]|-2.9 [-6.5, 0.7]|-0.028 [-0.040, -0.016]|4 / 3 / 60|0 / 1|0 / 60|
|boundary_local_harm|variance_proxy|0.0024 [-0.0055, 0.0103]|2.13 [-1.42, 5.69]|1.2 [-1.3, 3.7]|-0.009 [-0.014, -0.004]|4 / 4 / 60|0 / 0|0 / 60|
|harmful_adaptation|cost_stabilized_proxy|0.0048 [0.0015, 0.0080]|-1.21 [-4.71, 2.29]|42.5 [40.0, 45.0]|0.001 [-0.004, 0.005]|5 / 5 / 60|0 / 0|0 / 60|
|harmful_adaptation|cost_variance_proxy|0.0024 [-0.0030, 0.0076]|2.80 [-0.90, 6.50]|22.0 [19.3, 24.6]|-0.008 [-0.013, -0.003]|2 / 2 / 60|0 / 0|0 / 60|
|harmful_adaptation|decision_value_proxy|-0.0001 [-0.0080, 0.0078]|1.56 [-3.17, 6.28]|0.9 [-2.1, 4.0]|-0.023 [-0.034, -0.012]|0 / 0 / 60|0 / 0|0 / 60|
|harmful_adaptation|variance_proxy|0.0025 [-0.0021, 0.0076]|2.13 [-1.42, 5.69]|1.2 [-1.3, 3.7]|-0.009 [-0.014, -0.004]|3 / 3 / 60|0 / 0|0 / 60|
|recurring_regimes|cost_stabilized_proxy|0.0032 [-0.0049, 0.0115]|-1.21 [-4.71, 2.29]|42.5 [40.0, 45.0]|0.001 [-0.004, 0.005]|2 / 1 / 60|0 / 1|0 / 60|
|recurring_regimes|cost_variance_proxy|0.0078 [-0.0014, 0.0173]|2.80 [-0.90, 6.50]|22.0 [19.3, 24.6]|-0.008 [-0.013, -0.003]|4 / 3 / 60|0 / 1|0 / 60|
|recurring_regimes|decision_value_proxy|0.0061 [-0.0023, 0.0146]|-10.83 [-18.44, -3.23]|-7.1 [-12.1, -2.1]|-0.011 [-0.022, -0.001]|2 / 2 / 60|0 / 0|0 / 60|
|recurring_regimes|variance_proxy|0.0067 [-0.0034, 0.0172]|2.13 [-1.42, 5.69]|1.2 [-1.3, 3.7]|-0.009 [-0.014, -0.004]|5 / 4 / 60|0 / 1|0 / 60|
|residual_variance|cost_stabilized_proxy|0.0020 [-0.0033, 0.0074]|-1.21 [-4.71, 2.29]|42.5 [40.0, 45.0]|0.001 [-0.004, 0.005]|0 / 0 / 60|0 / 0|0 / 60|
|residual_variance|cost_variance_proxy|0.0006 [-0.0058, 0.0074]|2.80 [-0.90, 6.50]|22.0 [19.3, 24.6]|-0.008 [-0.013, -0.003]|0 / 0 / 60|0 / 0|0 / 60|
|residual_variance|decision_value_proxy|0.0018 [-0.0039, 0.0076]|4.82 [0.68, 8.96]|2.5 [-0.3, 5.4]|-0.043 [-0.056, -0.030]|0 / 0 / 60|0 / 0|0 / 60|
|residual_variance|variance_proxy|0.0033 [-0.0021, 0.0088]|2.13 [-1.42, 5.69]|1.2 [-1.3, 3.7]|-0.009 [-0.014, -0.004]|0 / 0 / 60|0 / 0|0 / 60|
