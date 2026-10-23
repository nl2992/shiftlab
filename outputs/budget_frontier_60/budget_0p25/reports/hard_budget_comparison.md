# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|900.39|892.77|0.992|470.7|0.970|0.0384|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|900.39|899.06|0.999|465.9|0.646|0.0384|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|900.39|898.92|0.998|456.8|0.618|0.0444|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|900.39|898.92|0.998|465.0|0.737|0.0109|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_mixture_growth_proxy|900.39|898.11|0.997|464.7|0.737|0.0110|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|900.39|899.10|0.999|453.6|0.758|0.0415|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|900.39|899.08|0.999|456.0|0.582|0.0396|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|900.39|885.95|0.984|644.5|0.985|0.0412|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|900.39|889.67|0.988|622.8|0.970|0.0509|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|900.39|877.03|0.974|585.4|0.943|0.0618|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|900.39|898.65|0.998|614.9|0.713|0.0150|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_mixture_growth_proxy|900.39|898.64|0.998|614.9|0.713|0.0149|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|900.39|885.28|0.983|589.0|0.982|0.0419|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|900.39|887.62|0.986|594.3|0.968|0.0520|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_stabilized_proxy|900.39|885.95|0.984|644.5|0.985|0.0392|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_variance_proxy|900.39|889.67|0.988|622.8|0.970|0.0416|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|decision_value_proxy|900.39|854.85|0.950|569.0|0.968|0.0572|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|exact_mixture_growth_proxy|900.39|898.82|0.998|614.1|0.534|0.0190|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|robust_mixture_growth_proxy|900.39|898.86|0.998|614.2|0.534|0.0190|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|900.39|885.28|0.983|589.0|0.982|0.0419|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|variance_proxy|900.39|887.62|0.986|594.3|0.968|0.0434|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|900.39|885.95|0.984|644.5|0.985|0.0312|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|900.39|889.67|0.988|622.8|0.970|0.0362|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|900.39|890.98|0.990|596.0|0.920|0.0424|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|900.39|867.16|0.963|594.4|0.926|0.0102|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_mixture_growth_proxy|900.39|867.47|0.964|594.8|0.926|0.0104|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|900.39|885.28|0.983|589.0|0.982|0.0354|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|900.39|887.62|0.986|594.3|0.968|0.0358|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28802026 --n 3200 --d 16 --budget-rate 0.25 --q-min 0.05 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.2 --scenarios stationary benign_nuisance boundary_local_harm recurring_regimes --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy --common-eprocess-bound --output outputs/budget_frontier_60/budget_0p25`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|-0.0031 [-0.0094, 0.0029]|-6.33 [-9.64, -3.02]|17.1 [15.5, 18.8]|0.212 [0.205, 0.220]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|-0.0030 [-0.0100, 0.0041]|-0.04 [-0.31, 0.23]|12.3 [10.6, 14.1]|-0.111 [-0.130, -0.092]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0030 [-0.0053, 0.0114]|-0.18 [-0.61, 0.24]|3.2 [1.3, 5.0]|-0.139 [-0.165, -0.114]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|exact_mixture_growth_proxy|-0.0305 [-0.0363, -0.0242]|-0.18 [-0.50, 0.14]|11.4 [7.8, 15.0]|-0.020 [-0.047, 0.006]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|robust_mixture_growth_proxy|-0.0305 [-0.0365, -0.0241]|-0.99 [-2.90, 0.93]|11.1 [7.3, 14.9]|-0.021 [-0.047, 0.005]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|-0.0019 [-0.0093, 0.0053]|-0.02 [-0.24, 0.20]|2.4 [0.9, 4.0]|-0.175 [-0.191, -0.159]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|-0.0007 [-0.0050, 0.0038]|0.66 [-3.26, 4.58]|55.5 [52.7, 58.3]|0.003 [-0.001, 0.007]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0090 [0.0022, 0.0156]|4.38 [-0.55, 9.32]|33.8 [28.5, 39.0]|-0.011 [-0.018, -0.005]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0199 [0.0113, 0.0285]|-8.25 [-18.79, 2.28]|-3.7 [-10.7, 3.3]|-0.038 [-0.052, -0.025]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0269 [-0.0342, -0.0195]|13.36 [8.25, 18.47]|25.8 [21.5, 30.1]|-0.268 [-0.285, -0.251]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|robust_mixture_growth_proxy|-0.0271 [-0.0344, -0.0199]|13.36 [8.25, 18.47]|25.8 [21.5, 30.2]|-0.269 [-0.285, -0.252]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|variance_proxy|0.0100 [0.0033, 0.0166]|2.34 [-2.45, 7.13]|5.2 [0.6, 9.9]|-0.013 [-0.020, -0.007]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_stabilized_proxy|-0.0027 [-0.0066, 0.0013]|0.66 [-3.26, 4.58]|55.5 [52.7, 58.3]|0.003 [-0.001, 0.007]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_variance_proxy|-0.0004 [-0.0060, 0.0054]|4.38 [-0.55, 9.32]|33.8 [28.5, 39.0]|-0.011 [-0.018, -0.005]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|decision_value_proxy|0.0153 [0.0051, 0.0251]|-30.44 [-43.29, -17.58]|-20.0 [-28.8, -11.2]|-0.014 [-0.025, -0.003]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|exact_mixture_growth_proxy|-0.0229 [-0.0299, -0.0159]|13.54 [8.40, 18.67]|25.0 [20.5, 29.5]|-0.448 [-0.468, -0.427]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|robust_mixture_growth_proxy|-0.0229 [-0.0301, -0.0158]|13.58 [8.48, 18.68]|25.2 [20.7, 29.7]|-0.448 [-0.468, -0.428]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|variance_proxy|0.0014 [-0.0053, 0.0082]|2.34 [-2.45, 7.13]|5.2 [0.6, 9.9]|-0.013 [-0.020, -0.007]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|stationary|cost_stabilized_proxy|-0.0042 [-0.0084, -0.0001]|0.66 [-3.26, 4.58]|55.5 [52.7, 58.3]|0.003 [-0.001, 0.007]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0009 [-0.0051, 0.0068]|4.38 [-0.55, 9.32]|33.8 [28.5, 39.0]|-0.011 [-0.018, -0.005]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0070 [-0.0005, 0.0145]|5.69 [-1.31, 12.70]|6.9 [1.3, 12.5]|-0.061 [-0.075, -0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|exact_mixture_growth_proxy|-0.0251 [-0.0308, -0.0192]|-18.13 [-32.65, -3.61]|5.3 [-4.3, 14.9]|-0.056 [-0.081, -0.031]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|robust_mixture_growth_proxy|-0.0250 [-0.0307, -0.0190]|-17.82 [-32.08, -3.55]|5.7 [-3.7, 15.2]|-0.056 [-0.080, -0.031]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0004 [-0.0044, 0.0051]|2.34 [-2.45, 7.13]|5.2 [0.6, 9.9]|-0.013 [-0.020, -0.007]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
