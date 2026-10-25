# Target-scout positive-signal development under abrupt context drift

Status: **exploratory development**. Device: cuda; seeds per cell: 60; seed block: 20268000–20268059.

The grid has 24 cells and three methods per matched stream, with both 20% and 40% hard caps. The target prevalence changes at the scout/certification boundary except in the stable 50% control. Primary contrasts equally weight the 24 settings and resample matched seed IDs as clusters.

| contrast                  | metric                          |   n_cells |   n_matched_seeds |   mean_paired_difference |   descriptive_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   bootstrap_draws |   bootstrap_seed |
|:--------------------------|:--------------------------------|----------:|------------------:|-------------------------:|---------------------------------:|-------------------:|--------------------:|------------------:|-----------------:|
| scout_minus_rank          | expected_postpromotion_net_gain |        24 |                60 |                   0.0958 |                           0.9500 |             0.0000 |              0.2419 |             10000 |         20268060 |
| scout_minus_nested_volume | expected_postpromotion_net_gain |        24 |                60 |                   0.0958 |                           0.9500 |             0.0000 |              0.2419 |             10000 |         20268060 |

These intervals are descriptive development summaries, not confirmation tests. Cellwise results and the complete stream-level evaluator metrics are saved in Parquet. No method is selected for publication from this run alone; any follow-up requires a frozen protocol and disjoint seed block. The separate zero-signal calibration, not this positive-signal grid, supplies false-promotion evidence.

Frozen protocol: docs/scout_context_policy_positive_drift_development_protocol.md (SHA-256 3d92f907c47518f0c4c07bfa7930f64f26d25ef5d83fd67484d2895a35814128). No figure was generated.
