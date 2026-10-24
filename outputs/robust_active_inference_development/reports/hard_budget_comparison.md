# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_variance_proxy|359.28|357.99|0.996|184.4|0.649|0.0620|0/0|5|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_proxy|359.28|357.80|0.996|182.2|0.688|0.0610|0/0|5|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|359.28|357.83|0.996|179.9|0.755|0.0742|0/0|5|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|359.28|357.83|0.996|180.7|0.585|0.0556|0/0|5|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|359.28|352.16|0.980|247.6|0.978|0.0957|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_proxy|359.28|350.98|0.977|240.0|0.977|0.0824|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|359.28|346.91|0.966|232.1|0.984|0.0884|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|359.28|351.79|0.979|236.3|0.977|0.0952|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|359.28|352.16|0.980|247.6|0.978|0.0590|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_proxy|359.28|350.98|0.977|240.0|0.977|0.0537|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|359.28|346.91|0.966|232.1|0.984|0.0550|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|359.28|351.79|0.979|236.3|0.977|0.0596|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 56110000 --n 3200 --d 16 --budget-rate 0.1 --q-min 0.05 --q-max 0.5 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --robust-active-inference-radius-fraction 0.5 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy cost_variance_proxy robust_active_inference_proxy --common-eprocess-bound --skip-figure --output outputs/robust_active_inference_development`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_variance_proxy|-0.0123 [-0.0242, -0.0008]|0.15 [-0.22, 0.53]|4.6 [3.7, 5.5]|-0.105 [-0.132, -0.078]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_proxy|-0.0133 [-0.0225, -0.0037]|-0.04 [-0.46, 0.38]|2.3 [1.6, 3.0]|-0.066 [-0.080, -0.053]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|variance_proxy|-0.0187 [-0.0339, -0.0039]|-0.01 [-0.37, 0.35]|0.9 [0.0, 1.7]|-0.170 [-0.195, -0.145]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|cost_variance_proxy|0.0072 [-0.0174, 0.0296]|5.26 [1.88, 8.63]|15.5 [12.2, 18.7]|-0.006 [-0.015, 0.002]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_proxy|-0.0060 [-0.0192, 0.0084]|4.07 [1.59, 6.56]|7.9 [5.9, 9.9]|-0.007 [-0.016, 0.001]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|variance_proxy|0.0067 [-0.0147, 0.0275]|4.89 [1.27, 8.50]|4.2 [1.3, 7.2]|-0.008 [-0.016, 0.001]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|cost_variance_proxy|0.0040 [-0.0090, 0.0164]|5.26 [1.88, 8.63]|15.5 [12.2, 18.7]|-0.006 [-0.015, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_proxy|-0.0014 [-0.0111, 0.0081]|4.07 [1.59, 6.56]|7.9 [5.9, 9.9]|-0.007 [-0.016, 0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|variance_proxy|0.0046 [-0.0079, 0.0162]|4.89 [1.27, 8.50]|4.2 [1.3, 7.2]|-0.008 [-0.016, 0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
