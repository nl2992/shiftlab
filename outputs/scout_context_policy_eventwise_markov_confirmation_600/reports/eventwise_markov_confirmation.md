# Eventwise-scout confirmation under persistent contexts

Status: **confirmed_on_registered_grid**. Device: cuda; seeds per cell: 600; seed block: 20910000–20910599; workers: 6.

The matched grid contains 72 positive-signal cells, 4 methods, and 172,800 method-cell-seed rows. The primary endpoint is evaluator-known expected postpromotion net decision gain, equally weighted over cells and paired by seed cluster.

| contrast                      | metric                          |   n_cells |   n_matched_seed_clusters |   mean_paired_difference |   percentile_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   familywise_one_sided_lower |   familywise_alpha_allocation | primary_comparison   |   bootstrap_draws |   bootstrap_seed |
|:------------------------------|:--------------------------------|----------:|--------------------------:|-------------------------:|--------------------------------:|-------------------:|--------------------:|-----------------------------:|------------------------------:|:---------------------|------------------:|-----------------:|
| eventwise_minus_rank          | expected_postpromotion_net_gain |        72 |                       600 |                  10.5668 |                          0.9500 |             9.7393 |             11.4169 |                       9.7393 |                        0.0250 | True                 |             10000 |         20910600 |
| eventwise_minus_nested_volume | expected_postpromotion_net_gain |        72 |                       600 |                  10.1697 |                          0.9500 |             9.3472 |             11.0016 |                       9.3472 |                        0.0250 | True                 |             10000 |         20910601 |
| eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        72 |                       600 |                   6.3994 |                          0.9500 |             5.8941 |              6.8970 |                     nan      |                      nan      | False                |             10000 |         20910602 |

The primary comparisons are eventwise versus pooled rank and nested context-volume. Their one-sided 97.5% seed-cluster bootstrap lower limits use Bonferroni allocation for approximate simultaneous 95% familywise assessment. The primary gate passes only when both limits exceed zero; coverage is approximate and is not an exact finite-sample guarantee. The minimum-bound comparison is secondary.

Integrity: all expected unique rows present; positive propensities verified; 0 cap violations; 11 harmful promotions by evaluator-known future utility. These results apply only to the frozen synthetic grid and feedback design.

Frozen protocol: docs/scout_context_policy_eventwise_markov_confirmation_protocol.md (SHA-256 1330f65212ac4cca349017847e23eb0bd5c0a214971b574c5d0c22c961b71291). No figure was generated.
