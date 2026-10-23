# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|360.15|352.00|0.977|186.1|0.962|0.0697|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|360.15|358.90|0.997|185.3|0.653|0.0580|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|360.15|358.74|0.996|181.3|0.659|0.0678|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|360.15|358.00|0.994|184.4|0.760|0.0363|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_mixture_growth_proxy|360.15|358.04|0.994|185.0|0.740|0.0347|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|360.15|358.95|0.997|180.8|0.754|0.0572|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|360.15|358.82|0.996|181.2|0.589|0.0632|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|360.15|349.73|0.971|254.2|0.973|0.0952|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|360.15|350.44|0.973|244.4|0.966|0.0954|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|360.15|347.66|0.965|232.1|0.963|0.0934|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|360.15|358.37|0.995|247.3|0.782|0.0280|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_mixture_growth_proxy|360.15|358.36|0.995|247.8|0.753|0.0308|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|360.15|348.79|0.968|232.6|0.974|0.0859|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|360.15|351.20|0.975|234.5|0.964|0.0933|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_stabilized_proxy|360.15|349.73|0.971|254.2|0.973|0.0710|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_variance_proxy|360.15|350.44|0.973|244.4|0.966|0.0801|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|decision_value_proxy|360.15|346.45|0.962|231.0|0.964|0.0810|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|exact_mixture_growth_proxy|360.15|358.40|0.995|249.0|0.655|0.0299|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|robust_mixture_growth_proxy|360.15|358.27|0.995|249.3|0.612|0.0325|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|360.15|348.79|0.968|232.6|0.974|0.0660|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|variance_proxy|360.15|351.20|0.975|234.5|0.964|0.0813|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|360.15|349.73|0.971|254.2|0.973|0.0549|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|360.15|350.44|0.973|244.4|0.966|0.0573|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|360.15|351.87|0.977|234.9|0.952|0.0646|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|360.15|350.04|0.972|240.5|0.928|0.0221|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_mixture_growth_proxy|360.15|352.96|0.980|243.1|0.913|0.0250|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|360.15|348.79|0.968|232.6|0.974|0.0522|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|360.15|351.20|0.975|234.5|0.964|0.0599|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28802026 --n 3200 --d 16 --budget-rate 0.1 --q-min 0.05 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.2 --scenarios stationary benign_nuisance boundary_local_harm recurring_regimes --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy --common-eprocess-bound --output outputs/budget_frontier_60/budget_0p10`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0126 [0.0001, 0.0253]|-6.95 [-9.88, -4.02]|5.3 [3.8, 6.7]|0.208 [0.199, 0.217]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|0.0009 [-0.0081, 0.0109]|-0.05 [-0.30, 0.20]|4.5 [3.7, 5.3]|-0.101 [-0.120, -0.081]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0107 [-0.0019, 0.0235]|-0.20 [-0.46, 0.05]|0.5 [-0.3, 1.3]|-0.094 [-0.116, -0.072]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|exact_mixture_growth_proxy|-0.0208 [-0.0339, -0.0082]|-0.95 [-2.69, 0.79]|3.6 [1.9, 5.3]|0.006 [-0.024, 0.037]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|robust_mixture_growth_proxy|-0.0225 [-0.0360, -0.0089]|-0.90 [-2.39, 0.58]|4.2 [2.6, 5.8]|-0.014 [-0.047, 0.020]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0061 [-0.0083, 0.0208]|-0.12 [-0.36, 0.11]|0.4 [-0.3, 1.1]|-0.165 [-0.181, -0.149]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|0.0092 [-0.0050, 0.0214]|0.94 [-1.47, 3.35]|21.7 [19.9, 23.4]|-0.001 [-0.006, 0.003]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0094 [0.0012, 0.0179]|1.66 [-1.12, 4.43]|11.9 [9.5, 14.3]|-0.008 [-0.016, -0.000]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0074 [-0.0019, 0.0171]|-1.13 [-4.98, 2.72]|-0.5 [-3.4, 2.4]|-0.012 [-0.021, -0.002]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0579 [-0.0773, -0.0386]|9.59 [6.26, 12.91]|14.8 [12.2, 17.3]|-0.192 [-0.213, -0.171]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|robust_mixture_growth_proxy|-0.0552 [-0.0755, -0.0352]|9.57 [6.24, 12.90]|15.2 [12.6, 17.9]|-0.222 [-0.241, -0.202]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|variance_proxy|0.0073 [-0.0032, 0.0185]|2.41 [-0.44, 5.27]|2.0 [-0.3, 4.3]|-0.010 [-0.018, -0.002]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_stabilized_proxy|0.0050 [-0.0040, 0.0149]|0.94 [-1.47, 3.35]|21.7 [19.9, 23.4]|-0.001 [-0.006, 0.003]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_variance_proxy|0.0141 [0.0005, 0.0279]|1.66 [-1.12, 4.43]|11.9 [9.5, 14.3]|-0.008 [-0.016, -0.000]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|decision_value_proxy|0.0150 [0.0043, 0.0258]|-2.33 [-7.05, 2.38]|-1.5 [-4.9, 1.9]|-0.010 [-0.021, 0.001]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|exact_mixture_growth_proxy|-0.0361 [-0.0500, -0.0228]|9.62 [6.30, 12.93]|16.4 [13.8, 19.1]|-0.319 [-0.346, -0.292]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|robust_mixture_growth_proxy|-0.0335 [-0.0480, -0.0196]|9.49 [6.16, 12.81]|16.7 [14.1, 19.4]|-0.363 [-0.390, -0.335]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|variance_proxy|0.0153 [0.0018, 0.0295]|2.41 [-0.44, 5.27]|2.0 [-0.3, 4.3]|-0.010 [-0.018, -0.002]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|stationary|cost_stabilized_proxy|0.0027 [-0.0025, 0.0081]|0.94 [-1.47, 3.35]|21.7 [19.9, 23.4]|-0.001 [-0.006, 0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0052 [-0.0031, 0.0133]|1.66 [-1.12, 4.43]|11.9 [9.5, 14.3]|-0.008 [-0.016, -0.000]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0124 [0.0031, 0.0216]|3.08 [-0.40, 6.56]|2.4 [-0.4, 5.1]|-0.023 [-0.035, -0.011]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|exact_mixture_growth_proxy|-0.0301 [-0.0414, -0.0187]|1.26 [-3.90, 6.41]|7.9 [4.5, 11.3]|-0.047 [-0.069, -0.025]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|robust_mixture_growth_proxy|-0.0272 [-0.0383, -0.0163]|4.17 [-0.69, 9.03]|10.6 [7.4, 13.8]|-0.062 [-0.085, -0.039]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0077 [0.0000, 0.0153]|2.41 [-0.44, 5.27]|2.0 [-0.3, 4.3]|-0.010 [-0.018, -0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
