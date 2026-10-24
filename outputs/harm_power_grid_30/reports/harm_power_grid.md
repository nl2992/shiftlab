# Harm severity, onset, and horizon development grid

This paired CUDA development screen evaluates 36 parameter cells with 30 shared seed streams per cell (1080 stream-cell observations). The common seed block is `54000000–54000029`. Each monitor receives the same uniform-query labels, prediction-powered increments, q_min=.20 global bound, alpha=.05, epsilon=.10, and 20% realized dollar cap within a cell.

Boundary-local harm varies DGP severity over 0.75, 1.50, 2.25; abrupt change fraction over .35, .50, .65; and stream horizon n over 2,400, 3,200, 4,000. Recurring regimes vary severity and horizon, while their built-in four-regime schedule is preserved; `change_fraction` is not presented as an onset control for recurrence.

Each cell reports the fraction of all evaluator-classified material-harm streams detected, Wilson intervals, onset reachability, delay among detections, labels, spend, horizon, and cap compliance. A stream whose material-harm onset is not reached remains a nondetection in the all-harm denominator. Paired exact tests are exploratory and unadjusted across this screen; they do not select a confirmatory winner.

No evaluator oracle probabilities enter model inputs or the exported stream metrics. The grid is intended to identify regions where the fixed-mixture result is robust and regions where the comparison changes. It is not a final test of error control or a novelty claim.

## Reproduction

Run `uv run python scripts/run_harm_power_grid.py --output outputs/harm_power_grid_30 --seeds 30 --seed-offset 54000000 --device cuda`. Use `metrics/harm_power_grid_summary.csv` for cell rates and `metrics/harm_power_grid_paired_tests.csv` only as exploratory contrasts.

## Cell summaries

|Scenario|n|Severity|Onset fraction|Monitor|Detect / material harm|Reach / material harm|Median delay|Mean labels|Mean spend / budget|
|---|---:|---:|---:|---|---:|---:|---:|---:|---:|
|boundary_local_harm|2400|0.75|0.35|fixed_mixture|6/30 [0.10, 0.37]|30/30|1249.0|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.35|predictable_variance|4/30 [0.05, 0.30]|30/30|1191.0|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.35|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.50|fixed_mixture|1/30 [0.01, 0.17]|30/30|1131.0|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.50|predictable_variance|1/30 [0.01, 0.17]|30/30|1162.0|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.65|fixed_mixture|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.65|predictable_variance|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|0.75|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.35|fixed_mixture|25/30 [0.66, 0.93]|30/30|1267.0|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.35|predictable_variance|20/30 [0.49, 0.81]|30/30|1142.5|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.35|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.50|fixed_mixture|13/30 [0.27, 0.61]|30/30|980.0|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.50|predictable_variance|7/30 [0.12, 0.41]|30/30|1020.0|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.65|fixed_mixture|1/30 [0.01, 0.17]|30/30|806.0|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.65|predictable_variance|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|1.50|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.35|fixed_mixture|28/30 [0.79, 0.98]|30/30|1004.0|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.35|predictable_variance|25/30 [0.66, 0.93]|30/30|1042.0|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.35|predictable_empirical_bernstein|1/30 [0.01, 0.17]|30/30|1488.0|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.50|fixed_mixture|17/30 [0.39, 0.73]|30/30|969.0|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.50|predictable_variance|15/30 [0.33, 0.67]|30/30|991.0|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.65|fixed_mixture|5/30 [0.07, 0.34]|30/30|768.0|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.65|predictable_variance|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|2400|2.25|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|boundary_local_harm|3200|0.75|0.35|fixed_mixture|16/30 [0.36, 0.70]|30/30|1514.0|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.35|predictable_variance|15/30 [0.33, 0.67]|30/30|1642.0|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.35|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.50|fixed_mixture|8/30 [0.14, 0.44]|30/30|1377.5|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.50|predictable_variance|4/30 [0.05, 0.30]|30/30|1428.0|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.65|fixed_mixture|1/30 [0.01, 0.17]|30/30|1017.0|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.65|predictable_variance|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|3200|0.75|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.35|fixed_mixture|25/30 [0.66, 0.93]|30/30|1273.0|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.35|predictable_variance|24/30 [0.63, 0.90]|30/30|1365.5|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.35|predictable_empirical_bernstein|9/30 [0.17, 0.48]|30/30|1928.0|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.50|fixed_mixture|19/30 [0.46, 0.78]|30/30|1240.0|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.50|predictable_variance|16/30 [0.36, 0.70]|30/30|1267.5|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.65|fixed_mixture|6/30 [0.10, 0.37]|30/30|922.5|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.65|predictable_variance|4/30 [0.05, 0.30]|30/30|960.0|472.9|708.6/719.1|
|boundary_local_harm|3200|1.50|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.35|fixed_mixture|29/30 [0.83, 0.99]|30/30|1092.0|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.35|predictable_variance|29/30 [0.83, 0.99]|30/30|1205.0|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.35|predictable_empirical_bernstein|14/30 [0.30, 0.64]|30/30|1893.5|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.50|fixed_mixture|23/30 [0.59, 0.88]|30/30|1108.0|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.50|predictable_variance|21/30 [0.52, 0.83]|30/30|1240.0|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.50|predictable_empirical_bernstein|1/30 [0.01, 0.17]|30/30|1592.0|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.65|fixed_mixture|10/30 [0.19, 0.51]|30/30|917.5|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.65|predictable_variance|7/30 [0.12, 0.41]|30/30|945.0|472.9|708.6/719.1|
|boundary_local_harm|3200|2.25|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|boundary_local_harm|4000|0.75|0.35|fixed_mixture|21/30 [0.52, 0.83]|30/30|1633.0|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.35|predictable_variance|18/30 [0.42, 0.75]|30/30|1781.5|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.35|predictable_empirical_bernstein|4/30 [0.05, 0.30]|30/30|2129.0|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.50|fixed_mixture|10/30 [0.19, 0.51]|30/30|1669.5|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.50|predictable_variance|9/30 [0.17, 0.48]|30/30|1703.0|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.50|predictable_empirical_bernstein|2/30 [0.02, 0.21]|30/30|1858.5|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.65|fixed_mixture|4/30 [0.05, 0.30]|30/30|1009.0|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.65|predictable_variance|4/30 [0.05, 0.30]|30/30|1137.0|587.4|880.2/898.1|
|boundary_local_harm|4000|0.75|0.65|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.35|fixed_mixture|30/30 [0.89, 1.00]|30/30|1358.5|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.35|predictable_variance|30/30 [0.89, 1.00]|30/30|1404.0|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.35|predictable_empirical_bernstein|16/30 [0.36, 0.70]|30/30|2111.5|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.50|fixed_mixture|24/30 [0.63, 0.90]|30/30|1354.0|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.50|predictable_variance|22/30 [0.56, 0.86]|30/30|1500.0|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.50|predictable_empirical_bernstein|5/30 [0.07, 0.34]|30/30|1680.0|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.65|fixed_mixture|12/30 [0.25, 0.58]|30/30|1202.5|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.65|predictable_variance|9/30 [0.17, 0.48]|30/30|1272.0|587.4|880.2/898.1|
|boundary_local_harm|4000|1.50|0.65|predictable_empirical_bernstein|1/30 [0.01, 0.17]|30/30|1281.0|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.35|fixed_mixture|30/30 [0.89, 1.00]|30/30|1221.0|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.35|predictable_variance|30/30 [0.89, 1.00]|30/30|1241.0|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.35|predictable_empirical_bernstein|19/30 [0.46, 0.78]|30/30|1958.0|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.50|fixed_mixture|26/30 [0.70, 0.95]|30/30|1326.5|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.50|predictable_variance|26/30 [0.70, 0.95]|30/30|1478.5|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.50|predictable_empirical_bernstein|8/30 [0.14, 0.44]|30/30|1721.0|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.65|fixed_mixture|15/30 [0.33, 0.67]|30/30|1120.0|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.65|predictable_variance|12/30 [0.25, 0.58]|30/30|1129.5|587.4|880.2/898.1|
|boundary_local_harm|4000|2.25|0.65|predictable_empirical_bernstein|1/30 [0.01, 0.17]|30/30|1281.0|587.4|880.2/898.1|
|recurring_regimes|2400|0.75|0.50|fixed_mixture|1/30 [0.01, 0.17]|30/30|1559.0|315.2|470.8/479.4|
|recurring_regimes|2400|0.75|0.50|predictable_variance|1/30 [0.01, 0.17]|30/30|1559.0|315.2|470.8/479.4|
|recurring_regimes|2400|0.75|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|recurring_regimes|2400|1.50|0.50|fixed_mixture|3/30 [0.03, 0.26]|30/30|1455.0|315.2|470.8/479.4|
|recurring_regimes|2400|1.50|0.50|predictable_variance|3/30 [0.03, 0.26]|30/30|1455.0|315.2|470.8/479.4|
|recurring_regimes|2400|1.50|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|recurring_regimes|2400|2.25|0.50|fixed_mixture|6/30 [0.10, 0.37]|30/30|1445.0|315.2|470.8/479.4|
|recurring_regimes|2400|2.25|0.50|predictable_variance|5/30 [0.07, 0.34]|30/30|1435.0|315.2|470.8/479.4|
|recurring_regimes|2400|2.25|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|315.2|470.8/479.4|
|recurring_regimes|3200|0.75|0.50|fixed_mixture|6/30 [0.10, 0.37]|30/30|2138.0|472.9|708.6/719.1|
|recurring_regimes|3200|0.75|0.50|predictable_variance|6/30 [0.10, 0.37]|30/30|2264.0|472.9|708.6/719.1|
|recurring_regimes|3200|0.75|0.50|predictable_empirical_bernstein|0/30 [0.00, 0.11]|30/30|nan|472.9|708.6/719.1|
|recurring_regimes|3200|1.50|0.50|fixed_mixture|17/30 [0.39, 0.73]|30/30|2035.0|472.9|708.6/719.1|
|recurring_regimes|3200|1.50|0.50|predictable_variance|16/30 [0.36, 0.70]|30/30|2098.0|472.9|708.6/719.1|
|recurring_regimes|3200|1.50|0.50|predictable_empirical_bernstein|1/30 [0.01, 0.17]|30/30|2312.0|472.9|708.6/719.1|
|recurring_regimes|3200|2.25|0.50|fixed_mixture|22/30 [0.56, 0.86]|30/30|1663.5|472.9|708.6/719.1|
|recurring_regimes|3200|2.25|0.50|predictable_variance|22/30 [0.56, 0.86]|30/30|1974.0|472.9|708.6/719.1|
|recurring_regimes|3200|2.25|0.50|predictable_empirical_bernstein|3/30 [0.03, 0.26]|30/30|2209.0|472.9|708.6/719.1|
|recurring_regimes|4000|0.75|0.50|fixed_mixture|13/30 [0.27, 0.61]|30/30|2333.0|587.4|880.2/898.1|
|recurring_regimes|4000|0.75|0.50|predictable_variance|12/30 [0.25, 0.58]|30/30|2471.0|587.4|880.2/898.1|
|recurring_regimes|4000|0.75|0.50|predictable_empirical_bernstein|2/30 [0.02, 0.21]|30/30|2638.5|587.4|880.2/898.1|
|recurring_regimes|4000|1.50|0.50|fixed_mixture|25/30 [0.66, 0.93]|30/30|1340.0|587.4|880.2/898.1|
|recurring_regimes|4000|1.50|0.50|predictable_variance|24/30 [0.63, 0.90]|30/30|2076.5|587.4|880.2/898.1|
|recurring_regimes|4000|1.50|0.50|predictable_empirical_bernstein|8/30 [0.14, 0.44]|30/30|2688.0|587.4|880.2/898.1|
|recurring_regimes|4000|2.25|0.50|fixed_mixture|26/30 [0.70, 0.95]|30/30|882.5|587.4|880.2/898.1|
|recurring_regimes|4000|2.25|0.50|predictable_variance|26/30 [0.70, 0.95]|30/30|945.5|587.4|880.2/898.1|
|recurring_regimes|4000|2.25|0.50|predictable_empirical_bernstein|11/30 [0.22, 0.54]|30/30|2669.0|587.4|880.2/898.1|
