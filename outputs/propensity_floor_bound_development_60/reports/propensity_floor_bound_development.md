# Propensity-floor and e-process bound development grid

This is a frozen development grid. The 60-seed null cells are descriptive and do not establish a 5% false-escalation guarantee; harmful-stream comparisons do not select a confirmatory winner.

CUDA: `NVIDIA GeForce RTX 4060 Laptop GPU`; seed block `56000000–56000059` paired across q_min values; 3000 stream-policy rows.

The fixed registered bound is valid only under the registered conditional-on-past null and support assumptions. The eventwise q_t bound requires the stronger conditional null given current context and bound-selection information. Eventwise rates below are uncalibrated sensitivity diagnostics, not valid population-null rates or evidence for deployment.

## Detection and false-escalation summaries

|q_min|Scenario|Policy|Monitor|Harm / streams|Onsets reached|Detections|Rate (Wilson 95%)|Null false / streams|Mean q|Mean labels|Mean spend / cap|Mean events|
|---:|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
## Execution note

The 3,000-row Parquet file and run manifest were written before the process returned exit code 1 while printing the workspace path through the Windows cp1252 console. The complete metrics and run-time source hashes were verified against the recorded Git commit; this analyzer then validated all rows and checksums. The runner now prints an escaped ASCII path. Data generation was not repeated.

|0.10|benign_nuisance|cost_stabilized_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.162|377.0|713.08 / 720.70|2319.3|
|0.10|benign_nuisance|cost_stabilized_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.162|377.0|713.08 / 720.70|2319.3|
|0.10|benign_nuisance|cost_stabilized_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.162|377.0|713.08 / 720.70|2319.3|
|0.10|benign_nuisance|cost_variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.241|371.6|717.81 / 720.70|1555.7|
|0.10|benign_nuisance|cost_variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.241|371.6|717.81 / 720.70|1555.7|
|0.10|benign_nuisance|cost_variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.241|371.6|717.81 / 720.70|1555.7|
|0.10|benign_nuisance|decision_value_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.251|364.5|718.20 / 720.70|1475.3|
|0.10|benign_nuisance|decision_value_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.251|364.5|718.20 / 720.70|1475.3|
|0.10|benign_nuisance|decision_value_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.251|364.5|718.20 / 720.70|1475.3|
|0.10|benign_nuisance|uniform_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.200|363.1|719.32 / 720.70|1809.5|
|0.10|benign_nuisance|uniform_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.200|363.1|719.32 / 720.70|1809.5|
|0.10|benign_nuisance|uniform_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.200|363.1|719.32 / 720.70|1809.5|
|0.10|benign_nuisance|variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.260|364.5|719.41 / 720.70|1418.0|
|0.10|benign_nuisance|variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.260|364.5|719.41 / 720.70|1418.0|
|0.10|benign_nuisance|variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.260|364.5|719.41 / 720.70|1418.0|
|0.10|boundary_local_harm|cost_stabilized_proxy|registered_bound|60|60|5|0.083 [0.036, 0.181]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|boundary_local_harm|cost_stabilized_proxy|common_q010|60|60|5|0.083 [0.036, 0.181]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|boundary_local_harm|cost_stabilized_proxy|eventwise_qt_diagnostic|60|60|47|0.783 [0.664, 0.869]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|boundary_local_harm|cost_variance_proxy|registered_bound|60|60|6|0.100 [0.047, 0.201]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|boundary_local_harm|cost_variance_proxy|common_q010|60|60|6|0.100 [0.047, 0.201]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|boundary_local_harm|cost_variance_proxy|eventwise_qt_diagnostic|60|60|47|0.783 [0.664, 0.869]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|boundary_local_harm|decision_value_proxy|registered_bound|60|60|6|0.100 [0.047, 0.201]|0/0|0.206|470.7|705.63 / 720.70|2301.8|
|0.10|boundary_local_harm|decision_value_proxy|common_q010|60|60|6|0.100 [0.047, 0.201]|0/0|0.206|470.7|705.63 / 720.70|2301.8|
|0.10|boundary_local_harm|decision_value_proxy|eventwise_qt_diagnostic|60|60|39|0.650 [0.524, 0.758]|0/0|0.206|470.7|705.63 / 720.70|2301.8|
|0.10|boundary_local_harm|uniform_proxy|registered_bound|60|60|38|0.633 [0.507, 0.744]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|boundary_local_harm|uniform_proxy|common_q010|60|60|8|0.133 [0.069, 0.242]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|boundary_local_harm|uniform_proxy|eventwise_qt_diagnostic|60|60|38|0.633 [0.507, 0.744]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|boundary_local_harm|variance_proxy|registered_bound|60|60|6|0.100 [0.047, 0.201]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|boundary_local_harm|variance_proxy|common_q010|60|60|6|0.100 [0.047, 0.201]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|boundary_local_harm|variance_proxy|eventwise_qt_diagnostic|60|60|41|0.683 [0.558, 0.787]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|harmful_adaptation|cost_stabilized_proxy|registered_bound|60|60|0|0.000 [0.000, 0.060]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|harmful_adaptation|cost_stabilized_proxy|common_q010|60|60|0|0.000 [0.000, 0.060]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|harmful_adaptation|cost_stabilized_proxy|eventwise_qt_diagnostic|60|60|56|0.933 [0.841, 0.974]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|harmful_adaptation|cost_variance_proxy|registered_bound|60|60|0|0.000 [0.000, 0.060]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|harmful_adaptation|cost_variance_proxy|common_q010|60|60|0|0.000 [0.000, 0.060]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|harmful_adaptation|cost_variance_proxy|eventwise_qt_diagnostic|60|60|56|0.933 [0.841, 0.974]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|harmful_adaptation|decision_value_proxy|registered_bound|60|60|1|0.017 [0.003, 0.089]|0/0|0.207|472.6|708.79 / 720.70|2295.5|
|0.10|harmful_adaptation|decision_value_proxy|common_q010|60|60|1|0.017 [0.003, 0.089]|0/0|0.207|472.6|708.79 / 720.70|2295.5|
|0.10|harmful_adaptation|decision_value_proxy|eventwise_qt_diagnostic|60|60|48|0.800 [0.682, 0.882]|0/0|0.207|472.6|708.79 / 720.70|2295.5|
|0.10|harmful_adaptation|uniform_proxy|registered_bound|60|60|53|0.883 [0.778, 0.942]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|harmful_adaptation|uniform_proxy|common_q010|60|60|0|0.000 [0.000, 0.060]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|harmful_adaptation|uniform_proxy|eventwise_qt_diagnostic|60|60|53|0.883 [0.778, 0.942]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|harmful_adaptation|variance_proxy|registered_bound|60|60|1|0.017 [0.003, 0.089]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|harmful_adaptation|variance_proxy|common_q010|60|60|1|0.017 [0.003, 0.089]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|harmful_adaptation|variance_proxy|eventwise_qt_diagnostic|60|60|56|0.933 [0.841, 0.974]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|recurring_regimes|cost_stabilized_proxy|registered_bound|60|60|7|0.117 [0.058, 0.222]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|recurring_regimes|cost_stabilized_proxy|common_q010|60|60|7|0.117 [0.058, 0.222]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|recurring_regimes|cost_stabilized_proxy|eventwise_qt_diagnostic|60|60|48|0.800 [0.682, 0.882]|0/0|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|recurring_regimes|cost_variance_proxy|registered_bound|60|60|5|0.083 [0.036, 0.181]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|recurring_regimes|cost_variance_proxy|common_q010|60|60|5|0.083 [0.036, 0.181]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|recurring_regimes|cost_variance_proxy|eventwise_qt_diagnostic|60|60|45|0.750 [0.628, 0.842]|0/0|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|recurring_regimes|decision_value_proxy|registered_bound|60|60|6|0.100 [0.047, 0.201]|0/0|0.199|465.3|697.70 / 720.70|2341.9|
|0.10|recurring_regimes|decision_value_proxy|common_q010|60|60|6|0.100 [0.047, 0.201]|0/0|0.199|465.3|697.70 / 720.70|2341.9|
|0.10|recurring_regimes|decision_value_proxy|eventwise_qt_diagnostic|60|60|42|0.700 [0.575, 0.801]|0/0|0.199|465.3|697.70 / 720.70|2341.9|
|0.10|recurring_regimes|uniform_proxy|registered_bound|60|60|40|0.667 [0.541, 0.773]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|recurring_regimes|uniform_proxy|common_q010|60|60|4|0.067 [0.026, 0.159]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|recurring_regimes|uniform_proxy|eventwise_qt_diagnostic|60|60|40|0.667 [0.541, 0.773]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|recurring_regimes|variance_proxy|registered_bound|60|60|7|0.117 [0.058, 0.222]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|recurring_regimes|variance_proxy|common_q010|60|60|7|0.117 [0.058, 0.222]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|recurring_regimes|variance_proxy|eventwise_qt_diagnostic|60|60|43|0.717 [0.592, 0.815]|0/0|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|stationary|cost_stabilized_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|stationary|cost_stabilized_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|stationary|cost_stabilized_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.219|517.2|709.35 / 720.70|2358.8|
|0.10|stationary|cost_variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|stationary|cost_variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|stationary|cost_variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.212|495.7|710.49 / 720.70|2342.0|
|0.10|stationary|decision_value_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.211|476.7|713.94 / 720.70|2265.0|
|0.10|stationary|decision_value_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.211|476.7|713.94 / 720.70|2265.0|
|0.10|stationary|decision_value_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.211|476.7|713.94 / 720.70|2265.0|
|0.10|stationary|uniform_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|stationary|uniform_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|stationary|uniform_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.200|471.2|706.14 / 720.70|2358.6|
|0.10|stationary|variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|stationary|variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.203|474.4|710.10 / 720.70|2342.2|
|0.10|stationary|variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.203|474.4|710.10 / 720.70|2342.2|
|0.11|benign_nuisance|cost_stabilized_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.162|376.9|712.90 / 720.70|2319.8|
|0.11|benign_nuisance|cost_stabilized_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.162|376.9|712.90 / 720.70|2319.8|
|0.11|benign_nuisance|cost_stabilized_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.162|376.9|712.90 / 720.70|2319.8|
|0.11|benign_nuisance|cost_variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.240|371.6|718.36 / 720.70|1560.8|
|0.11|benign_nuisance|cost_variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.240|371.6|718.36 / 720.70|1560.8|
|0.11|benign_nuisance|cost_variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.240|371.6|718.36 / 720.70|1560.8|
|0.11|benign_nuisance|decision_value_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.250|364.2|718.45 / 720.70|1479.0|
|0.11|benign_nuisance|decision_value_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.250|364.2|718.45 / 720.70|1479.0|
|0.11|benign_nuisance|decision_value_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.250|364.2|718.45 / 720.70|1479.0|
|0.11|benign_nuisance|uniform_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.200|363.1|719.32 / 720.70|1809.5|
|0.11|benign_nuisance|uniform_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.200|363.1|719.32 / 720.70|1809.5|
|0.11|benign_nuisance|uniform_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.200|363.1|719.32 / 720.70|1809.5|
|0.11|benign_nuisance|variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.259|364.2|719.06 / 720.70|1422.0|
|0.11|benign_nuisance|variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.259|364.2|719.06 / 720.70|1422.0|
|0.11|benign_nuisance|variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.259|364.2|719.06 / 720.70|1422.0|
|0.11|boundary_local_harm|cost_stabilized_proxy|registered_bound|60|60|9|0.150 [0.081, 0.261]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|boundary_local_harm|cost_stabilized_proxy|common_q010|60|60|5|0.083 [0.036, 0.181]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|boundary_local_harm|cost_stabilized_proxy|eventwise_qt_diagnostic|60|60|47|0.783 [0.664, 0.869]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|boundary_local_harm|cost_variance_proxy|registered_bound|60|60|6|0.100 [0.047, 0.201]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|boundary_local_harm|cost_variance_proxy|common_q010|60|60|4|0.067 [0.026, 0.159]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|boundary_local_harm|cost_variance_proxy|eventwise_qt_diagnostic|60|60|46|0.767 [0.646, 0.856]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|boundary_local_harm|decision_value_proxy|registered_bound|60|60|9|0.150 [0.081, 0.261]|0/0|0.206|470.3|704.89 / 720.70|2303.3|
|0.11|boundary_local_harm|decision_value_proxy|common_q010|60|60|6|0.100 [0.047, 0.201]|0/0|0.206|470.3|704.89 / 720.70|2303.3|
|0.11|boundary_local_harm|decision_value_proxy|eventwise_qt_diagnostic|60|60|41|0.683 [0.558, 0.787]|0/0|0.206|470.3|704.89 / 720.70|2303.3|
|0.11|boundary_local_harm|uniform_proxy|registered_bound|60|60|38|0.633 [0.507, 0.744]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|boundary_local_harm|uniform_proxy|common_q010|60|60|8|0.133 [0.069, 0.242]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|boundary_local_harm|uniform_proxy|eventwise_qt_diagnostic|60|60|38|0.633 [0.507, 0.744]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|boundary_local_harm|variance_proxy|registered_bound|60|60|7|0.117 [0.058, 0.222]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|boundary_local_harm|variance_proxy|common_q010|60|60|5|0.083 [0.036, 0.181]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|boundary_local_harm|variance_proxy|eventwise_qt_diagnostic|60|60|42|0.700 [0.575, 0.801]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|harmful_adaptation|cost_stabilized_proxy|registered_bound|60|60|6|0.100 [0.047, 0.201]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|harmful_adaptation|cost_stabilized_proxy|common_q010|60|60|0|0.000 [0.000, 0.060]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|harmful_adaptation|cost_stabilized_proxy|eventwise_qt_diagnostic|60|60|56|0.933 [0.841, 0.974]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|harmful_adaptation|cost_variance_proxy|registered_bound|60|60|4|0.067 [0.026, 0.159]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|harmful_adaptation|cost_variance_proxy|common_q010|60|60|0|0.000 [0.000, 0.060]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|harmful_adaptation|cost_variance_proxy|eventwise_qt_diagnostic|60|60|56|0.933 [0.841, 0.974]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|harmful_adaptation|decision_value_proxy|registered_bound|60|60|4|0.067 [0.026, 0.159]|0/0|0.206|472.4|709.07 / 720.70|2299.1|
|0.11|harmful_adaptation|decision_value_proxy|common_q010|60|60|1|0.017 [0.003, 0.089]|0/0|0.206|472.4|709.07 / 720.70|2299.1|
|0.11|harmful_adaptation|decision_value_proxy|eventwise_qt_diagnostic|60|60|47|0.783 [0.664, 0.869]|0/0|0.206|472.4|709.07 / 720.70|2299.1|
|0.11|harmful_adaptation|uniform_proxy|registered_bound|60|60|53|0.883 [0.778, 0.942]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|harmful_adaptation|uniform_proxy|common_q010|60|60|0|0.000 [0.000, 0.060]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|harmful_adaptation|uniform_proxy|eventwise_qt_diagnostic|60|60|53|0.883 [0.778, 0.942]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|harmful_adaptation|variance_proxy|registered_bound|60|60|5|0.083 [0.036, 0.181]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|harmful_adaptation|variance_proxy|common_q010|60|60|1|0.017 [0.003, 0.089]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|harmful_adaptation|variance_proxy|eventwise_qt_diagnostic|60|60|55|0.917 [0.819, 0.964]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|recurring_regimes|cost_stabilized_proxy|registered_bound|60|60|9|0.150 [0.081, 0.261]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|recurring_regimes|cost_stabilized_proxy|common_q010|60|60|7|0.117 [0.058, 0.222]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|recurring_regimes|cost_stabilized_proxy|eventwise_qt_diagnostic|60|60|48|0.800 [0.682, 0.882]|0/0|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|recurring_regimes|cost_variance_proxy|registered_bound|60|60|8|0.133 [0.069, 0.242]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|recurring_regimes|cost_variance_proxy|common_q010|60|60|4|0.067 [0.026, 0.159]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|recurring_regimes|cost_variance_proxy|eventwise_qt_diagnostic|60|60|45|0.750 [0.628, 0.842]|0/0|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|recurring_regimes|decision_value_proxy|registered_bound|60|60|8|0.133 [0.069, 0.242]|0/0|0.199|466.2|699.73 / 720.70|2335.8|
|0.11|recurring_regimes|decision_value_proxy|common_q010|60|60|6|0.100 [0.047, 0.201]|0/0|0.199|466.2|699.73 / 720.70|2335.8|
|0.11|recurring_regimes|decision_value_proxy|eventwise_qt_diagnostic|60|60|44|0.733 [0.610, 0.829]|0/0|0.199|466.2|699.73 / 720.70|2335.8|
|0.11|recurring_regimes|uniform_proxy|registered_bound|60|60|40|0.667 [0.541, 0.773]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|recurring_regimes|uniform_proxy|common_q010|60|60|4|0.067 [0.026, 0.159]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|recurring_regimes|uniform_proxy|eventwise_qt_diagnostic|60|60|40|0.667 [0.541, 0.773]|0/0|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|recurring_regimes|variance_proxy|registered_bound|60|60|8|0.133 [0.069, 0.242]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|recurring_regimes|variance_proxy|common_q010|60|60|7|0.117 [0.058, 0.222]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|recurring_regimes|variance_proxy|eventwise_qt_diagnostic|60|60|43|0.717 [0.592, 0.815]|0/0|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|stationary|cost_stabilized_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|stationary|cost_stabilized_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|stationary|cost_stabilized_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.219|517.2|709.45 / 720.70|2358.7|
|0.11|stationary|cost_variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|stationary|cost_variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|stationary|cost_variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.212|494.9|710.15 / 720.70|2342.8|
|0.11|stationary|decision_value_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.211|476.2|713.78 / 720.70|2267.6|
|0.11|stationary|decision_value_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.211|476.2|713.78 / 720.70|2267.6|
|0.11|stationary|decision_value_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.211|476.2|713.78 / 720.70|2267.6|
|0.11|stationary|uniform_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|stationary|uniform_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|stationary|uniform_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.200|471.2|706.14 / 720.70|2358.6|
|0.11|stationary|variance_proxy|registered_bound|0|0|0|nan [nan, nan]|0/60|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|stationary|variance_proxy|common_q010|0|0|0|nan [nan, nan]|0/60|0.203|474.0|709.50 / 720.70|2342.0|
|0.11|stationary|variance_proxy|eventwise_qt_diagnostic|0|0|0|nan [nan, nan]|0/60|0.203|474.0|709.50 / 720.70|2342.0|

## Paired monitor and floor effects

`common_q010` is the same query path with the common 0.10 support bound. `eventwise_qt_diagnostic` uses the realized pre-outcome propensity and is conditional-null sensitive. The floor contrast changes acquisition as well as the registered support bound.

### Monitor bound contrasts

|q_min|Scenario|Policy|Monitor vs registered|Paired rate difference (bootstrap 95%)|Monitor-only / registered-only|
|---:|---|---|---|---:|---:|
|0.10|benign_nuisance|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|cost_stabilized_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|cost_variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|decision_value_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|uniform_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|benign_nuisance|variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|boundary_local_harm|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|boundary_local_harm|cost_stabilized_proxy|eventwise_qt_diagnostic|0.700 [0.583, 0.817]|42 / 0|
|0.10|boundary_local_harm|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|boundary_local_harm|cost_variance_proxy|eventwise_qt_diagnostic|0.683 [0.567, 0.800]|41 / 0|
|0.10|boundary_local_harm|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|boundary_local_harm|decision_value_proxy|eventwise_qt_diagnostic|0.550 [0.417, 0.667]|33 / 0|
|0.10|boundary_local_harm|uniform_proxy|common_q010|-0.500 [-0.633, -0.367]|0 / 30|
|0.10|boundary_local_harm|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|boundary_local_harm|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|boundary_local_harm|variance_proxy|eventwise_qt_diagnostic|0.583 [0.450, 0.700]|35 / 0|
|0.10|harmful_adaptation|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|harmful_adaptation|cost_stabilized_proxy|eventwise_qt_diagnostic|0.933 [0.867, 0.983]|56 / 0|
|0.10|harmful_adaptation|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|harmful_adaptation|cost_variance_proxy|eventwise_qt_diagnostic|0.933 [0.867, 0.983]|56 / 0|
|0.10|harmful_adaptation|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|harmful_adaptation|decision_value_proxy|eventwise_qt_diagnostic|0.783 [0.667, 0.883]|47 / 0|
|0.10|harmful_adaptation|uniform_proxy|common_q010|-0.883 [-0.950, -0.800]|0 / 53|
|0.10|harmful_adaptation|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|harmful_adaptation|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|harmful_adaptation|variance_proxy|eventwise_qt_diagnostic|0.917 [0.833, 0.983]|55 / 0|
|0.10|recurring_regimes|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|recurring_regimes|cost_stabilized_proxy|eventwise_qt_diagnostic|0.683 [0.567, 0.800]|41 / 0|
|0.10|recurring_regimes|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|recurring_regimes|cost_variance_proxy|eventwise_qt_diagnostic|0.667 [0.550, 0.783]|40 / 0|
|0.10|recurring_regimes|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|recurring_regimes|decision_value_proxy|eventwise_qt_diagnostic|0.600 [0.467, 0.717]|36 / 0|
|0.10|recurring_regimes|uniform_proxy|common_q010|-0.600 [-0.717, -0.483]|0 / 36|
|0.10|recurring_regimes|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|recurring_regimes|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|recurring_regimes|variance_proxy|eventwise_qt_diagnostic|0.600 [0.483, 0.733]|36 / 0|
|0.10|stationary|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|cost_stabilized_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|cost_variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|decision_value_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|uniform_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.10|stationary|variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|cost_stabilized_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|cost_variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|decision_value_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|uniform_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|benign_nuisance|variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|boundary_local_harm|cost_stabilized_proxy|common_q010|-0.067 [-0.133, -0.017]|0 / 4|
|0.11|boundary_local_harm|cost_stabilized_proxy|eventwise_qt_diagnostic|0.633 [0.500, 0.750]|38 / 0|
|0.11|boundary_local_harm|cost_variance_proxy|common_q010|-0.033 [-0.083, 0.000]|0 / 2|
|0.11|boundary_local_harm|cost_variance_proxy|eventwise_qt_diagnostic|0.667 [0.550, 0.783]|40 / 0|
|0.11|boundary_local_harm|decision_value_proxy|common_q010|-0.050 [-0.117, 0.000]|0 / 3|
|0.11|boundary_local_harm|decision_value_proxy|eventwise_qt_diagnostic|0.533 [0.400, 0.667]|32 / 0|
|0.11|boundary_local_harm|uniform_proxy|common_q010|-0.500 [-0.633, -0.367]|0 / 30|
|0.11|boundary_local_harm|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|boundary_local_harm|variance_proxy|common_q010|-0.033 [-0.083, 0.000]|0 / 2|
|0.11|boundary_local_harm|variance_proxy|eventwise_qt_diagnostic|0.583 [0.450, 0.700]|35 / 0|
|0.11|harmful_adaptation|cost_stabilized_proxy|common_q010|-0.100 [-0.183, -0.033]|0 / 6|
|0.11|harmful_adaptation|cost_stabilized_proxy|eventwise_qt_diagnostic|0.833 [0.733, 0.917]|50 / 0|
|0.11|harmful_adaptation|cost_variance_proxy|common_q010|-0.067 [-0.133, -0.017]|0 / 4|
|0.11|harmful_adaptation|cost_variance_proxy|eventwise_qt_diagnostic|0.867 [0.783, 0.950]|52 / 0|
|0.11|harmful_adaptation|decision_value_proxy|common_q010|-0.050 [-0.117, 0.000]|0 / 3|
|0.11|harmful_adaptation|decision_value_proxy|eventwise_qt_diagnostic|0.717 [0.600, 0.817]|43 / 0|
|0.11|harmful_adaptation|uniform_proxy|common_q010|-0.883 [-0.950, -0.800]|0 / 53|
|0.11|harmful_adaptation|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|harmful_adaptation|variance_proxy|common_q010|-0.067 [-0.133, -0.017]|0 / 4|
|0.11|harmful_adaptation|variance_proxy|eventwise_qt_diagnostic|0.833 [0.733, 0.917]|50 / 0|
|0.11|recurring_regimes|cost_stabilized_proxy|common_q010|-0.033 [-0.083, 0.000]|0 / 2|
|0.11|recurring_regimes|cost_stabilized_proxy|eventwise_qt_diagnostic|0.650 [0.533, 0.767]|39 / 0|
|0.11|recurring_regimes|cost_variance_proxy|common_q010|-0.067 [-0.133, -0.017]|0 / 4|
|0.11|recurring_regimes|cost_variance_proxy|eventwise_qt_diagnostic|0.617 [0.500, 0.733]|37 / 0|
|0.11|recurring_regimes|decision_value_proxy|common_q010|-0.033 [-0.083, 0.000]|0 / 2|
|0.11|recurring_regimes|decision_value_proxy|eventwise_qt_diagnostic|0.600 [0.483, 0.717]|36 / 0|
|0.11|recurring_regimes|uniform_proxy|common_q010|-0.600 [-0.717, -0.483]|0 / 36|
|0.11|recurring_regimes|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|recurring_regimes|variance_proxy|common_q010|-0.017 [-0.050, 0.000]|0 / 1|
|0.11|recurring_regimes|variance_proxy|eventwise_qt_diagnostic|0.583 [0.450, 0.700]|35 / 0|
|0.11|stationary|cost_stabilized_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|cost_stabilized_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|cost_variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|cost_variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|decision_value_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|decision_value_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|uniform_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|uniform_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|variance_proxy|common_q010|0.000 [0.000, 0.000]|0 / 0|
|0.11|stationary|variance_proxy|eventwise_qt_diagnostic|0.000 [0.000, 0.000]|0 / 0|

### Propensity-floor contrasts

|Scenario|Policy|q_min 0.11 minus 0.10 rate difference (bootstrap 95%)|high-floor-only / low-floor-only|
|---|---|---:|---:|
|benign_nuisance|cost_stabilized_proxy|0.000 [0.000, 0.000]|0 / 0|
|benign_nuisance|cost_variance_proxy|0.000 [0.000, 0.000]|0 / 0|
|benign_nuisance|decision_value_proxy|0.000 [0.000, 0.000]|0 / 0|
|benign_nuisance|uniform_proxy|0.000 [0.000, 0.000]|0 / 0|
|benign_nuisance|variance_proxy|0.000 [0.000, 0.000]|0 / 0|
|boundary_local_harm|cost_stabilized_proxy|0.067 [0.017, 0.133]|4 / 0|
|boundary_local_harm|cost_variance_proxy|0.000 [0.000, 0.000]|0 / 0|
|boundary_local_harm|decision_value_proxy|0.050 [-0.017, 0.133]|4 / 1|
|boundary_local_harm|uniform_proxy|0.000 [0.000, 0.000]|0 / 0|
|boundary_local_harm|variance_proxy|0.017 [0.000, 0.050]|1 / 0|
|harmful_adaptation|cost_stabilized_proxy|0.100 [0.033, 0.183]|6 / 0|
|harmful_adaptation|cost_variance_proxy|0.067 [0.017, 0.133]|4 / 0|
|harmful_adaptation|decision_value_proxy|0.050 [0.000, 0.117]|3 / 0|
|harmful_adaptation|uniform_proxy|0.000 [0.000, 0.000]|0 / 0|
|harmful_adaptation|variance_proxy|0.067 [0.017, 0.133]|4 / 0|
|recurring_regimes|cost_stabilized_proxy|0.033 [0.000, 0.083]|2 / 0|
|recurring_regimes|cost_variance_proxy|0.050 [0.000, 0.117]|3 / 0|
|recurring_regimes|decision_value_proxy|0.033 [-0.033, 0.100]|3 / 1|
|recurring_regimes|uniform_proxy|0.000 [0.000, 0.000]|0 / 0|
|recurring_regimes|variance_proxy|0.017 [0.000, 0.050]|1 / 0|
|stationary|cost_stabilized_proxy|0.000 [0.000, 0.000]|0 / 0|
|stationary|cost_variance_proxy|0.000 [0.000, 0.000]|0 / 0|
|stationary|decision_value_proxy|0.000 [0.000, 0.000]|0 / 0|
|stationary|uniform_proxy|0.000 [0.000, 0.000]|0 / 0|
|stationary|variance_proxy|0.000 [0.000, 0.000]|0 / 0|

No confirmatory winner or novelty claim is supported. Before treating the eventwise comparator as valid for population harm, either establish a suitable conditional null or use a scale predictable before current covariates are observed. A new registered null-calibration block is required before confirmation.

No figure was generated under this protocol.
