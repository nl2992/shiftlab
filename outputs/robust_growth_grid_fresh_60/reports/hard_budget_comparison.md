# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|720.74|711.08|0.987|374.6|0.971|0.0450|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|720.74|719.40|0.998|370.4|0.643|0.0369|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|720.74|719.50|0.998|363.9|0.625|0.0412|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|720.74|719.59|0.998|370.4|0.707|0.0151|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_mixture_growth_proxy|720.74|718.70|0.997|370.3|0.715|0.0152|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|720.74|719.34|0.998|362.7|0.761|0.0402|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|720.74|719.49|0.998|363.1|0.581|0.0395|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|720.74|707.76|0.982|514.6|0.986|0.0472|60/60|60|0.050 / 0.050|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|720.74|709.99|0.985|492.4|0.976|0.0486|60/60|60|0.050 / 0.050|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|720.74|708.64|0.983|470.2|0.964|0.0540|60/60|60|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|720.74|719.10|0.998|490.6|0.707|0.0151|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_mixture_growth_proxy|720.74|719.00|0.998|491.1|0.706|0.0163|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|720.74|707.13|0.981|470.6|0.986|0.0496|60/60|60|0.067 / 0.067|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|720.74|709.45|0.984|471.3|0.976|0.0514|60/60|60|0.067 / 0.067|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|720.74|707.76|0.982|514.6|0.986|0.0369|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|720.74|709.99|0.985|492.4|0.976|0.0404|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|720.74|713.75|0.990|474.4|0.951|0.0413|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|720.74|706.33|0.980|481.2|0.934|0.0115|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_mixture_growth_proxy|720.74|705.14|0.978|481.0|0.933|0.0117|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|720.74|707.13|0.981|470.6|0.986|0.0363|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|720.74|709.45|0.984|471.3|0.976|0.0408|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28702026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.2 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy --common-eprocess-bound --output outputs/robust_growth_grid_fresh_60`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0048 [-0.0022, 0.0114]|-8.26 [-12.24, -4.27]|11.9 [9.9, 13.9]|0.211 [0.204, 0.217]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|-0.0032 [-0.0106, 0.0040]|0.06 [-0.17, 0.30]|7.8 [6.6, 9.0]|-0.118 [-0.135, -0.102]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0010 [-0.0058, 0.0082]|0.16 [-0.10, 0.42]|1.2 [-0.1, 2.6]|-0.136 [-0.154, -0.118]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|exact_mixture_growth_proxy|-0.0250 [-0.0317, -0.0184]|0.25 [-0.01, 0.51]|7.7 [5.7, 9.8]|-0.053 [-0.075, -0.032]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|robust_mixture_growth_proxy|-0.0250 [-0.0316, -0.0183]|-0.64 [-2.07, 0.78]|7.6 [5.4, 9.8]|-0.046 [-0.068, -0.024]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|-0.0007 [-0.0076, 0.0065]|0.15 [-0.09, 0.40]|0.5 [-0.5, 1.4]|-0.179 [-0.193, -0.166]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|-0.0023 [-0.0101, 0.0049]|0.63 [-2.65, 3.90]|44.0 [41.5, 46.5]|-0.000 [-0.005, 0.004]|3 / 3 / 3 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|-0.0009 [-0.0086, 0.0064]|2.86 [-0.31, 6.03]|21.8 [18.5, 25.0]|-0.010 [-0.017, -0.004]|3 / 2 / 2 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0044 [-0.0038, 0.0129]|1.51 [-2.71, 5.73]|-0.4 [-4.0, 3.2]|-0.022 [-0.031, -0.012]|2 / 2 / 2 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0344 [-0.0431, -0.0258]|11.96 [7.67, 16.26]|20.0 [15.9, 24.1]|-0.278 [-0.293, -0.264]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|robust_mixture_growth_proxy|-0.0333 [-0.0420, -0.0246]|11.87 [7.57, 16.17]|20.5 [16.4, 24.6]|-0.280 [-0.294, -0.265]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|variance_proxy|0.0019 [-0.0053, 0.0085]|2.31 [-0.91, 5.53]|0.6 [-2.2, 3.5]|-0.010 [-0.017, -0.003]|4 / 2 / 2 / 60|0 / 2|0 / 2|0 / 60|
|stationary|cost_stabilized_proxy|0.0006 [-0.0041, 0.0053]|0.63 [-2.65, 3.90]|44.0 [41.5, 46.5]|-0.000 [-0.005, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0041 [-0.0031, 0.0111]|2.86 [-0.31, 6.03]|21.8 [18.5, 25.0]|-0.010 [-0.017, -0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0051 [-0.0010, 0.0112]|6.62 [2.77, 10.46]|3.8 [0.2, 7.4]|-0.035 [-0.046, -0.023]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|exact_mixture_growth_proxy|-0.0248 [-0.0309, -0.0188]|-0.81 [-8.11, 6.50]|10.6 [4.7, 16.4]|-0.052 [-0.070, -0.034]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|robust_mixture_growth_proxy|-0.0246 [-0.0305, -0.0186]|-1.99 [-9.95, 5.96]|10.4 [4.3, 16.5]|-0.053 [-0.072, -0.034]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0045 [-0.0009, 0.0098]|2.31 [-0.91, 5.53]|0.6 [-2.2, 3.5]|-0.010 [-0.017, -0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
