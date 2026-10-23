# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.
All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|719.76|712.39|0.990|375.0|0.966|0.0411|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|719.76|717.66|0.997|370.4|0.666|0.0413|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|719.76|718.49|0.998|364.5|0.636|0.0370|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|719.76|718.41|0.998|367.8|0.703|0.0175|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|719.76|718.54|0.998|361.8|0.750|0.0386|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|719.76|718.46|0.998|363.7|0.599|0.0411|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|719.76|711.69|0.989|519.1|0.983|0.0486|60/60|60|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|719.76|711.45|0.988|496.0|0.974|0.0529|60/60|60|0.050 / 0.050|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|719.76|709.04|0.985|473.1|0.947|0.0568|60/60|60|0.033 / 0.033|0.017 / 0.017|0.017 / 0.017|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|719.76|718.01|0.998|487.6|0.698|0.0160|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|719.76|708.91|0.985|472.1|0.979|0.0489|60/60|60|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|719.76|710.77|0.988|474.9|0.970|0.0540|60/60|60|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|719.76|711.69|0.989|519.1|0.983|0.0368|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|719.76|711.45|0.988|496.0|0.974|0.0397|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|719.76|714.68|0.993|476.7|0.933|0.0391|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|719.76|708.28|0.984|480.1|0.923|0.0139|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|719.76|708.91|0.985|472.1|0.979|0.0340|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|719.76|710.77|0.988|474.9|0.970|0.0397|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28302026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy --common-eprocess-bound --output outputs/exact_mixture_growth_matched_60`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0025 [-0.0051, 0.0101]|-6.16 [-9.06, -3.26]|13.2 [11.5, 14.8]|0.216 [0.209, 0.224]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|0.0027 [-0.0039, 0.0096]|-0.89 [-1.83, 0.05]|8.6 [7.4, 9.9]|-0.084 [-0.110, -0.058]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|-0.0016 [-0.0087, 0.0057]|-0.05 [-0.32, 0.22]|2.7 [1.3, 4.0]|-0.114 [-0.138, -0.090]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|exact_mixture_growth_proxy|-0.0211 [-0.0275, -0.0146]|-0.13 [-0.37, 0.11]|6.0 [4.1, 7.9]|-0.047 [-0.072, -0.023]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0024 [-0.0054, 0.0111]|-0.09 [-0.36, 0.19]|1.9 [0.7, 3.0]|-0.151 [-0.172, -0.129]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|-0.0003 [-0.0064, 0.0059]|2.78 [-0.83, 6.40]|47.0 [44.3, 49.6]|0.004 [-0.001, 0.009]|2 / 2 / 2 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0040 [-0.0036, 0.0120]|2.54 [-1.64, 6.71]|23.9 [20.1, 27.6]|-0.005 [-0.011, 0.001]|3 / 2 / 2 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0079 [-0.0021, 0.0170]|0.13 [-5.00, 5.25]|0.9 [-3.1, 4.9]|-0.033 [-0.045, -0.021]|2 / 1 / 1 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0329 [-0.0425, -0.0232]|9.10 [5.13, 13.08]|15.4 [12.1, 18.8]|-0.281 [-0.297, -0.264]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|variance_proxy|0.0051 [-0.0027, 0.0132]|1.86 [-2.37, 6.10]|2.8 [-0.9, 6.4]|-0.009 [-0.015, -0.003]|2 / 2 / 2 / 60|0 / 0|0 / 0|0 / 60|
|stationary|cost_stabilized_proxy|0.0029 [-0.0017, 0.0074]|2.78 [-0.83, 6.40]|47.0 [44.3, 49.6]|0.004 [-0.001, 0.009]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0058 [-0.0001, 0.0114]|2.54 [-1.64, 6.71]|23.9 [20.1, 27.6]|-0.005 [-0.011, 0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0051 [-0.0007, 0.0111]|5.77 [1.57, 9.98]|4.5 [0.9, 8.1]|-0.046 [-0.058, -0.034]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|exact_mixture_growth_proxy|-0.0201 [-0.0258, -0.0142]|-0.63 [-6.69, 5.44]|7.9 [3.4, 12.4]|-0.057 [-0.080, -0.033]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0058 [-0.0009, 0.0122]|1.86 [-2.37, 6.10]|2.8 [-0.9, 6.4]|-0.009 [-0.015, -0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
