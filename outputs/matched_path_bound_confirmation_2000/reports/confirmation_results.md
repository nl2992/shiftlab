# Matched-path selected-schedule harm confirmation

- Streams per dose and bound: 2000; schedule: `periodic_q080`; delay: 12; horizon: 2400; device: cuda.
- Independent null calibration: PASS.
- Frozen retention rule: PASS.
- Fixed/eventwise paths were verified identical for labels, registered prefix, and processed events.
- No figure was generated; the prespecified numeric result and stream metrics are provided.

## Primary result

```json
{
  "primary_estimand": "equal-weight macro over four doses of paired eventwise-minus-fixed post-onset detection under the frozen periodic q={0.05,0.80} schedule",
  "paired_mean_detection_difference": 0.054125,
  "paired_bootstrap_95_ci_detection": [
    0.045875,
    0.0625
  ],
  "detection_gate_lower_bound": 0.02,
  "passes_detection_gate": true,
  "paired_mean_label_difference": 0.0,
  "paired_bootstrap_95_ci_labels": [
    0.0,
    0.0
  ],
  "passes_no_extra_labels_gate": true,
  "paired_mean_expected_exposure_difference": -16.618646666666667,
  "paired_bootstrap_95_ci_expected_exposure": [
    -19.573534999999996,
    -13.770513333333335
  ],
  "bootstrap_replicates": 10000,
  "bootstrap_seed_root": 28703028,
  "passes_calibration_gate": true,
  "retention_rule_passes": true,
  "independent_calibration_sha256": "7e9ecd2c0ca1433f202af6ba4004095f0de0aaadfa99d853c7c293754ddb988d",
  "independent_calibration_path": "outputs\\matched_path_bound_calibration_2000\\metrics\\calibration.csv"
}
```

## Dose results

| scenario                     |   effect |   fixed_detection |   eventwise_detection |   paired_detection_difference |   fixed_mean_labels |   eventwise_mean_labels |   paired_label_difference |   fixed_mean_expected_exposure |   eventwise_mean_expected_exposure |   paired_expected_exposure_difference |   eventwise_pre_onset_alarms |
|:-----------------------------|---------:|------------------:|----------------------:|------------------------------:|--------------------:|------------------------:|--------------------------:|-------------------------------:|-----------------------------------:|--------------------------------------:|-----------------------------:|
| markov_volatility_harm_d0.04 |  0.04000 |           0.00750 |               0.00550 |                      -0.00200 |           475.05650 |               475.05650 |                   0.00000 |                       46.53511 |                           45.77779 |                              -0.75732 |                           41 |
| markov_volatility_harm_d0.20 |  0.20000 |           0.01150 |               0.01700 |                       0.00550 |           475.05650 |               475.05650 |                   0.00000 |                      232.40467 |                          227.79407 |                              -4.61060 |                           41 |
| markov_volatility_harm_d0.40 |  0.40000 |           0.02700 |               0.07550 |                       0.04850 |           475.05650 |               475.05650 |                   0.00000 |                      462.36573 |                          447.75387 |                             -14.61187 |                           41 |
| markov_volatility_harm_d0.60 |  0.60000 |           0.05450 |               0.21900 |                       0.16450 |           475.05650 |               475.05650 |                   0.00000 |                      688.05980 |                          641.56500 |                             -46.49480 |                           41 |
