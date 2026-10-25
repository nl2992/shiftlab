# Target-scout positive-signal development under abrupt context drift

Status: **exploratory development**. Device: cuda; seeds per cell: 60; seed block: 20268100–20268159.

The grid has 24 cells and 4 methods per matched stream, with both 20% and 40% hard caps. The target prevalence changes at the scout/certification boundary except in the stable 50% control. Primary contrasts equally weight the 24 settings and resample matched seed IDs as clusters.

| contrast                                  | metric                          |   n_cells |   n_matched_seeds |   mean_paired_difference |   descriptive_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   bootstrap_draws |   bootstrap_seed |
|:------------------------------------------|:--------------------------------|----------:|------------------:|-------------------------:|---------------------------------:|-------------------:|--------------------:|------------------:|-----------------:|
| scout_minimum_bound_minus_rank            | expected_postpromotion_net_gain |        24 |                60 |                   0.1820 |                           0.9500 |             0.0000 |              0.4644 |             10000 |         20268060 |
| scout_minimum_bound_minus_nested_volume   | expected_postpromotion_net_gain |        24 |                60 |                   0.1820 |                           0.9500 |             0.0000 |              0.4644 |             10000 |         20268060 |
| scout_eventwise_bound_minus_rank          | expected_postpromotion_net_gain |        24 |                60 |                   0.4090 |                           0.9500 |             0.0650 |              0.8633 |             10000 |         20268060 |
| scout_eventwise_bound_minus_nested_volume | expected_postpromotion_net_gain |        24 |                60 |                   0.4090 |                           0.9500 |             0.0650 |              0.8633 |             10000 |         20268060 |
| eventwise_bound_minus_minimum_bound       | expected_postpromotion_net_gain |        24 |                60 |                   0.2269 |                           0.9500 |             0.0408 |              0.4718 |             10000 |         20268060 |

These intervals are descriptive development summaries, not confirmation tests. Cellwise results and the complete stream-level evaluator metrics are saved in Parquet. No method is selected for publication from this run alone; any follow-up requires a frozen protocol and disjoint seed block. The separate zero-signal calibration, not this positive-signal grid, supplies false-promotion evidence.

Frozen protocol: docs/scout_context_policy_eventwise_bound_development_protocol.md (SHA-256 5cc10d034f99bb7d67ed6111cdb502b6cb79c2222e40050a4a7349c9ee4ec795). No figure was generated.
