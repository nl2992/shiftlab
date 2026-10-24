# Feature-dependent promotion/rollback development results

This is a synthetic development screen, not calibration or confirmation. The candidate is frozen before each stream. Querying is randomized with a logged fixed propensity and bounded by a pathwise label cap. Both actions' costs are identifiable from each queried binary outcome in this simulator.

- Device: `cuda`; seeds per scenario: 30; horizon: 400 events per phase.
- Query propensity: 0.4; total label cap: 40%; alpha: 0.05 split equally across promotion and rollback.
- Data rows: 720; all budget checks passed: True.
- No figures were generated in this run.

## Scenario means

| scenario            |   budget_rate | method                |   streams |   promotions |   promotion_rate |   rollbacks |   rollback_rate |   false_promotions |   false_rollbacks |   mean_expected_net_utility |   mean_realized_net_utility |   mean_labels |   maximum_labels | budget_respected   |
|:--------------------|--------------:|:----------------------|----------:|-------------:|-----------------:|------------:|----------------:|-------------------:|------------------:|----------------------------:|----------------------------:|--------------:|-----------------:|:-------------------|
| benign_nuisance     |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| benign_nuisance     |           0.4 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.61633 |                    -1.61633 |      161.633  |              182 | True               |
| benign_nuisance     |           0.4 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.61633 |                    -1.61633 |      161.633  |              182 | True               |
| benign_nuisance     |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                    -0.05    |                    12.15    |        0      |                0 | True               |
| boundary_local_harm |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| boundary_local_harm |           0.4 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.61633 |                    -1.61633 |      161.633  |              182 | True               |
| boundary_local_harm |           0.4 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.61633 |                    -1.61633 |      161.633  |              182 | True               |
| boundary_local_harm |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                   399.95    |                   406.617   |        0      |                0 | True               |
| harmful_adaptation  |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| harmful_adaptation  |           0.4 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  -140.552   |                  -145.052   |       50.2333 |               87 | True               |
| harmful_adaptation  |           0.4 | promotion_rollback    |        30 |           30 |                1 |          23 |        0.766667 |                  0 |                 0 |                  -101.426   |                  -104.901   |      164.567  |              229 | True               |
| harmful_adaptation  |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  -140.05    |                  -144.55    |        0      |                0 | True               |
| persistent_benefit  |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| persistent_benefit  |           0.4 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   399.443   |                   397.376   |       50.7333 |               95 | True               |
| persistent_benefit  |           0.4 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   397.84    |                   395.773   |      211      |              252 | True               |
| persistent_benefit  |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   399.95    |                   397.883   |        0      |                0 | True               |
| rollback_boundary   |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| rollback_boundary   |           0.4 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                    -0.562   |                    11.188   |       46.2    |               80 | True               |
| rollback_boundary   |           0.4 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                    -2.16467 |                     9.58533 |      206.467  |              254 | True               |
| rollback_boundary   |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                    -0.1     |                    11.65    |        0      |                0 | True               |
| stationary          |           0.4 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| stationary          |           0.4 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.61633 |                    -1.61633 |      161.633  |              182 | True               |
| stationary          |           0.4 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.61633 |                    -1.61633 |      161.633  |              182 | True               |
| stationary          |           0.4 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                    -0.05    |                    -4.08333 |        0      |                0 | True               |

## Paired expected-utility contrasts

| scenario            |   budget_rate | method             | reference      |   paired_mean_expected_utility_difference |   seed_cluster_ci95_low |   seed_cluster_ci95_high |   seed_clusters |
|:--------------------|--------------:|:-------------------|:---------------|------------------------------------------:|------------------------:|-------------------------:|----------------:|
| benign_nuisance     |           0.4 | promotion_rollback | promotion_only |                                   0       |                 0       |                 0        |              30 |
| benign_nuisance     |           0.4 | promotion_rollback | continue       |                                  -1.61633 |                -1.65467 |                -1.57733  |              30 |
| benign_nuisance     |           0.4 | promotion_only     | continue       |                                  -1.61633 |                -1.65333 |                -1.57633  |              30 |
| boundary_local_harm |           0.4 | promotion_rollback | promotion_only |                                   0       |                 0       |                 0        |              30 |
| boundary_local_harm |           0.4 | promotion_rollback | continue       |                                  -1.61633 |                -1.65533 |                -1.576    |              30 |
| boundary_local_harm |           0.4 | promotion_only     | continue       |                                  -1.61633 |                -1.65467 |                -1.57633  |              30 |
| harmful_adaptation  |           0.4 | promotion_rollback | promotion_only |                                  39.1267  |                27.4447  |                51.1522   |              30 |
| harmful_adaptation  |           0.4 | promotion_rollback | continue       |                                -101.426   |              -113.081   |               -89.5449   |              30 |
| harmful_adaptation  |           0.4 | promotion_only     | continue       |                                -140.552   |              -140.603   |              -140.505    |              30 |
| persistent_benefit  |           0.4 | promotion_rollback | promotion_only |                                  -1.60267 |                -1.64233 |                -1.565    |              30 |
| persistent_benefit  |           0.4 | promotion_rollback | continue       |                                 397.84    |               397.773   |               397.906    |              30 |
| persistent_benefit  |           0.4 | promotion_only     | continue       |                                 399.443   |               399.38    |               399.501    |              30 |
| rollback_boundary   |           0.4 | promotion_rollback | promotion_only |                                  -1.60267 |                -1.64233 |                -1.565    |              30 |
| rollback_boundary   |           0.4 | promotion_rollback | continue       |                                  -2.16467 |                -2.23268 |                -2.09567  |              30 |
| rollback_boundary   |           0.4 | promotion_only     | continue       |                                  -0.562   |                -0.612   |                -0.511667 |              30 |
| stationary          |           0.4 | promotion_rollback | promotion_only |                                   0       |                 0       |                 0        |              30 |
| stationary          |           0.4 | promotion_rollback | continue       |                                  -1.61633 |                -1.65467 |                -1.57667  |              30 |
| stationary          |           0.4 | promotion_only     | continue       |                                  -1.61633 |                -1.655   |                -1.57699  |              30 |

## Limits

Costs and shift schedules are controlled synthetic choices. The nominal error guarantees require the listed independent-stream, predictable-query, conditional-mean, bounded-support, frozen-candidate, and stage-specific assumptions. This screen cannot establish general validity, literature novelty, or real-world decision utility. False-alarm counts from this grid are descriptive and do not replace a frozen independent calibration.
