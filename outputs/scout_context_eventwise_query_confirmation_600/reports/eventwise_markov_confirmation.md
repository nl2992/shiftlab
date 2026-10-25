# Eventwise-scout confirmation under persistent contexts

Status: **confirmed_on_registered_grid**. Device: cuda; seeds per cell: 600; seed block: 21300000–21300599; workers: 6.

The matched grid contains 48 positive-signal cells, query policies uniform, variance, 4 methods, and 230,400 method-cell-seed-query rows. The endpoint is evaluator-known expected postpromotion net decision gain, equally weighted over cells and paired by seed cluster.

| contrast                                   | metric                          |   n_cells |   n_matched_seed_clusters |   mean_paired_difference |   percentile_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   familywise_one_sided_lower |   familywise_alpha_allocation | primary_comparison   |   bootstrap_draws |   bootstrap_seed |
|:-------------------------------------------|:--------------------------------|----------:|--------------------------:|-------------------------:|--------------------------------:|-------------------:|--------------------:|-----------------------------:|------------------------------:|:---------------------|------------------:|-----------------:|
| variance_eventwise_minus_rank              | expected_postpromotion_net_gain |        48 |                       600 |                  11.2436 |                          0.9500 |            10.3412 |             12.1530 |                      10.3412 |                        0.0250 | True                 |             10000 |         21300600 |
| variance_eventwise_minus_nested_volume     | expected_postpromotion_net_gain |        48 |                       600 |                  10.7399 |                          0.9500 |             9.8610 |             11.6377 |                       9.8610 |                        0.0250 | True                 |             10000 |         21300601 |
| variance_eventwise_minus_minimum_bound     | expected_postpromotion_net_gain |        48 |                       600 |                   7.2232 |                          0.9500 |             6.6430 |              7.8158 |                     nan      |                      nan      | False                |             10000 |         21300602 |
| variance_eventwise_minus_uniform_eventwise | expected_postpromotion_net_gain |        48 |                       600 |                   1.2304 |                          0.9500 |             0.7192 |              1.7501 |                     nan      |                      nan      | False                |             10000 |         21300603 |

The primary comparisons are eventwise variance-query scouting versus pooled rank and nested context-volume under variance querying. Their one-sided 97.5% seed-cluster bootstrap lower limits use Bonferroni allocation for approximate simultaneous 95% familywise assessment. The gate passes only when both limits exceed zero. The minimum-bound and uniform-query contrasts are secondary. Bootstrap coverage is approximate, not an exact finite-sample guarantee.

Integrity: 230,400/230,400 expected unique rows; positive propensities verified; 0 cap violations; 12 harmful promotions by evaluator-known future utility.

Analysis correction: a post-run audit found that the initial primary variance-eventwise-minus-rank contrast selected eventwise on both sides. The saved streams were not changed; the frozen contrast mapping was corrected and all contrasts recomputed from the row-level metrics. This correction does not tune or select a method using confirmation outcomes.

Frozen protocol: docs/scout_context_eventwise_query_confirmation_protocol.md (SHA-256 e9051c1e722cd6b95d5d12ec75f8f622864abe2abb8b5b668ffc72de84fd77b7). No figure was generated.
