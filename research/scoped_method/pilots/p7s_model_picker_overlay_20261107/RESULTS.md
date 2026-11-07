# Frozen overlay pilot results

All 50 seeds in each registered cell and all seven methods are included. Paired 95% t intervals use the shared synthetic seeds. This is a development screen, not confirmation.

## Per-method outcomes

| Cell | Method | Net cost (95% CI) | Loss | Label cost | Switch cost | Labels | Switches | Promotions | Rollbacks | Median promotion t |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| F1_late_800 | P7s_MP_overlay | 377.94 [370.55, 385.32] | 364.78 | 9.65 | 3.50 | 193.1 | 0.70 | 35 | 0 | 1512.0 |
| F1_late_800 | P7s_MP_no_settled_throttle | 378.21 [370.89, 385.53] | 364.78 | 9.93 | 3.50 | 198.7 | 0.70 | 35 | 0 | 1512.0 |
| F1_late_800 | P7s_settled | 377.21 [370.28, 384.13] | 364.14 | 9.17 | 3.90 | 183.3 | 0.78 | 39 | 0 | 1537.0 |
| F1_late_800 | model_picker_adapter | 378.93 [368.87, 388.99] | 341.86 | 4.57 | 32.50 | 91.4 | 6.50 | 186 | 139 | 208.5 |
| F1_late_800 | D1 | 384.03 [378.24, 389.82] | 373.66 | 7.67 | 2.70 | 153.4 | 0.54 | 27 | 0 | 1551.0 |
| F1_late_800 | gated_adaptive_range+front | 400.76 [396.04, 405.49] | 391.86 | 8.90 | 0.00 | 178.1 | 0.00 | 0 | 0 | NA |
| F1_late_800 | CONTROL_never_switch | 391.86 [387.30, 396.42] | 391.86 | 0.00 | 0.00 | 0.0 | 0.00 | 0 | 0 | NA |
| F0_better | P7s_MP_overlay | 365.28 [356.02, 374.54] | 352.86 | 7.82 | 4.60 | 156.4 | 0.92 | 46 | 0 | 703.5 |
| F0_better | P7s_MP_no_settled_throttle | 366.38 [357.28, 375.48] | 352.86 | 8.92 | 4.60 | 178.4 | 0.92 | 46 | 0 | 703.5 |
| F0_better | P7s_settled | 375.43 [365.51, 385.34] | 363.50 | 7.73 | 4.20 | 154.6 | 0.84 | 42 | 0 | 835.5 |
| F0_better | model_picker_adapter | 325.15 [317.19, 333.11] | 306.88 | 3.87 | 14.40 | 77.4 | 2.88 | 97 | 47 | 130.0 |
| F0_better | D1 | 349.19 [342.27, 356.12] | 338.92 | 5.37 | 4.90 | 107.5 | 0.98 | 49 | 0 | 588.0 |
| F0_better | gated_adaptive_range+front | 356.38 [348.10, 364.65] | 345.28 | 6.70 | 4.40 | 134.0 | 0.88 | 44 | 0 | 640.5 |
| F0_better | CONTROL_never_switch | 417.76 [411.74, 423.78] | 417.76 | 0.00 | 0.00 | 0.0 | 0.00 | 0 | 0 | NA |
| F3_reversal_800 | P7s_MP_overlay | 398.99 [389.95, 408.03] | 382.14 | 9.95 | 6.90 | 199.0 | 1.38 | 39 | 30 | 530.0 |
| F3_reversal_800 | P7s_MP_no_settled_throttle | 392.53 [384.09, 400.97] | 375.24 | 9.99 | 7.30 | 199.7 | 1.46 | 39 | 34 | 530.0 |
| F3_reversal_800 | P7s_settled | 395.50 [385.80, 405.21] | 379.14 | 9.76 | 6.60 | 195.2 | 1.32 | 36 | 30 | 567.0 |
| F3_reversal_800 | model_picker_adapter | 384.02 [377.72, 390.33] | 361.06 | 4.26 | 18.70 | 85.3 | 3.74 | 99 | 88 | 108.0 |
| F3_reversal_800 | D1 | 411.93 [404.50, 419.37] | 403.78 | 3.55 | 4.60 | 71.1 | 0.92 | 46 | 0 | 368.0 |
| F3_reversal_800 | gated_adaptive_range+front | 421.79 [416.90, 426.68] | 412.10 | 4.69 | 5.00 | 93.8 | 1.00 | 50 | 0 | 423.5 |
| F3_reversal_800 | CONTROL_never_switch | 342.56 [338.33, 346.79] | 342.56 | 0.00 | 0.00 | 0.0 | 0.00 | 0 | 0 | NA |
| F0_null | P7s_MP_overlay | 369.37 [365.28, 373.45] | 359.28 | 9.98 | 0.10 | 199.7 | 0.02 | 1 | 0 | 1088.0 |
| F0_null | P7s_MP_no_settled_throttle | 369.38 [365.29, 373.47] | 359.28 | 10.00 | 0.10 | 200.0 | 0.02 | 1 | 0 | 1088.0 |
| F0_null | P7s_settled | 369.33 [365.23, 373.43] | 359.34 | 9.89 | 0.10 | 197.8 | 0.02 | 1 | 0 | 1117.0 |
| F0_null | model_picker_adapter | 395.22 [385.97, 404.48] | 359.92 | 4.60 | 30.70 | 92.0 | 6.14 | 167 | 140 | 148.0 |
| F0_null | D1 | 368.35 [364.03, 372.68] | 359.80 | 8.35 | 0.20 | 167.1 | 0.04 | 2 | 0 | 340.5 |
| F0_null | gated_adaptive_range+front | 369.40 [365.30, 373.50] | 359.40 | 10.00 | 0.00 | 200.0 | 0.00 | 0 | 0 | NA |
| F0_null | CONTROL_never_switch | 359.40 [355.30, 363.50] | 359.40 | 0.00 | 0.00 | 0.0 | 0.00 | 0 | 0 | NA |

## Frozen development rule

- F1_late_800 candidate minus model_picker_adapter: -1.00 [-10.53, 8.54]; requires mean <= -5 and upper CI < 0: **FAIL**.
- F1_late_800 candidate minus P7s_settled: 0.73 [-2.78, 4.24]; requires mean <= -5 and upper CI < 0: **FAIL**.
- F3_reversal_800 excess versus never-switch: 56.43 [47.69, 65.17]; requires mean <= 5: **FAIL**.
- F0_null excess versus never-switch: 9.96 [9.89, 10.04]; requires mean <= 5: **FAIL**.
- F0_null candidate promotions: 1/50; requires <=5/50: **PASS**.

**Development gate: FAIL.** A pass permits only separate prior-art review and frozen independent evaluation.

## Audit notes

The runner aborts on a refused request, a budget exceedance, or any mismatch between the combined issue propensity and CertPlus's frozen propensity. The compressed event trace records every synthetic event and every method; the manifest contains source and output hashes.
