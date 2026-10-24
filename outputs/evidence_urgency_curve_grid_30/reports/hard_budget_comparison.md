# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|359.41|328.83|0.915|167.4|0.928|0.0668|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p1|359.41|277.68|0.773|134.8|0.996|0.0740|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p2|359.41|252.33|0.702|122.1|1.000|0.0750|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p0.5|359.41|351.41|0.978|184.4|0.867|0.0599|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p1|359.41|292.97|0.816|143.7|0.995|0.0660|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p2|359.41|255.00|0.710|123.3|1.000|0.0744|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p0.5|359.41|291.82|0.812|144.5|0.960|0.0729|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p1|359.41|266.24|0.741|128.7|0.998|0.0763|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p2|359.41|250.70|0.698|121.3|1.000|0.0740|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|359.41|358.03|0.996|180.6|0.748|0.0610|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p0.5|359.41|326.59|0.909|218.4|0.985|0.0803|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p1|359.41|249.77|0.695|167.1|1.000|0.1035|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p2|359.41|202.54|0.564|135.6|1.000|0.1100|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p0.5|359.41|345.97|0.963|231.4|0.968|0.0662|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p1|359.41|265.54|0.739|177.6|1.000|0.0957|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p2|359.41|207.19|0.577|138.6|1.000|0.1097|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p0.5|359.41|289.77|0.807|194.2|0.996|0.0971|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p1|359.41|240.19|0.669|161.0|1.000|0.1083|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p2|359.41|199.12|0.554|133.3|1.000|0.1124|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|359.41|350.52|0.975|233.8|0.967|0.0759|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p0.5|359.41|277.84|0.773|185.5|0.995|0.0606|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p1|359.41|207.03|0.576|138.1|1.000|0.0687|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p2|359.41|182.88|0.509|122.3|1.000|0.0759|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p0.5|359.41|312.42|0.869|208.7|0.990|0.0533|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p1|359.41|222.21|0.619|148.5|1.000|0.0623|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p2|359.41|184.82|0.515|123.5|1.000|0.0742|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p0.5|359.41|235.39|0.655|157.6|1.000|0.0664|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p1|359.41|196.41|0.547|131.3|1.000|0.0744|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p2|359.41|181.41|0.505|121.3|1.000|0.0732|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|359.41|350.52|0.975|233.8|0.967|0.0505|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 20372024 --n 3200 --d 16 --budget-rate 0.1 --q-min 0.05 --q-max 0.5 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0_p0.5 evidence_curve_a0_p1 evidence_curve_a0_p2 evidence_curve_a0.025_p0.5 evidence_curve_a0.025_p1 evidence_curve_a0.025_p2 evidence_curve_a0.05_p0.5 evidence_curve_a0.05_p1 evidence_curve_a0.05_p2 --common-eprocess-bound --skip-figure --output outputs/evidence_urgency_curve_grid_30`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|0.0058 [-0.0053, 0.0174]|-29.21 [-42.26, -16.15]|-13.3 [-20.9, -5.6]|0.180 [0.143, 0.218]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p1|0.0130 [0.0003, 0.0261]|-80.36 [-95.59, -65.12]|-45.9 [-52.8, -38.9]|0.248 [0.229, 0.268]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p2|0.0140 [-0.0024, 0.0304]|-105.70 [-116.08, -95.32]|-58.6 [-62.9, -54.2]|0.252 [0.233, 0.271]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p0.5|-0.0012 [-0.0129, 0.0123]|-6.62 [-11.77, -1.47]|3.8 [0.4, 7.2]|0.120 [0.082, 0.157]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p1|0.0050 [-0.0091, 0.0195]|-65.06 [-79.77, -50.35]|-37.0 [-43.6, -30.3]|0.247 [0.226, 0.268]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p2|0.0134 [-0.0026, 0.0299]|-103.03 [-113.52, -92.55]|-57.3 [-61.7, -52.9]|0.252 [0.233, 0.271]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p0.5|0.0119 [0.0021, 0.0218]|-66.21 [-85.20, -47.22]|-36.2 [-46.7, -25.7]|0.212 [0.183, 0.241]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p1|0.0153 [0.0006, 0.0299]|-91.80 [-106.45, -77.14]|-51.9 [-58.4, -45.4]|0.250 [0.231, 0.269]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p2|0.0130 [-0.0026, 0.0290]|-107.34 [-117.70, -96.98]|-59.3 [-63.6, -55.0]|0.252 [0.233, 0.271]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p0.5|0.0045 [-0.0095, 0.0178]|-23.93 [-40.09, -7.77]|-15.4 [-26.2, -4.5]|0.018 [0.005, 0.031]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p1|0.0276 [0.0126, 0.0422]|-100.75 [-119.78, -81.71]|-66.7 [-79.1, -54.2]|0.033 [0.019, 0.047]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p2|0.0341 [0.0156, 0.0505]|-147.98 [-159.17, -136.78]|-98.2 [-105.6, -90.8]|0.033 [0.019, 0.047]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p0.5|-0.0097 [-0.0241, 0.0054]|-4.54 [-13.51, 4.43]|-2.3 [-8.2, 3.5]|0.001 [-0.015, 0.017]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p1|0.0199 [0.0065, 0.0316]|-84.98 [-101.54, -68.41]|-56.2 [-66.9, -45.4]|0.033 [0.019, 0.047]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p2|0.0338 [0.0153, 0.0506]|-143.33 [-155.51, -131.15]|-95.1 [-103.2, -87.1]|0.033 [0.019, 0.047]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0_p0.5|0.0212 [0.0054, 0.0374]|-60.75 [-85.00, -36.50]|-39.6 [-55.6, -23.5]|0.029 [0.014, 0.043]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0_p1|0.0324 [0.0160, 0.0479]|-110.33 [-129.47, -91.20]|-72.8 [-85.3, -60.3]|0.033 [0.019, 0.047]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0_p2|0.0365 [0.0177, 0.0534]|-151.39 [-162.21, -140.58]|-100.5 [-107.6, -93.3]|0.033 [0.019, 0.047]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p0.5|0.0101 [0.0014, 0.0194]|-72.67 [-93.51, -51.84]|-48.3 [-62.3, -34.3]|0.028 [0.016, 0.039]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p1|0.0181 [0.0076, 0.0277]|-143.48 [-155.32, -131.65]|-95.6 [-103.5, -87.8]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p2|0.0253 [0.0076, 0.0428]|-167.64 [-173.75, -161.53]|-111.5 [-115.4, -107.6]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p0.5|0.0028 [-0.0046, 0.0101]|-38.10 [-52.49, -23.70]|-25.0 [-34.7, -15.4]|0.023 [0.009, 0.037]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p1|0.0118 [0.0004, 0.0226]|-128.30 [-140.47, -116.14]|-85.3 [-93.3, -77.3]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p2|0.0237 [0.0060, 0.0404]|-165.70 [-171.95, -159.44]|-110.2 [-114.3, -106.2]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p0.5|0.0159 [0.0069, 0.0248]|-115.13 [-138.39, -91.87]|-76.2 [-91.7, -60.6]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p1|0.0238 [0.0125, 0.0338]|-154.11 [-165.39, -142.83]|-102.5 [-109.9, -95.0]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p2|0.0226 [0.0070, 0.0375]|-169.11 [-174.95, -163.27]|-112.5 [-116.2, -108.8]|0.033 [0.019, 0.047]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
