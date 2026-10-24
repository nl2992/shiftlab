# Delayed history-predictable bound: independent harm confirmation

- Streams per harm dose and arm: 2000; total rows: 16000.
- Horizon: 2400; delay: 12; q_min/q_max: 0.05/0.80; hard label cap: 480.
- Stream generation device: cuda; sequential monitor replay: CPU NumPy.
- Fresh confirmation seed root: 27604027; calibration seed root: 27504027.
- Detection retention rule: lower 95% paired-bootstrap limit for the equal-weight macro gain must exceed +2 percentage points; paired label-difference upper limit must be at most zero; separate null calibration upper limits must all be at most 5%.
- No further tuning was performed on confirmation seeds. The test covers only iid events and deterministic outcome-independent feedback delay.
- No figure was generated because PaperBanana is unavailable in the active environment.

## Independent calibration

| scenario                       | arm         |   streams |   false_escalations |   false_rate |   simultaneous_one_sided_95_upper |   per_cell_alpha | passes_5pct_calibration_gate   |   mean_labels |   mean_events_processed |
|:-------------------------------|:------------|----------:|--------------------:|-------------:|----------------------------------:|-----------------:|:-------------------------------|--------------:|------------------------:|
| mixed_sign_exact_marginal_null | fixed       |      2000 |                   5 |       0.0025 |                            0.0064 |           0.0125 | True                           |      298.6965 |               2399.2990 |
| mixed_sign_exact_marginal_null | predictable |      2000 |                  44 |       0.0220 |                            0.0305 |           0.0125 | True                           |      172.1330 |               2359.9010 |
| strict_negative_control        | fixed       |      2000 |                   1 |       0.0005 |                            0.0032 |           0.0125 | True                           |      283.5585 |               2399.9285 |
| strict_negative_control        | predictable |      2000 |                  30 |       0.0150 |                            0.0223 |           0.0125 | True                           |      167.1345 |               2372.0250 |

## Harm dose response

| scenario                   |   fixed_detection_rate |   predictable_detection_rate |   paired_detection_difference | paired_detection_ci95   |   fixed_onset_reach_rate |   predictable_onset_reach_rate |   paired_label_difference | paired_label_ci95                          |   paired_exposure_difference |
|:---------------------------|-----------------------:|-----------------------------:|------------------------------:|:------------------------|-------------------------:|-------------------------------:|--------------------------:|:-------------------------------------------|-----------------------------:|
| high_cost_local_harm_d0.04 |                 0.0030 |                       0.0010 |                       -0.0020 | (-0.0045, 0.0)          |                   1.0000 |                         0.9800 |                 -126.1870 | (-130.40356250000002, -122.03128749999999) |                      -0.9367 |
| high_cost_local_harm_d0.20 |                 0.0070 |                       0.0110 |                        0.0040 | (-0.001, 0.0095)        |                   1.0000 |                         0.9795 |                 -129.0605 | (-133.36803749999999, -124.7998875)        |                      -5.4629 |
| high_cost_local_harm_d0.40 |                 0.0235 |                       0.0525 |                        0.0290 | (0.0195, 0.0385)        |                   1.0000 |                         0.9880 |                 -135.0175 | (-139.35764999999998, -130.67442499999999) |                     -13.8912 |
| high_cost_local_harm_d0.60 |                 0.0650 |                       0.1595 |                        0.0945 | (0.078, 0.1115)         |                   1.0000 |                         0.9840 |                 -134.7370 | (-139.1510125, -130.4254375)               |                     -43.4622 |

## Operational characteristics

| scenario                   | bound_mode   |   streams |   false_escalations_before_onset |   onset_reach_rate |   detection_rate |   mean_labels |   mean_events_processed |   mean_event_delay_given_detection |   mean_wall_delay_given_detection |
|:---------------------------|:-------------|----------:|---------------------------------:|-------------------:|-----------------:|--------------:|------------------------:|-----------------------------------:|----------------------------------:|
| high_cost_local_harm_d0.04 | fixed        |      2000 |                                0 |             1.0000 |           0.0030 |      300.7010 |               2399.2295 |                           963.6667 |                          975.5000 |
| high_cost_local_harm_d0.04 | predictable  |      2000 |                               40 |             0.9800 |           0.0010 |      174.5140 |               2359.9990 |                          1074.5000 |                         1086.5000 |
| high_cost_local_harm_d0.20 | fixed        |      2000 |                                0 |             1.0000 |           0.0070 |      309.4080 |               2397.7500 |                           888.2143 |                          900.2143 |
| high_cost_local_harm_d0.20 | predictable  |      2000 |                               41 |             0.9795 |           0.0110 |      180.3475 |               2355.2960 |                           754.4545 |                          766.4545 |
| high_cost_local_harm_d0.40 | fixed        |      2000 |                                0 |             1.0000 |           0.0235 |      328.5850 |               2394.2455 |                           945.6383 |                          957.4043 |
| high_cost_local_harm_d0.40 | predictable  |      2000 |                               24 |             0.9880 |           0.0525 |      193.5675 |               2348.3910 |                           698.3905 |                          710.3333 |
| high_cost_local_harm_d0.60 | fixed        |      2000 |                                0 |             1.0000 |           0.0650 |      337.2830 |               2386.8575 |                           986.0692 |                          997.9462 |
| high_cost_local_harm_d0.60 | predictable  |      2000 |                               32 |             0.9840 |           0.1595 |      202.5460 |               2301.9260 |                           778.4514 |                          790.4201 |

## Primary result

- Paired mean detection difference: 0.0314 (95% CI (0.026375, 0.03625)).
- Paired mean label difference: -131.25 (95% CI (-133.39325, -129.13694375)).
- Paired evaluator exposure-cost difference: -15.94 (95% CI (-17.655040999999997, -14.247827750000003)).
- Overall retention rule: True.

The evaluator exposure assumes immediate mitigation at the first alarm; it is a synthetic expected-cost accounting metric, not observed harm prevented. A pass supports only this frozen synthetic design and does not establish novelty or general superiority.
