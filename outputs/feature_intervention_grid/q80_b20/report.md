# Feature-dependent promotion/rollback development results

This is a synthetic development screen, not calibration or confirmation. The candidate is frozen before each stream. Querying is randomized with a logged fixed propensity and bounded by a pathwise label cap. Both actions' costs are identifiable from each queried binary outcome in this simulator.

- Device: `cuda`; seeds per scenario: 30; horizon: 400 events per phase.
- Query propensity: 0.8; total label cap: 20%; alpha: 0.05 split equally across promotion and rollback.
- Data rows: 720; all budget checks passed: True.
- No figures were generated in this run.

## Scenario means

| scenario            |   budget_rate | method                |   streams |   promotions |   promotion_rate |   rollbacks |   rollback_rate |   false_promotions |   false_rollbacks |   mean_expected_net_utility |   mean_realized_net_utility |   mean_labels |   maximum_labels | budget_respected   |
|:--------------------|--------------:|:----------------------|----------:|-------------:|-----------------:|------------:|----------------:|-------------------:|------------------:|----------------------------:|----------------------------:|--------------:|-----------------:|:-------------------|
| benign_nuisance     |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| benign_nuisance     |           0.2 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -1.6      |                    -1.6     |      160      |              160 | True               |
| benign_nuisance     |           0.2 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -1.6      |                    -1.6     |      160      |              160 | True               |
| benign_nuisance     |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                   -0.05     |                    12.15    |        0      |                0 | True               |
| boundary_local_harm |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| boundary_local_harm |           0.2 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -1.6      |                    -1.6     |      160      |              160 | True               |
| boundary_local_harm |           0.2 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -1.6      |                    -1.6     |      160      |              160 | True               |
| boundary_local_harm |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                  399.95     |                   406.617   |        0      |                0 | True               |
| harmful_adaptation  |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| harmful_adaptation  |           0.2 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                 -140.556    |                  -145.056   |       50.5667 |               92 | True               |
| harmful_adaptation  |           0.2 | promotion_rollback    |        30 |           30 |                1 |          11 |        0.366667 |                  0 |                 0 |                 -103.595    |                  -106.492   |      149      |              160 | True               |
| harmful_adaptation  |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                 -140.05     |                  -144.55    |        0      |                0 | True               |
| persistent_benefit  |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| persistent_benefit  |           0.2 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  399.436    |                   397.369   |       51.4333 |              107 | True               |
| persistent_benefit  |           0.2 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  398.35     |                   396.283   |      160      |              160 | True               |
| persistent_benefit  |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                  399.95     |                   397.883   |        0      |                0 | True               |
| rollback_boundary   |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| rollback_boundary   |           0.2 | promotion_only        |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   -0.601667 |                    11.1483  |       50.1667 |              117 | True               |
| rollback_boundary   |           0.2 | promotion_rollback    |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   -1.7      |                    10.05    |      160      |              160 | True               |
| rollback_boundary   |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                  0 |                 0 |                   -0.1      |                    11.65    |        0      |                0 | True               |
| stationary          |           0.2 | continue              |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                    0        |                     0       |        0      |                0 | True               |
| stationary          |           0.2 | promotion_only        |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -1.6      |                    -1.6     |      160      |              160 | True               |
| stationary          |           0.2 | promotion_rollback    |        30 |            0 |                0 |           0 |        0        |                  0 |                 0 |                   -1.6      |                    -1.6     |      160      |              160 | True               |
| stationary          |           0.2 | unconditional_promote |        30 |           30 |                1 |           0 |        0        |                 30 |                 0 |                   -0.05     |                    -4.08333 |        0      |                0 | True               |

## Paired expected-utility contrasts

| scenario            |   budget_rate | method             | reference      |   paired_mean_expected_utility_difference |   seed_cluster_ci95_low |   seed_cluster_ci95_high |   seed_clusters |
|:--------------------|--------------:|:-------------------|:---------------|------------------------------------------:|------------------------:|-------------------------:|----------------:|
| benign_nuisance     |           0.2 | promotion_rollback | promotion_only |                                  0        |                0        |                 0        |              30 |
| benign_nuisance     |           0.2 | promotion_rollback | continue       |                                 -1.6      |               -1.6      |                -1.6      |              30 |
| benign_nuisance     |           0.2 | promotion_only     | continue       |                                 -1.6      |               -1.6      |                -1.6      |              30 |
| boundary_local_harm |           0.2 | promotion_rollback | promotion_only |                                  0        |                0        |                 0        |              30 |
| boundary_local_harm |           0.2 | promotion_rollback | continue       |                                 -1.6      |               -1.6      |                -1.6      |              30 |
| boundary_local_harm |           0.2 | promotion_only     | continue       |                                 -1.6      |               -1.6      |                -1.6      |              30 |
| harmful_adaptation  |           0.2 | promotion_rollback | promotion_only |                                 36.9607   |               19.5562   |                55.0817   |              30 |
| harmful_adaptation  |           0.2 | promotion_rollback | continue       |                               -103.595    |             -121.045    |               -85.6318   |              30 |
| harmful_adaptation  |           0.2 | promotion_only     | continue       |                               -140.556    |             -140.611    |              -140.502    |              30 |
| persistent_benefit  |           0.2 | promotion_rollback | promotion_only |                                 -1.08567  |               -1.14367  |                -1.02     |              30 |
| persistent_benefit  |           0.2 | promotion_rollback | continue       |                                398.35     |              398.35     |               398.35     |              30 |
| persistent_benefit  |           0.2 | promotion_only     | continue       |                                399.436    |              399.37     |               399.495    |              30 |
| rollback_boundary   |           0.2 | promotion_rollback | promotion_only |                                 -1.09833  |               -1.17268  |                -1.017    |              30 |
| rollback_boundary   |           0.2 | promotion_rollback | continue       |                                 -1.7      |               -1.7      |                -1.7      |              30 |
| rollback_boundary   |           0.2 | promotion_only     | continue       |                                 -0.601667 |               -0.684333 |                -0.528667 |              30 |
| stationary          |           0.2 | promotion_rollback | promotion_only |                                  0        |                0        |                 0        |              30 |
| stationary          |           0.2 | promotion_rollback | continue       |                                 -1.6      |               -1.6      |                -1.6      |              30 |
| stationary          |           0.2 | promotion_only     | continue       |                                 -1.6      |               -1.6      |                -1.6      |              30 |

## Limits

Costs and shift schedules are controlled synthetic choices. The nominal error guarantees require the listed independent-stream, predictable-query, conditional-mean, bounded-support, frozen-candidate, and stage-specific assumptions. This screen cannot establish general validity, literature novelty, or real-world decision utility. False-alarm counts from this grid are descriptive and do not replace a frozen independent calibration.
