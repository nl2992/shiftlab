# Policy-specific-bound harmful-stream confirmation

This report compares five label-query policies at a matched 20% pathwise dollar cap, with policy-specific propensity support bounds. It is evidence only for the registered synthetic streams and does not establish a deployment guarantee or algorithmic novelty.

GPU: `NVIDIA GeForce RTX 4060 Laptop GPU`; resolved device: `cuda`; independent seeds: 200 per scenario; seed block: `55000000–55000199`.

## Detection outcomes

|Scenario|Policy|Monitor|Material streams|Onsets reached|Detections|Rate (Wilson 95%)|Rate among reached|Mean delay if detected|Mean labels|Mean spend / cap|Mean events|Mean RMSE|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|fixed_mixture|200|200|10|0.050 [0.027, 0.090]|0.050|1355.2|516.3|708.80 / 720.63|2351.8|2.4272|
|boundary_local_harm|cost_stabilized_proxy|predictable_variance|200|200|3|0.015 [0.005, 0.043]|0.015|1445.7|516.3|708.80 / 720.63|2351.8|2.4272|
|boundary_local_harm|cost_stabilized_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|516.3|708.80 / 720.63|2351.8|2.4272|
|boundary_local_harm|cost_variance_proxy|fixed_mixture|200|200|12|0.060 [0.035, 0.102]|0.060|1384.2|495.0|709.90 / 720.63|2340.5|2.5735|
|boundary_local_harm|cost_variance_proxy|predictable_variance|200|200|4|0.020 [0.008, 0.050]|0.020|1413.8|495.0|709.90 / 720.63|2340.5|2.5735|
|boundary_local_harm|cost_variance_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|495.0|709.90 / 720.63|2340.5|2.5735|
|boundary_local_harm|decision_value_proxy|fixed_mixture|200|200|11|0.055 [0.031, 0.096]|0.055|1411.5|470.3|704.83 / 720.63|2303.1|2.6864|
|boundary_local_harm|decision_value_proxy|predictable_variance|200|200|5|0.025 [0.011, 0.057]|0.025|1573.2|470.3|704.83 / 720.63|2303.1|2.6864|
|boundary_local_harm|decision_value_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|470.3|704.83 / 720.63|2303.1|2.6864|
|boundary_local_harm|uniform_proxy|fixed_mixture|200|200|135|0.675 [0.607, 0.736]|0.675|1128.9|471.5|707.10 / 720.63|2353.9|2.4404|
|boundary_local_harm|uniform_proxy|predictable_variance|200|200|115|0.575 [0.506, 0.641]|0.575|1167.6|471.5|707.10 / 720.63|2353.9|2.4404|
|boundary_local_harm|uniform_proxy|pm_eb|200|200|6|0.030 [0.014, 0.064]|0.030|1382.7|471.5|707.10 / 720.63|2353.9|2.4404|
|boundary_local_harm|variance_proxy|fixed_mixture|200|200|10|0.050 [0.027, 0.090]|0.050|1257.5|473.7|709.79 / 720.63|2338.7|2.6125|
|boundary_local_harm|variance_proxy|predictable_variance|200|200|5|0.025 [0.011, 0.057]|0.025|1334.0|473.7|709.79 / 720.63|2338.7|2.6125|
|boundary_local_harm|variance_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|473.7|709.79 / 720.63|2338.7|2.6125|
|harmful_adaptation|cost_stabilized_proxy|fixed_mixture|200|200|5|0.025 [0.011, 0.057]|0.025|1684.0|516.3|708.80 / 720.63|2351.8|1.5036|
|harmful_adaptation|cost_stabilized_proxy|predictable_variance|200|200|0|0.000 [0.000, 0.019]|0.000|nan|516.3|708.80 / 720.63|2351.8|1.5036|
|harmful_adaptation|cost_stabilized_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|516.3|708.80 / 720.63|2351.8|1.5036|
|harmful_adaptation|cost_variance_proxy|fixed_mixture|200|200|3|0.015 [0.005, 0.043]|0.015|1409.0|495.0|709.90 / 720.63|2340.5|1.5930|
|harmful_adaptation|cost_variance_proxy|predictable_variance|200|200|1|0.005 [0.001, 0.028]|0.005|1287.0|495.0|709.90 / 720.63|2340.5|1.5930|
|harmful_adaptation|cost_variance_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|495.0|709.90 / 720.63|2340.5|1.5930|
|harmful_adaptation|decision_value_proxy|fixed_mixture|200|200|8|0.040 [0.020, 0.077]|0.040|1434.8|473.1|709.45 / 720.63|2294.6|1.6805|
|harmful_adaptation|decision_value_proxy|predictable_variance|200|200|1|0.005 [0.001, 0.028]|0.005|1591.0|473.1|709.45 / 720.63|2294.6|1.6805|
|harmful_adaptation|decision_value_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|473.1|709.45 / 720.63|2294.6|1.6805|
|harmful_adaptation|uniform_proxy|fixed_mixture|200|200|175|0.875 [0.822, 0.914]|0.875|1141.4|471.5|707.10 / 720.63|2353.9|1.5151|
|harmful_adaptation|uniform_proxy|predictable_variance|200|200|165|0.825 [0.766, 0.871]|0.825|1234.8|471.5|707.10 / 720.63|2353.9|1.5151|
|harmful_adaptation|uniform_proxy|pm_eb|200|200|4|0.020 [0.008, 0.050]|0.020|1345.0|471.5|707.10 / 720.63|2353.9|1.5151|
|harmful_adaptation|variance_proxy|fixed_mixture|200|200|5|0.025 [0.011, 0.057]|0.025|1420.6|473.7|709.79 / 720.63|2338.7|1.6200|
|harmful_adaptation|variance_proxy|predictable_variance|200|200|1|0.005 [0.001, 0.028]|0.005|1287.0|473.7|709.79 / 720.63|2338.7|1.6200|
|harmful_adaptation|variance_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|473.7|709.79 / 720.63|2338.7|1.6200|
|recurring_regimes|cost_stabilized_proxy|fixed_mixture|200|200|7|0.035 [0.017, 0.070]|0.035|2222.3|516.3|708.80 / 720.63|2351.8|2.4256|
|recurring_regimes|cost_stabilized_proxy|predictable_variance|200|200|3|0.015 [0.005, 0.043]|0.015|2166.7|516.3|708.80 / 720.63|2351.8|2.4256|
|recurring_regimes|cost_stabilized_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|516.3|708.80 / 720.63|2351.8|2.4256|
|recurring_regimes|cost_variance_proxy|fixed_mixture|200|200|14|0.070 [0.042, 0.114]|0.070|2194.1|495.0|709.90 / 720.63|2340.5|2.5718|
|recurring_regimes|cost_variance_proxy|predictable_variance|200|200|11|0.055 [0.031, 0.096]|0.055|2274.4|495.0|709.90 / 720.63|2340.5|2.5718|
|recurring_regimes|cost_variance_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|495.0|709.90 / 720.63|2340.5|2.5718|
|recurring_regimes|decision_value_proxy|fixed_mixture|200|200|17|0.085 [0.054, 0.132]|0.085|2189.9|464.4|696.97 / 720.63|2334.2|2.7350|
|recurring_regimes|decision_value_proxy|predictable_variance|200|200|13|0.065 [0.038, 0.108]|0.065|2211.2|464.4|696.97 / 720.63|2334.2|2.7350|
|recurring_regimes|decision_value_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|464.4|696.97 / 720.63|2334.2|2.7350|
|recurring_regimes|uniform_proxy|fixed_mixture|200|200|135|0.675 [0.607, 0.736]|0.675|1605.5|471.5|707.10 / 720.63|2353.9|2.4392|
|recurring_regimes|uniform_proxy|predictable_variance|200|200|134|0.670 [0.602, 0.731]|0.670|1726.5|471.5|707.10 / 720.63|2353.9|2.4392|
|recurring_regimes|uniform_proxy|pm_eb|200|200|11|0.055 [0.031, 0.096]|0.055|2290.4|471.5|707.10 / 720.63|2353.9|2.4392|
|recurring_regimes|variance_proxy|fixed_mixture|200|200|17|0.085 [0.054, 0.132]|0.085|2185.9|473.7|709.79 / 720.63|2338.7|2.6061|
|recurring_regimes|variance_proxy|predictable_variance|200|200|11|0.055 [0.031, 0.096]|0.055|2236.4|473.7|709.79 / 720.63|2338.7|2.6061|
|recurring_regimes|variance_proxy|pm_eb|200|200|0|0.000 [0.000, 0.019]|0.000|nan|473.7|709.79 / 720.63|2338.7|2.6061|

## Paired primary comparisons

The primary monitor is the fixed mixture. Each adaptive policy is compared with uniform by a one-sided exact McNemar test across paired seed streams; Holm adjustment covers all 12 policy-by-scenario tests.

|Scenario|Policy vs uniform|Method-only / uniform-only|Paired rate difference (bootstrap 95%)|Exact p|Holm p|
|---|---|---:|---:|---:|---:|
|boundary_local_harm|variance_proxy|0 / 125|-0.625 [-0.690, -0.560]|1|1|
|boundary_local_harm|decision_value_proxy|0 / 124|-0.620 [-0.685, -0.550]|1|1|
|boundary_local_harm|cost_variance_proxy|0 / 123|-0.615 [-0.680, -0.550]|1|1|
|boundary_local_harm|cost_stabilized_proxy|0 / 125|-0.625 [-0.690, -0.560]|1|1|
|recurring_regimes|variance_proxy|0 / 118|-0.590 [-0.660, -0.520]|1|1|
|recurring_regimes|decision_value_proxy|0 / 118|-0.590 [-0.655, -0.520]|1|1|
|recurring_regimes|cost_variance_proxy|0 / 121|-0.605 [-0.670, -0.535]|1|1|
|recurring_regimes|cost_stabilized_proxy|0 / 128|-0.640 [-0.705, -0.570]|1|1|
|harmful_adaptation|variance_proxy|0 / 170|-0.850 [-0.895, -0.800]|1|1|
|harmful_adaptation|decision_value_proxy|0 / 167|-0.835 [-0.885, -0.785]|1|1|
|harmful_adaptation|cost_variance_proxy|0 / 172|-0.860 [-0.905, -0.810]|1|1|
|harmful_adaptation|cost_stabilized_proxy|0 / 170|-0.850 [-0.900, -0.800]|1|1|

A query policy shows a confirmatory detection improvement only where its adjusted p-value is below 0.05 and its paired effect is positive. All nondetections remain in the all-material-harm denominator; rates among onset-reached streams are reported separately. The event horizon can vary under the shared hard dollar cap, so these results compare resource-constrained policies rather than fixed-horizon monitors.

No figure was generated because this frozen protocol specifies no figures.
