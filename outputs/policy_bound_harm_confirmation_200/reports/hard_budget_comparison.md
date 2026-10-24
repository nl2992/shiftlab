# Common hard label-dollar budget comparison

Evaluated 200 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The primary eventwise monitors use policy-specific support bounds: adaptive query policies use the configured q_min=0.10, and uniform querying uses its fixed q=0.20. The resulting minimum propensity and PPI support bound are recorded per method-stream.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|720.63|708.80|0.984|516.3|0.980|0.0483|200/200|200|0.050 / 0.050|0.035 / 0.035|0.035 / 0.035|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|720.63|709.90|0.985|495.0|0.975|0.0538|200/200|200|0.060 / 0.060|0.055 / 0.055|0.055 / 0.055|0.000 / 0.000 / 0.000|
|boundary_local_harm|decision_value_proxy|720.63|704.83|0.978|470.3|0.960|0.0581|200/200|200|0.055 / 0.055|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|720.63|707.10|0.981|471.5|0.981|0.0501|200/200|200|0.675 / 0.675|0.590 / 0.590|0.645 / 0.645|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|720.63|709.79|0.985|473.7|0.974|0.0553|200/200|200|0.050 / 0.050|0.045 / 0.045|0.045 / 0.045|0.000 / 0.000 / 0.000|
|harmful_adaptation|cost_stabilized_proxy|720.63|708.80|0.984|516.3|0.980|0.0295|200/200|200|0.025 / 0.025|0.035 / 0.035|0.015 / 0.015|0.000 / 0.000 / 0.000|
|harmful_adaptation|cost_variance_proxy|720.63|709.90|0.985|495.0|0.975|0.0314|200/200|200|0.015 / 0.015|0.015 / 0.015|0.010 / 0.010|0.000 / 0.000 / 0.000|
|harmful_adaptation|decision_value_proxy|720.63|709.45|0.985|473.1|0.956|0.0339|200/200|200|0.040 / 0.040|0.040 / 0.040|0.030 / 0.030|0.000 / 0.000 / 0.000|
|harmful_adaptation|uniform_proxy|720.63|707.10|0.981|471.5|0.981|0.0305|200/200|200|0.875 / 0.875|0.845 / 0.845|0.875 / 0.875|0.000 / 0.000 / 0.000|
|harmful_adaptation|variance_proxy|720.63|709.79|0.985|473.7|0.974|0.0327|200/200|200|0.025 / 0.025|0.035 / 0.035|0.015 / 0.015|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_stabilized_proxy|720.63|708.80|0.984|516.3|0.980|0.0464|200/200|200|0.035 / 0.035|0.035 / 0.035|0.035 / 0.035|0.000 / 0.000 / 0.000|
|recurring_regimes|cost_variance_proxy|720.63|709.90|0.985|495.0|0.975|0.0518|200/200|200|0.070 / 0.070|0.065 / 0.065|0.060 / 0.060|0.000 / 0.000 / 0.000|
|recurring_regimes|decision_value_proxy|720.63|696.97|0.967|464.4|0.973|0.0575|200/200|200|0.085 / 0.085|0.080 / 0.080|0.075 / 0.075|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|720.63|707.10|0.981|471.5|0.981|0.0493|200/200|200|0.675 / 0.675|0.630 / 0.630|0.660 / 0.660|0.000 / 0.000 / 0.000|
|recurring_regimes|variance_proxy|720.63|709.79|0.985|473.7|0.974|0.0553|200/200|200|0.085 / 0.085|0.085 / 0.085|0.080 / 0.080|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 200 --seed-offset 55000000 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios boundary_local_harm recurring_regimes harmful_adaptation --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy --skip-figure --output C:/Users/nigel/OneDrive/桌面/ICML/shift-research-starter/outputs/policy_bound_harm_confirmation_200`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|-0.0019 [-0.0054, 0.0016]|1.70 [0.10, 3.29]|44.9 [43.7, 46.1]|-0.001 [-0.003, 0.002]|10 / 7 / 7 / 200|0 / 3|0 / 3|0 / 200|
|boundary_local_harm|cost_variance_proxy|0.0037 [-0.0009, 0.0082]|2.80 [1.08, 4.52]|23.6 [21.7, 25.5]|-0.006 [-0.009, -0.002]|12 / 11 / 11 / 200|0 / 1|0 / 1|0 / 200|
|boundary_local_harm|decision_value_proxy|0.0080 [0.0030, 0.0129]|-2.27 [-5.35, 0.81]|-1.2 [-3.6, 1.2]|-0.021 [-0.027, -0.015]|11 / 10 / 10 / 200|0 / 1|0 / 1|0 / 200|
|boundary_local_harm|variance_proxy|0.0052 [0.0001, 0.0104]|2.69 [0.92, 4.46]|2.2 [0.5, 4.0]|-0.006 [-0.010, -0.003]|10 / 9 / 9 / 200|0 / 1|0 / 1|0 / 200|
|harmful_adaptation|cost_stabilized_proxy|-0.0011 [-0.0041, 0.0017]|1.70 [0.10, 3.29]|44.9 [43.7, 46.1]|-0.001 [-0.003, 0.002]|5 / 7 / 3 / 200|2 / 0|0 / 2|0 / 200|
|harmful_adaptation|cost_variance_proxy|0.0009 [-0.0027, 0.0042]|2.80 [1.08, 4.52]|23.6 [21.7, 25.5]|-0.006 [-0.009, -0.002]|3 / 3 / 2 / 200|0 / 0|0 / 1|0 / 200|
|harmful_adaptation|decision_value_proxy|0.0034 [-0.0001, 0.0067]|2.35 [-0.22, 4.92]|1.6 [-0.6, 3.8]|-0.025 [-0.031, -0.018]|8 / 8 / 6 / 200|0 / 0|0 / 2|0 / 200|
|harmful_adaptation|variance_proxy|0.0022 [-0.0010, 0.0053]|2.69 [0.92, 4.46]|2.2 [0.5, 4.0]|-0.006 [-0.010, -0.003]|5 / 7 / 3 / 200|2 / 0|0 / 2|0 / 200|
|recurring_regimes|cost_stabilized_proxy|-0.0029 [-0.0067, 0.0008]|1.70 [0.10, 3.29]|44.9 [43.7, 46.1]|-0.001 [-0.003, 0.002]|7 / 7 / 7 / 200|0 / 0|0 / 0|0 / 200|
|recurring_regimes|cost_variance_proxy|0.0025 [-0.0022, 0.0071]|2.80 [1.08, 4.52]|23.6 [21.7, 25.5]|-0.006 [-0.009, -0.002]|14 / 13 / 12 / 200|0 / 1|0 / 2|0 / 200|
|recurring_regimes|decision_value_proxy|0.0081 [0.0032, 0.0130]|-10.13 [-14.56, -5.71]|-7.1 [-10.3, -3.9]|-0.008 [-0.014, -0.002]|17 / 16 / 15 / 200|0 / 1|0 / 2|0 / 200|
|recurring_regimes|variance_proxy|0.0059 [0.0013, 0.0106]|2.69 [0.92, 4.46]|2.2 [0.5, 4.0]|-0.006 [-0.010, -0.003]|17 / 17 / 16 / 200|0 / 0|0 / 1|0 / 200|
