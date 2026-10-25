# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|718.26|716.74|0.998|374.8|0.695|0.0348|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p1|718.26|716.99|0.998|365.5|0.734|0.0403|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p2|718.26|716.96|0.998|362.0|0.752|0.0349|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p0.5|718.26|716.92|0.998|380.5|0.673|0.0360|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p1|718.26|717.04|0.998|367.0|0.727|0.0386|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p2|718.26|717.03|0.998|362.2|0.751|0.0349|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p0.5|718.26|717.11|0.998|370.3|0.713|0.0361|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p1|718.26|717.08|0.998|364.3|0.741|0.0381|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p2|718.26|717.12|0.998|361.9|0.753|0.0350|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|718.26|716.99|0.998|361.0|0.756|0.0336|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p0.5|718.26|716.38|0.997|476.4|0.778|0.0475|30/30|30|0.667 / 0.667|0.467 / 0.467|0.633 / 0.633|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p1|718.26|716.59|0.998|476.8|0.850|0.0441|30/30|30|0.767 / 0.767|0.700 / 0.700|0.767 / 0.767|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p2|718.26|716.53|0.998|477.1|0.893|0.0515|30/30|30|0.867 / 0.867|0.733 / 0.733|0.833 / 0.833|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p0.5|718.26|716.42|0.997|476.7|0.755|0.0488|30/30|30|0.567 / 0.567|0.400 / 0.400|0.533 / 0.533|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p1|718.26|716.61|0.998|476.7|0.837|0.0425|30/30|30|0.800 / 0.800|0.633 / 0.633|0.767 / 0.767|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p2|718.26|716.64|0.998|476.9|0.888|0.0521|30/30|30|0.867 / 0.867|0.733 / 0.733|0.833 / 0.833|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p0.5|718.26|716.73|0.998|476.7|0.806|0.0480|30/30|30|0.733 / 0.733|0.533 / 0.533|0.667 / 0.667|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p1|718.26|716.62|0.998|476.9|0.858|0.0450|30/30|30|0.800 / 0.800|0.700 / 0.700|0.767 / 0.767|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p2|718.26|716.29|0.997|477.0|0.897|0.0506|30/30|30|0.867 / 0.867|0.800 / 0.800|0.833 / 0.833|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0486|30/30|30|0.867 / 0.867|0.767 / 0.767|0.833 / 0.833|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p0.5|718.26|716.58|0.998|476.5|0.771|0.0268|30/30|30|0.900 / 0.900|0.800 / 0.800|0.900 / 0.900|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p1|718.26|716.46|0.997|476.7|0.831|0.0294|30/30|30|0.933 / 0.933|0.800 / 0.800|0.933 / 0.933|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p2|718.26|716.67|0.998|477.2|0.870|0.0299|30/30|30|0.967 / 0.967|0.800 / 0.800|0.933 / 0.933|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p0.5|718.26|716.60|0.998|476.4|0.749|0.0263|30/30|30|0.933 / 0.933|0.700 / 0.700|0.900 / 0.900|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p1|718.26|716.66|0.998|476.4|0.822|0.0265|30/30|30|0.933 / 0.933|0.800 / 0.800|0.933 / 0.933|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p2|718.26|716.44|0.997|476.9|0.865|0.0292|30/30|30|0.967 / 0.967|0.800 / 0.800|0.933 / 0.933|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p0.5|718.26|716.56|0.998|476.6|0.791|0.0266|30/30|30|0.933 / 0.933|0.767 / 0.767|0.933 / 0.933|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p1|718.26|716.52|0.998|476.8|0.838|0.0298|30/30|30|0.900 / 0.900|0.800 / 0.800|0.900 / 0.900|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p2|718.26|716.50|0.998|477.0|0.872|0.0304|30/30|30|0.967 / 0.967|0.800 / 0.800|0.967 / 0.967|0.000 / 0.000 / 0.000|
|harmful_adaptation|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0318|30/30|30|0.967 / 0.967|0.833 / 0.833|0.967 / 0.967|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p0.5|718.26|716.51|0.998|475.9|0.532|0.0475|30/30|30|0.900 / 0.900|0.867 / 0.867|0.867 / 0.867|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p1|718.26|716.58|0.998|476.0|0.586|0.0456|30/30|30|0.800 / 0.800|0.767 / 0.767|0.800 / 0.800|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p2|718.26|716.62|0.998|476.5|0.666|0.0494|30/30|30|0.900 / 0.900|0.800 / 0.800|0.900 / 0.900|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p0.5|718.26|716.53|0.998|476.0|0.527|0.0472|30/30|30|0.900 / 0.900|0.867 / 0.867|0.900 / 0.900|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p1|718.26|716.63|0.998|476.1|0.579|0.0450|30/30|30|0.800 / 0.800|0.800 / 0.800|0.800 / 0.800|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p2|718.26|716.69|0.998|476.4|0.659|0.0476|30/30|30|0.833 / 0.833|0.767 / 0.767|0.800 / 0.800|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p0.5|718.26|716.52|0.998|475.9|0.544|0.0463|30/30|30|0.900 / 0.900|0.867 / 0.867|0.867 / 0.867|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p1|718.26|716.52|0.998|476.0|0.599|0.0452|30/30|30|0.767 / 0.767|0.733 / 0.733|0.733 / 0.733|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p2|718.26|716.53|0.998|476.3|0.677|0.0546|30/30|30|0.867 / 0.867|0.733 / 0.733|0.867 / 0.867|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0476|30/30|30|0.833 / 0.833|0.733 / 0.733|0.800 / 0.800|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p0.5|718.26|713.23|0.993|474.7|0.884|0.0387|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p1|718.26|709.45|0.988|472.5|0.947|0.0377|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p2|718.26|706.41|0.984|470.9|0.972|0.0369|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p0.5|718.26|715.32|0.996|476.3|0.853|0.0379|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p1|718.26|710.55|0.989|473.1|0.937|0.0383|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p2|718.26|706.77|0.984|471.1|0.970|0.0370|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p0.5|718.26|710.58|0.989|473.1|0.912|0.0403|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p1|718.26|708.93|0.987|472.5|0.956|0.0371|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p2|718.26|706.30|0.983|470.9|0.974|0.0368|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0351|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p0.5|718.26|713.38|0.993|474.8|0.896|0.0313|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p1|718.26|709.49|0.988|472.6|0.955|0.0295|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p2|718.26|705.88|0.983|470.8|0.978|0.0278|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p0.5|718.26|715.30|0.996|476.4|0.865|0.0313|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p1|718.26|710.63|0.989|473.3|0.946|0.0308|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p2|718.26|706.46|0.984|471.1|0.977|0.0273|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p0.5|718.26|710.59|0.989|473.4|0.923|0.0316|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p1|718.26|708.96|0.987|472.5|0.963|0.0281|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p2|718.26|705.64|0.982|470.7|0.979|0.0285|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0279|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 31025000 --n 3200 --d 16 --budget-rate 0.2 --monitor-estimator direct_ipw --q-min 0.2 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --robust-active-inference-radius-fraction 0.5 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation --methods uniform_proxy evidence_curve_a0_p0.5 evidence_curve_a0_p1 evidence_curve_a0_p2 evidence_curve_a0.025_p0.5 evidence_curve_a0.025_p1 evidence_curve_a0.025_p2 evidence_curve_a0.05_p0.5 evidence_curve_a0.05_p1 evidence_curve_a0.05_p2 --common-eprocess-bound --skip-figure --output outputs/direct_ipw_query_development_30_w4/runs/q_min_0p20`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|0.0013 [-0.0051, 0.0076]|-0.25 [-0.62, 0.13]|13.8 [8.7, 18.9]|-0.061 [-0.083, -0.039]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p1|0.0068 [-0.0010, 0.0146]|0.01 [-0.27, 0.28]|4.4 [2.1, 6.8]|-0.022 [-0.034, -0.010]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p2|0.0013 [-0.0001, 0.0029]|-0.03 [-0.27, 0.21]|0.9 [-0.2, 2.1]|-0.004 [-0.008, 0.000]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p0.5|0.0025 [-0.0040, 0.0088]|-0.07 [-0.47, 0.34]|19.5 [14.5, 24.5]|-0.083 [-0.105, -0.061]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p1|0.0051 [-0.0008, 0.0106]|0.05 [-0.37, 0.47]|6.0 [3.3, 8.7]|-0.029 [-0.042, -0.016]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p2|0.0013 [0.0001, 0.0029]|0.05 [-0.16, 0.26]|1.1 [-0.1, 2.3]|-0.005 [-0.010, -0.000]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p0.5|0.0025 [-0.0010, 0.0057]|0.12 [-0.17, 0.41]|9.3 [4.6, 14.0]|-0.043 [-0.064, -0.022]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p1|0.0045 [-0.0013, 0.0101]|0.10 [-0.13, 0.33]|3.3 [1.2, 5.3]|-0.016 [-0.025, -0.006]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p2|0.0015 [-0.0001, 0.0033]|0.14 [-0.06, 0.33]|0.9 [-0.2, 2.0]|-0.003 [-0.007, 0.001]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p0.5|-0.0012 [-0.0151, 0.0115]|12.31 [5.65, 18.96]|6.7 [2.1, 11.3]|-0.205 [-0.236, -0.174]|20 / 14 / 19 / 30|0 / 6|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p1|-0.0045 [-0.0150, 0.0051]|12.51 [5.84, 19.19]|7.1 [2.5, 11.7]|-0.133 [-0.160, -0.106]|23 / 21 / 23 / 30|0 / 2|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p2|0.0028 [-0.0044, 0.0108]|12.45 [5.90, 19.01]|7.4 [2.8, 12.0]|-0.089 [-0.117, -0.061]|26 / 22 / 25 / 30|0 / 4|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p0.5|0.0002 [-0.0152, 0.0143]|12.35 [5.69, 19.01]|7.0 [2.3, 11.7]|-0.227 [-0.257, -0.198]|17 / 12 / 16 / 30|0 / 5|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p1|-0.0062 [-0.0175, 0.0040]|12.54 [5.86, 19.22]|7.0 [2.4, 11.6]|-0.146 [-0.173, -0.119]|24 / 19 / 23 / 30|0 / 5|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p2|0.0034 [-0.0034, 0.0113]|12.57 [5.98, 19.15]|7.2 [2.6, 11.8]|-0.095 [-0.122, -0.067]|26 / 22 / 25 / 30|0 / 4|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0_p0.5|-0.0006 [-0.0132, 0.0106]|12.66 [5.95, 19.37]|7.0 [2.3, 11.7]|-0.177 [-0.208, -0.145]|22 / 16 / 20 / 30|0 / 6|0 / 2|0 / 30|
|boundary_local_harm|evidence_curve_a0_p1|-0.0036 [-0.0142, 0.0065]|12.55 [5.86, 19.23]|7.1 [2.7, 11.6]|-0.125 [-0.152, -0.098]|24 / 21 / 23 / 30|0 / 3|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0_p2|0.0020 [-0.0050, 0.0101]|12.22 [5.74, 18.70]|7.3 [2.6, 11.9]|-0.086 [-0.114, -0.057]|26 / 24 / 25 / 30|0 / 2|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p0.5|-0.0050 [-0.0104, 0.0014]|12.50 [5.80, 19.21]|6.7 [2.1, 11.4]|-0.212 [-0.242, -0.181]|27 / 24 / 27 / 30|0 / 3|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p1|-0.0024 [-0.0072, 0.0030]|12.39 [5.77, 19.00]|6.9 [2.0, 11.9]|-0.151 [-0.176, -0.126]|28 / 24 / 28 / 30|0 / 4|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p2|-0.0019 [-0.0059, 0.0016]|12.60 [5.90, 19.30]|7.5 [2.8, 12.1]|-0.113 [-0.136, -0.089]|29 / 24 / 28 / 30|0 / 5|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p0.5|-0.0055 [-0.0110, 0.0008]|12.53 [5.86, 19.19]|6.7 [1.9, 11.4]|-0.234 [-0.263, -0.204]|28 / 21 / 27 / 30|0 / 7|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p1|-0.0053 [-0.0096, -0.0007]|12.59 [5.86, 19.32]|6.7 [1.7, 11.6]|-0.160 [-0.185, -0.135]|28 / 24 / 28 / 30|0 / 4|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p2|-0.0026 [-0.0064, 0.0007]|12.37 [5.69, 19.04]|7.2 [2.5, 11.9]|-0.117 [-0.140, -0.094]|29 / 24 / 28 / 30|0 / 5|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0_p0.5|-0.0052 [-0.0107, 0.0013]|12.48 [5.82, 19.15]|6.9 [2.1, 11.6]|-0.192 [-0.223, -0.161]|28 / 23 / 28 / 30|0 / 5|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0_p1|-0.0020 [-0.0068, 0.0033]|12.45 [5.72, 19.18]|7.0 [2.2, 11.9]|-0.144 [-0.169, -0.119]|27 / 24 / 27 / 30|0 / 3|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0_p2|-0.0014 [-0.0054, 0.0022]|12.43 [5.77, 19.08]|7.3 [2.6, 11.9]|-0.110 [-0.134, -0.086]|29 / 24 / 29 / 30|0 / 5|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p0.5|-0.0001 [-0.0167, 0.0192]|12.43 [5.78, 19.09]|6.1 [1.4, 10.9]|-0.450 [-0.469, -0.432]|27 / 26 / 26 / 30|0 / 1|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p1|-0.0020 [-0.0192, 0.0156]|12.51 [5.80, 19.22]|6.3 [1.6, 11.0]|-0.397 [-0.424, -0.369]|24 / 23 / 24 / 30|0 / 1|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p2|0.0018 [-0.0132, 0.0183]|12.54 [5.89, 19.20]|6.8 [1.9, 11.7]|-0.317 [-0.369, -0.264]|27 / 24 / 27 / 30|0 / 3|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p0.5|-0.0004 [-0.0196, 0.0195]|12.45 [5.80, 19.11]|6.3 [1.5, 11.0]|-0.455 [-0.473, -0.438]|27 / 26 / 27 / 30|0 / 1|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p1|-0.0026 [-0.0198, 0.0146]|12.55 [5.92, 19.19]|6.3 [1.6, 11.1]|-0.403 [-0.431, -0.376]|24 / 24 / 24 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p2|0.0000 [-0.0153, 0.0171]|12.61 [5.92, 19.31]|6.6 [1.9, 11.4]|-0.323 [-0.373, -0.274]|25 / 23 / 24 / 30|0 / 2|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0_p0.5|-0.0013 [-0.0163, 0.0153]|12.44 [5.80, 19.08]|6.1 [1.4, 10.9]|-0.439 [-0.457, -0.421]|27 / 26 / 26 / 30|0 / 1|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0_p1|-0.0024 [-0.0201, 0.0159]|12.44 [5.79, 19.09]|6.3 [1.8, 10.8]|-0.384 [-0.416, -0.352]|23 / 22 / 22 / 30|0 / 1|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0_p2|0.0069 [-0.0074, 0.0211]|12.45 [5.84, 19.07]|6.6 [1.9, 11.3]|-0.305 [-0.360, -0.250]|26 / 22 / 26 / 30|0 / 4|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p0.5|0.0036 [-0.0033, 0.0101]|9.16 [3.70, 14.62]|5.0 [1.5, 8.4]|-0.098 [-0.132, -0.064]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p1|0.0026 [-0.0012, 0.0071]|5.37 [1.09, 9.65]|2.8 [0.1, 5.5]|-0.035 [-0.055, -0.015]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p2|0.0018 [-0.0009, 0.0048]|2.33 [-0.36, 5.03]|1.2 [-0.4, 2.8]|-0.010 [-0.019, -0.001]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p0.5|0.0028 [-0.0042, 0.0095]|11.25 [5.49, 17.01]|6.5 [2.7, 10.3]|-0.129 [-0.164, -0.095]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p1|0.0032 [-0.0006, 0.0071]|6.48 [1.81, 11.14]|3.3 [0.3, 6.3]|-0.045 [-0.067, -0.023]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p2|0.0018 [-0.0015, 0.0051]|2.70 [-0.06, 5.46]|1.4 [-0.3, 3.0]|-0.012 [-0.022, -0.002]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p0.5|0.0052 [-0.0004, 0.0105]|6.51 [1.76, 11.26]|3.4 [0.3, 6.5]|-0.070 [-0.103, -0.038]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p1|0.0020 [-0.0009, 0.0050]|4.86 [0.64, 9.08]|2.7 [0.2, 5.3]|-0.026 [-0.043, -0.009]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p2|0.0017 [-0.0001, 0.0043]|2.22 [-0.47, 4.92]|1.2 [-0.4, 2.7]|-0.009 [-0.017, -0.000]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p0.5|0.0034 [-0.0017, 0.0084]|9.31 [3.85, 14.77]|5.1 [1.7, 8.4]|-0.086 [-0.118, -0.055]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p1|0.0016 [-0.0026, 0.0060]|5.41 [1.07, 9.75]|2.9 [0.2, 5.6]|-0.027 [-0.044, -0.011]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p2|-0.0001 [-0.0008, 0.0009]|1.80 [0.01, 3.60]|1.1 [-0.0, 2.2]|-0.005 [-0.012, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p0.5|0.0034 [-0.0018, 0.0086]|11.22 [5.47, 16.97]|6.6 [2.9, 10.3]|-0.118 [-0.151, -0.084]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p1|0.0029 [-0.0014, 0.0073]|6.55 [1.84, 11.27]|3.6 [0.6, 6.6]|-0.036 [-0.055, -0.018]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p2|-0.0005 [-0.0018, 0.0006]|2.38 [0.19, 4.58]|1.4 [0.0, 2.8]|-0.006 [-0.013, 0.002]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p0.5|0.0037 [-0.0007, 0.0083]|6.52 [1.74, 11.30]|3.6 [0.6, 6.7]|-0.060 [-0.090, -0.029]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p1|0.0002 [-0.0026, 0.0028]|4.89 [0.61, 9.17]|2.7 [0.2, 5.3]|-0.019 [-0.032, -0.006]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p2|0.0007 [-0.0002, 0.0018]|1.56 [-0.09, 3.22]|1.0 [-0.1, 2.1]|-0.004 [-0.011, 0.003]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
