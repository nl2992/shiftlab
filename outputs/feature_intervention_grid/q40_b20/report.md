# Feature-dependent promotion/rollback development results

This is a synthetic development screen, not calibration or confirmation. The candidate is frozen before each stream. Querying is randomized with a logged fixed propensity and bounded by a pathwise label cap. Both actions' costs are identifiable from each queried binary outcome in this simulator.

- Device: `cuda`; seeds per scenario: 30; horizon: 400 events per phase.
- Query propensity: 0.4; total label cap: 20%; alpha: 0.05 split equally across promotion and rollback.
- Data rows: 720; all budget checks passed: True.
- No figures were generated in this run.

## Scenario means

| scenario            |   budget_rate | method                |   streams |   promotions |   promotion_rate |   rollbacks |   rollback_rate |   false_promotions |   false_rollbacks |   mean_expected_net_utility |   mean_realized_net_utility |   mean_labels |   maximum_labels | budget_respected   |
|:--------------------|--------------:|:----------------------|----------:|-------------:|-----------------:|------------:|----------------:|-------------------:|------------------:|----------------------------:|----------------------------:|--------------:|-----------------:|:-------------------|
| benign_nuisance     |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| benign_nuisance     |           0.2 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.563   |                    -1.563   |      156.3    |              160 | True               |
| benign_nuisance     |           0.2 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.563   |                    -1.563   |      156.3    |              160 | True               |
| benign_nuisance     |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                    -0.05    |                    12.15    |        0      |                0 | True               |
| boundary_local_harm |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| boundary_local_harm |           0.2 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.563   |                    -1.563   |      156.3    |              160 | True               |
| boundary_local_harm |           0.2 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.563   |                    -1.563   |      156.3    |              160 | True               |
| boundary_local_harm |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                   399.95    |                   406.617   |        0      |                0 | True               |
| harmful_adaptation  |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| harmful_adaptation  |           0.2 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  -140.552   |                  -145.052   |       50.2333 |               87 | True               |
| harmful_adaptation  |           0.2 | promotion_rollback    |        30 |           30 |                1 |          14 |        0.466667 |                  0 |                 0 |                  -108.883   |                  -113.948   |      144.1    |              160 | True               |
| harmful_adaptation  |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  -140.05    |                  -144.55    |        0      |                0 | True               |
| persistent_benefit  |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| persistent_benefit  |           0.2 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   399.443   |                   397.376   |       50.7333 |               95 | True               |
| persistent_benefit  |           0.2 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   398.35    |                   396.283   |      160      |              160 | True               |
| persistent_benefit  |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   399.95    |                   397.883   |        0      |                0 | True               |
| rollback_boundary   |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| rollback_boundary   |           0.2 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                    -0.562   |                    11.188   |       46.2    |               80 | True               |
| rollback_boundary   |           0.2 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                    -1.69967 |                    10.0503  |      159.967  |              160 | True               |
| rollback_boundary   |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                    -0.1     |                    11.65    |        0      |                0 | True               |
| stationary          |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                     0       |                     0       |        0      |                0 | True               |
| stationary          |           0.2 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.563   |                    -1.563   |      156.3    |              160 | True               |
| stationary          |           0.2 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    -1.563   |                    -1.563   |      156.3    |              160 | True               |
| stationary          |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                    -0.05    |                    -4.08333 |        0      |                0 | True               |

## Paired expected-utility contrasts

| scenario            |   budget_rate | method             | reference      |   paired_mean_expected_utility_difference |   seed_cluster_ci95_low |   seed_cluster_ci95_high |   seed_clusters |
|:--------------------|--------------:|:-------------------|:---------------|------------------------------------------:|------------------------:|-------------------------:|----------------:|
| benign_nuisance     |           0.2 | promotion_rollback | promotion_only |                                   0       |                 0       |                 0        |              30 |
| benign_nuisance     |           0.2 | promotion_rollback | continue       |                                  -1.563   |                -1.58233 |                -1.539    |              30 |
| benign_nuisance     |           0.2 | promotion_only     | continue       |                                  -1.563   |                -1.582   |                -1.53933  |              30 |
| boundary_local_harm |           0.2 | promotion_rollback | promotion_only |                                   0       |                 0       |                 0        |              30 |
| boundary_local_harm |           0.2 | promotion_rollback | continue       |                                  -1.563   |                -1.58267 |                -1.53933  |              30 |
| boundary_local_harm |           0.2 | promotion_only     | continue       |                                  -1.563   |                -1.582   |                -1.53933  |              30 |
| harmful_adaptation  |           0.2 | promotion_rollback | promotion_only |                                  31.6697  |                18.5813  |                45.1919   |              30 |
| harmful_adaptation  |           0.2 | promotion_rollback | continue       |                                -108.883   |              -121.847   |               -95.5345   |              30 |
| harmful_adaptation  |           0.2 | promotion_only     | continue       |                                -140.552   |              -140.603   |              -140.505    |              30 |
| persistent_benefit  |           0.2 | promotion_rollback | promotion_only |                                  -1.09267 |                -1.15133 |                -1.02999  |              30 |
| persistent_benefit  |           0.2 | promotion_rollback | continue       |                                 398.35    |               398.35    |               398.35     |              30 |
| persistent_benefit  |           0.2 | promotion_only     | continue       |                                 399.443   |               399.38    |               399.501    |              30 |
| rollback_boundary   |           0.2 | promotion_rollback | promotion_only |                                  -1.13767 |                -1.18733 |                -1.08733  |              30 |
| rollback_boundary   |           0.2 | promotion_rollback | continue       |                                  -1.69967 |                -1.7     |                -1.699    |              30 |
| rollback_boundary   |           0.2 | promotion_only     | continue       |                                  -0.562   |                -0.612   |                -0.511667 |              30 |
| stationary          |           0.2 | promotion_rollback | promotion_only |                                   0       |                 0       |                 0        |              30 |
| stationary          |           0.2 | promotion_rollback | continue       |                                  -1.563   |                -1.58233 |                -1.53933  |              30 |
| stationary          |           0.2 | promotion_only     | continue       |                                  -1.563   |                -1.58267 |                -1.53967  |              30 |

## Limits

Costs and shift schedules are controlled synthetic choices. The nominal error guarantees require the listed independent-stream, predictable-query, conditional-mean, bounded-support, frozen-candidate, and stage-specific assumptions. This screen cannot establish general validity, literature novelty, or real-world decision utility. False-alarm counts from this grid are descriptive and do not replace a frozen independent calibration.
