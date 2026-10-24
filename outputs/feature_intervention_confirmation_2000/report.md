# Feature-dependent intervention confirmation

Rollback mechanism retention: **rollback_mechanism_retained**.

- Calibration manifest SHA-256: `2010cb00beb752a1ce223a7d02898b4f6e87d9e9edd720a81a36847235260395`.
- Fresh confirmation block begins at seed offset 78102024; 2000 seeds per scenario; CUDA device `cuda`.
- Primary harmful-reversal contrast: 71.1904 expected utility units, paired 95% seed-bootstrap interval [69.6604, 72.6991].
- Net utility against `continue` under harmful reversal: -69.3769, paired 95% interval [-70.8713, -67.9047].
- All hard label caps respected: True.

## Scenario results

| scenario            | method                |   streams |   promotions |   promotion_rate |   rollbacks |   rollback_rate |   mean_rollback_event |   mean_expected_net_utility |   mean_realized_net_utility |   mean_labels |   maximum_labels | budget_respected   |
|:--------------------|:----------------------|----------:|-------------:|-----------------:|------------:|----------------:|----------------------:|----------------------------:|----------------------------:|--------------:|-----------------:|:-------------------|
| boundary_local_harm | continue              |      2000 |            0 |           0      |           0 |           0     |               nan     |                    0        |                    0        |         0     |                0 | True               |
| boundary_local_harm | promotion_only        |      2000 |           11 |           0.0055 |           0 |           0     |               nan     |                   -0.958045 |                   -0.913545 |       315.777 |              320 | True               |
| boundary_local_harm | promotion_rollback    |      2000 |           11 |           0.0055 |           0 |           0     |               nan     |                   -0.96777  |                   -0.92327  |       316.75  |              320 | True               |
| boundary_local_harm | unconditional_promote |      2000 |         2000 |           1      |           0 |           0     |               nan     |                  399.95     |                  399.41     |         0     |                0 | True               |
| harmful_adaptation  | continue              |      2000 |            0 |           0      |           0 |           0     |               nan     |                    0        |                    0        |         0     |                0 | True               |
| harmful_adaptation  | promotion_only        |      2000 |         2000 |           1      |           0 |           0     |               nan     |                 -140.567    |                 -140.871    |        51.724 |              157 | True               |
| harmful_adaptation  | promotion_rollback    |      2000 |         2000 |           1      |        1790 |           0.895 |               166.882 |                  -69.3769   |                  -69.6698   |       199.305 |              320 | True               |
| harmful_adaptation  | unconditional_promote |      2000 |         2000 |           1      |           0 |           0     |               nan     |                 -140.05     |                 -140.354    |         0     |                0 | True               |
| persistent_benefit  | continue              |      2000 |            0 |           0      |           0 |           0     |               nan     |                    0        |                    0        |         0     |                0 | True               |
| persistent_benefit  | promotion_only        |      2000 |         2000 |           1      |           0 |           0     |               nan     |                  399.433    |                  401.979    |        51.697 |              154 | True               |
| persistent_benefit  | promotion_rollback    |      2000 |         2000 |           1      |           0 |           0     |               nan     |                  396.75     |                  399.296    |       319.998 |              320 | True               |
| persistent_benefit  | unconditional_promote |      2000 |         2000 |           1      |           0 |           0     |               nan     |                  399.95     |                  402.496    |         0     |                0 | True               |

## Paired expected-utility contrasts

| scenario            |   budget_rate | method             | reference      |   paired_mean_expected_utility_difference |   seed_cluster_ci95_low |   seed_cluster_ci95_high |   seed_clusters |
|:--------------------|--------------:|:-------------------|:---------------|------------------------------------------:|------------------------:|-------------------------:|----------------:|
| boundary_local_harm |           0.4 | promotion_rollback | promotion_only |                                 -0.009725 |               -0.016375 |              -0.00416962 |            2000 |
| boundary_local_harm |           0.4 | promotion_rollback | continue       |                                 -0.96777  |               -2.16755  |               0.431855   |            2000 |
| boundary_local_harm |           0.4 | promotion_only     | continue       |                                 -0.958045 |               -2.16318  |               0.44754    |            2000 |
| harmful_adaptation  |           0.4 | promotion_rollback | promotion_only |                                 71.1904   |               69.6604   |              72.6991     |            2000 |
| harmful_adaptation  |           0.4 | promotion_rollback | continue       |                                -69.3769   |              -70.8713   |             -67.9047     |            2000 |
| harmful_adaptation  |           0.4 | promotion_only     | continue       |                               -140.567    |             -140.576    |            -140.559      |            2000 |
| persistent_benefit  |           0.4 | promotion_rollback | promotion_only |                                 -2.68301  |               -2.69159  |              -2.67436    |            2000 |
| persistent_benefit  |           0.4 | promotion_rollback | continue       |                                396.75     |              396.75     |             396.75       |            2000 |
| persistent_benefit  |           0.4 | promotion_only     | continue       |                                399.433    |              399.424    |             399.441      |            2000 |

These results apply only to the frozen, immediate-label simulator and its registered cost schedules. No figures were generated.
