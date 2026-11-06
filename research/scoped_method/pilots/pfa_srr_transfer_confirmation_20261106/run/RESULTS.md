# PFA-SR matched-host transfer confirmation results

**Status:** fresh synthetic confirmation of a published detector application, not independent
real-data validation and not a new-method claim. The cross-host development screen is not
pooled. This run uses 100 matched streams in each of five cells (4,500 policy rows).

Net cost = predictive loss + 0.05 × requested labels + 5 × deployment switches.
Intervals are paired t intervals over the 100 shared streams; the prespecified target-cell
gate requires at least 5 units of savings with the interval below zero against both the
corrected adapter and the same-host RMM. No multiplicity adjustment across target cells.

## All policy results

| Cell | Policy | Net [95% CI] | Difference vs never [95% CI] | Loss | Labels | Switches | Promotions | Rollbacks |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| PFA_confirm_persistent | `CONTROL_never_switch` | 490.45 [486.90, 494.00] | +0.00 [+0.00, +0.00] | 490.45 | 0.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_persistent | `xu_acquisition_only` | 390.09 [383.17, 397.01] | -100.36 [-108.17, -92.56] | 375.43 | 195.2 | 0.98 | 98/100 | 0.00 |
| PFA_confirm_persistent | `E_rb:gated_adaptive_range` | 388.89 [383.44, 394.34] | -101.56 [-108.13, -94.99] | 373.94 | 200.0 | 0.99 | 99/100 | 0.00 |
| PFA_confirm_persistent | `rmm:gated_deployment+RMM` | 385.99 [380.49, 391.49] | -104.46 [-111.29, -97.63] | 371.04 | 200.0 | 0.99 | 99/100 | 0.00 |
| PFA_confirm_persistent | `rmm:gated_adaptive_range+RMM` | 388.89 [383.44, 394.34] | -101.56 [-108.13, -94.99] | 373.94 | 200.0 | 0.99 | 99/100 | 0.00 |
| PFA_confirm_persistent | `E_swcert` | 404.95 [392.72, 417.19] | -85.50 [-98.06, -72.93] | 391.06 | 199.9 | 0.78 | 78/100 | 0.00 |
| PFA_confirm_persistent | `E_srrSR:gated_deployment` | 394.00 [386.94, 401.06] | -96.45 [-104.41, -88.49] | 367.90 | 200.0 | 3.22 | 100/100 | 1.27 |
| PFA_confirm_persistent | `PFA-SR:gated_deployment` | 371.75 [366.18, 377.32] | -118.70 [-125.50, -111.90] | 356.80 | 200.0 | 0.99 | 99/100 | 0.00 |
| PFA_confirm_persistent | `PFA-SR:gated_adaptive_range` | 369.70 [365.37, 374.03] | -120.75 [-126.44, -115.06] | 354.70 | 200.0 | 1.00 | 100/100 | 0.00 |
| PFA_confirm_near | `CONTROL_never_switch` | 432.65 [428.79, 436.51] | +0.00 [+0.00, +0.00] | 432.65 | 0.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_near | `xu_acquisition_only` | 435.21 [430.60, 439.82] | +2.56 [-0.83, +5.95] | 424.23 | 194.6 | 0.25 | 25/100 | 0.00 |
| PFA_confirm_near | `E_rb:gated_adaptive_range` | 435.86 [431.44, 440.28] | +3.21 [-0.12, +6.54] | 424.96 | 200.0 | 0.18 | 18/100 | 0.00 |
| PFA_confirm_near | `rmm:gated_deployment+RMM` | 435.97 [431.98, 439.96] | +3.32 [+0.23, +6.41] | 424.92 | 200.0 | 0.21 | 21/100 | 0.00 |
| PFA_confirm_near | `rmm:gated_adaptive_range+RMM` | 435.86 [431.44, 440.28] | +3.21 [-0.12, +6.54] | 424.96 | 200.0 | 0.18 | 18/100 | 0.00 |
| PFA_confirm_near | `E_swcert` | 438.23 [434.01, 442.45] | +5.58 [+2.35, +8.80] | 427.79 | 199.7 | 0.09 | 9/100 | 0.00 |
| PFA_confirm_near | `E_srrSR:gated_deployment` | 433.97 [429.76, 438.18] | +1.32 [-2.13, +4.77] | 405.07 | 200.0 | 3.78 | 100/100 | 1.70 |
| PFA_confirm_near | `PFA-SR:gated_deployment` | 434.10 [429.77, 438.43] | +1.45 [-2.39, +5.29] | 422.90 | 200.0 | 0.24 | 24/100 | 0.00 |
| PFA_confirm_near | `PFA-SR:gated_adaptive_range` | 431.34 [426.20, 436.48] | -1.31 [-5.73, +3.11] | 419.89 | 200.0 | 0.29 | 29/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `CONTROL_never_switch` | 450.40 [446.78, 454.02] | +0.00 [+0.00, +0.00] | 450.40 | 0.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `xu_acquisition_only` | 440.69 [435.86, 445.52] | -9.71 [-13.65, -5.78] | 433.39 | 96.9 | 0.49 | 49/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `E_rb:gated_adaptive_range` | 417.66 [411.16, 424.16] | -32.74 [-39.58, -25.90] | 409.16 | 100.0 | 0.70 | 70/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `rmm:gated_deployment+RMM` | 429.97 [423.43, 436.51] | -20.43 [-26.47, -14.39] | 421.87 | 100.0 | 0.62 | 62/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `rmm:gated_adaptive_range+RMM` | 417.66 [411.16, 424.16] | -32.74 [-39.58, -25.90] | 409.16 | 100.0 | 0.70 | 70/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `E_swcert` | 425.86 [418.32, 433.39] | -24.55 [-31.85, -17.24] | 418.46 | 99.9 | 0.48 | 48/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `E_srrSR:gated_deployment` | 375.04 [369.19, 380.89] | -75.36 [-81.81, -68.91] | 362.79 | 100.0 | 1.45 | 100/100 | 0.43 |
| PFA_confirm_delay_scarce@B100 | `PFA-SR:gated_deployment` | 409.83 [402.58, 417.08] | -40.57 [-47.93, -33.21] | 400.93 | 100.0 | 0.78 | 78/100 | 0.00 |
| PFA_confirm_delay_scarce@B100 | `PFA-SR:gated_adaptive_range` | 412.45 [404.69, 420.21] | -37.95 [-45.57, -30.33] | 404.05 | 100.0 | 0.68 | 68/100 | 0.00 |
| PFA_confirm_null | `CONTROL_never_switch` | 398.96 [395.43, 402.49] | +0.00 [+0.00, +0.00] | 398.96 | 0.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_null | `xu_acquisition_only` | 409.00 [405.43, 412.57] | +10.04 [+9.64, +10.44] | 399.14 | 195.2 | 0.02 | 2/100 | 0.00 |
| PFA_confirm_null | `E_rb:gated_adaptive_range` | 408.96 [405.43, 412.49] | +10.00 [+10.00, +10.00] | 398.96 | 200.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_null | `rmm:gated_deployment+RMM` | 408.96 [405.43, 412.49] | +10.00 [+10.00, +10.00] | 398.96 | 200.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_null | `rmm:gated_adaptive_range+RMM` | 408.96 [405.43, 412.49] | +10.00 [+10.00, +10.00] | 398.96 | 200.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_null | `E_swcert` | 408.97 [405.45, 412.49] | +10.01 [+9.97, +10.05] | 398.93 | 199.8 | 0.01 | 1/100 | 0.00 |
| PFA_confirm_null | `E_srrSR:gated_deployment` | 423.81 [419.95, 427.67] | +24.85 [+22.33, +27.37] | 398.66 | 200.0 | 3.03 | 100/100 | 1.40 |
| PFA_confirm_null | `PFA-SR:gated_deployment` | 408.96 [405.43, 412.49] | +10.00 [+10.00, +10.00] | 398.96 | 200.0 | 0.00 | 0/100 | 0.00 |
| PFA_confirm_null | `PFA-SR:gated_adaptive_range` | 409.01 [405.47, 412.55] | +10.05 [+9.95, +10.15] | 398.96 | 200.0 | 0.01 | 1/100 | 0.00 |
| F3_reversal_800 | `CONTROL_never_switch` | 341.22 [338.32, 344.12] | +0.00 [+0.00, +0.00] | 341.22 | 0.0 | 0.00 | 0/100 | 0.00 |
| F3_reversal_800 | `xu_acquisition_only` | 404.09 [397.17, 411.01] | +62.87 [+56.96, +68.78] | 387.55 | 195.8 | 1.35 | 81/100 | 0.54 |
| F3_reversal_800 | `E_rb:gated_adaptive_range` | 385.82 [379.81, 391.83] | +44.60 [+39.90, +49.30] | 367.57 | 200.0 | 1.65 | 85/100 | 0.80 |
| F3_reversal_800 | `rmm:gated_deployment+RMM` | 387.97 [381.34, 394.60] | +46.75 [+40.96, +52.54] | 370.82 | 200.0 | 1.43 | 79/100 | 0.64 |
| F3_reversal_800 | `rmm:gated_adaptive_range+RMM` | 396.55 [389.61, 403.49] | +55.33 [+49.61, +61.05] | 378.90 | 200.0 | 1.53 | 85/100 | 0.68 |
| F3_reversal_800 | `E_swcert` | 389.88 [383.14, 396.61] | +48.65 [+42.46, +54.85] | 374.49 | 199.7 | 1.08 | 70/100 | 0.38 |
| F3_reversal_800 | `E_srrSR:gated_deployment` | 333.35 [329.11, 337.59] | -7.87 [-11.69, -4.05] | 311.45 | 200.0 | 2.38 | 100/100 | 1.19 |
| F3_reversal_800 | `PFA-SR:gated_deployment` | 406.26 [400.69, 411.83] | +65.04 [+60.33, +69.75] | 389.51 | 200.0 | 1.35 | 93/100 | 0.42 |
| F3_reversal_800 | `PFA-SR:gated_adaptive_range` | 400.40 [395.20, 405.60] | +59.18 [+54.60, +63.76] | 383.30 | 200.0 | 1.42 | 92/100 | 0.50 |

## Frozen paired contrasts: PFA_confirm_persistent

| PFA-SR host | Comparator | Difference [95% CI] | Pass ≥5 savings? |
|---|---|---:|---|
| `PFA-SR:gated_deployment` | `xu_acquisition_only` | -18.34 [-25.57, -11.11] | yes |
| `PFA-SR:gated_deployment` | `rmm:gated_deployment+RMM` | -14.24 [-20.71, -7.77] | yes |
| `PFA-SR:gated_adaptive_range` | `xu_acquisition_only` | -20.39 [-27.33, -13.44] | yes |
| `PFA-SR:gated_adaptive_range` | `rmm:gated_adaptive_range+RMM` | -19.19 [-24.81, -13.57] | yes |

## Frozen paired contrasts: PFA_confirm_near

| PFA-SR host | Comparator | Difference [95% CI] | Pass ≥5 savings? |
|---|---|---:|---|
| `PFA-SR:gated_deployment` | `xu_acquisition_only` | -1.11 [-5.78, +3.56] | no |
| `PFA-SR:gated_deployment` | `rmm:gated_deployment+RMM` | -1.87 [-6.40, +2.66] | no |
| `PFA-SR:gated_adaptive_range` | `xu_acquisition_only` | -3.87 [-8.82, +1.08] | no |
| `PFA-SR:gated_adaptive_range` | `rmm:gated_adaptive_range+RMM` | -4.52 [-9.76, +0.72] | no |

## Frozen paired contrasts: PFA_confirm_delay_scarce@B100

| PFA-SR host | Comparator | Difference [95% CI] | Pass ≥5 savings? |
|---|---|---:|---|
| `PFA-SR:gated_deployment` | `xu_acquisition_only` | -30.86 [-38.63, -23.08] | yes |
| `PFA-SR:gated_deployment` | `rmm:gated_deployment+RMM` | -20.14 [-28.96, -11.32] | yes |
| `PFA-SR:gated_adaptive_range` | `xu_acquisition_only` | -28.24 [-36.34, -20.13] | yes |
| `PFA-SR:gated_adaptive_range` | `rmm:gated_adaptive_range+RMM` | -5.21 [-13.52, +3.10] | no |

## Decision

Strong persistent cell passed both comparator contrasts: `True`. Null screening gate passed: `True`.
Full frozen target-region gate across strong, near, delayed/scarce cells: `False`.

PFA-SR shows a reproducible, practically material synthetic gain in the prespecified
strong-persistent cell, with same-host comparisons and a null promotion rate within the
screening tolerance. It does not pass the full frozen persistent/near/delayed target
region: the weaker near-effect cell has no resolved savings, and the delayed/scarce cell
does not clear the same-host comparison. In the reversal stress cell, both PFA-SR hosts
are substantially more costly than never-switch; report this as an explicit scope limit.

The 2026 PFA-weighted e-SR is established prior art. Current evidence is an application
signal for the strong-persistent environment, not a novel detector contribution. It may
justify a frozen real-data replay only if the target can be defined without inspecting
evaluation outcomes and the PFA prior remains fixed.

Net-cost accounting maximum absolute residual: 0.

## Null promotion intervals

- `PFA-SR:gated_deployment`: 0/100 = 0.000, Wilson 95% CI [0.000, 0.037].
- `PFA-SR:gated_adaptive_range`: 1/100 = 0.010, Wilson 95% CI [0.002, 0.054].

## Provenance

- Source revision: `ff4fefbfa5c1099d1f05311f4e4b4010f7451c14`.
- Raw records SHA-256: `d2ef94baf68b3eb4fe6a117bd180d32ab2a94b69e7d55758dcbf903099e6a120`.
- Manifest SHA-256: `a8038074e072144f8a82555036c631ac6eb2dceddae3edab977df214d114e0c2`.
- Protocol SHA-256: `753458330a040030be12dfada6e3927d7e4785e1fc050efca809b92c1c698c84`.
- Detector SHA-256: `8bc614e2de4a1791b70f203add5555d21153f8f5f88b134937f749842e466815`.
- Runner SHA-256: `26da8bbd27fc49dcfd720481a832a0a9f0f3fd3815b2fb52d6980a25ce4c6aee`.
- Synthetic only; the oracle truth was evaluator-side and no real or locked holdout was opened.
