# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_variance_proxy|359.37|358.15|0.997|186.2|0.637|0.0755|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0|359.37|358.15|0.997|186.2|0.637|0.0755|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0.1|359.37|357.92|0.996|185.3|0.651|0.0755|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0.25|359.37|357.95|0.996|184.8|0.666|0.0726|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r0.5|359.37|357.94|0.996|184.2|0.684|0.0763|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r1|359.37|357.94|0.996|183.2|0.705|0.0781|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|robust_active_inference_r2|359.37|358.16|0.997|182.6|0.722|0.0792|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|359.37|357.93|0.996|181.5|0.763|0.0836|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|359.37|358.10|0.996|182.2|0.579|0.0780|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|359.37|351.48|0.978|245.7|0.974|0.0795|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0|359.37|351.48|0.978|245.7|0.974|0.0795|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0.1|359.37|351.29|0.978|243.7|0.971|0.0716|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0.25|359.37|350.85|0.976|241.4|0.968|0.0747|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r0.5|359.37|350.13|0.974|239.0|0.971|0.0713|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r1|359.37|349.63|0.973|237.0|0.973|0.0755|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|robust_active_inference_r2|359.37|349.82|0.974|235.7|0.975|0.0802|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|359.37|348.88|0.971|232.6|0.977|0.0861|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|359.37|351.21|0.977|234.6|0.974|0.0772|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|359.37|351.48|0.978|245.7|0.974|0.0653|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0|359.37|351.48|0.978|245.7|0.974|0.0653|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0.1|359.37|351.29|0.978|243.7|0.971|0.0639|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0.25|359.37|350.85|0.976|241.4|0.968|0.0575|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r0.5|359.37|350.13|0.974|239.0|0.971|0.0565|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r1|359.37|349.63|0.973|237.0|0.973|0.0592|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|robust_active_inference_r2|359.37|349.82|0.974|235.7|0.975|0.0597|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|359.37|348.88|0.971|232.6|0.977|0.0609|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|359.37|351.21|0.977|234.6|0.974|0.0627|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 56220000 --n 3200 --d 16 --budget-rate 0.1 --q-min 0.05 --q-max 0.5 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --robust-active-inference-radius-fraction 0.5 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy cost_variance_proxy robust_active_inference_r0 robust_active_inference_r0.1 robust_active_inference_r0.25 robust_active_inference_r0.5 robust_active_inference_r1 robust_active_inference_r2 --common-eprocess-bound --skip-figure --output outputs/robust_active_inference_radius_development`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_variance_proxy|-0.0082 [-0.0298, 0.0135]|0.21 [-0.08, 0.50]|4.7 [3.2, 6.1]|-0.127 [-0.151, -0.102]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0|-0.0082 [-0.0300, 0.0132]|0.21 [-0.08, 0.50]|4.7 [3.2, 6.1]|-0.127 [-0.151, -0.102]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0.1|-0.0081 [-0.0231, 0.0090]|-0.02 [-0.39, 0.36]|3.8 [2.5, 5.1]|-0.112 [-0.132, -0.092]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0.25|-0.0110 [-0.0231, 0.0041]|0.01 [-0.36, 0.38]|3.3 [2.3, 4.4]|-0.098 [-0.114, -0.081]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r0.5|-0.0073 [-0.0178, 0.0058]|0.01 [-0.31, 0.32]|2.7 [1.8, 3.6]|-0.079 [-0.093, -0.065]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r1|-0.0055 [-0.0131, 0.0039]|0.01 [-0.37, 0.38]|1.7 [1.1, 2.3]|-0.058 [-0.068, -0.048]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|robust_active_inference_r2|-0.0044 [-0.0150, 0.0088]|0.22 [-0.18, 0.63]|1.1 [0.7, 1.5]|-0.041 [-0.048, -0.034]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|variance_proxy|-0.0056 [-0.0223, 0.0138]|0.16 [-0.18, 0.51]|0.7 [-0.5, 1.9]|-0.185 [-0.205, -0.164]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|cost_variance_proxy|-0.0066 [-0.0236, 0.0144]|2.60 [-0.52, 5.72]|13.1 [9.6, 16.6]|-0.003 [-0.012, 0.006]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0|-0.0066 [-0.0241, 0.0145]|2.60 [-0.52, 5.72]|13.1 [9.6, 16.6]|-0.003 [-0.012, 0.006]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0.1|-0.0146 [-0.0294, 0.0036]|2.42 [-0.28, 5.11]|11.1 [8.2, 14.0]|-0.007 [-0.014, 0.001]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0.25|-0.0114 [-0.0251, -0.0025]|1.97 [-0.52, 4.47]|8.8 [6.5, 11.0]|-0.009 [-0.015, -0.003]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r0.5|-0.0148 [-0.0202, -0.0093]|1.25 [-1.06, 3.56]|6.4 [4.4, 8.3]|-0.006 [-0.012, -0.001]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r1|-0.0106 [-0.0152, -0.0052]|0.75 [-1.31, 2.81]|4.4 [2.9, 5.9]|-0.004 [-0.008, 0.000]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|robust_active_inference_r2|-0.0060 [-0.0119, 0.0006]|0.94 [-1.06, 2.94]|3.1 [1.7, 4.6]|-0.003 [-0.006, 0.001]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|variance_proxy|-0.0089 [-0.0270, 0.0133]|2.34 [0.08, 4.59]|2.0 [-0.8, 4.8]|-0.003 [-0.011, 0.004]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|cost_variance_proxy|0.0044 [-0.0078, 0.0136]|2.60 [-0.52, 5.72]|13.1 [9.6, 16.6]|-0.003 [-0.012, 0.006]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0|0.0044 [-0.0079, 0.0136]|2.60 [-0.52, 5.72]|13.1 [9.6, 16.6]|-0.003 [-0.012, 0.006]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0.1|0.0030 [-0.0051, 0.0114]|2.42 [-0.28, 5.11]|11.1 [8.2, 14.0]|-0.007 [-0.014, 0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0.25|-0.0034 [-0.0097, 0.0047]|1.97 [-0.52, 4.47]|8.8 [6.5, 11.0]|-0.009 [-0.015, -0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r0.5|-0.0044 [-0.0111, 0.0023]|1.25 [-1.06, 3.56]|6.4 [4.4, 8.3]|-0.006 [-0.012, -0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r1|-0.0017 [-0.0085, 0.0038]|0.75 [-1.31, 2.81]|4.4 [2.9, 5.9]|-0.004 [-0.008, 0.000]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|robust_active_inference_r2|-0.0012 [-0.0067, 0.0034]|0.94 [-1.06, 2.94]|3.1 [1.7, 4.6]|-0.003 [-0.006, 0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|variance_proxy|0.0018 [-0.0098, 0.0137]|2.34 [0.08, 4.59]|2.0 [-0.8, 4.8]|-0.003 [-0.011, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
