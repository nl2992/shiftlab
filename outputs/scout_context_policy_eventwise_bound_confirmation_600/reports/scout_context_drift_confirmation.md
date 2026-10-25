# Eventwise-propensity target-scout confirmation under abrupt context drift

Status: **confirmed_on_registered_grid**. Device: cuda; seeds per cell: 600; seed block: 20271000–20271599; worker processes: 6.

The matched grid contains 24 prevalence, signal, proxy-error, and budget cells, 4 methods, and 57,600 method-cell-seed rows. The primary endpoint is evaluator-known postpromotion net decision utility, equally weighted over cells. Seed IDs are resampled as clusters across all cells.

| contrast                      | metric                          |   n_cells |   n_matched_seed_clusters |   mean_paired_difference |   percentile_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   familywise_one_sided_lower |   familywise_alpha_allocation | primary_comparison   |   bootstrap_draws |   bootstrap_seed |
|:------------------------------|:--------------------------------|----------:|--------------------------:|-------------------------:|--------------------------------:|-------------------:|--------------------:|-----------------------------:|------------------------------:|:---------------------|------------------:|-----------------:|
| eventwise_minus_rank          | expected_postpromotion_net_gain |        24 |                       600 |                   0.5990 |                          0.9500 |             0.4515 |              0.7619 |                       0.4515 |                        0.0250 | True                 |             10000 |         20271600 |
| eventwise_minus_nested_volume | expected_postpromotion_net_gain |        24 |                       600 |                   0.5703 |                          0.9500 |             0.4311 |              0.7217 |                       0.4311 |                        0.0250 | True                 |             10000 |         20271601 |
| eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        24 |                       600 |                   0.4383 |                          0.9500 |             0.3325 |              0.5528 |                     nan      |                      nan      | False                |             10000 |         20271602 |

The two primary comparisons are eventwise scout versus pooled rank and nested-volume. Their one-sided 97.5% seed-cluster bootstrap lower limits are Bonferroni-adjusted for an approximate simultaneous 95% familywise assessment. The primary gate passes only when both exceed zero. Bootstrap coverage is approximate, not a finite-sample theorem.

Integrity: all expected rows present; positive propensities verified; 0 cap violations; 4 harmful promotions by evaluator-known future utility. These finite synthetic results apply only to the frozen DGP and feedback design and establish no novelty claim.

Frozen protocol: docs/scout_context_policy_eventwise_bound_confirmation_protocol.md (SHA-256 d442b8b7f0945f3216d8cb1bb6326a8a087b273dda98dc7b20662c30b65ae068). No figure was generated.
