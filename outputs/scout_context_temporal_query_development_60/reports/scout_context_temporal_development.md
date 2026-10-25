# Eventwise target-scout development under gradual and recurring contexts

Status: **exploratory_development**. Device: cuda; seeds per cell: 60; seed block: 21420000–21420059; workers: 6.

The factorial has 96 query-policy/profile/cap cells (64 positive-signal and 32 zero-signal controls), four methods per stream, and 23,040 rows. Query policies: uniform, variance.

## Paired expected-net-gain contrasts

| contrast                                   | metric                          |   n_cells |   n_seed_clusters |   mean_paired_difference |   descriptive_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   bootstrap_draws |   bootstrap_seed | confirmatory   |
|:-------------------------------------------|:--------------------------------|----------:|------------------:|-------------------------:|---------------------------------:|-------------------:|--------------------:|------------------:|-----------------:|:---------------|
| uniform_eventwise_minus_minimum_bound      | expected_postpromotion_net_gain |        32 |                60 |                   2.4699 |                           0.9500 |             1.6355 |              3.3728 |             10000 |         20274060 | False          |
| uniform_eventwise_minus_rank               | expected_postpromotion_net_gain |        32 |                60 |                   4.3131 |                           0.9500 |             2.8613 |              5.9234 |             10000 |         20274061 | False          |
| uniform_eventwise_minus_nested_volume      | expected_postpromotion_net_gain |        32 |                60 |                   3.9635 |                           0.9500 |             2.5619 |              5.4984 |             10000 |         20274062 | False          |
| variance_eventwise_minus_minimum_bound     | expected_postpromotion_net_gain |        32 |                60 |                   4.3847 |                           0.9500 |             2.9891 |              5.9322 |             10000 |         20274063 | False          |
| variance_eventwise_minus_rank              | expected_postpromotion_net_gain |        32 |                60 |                   6.0127 |                           0.9500 |             3.9995 |              8.2897 |             10000 |         20274064 | False          |
| variance_eventwise_minus_nested_volume     | expected_postpromotion_net_gain |        32 |                60 |                   5.6368 |                           0.9500 |             3.7447 |              7.7761 |             10000 |         20274065 | False          |
| variance_eventwise_minus_uniform_eventwise | expected_postpromotion_net_gain |        32 |                60 |                   1.6683 |                           0.9500 |             0.4255 |              2.9562 |             10000 |         20274066 | False          |

Intervals are descriptive seed-cluster bootstrap intervals. Zero-signal cells verify the simulator's event-conditional expected-gain null and are not a false-promotion calibration. No confirmatory or novelty claim follows from this development run.
