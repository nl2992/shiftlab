# Delayed Markov harm confirmation

- Streams per harm dose and arm: 2000; delay: 12; horizon: 2400; device: cuda.
- Independent null calibration gate: PASS.
- Frozen retention rule: PASS.
- This is confirmation only for the frozen Markov-volatility process and deterministic outcome-independent 12-event feedback delay.
- Evaluator expected exposure conditions on latent state and assumes mitigation at escalation; it is not observed prevented loss.
- No figure was generated; this confirmation is reported as a numeric table and Parquet stream file.

## Primary result

```json
{
  "primary_estimand": "equal-weight mean over four Markov harm doses of paired post-onset detection difference, predictable minus fixed, 12-event delay",
  "paired_mean_detection_difference": 0.06025,
  "paired_bootstrap_95_ci_detection": [
    0.05325,
    0.0675
  ],
  "detection_gate_lower_bound": 0.02,
  "passes_detection_gate": true,
  "paired_mean_label_difference": -130.263875,
  "paired_bootstrap_95_ci_labels": [
    -134.223915625,
    -126.376865625
  ],
  "passes_no_extra_labels_gate": true,
  "paired_mean_expected_exposure_difference": -22.701736666666665,
  "paired_bootstrap_95_ci_expected_exposure": [
    -25.529343416666666,
    -19.953330833333332
  ],
  "bootstrap_replicates": 10000,
  "bootstrap_seed_root": 28385028,
  "passes_calibration_gate": true,
  "retention_rule_passes": true,
  "independent_calibration_summary": "outputs\\delayed_markov_predictable_calibration_2000\\metrics\\calibration.csv",
  "independent_calibration_sha256": "9b6ca285a18b68c5f254746937dbf5c9b4004a7e32a8069463d6d1dfa95a045d"
}
```

## Dose results

| scenario                     |   effect |   fixed_detection |   predictable_detection |   paired_detection_difference |   fixed_mean_labels |   predictable_mean_labels |   paired_label_difference |   fixed_mean_expected_exposure |   predictable_mean_expected_exposure |   paired_expected_exposure_difference |   predictable_pre_onset_alarms |
|:-----------------------------|---------:|------------------:|------------------------:|------------------------------:|--------------------:|--------------------------:|--------------------------:|-------------------------------:|-------------------------------------:|--------------------------------------:|-------------------------------:|
| markov_volatility_harm_d0.04 |  0.04000 |           0.00000 |                 0.00650 |                       0.00650 |           305.86450 |                 181.09600 |                -124.76850 |                       47.98579 |                             47.08051 |                              -0.90528 |                             31 |
| markov_volatility_harm_d0.20 |  0.20000 |           0.00100 |                 0.02000 |                       0.01900 |           317.43850 |                 188.98150 |                -128.45700 |                      239.90700 |                            233.98433 |                              -5.92267 |                             31 |
| markov_volatility_harm_d0.40 |  0.40000 |           0.01600 |                 0.07900 |                       0.06300 |           333.78450 |                 201.80050 |                -131.98400 |                      478.69840 |                            457.41200 |                             -21.28640 |                             31 |
| markov_volatility_harm_d0.60 |  0.60000 |           0.05700 |                 0.20950 |                       0.15250 |           348.97850 |                 213.13250 |                -135.84600 |                      712.41680 |                            649.72420 |                             -62.69260 |                             31 |

