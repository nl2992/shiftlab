# Fresh synthetic F8 follow-up results

Paired bootstrap intervals resample the 100 fresh synthetic streams. The candidate is a fixed deployment control, not a learned method.

## F0_null

Candidate minus CAMS: -59.931; paired percentile 95% CI [-68.487, -51.655]. Adverse-cell diagnostic only; no success gate is applied.

| Method | Net cost | Loss | Labels | Switches | Promotions |
|---|---:|---:|---:|---:|---:|
| CONTROL_never_switch | 359.330 | 359.330 | 0.0 | 0.00 | 0 |
| fixed_challenger | 363.310 | 358.310 | 0.0 | 1.00 | 100 |
| xu_acquisition_only | 369.268 | 359.390 | 195.6 | 0.02 | 2 |
| gated_deployment | 369.310 | 359.330 | 199.6 | 0.00 | 0 |
| SMCS+retain-incumbent | 369.447 | 359.370 | 199.6 | 0.02 | 2 |
| qiu_delayed_movement | 393.553 | 359.980 | 199.5 | 4.72 | 97 |
| model_selector_causal | 397.619 | 359.030 | 199.8 | 5.72 | 99 |
| model_picker_adapter | 400.986 | 358.090 | 95.9 | 7.62 | 96 |
| gong_zhang_paid_obs | 403.658 | 358.630 | 199.6 | 7.01 | 99 |
| online_llm_picker | 410.303 | 360.130 | 95.5 | 9.08 | 100 |
| cams_adapter | 423.241 | 358.670 | 193.4 | 10.98 | 99 |

## F3_reversal_800

Candidate minus CAMS: -11.499; paired percentile 95% CI [-16.290, -6.769]. Adverse-cell diagnostic only; no success gate is applied.

| Method | Net cost | Loss | Labels | Switches | Promotions |
|---|---:|---:|---:|---:|---:|
| CONTROL_never_switch | 344.770 | 344.770 | 0.0 | 0.00 | 0 |
| gong_zhang_paid_obs | 349.579 | 324.990 | 199.8 | 2.92 | 100 |
| qiu_delayed_movement | 352.387 | 331.800 | 199.7 | 2.12 | 100 |
| gated_deployment | 359.363 | 349.440 | 193.5 | 0.05 | 5 |
| fixed_challenger | 384.220 | 379.220 | 0.0 | 1.00 | 100 |
| online_llm_picker | 385.024 | 357.920 | 84.1 | 4.58 | 100 |
| model_selector_causal | 385.903 | 361.260 | 199.9 | 2.93 | 100 |
| model_picker_adapter | 386.423 | 365.640 | 85.7 | 3.30 | 100 |
| cams_adapter | 395.720 | 364.440 | 191.6 | 4.34 | 100 |
| xu_acquisition_only | 406.701 | 390.350 | 196.0 | 1.31 | 77 |
| SMCS+retain-incumbent | 416.498 | 402.410 | 199.8 | 0.82 | 82 |

## F8_rare_better

Candidate minus CAMS: -6.174; paired percentile 95% CI [-6.857, -5.544]. Primary F8 gate pass: True.

| Method | Net cost | Loss | Labels | Switches | Promotions |
|---|---:|---:|---:|---:|---:|
| fixed_challenger | 207.990 | 202.990 | 0.0 | 1.00 | 100 |
| cams_adapter | 214.164 | 206.900 | 29.3 | 1.16 | 100 |
| model_selector_causal | 214.189 | 206.150 | 58.8 | 1.02 | 100 |
| online_llm_picker | 214.639 | 206.800 | 36.8 | 1.20 | 100 |
| gong_zhang_paid_obs | 215.882 | 207.860 | 58.4 | 1.02 | 100 |
| qiu_delayed_movement | 215.935 | 207.810 | 58.5 | 1.04 | 100 |
| model_picker_adapter | 216.345 | 209.540 | 14.1 | 1.22 | 100 |
| SMCS+retain-incumbent | 224.174 | 216.300 | 58.5 | 0.99 | 99 |
| xu_acquisition_only | 230.053 | 222.170 | 58.6 | 0.99 | 99 |
| gated_deployment | 232.299 | 225.950 | 28.0 | 0.99 | 99 |
| CONTROL_never_switch | 249.890 | 249.890 | 0.0 | 0.00 | 0 |

## Interpretation

These results evaluate a known static control on simulator-generated streams. The F8 cell is the only primary gate; null and reversal cells are adverse scope diagnostics. The apparent null-cell cost difference is not a calibrated type-I error estimate. Results do not establish a novel method or independent real-world transfer.
