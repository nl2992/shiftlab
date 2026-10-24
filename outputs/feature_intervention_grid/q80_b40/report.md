# Feature-dependent promotion/rollback development results

This is a synthetic development screen, not calibration or confirmation. The candidate is frozen before each stream. Querying is randomized with a logged fixed propensity and bounded by a pathwise label cap. Both actions' costs are identifiable from each queried binary outcome in this simulator.

- Device: `cuda`; seeds per scenario: 30; horizon: 400 events per phase.
- Query propensity: 0.8; total label cap: 40%; alpha: 0.05 split equally across promotion and rollback.
- Data rows: 720; all budget checks passed: True.
- No figures were generated in this run.

## Scenario means

| scenario            |   budget_rate | method                |   streams |   promotions |   promotion_rate |   rollbacks |   rollback_rate |   false_promotions |   false_rollbacks |   mean_expected_net_utility |   mean_realized_net_utility |   mean_labels |   maximum_labels | budget_respected   |
|:--------------------|--------------:|:----------------------|----------:|-------------:|-----------------:|------------:|----------------:|-------------------:|------------------:|----------------------------:|----------------------------:|--------------:|-----------------:|:-------------------|
| benign_nuisance     |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| benign_nuisance     |           0.4 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -3.18033  |                    -3.18033 |      318.033  |              320 | True               |
| benign_nuisance     |           0.4 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -3.18033  |                    -3.18033 |      318.033  |              320 | True               |
| benign_nuisance     |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                   -0.05     |                    12.15    |        0      |                0 | True               |
| boundary_local_harm |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| boundary_local_harm |           0.4 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -3.18033  |                    -3.18033 |      318.033  |              320 | True               |
| boundary_local_harm |           0.4 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -3.18033  |                    -3.18033 |      318.033  |              320 | True               |
| boundary_local_harm |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                  399.95     |                   406.617   |        0      |                0 | True               |
| harmful_adaptation  |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| harmful_adaptation  |           0.4 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                 -140.556    |                  -145.056   |       50.5667 |               92 | True               |
| harmful_adaptation  |           0.4 | promotion_rollback    |        30 |           30 |                1 |          28 |        0.933333 |                  0 |                 0 |                  -65.2183   |                   -67.075   |      191.167  |              320 | True               |
| harmful_adaptation  |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                 -140.05     |                  -144.55    |        0      |                0 | True               |
| persistent_benefit  |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| persistent_benefit  |           0.4 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  399.436    |                   397.369   |       51.4333 |              107 | True               |
| persistent_benefit  |           0.4 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  396.75     |                   394.683   |      320      |              320 | True               |
| persistent_benefit  |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  399.95     |                   397.883   |        0      |                0 | True               |
| rollback_boundary   |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| rollback_boundary   |           0.4 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   -0.601667 |                    11.1483  |       50.1667 |              117 | True               |
| rollback_boundary   |           0.4 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   -3.3      |                     8.45    |      320      |              320 | True               |
| rollback_boundary   |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   -0.1      |                    11.65    |        0      |                0 | True               |
| stationary          |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| stationary          |           0.4 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -3.18033  |                    -3.18033 |      318.033  |              320 | True               |
| stationary          |           0.4 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -3.18033  |                    -3.18033 |      318.033  |              320 | True               |
| stationary          |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                   -0.05     |                    -4.08333 |        0      |                0 | True               |

## Paired expected-utility contrasts

| scenario            |   budget_rate | method             | reference      |   paired_mean_expected_utility_difference |   seed_cluster_ci95_low |   seed_cluster_ci95_high |   seed_clusters |
|:--------------------|--------------:|:-------------------|:---------------|------------------------------------------:|------------------------:|-------------------------:|----------------:|
| benign_nuisance     |           0.4 | promotion_rollback | promotion_only |                                  0        |                0        |                 0        |              30 |
| benign_nuisance     |           0.4 | promotion_rollback | continue       |                                 -3.18033  |               -3.18967  |                -3.16967  |              30 |
| benign_nuisance     |           0.4 | promotion_only     | continue       |                                 -3.18033  |               -3.18967  |                -3.16933  |              30 |
| boundary_local_harm |           0.4 | promotion_rollback | promotion_only |                                  0        |                0        |                 0        |              30 |
| boundary_local_harm |           0.4 | promotion_rollback | continue       |                                 -3.18033  |               -3.18967  |                -3.16967  |              30 |
| boundary_local_harm |           0.4 | promotion_only     | continue       |                                 -3.18033  |               -3.18967  |                -3.16967  |              30 |
| harmful_adaptation  |           0.4 | promotion_rollback | promotion_only |                                 75.3373   |               63.9596   |                85.4977   |              30 |
| harmful_adaptation  |           0.4 | promotion_rollback | continue       |                                -65.2183   |              -76.5422   |               -54.9636   |              30 |
| harmful_adaptation  |           0.4 | promotion_only     | continue       |                               -140.556    |             -140.611    |              -140.502    |              30 |
| persistent_benefit  |           0.4 | promotion_rollback | promotion_only |                                 -2.68567  |               -2.74367  |                -2.62     |              30 |
| persistent_benefit  |           0.4 | promotion_rollback | continue       |                                396.75     |              396.75     |               396.75     |              30 |
| persistent_benefit  |           0.4 | promotion_only     | continue       |                                399.436    |              399.37     |               399.495    |              30 |
| rollback_boundary   |           0.4 | promotion_rollback | promotion_only |                                 -2.69833  |               -2.77268  |                -2.617    |              30 |
| rollback_boundary   |           0.4 | promotion_rollback | continue       |                                 -3.3      |               -3.3      |                -3.3      |              30 |
| rollback_boundary   |           0.4 | promotion_only     | continue       |                                 -0.601667 |               -0.684333 |                -0.528667 |              30 |
| stationary          |           0.4 | promotion_rollback | promotion_only |                                  0        |                0        |                 0        |              30 |
| stationary          |           0.4 | promotion_rollback | continue       |                                 -3.18033  |               -3.18967  |                -3.16933  |              30 |
| stationary          |           0.4 | promotion_only     | continue       |                                 -3.18033  |               -3.18967  |                -3.16967  |              30 |

## Limits

Costs and shift schedules are controlled synthetic choices. The nominal error guarantees require the listed independent-stream, predictable-query, conditional-mean, bounded-support, frozen-candidate, and stage-specific assumptions. This screen cannot establish general validity, literature novelty, or real-world decision utility. False-alarm counts from this grid are descriptive and do not replace a frozen independent calibration.
