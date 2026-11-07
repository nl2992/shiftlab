# Publisher-stratified MN-DS replay results

**Feedback:** simulated 24-hour release delay. All figures are retrospective replay results.

| Policy | Net / 1,000 | Error | Labels | Label cost | Switches | Switch cost | Promotions | Rollbacks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| CONTROL_never_switch | 338.47 | 1033 | 0 | 0.00 | 0 | 0.00 | 0 | 0 |
| publisher_stratified_promotion_rollback | 340.10 | 1033 | 100 | 5.00 | 0 | 0.00 | 0 | 0 |
| E_swcert | 341.73 | 1033 | 199 | 9.95 | 0 | 0.00 | 0 | 0 |
| gated_adaptive_range | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| discern_style | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| SMCS+retain-incumbent | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| xu_acquisition_only | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| PFA-SR:gated_adaptive_range | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| rmm:gated_adaptive_range+RMM | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| E_rb:gated_adaptive_range | 341.74 | 1033 | 200 | 10.00 | 0 | 0.00 | 0 | 0 |
| validation_selected_source_static | 342.40 | 1040 | 0 | 0.00 | 1 | 5.00 | 1 | 0 |
| model_selector_causal | 351.23 | 1042 | 199 | 9.95 | 4 | 20.00 | 2 | 2 |
| cams_adapter | 353.57 | 1058 | 22 | 1.10 | 4 | 20.00 | 2 | 2 |
| model_picker_adapter | 354.93 | 1077 | 25 | 1.25 | 1 | 5.00 | 1 | 0 |
| economic_replacement | 357.47 | 1076 | 200 | 10.00 | 1 | 5.00 | 1 | 0 |
| gong_zhang_paid_obs | 362.06 | 1055 | 200 | 10.00 | 8 | 40.00 | 4 | 4 |
| qiu_delayed_movement | 364.01 | 1071 | 199 | 9.95 | 6 | 30.00 | 3 | 3 |

## Candidate paired cost contrasts

| Reference | Primary | Candidate − reference / 1,000 | 95% block interval | registered interval | Level | publisher-cluster interval |
|---|---:|---:|---:|---:|---:|---:|
| CONTROL_never_switch | False | 1.64 | [0.87, 2.18] | [0.87, 2.18] | 95.0% | [0.48, 2.78] |
| gated_adaptive_range | False | -1.64 | [-2.64, -0.97] | [-2.64, -0.97] | 95.0% | [-3.05, -0.30] |
| discern_style | False | -1.64 | [-2.74, -0.92] | [-2.74, -0.92] | 95.0% | [-2.75, -0.59] |
| SMCS+retain-incumbent | False | -1.64 | [-2.56, -1.03] | [-2.56, -1.03] | 95.0% | [-2.97, -0.29] |
| xu_acquisition_only | False | -1.64 | [-2.74, -0.97] | [-2.74, -0.97] | 95.0% | [-2.85, -0.43] |
| PFA-SR:gated_adaptive_range | True | -1.64 | [-2.92, -0.98] | [-3.29, -0.75] | 99.0% | [-2.90, -0.33] |
| rmm:gated_adaptive_range+RMM | True | -1.64 | [-2.77, -1.03] | [-3.03, -0.85] | 99.0% | [-2.90, -0.37] |
| E_rb:gated_adaptive_range | True | -1.64 | [-2.77, -1.03] | [-3.03, -0.85] | 99.0% | [-2.90, -0.37] |
| E_swcert | True | -1.62 | [-2.65, -0.92] | [-2.88, -0.70] | 99.0% | [-2.86, -0.40] |
| qiu_delayed_movement | False | -23.90 | [-41.33, -10.47] | [-41.33, -10.47] | 95.0% | [-36.18, -11.17] |
| gong_zhang_paid_obs | False | -21.95 | [-38.13, -9.58] | [-38.13, -9.58] | 95.0% | [-35.49, -7.98] |
| cams_adapter | False | -13.47 | [-32.86, -1.00] | [-32.86, -1.00] | 95.0% | [-25.05, -2.20] |
| model_picker_adapter | False | -14.83 | [-26.85, -2.83] | [-26.85, -2.83] | 95.0% | [-29.21, 0.15] |
| model_selector_causal | False | -11.12 | [-25.34, -1.57] | [-25.34, -1.57] | 95.0% | [-19.89, -4.27] |
| economic_replacement | False | -17.37 | [-29.44, -4.86] | [-29.44, -4.86] | 95.0% | [-31.29, -3.29] |
| validation_selected_source_static | True | -2.29 | [-4.80, 2.74] | [-5.75, 3.62] | 99.0% | [-10.11, 2.10] |

## Named publisher contrasts vs validation-selected static

| Publisher | Difference / 1,000 | 95% 7-day interval |
|---|---:|---:|
| eveningstandard | 6.79 | [2.99, 12.50] |
| sputnik | -70.72 | [-116.46, 29.93] |
| tass | 9.54 | [6.11, 13.74] |

The publisher-stratified gate is a standard composition, not a new statistical test. Its e-process interpretation is not asserted for this serial source without a matching conditional-mean assumption. Source-level cost results are descriptive; a single dataset does not establish external generalization.
