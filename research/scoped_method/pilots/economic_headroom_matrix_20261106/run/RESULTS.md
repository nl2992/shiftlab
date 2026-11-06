# Economic headroom matrix — development results

**Status:** exploratory development pilot, not confirmation. Protocol was committed as
`89e5d060` before the run. Thirty matched synthetic streams per cell; 1,350 policy rows.

Net cost is predictive loss + 0.05 × requested labels + 5 × deployment switches.
Intervals are two-sided paired t intervals over 30 shared streams. The prespecified primary
contrasts and decision rule are in `protocol.md`; no multiplicity correction is applied to
these screening intervals.

## Primary frozen contrasts

| Cell | Policy | Reference | Policy net cost | Paired difference [95% CI] | Loss | Labels | Switches | Promote | Mean first promotion | Mean rollbacks |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| F0_better | `CONTROL_never_switch` | `xu_acquisition_only` | 425.07 [416.41, 433.72] | +54.15 [+42.01, +66.29] | 425.07 | 0.0 | 0.00 | 0/30 | — | 0.00 |
| F0_better | `gated_adaptive_range` | `xu_acquisition_only` | 417.55 [402.81, 432.29] | +46.63 [+33.11, +60.16] | 407.23 | 169.7 | 0.37 | 11/30 | 1139.4545454545455 | 0.00 |
| F0_better | `discern_style` | `xu_acquisition_only` | 435.05 [426.40, 443.71] | +64.13 [+51.99, +76.28] | 425.07 | 199.7 | 0.00 | 0/30 | — | 0.00 |
| F0_better | `xu_acquisition_only` | `xu_acquisition_only` | 370.92 [358.79, 383.05] | +0.00 [+0.00, +0.00] | 356.30 | 195.7 | 0.97 | 29/30 | 868.7586206896551 | 0.00 |
| F0_better | `E_rb:gated_adaptive_range` | `xu_acquisition_only` | 369.50 [359.63, 379.37] | -1.42 [-13.88, +11.04] | 354.67 | 200.0 | 0.97 | 29/30 | 826 | 0.00 |
| F0_better | `rmm:gated_adaptive_range+RMM` | `xu_acquisition_only` | 369.50 [359.63, 379.37] | -1.42 [-13.88, +11.04] | 354.67 | 200.0 | 0.97 | 29/30 | 826 | 0.00 |
| F0_better | `E_swcert` | `xu_acquisition_only` | 369.02 [355.06, 382.98] | -1.90 [-16.16, +12.36] | 355.20 | 199.7 | 0.77 | 23/30 | 558.0869565217391 | 0.00 |
| F0_better | `economic_replacement` | `xu_acquisition_only` | 332.55 [325.46, 339.64] | -38.37 [-48.06, -28.68] | 317.57 | 199.7 | 1.00 | 30/30 | 260.56666666666666 | 0.00 |
| F0_better | `E_srrSR:gated_deployment` | `xu_acquisition_only` | 379.47 [365.34, 393.59] | +8.55 [-4.31, +21.41] | 351.30 | 200.0 | 3.63 | 30/30 | 238.96666666666667 | 1.57 |
| F3_reversal_1200 | `CONTROL_never_switch` | `CONTROL_never_switch` | 378.83 [370.91, 386.76] | +0.00 [+0.00, +0.00] | 378.83 | 0.0 | 0.00 | 0/30 | — | 0.00 |
| F3_reversal_1200 | `gated_adaptive_range` | `CONTROL_never_switch` | 412.33 [401.35, 423.30] | +33.49 [+23.59, +43.40] | 402.67 | 126.5 | 0.67 | 20/30 | 895.55 | 0.00 |
| F3_reversal_1200 | `discern_style` | `CONTROL_never_switch` | 388.81 [380.89, 396.74] | +9.98 [+9.97, +10.00] | 378.83 | 199.6 | 0.00 | 0/30 | — | 0.00 |
| F3_reversal_1200 | `xu_acquisition_only` | `CONTROL_never_switch` | 408.63 [399.79, 417.48] | +29.80 [+19.78, +39.82] | 394.20 | 195.3 | 0.93 | 26/30 | 677.1923076923077 | 0.07 |
| F3_reversal_1200 | `E_rb:gated_adaptive_range` | `CONTROL_never_switch` | 404.47 [396.61, 412.33] | +25.63 [+16.91, +34.36] | 386.97 | 200.0 | 1.50 | 29/30 | 687.5172413793103 | 0.53 |
| F3_reversal_1200 | `rmm:gated_adaptive_range+RMM` | `CONTROL_never_switch` | 410.77 [402.13, 419.41] | +31.93 [+21.99, +41.87] | 394.60 | 200.0 | 1.23 | 29/30 | 687.5172413793103 | 0.27 |
| F3_reversal_1200 | `E_swcert` | `CONTROL_never_switch` | 402.34 [392.21, 412.48] | +23.51 [+14.34, +32.68] | 387.03 | 199.6 | 1.07 | 23/30 | 635.5652173913044 | 0.30 |
| F3_reversal_1200 | `economic_replacement` | `CONTROL_never_switch` | 383.00 [375.28, 390.73] | +4.17 [-3.44, +11.78] | 368.03 | 199.4 | 1.00 | 30/30 | 256.26666666666665 | 0.00 |
| F3_reversal_1200 | `E_srrSR:gated_deployment` | `CONTROL_never_switch` | 360.00 [349.26, 370.74] | -18.83 [-30.96, -6.71] | 332.00 | 200.0 | 3.60 | 30/30 | 212.76666666666668 | 1.80 |
| F3_reversal_800 | `CONTROL_never_switch` | `CONTROL_never_switch` | 346.30 [339.79, 352.81] | +0.00 [+0.00, +0.00] | 346.30 | 0.0 | 0.00 | 0/30 | — | 0.00 |
| F3_reversal_800 | `gated_adaptive_range` | `CONTROL_never_switch` | 386.26 [368.97, 403.55] | +39.96 [+25.58, +54.34] | 376.97 | 145.8 | 0.40 | 12/30 | 655.9166666666666 | 0.00 |
| F3_reversal_800 | `discern_style` | `CONTROL_never_switch` | 356.28 [349.78, 362.79] | +9.98 [+9.97, +10.00] | 346.30 | 199.7 | 0.00 | 0/30 | — | 0.00 |
| F3_reversal_800 | `xu_acquisition_only` | `CONTROL_never_switch` | 403.03 [389.69, 416.37] | +56.73 [+45.27, +68.19] | 387.63 | 194.6 | 1.13 | 23/30 | 481 | 0.37 |
| F3_reversal_800 | `E_rb:gated_adaptive_range` | `CONTROL_never_switch` | 386.40 [376.82, 395.98] | +40.10 [+32.63, +47.57] | 367.73 | 200.0 | 1.73 | 27/30 | 525.074074074074 | 0.83 |
| F3_reversal_800 | `rmm:gated_adaptive_range+RMM` | `CONTROL_never_switch` | 396.67 [386.43, 406.91] | +50.37 [+40.96, +59.77] | 378.50 | 200.0 | 1.63 | 27/30 | 525.074074074074 | 0.73 |
| F3_reversal_800 | `E_swcert` | `CONTROL_never_switch` | 390.56 [377.97, 403.14] | +44.25 [+33.90, +54.61] | 374.57 | 199.8 | 1.20 | 23/30 | 400.8695652173913 | 0.43 |
| F3_reversal_800 | `economic_replacement` | `CONTROL_never_switch` | 410.62 [404.66, 416.57] | +64.32 [+57.66, +70.97] | 395.63 | 199.7 | 1.00 | 30/30 | 249.53333333333333 | 0.00 |
| F3_reversal_800 | `E_srrSR:gated_deployment` | `CONTROL_never_switch` | 341.00 [331.43, 350.57] | -5.30 [-13.40, +2.80] | 317.67 | 200.0 | 2.67 | 30/30 | 225.4 | 1.33 |
| F0_null | `CONTROL_never_switch` | `CONTROL_never_switch` | 361.50 [355.32, 367.68] | +0.00 [+0.00, +0.00] | 361.50 | 0.0 | 0.00 | 0/30 | — | 0.00 |
| F0_null | `gated_adaptive_range` | `CONTROL_never_switch` | 371.49 [365.31, 377.67] | +9.99 [+9.99, +10.00] | 361.50 | 199.9 | 0.00 | 0/30 | — | 0.00 |
| F0_null | `discern_style` | `CONTROL_never_switch` | 371.49 [365.31, 377.67] | +9.99 [+9.98, +10.00] | 361.50 | 199.8 | 0.00 | 0/30 | — | 0.00 |
| F0_null | `xu_acquisition_only` | `CONTROL_never_switch` | 371.34 [365.10, 377.58] | +9.84 [+9.67, +10.01] | 361.40 | 195.5 | 0.03 | 1/30 | 1011 | 0.00 |
| F0_null | `E_rb:gated_adaptive_range` | `CONTROL_never_switch` | 371.90 [365.75, 378.05] | +10.40 [+9.58, +11.22] | 361.73 | 200.0 | 0.03 | 1/30 | 1402 | 0.00 |
| F0_null | `rmm:gated_adaptive_range+RMM` | `CONTROL_never_switch` | 371.90 [365.75, 378.05] | +10.40 [+9.58, +11.22] | 361.73 | 200.0 | 0.03 | 1/30 | 1402 | 0.00 |
| F0_null | `E_swcert` | `CONTROL_never_switch` | 371.49 [365.31, 377.67] | +9.99 [+9.98, +10.00] | 361.50 | 199.8 | 0.00 | 0/30 | — | 0.00 |
| F0_null | `economic_replacement` | `CONTROL_never_switch` | 373.70 [367.62, 379.77] | +12.20 [+7.24, +17.15] | 359.03 | 199.9 | 0.93 | 28/30 | 324.35714285714283 | 0.00 |
| F0_null | `E_srrSR:gated_deployment` | `CONTROL_never_switch` | 387.10 [378.92, 395.28] | +25.60 [+21.28, +29.92] | 360.93 | 200.0 | 3.23 | 30/30 | 403.8666666666667 | 1.53 |
| F6_delay400_better@B100 | `CONTROL_never_switch` | `xu_acquisition_only` | 419.63 [411.66, 427.61] | +3.32 [-2.22, +8.87] | 419.63 | 0.0 | 0.00 | 0/30 | — | 0.00 |
| F6_delay400_better@B100 | `gated_adaptive_range` | `xu_acquisition_only` | 424.63 [416.65, 432.61] | +8.32 [+2.78, +13.87] | 419.63 | 100.0 | 0.00 | 0/30 | — | 0.00 |
| F6_delay400_better@B100 | `discern_style` | `xu_acquisition_only` | 424.63 [416.65, 432.61] | +8.32 [+2.78, +13.86] | 419.63 | 99.9 | 0.00 | 0/30 | — | 0.00 |
| F6_delay400_better@B100 | `xu_acquisition_only` | `xu_acquisition_only` | 416.31 [406.83, 425.79] | +0.00 [+0.00, +0.00] | 409.10 | 97.5 | 0.47 | 14/30 | 1646.5714285714287 | 0.00 |
| F6_delay400_better@B100 | `E_rb:gated_adaptive_range` | `xu_acquisition_only` | 406.70 [397.74, 415.66] | -9.61 [-20.68, +1.46] | 399.03 | 100.0 | 0.53 | 16/30 | 1378.9375 | 0.00 |
| F6_delay400_better@B100 | `rmm:gated_adaptive_range+RMM` | `xu_acquisition_only` | 406.70 [397.74, 415.66] | -9.61 [-20.68, +1.46] | 399.03 | 100.0 | 0.53 | 16/30 | 1378.9375 | 0.00 |
| F6_delay400_better@B100 | `E_swcert` | `xu_acquisition_only` | 406.93 [391.81, 422.06] | -9.38 [-21.19, +2.43] | 400.10 | 100.0 | 0.37 | 11/30 | 1170.6363636363637 | 0.00 |
| F6_delay400_better@B100 | `economic_replacement` | `xu_acquisition_only` | 351.83 [344.38, 359.28] | -64.48 [-71.38, -57.58] | 341.83 | 99.9 | 1.00 | 30/30 | 740.9333333333333 | 0.00 |
| F6_delay400_better@B100 | `E_srrSR:gated_deployment` | `xu_acquisition_only` | 357.73 [348.49, 366.98] | -58.58 [-67.87, -49.28] | 345.73 | 100.0 | 1.40 | 30/30 | 672.4 | 0.40 |

## Interpretation and decision

The primary development gate requires ≥5 units of paired savings with the full interval
below zero on a worthwhile cell and ≤5 units mean harm to never-switch in both the
unfavorable reversal and null cells. No policy met that gate. `economic_replacement` and
`E_srrSR:gated_deployment` were excluded from equal-safety headroom because their prior
stated error controls are not probability-of-any-false-promotion controls; see null rates
below. The E-SR's ARL guarantee is not equivalent to an anytime false-alarm guarantee.

The two reversal cells share a ±0.08/event advantage schedule. Expected cumulative gain
before switch expenditure is +32 in `F3_reversal_1200` and −32 in `F3_reversal_800`;
thus the former can repay two 5-unit switches while the latter cannot. These are
evaluator-side design facts, not information supplied to methods.

Cost identity maximum absolute residual: 0.

**Decision: `BENCHMARK_ONLY`.** This pilot identifies a real economic trade-off and a
promising favorable-reversal cell for future work, but no frozen, safety-qualified
implemented comparator combination met the development gate. The large apparent gains
from the economic selector and E-SR come with null promotion rates that rule out an
equal-safety claim at this sample size. There is no basis for a novel-method claim or
real-data confirmation yet.

### Smallest next step

Before proposing a new mechanism, prospectively calibrate the existing conventional
two-sided restart detector to a probability-of-any-false-promotion contract on a
correctly specified null, then repeat only the two reversal cells plus the null and
compare against `E_swcert`, RMM, and never-switch. If the calibrated conventional method
closes the economic gap, stop the novelty search.

## Provenance

- Runner manifest source revision: `89e5d060cdf427d44774ab0aeda8bd990bafdb6e`.
- Raw records SHA-256: `da0624f02e7d1d103cc2278a09caa25d1949fa4f515affa8cd006fee4aef4aff`.
- Manifest SHA-256: `5e2459ba1a96fa4d61c5bcfe6fb7d7ec43529032500cc16e0d9330d8974ba9b6`.
- Experiment script SHA-256: `c61785a87f5e86d2ec7cac4d8f4f4b0545b6ae7f21764e6775b405da8634c177`.
- Analysis script SHA-256: `adb432f7585b11310d84b6878cd24bc667377c02388ad54c86bfa8f0fa5f9119`.
- Protocol SHA-256: `b7220b624cf55ae1b4f4c480bf2efd0ae89d1589cd82281391385ba530b29942`.
- Synthetic only; no real data, confirmation holdout, or oracle policy access.
