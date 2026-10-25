# Predictable query allocation for the eventwise target scout

Status: **exploratory_development**. Device: `cuda`; seeds/cell: 60; seed block: 20930000–20930059; workers: 6.

The grid covers 72 profile/cap cells, three query policies, four decision rules, and 51,840 matched stream-method rows. Query policies are uniform, variance-weighted, and decision-value-weighted; every method uses the same seed-specific uniforms across these policies. The eventwise monitor sees each propensity before its label and uses the corresponding predictable bound.

## Paired positive-signal development contrasts

| comparison                                    | metric                          |   n_positive_cells |   n_seed_clusters |   equal_cell_mean_difference |   descriptive_bootstrap_ci_level |   bootstrap_ci_low |   bootstrap_ci_high |   bootstrap_draws |   bootstrap_seed | confirmatory   |
|:----------------------------------------------|:--------------------------------|-------------------:|------------------:|-----------------------------:|---------------------------------:|-------------------:|--------------------:|------------------:|-----------------:|:---------------|
| eventwise_minus_minimum_bound__uniform        | expected_postpromotion_net_gain |                 48 |                60 |                       5.4480 |                           0.9500 |             3.7311 |              7.4030 |             10000 |         20930060 | False          |
| eventwise_minus_minimum_bound__uniform        | labels_queried                  |                 48 |                60 |                       0.0000 |                           0.9500 |             0.0000 |              0.0000 |             10000 |         20930061 | False          |
| eventwise_minus_minimum_bound__uniform        | mean_event_process_bound        |                 48 |                60 |                     -18.7500 |                           0.9500 |           -18.7500 |            -18.7500 |             10000 |         20930062 | False          |
| eventwise_minus_minimum_bound__variance       | expected_postpromotion_net_gain |                 48 |                60 |                       6.7293 |                           0.9500 |             4.6690 |              9.0338 |             10000 |         20930063 | False          |
| eventwise_minus_minimum_bound__variance       | labels_queried                  |                 48 |                60 |                       0.0000 |                           0.9500 |             0.0000 |              0.0000 |             10000 |         20930064 | False          |
| eventwise_minus_minimum_bound__variance       | mean_event_process_bound        |                 48 |                60 |                     -17.4616 |                           0.9500 |           -17.6217 |            -17.3012 |             10000 |         20930065 | False          |
| eventwise_minus_minimum_bound__decision_value | expected_postpromotion_net_gain |                 48 |                60 |                       6.7293 |                           0.9500 |             4.6614 |              9.0148 |             10000 |         20930066 | False          |
| eventwise_minus_minimum_bound__decision_value | labels_queried                  |                 48 |                60 |                       0.0000 |                           0.9500 |             0.0000 |              0.0000 |             10000 |         20930067 | False          |
| eventwise_minus_minimum_bound__decision_value | mean_event_process_bound        |                 48 |                60 |                     -17.4616 |                           0.9500 |           -17.6235 |            -17.2989 |             10000 |         20930068 | False          |
| eventwise_variance_minus_uniform              | expected_postpromotion_net_gain |                 48 |                60 |                       2.1302 |                           0.9500 |             0.7221 |              3.5899 |             10000 |         20930069 | False          |
| eventwise_variance_minus_uniform              | labels_queried                  |                 48 |                60 |                       0.2660 |                           0.9500 |            -0.7674 |              1.2597 |             10000 |         20930070 | False          |
| eventwise_variance_minus_uniform              | mean_event_process_bound        |                 48 |                60 |                       1.2884 |                           0.9500 |             1.1263 |              1.4531 |             10000 |         20930071 | False          |
| eventwise_decision_value_minus_uniform        | expected_postpromotion_net_gain |                 48 |                60 |                       2.1302 |                           0.9500 |             0.7149 |              3.6088 |             10000 |         20930072 | False          |
| eventwise_decision_value_minus_uniform        | labels_queried                  |                 48 |                60 |                       0.2660 |                           0.9500 |            -0.7334 |              1.2507 |             10000 |         20930073 | False          |
| eventwise_decision_value_minus_uniform        | mean_event_process_bound        |                 48 |                60 |                       1.2884 |                           0.9500 |             1.1273 |              1.4538 |             10000 |         20930074 | False          |

Intervals resample seed clusters and equally weight profile/cap cells. They are development summaries after scanning query and decision rules, not confirmatory inference. Zero-signal promotion rates are diagnostic only; any candidate requires a fresh null calibration and a disjoint confirmation before a power or utility claim.

## Zero-signal controls

| query_policy   | alpha_allocation                                |   streams |   promotions |   harmful_promotions |   promotion_rate |   mean_labels |   mean_bound |
|:---------------|:------------------------------------------------|----------:|-------------:|---------------------:|-----------------:|--------------:|-------------:|
| decision_value | rank                                            |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      37.5001 |
| decision_value | rank_context_volume                             |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      37.5001 |
| decision_value | scout_context_policy                            |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      37.5001 |
| decision_value | scout_context_policy_eventwise_propensity_bound |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      20.0385 |
| uniform        | rank                                            |      1440 |            0 |                    0 |           0.0000 |      471.3583 |      37.5001 |
| uniform        | rank_context_volume                             |      1440 |            0 |                    0 |           0.0000 |      471.3583 |      37.5001 |
| uniform        | scout_context_policy                            |      1440 |            0 |                    0 |           0.0000 |      471.3583 |      37.5001 |
| uniform        | scout_context_policy_eventwise_propensity_bound |      1440 |            0 |                    0 |           0.0000 |      471.3583 |      18.7501 |
| variance       | rank                                            |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      37.5001 |
| variance       | rank_context_volume                             |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      37.5001 |
| variance       | scout_context_policy                            |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      37.5001 |
| variance       | scout_context_policy_eventwise_propensity_bound |      1440 |            0 |                    0 |           0.0000 |      471.6243 |      20.0385 |

## Mathematical condition and scope

For a fixed candidate selected on the disjoint scout slice, let `G_t` be its bounded paired cost improvement, `Q_t` the randomized label indicator, `q_t` its learner-visible predictable query probability, and `kappa` the per-event switching charge. Under the certification null `E[G_t | F_{t-1}, X_t] <= kappa`, independent Bernoulli querying gives `E[Q_t G_t/q_t - kappa | F_{t-1}, X_t] <= 0`. If `|G_t| <= C`, the increment is bounded by `B_t=C/q_t+kappa`, known before the label. Therefore each fixed bounded-betting factor `1 + lambda * increment / B_t`, for `lambda in [0,1]`, has conditional expectation at most one; the frozen mixture is an e-process under this filtration. This is a predictable-bound application of the standard betting argument, not a new theorem.

The query policies here are covariate-adaptive but fixed from pre-monitor fits; this grid does not test propensities adapted to prior certification evidence, delayed or outcome-dependent feedback, conditional-null violations, or real data. These results cannot support a novelty claim.

Frozen protocol: `docs/scout_context_policy_eventwise_query_development_protocol.md` (SHA-256 `74208661a227c8b6e2cea4c4294a904efafeafe630f8ae00935a7120e0a25119`). No figure was generated.
