# Common hard label-dollar budget comparison

Evaluated 500 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The primary eventwise monitors use policy-specific support bounds: adaptive query policies use the configured q_min=0.10, and uniform querying uses its fixed q=0.20. The resulting minimum propensity and PPI support bound are recorded per method-stream.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|720.26|710.49|0.986|374.3|0.971|0.0451|0/0|14|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|720.26|718.74|0.998|370.5|0.650|0.0427|0/0|14|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|decision_value_proxy|720.26|718.97|0.998|363.9|0.619|0.0481|0/0|14|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|720.26|718.98|0.998|362.4|0.759|0.0403|0/0|14|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|720.26|718.90|0.998|363.0|0.588|0.0441|0/0|14|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|720.26|706.64|0.981|514.7|0.986|0.0368|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|720.26|708.03|0.983|493.6|0.979|0.0387|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|decision_value_proxy|720.26|712.40|0.989|475.4|0.946|0.0405|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|720.26|705.31|0.979|470.1|0.985|0.0361|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|720.26|706.93|0.982|471.9|0.979|0.0390|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 500 --seed-offset 54000000 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy --skip-figure --output C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/policy_bound_null_calibration_500`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0048 [0.0017, 0.0079]|-8.48 [-9.90, -7.06]|11.9 [11.2, 12.6]|0.212 [0.210, 0.215]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|benign_nuisance|cost_variance_proxy|0.0024 [-0.0001, 0.0049]|-0.24 [-0.59, 0.12]|8.1 [7.6, 8.5]|-0.110 [-0.116, -0.103]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|benign_nuisance|decision_value_proxy|0.0078 [0.0049, 0.0108]|-0.01 [-0.10, 0.08]|1.5 [1.1, 2.0]|-0.140 [-0.147, -0.134]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|benign_nuisance|variance_proxy|0.0038 [0.0011, 0.0066]|-0.07 [-0.16, 0.01]|0.6 [0.2, 0.9]|-0.171 [-0.177, -0.166]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|stationary|cost_stabilized_proxy|0.0007 [-0.0011, 0.0025]|1.33 [0.24, 2.41]|44.6 [43.7, 45.4]|0.001 [-0.000, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|stationary|cost_variance_proxy|0.0026 [0.0006, 0.0047]|2.71 [1.29, 4.14]|23.5 [22.1, 24.8]|-0.005 [-0.007, -0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|stationary|decision_value_proxy|0.0044 [0.0022, 0.0067]|7.08 [5.39, 8.78]|5.3 [3.9, 6.7]|-0.039 [-0.043, -0.035]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
|stationary|variance_proxy|0.0029 [0.0010, 0.0048]|1.61 [0.24, 2.99]|1.8 [0.6, 2.9]|-0.006 [-0.008, -0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 500|
