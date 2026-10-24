# Common hard label-dollar budget comparison

Evaluated 60 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|720.51|710.33|0.986|375.0|0.967|0.0457|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|cost_variance_proxy|720.51|719.17|0.998|371.7|0.636|0.0404|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p0.5|720.51|676.96|0.940|347.2|0.942|0.0487|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|720.51|719.13|0.998|362.9|0.760|0.0384|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|variance_proxy|720.51|719.22|0.998|364.1|0.577|0.0433|0/0|2|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_stabilized_proxy|720.51|707.05|0.981|515.6|0.981|0.0509|60/60|60|0.083 / 0.083|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|cost_variance_proxy|720.51|707.79|0.982|494.5|0.972|0.0549|60/60|60|0.033 / 0.033|0.033 / 0.033|0.017 / 0.017|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p0.5|720.51|691.57|0.960|461.5|0.979|0.0542|60/60|60|0.067 / 0.067|0.050 / 0.050|0.050 / 0.050|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|720.51|704.81|0.978|469.8|0.982|0.0504|60/60|60|0.100 / 0.100|0.050 / 0.050|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|variance_proxy|720.51|707.08|0.981|472.7|0.971|0.0546|60/60|60|0.050 / 0.050|0.017 / 0.017|0.017 / 0.017|0.000 / 0.000 / 0.000|
|stationary|cost_stabilized_proxy|720.51|707.05|0.981|515.6|0.981|0.0340|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|cost_variance_proxy|720.51|707.79|0.982|494.5|0.972|0.0394|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p0.5|720.51|566.00|0.786|377.8|0.999|0.0409|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|720.51|704.81|0.978|469.8|0.982|0.0335|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|variance_proxy|720.51|707.08|0.981|472.7|0.971|0.0385|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20373024 --n 3200 --d 16 --budget-rate 0.2 --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0.05_p0.5 variance_proxy cost_variance_proxy cost_stabilized_proxy --common-eprocess-bound --skip-figure --output outputs/evidence_budget20_comparison_60`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.0073 [0.0010, 0.0131]|-8.80 [-13.99, -3.60]|12.1 [9.5, 14.6]|0.207 [0.199, 0.214]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|cost_variance_proxy|0.0020 [-0.0067, 0.0104]|0.04 [-0.23, 0.31]|8.8 [7.3, 10.3]|-0.124 [-0.140, -0.107]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|evidence_curve_a0.05_p0.5|0.0103 [0.0031, 0.0180]|-42.17 [-56.54, -27.80]|-15.7 [-23.6, -7.8]|0.182 [0.162, 0.202]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|benign_nuisance|variance_proxy|0.0049 [-0.0042, 0.0147]|0.09 [-0.15, 0.33]|1.2 [-0.1, 2.4]|-0.183 [-0.197, -0.169]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|boundary_local_harm|cost_stabilized_proxy|0.0006 [-0.0059, 0.0072]|2.23 [-1.17, 5.64]|45.8 [43.4, 48.3]|-0.001 [-0.006, 0.004]|5 / 4 / 4 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|cost_variance_proxy|0.0045 [-0.0030, 0.0120]|2.97 [-0.47, 6.42]|24.6 [20.8, 28.5]|-0.010 [-0.016, -0.004]|2 / 2 / 1 / 60|0 / 0|0 / 1|0 / 60|
|boundary_local_harm|evidence_curve_a0.05_p0.5|0.0038 [-0.0031, 0.0108]|-13.24 [-22.96, -3.52]|-8.3 [-14.6, -2.0]|-0.003 [-0.011, 0.006]|4 / 3 / 3 / 60|0 / 1|0 / 1|0 / 60|
|boundary_local_harm|variance_proxy|0.0042 [-0.0039, 0.0134]|2.26 [-1.60, 6.13]|2.9 [-0.7, 6.5]|-0.011 [-0.016, -0.005]|3 / 1 / 1 / 60|0 / 2|0 / 2|0 / 60|
|stationary|cost_stabilized_proxy|0.0005 [-0.0037, 0.0044]|2.23 [-1.17, 5.64]|45.8 [43.4, 48.3]|-0.001 [-0.006, 0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|cost_variance_proxy|0.0059 [-0.0013, 0.0126]|2.97 [-0.47, 6.42]|24.6 [20.8, 28.5]|-0.010 [-0.016, -0.004]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|evidence_curve_a0.05_p0.5|0.0074 [0.0012, 0.0133]|-138.81 [-161.80, -115.83]|-92.0 [-107.1, -76.9]|0.018 [0.012, 0.024]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
|stationary|variance_proxy|0.0050 [-0.0003, 0.0099]|2.26 [-1.60, 6.13]|2.9 [-0.7, 6.5]|-0.011 [-0.016, -0.005]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 60|
