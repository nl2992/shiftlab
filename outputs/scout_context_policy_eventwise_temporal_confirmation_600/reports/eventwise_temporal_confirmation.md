# Eventwise-scout confirmation under gradual and recurring contexts

Status: **confirmed_on_registered_grid**. Device: cuda; seeds per cell: 600; seed block: 20920000–20920599; workers: 6.

The matched grid contains 32 positive-signal cells, 4 methods, and 76,800 method-cell-seed rows. The endpoint is evaluator-known expected postpromotion net decision gain, equally weighted over cells and paired by seed cluster.

| contrast                      | metric                          |   n_cells |   n_matched_seed_clusters |   mean_paired_difference |   percentile_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   familywise_one_sided_lower |   familywise_alpha_allocation | primary_comparison   |   bootstrap_draws |   bootstrap_seed |
|:------------------------------|:--------------------------------|----------:|--------------------------:|-------------------------:|--------------------------------:|-------------------:|--------------------:|-----------------------------:|------------------------------:|:---------------------|------------------:|-----------------:|
| eventwise_minus_rank          | expected_postpromotion_net_gain |        32 |                       600 |                   4.7266 |                          0.9500 |             4.2161 |              5.2659 |                       4.2161 |                        0.0250 | True                 |             10000 |         20920600 |
| eventwise_minus_nested_volume | expected_postpromotion_net_gain |        32 |                       600 |                   4.4666 |                          0.9500 |             3.9743 |              4.9762 |                       3.9743 |                        0.0250 | True                 |             10000 |         20920601 |
| eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        32 |                       600 |                   3.4845 |                          0.9500 |             3.0895 |              3.8863 |                     nan      |                      nan      | False                |             10000 |         20920602 |

The primary comparisons are eventwise versus pooled rank and nested context-volume. Their one-sided 97.5% seed-cluster bootstrap lower limits use Bonferroni allocation for approximate simultaneous 95% familywise assessment. The primary gate passes only when both limits exceed zero; this bootstrap coverage is approximate, not an exact finite-sample guarantee. The minimum-bound comparison is secondary.

Integrity: all expected unique rows present; positive propensities verified; 0 cap violations; 90 harmful promotions by evaluator-known future utility. Results apply only to the frozen synthetic grid and feedback design.

Frozen protocol: docs/scout_context_policy_eventwise_temporal_confirmation_protocol.md (normalized SHA-256 ad6750dcb707865cf16a4ecda1062142e585eddac13b798c7e7909ecd7e1d6a2). No figure was generated.
