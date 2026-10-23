# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap.

All methods use the common configured propensity floor for their e-process bound.

The e-process is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Fixed detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Fixed / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|720.31|711.16|0.987|375.5|0.967|0.0448|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|720.31|718.89|0.998|372.7|0.648|0.0404|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|720.31|718.99|0.998|365.3|0.620|0.0496|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|exact_mixture_growth_proxy|720.31|718.98|0.998|373.9|0.696|0.0125|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_mixture_growth_proxy|720.31|718.70|0.998|373.9|0.703|0.0119|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|720.31|719.07|0.998|362.8|0.759|0.0430|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|720.31|718.96|0.998|364.4|0.583|0.0445|0/0|3|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|720.31|706.78|0.981|514.5|0.983|0.0484|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|720.31|709.34|0.985|496.7|0.968|0.0594|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|720.31|702.05|0.975|468.5|0.953|0.0643|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|exact_mixture_growth_proxy|720.31|718.59|0.998|492.8|0.700|0.0167|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_mixture_growth_proxy|720.31|718.57|0.998|492.9|0.698|0.0165|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|720.31|705.30|0.979|469.7|0.980|0.0457|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|720.31|707.90|0.983|473.5|0.966|0.0575|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_stabilized_proxy|720.31|706.78|0.981|514.5|0.983|0.0407|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_variance_proxy|720.31|709.34|0.985|496.7|0.968|0.0495|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|decision_value_proxy|720.31|682.54|0.948|454.9|0.963|0.0553|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|exact_mixture_growth_proxy|720.31|718.50|0.997|492.2|0.517|0.0211|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|robust_mixture_growth_proxy|720.31|718.50|0.997|492.5|0.516|0.0210|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|720.31|705.30|0.979|469.7|0.980|0.0477|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|variance_proxy|720.31|707.90|0.983|473.5|0.966|0.0512|60/60|60|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|720.31|706.78|0.981|514.5|0.983|0.0359|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|720.31|709.34|0.985|496.7|0.968|0.0384|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|720.31|710.29|0.986|474.7|0.929|0.0460|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|exact_mixture_growth_proxy|720.31|705.58|0.980|483.4|0.899|0.0112|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_mixture_growth_proxy|720.31|705.65|0.980|483.8|0.898|0.0111|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|720.31|705.30|0.979|469.7|0.980|0.0389|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|720.31|707.90|0.983|473.5|0.966|0.0399|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

This run evaluates each e-process only through its hard-budget stopping time and does not recompute a full-horizon monitor. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers; the earlier 30-seed pilot consistency check is recorded in the Paper 3 research log.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation comparison under a finite spend cap, not an intervention controller and not a new sequential-test theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. The e-process validity still requires the documented bounded-increment conditional-mean null and predictable query probabilities. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 28802026 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.05 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.2 --scenarios stationary benign_nuisance boundary_local_harm recurring_regimes --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy exact_mixture_growth_proxy robust_mixture_growth_proxy --common-eprocess-bound --output outputs/budget_frontier_60/budget_0p20`.

![Hard-budget tradeoff](../figures/hard_budget_tradeoff.png)

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Fixed / multiscale / protected detections / reached|Multiscale-only / fixed-only|Protected-only / fixed-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0018 [-0.0064, 0.0102]|-7.91 [-11.78, -4.04]|12.7 [10.7, 14.6]|0.208 [0.200, 0.216]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|-0.0026 [-0.0120, 0.0073]|-0.17 [-0.44, 0.10]|9.9 [8.4, 11.4]|-0.110 [-0.129, -0.091]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|decision_value_proxy|0.0065 [-0.0069, 0.0198]|-0.07 [-0.32, 0.18]|2.5 [1.0, 3.9]|-0.139 [-0.159, -0.119]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|exact_mixture_growth_proxy|-0.0305 [-0.0378, -0.0232]|-0.08 [-0.39, 0.22]|11.1 [8.1, 14.0]|-0.063 [-0.087, -0.038]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|robust_mixture_growth_proxy|-0.0312 [-0.0384, -0.0239]|-0.37 [-1.03, 0.30]|11.1 [8.1, 14.1]|-0.056 [-0.082, -0.030]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0015 [-0.0085, 0.0114]|-0.10 [-0.34, 0.14]|1.6 [0.3, 2.8]|-0.176 [-0.191, -0.160]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|0.0027 [-0.0033, 0.0094]|1.48 [-2.20, 5.16]|44.8 [42.0, 47.5]|0.004 [-0.002, 0.009]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0137 [0.0046, 0.0230]|4.04 [0.44, 7.64]|27.0 [23.0, 30.9]|-0.012 [-0.018, -0.005]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|decision_value_proxy|0.0186 [0.0092, 0.0276]|-3.25 [-11.48, 4.97]|-1.2 [-6.8, 4.3]|-0.027 [-0.039, -0.015]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|exact_mixture_growth_proxy|-0.0290 [-0.0382, -0.0199]|13.29 [8.58, 18.00]|23.0 [19.2, 26.9]|-0.280 [-0.297, -0.263]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|robust_mixture_growth_proxy|-0.0292 [-0.0386, -0.0202]|13.27 [8.55, 17.99]|23.2 [19.3, 27.1]|-0.281 [-0.298, -0.265]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|variance_proxy|0.0118 [0.0053, 0.0182]|2.60 [-1.39, 6.59]|3.8 [-0.0, 7.6]|-0.014 [-0.021, -0.007]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_stabilized_proxy|-0.0071 [-0.0134, -0.0008]|1.48 [-2.20, 5.16]|44.8 [42.0, 47.5]|0.004 [-0.002, 0.009]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|cost_variance_proxy|0.0018 [-0.0075, 0.0110]|4.04 [0.44, 7.64]|27.0 [23.0, 30.9]|-0.012 [-0.018, -0.005]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|decision_value_proxy|0.0076 [-0.0032, 0.0175]|-22.76 [-33.58, -11.95]|-14.8 [-21.9, -7.8]|-0.017 [-0.028, -0.006]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|exact_mixture_growth_proxy|-0.0267 [-0.0342, -0.0190]|13.19 [8.50, 17.89]|22.5 [18.3, 26.7]|-0.463 [-0.485, -0.441]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|robust_mixture_growth_proxy|-0.0267 [-0.0341, -0.0190]|13.20 [8.48, 17.91]|22.8 [18.7, 26.9]|-0.463 [-0.485, -0.442]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|recurring_regimes|variance_proxy|0.0035 [-0.0057, 0.0123]|2.60 [-1.39, 6.59]|3.8 [-0.0, 7.6]|-0.014 [-0.021, -0.007]|0 / 0 / 0 / 60|0 / 0|0 / 0|0 / 60|
|stationary|cost_stabilized_proxy|-0.0030 [-0.0070, 0.0011]|1.48 [-2.20, 5.16]|44.8 [42.0, 47.5]|0.004 [-0.002, 0.009]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|-0.0004 [-0.0064, 0.0058]|4.04 [0.44, 7.64]|27.0 [23.0, 30.9]|-0.012 [-0.018, -0.005]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|decision_value_proxy|0.0072 [-0.0011, 0.0152]|4.99 [-1.18, 11.17]|5.0 [0.1, 9.9]|-0.051 [-0.065, -0.037]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|exact_mixture_growth_proxy|-0.0277 [-0.0337, -0.0215]|0.28 [-8.84, 9.39]|13.6 [7.4, 19.8]|-0.081 [-0.108, -0.055]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|robust_mixture_growth_proxy|-0.0277 [-0.0337, -0.0216]|0.35 [-8.48, 9.18]|14.0 [8.0, 20.0]|-0.082 [-0.108, -0.056]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0011 [-0.0042, 0.0064]|2.60 [-1.39, 6.59]|3.8 [-0.0, 7.6]|-0.014 [-0.021, -0.007]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
