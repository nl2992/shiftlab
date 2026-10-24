# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_variance_proxy|719.19|717.89|0.998|371.4|0.666|0.0469|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0|719.19|717.89|0.998|371.4|0.666|0.0469|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0.1|719.19|717.75|0.998|370.7|0.672|0.0493|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0.25|719.19|717.98|0.998|369.1|0.684|0.0472|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0.5|719.19|717.83|0.998|367.4|0.697|0.0425|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r1|719.19|718.01|0.998|366.5|0.707|0.0421|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r2|719.19|718.03|0.998|365.6|0.718|0.0404|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|719.19|717.85|0.998|363.7|0.746|0.0394|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|719.19|717.73|0.998|364.7|0.600|0.0448|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|719.19|713.00|0.991|497.2|0.968|0.0542|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0|719.19|713.00|0.991|497.2|0.968|0.0542|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0.1|719.19|712.94|0.991|493.5|0.967|0.0494|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0.25|719.19|712.32|0.990|489.0|0.969|0.0514|30/30|30|0.100 / 0.100|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0.5|719.19|710.16|0.988|484.1|0.970|0.0495|30/30|30|0.100 / 0.100|0.100 / 0.100|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r1|719.19|708.35|0.985|480.0|0.969|0.0470|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r2|719.19|707.56|0.984|477.2|0.971|0.0442|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|719.19|706.33|0.982|471.8|0.973|0.0455|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|719.19|712.37|0.991|476.2|0.966|0.0505|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|719.19|713.00|0.991|497.2|0.968|0.0344|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0|719.19|713.00|0.991|497.2|0.968|0.0344|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0.1|719.19|712.94|0.991|493.5|0.967|0.0312|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0.25|719.19|712.32|0.990|489.0|0.969|0.0302|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0.5|719.19|710.16|0.988|484.1|0.970|0.0292|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r1|719.19|708.35|0.985|480.0|0.969|0.0294|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r2|719.19|707.56|0.984|477.2|0.971|0.0259|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|719.19|706.33|0.982|471.8|0.973|0.0280|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|719.19|712.37|0.991|476.2|0.966|0.0321|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 56300000 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --robust-active-inference-radius-fraction 0.5 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy cost_variance_proxy robust_active_inference_r0 robust_active_inference_r0.1 robust_active_inference_r0.25 robust_active_inference_r0.5 robust_active_inference_r1 robust_active_inference_r2 --common-eprocess-bound --skip-figure --output outputs/robust_active_inference_radius_budget20_development`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_variance_proxy|0.0075 [-0.0004, 0.0155]|0.04 [-0.28, 0.36]|7.7 [6.0, 9.4]|-0.080 [-0.109, -0.051]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0|0.0075 [-0.0004, 0.0152]|0.04 [-0.28, 0.36]|7.7 [6.0, 9.4]|-0.080 [-0.109, -0.051]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0.1|0.0099 [0.0031, 0.0164]|-0.10 [-0.47, 0.27]|7.0 [5.4, 8.6]|-0.074 [-0.098, -0.050]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0.25|0.0078 [0.0023, 0.0130]|0.13 [-0.24, 0.50]|5.4 [4.2, 6.6]|-0.061 [-0.079, -0.043]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0.5|0.0030 [-0.0022, 0.0077]|-0.01 [-0.41, 0.38]|3.8 [2.9, 4.7]|-0.049 [-0.062, -0.036]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r1|0.0027 [-0.0020, 0.0071]|0.17 [-0.27, 0.60]|2.8 [2.1, 3.5]|-0.038 [-0.048, -0.029]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r2|0.0010 [-0.0029, 0.0050]|0.18 [-0.19, 0.56]|1.9 [1.3, 2.5]|-0.028 [-0.035, -0.021]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|variance_proxy|0.0054 [-0.0023, 0.0121]|-0.12 [-0.50, 0.27]|1.0 [-0.5, 2.6]|-0.146 [-0.169, -0.122]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|cost_variance_proxy|0.0087 [-0.0050, 0.0212]|6.67 [0.42, 12.92]|25.4 [20.6, 30.2]|-0.005 [-0.014, 0.004]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0|0.0087 [-0.0053, 0.0213]|6.67 [0.42, 12.92]|25.4 [20.6, 30.2]|-0.005 [-0.014, 0.004]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0.1|0.0039 [-0.0058, 0.0124]|6.61 [0.64, 12.59]|21.7 [17.1, 26.4]|-0.006 [-0.014, 0.002]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0.25|0.0059 [-0.0039, 0.0148]|5.99 [0.80, 11.19]|17.2 [13.3, 21.2]|-0.004 [-0.010, 0.002]|3 / 2 / 2 / 30|0 / 1|0 / 1|0 / 30|
|boundary_local_harm|robust_active_inference_r0.5|0.0040 [-0.0064, 0.0136]|3.83 [-0.44, 8.10]|12.3 [9.2, 15.3]|-0.003 [-0.009, 0.003]|3 / 3 / 2 / 30|0 / 0|0 / 1|0 / 30|
|boundary_local_harm|robust_active_inference_r1|0.0015 [-0.0069, 0.0091]|2.02 [-0.82, 4.87]|8.2 [5.9, 10.5]|-0.004 [-0.009, 0.002]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r2|-0.0013 [-0.0053, 0.0027]|1.23 [-0.89, 3.34]|5.4 [3.8, 7.1]|-0.002 [-0.006, 0.002]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|variance_proxy|0.0050 [-0.0052, 0.0145]|6.04 [-0.23, 12.30]|4.4 [-0.5, 9.2]|-0.007 [-0.016, 0.002]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|stationary|cost_variance_proxy|0.0064 [-0.0025, 0.0153]|6.67 [0.42, 12.92]|25.4 [20.6, 30.2]|-0.005 [-0.014, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0|0.0064 [-0.0027, 0.0155]|6.67 [0.42, 12.92]|25.4 [20.6, 30.2]|-0.005 [-0.014, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0.1|0.0032 [-0.0056, 0.0111]|6.61 [0.64, 12.59]|21.7 [17.1, 26.4]|-0.006 [-0.014, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0.25|0.0022 [-0.0047, 0.0087]|5.99 [0.80, 11.19]|17.2 [13.3, 21.2]|-0.004 [-0.010, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0.5|0.0012 [-0.0054, 0.0074]|3.83 [-0.44, 8.10]|12.3 [9.2, 15.3]|-0.003 [-0.009, 0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r1|0.0014 [-0.0039, 0.0065]|2.02 [-0.82, 4.87]|8.2 [5.9, 10.5]|-0.004 [-0.009, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r2|-0.0021 [-0.0062, 0.0017]|1.23 [-0.89, 3.34]|5.4 [3.8, 7.1]|-0.002 [-0.006, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|variance_proxy|0.0041 [-0.0034, 0.0119]|6.04 [-0.23, 12.30]|4.4 [-0.5, 9.2]|-0.007 [-0.016, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
