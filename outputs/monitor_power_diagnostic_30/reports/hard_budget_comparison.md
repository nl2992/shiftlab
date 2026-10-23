# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|721.91|718.68|0.996|378.6|0.964|0.0429|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|721.91|720.57|0.998|373.3|0.702|0.0121|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|721.91|720.63|0.998|363.8|0.752|0.0368|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|721.91|710.68|0.984|517.0|0.982|0.0463|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|721.91|720.20|0.998|496.0|0.706|0.0124|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|721.91|710.01|0.984|472.2|0.978|0.0452|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_stabilized_proxy|721.91|710.68|0.984|517.0|0.982|0.0509|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|exact_mixture_growth_proxy|721.91|720.25|0.998|493.4|0.537|0.0208|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|721.91|710.01|0.984|472.2|0.978|0.0447|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|721.91|710.68|0.984|517.0|0.982|0.0400|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|721.91|699.91|0.969|482.5|0.908|0.0113|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|721.91|710.01|0.984|472.2|0.978|0.0353|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 39102026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.05 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.2 --scenarios stationary benign_nuisance boundary_local_harm recurring_regimes --methods uniform_proxy cost_stabilized_proxy exact_mixture_growth_proxy --common-eprocess-bound --output outputs/monitor_power_diagnostic_30`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0061 [-0.0049, 0.0185]|-1.95 [-3.96, 0.07]|14.8 [13.2, 16.5]|0.212 [0.200, 0.225]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|exact_mixture_growth_proxy|-0.0247 [-0.0332, -0.0156]|-0.06 [-0.41, 0.29]|9.5 [4.9, 14.1]|-0.050 [-0.086, -0.015]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|cost_stabilized_proxy|0.0012 [-0.0099, 0.0124]|0.67 [-3.30, 4.63]|44.8 [41.6, 48.0]|0.005 [-0.001, 0.011]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0328 [-0.0447, -0.0210]|10.19 [3.33, 17.05]|23.8 [18.5, 29.2]|-0.271 [-0.296, -0.246]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|cost_stabilized_proxy|0.0062 [-0.0020, 0.0157]|0.67 [-3.30, 4.63]|44.8 [41.6, 48.0]|0.005 [-0.001, 0.011]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|exact_mixture_growth_proxy|-0.0239 [-0.0374, -0.0103]|10.24 [3.44, 17.04]|21.3 [15.2, 27.3]|-0.441 [-0.471, -0.411]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|cost_stabilized_proxy|0.0046 [-0.0017, 0.0100]|0.67 [-3.30, 4.63]|44.8 [41.6, 48.0]|0.005 [-0.001, 0.011]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|exact_mixture_growth_proxy|-0.0240 [-0.0326, -0.0158]|-10.11 [-23.19, 2.98]|10.3 [0.3, 20.3]|-0.069 [-0.106, -0.033]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
