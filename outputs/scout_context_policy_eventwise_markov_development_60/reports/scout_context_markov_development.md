# Eventwise target-scout development under persistent contexts

Status: **exploratory_development**. Device: cuda; seeds per cell: 60; seed block: 20273000–20273059; worker processes: 6.

The grid has 108 cells (72 positive-signal and 36 zero-signal controls), 4 methods per stream, and 25,920 matched method-cell-seed rows. Stationary latent context prevalence is crossed with Markov persistence, signal, proxy error, and hard label cap.

## Positive-signal paired utility contrasts

| slice              | contrast                      | metric                          |   n_cells |   n_seed_clusters |   mean_paired_difference |   descriptive_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   bootstrap_draws |   bootstrap_seed | confirmatory   |
|:-------------------|:------------------------------|:--------------------------------|----------:|------------------:|-------------------------:|---------------------------------:|-------------------:|--------------------:|------------------:|-----------------:|:---------------|
| all_positive_cells | eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        72 |                60 |                   5.4678 |                           0.9500 |             4.0898 |              6.9673 |             10000 |         20273060 | False          |
| all_positive_cells | eventwise_minus_rank          | expected_postpromotion_net_gain |        72 |                60 |                   8.5023 |                           0.9500 |             6.2443 |             10.8047 |             10000 |         20273061 | False          |
| all_positive_cells | eventwise_minus_nested_volume | expected_postpromotion_net_gain |        72 |                60 |                   8.0797 |                           0.9500 |             6.0082 |             10.2736 |             10000 |         20273062 | False          |
| signal_050         | eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        36 |                60 |                   1.4102 |                           0.9500 |             0.6720 |              2.2889 |             10000 |         20273070 | False          |
| signal_050         | eventwise_minus_rank          | expected_postpromotion_net_gain |        36 |                60 |                   1.6977 |                           0.9500 |             0.8468 |              2.7186 |             10000 |         20273071 | False          |
| signal_050         | eventwise_minus_nested_volume | expected_postpromotion_net_gain |        36 |                60 |                   1.6949 |                           0.9500 |             0.8220 |              2.6954 |             10000 |         20273072 | False          |
| signal_100         | eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        36 |                60 |                   9.5254 |                           0.9500 |             7.0788 |             12.1643 |             10000 |         20273080 | False          |
| signal_100         | eventwise_minus_rank          | expected_postpromotion_net_gain |        36 |                60 |                  15.3069 |                           0.9500 |            11.5203 |             19.3459 |             10000 |         20273081 | False          |
| signal_100         | eventwise_minus_nested_volume | expected_postpromotion_net_gain |        36 |                60 |                  14.4644 |                           0.9500 |            10.8557 |             18.1323 |             10000 |         20273082 | False          |
| persistence_00     | eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        24 |                60 |                   3.8826 |                           0.9500 |             2.3958 |              5.4939 |             10000 |         20273090 | False          |
| persistence_00     | eventwise_minus_rank          | expected_postpromotion_net_gain |        24 |                60 |                   6.0358 |                           0.9500 |             4.1289 |              8.0654 |             10000 |         20273091 | False          |
| persistence_00     | eventwise_minus_nested_volume | expected_postpromotion_net_gain |        24 |                60 |                   5.3526 |                           0.9500 |             3.4708 |              7.3192 |             10000 |         20273092 | False          |
| persistence_50     | eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        24 |                60 |                   6.1033 |                           0.9500 |             4.1920 |              8.1685 |             10000 |         20273100 | False          |
| persistence_50     | eventwise_minus_rank          | expected_postpromotion_net_gain |        24 |                60 |                   8.8629 |                           0.9500 |             6.3240 |             11.6300 |             10000 |         20273101 | False          |
| persistence_50     | eventwise_minus_nested_volume | expected_postpromotion_net_gain |        24 |                60 |                   9.0327 |                           0.9500 |             6.5006 |             11.6956 |             10000 |         20273102 | False          |
| persistence_80     | eventwise_minus_minimum_bound | expected_postpromotion_net_gain |        24 |                60 |                   6.4175 |                           0.9500 |             4.4692 |              8.4662 |             10000 |         20273110 | False          |
| persistence_80     | eventwise_minus_rank          | expected_postpromotion_net_gain |        24 |                60 |                  10.6081 |                           0.9500 |             7.3185 |             14.0170 |             10000 |         20273111 | False          |
| persistence_80     | eventwise_minus_nested_volume | expected_postpromotion_net_gain |        24 |                60 |                   9.8536 |                           0.9500 |             6.8804 |             12.8788 |             10000 |         20273112 | False          |

All intervals are descriptive seed-cluster bootstrap summaries. They are not confirmatory inference and do not establish null calibration for the eventwise bound under Markov context. Zero-signal promotion rates are smoke diagnostics only.

Integrity: all expected rows present; positive support verified; 0 cap violations. Zero-signal controls contain 8,640 method-cell-seed rows; retain their cellwise promotion rates as descriptive only.

Frozen protocol: docs/scout_context_policy_eventwise_markov_development_protocol.md (SHA-256 bc5c2281aa656bfc0ea6a6126546d2bf174b791872ea8739592d42a817d672af). No figure was generated.
