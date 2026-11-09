# WP1 late-improvement metric-specific leaderboard

**Scope:** 10 retrospective episodes from 5 source clusters; 3 paired seeds per episode; 34 policies.
The selected strongest certified comparator is `gated_adaptive_range+front`. It is selected on the same episodes used for these descriptive rankings.

These are within-stratum rankings, not a global ordering across Tracks E/R/V. Intervals are 95% percentile bootstraps over source clusters (10,000 resamples). Raw streams and class labels were development-exposed; episode classes are retrospective, not causal change labels.

## Metric-specific rankings

### Mean net cost J per episode

| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |
|---:|---|---:|---:|---:|---:|
| 1 | `E_srr:gated_deployment` | 411.13 | [293.48, 499.83] | 10 | 5 |
| 2 | `E_srr:discern_style` | 412.23 | [296.10, 504.45] | 10 | 5 |
| 3 | `E_srr:SMCS+retain-incumbent` | 413.64 | [297.05, 504.55] | 10 | 5 |
| 4 | `E_srr:gated_adaptive_range` | 414.10 | [294.95, 503.74] | 10 | 5 |
| 5 | `E_srrSR:gated_deployment` | 416.43 | [297.25, 522.83] | 10 | 5 |
| 6 | `rmm:discern_style+RMM` | 416.60 | [299.72, 514.83] | 10 | 5 |
| 7 | `rmm:gated_deployment+RMM` | 417.47 | [299.05, 508.11] | 10 | 5 |
| 8 | `rmm:LRMD` | 420.45 | [303.80, 511.31] | 10 | 5 |
| 9 | `rmm:SMCS+retain-incumbent+RMM` | 420.74 | [303.86, 511.12] | 10 | 5 |
| 10 | `rmm:discern_style+RMM_noacq` | 422.36 | [303.92, 517.05] | 10 | 5 |
| 11 | `rmm:gated_adaptive_range+RMM` | 423.43 | [301.99, 513.72] | 10 | 5 |
| 12 | `E_rb:discern_style` | 423.67 | [309.81, 514.83] | 10 | 5 |
| 13 | `E_rb:gated_deployment` | 424.17 | [308.63, 512.40] | 10 | 5 |
| 14 | `E_rb:gated_adaptive_range` | 425.90 | [305.52, 513.72] | 10 | 5 |
| 15 | `E_glr:gated_deployment` | 427.03 | [323.53, 515.70] | 10 | 5 |
| 16 | `qiu_delayed_movement` | 428.45 | [307.20, 537.41] | 10 | 5 |
| 17 | `E_rb:SMCS+retain-incumbent` | 431.17 | [318.20, 519.39] | 10 | 5 |
| 18 | `E_swcert` | 439.18 | [324.07, 521.15] | 10 | 5 |
| 19 | `E_glr:gated_adaptive_range` | 446.06 | [336.46, 541.88] | 10 | 5 |
| 20 | `E_srr_noacq:gated_deployment` | 451.60 | [325.12, 528.32] | 10 | 5 |
| 21 | `rmm:gated_deployment+RMM_noacq` | 451.98 | [310.01, 541.76] | 10 | 5 |
| 22 | `gated_adaptive_range+front` | 455.38 | [301.56, 555.64] | 10 | 5 |
| 23 | `choe_ramdas_eb+front` | 456.16 | [301.59, 557.35] | 10 | 5 |
| 24 | `rmm:discern_style+RMM_single` | 457.37 | [335.67, 541.86] | 10 | 5 |
| 25 | `E_srr_noacq:gated_adaptive_range` | 458.68 | [312.82, 542.41] | 10 | 5 |
| 26 | `xu_acquisition_only` | 462.34 | [335.05, 547.60] | 10 | 5 |
| 27 | `rmm:gated_deployment+RMM_single` | 462.92 | [340.58, 543.98] | 10 | 5 |
| 28 | `rmm:SMCS+retain-incumbent+RMM_single` | 468.84 | [355.33, 547.41] | 10 | 5 |
| 29 | `SMCS+retain-incumbent` | 475.80 | [346.61, 560.15] | 10 | 5 |
| 30 | `gated_adaptive_range` | 487.86 | [351.61, 561.81] | 10 | 5 |
| 31 | `A5b` | 500.44 | [374.57, 562.10] | 10 | 5 |
| 32 | `gated_deployment` | 510.58 | [374.58, 568.19] | 10 | 5 |
| 33 | `CONTROL_never_switch` | 525.30 | [372.88, 584.00] | 10 | 5 |
| 34 | `discern_style` | 535.26 | [382.50, 594.21] | 10 | 5 |

### Mean retrospective hindsight regret per episode

| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |
|---:|---|---:|---:|---:|---:|
| 1 | `E_srr:gated_deployment` | 82.53 | [69.55, 108.62] | 10 | 5 |
| 2 | `E_srr:discern_style` | 83.63 | [69.43, 112.89] | 10 | 5 |
| 3 | `E_srr:SMCS+retain-incumbent` | 85.04 | [74.93, 109.39] | 10 | 5 |
| 4 | `E_srr:gated_adaptive_range` | 85.50 | [71.23, 112.27] | 10 | 5 |
| 5 | `E_srrSR:gated_deployment` | 87.83 | [70.72, 119.98] | 10 | 5 |
| 6 | `rmm:discern_style+RMM` | 88.00 | [71.24, 116.47] | 10 | 5 |
| 7 | `rmm:gated_deployment+RMM` | 88.86 | [77.24, 110.38] | 10 | 5 |
| 8 | `rmm:LRMD` | 91.85 | [82.71, 112.96] | 10 | 5 |
| 9 | `rmm:SMCS+retain-incumbent+RMM` | 92.14 | [83.12, 112.81] | 10 | 5 |
| 10 | `rmm:discern_style+RMM_noacq` | 93.76 | [83.60, 117.46] | 10 | 5 |
| 11 | `rmm:gated_adaptive_range+RMM` | 94.83 | [79.81, 115.24] | 10 | 5 |
| 12 | `E_rb:discern_style` | 95.06 | [85.40, 116.47] | 10 | 5 |
| 13 | `E_rb:gated_deployment` | 95.56 | [83.11, 120.62] | 10 | 5 |
| 14 | `E_rb:gated_adaptive_range` | 97.30 | [87.57, 115.24] | 10 | 5 |
| 15 | `E_glr:gated_deployment` | 98.43 | [68.33, 144.09] | 10 | 5 |
| 16 | `qiu_delayed_movement` | 99.85 | [78.59, 134.38] | 10 | 5 |
| 17 | `E_rb:SMCS+retain-incumbent` | 102.57 | [87.70, 130.19] | 10 | 5 |
| 18 | `E_swcert` | 110.58 | [101.41, 129.54] | 10 | 5 |
| 19 | `E_glr:gated_adaptive_range` | 117.46 | [77.81, 185.85] | 10 | 5 |
| 20 | `E_srr_noacq:gated_deployment` | 122.99 | [80.61, 151.73] | 10 | 5 |
| 21 | `rmm:gated_deployment+RMM_noacq` | 123.38 | [83.92, 151.96] | 10 | 5 |
| 22 | `gated_adaptive_range+front` | 126.78 | [76.63, 154.98] | 10 | 5 |
| 23 | `choe_ramdas_eb+front` | 127.56 | [77.64, 155.29] | 10 | 5 |
| 24 | `rmm:discern_style+RMM_single` | 128.77 | [123.35, 135.54] | 10 | 5 |
| 25 | `E_srr_noacq:gated_adaptive_range` | 130.08 | [86.90, 164.54] | 10 | 5 |
| 26 | `xu_acquisition_only` | 133.74 | [121.09, 143.41] | 10 | 5 |
| 27 | `rmm:gated_deployment+RMM_single` | 134.32 | [129.11, 140.28] | 10 | 5 |
| 28 | `rmm:SMCS+retain-incumbent+RMM_single` | 140.24 | [127.97, 162.15] | 10 | 5 |
| 29 | `SMCS+retain-incumbent` | 147.20 | [128.79, 162.41] | 10 | 5 |
| 30 | `gated_adaptive_range` | 159.26 | [130.80, 174.59] | 10 | 5 |
| 31 | `A5b` | 171.84 | [131.13, 214.71] | 10 | 5 |
| 32 | `gated_deployment` | 181.98 | [131.57, 224.40] | 10 | 5 |
| 33 | `CONTROL_never_switch` | 196.70 | [126.57, 238.38] | 10 | 5 |
| 34 | `discern_style` | 206.66 | [136.18, 248.68] | 10 | 5 |

### Mean label expenditure c_q × labels per episode

| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |
|---:|---|---:|---:|---:|---:|
| 1 | `CONTROL_never_switch` | 0.00 | [0.00, 0.00] | 10 | 5 |
| 2 | `gated_adaptive_range+front` | 3.49 | [2.30, 5.45] | 10 | 5 |
| 3 | `choe_ramdas_eb+front` | 3.56 | [2.21, 5.90] | 10 | 5 |
| 4 | `gated_adaptive_range` | 5.23 | [3.26, 7.64] | 10 | 5 |
| 5 | `E_srr_noacq:gated_adaptive_range` | 6.08 | [3.84, 8.82] | 10 | 5 |
| 6 | `gated_deployment` | 6.55 | [4.53, 8.99] | 10 | 5 |
| 7 | `rmm:gated_deployment+RMM_noacq` | 6.91 | [4.78, 9.38] | 10 | 5 |
| 8 | `E_srr_noacq:gated_deployment` | 6.93 | [4.79, 9.39] | 10 | 5 |
| 9 | `A5b` | 7.07 | [4.56, 8.55] | 10 | 5 |
| 10 | `xu_acquisition_only` | 9.00 | [7.57, 9.80] | 10 | 5 |
| 11 | `rmm:discern_style+RMM_noacq` | 9.69 | [9.35, 9.88] | 10 | 5 |
| 12 | `discern_style` | 9.70 | [9.38, 9.89] | 10 | 5 |
| 13 | `SMCS+retain-incumbent` | 9.70 | [9.39, 9.91] | 10 | 5 |
| 14 | `qiu_delayed_movement` | 9.71 | [9.39, 9.90] | 10 | 5 |
| 15 | `E_swcert` | 9.71 | [9.41, 9.91] | 10 | 5 |
| 16 | `rmm:gated_deployment+RMM_single` | 9.82 | [9.43, 9.99] | 10 | 5 |
| 17 | `E_glr:gated_adaptive_range` | 9.83 | [9.41, 10.00] | 10 | 5 |
| 18 | `rmm:gated_deployment+RMM` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 19 | `rmm:gated_adaptive_range+RMM` | 9.83 | [9.41, 10.00] | 10 | 5 |
| 20 | `rmm:discern_style+RMM_single` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 21 | `rmm:discern_style+RMM` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 22 | `E_srr:gated_adaptive_range` | 9.83 | [9.41, 10.00] | 10 | 5 |
| 23 | `E_rb:discern_style` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 24 | `E_rb:gated_adaptive_range` | 9.83 | [9.41, 10.00] | 10 | 5 |
| 25 | `E_rb:gated_deployment` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 26 | `E_srrSR:gated_deployment` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 27 | `E_srr:gated_deployment` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 28 | `E_srr:discern_style` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 29 | `E_glr:gated_deployment` | 9.83 | [9.43, 10.00] | 10 | 5 |
| 30 | `E_rb:SMCS+retain-incumbent` | 9.84 | [9.42, 10.00] | 10 | 5 |
| 31 | `rmm:SMCS+retain-incumbent+RMM` | 9.84 | [9.42, 10.00] | 10 | 5 |
| 32 | `rmm:SMCS+retain-incumbent+RMM_single` | 9.84 | [9.42, 10.00] | 10 | 5 |
| 33 | `E_srr:SMCS+retain-incumbent` | 9.84 | [9.42, 10.00] | 10 | 5 |
| 34 | `rmm:LRMD` | 9.85 | [9.45, 10.00] | 10 | 5 |

### Mean switching expenditure c_s × switches per episode

| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |
|---:|---|---:|---:|---:|---:|
| 1 | `CONTROL_never_switch` | 0.00 | [0.00, 0.00] | 10 | 5 |
| 2 | `discern_style` | 0.17 | [0.00, 0.33] | 10 | 5 |
| 3 | `gated_deployment` | 1.00 | [0.28, 1.36] | 10 | 5 |
| 4 | `A5b` | 1.50 | [0.00, 2.33] | 10 | 5 |
| 5 | `choe_ramdas_eb+front` | 1.50 | [0.00, 3.33] | 10 | 5 |
| 6 | `gated_adaptive_range` | 1.67 | [0.56, 3.15] | 10 | 5 |
| 7 | `SMCS+retain-incumbent` | 1.83 | [0.56, 3.70] | 10 | 5 |
| 8 | `gated_adaptive_range+front` | 2.00 | [0.62, 3.75] | 10 | 5 |
| 9 | `rmm:gated_deployment+RMM_noacq` | 2.67 | [1.04, 4.26] | 10 | 5 |
| 10 | `xu_acquisition_only` | 2.83 | [0.83, 3.94] | 10 | 5 |
| 11 | `rmm:SMCS+retain-incumbent+RMM_single` | 4.50 | [0.83, 7.27] | 10 | 5 |
| 12 | `E_srr_noacq:gated_adaptive_range` | 4.67 | [1.39, 8.70] | 10 | 5 |
| 13 | `rmm:discern_style+RMM_noacq` | 4.67 | [3.33, 5.00] | 10 | 5 |
| 14 | `rmm:discern_style+RMM_single` | 4.83 | [0.83, 8.33] | 10 | 5 |
| 15 | `E_glr:gated_adaptive_range` | 5.00 | [2.62, 6.31] | 10 | 5 |
| 16 | `rmm:discern_style+RMM` | 5.00 | [2.50, 6.22] | 10 | 5 |
| 17 | `rmm:gated_deployment+RMM_single` | 5.17 | [0.83, 9.44] | 10 | 5 |
| 18 | `E_glr:gated_deployment` | 5.33 | [4.52, 6.06] | 10 | 5 |
| 19 | `E_swcert` | 5.50 | [2.86, 6.88] | 10 | 5 |
| 20 | `rmm:gated_deployment+RMM` | 5.83 | [3.06, 7.08] | 10 | 5 |
| 21 | `rmm:gated_adaptive_range+RMM` | 5.83 | [3.06, 7.08] | 10 | 5 |
| 22 | `rmm:SMCS+retain-incumbent+RMM` | 5.83 | [3.06, 7.08] | 10 | 5 |
| 23 | `E_rb:discern_style` | 6.00 | [3.06, 8.12] | 10 | 5 |
| 24 | `E_srr_noacq:gated_deployment` | 6.17 | [2.22, 11.48] | 10 | 5 |
| 25 | `E_rb:gated_adaptive_range` | 6.17 | [3.33, 7.56] | 10 | 5 |
| 26 | `rmm:LRMD` | 6.50 | [3.33, 8.33] | 10 | 5 |
| 27 | `E_rb:gated_deployment` | 6.83 | [3.33, 9.38] | 10 | 5 |
| 28 | `E_rb:SMCS+retain-incumbent` | 7.00 | [3.33, 9.44] | 10 | 5 |
| 29 | `E_srr:discern_style` | 7.50 | [3.33, 11.36] | 10 | 5 |
| 30 | `E_srr:gated_adaptive_range` | 8.00 | [4.44, 11.67] | 10 | 5 |
| 31 | `E_srr:gated_deployment` | 8.17 | [5.00, 11.67] | 10 | 5 |
| 32 | `E_srr:SMCS+retain-incumbent` | 8.17 | [4.17, 11.67] | 10 | 5 |
| 33 | `qiu_delayed_movement` | 12.83 | [8.54, 15.00] | 10 | 5 |
| 34 | `E_srrSR:gated_deployment` | 13.67 | [9.55, 19.29] | 10 | 5 |

### Paired ΔJ vs same-sample selected comparator `gated_adaptive_range+front`

| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |
|---:|---|---:|---:|---:|---:|
| 1 | `E_srr:gated_deployment` | -44.25 | [-77.63, 17.74] | 10 | 5 |
| 2 | `E_srr:discern_style` | -43.15 | [-79.17, 23.73] | 10 | 5 |
| 3 | `E_srr:SMCS+retain-incumbent` | -41.75 | [-76.87, 18.30] | 10 | 5 |
| 4 | `E_srr:gated_adaptive_range` | -41.29 | [-75.58, 22.40] | 10 | 5 |
| 5 | `E_srrSR:gated_deployment` | -38.95 | [-71.77, 4.83] | 10 | 5 |
| 6 | `rmm:discern_style+RMM` | -38.79 | [-69.10, 3.35] | 10 | 5 |
| 7 | `rmm:gated_deployment+RMM` | -37.92 | [-66.61, 13.26] | 10 | 5 |
| 8 | `rmm:LRMD` | -34.93 | [-67.65, 17.55] | 10 | 5 |
| 9 | `rmm:SMCS+retain-incumbent+RMM` | -34.65 | [-67.32, 18.16] | 10 | 5 |
| 10 | `rmm:discern_style+RMM_noacq` | -33.03 | [-64.94, 16.12] | 10 | 5 |
| 11 | `rmm:gated_adaptive_range+RMM` | -31.95 | [-58.92, 10.11] | 10 | 5 |
| 12 | `E_rb:discern_style` | -31.72 | [-69.10, 23.54] | 10 | 5 |
| 13 | `E_rb:gated_deployment` | -31.22 | [-66.61, 32.40] | 10 | 5 |
| 14 | `E_rb:gated_adaptive_range` | -29.49 | [-58.92, 17.16] | 10 | 5 |
| 15 | `E_glr:gated_deployment` | -28.35 | [-86.79, 67.70] | 10 | 5 |
| 16 | `qiu_delayed_movement` | -26.94 | [-55.86, 25.19] | 10 | 5 |
| 17 | `E_rb:SMCS+retain-incumbent` | -24.21 | [-66.47, 46.83] | 10 | 5 |
| 18 | `E_swcert` | -16.20 | [-49.78, 41.33] | 10 | 5 |
| 19 | `E_glr:gated_adaptive_range` | -9.32 | [-77.17, 109.22] | 10 | 5 |
| 20 | `E_srr_noacq:gated_deployment` | -3.79 | [-39.17, 32.43] | 10 | 5 |
| 21 | `rmm:gated_deployment+RMM_noacq` | -3.40 | [-18.06, 11.87] | 10 | 5 |
| 22 | `gated_adaptive_range+front` | 0.00 | [0.00, 0.00] | 10 | 5 |
| 23 | `choe_ramdas_eb+front` | 0.78 | [-0.30, 3.03] | 10 | 5 |
| 24 | `rmm:discern_style+RMM_single` | 1.98 | [-25.68, 48.07] | 10 | 5 |
| 25 | `E_srr_noacq:gated_adaptive_range` | 3.30 | [-31.17, 28.53] | 10 | 5 |
| 26 | `xu_acquisition_only` | 6.95 | [-13.33, 45.25] | 10 | 5 |
| 27 | `rmm:gated_deployment+RMM_single` | 7.54 | [-21.43, 59.52] | 10 | 5 |
| 28 | `rmm:SMCS+retain-incumbent+RMM_single` | 13.45 | [-24.88, 84.97] | 10 | 5 |
| 29 | `SMCS+retain-incumbent` | 20.42 | [3.56, 55.13] | 10 | 5 |
| 30 | `gated_adaptive_range` | 32.48 | [0.40, 89.58] | 10 | 5 |
| 31 | `A5b` | 45.05 | [1.23, 138.08] | 10 | 5 |
| 32 | `gated_deployment` | 55.20 | [0.85, 145.34] | 10 | 5 |
| 33 | `CONTROL_never_switch` | 69.92 | [-3.53, 150.26] | 10 | 5 |
| 34 | `discern_style` | 79.88 | [5.95, 160.02] | 10 | 5 |

### Mean detect_delay among episodes with a promotion

| Rank | Policy | Mean | 95% cluster CI | Episodes | Clusters |
|---:|---|---:|---:|---:|---:|
| 1 | `E_srrSR:gated_deployment` | 135.97 | [70.22, 241.17] | 10 | 5 |
| 2 | `E_srr:discern_style` | 150.59 | [107.77, 206.78] | 9 | 4 |
| 3 | `E_srr:gated_deployment` | 182.53 | [127.15, 276.33] | 10 | 5 |
| 4 | `E_srr:SMCS+retain-incumbent` | 184.07 | [124.77, 289.52] | 10 | 5 |
| 5 | `E_srr:gated_adaptive_range` | 197.23 | [128.93, 294.38] | 10 | 5 |
| 6 | `E_srr_noacq:gated_deployment` | 208.22 | [89.67, 313.83] | 6 | 3 |
| 7 | `rmm:LRMD` | 239.41 | [188.47, 303.08] | 9 | 4 |
| 8 | `qiu_delayed_movement` | 239.74 | [186.77, 366.73] | 9 | 4 |
| 9 | `choe_ramdas_eb+front` | 297.67 | not estimable | 3 | 2 |
| 10 | `rmm:gated_deployment+RMM` | 299.30 | [218.27, 430.42] | 9 | 4 |
| 11 | `E_rb:gated_deployment` | 299.30 | [218.27, 430.42] | 9 | 4 |
| 12 | `rmm:SMCS+retain-incumbent+RMM` | 309.15 | [183.73, 529.62] | 9 | 4 |
| 13 | `E_rb:SMCS+retain-incumbent` | 309.15 | [183.73, 529.62] | 9 | 4 |
| 14 | `E_srr_noacq:gated_adaptive_range` | 310.60 | [114.50, 453.33] | 5 | 3 |
| 15 | `rmm:gated_adaptive_range+RMM` | 320.22 | [242.60, 426.48] | 9 | 4 |
| 16 | `E_rb:gated_adaptive_range` | 320.22 | [242.60, 426.48] | 9 | 4 |
| 17 | `E_rb:discern_style` | 320.81 | [256.67, 369.07] | 9 | 4 |
| 18 | `rmm:discern_style+RMM` | 320.81 | [256.67, 369.07] | 9 | 4 |
| 19 | `rmm:discern_style+RMM_single` | 323.73 | [248.83, 409.67] | 5 | 3 |
| 20 | `rmm:gated_deployment+RMM_single` | 348.40 | [282.33, 416.33] | 5 | 3 |
| 21 | `gated_adaptive_range+front` | 411.25 | [190.00, 693.00] | 4 | 3 |
| 22 | `rmm:SMCS+retain-incumbent+RMM_single` | 451.20 | [254.50, 665.67] | 5 | 3 |
| 23 | `E_glr:gated_adaptive_range` | 459.90 | [220.14, 746.78] | 10 | 5 |
| 24 | `E_glr:gated_deployment` | 475.95 | [235.43, 795.87] | 10 | 5 |
| 25 | `rmm:discern_style+RMM_noacq` | 505.00 | [325.48, 622.08] | 10 | 5 |
| 26 | `E_swcert` | 506.44 | [331.00, 782.46] | 9 | 4 |
| 27 | `rmm:gated_deployment+RMM_noacq` | 630.89 | [361.00, 939.83] | 6 | 3 |
| 28 | `SMCS+retain-incumbent` | 673.21 | [418.00, 892.67] | 4 | 3 |
| 29 | `A5b` | 683.00 | not estimable | 3 | 2 |
| 30 | `xu_acquisition_only` | 896.28 | [381.00, 1020.67] | 6 | 3 |
| 31 | `gated_deployment` | 1145.67 | [594.00, 1561.00] | 3 | 3 |
| 32 | `discern_style` | 1147.00 | not estimable | 1 | 1 |
| 33 | `gated_adaptive_range` | 1161.50 | [593.00, 1463.33] | 4 | 3 |

Not rankable for promotion delay (no promotion in any seed): `CONTROL_never_switch`.

## Scope and reproduction

Label and switch expenditure are reported separately from J; total J already includes both. Hindsight regret is retrospective. The paired ΔJ table uses the same-sample selected comparator `gated_adaptive_range+front`, so it is exploratory and not selection-adjusted.

Limitations: retrospective class labels, exposed raw streams, five source clusters, and no independent confirmation. See `RESULTS.md` and `protocol.md` for the registered WP1 estimand, comparator definitions and late-class verdict.

Reproduce from the registered saved records:

```sh
uv run python scripts/sota_sprint/build_wp1_late_metric_leaderboard.py
```
