# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.
Exact mixture-growth acquisition uses adaptive weight 0.000 toward the per-event cost-neutral propensity. Its worst-case expected-spend drift bound is computed over tariff support [0.5, 2.5].
All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|721.24|710.77|0.985|375.9|0.969|0.0503|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|721.24|719.93|0.998|373.6|0.643|0.0492|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|721.24|719.96|0.998|366.3|0.613|0.0560|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|721.24|702.65|0.974|372.7|0.981|0.0493|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|721.24|720.06|0.998|363.9|0.757|0.0510|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|721.24|719.85|0.998|365.6|0.584|0.0542|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|721.24|708.92|0.983|517.0|0.982|0.0555|60/60|60|0.133 / 0.133|0.117 / 0.117|0.117 / 0.117|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|721.24|711.25|0.986|497.4|0.973|0.0524|60/60|60|0.050 / 0.050|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|721.24|704.77|0.977|471.5|0.949|0.0598|60/60|60|0.117 / 0.117|0.100 / 0.100|0.100 / 0.100|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|721.24|708.40|0.982|517.2|0.981|0.0548|60/60|60|0.133 / 0.133|0.117 / 0.117|0.117 / 0.117|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|721.24|704.98|0.978|470.6|0.982|0.0499|60/60|60|0.067 / 0.067|0.050 / 0.050|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|721.24|709.22|0.983|474.8|0.974|0.0564|60/60|60|0.050 / 0.050|0.050 / 0.050|0.033 / 0.033|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|721.24|708.92|0.983|517.0|0.982|0.0397|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|721.24|711.25|0.986|497.4|0.973|0.0420|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|721.24|713.84|0.990|477.0|0.932|0.0424|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|721.24|708.40|0.982|517.2|0.981|0.0392|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|721.24|704.98|0.978|470.6|0.982|0.0417|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|721.24|709.22|0.983|474.8|0.974|0.0416|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28502026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 0.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy --common-eprocess-bound --output outputs/cost_neutral_growth_grid_fresh_60`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|-0.0006 [-0.0068, 0.0062]|-9.29 [-13.40, -5.18]|12.0 [9.8, 14.2]|0.212 [0.205, 0.219]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|-0.0018 [-0.0119, 0.0069]|-0.13 [-0.35, 0.08]|9.7 [8.5, 10.8]|-0.114 [-0.134, -0.094]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0051 [-0.0075, 0.0165]|-0.10 [-0.36, 0.15]|2.4 [1.2, 3.7]|-0.143 [-0.164, -0.123]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|exact_mixture_growth_proxy|-0.0016 [-0.0088, 0.0065]|-17.41 [-23.14, -11.68]|8.8 [6.0, 11.6]|0.224 [0.218, 0.231]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0032 [-0.0081, 0.0134]|-0.21 [-0.47, 0.06]|1.7 [0.6, 2.8]|-0.173 [-0.190, -0.156]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|0.0056 [0.0001, 0.0113]|3.94 [0.14, 7.73]|46.4 [43.5, 49.3]|0.000 [-0.004, 0.005]|8 / 7 / 7 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0025 [-0.0046, 0.0099]|6.27 [2.22, 10.32]|26.9 [23.1, 30.7]|-0.009 [-0.015, -0.003]|3 / 3 / 3 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0098 [0.0003, 0.0190]|-0.21 [-8.00, 7.57]|0.9 [-4.7, 6.6]|-0.033 [-0.045, -0.020]|7 / 6 / 6 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|exact_mixture_growth_proxy|0.0049 [-0.0004, 0.0105]|3.42 [-0.33, 7.18]|46.6 [43.8, 49.5]|-0.000 [-0.005, 0.004]|8 / 7 / 7 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|variance_proxy|0.0065 [-0.0009, 0.0135]|4.24 [0.46, 8.02]|4.3 [0.7, 7.8]|-0.008 [-0.014, -0.001]|3 / 3 / 2 / 60|0 / 0|0 / 1|0 / 60|
|stationary|cost_stabilized_proxy|-0.0020 [-0.0054, 0.0013]|3.94 [0.14, 7.73]|46.4 [43.5, 49.3]|0.000 [-0.004, 0.005]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0003 [-0.0071, 0.0070]|6.27 [2.22, 10.32]|26.9 [23.1, 30.7]|-0.009 [-0.015, -0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0007 [-0.0070, 0.0084]|8.86 [2.96, 14.76]|6.5 [1.9, 11.0]|-0.050 [-0.060, -0.039]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|exact_mixture_growth_proxy|-0.0025 [-0.0062, 0.0012]|3.42 [-0.33, 7.18]|46.6 [43.8, 49.5]|-0.000 [-0.005, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|-0.0001 [-0.0075, 0.0066]|4.24 [0.46, 8.02]|4.3 [0.7, 7.8]|-0.008 [-0.014, -0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
