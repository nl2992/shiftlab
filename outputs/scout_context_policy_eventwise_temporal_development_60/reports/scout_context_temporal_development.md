# Eventwise target-scout development under gradual and recurring contexts

Status: **exploratory_development**. Device: cuda; seeds per cell: 60; seed block: 20274000–20274059; workers: 6.

The factorial has 48 cells (32 positive-signal and 16 zero-signal controls), four methods per stream, and 11,520 rows.

## Paired expected-net-gain contrasts

| contrast                      | metric                          |   n_cells |   n_seed_clusters |   mean_paired_difference |   descriptive_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   bootstrap_draws |   bootstrap_seed | confirmatory   |
|:------------------------------|:--------------------------------|----------:|------------------:|-------------------------:|---------------------------------:|-------------------:|--------------------:|------------------:|-----------------:|:---------------|
| eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        32 |                60 |                   3.8295 |                           0.9500 |             2.7290 |              4.9707 |             10000 |         20274060 | False          |
| eventwise_minus_rank          | expected_postpromotion_net_gain |        32 |                60 |                   5.5031 |                           0.9500 |             4.0513 |              7.0518 |             10000 |         20274061 | False          |
| eventwise_minus_nested_volume | expected_postpromotion_net_gain |        32 |                60 |                   5.2812 |                           0.9500 |             3.8962 |              6.7562 |             10000 |         20274062 | False          |

Intervals are descriptive seed-cluster bootstrap intervals. Zero-signal cells verify the simulator's event-conditional expected-gain null and are not a false-promotion calibration. No confirmatory or novelty claim follows from this development run.
