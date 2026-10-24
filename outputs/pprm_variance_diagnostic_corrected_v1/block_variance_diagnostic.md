# PPI block estimator variance diagnosis

This design-based diagnosis uses 30 stream seeds per scenario at n=1600, B=20, and 4 uniformly sampled labels per block. Every estimator strategy uses the exact same labeled subset in each block. The conditional finite-population design variance is calculated from the block's evaluator-known values as `(1/n_labeled - 1/B) * S²[z - eta * B/(B-n_labeled) * h]`. This is a conditional variance calculation for simple random sampling without replacement; it does not reveal the values to the learner.

Strategies compare fixed eta values 0, 0.1, 0.5, and 1 with the existing plug-in rule capped at 0.1 or 1.0. The stream prediction is the equally weighted mean of block estimates. These are estimator diagnostics, not monitor power or calibration results.

|Scenario|Strategy|Streams|Empirical stream RMSE|Mean stream error|Stream error SD|Mean predicted design SD|Mean eta|Evaluator oracle eta|Proxy RMSE|Proxy correlation squared|Mean block design variance|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|eta_0|30|0.00753|0.00106|0.00758|0.00962|0.000|0.268|1.39290|0.0010|0.003590|
|boundary_local_harm|eta_0p1|30|0.00752|0.00110|0.00757|0.00963|0.100|0.268|1.39290|0.0010|0.003591|
|boundary_local_harm|eta_0p5|30|0.00755|0.00126|0.00757|0.00968|0.500|0.268|1.39290|0.0010|0.003635|
|boundary_local_harm|eta_1|30|0.00777|0.00147|0.00776|0.00988|1.000|0.268|1.39290|0.0010|0.003783|
|boundary_local_harm|plugin_cap_0p1|30|0.00752|0.00108|0.00757|0.00963|0.040|0.268|1.39290|0.0010|0.003590|
|boundary_local_harm|plugin_cap_1|30|0.00751|0.00109|0.00756|0.00966|0.199|0.268|1.39290|0.0010|0.003619|
|harmful_adaptation|eta_0|30|0.00473|-0.00043|0.00479|0.00481|0.000|0.194|0.77379|0.0036|0.000905|
|harmful_adaptation|eta_0p1|30|0.00474|-0.00039|0.00481|0.00481|0.100|0.194|0.77379|0.0036|0.000906|
|harmful_adaptation|eta_0p5|30|0.00492|-0.00023|0.00500|0.00494|0.500|0.194|0.77379|0.0036|0.000953|
|harmful_adaptation|eta_1|30|0.00540|-0.00003|0.00549|0.00531|1.000|0.194|0.77379|0.0036|0.001102|
|harmful_adaptation|plugin_cap_0p1|30|0.00476|-0.00044|0.00482|0.00481|0.041|0.194|0.77379|0.0036|0.000905|
|harmful_adaptation|plugin_cap_1|30|0.00490|-0.00051|0.00496|0.00484|0.137|0.194|0.77379|0.0036|0.000916|
|recurring_regimes|eta_0|30|0.00487|0.00011|0.00495|0.00802|0.000|0.222|1.16984|0.0007|0.002508|
|recurring_regimes|eta_0p1|30|0.00489|0.00015|0.00497|0.00803|0.100|0.222|1.16984|0.0007|0.002509|
|recurring_regimes|eta_0p5|30|0.00508|0.00032|0.00515|0.00810|0.500|0.222|1.16984|0.0007|0.002556|
|recurring_regimes|eta_1|30|0.00556|0.00052|0.00563|0.00833|1.000|0.222|1.16984|0.0007|0.002705|
|recurring_regimes|plugin_cap_0p1|30|0.00485|0.00012|0.00493|0.00803|0.033|0.222|1.16984|0.0007|0.002509|
|recurring_regimes|plugin_cap_1|30|0.00472|0.00006|0.00480|0.00805|0.105|0.222|1.16984|0.0007|0.002523|
|stationary|eta_0|30|0.00568|-0.00108|0.00567|0.00619|0.000|0.173|0.89640|0.0006|0.001497|
|stationary|eta_0p1|30|0.00562|-0.00104|0.00561|0.00619|0.100|0.173|0.89640|0.0006|0.001499|
|stationary|eta_0p5|30|0.00546|-0.00088|0.00548|0.00629|0.500|0.173|0.89640|0.0006|0.001547|
|stationary|eta_1|30|0.00551|-0.00067|0.00556|0.00659|1.000|0.173|0.89640|0.0006|0.001698|
|stationary|plugin_cap_0p1|30|0.00569|-0.00105|0.00569|0.00619|0.030|0.173|0.89640|0.0006|0.001499|
|stationary|plugin_cap_1|30|0.00568|-0.00106|0.00568|0.00622|0.099|0.173|0.89640|0.0006|0.001513|
