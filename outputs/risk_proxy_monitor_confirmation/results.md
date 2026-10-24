# Independent fixed-mixture monitor confirmation

Independent seed blocks: {'stationary': [20405024, 20407023], 'benign_nuisance': [20405024, 20407023], 'boundary_local_harm': [20407024, 20408023], 'harmful_adaptation': [20407024, 20408023]}. Query rate: 20%. Streams: 12,000 monitor-stream rows.

## Frozen decision rule

Advance the fixed-mixture monitor only if all four Bonferroni null cells pass the 5% upper-bound screen, the paired macro detection interval across boundary harm and harmful adaptation is entirely above zero, and neither scenario's point estimate favors Kelly.

Decision: `{'null_calibration_pass': True, 'primary_macro_interval_above_zero': True, 'no_registered_scenario_point_loss': True, 'advance_fixed_mixture': True}`

## Alternative results

| scenario            | method            |   streams |   detections |   detection_rate |   false_alarms |   mean_detection_delay |   mean_labels |   mean_spend |   mean_events_processed |
|:--------------------|:------------------|----------:|-------------:|-----------------:|---------------:|-----------------------:|--------------:|-------------:|------------------------:|
| boundary_local_harm | fixed_mixture     |      1000 |          494 |           0.4940 |              0 |               955.2551 |      312.1860 |     468.5598 |               1561.3690 |
| boundary_local_harm | predictable_kelly |      1000 |          393 |           0.3930 |              0 |               993.9186 |      312.1860 |     468.5598 |               1561.3690 |
| harmful_adaptation  | fixed_mixture     |      1000 |          633 |           0.6330 |              0 |               982.4360 |      312.1860 |     468.5598 |               1561.3690 |
| harmful_adaptation  | predictable_kelly |      1000 |          466 |           0.4660 |              0 |              1033.4506 |      312.1860 |     468.5598 |               1561.3690 |

## Paired primary and scenario contrasts

| scenario               |   fixed_detection_rate |   kelly_detection_rate |   fixed_minus_kelly |   seed_cluster_ci95_low |   seed_cluster_ci95_high |   seed_clusters | primary   |
|:-----------------------|-----------------------:|-----------------------:|--------------------:|------------------------:|-------------------------:|----------------:|:----------|
| macro_two_alternatives |                 0.5635 |                 0.4295 |              0.1340 |                  0.1195 |                   0.1490 |            1000 | True      |
| boundary_local_harm    |                 0.4940 |                 0.3930 |              0.1010 |                  0.0830 |                   0.1200 |            1000 | False     |
| harmful_adaptation     |                 0.6330 |                 0.4660 |              0.1670 |                  0.1440 |                   0.1900 |            1000 | False     |

## Independent null calibration

| scenario        | method            |   false_alarms |   streams |   false_alarm_rate |   bonferroni_one_sided_cp95_upper |   familywise_alpha |   family_cells | calibration_pass   |
|:----------------|:------------------|---------------:|----------:|-------------------:|----------------------------------:|-------------------:|---------------:|:-------------------|
| benign_nuisance | fixed_mixture     |              0 |      2000 |            0.00000 |                           0.00219 |            0.05000 |              4 | True               |
| benign_nuisance | predictable_kelly |              0 |      2000 |            0.00000 |                           0.00219 |            0.05000 |              4 | True               |
| stationary      | fixed_mixture     |              0 |      2000 |            0.00000 |                           0.00219 |            0.05000 |              4 | True               |
| stationary      | predictable_kelly |              0 |      2000 |            0.00000 |                           0.00219 |            0.05000 |              4 | True               |

The monitors share the same frozen logistic proxy, Bernoulli queries, labels, spend, and stopping horizon. This is a baseline confirmation, not a novel method. Its e-process claims still require the stated history-conditional null, known support bounds, and outcome-independent query randomization.
