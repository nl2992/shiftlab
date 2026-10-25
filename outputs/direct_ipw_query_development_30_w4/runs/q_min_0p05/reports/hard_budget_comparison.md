# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|718.26|469.98|0.655|233.3|1.000|0.0624|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p1|718.26|332.03|0.462|162.3|1.000|0.0644|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p2|718.26|269.41|0.375|129.7|1.000|0.0784|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p0.5|718.26|503.48|0.702|256.1|1.000|0.0556|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p1|718.26|354.05|0.493|173.8|1.000|0.0629|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p2|718.26|273.35|0.381|132.0|1.000|0.0744|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p0.5|718.26|442.92|0.617|220.5|1.000|0.0638|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p1|718.26|323.20|0.450|157.4|1.000|0.0690|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p2|718.26|264.39|0.368|127.3|1.000|0.0768|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|718.26|716.99|0.998|361.0|0.756|0.0336|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p0.5|718.26|579.38|0.807|386.7|1.000|0.0565|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p1|718.26|456.22|0.635|304.7|1.000|0.0662|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p2|718.26|326.15|0.454|218.5|1.000|0.0861|30/30|30|0.100 / 0.100|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p0.5|718.26|605.84|0.844|403.4|1.000|0.0558|30/30|30|0.067 / 0.067|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p1|718.26|465.94|0.649|311.1|1.000|0.0634|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p2|718.26|341.99|0.476|228.8|1.000|0.0828|30/30|30|0.100 / 0.100|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p0.5|718.26|563.87|0.785|376.2|1.000|0.0686|30/30|30|0.100 / 0.100|0.100 / 0.100|0.100 / 0.100|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p1|718.26|447.60|0.623|298.8|1.000|0.0703|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p2|718.26|311.35|0.433|208.6|1.000|0.0816|30/30|30|0.100 / 0.100|0.100 / 0.100|0.100 / 0.100|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0486|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p0.5|718.26|576.19|0.802|384.4|1.000|0.0384|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p1|718.26|448.02|0.624|299.4|1.000|0.0434|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p2|718.26|307.55|0.428|205.9|1.000|0.0474|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p0.5|718.26|602.40|0.839|401.4|1.000|0.0368|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p1|718.26|467.84|0.652|312.8|1.000|0.0393|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p2|718.26|323.26|0.450|216.4|1.000|0.0486|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p0.5|718.26|551.20|0.767|367.8|1.000|0.0431|30/30|30|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p1|718.26|435.74|0.607|290.9|1.000|0.0456|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p2|718.26|295.71|0.412|198.0|1.000|0.0483|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|harmful_adaptation|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0318|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p0.5|718.26|657.14|0.915|437.8|0.995|0.0651|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p1|718.26|528.52|0.735|353.1|0.999|0.0677|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p2|718.26|369.67|0.514|247.3|1.000|0.0809|30/30|30|0.067 / 0.067|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p0.5|718.26|685.30|0.954|455.8|0.988|0.0690|30/30|30|0.067 / 0.067|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p1|718.26|542.94|0.756|362.5|1.000|0.0675|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p2|718.26|383.04|0.533|256.2|1.000|0.0759|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p0.5|718.26|640.16|0.891|426.3|0.993|0.0750|30/30|30|0.100 / 0.100|0.067 / 0.067|0.067 / 0.067|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p1|718.26|503.94|0.701|336.7|1.000|0.0743|30/30|30|0.033 / 0.033|0.033 / 0.033|0.033 / 0.033|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p2|718.26|340.34|0.474|227.5|1.000|0.0812|30/30|30|0.067 / 0.067|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0476|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p0.5|718.26|404.73|0.564|270.4|1.000|0.0635|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p1|718.26|269.93|0.376|180.6|1.000|0.0688|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p2|718.26|201.88|0.281|135.2|1.000|0.0770|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p0.5|718.26|434.13|0.605|289.1|1.000|0.0618|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p1|718.26|287.04|0.400|191.9|1.000|0.0658|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p2|718.26|206.49|0.288|138.3|1.000|0.0757|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p0.5|718.26|380.20|0.530|253.8|1.000|0.0658|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p1|718.26|262.03|0.365|175.2|1.000|0.0727|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p2|718.26|196.20|0.273|131.5|1.000|0.0780|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0351|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p0.5|718.26|369.97|0.515|246.8|1.000|0.0627|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p1|718.26|246.54|0.343|165.0|1.000|0.0647|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p2|718.26|195.10|0.272|130.6|1.000|0.0769|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p0.5|718.26|402.50|0.561|267.7|1.000|0.0555|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p1|718.26|263.94|0.368|176.6|1.000|0.0607|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p2|718.26|199.61|0.278|133.6|1.000|0.0767|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p0.5|718.26|344.45|0.480|229.6|1.000|0.0631|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p1|718.26|239.03|0.333|159.9|1.000|0.0694|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p2|718.26|190.91|0.266|127.9|1.000|0.0776|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0279|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 31025000 --n 3200 --d 16 --budget-rate 0.2 --monitor-estimator direct_ipw --q-min 0.05 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --robust-active-inference-radius-fraction 0.5 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation --methods uniform_proxy evidence_curve_a0_p0.5 evidence_curve_a0_p1 evidence_curve_a0_p2 evidence_curve_a0.025_p0.5 evidence_curve_a0.025_p1 evidence_curve_a0.025_p2 evidence_curve_a0.05_p0.5 evidence_curve_a0.05_p1 evidence_curve_a0.05_p2 --common-eprocess-bound --skip-figure --output outputs/direct_ipw_query_development_30_w4/runs/q_min_0p05`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|0.0289 [0.0109, 0.0464]|-247.00 [-298.98, -195.02]|-127.7 [-153.0, -102.4]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p1|0.0309 [0.0109, 0.0497]|-384.95 [-416.50, -353.41]|-198.8 [-214.1, -183.4]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p2|0.0448 [0.0160, 0.0743]|-447.57 [-467.71, -427.43]|-231.3 [-240.6, -222.0]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p0.5|0.0220 [0.0043, 0.0391]|-213.51 [-259.73, -167.29]|-104.9 [-127.5, -82.4]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p1|0.0294 [0.0104, 0.0476]|-362.94 [-393.99, -331.88]|-187.2 [-202.0, -172.4]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p2|0.0408 [0.0169, 0.0640]|-443.64 [-462.80, -424.47]|-229.1 [-238.1, -220.1]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p0.5|0.0302 [0.0118, 0.0488]|-274.07 [-332.19, -215.94]|-140.5 [-170.4, -110.6]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p1|0.0355 [0.0147, 0.0556]|-393.79 [-425.72, -361.85]|-203.6 [-219.2, -188.1]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p2|0.0433 [0.0172, 0.0683]|-452.59 [-469.00, -436.19]|-233.8 [-241.2, -226.4]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p0.5|0.0079 [-0.0060, 0.0206]|-124.70 [-154.41, -94.98]|-83.0 [-103.1, -62.9]|0.017 [0.008, 0.027]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p1|0.0176 [-0.0015, 0.0342]|-247.86 [-287.54, -208.18]|-165.0 [-192.2, -137.8]|0.017 [0.008, 0.027]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p2|0.0375 [0.0164, 0.0571]|-377.93 [-427.86, -328.00]|-251.2 [-285.1, -217.3]|0.017 [0.008, 0.027]|3 / 2 / 2 / 30|0 / 1|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p0.5|0.0072 [-0.0082, 0.0206]|-98.24 [-120.08, -76.39]|-66.3 [-81.3, -51.3]|0.017 [0.008, 0.027]|2 / 1 / 1 / 30|0 / 1|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p1|0.0147 [-0.0023, 0.0291]|-238.13 [-275.73, -200.53]|-158.6 [-184.4, -132.8]|0.017 [0.008, 0.027]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p2|0.0342 [0.0145, 0.0533]|-362.08 [-410.50, -313.67]|-241.0 [-274.0, -207.9]|0.017 [0.008, 0.027]|3 / 2 / 2 / 30|0 / 1|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0_p0.5|0.0200 [0.0024, 0.0361]|-140.20 [-178.85, -101.56]|-93.5 [-119.5, -67.5]|0.017 [0.008, 0.027]|3 / 3 / 3 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0_p1|0.0217 [0.0013, 0.0398]|-256.48 [-299.24, -213.72]|-171.0 [-200.2, -141.7]|0.017 [0.008, 0.027]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0_p2|0.0329 [0.0146, 0.0488]|-392.73 [-439.89, -345.57]|-261.1 [-293.3, -228.9]|0.017 [0.008, 0.027]|3 / 3 / 3 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p0.5|0.0066 [0.0002, 0.0136]|-127.88 [-153.04, -102.72]|-85.3 [-101.9, -68.8]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p1|0.0116 [0.0041, 0.0208]|-256.06 [-294.39, -217.73]|-170.3 [-195.9, -144.8]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p2|0.0156 [0.0012, 0.0302]|-396.52 [-431.03, -362.02]|-263.8 [-287.0, -240.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p0.5|0.0050 [0.0001, 0.0092]|-101.67 [-120.76, -82.58]|-68.3 [-80.8, -55.8]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p1|0.0075 [0.0008, 0.0160]|-236.23 [-269.53, -202.93]|-156.9 [-179.2, -134.6]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p2|0.0168 [0.0024, 0.0312]|-380.82 [-417.58, -344.06]|-253.4 [-278.1, -228.6]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0_p0.5|0.0113 [0.0027, 0.0214]|-152.88 [-198.57, -107.19]|-101.9 [-132.1, -71.8]|0.017 [0.008, 0.027]|1 / 1 / 0 / 30|0 / 0|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0_p1|0.0138 [0.0053, 0.0238]|-268.33 [-309.57, -227.09]|-178.8 [-206.4, -151.2]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0_p2|0.0165 [0.0013, 0.0317]|-408.36 [-441.64, -375.09]|-271.8 [-294.2, -249.3]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p0.5|0.0175 [-0.0062, 0.0401]|-46.93 [-72.50, -21.37]|-31.9 [-48.7, -15.1]|0.013 [0.001, 0.024]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p1|0.0201 [-0.0031, 0.0451]|-175.56 [-219.31, -131.80]|-116.7 [-145.8, -87.6]|0.017 [0.007, 0.027]|1 / 1 / 1 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p2|0.0333 [0.0084, 0.0562]|-334.40 [-391.77, -277.04]|-222.4 [-260.3, -184.5]|0.017 [0.008, 0.027]|2 / 1 / 1 / 30|0 / 1|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p0.5|0.0214 [-0.0034, 0.0455]|-18.77 [-30.44, -7.11]|-14.0 [-21.7, -6.2]|0.005 [-0.007, 0.018]|2 / 2 / 2 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p1|0.0199 [-0.0008, 0.0409]|-161.14 [-202.96, -119.32]|-107.2 [-135.1, -79.4]|0.017 [0.007, 0.027]|1 / 1 / 1 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p2|0.0283 [0.0038, 0.0508]|-321.03 [-377.28, -264.79]|-213.5 [-250.7, -176.3]|0.017 [0.008, 0.027]|1 / 1 / 1 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0_p0.5|0.0274 [-0.0046, 0.0590]|-63.91 [-98.10, -29.73]|-43.5 [-65.8, -21.1]|0.010 [-0.003, 0.023]|3 / 2 / 2 / 30|0 / 1|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0_p1|0.0267 [-0.0005, 0.0541]|-200.13 [-250.07, -150.20]|-133.0 [-166.1, -99.9]|0.017 [0.008, 0.027]|1 / 1 / 1 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0_p2|0.0336 [0.0150, 0.0529]|-363.74 [-418.24, -309.23]|-242.2 [-278.4, -206.0]|0.017 [0.008, 0.027]|2 / 0 / 0 / 30|0 / 2|0 / 2|0 / 30|
|residual_variance|evidence_curve_a0.025_p0.5|0.0283 [0.0129, 0.0450]|-299.34 [-350.04, -248.65]|-199.3 [-233.4, -165.2]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p1|0.0337 [0.0194, 0.0483]|-434.15 [-469.13, -399.16]|-289.2 [-312.5, -265.8]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p2|0.0419 [0.0204, 0.0642]|-502.19 [-522.47, -481.92]|-334.6 [-348.0, -321.1]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p0.5|0.0267 [0.0101, 0.0435]|-269.94 [-315.74, -224.14]|-180.6 [-211.5, -149.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p1|0.0307 [0.0164, 0.0454]|-417.04 [-450.40, -383.67]|-277.8 [-300.1, -255.5]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p2|0.0406 [0.0204, 0.0620]|-497.59 [-518.24, -476.94]|-331.4 [-345.2, -317.6]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p0.5|0.0307 [0.0165, 0.0449]|-323.87 [-381.20, -266.55]|-215.9 [-254.1, -177.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p1|0.0376 [0.0222, 0.0527]|-442.05 [-477.73, -406.37]|-294.6 [-318.4, -270.8]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p2|0.0429 [0.0213, 0.0651]|-507.88 [-524.26, -491.50]|-338.2 [-349.1, -327.3]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p0.5|0.0348 [0.0195, 0.0485]|-334.10 [-378.47, -289.73]|-222.9 [-252.8, -193.1]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p1|0.0368 [0.0207, 0.0523]|-457.53 [-483.32, -431.75]|-304.8 [-322.1, -287.4]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p2|0.0490 [0.0241, 0.0739]|-508.97 [-525.75, -492.20]|-339.1 [-350.4, -327.8]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p0.5|0.0276 [0.0131, 0.0410]|-301.58 [-341.01, -262.15]|-202.1 [-228.6, -175.6]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p1|0.0328 [0.0173, 0.0474]|-440.14 [-465.21, -415.07]|-293.2 [-310.0, -276.3]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p2|0.0489 [0.0256, 0.0719]|-504.46 [-521.77, -487.15]|-336.1 [-347.8, -324.4]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p0.5|0.0352 [0.0196, 0.0495]|-359.63 [-410.32, -308.93]|-240.1 [-273.9, -206.4]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p1|0.0416 [0.0246, 0.0580]|-465.05 [-491.27, -438.82]|-309.9 [-327.4, -292.3]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p2|0.0498 [0.0250, 0.0733]|-513.16 [-526.22, -500.11]|-341.8 [-350.6, -333.0]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
