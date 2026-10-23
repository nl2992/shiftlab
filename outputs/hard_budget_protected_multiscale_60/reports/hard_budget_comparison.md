# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.
All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over all evaluator-labeled harmful streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|721.59|709.81|0.984|375.3|0.965|0.0466|7/7|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|721.59|720.39|0.998|372.9|0.656|0.0391|7/7|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|721.59|720.23|0.998|365.9|0.632|0.0445|7/7|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|721.59|720.34|0.998|364.1|0.757|0.0380|7/7|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|721.59|720.18|0.998|364.4|0.594|0.0402|7/7|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|721.59|707.19|0.980|516.3|0.980|0.0478|60/60|0.050 / 0.050|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|721.59|708.72|0.982|497.4|0.975|0.0511|60/60|0.050 / 0.050|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|721.59|702.74|0.974|472.8|0.970|0.0573|60/60|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|721.59|704.62|0.977|470.6|0.981|0.0482|60/60|0.067 / 0.067|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|721.59|707.06|0.980|474.5|0.978|0.0550|60/60|0.083 / 0.083|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|harmful_adaptation|cost_stabilized_proxy|721.59|707.19|0.980|516.3|0.980|0.0315|60/60|0.017 / 0.017|0.017 / 0.017|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|cost_variance_proxy|721.59|708.72|0.982|497.4|0.975|0.0345|60/60|0.017 / 0.017|0.017 / 0.017|0.017 / 0.017|0.000 / 0.000 / 0.000|
|harmful_adaptation|decision_value_proxy|721.59|705.37|0.978|474.2|0.974|0.0361|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|uniform_proxy|721.59|704.62|0.977|470.6|0.981|0.0287|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|variance_proxy|721.59|707.06|0.980|474.5|0.978|0.0326|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_stabilized_proxy|721.59|707.19|0.980|516.3|0.980|0.0603|60/60|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_variance_proxy|721.59|708.72|0.982|497.4|0.975|0.0645|60/60|0.083 / 0.083|0.067 / 0.067|0.050 / 0.050|0.000 / 0.000 / 0.000|
|recurring_regimes|decision_value_proxy|721.59|693.55|0.961|466.2|0.986|0.0675|60/60|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|721.59|704.62|0.977|470.6|0.981|0.0565|60/60|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|recurring_regimes|variance_proxy|721.59|707.06|0.980|474.5|0.978|0.0682|60/60|0.050 / 0.050|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|residual_variance|cost_stabilized_proxy|721.59|707.19|0.980|516.3|0.980|0.0406|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|cost_variance_proxy|721.59|708.72|0.982|497.4|0.975|0.0409|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|decision_value_proxy|721.59|710.76|0.985|477.4|0.953|0.0462|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|uniform_proxy|721.59|704.62|0.977|470.6|0.981|0.0369|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|variance_proxy|721.59|707.06|0.980|474.5|0.978|0.0440|60/60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|721.59|707.19|0.980|516.3|0.980|0.0372|1/1|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|721.59|708.72|0.982|497.4|0.975|0.0366|1/1|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|721.59|710.54|0.985|477.2|0.952|0.0418|1/1|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|721.59|704.62|0.977|470.6|0.981|0.0350|1/1|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|721.59|707.06|0.980|474.5|0.978|0.0386|1/1|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20365022 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --scenarios stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy --common-eprocess-bound --output outputs/hard_budget_protected_multiscale_60`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0086 [0.0008, 0.0162]|-10.53 [-15.24, -5.82]|11.2 [9.0, 13.4]|0.208 [0.201, 0.216]|0 / 0 / 0 / 7|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|0.0011 [-0.0049, 0.0075]|0.05 [-0.21, 0.30]|8.8 [7.5, 10.2]|-0.101 [-0.125, -0.078]|0 / 0 / 0 / 7|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0065 [-0.0021, 0.0147]|-0.11 [-0.31, 0.09]|1.8 [0.6, 3.1]|-0.125 [-0.146, -0.104]|0 / 0 / 0 / 7|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0022 [-0.0049, 0.0093]|-0.16 [-0.40, 0.07]|0.4 [-0.8, 1.6]|-0.163 [-0.182, -0.144]|0 / 0 / 0 / 7|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|-0.0005 [-0.0073, 0.0065]|2.57 [-0.30, 5.44]|45.7 [43.2, 48.2]|-0.002 [-0.006, 0.003]|3 / 3 / 3 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0029 [-0.0065, 0.0119]|4.10 [0.40, 7.80]|26.8 [22.6, 30.9]|-0.006 [-0.012, -0.001]|3 / 2 / 2 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0090 [-0.0013, 0.0193]|-1.88 [-9.04, 5.27]|2.2 [-3.0, 7.4]|-0.011 [-0.021, -0.001]|4 / 4 / 4 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|variance_proxy|0.0067 [-0.0016, 0.0152]|2.44 [-1.68, 6.55]|3.9 [0.2, 7.6]|-0.004 [-0.010, 0.002]|5 / 3 / 3 / 60|0 / 2|0 / 2|0 / 60|
|harmful_adaptation|cost_stabilized_proxy|0.0028 [-0.0008, 0.0064]|2.57 [-0.30, 5.44]|45.7 [43.2, 48.2]|-0.002 [-0.006, 0.003]|1 / 1 / 0 / 60|0 / 0|0 / 1|0 / 60|
|harmful_adaptation|cost_variance_proxy|0.0058 [0.0005, 0.0109]|4.10 [0.40, 7.80]|26.8 [22.6, 30.9]|-0.006 [-0.012, -0.001]|1 / 1 / 1 / 60|0 / 0|0 / 0|0 / 60|
|harmful_adaptation|decision_value_proxy|0.0074 [0.0015, 0.0135]|0.75 [-6.07, 7.57]|3.6 [-1.2, 8.4]|-0.007 [-0.017, 0.003]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|harmful_adaptation|variance_proxy|0.0039 [-0.0012, 0.0090]|2.44 [-1.68, 6.55]|3.9 [0.2, 7.6]|-0.004 [-0.010, 0.002]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_stabilized_proxy|0.0038 [-0.0039, 0.0112]|2.57 [-0.30, 5.44]|45.7 [43.2, 48.2]|-0.002 [-0.006, 0.003]|4 / 4 / 4 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_variance_proxy|0.0080 [-0.0017, 0.0168]|4.10 [0.40, 7.80]|26.8 [22.6, 30.9]|-0.006 [-0.012, -0.001]|5 / 4 / 3 / 60|0 / 1|0 / 2|0 / 60|
|recurring_regimes|decision_value_proxy|0.0110 [0.0028, 0.0194]|-11.07 [-19.68, -2.46]|-4.4 [-11.0, 2.1]|0.005 [-0.004, 0.013]|2 / 2 / 2 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|variance_proxy|0.0117 [0.0029, 0.0202]|2.44 [-1.68, 6.55]|3.9 [0.2, 7.6]|-0.004 [-0.010, 0.002]|3 / 3 / 3 / 60|0 / 0|0 / 0|0 / 60|
|residual_variance|cost_stabilized_proxy|0.0037 [-0.0004, 0.0080]|2.57 [-0.30, 5.44]|45.7 [43.2, 48.2]|-0.002 [-0.006, 0.003]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|residual_variance|cost_variance_proxy|0.0041 [-0.0011, 0.0093]|4.10 [0.40, 7.80]|26.8 [22.6, 30.9]|-0.006 [-0.012, -0.001]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|residual_variance|decision_value_proxy|0.0093 [0.0019, 0.0161]|6.14 [-0.15, 12.44]|6.8 [2.2, 11.5]|-0.029 [-0.038, -0.019]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|residual_variance|variance_proxy|0.0071 [0.0007, 0.0131]|2.44 [-1.68, 6.55]|3.9 [0.2, 7.6]|-0.004 [-0.010, 0.002]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|stationary|cost_stabilized_proxy|0.0021 [-0.0023, 0.0067]|2.57 [-0.30, 5.44]|45.7 [43.2, 48.2]|-0.002 [-0.006, 0.003]|0 / 0 / 0 / 1|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0016 [-0.0031, 0.0064]|4.10 [0.40, 7.80]|26.8 [22.6, 30.9]|-0.006 [-0.012, -0.001]|0 / 0 / 0 / 1|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0067 [-0.0010, 0.0144]|5.92 [-0.58, 12.41]|6.6 [1.8, 11.4]|-0.029 [-0.040, -0.019]|0 / 0 / 0 / 1|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0036 [-0.0018, 0.0086]|2.44 [-1.68, 6.55]|3.9 [0.2, 7.6]|-0.004 [-0.010, 0.002]|0 / 0 / 0 / 1|0 / 0|0 / 0|0 / 60|
