# Common hard label-dollar budget comparison

Evaluated 30 seeds per scenario on `cuda`. Every policy received the same per-stream dollar cap, calibrated from the mean tariff in the pre-monitor validation slice. Methods share per-seed uniform random variates to enable paired comparisons. The maximum tariff support is fixed at 2.5; the monitor stops before the next event once the remaining balance is below that support maximum. This makes every processed event's query propensity positive and predictable, while ensuring spend never exceeds the cap. The monitoring horizon is the full available stream events.

The eventwise e-process monitors use the common configured propensity floor in their support bound; the PPRM-style block confidence sequence instead uses its declared fixed block support.

Each monitor is evaluated only through its budget stopping time. Harm detection is reported both over evaluator-labeled alternative streams and over harmful streams whose onset occurred before budget stopping; the latter avoids calling an unobserved late onset a monitor miss. Stationary and benign-nuisance controls are population nulls; finite-stream oracle flags are reported separately and every alarm on these controls counts as a false escalation. Stream seeds are the inferential units. The outcomes and tariffs are synthetic; current and reference policy costs are paired on the same label.

|Scenario|Method|Mean cap|Mean spend|Mean cap use|Mean labels|Monitor fraction|Stream-mean RMSE|Harm reached / harmful streams|Pathwise oracle flags|Primary detection all / reached|Multiscale detection all / reached|Protected detection all / reached|Primary / multiscale / protected false escalation|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|718.26|603.10|0.840|300.9|0.984|0.0391|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p1|718.26|539.34|0.751|262.6|1.000|0.0399|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.025_p2|718.26|507.78|0.707|245.0|1.000|0.0418|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p0.5|718.26|635.00|0.885|320.6|0.975|0.0409|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p1|718.26|554.73|0.773|270.9|1.000|0.0383|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0.05_p2|718.26|509.29|0.709|245.8|1.000|0.0410|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p0.5|718.26|570.49|0.794|281.8|0.985|0.0407|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p1|718.26|528.94|0.737|256.7|1.000|0.0399|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|evidence_curve_a0_p2|718.26|506.27|0.705|244.1|1.000|0.0425|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|benign_nuisance|uniform_proxy|718.26|716.99|0.998|361.0|0.756|0.0336|0/0|1|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p0.5|718.26|664.89|0.926|442.7|0.979|0.0653|30/30|30|0.533 / 0.533|0.467 / 0.467|0.533 / 0.533|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p1|718.26|597.35|0.831|398.3|0.999|0.0613|30/30|30|0.533 / 0.533|0.500 / 0.500|0.533 / 0.533|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.025_p2|718.26|535.39|0.745|357.6|1.000|0.0719|30/30|30|0.600 / 0.600|0.500 / 0.500|0.600 / 0.600|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p0.5|718.26|683.67|0.952|454.8|0.973|0.0568|30/30|30|0.600 / 0.600|0.533 / 0.533|0.567 / 0.567|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p1|718.26|610.90|0.850|407.1|0.996|0.0624|30/30|30|0.567 / 0.567|0.500 / 0.500|0.533 / 0.533|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0.05_p2|718.26|538.27|0.749|359.5|1.000|0.0714|30/30|30|0.567 / 0.567|0.500 / 0.500|0.533 / 0.533|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p0.5|718.26|647.42|0.901|431.5|0.984|0.0675|30/30|30|0.567 / 0.567|0.500 / 0.500|0.533 / 0.533|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p1|718.26|589.84|0.821|393.3|0.999|0.0614|30/30|30|0.567 / 0.567|0.467 / 0.467|0.567 / 0.567|0.000 / 0.000 / 0.000|
|boundary_local_harm|evidence_curve_a0_p2|718.26|525.20|0.731|351.1|1.000|0.0738|30/30|30|0.567 / 0.567|0.467 / 0.467|0.567 / 0.567|0.000 / 0.000 / 0.000|
|boundary_local_harm|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0486|30/30|30|0.400 / 0.400|0.367 / 0.367|0.400 / 0.400|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p0.5|718.26|677.76|0.944|451.7|0.974|0.0299|30/30|30|0.867 / 0.867|0.767 / 0.767|0.867 / 0.867|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p1|718.26|618.36|0.862|412.9|0.999|0.0345|30/30|30|0.700 / 0.700|0.667 / 0.667|0.700 / 0.700|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.025_p2|718.26|564.63|0.787|377.0|1.000|0.0376|30/30|30|0.700 / 0.700|0.600 / 0.600|0.700 / 0.700|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p0.5|718.26|688.80|0.959|458.5|0.969|0.0316|30/30|30|0.867 / 0.867|0.733 / 0.733|0.767 / 0.767|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p1|718.26|634.75|0.884|423.7|0.996|0.0328|30/30|30|0.767 / 0.767|0.733 / 0.733|0.767 / 0.767|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0.05_p2|718.26|566.16|0.789|378.1|1.000|0.0365|30/30|30|0.667 / 0.667|0.600 / 0.600|0.667 / 0.667|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p0.5|718.26|663.91|0.925|442.8|0.984|0.0283|30/30|30|0.800 / 0.800|0.733 / 0.733|0.767 / 0.767|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p1|718.26|615.32|0.857|411.0|0.999|0.0336|30/30|30|0.733 / 0.733|0.667 / 0.667|0.700 / 0.700|0.000 / 0.000 / 0.000|
|harmful_adaptation|evidence_curve_a0_p2|718.26|556.20|0.775|371.6|1.000|0.0381|30/30|30|0.700 / 0.700|0.600 / 0.600|0.700 / 0.700|0.000 / 0.000 / 0.000|
|harmful_adaptation|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0318|30/30|30|0.800 / 0.800|0.733 / 0.733|0.733 / 0.733|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p0.5|718.26|708.81|0.987|471.3|0.796|0.0651|30/30|30|0.333 / 0.333|0.300 / 0.300|0.333 / 0.333|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p1|718.26|662.15|0.921|440.9|0.910|0.0639|30/30|30|0.400 / 0.400|0.300 / 0.300|0.333 / 0.333|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.025_p2|718.26|593.29|0.826|395.5|0.955|0.0724|30/30|30|0.500 / 0.500|0.467 / 0.467|0.467 / 0.467|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p0.5|718.26|716.62|0.998|476.2|0.766|0.0667|30/30|30|0.300 / 0.300|0.300 / 0.300|0.300 / 0.300|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p1|718.26|669.96|0.932|446.1|0.902|0.0693|30/30|30|0.367 / 0.367|0.300 / 0.300|0.333 / 0.333|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0.05_p2|718.26|599.31|0.834|399.5|0.952|0.0713|30/30|30|0.433 / 0.433|0.400 / 0.400|0.433 / 0.433|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p0.5|718.26|694.23|0.966|462.0|0.819|0.0661|30/30|30|0.367 / 0.367|0.267 / 0.267|0.300 / 0.300|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p1|718.26|652.33|0.908|434.4|0.913|0.0629|30/30|30|0.367 / 0.367|0.267 / 0.267|0.367 / 0.367|0.000 / 0.000 / 0.000|
|recurring_regimes|evidence_curve_a0_p2|718.26|582.34|0.810|388.2|0.956|0.0735|30/30|30|0.500 / 0.500|0.467 / 0.467|0.467 / 0.467|0.000 / 0.000 / 0.000|
|recurring_regimes|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0476|30/30|30|0.533 / 0.533|0.500 / 0.500|0.533 / 0.533|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p0.5|718.26|507.20|0.706|338.1|1.000|0.0446|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p1|718.26|413.71|0.576|276.2|1.000|0.0467|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.025_p2|718.26|372.09|0.518|248.5|1.000|0.0518|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p0.5|718.26|540.12|0.752|359.6|1.000|0.0427|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p1|718.26|431.80|0.601|288.1|1.000|0.0447|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0.05_p2|718.26|375.56|0.523|250.9|1.000|0.0521|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p0.5|718.26|468.58|0.652|312.6|1.000|0.0463|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p1|718.26|401.91|0.560|268.4|1.000|0.0475|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|evidence_curve_a0_p2|718.26|370.33|0.516|247.3|1.000|0.0526|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|residual_variance|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0351|30/30|30|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p0.5|718.26|463.52|0.646|309.0|1.000|0.0367|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p1|718.26|394.77|0.550|263.5|1.000|0.0386|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.025_p2|718.26|367.13|0.511|245.2|1.000|0.0431|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p0.5|718.26|498.12|0.694|331.7|1.000|0.0351|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p1|718.26|408.88|0.570|272.9|1.000|0.0370|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0.05_p2|718.26|368.44|0.513|246.1|1.000|0.0423|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p0.5|718.26|432.53|0.602|288.6|1.000|0.0376|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p1|718.26|385.48|0.537|257.4|1.000|0.0387|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|evidence_curve_a0_p2|718.26|365.94|0.510|244.4|1.000|0.0439|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|
|stationary|uniform_proxy|718.26|704.08|0.980|469.7|0.983|0.0279|0/0|0|n/a / n/a|n/a / n/a|n/a / n/a|0.000 / 0.000 / 0.000|

## Full-horizon consistency check

Each monitor is evaluated only through its hard-budget stopping time. The eventwise monitors are e-processes; the PPI block comparator is a Hoeffding-mixture confidence sequence for the running average of predictable block means. It does not reproduce PPRM's empirical-Bernstein bound. Any comparison with a full-monitor baseline must use matching stream seeds and query random numbers.

The fixed-stake baseline uses (0.05, 0.10, 0.20, 0.40, 0.80). The multiscale comparator uses 13 equally weighted geometric stakes from 1/1024 to 0.99. Both are fixed mixtures of factors `1 + eta * X / B`; under the same predictable conditional-mean null and `|X| <= B`, each mixture remains an e-process. The multiscale comparator is a predeclared robustness baseline, not a new validity theorem.
The protected mixture assigns 0.90 total initial weight equally to the five fixed stakes and 0.10 equally to eight geometric stakes from 1/1024 to 0.04. Its weights and support are fixed before evaluation, so it has the same e-process guarantee; it tests whether preserving baseline mass avoids dilution while retaining smaller-scale sensitivity.

## Interpretation limits

This is an allocation and monitor comparison under a finite spend cap, not an intervention controller or a new theorem. The hard-cap stopping time is based on past realized spend, not current evaluator truth. Eventwise e-process validity requires the documented bounded-increment conditional-mean null and predictable query probabilities. The PPI block confidence sequence assumes bounded block estimates and valid predictable block means; its Hoeffding boundary is conservative and does not provide PPRM's empirical-Bernstein efficiency. Early budget exhaustion censors later harm onsets; report both reachability and detection. Realized label dollars are bounded, while the number of labels and monitor horizon remain random. The saved sum of per-event `q_t * cost_t` is a predictable-spend compensator along the realized stopping path; its pathwise sum can exceed the hard cap and it must not be read as realized spend.

Reproduce with `uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 31025000 --n 3200 --d 16 --budget-rate 0.2 --monitor-estimator direct_ipw --q-min 0.1 --q-max 0.8 --device cuda --exact-growth-adaptive-weight 1.0 --robust-growth-probability-radius 0.0 --robust-active-inference-radius-fraction 0.5 --pprm-block-size 20 --pprm-labels-per-block 4 --pprm-max-reliance 1.0 --pprm-initial-reliance 1.0 --scenarios stationary benign_nuisance boundary_local_harm residual_variance recurring_regimes harmful_adaptation --methods uniform_proxy evidence_curve_a0_p0.5 evidence_curve_a0_p1 evidence_curve_a0_p2 evidence_curve_a0.025_p0.5 evidence_curve_a0.025_p1 evidence_curve_a0.025_p2 evidence_curve_a0.05_p0.5 evidence_curve_a0.05_p1 evidence_curve_a0.05_p2 --common-eprocess-bound --skip-figure --output outputs/direct_ipw_query_development_30_w4/runs/q_min_0p10`.


No figure was generated for this run; PaperBanana is unavailable in the active environment.

## Paired comparison against uniform sampling

RMSE intervals are paired percentile bootstraps over independent seeds (20,000 resamples). Spend, label-count and monitor-fraction intervals are paired t intervals. They are descriptive and do not adjust for selecting a method after seeing this grid.

|Scenario|Method|RMSE difference (95% bootstrap CI)|Spend difference (95% t CI)|Label difference (95% t CI)|Monitor-fraction difference (95% t CI)|Primary / multiscale / protected detections / reached|Multiscale-only / primary-only|Protected-only / primary-only|Protected false escalations / streams|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.025_p0.5|0.0056 [-0.0087, 0.0203]|-113.89 [-144.01, -83.77]|-60.1 [-78.1, -42.2]|0.228 [0.210, 0.245]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p1|0.0063 [-0.0089, 0.0219]|-177.64 [-198.57, -156.72]|-98.5 [-109.8, -87.1]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.025_p2|0.0083 [-0.0081, 0.0257]|-209.21 [-221.88, -196.54]|-116.1 [-122.0, -110.1]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p0.5|0.0074 [-0.0081, 0.0241]|-81.98 [-108.21, -55.75]|-40.5 [-56.0, -24.9]|0.219 [0.199, 0.239]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p1|0.0048 [-0.0088, 0.0196]|-162.26 [-185.41, -139.11]|-90.1 [-102.5, -77.7]|0.243 [0.234, 0.253]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0.05_p2|0.0075 [-0.0084, 0.0241]|-207.70 [-220.55, -194.85]|-115.2 [-121.3, -109.1]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p0.5|0.0072 [-0.0089, 0.0241]|-146.49 [-178.26, -114.72]|-79.2 [-98.0, -60.4]|0.229 [0.212, 0.245]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p1|0.0064 [-0.0094, 0.0230]|-188.04 [-207.18, -168.91]|-104.3 [-114.6, -94.0]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|benign_nuisance|evidence_curve_a0_p2|0.0089 [-0.0080, 0.0266]|-210.72 [-223.29, -198.14]|-116.9 [-122.7, -111.1]|0.244 [0.234, 0.254]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p0.5|0.0166 [0.0033, 0.0294]|-39.18 [-64.62, -13.74]|-27.0 [-43.9, -10.1]|-0.003 [-0.019, 0.013]|16 / 14 / 16 / 30|0 / 2|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p1|0.0127 [-0.0024, 0.0269]|-106.72 [-141.76, -71.69]|-71.5 [-95.1, -47.8]|0.016 [0.006, 0.027]|16 / 15 / 16 / 30|0 / 1|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.025_p2|0.0233 [0.0071, 0.0373]|-168.68 [-211.91, -125.46]|-112.1 [-141.1, -83.1]|0.017 [0.007, 0.027]|18 / 15 / 18 / 30|0 / 3|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p0.5|0.0081 [-0.0075, 0.0230]|-20.41 [-40.88, 0.06]|-14.9 [-28.6, -1.2]|-0.010 [-0.027, 0.008]|18 / 16 / 17 / 30|0 / 2|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p1|0.0138 [-0.0010, 0.0271]|-93.18 [-126.27, -60.08]|-62.7 [-85.0, -40.4]|0.014 [0.002, 0.025]|17 / 15 / 16 / 30|0 / 2|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0.05_p2|0.0228 [0.0062, 0.0367]|-165.81 [-208.32, -123.30]|-110.3 [-138.7, -81.8]|0.017 [0.007, 0.027]|17 / 15 / 16 / 30|0 / 2|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0_p0.5|0.0189 [0.0041, 0.0329]|-56.66 [-85.98, -27.33]|-38.2 [-58.0, -18.5]|0.002 [-0.014, 0.018]|17 / 15 / 16 / 30|0 / 2|0 / 1|0 / 30|
|boundary_local_harm|evidence_curve_a0_p1|0.0128 [-0.0035, 0.0273]|-114.23 [-150.44, -78.03]|-76.5 [-100.8, -52.1]|0.016 [0.006, 0.027]|17 / 14 / 17 / 30|0 / 3|0 / 0|0 / 30|
|boundary_local_harm|evidence_curve_a0_p2|0.0252 [0.0090, 0.0393]|-178.88 [-221.78, -135.97]|-118.7 [-147.6, -89.8]|0.017 [0.008, 0.027]|17 / 14 / 17 / 30|0 / 3|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p0.5|-0.0019 [-0.0084, 0.0063]|-26.31 [-41.71, -10.91]|-18.0 [-28.0, -8.1]|-0.008 [-0.028, 0.012]|26 / 23 / 26 / 30|0 / 3|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p1|0.0027 [-0.0039, 0.0108]|-85.71 [-111.35, -60.07]|-56.8 [-73.8, -39.8]|0.016 [0.006, 0.027]|21 / 20 / 21 / 30|0 / 1|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.025_p2|0.0058 [-0.0049, 0.0175]|-139.45 [-175.18, -103.71]|-92.7 [-116.7, -68.7]|0.017 [0.008, 0.027]|21 / 18 / 21 / 30|0 / 3|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p0.5|-0.0002 [-0.0057, 0.0063]|-15.27 [-28.48, -2.06]|-11.3 [-19.6, -2.9]|-0.014 [-0.034, 0.007]|26 / 22 / 23 / 30|0 / 4|0 / 3|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p1|0.0010 [-0.0044, 0.0083]|-69.33 [-90.69, -47.97]|-46.1 [-60.1, -32.0]|0.013 [0.001, 0.026]|23 / 22 / 23 / 30|0 / 1|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0.05_p2|0.0047 [-0.0056, 0.0161]|-137.92 [-172.14, -103.70]|-91.6 [-114.7, -68.6]|0.017 [0.008, 0.027]|20 / 18 / 20 / 30|0 / 2|0 / 0|0 / 30|
|harmful_adaptation|evidence_curve_a0_p0.5|-0.0035 [-0.0093, 0.0036]|-40.17 [-59.77, -20.57]|-27.0 [-39.8, -14.1]|0.001 [-0.017, 0.019]|24 / 22 / 23 / 30|0 / 2|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0_p1|0.0018 [-0.0051, 0.0103]|-88.75 [-114.00, -63.50]|-58.7 [-75.5, -42.0]|0.017 [0.007, 0.027]|22 / 20 / 21 / 30|0 / 2|0 / 1|0 / 30|
|harmful_adaptation|evidence_curve_a0_p2|0.0063 [-0.0050, 0.0184]|-147.88 [-184.51, -111.25]|-98.2 [-122.8, -73.5]|0.017 [0.008, 0.027]|21 / 18 / 21 / 30|0 / 3|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p0.5|0.0175 [0.0001, 0.0366]|4.74 [-8.65, 18.12]|1.6 [-7.0, 10.2]|-0.186 [-0.226, -0.147]|10 / 9 / 10 / 30|0 / 1|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p1|0.0163 [-0.0029, 0.0358]|-41.93 [-75.70, -8.16]|-28.8 [-51.3, -6.3]|-0.073 [-0.114, -0.031]|12 / 9 / 10 / 30|0 / 3|0 / 2|0 / 30|
|recurring_regimes|evidence_curve_a0.025_p2|0.0248 [0.0043, 0.0449]|-110.78 [-156.46, -65.11]|-74.3 [-104.5, -44.0]|-0.027 [-0.065, 0.010]|15 / 14 / 14 / 30|0 / 1|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p0.5|0.0191 [0.0018, 0.0386]|12.54 [5.84, 19.25]|6.5 [1.9, 11.1]|-0.216 [-0.246, -0.186]|9 / 9 / 9 / 30|0 / 0|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p1|0.0217 [0.0024, 0.0418]|-34.11 [-65.67, -2.56]|-23.6 [-44.7, -2.5]|-0.081 [-0.121, -0.040]|11 / 9 / 10 / 30|0 / 2|0 / 1|0 / 30|
|recurring_regimes|evidence_curve_a0.05_p2|0.0237 [0.0035, 0.0436]|-104.77 [-149.33, -60.20]|-70.3 [-99.8, -40.8]|-0.030 [-0.067, 0.007]|13 / 12 / 13 / 30|0 / 1|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0_p0.5|0.0184 [-0.0034, 0.0407]|-9.85 [-35.31, 15.61]|-7.7 [-24.7, 9.2]|-0.164 [-0.205, -0.123]|11 / 8 / 9 / 30|0 / 3|0 / 2|0 / 30|
|recurring_regimes|evidence_curve_a0_p1|0.0152 [-0.0027, 0.0347]|-51.74 [-88.72, -14.76]|-35.3 [-59.8, -10.9]|-0.069 [-0.110, -0.029]|11 / 8 / 11 / 30|0 / 3|0 / 0|0 / 30|
|recurring_regimes|evidence_curve_a0_p2|0.0259 [0.0051, 0.0463]|-121.74 [-168.41, -75.06]|-81.6 [-112.4, -50.7]|-0.027 [-0.064, 0.011]|15 / 14 / 14 / 30|0 / 1|0 / 1|0 / 30|
|residual_variance|evidence_curve_a0.025_p0.5|0.0095 [0.0000, 0.0189]|-196.87 [-233.15, -160.60]|-131.7 [-155.7, -107.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p1|0.0116 [0.0028, 0.0209]|-290.36 [-312.53, -268.20]|-193.6 [-208.4, -178.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.025_p2|0.0167 [0.0044, 0.0298]|-331.98 [-344.19, -319.77]|-221.2 [-229.2, -213.2]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p0.5|0.0076 [-0.0021, 0.0176]|-163.96 [-196.64, -131.27]|-110.2 [-132.0, -88.3]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p1|0.0096 [0.0015, 0.0185]|-272.28 [-295.14, -249.41]|-181.7 [-197.0, -166.4]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0.05_p2|0.0170 [0.0054, 0.0293]|-328.52 [-341.93, -315.11]|-218.8 [-227.5, -210.1]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p0.5|0.0112 [0.0016, 0.0214]|-235.50 [-273.19, -197.81]|-157.2 [-182.5, -131.9]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p1|0.0124 [0.0031, 0.0220]|-302.17 [-323.64, -280.69]|-201.4 [-215.7, -187.1]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|residual_variance|evidence_curve_a0_p2|0.0175 [0.0048, 0.0311]|-333.74 [-345.61, -321.88]|-222.5 [-230.2, -214.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 30|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p0.5|0.0088 [-0.0014, 0.0196]|-240.56 [-273.89, -207.23]|-160.8 [-182.8, -138.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p1|0.0108 [-0.0000, 0.0228]|-309.31 [-327.35, -291.26]|-206.2 [-218.3, -194.1]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.025_p2|0.0152 [0.0012, 0.0314]|-336.95 [-347.36, -326.54]|-224.5 [-231.4, -217.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p0.5|0.0073 [-0.0026, 0.0177]|-205.96 [-237.01, -174.91]|-138.0 [-158.7, -117.4]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p1|0.0091 [-0.0004, 0.0200]|-295.20 [-315.03, -275.36]|-196.9 [-210.1, -183.6]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0.05_p2|0.0144 [0.0010, 0.0298]|-335.63 [-346.08, -325.18]|-223.6 [-230.5, -216.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p0.5|0.0097 [-0.0011, 0.0216]|-271.55 [-306.15, -236.94]|-181.1 [-204.3, -158.0]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p1|0.0108 [-0.0005, 0.0235]|-318.60 [-335.20, -301.99]|-212.3 [-223.4, -201.3]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
|stationary|evidence_curve_a0_p2|0.0161 [0.0015, 0.0325]|-338.14 [-348.36, -327.91]|-225.4 [-232.1, -218.7]|0.017 [0.008, 0.027]|0 / 0 / 0 / 0|0 / 0|0 / 0|0 / 30|
