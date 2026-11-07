# P6 Beta(2,1) bounded development pilot results

This is development evidence only. The candidate is a conventional weighted restart prior;
the pilot does not establish novelty or authorize real-data confirmation.

- Episode blocks: 600
- Raw policy records: 4800
- Runner manifest Git revision: `58fb75525758da75ef4b9ef320422ba326e86d15`
- Raw records SHA-256: `84f8add9b67afc0ea3e10b092ab516094d0dcb57509099af706210f40a3eb97e`
- Compressed records SHA-256: `e56c8f38fa842a8a9ab57d12bc9669957972fd4692b998093161006674425eb3`
- Manifest SHA-256: `0652a2d9d6af0332764370830f746dcdaa8a9029dc9868926bbc7cce02014f7a`
- Analysis script SHA-256: `40c70231cf2bce1b6a88bf40f7cff8f164b182cbe9865d13e83f3b6cc549b0d9`
- Paired bootstrap: 10,000 draws, seed `2026110714`, percentile 95% intervals.

Negative paired differences favor the candidate. Loss, label and switching expenditures are
reported as separate averages; net cost is the simulator's all-in deployment cost.

## S_late_1500@B100

| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |
|---|---:|---:|---:|---:|---:|---:|
| `P6_LRMD_BETA2` | 361.797 | 356.550 | 99.94 | 0.050 | 5.0% | 1937.6 |
| `P6_LRMD_U` | 361.817 | 356.670 | 99.94 | 0.030 | 3.0% | 1942.7 |
| `PFA-SR:gated_adaptive_range` | 361.820 | 356.820 | 100.00 | 0.000 | 0.0% | NA |
| `rmm:gated_adaptive_range+RMM` | 361.820 | 356.820 | 100.00 | 0.000 | 0.0% | NA |
| `E_rb:gated_adaptive_range+front` | 361.820 | 356.820 | 100.00 | 0.000 | 0.0% | NA |
| `gated_adaptive_range+front` | 361.782 | 356.820 | 99.24 | 0.000 | 0.0% | NA |
| `CONTROL_never_switch` | 356.820 | 356.820 | 0.00 | 0.000 | 0.0% | NA |
| `xu_acquisition_only` | 361.634 | 356.820 | 96.28 | 0.000 | 0.0% | NA |

| Paired comparator | Mean difference | 95% bootstrap CI |
|---|---:|---:|
| `P6_LRMD_U` | -0.020 | [-0.140, 0.100] |
| `PFA-SR:gated_adaptive_range` | -0.023 | [-0.353, 0.206] |
| `rmm:gated_adaptive_range+RMM` | -0.023 | [-0.353, 0.198] |
| `E_rb:gated_adaptive_range+front` | -0.023 | [-0.346, 0.205] |
| `gated_adaptive_range+front` | 0.015 | [-0.318, 0.241] |
| `CONTROL_never_switch` | 4.977 | [4.657, 5.207] |
| `xu_acquisition_only` | 0.163 | [-0.168, 0.393] |

Strongest applicable published comparator by observed mean: `gated_adaptive_range+front`.
Primary gate: FAIL (candidate minus comparator = 0.015, 95% CI [-0.318, 0.241]; requires mean <= -5 and upper bound < 0).
*Mean event index among episodes that promoted; `NA` means no promotions.

## F1_late_1200@B100

| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |
|---|---:|---:|---:|---:|---:|---:|
| `P6_LRMD_BETA2` | 376.301 | 369.610 | 99.83 | 0.340 | 34.0% | 1855.1 |
| `P6_LRMD_U` | 376.791 | 370.250 | 99.83 | 0.310 | 31.0% | 1858.6 |
| `PFA-SR:gated_adaptive_range` | 379.700 | 374.700 | 100.00 | 0.000 | 0.0% | NA |
| `rmm:gated_adaptive_range+RMM` | 379.570 | 374.470 | 100.00 | 0.020 | 2.0% | 1882.5 |
| `E_rb:gated_adaptive_range+front` | 379.700 | 374.700 | 100.00 | 0.000 | 0.0% | NA |
| `gated_adaptive_range+front` | 379.625 | 374.700 | 98.51 | 0.000 | 0.0% | NA |
| `CONTROL_never_switch` | 374.700 | 374.700 | 0.00 | 0.000 | 0.0% | NA |
| `xu_acquisition_only` | 379.469 | 374.700 | 95.38 | 0.000 | 0.0% | NA |

| Paired comparator | Mean difference | 95% bootstrap CI |
|---|---:|---:|
| `P6_LRMD_U` | -0.490 | [-1.030, -0.080] |
| `PFA-SR:gated_adaptive_range` | -3.399 | [-5.076, -1.937] |
| `rmm:gated_adaptive_range+RMM` | -3.269 | [-4.928, -1.795] |
| `E_rb:gated_adaptive_range+front` | -3.399 | [-5.101, -1.895] |
| `gated_adaptive_range+front` | -3.324 | [-5.001, -1.844] |
| `CONTROL_never_switch` | 1.601 | [-0.068, 3.099] |
| `xu_acquisition_only` | -3.167 | [-4.864, -1.684] |

## F6_delay400_better@B100

| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |
|---|---:|---:|---:|---:|---:|---:|
| `P6_LRMD_BETA2` | 423.254 | 417.260 | 99.88 | 0.200 | 20.0% | 1739.4 |
| `P6_LRMD_U` | 417.114 | 410.220 | 99.88 | 0.380 | 38.0% | 1571.0 |
| `PFA-SR:gated_adaptive_range` | 401.720 | 394.120 | 100.00 | 0.520 | 52.0% | 1172.4 |
| `rmm:gated_adaptive_range+RMM` | 407.620 | 400.120 | 100.00 | 0.500 | 50.0% | 1319.4 |
| `E_rb:gated_adaptive_range+front` | 384.230 | 376.280 | 100.00 | 0.590 | 59.0% | 748.3 |
| `gated_adaptive_range+front` | 391.479 | 384.080 | 99.99 | 0.480 | 48.0% | 725.5 |
| `CONTROL_never_switch` | 420.360 | 420.360 | 0.00 | 0.000 | 0.0% | NA |
| `xu_acquisition_only` | 416.405 | 409.750 | 96.11 | 0.370 | 37.0% | 1515.4 |

| Paired comparator | Mean difference | 95% bootstrap CI |
|---|---:|---:|
| `P6_LRMD_U` | 6.140 | [3.820, 8.820] |
| `PFA-SR:gated_adaptive_range` | 21.534 | [15.884, 27.293] |
| `rmm:gated_adaptive_range+RMM` | 15.634 | [11.125, 20.365] |
| `E_rb:gated_adaptive_range+front` | 39.024 | [31.734, 46.483] |
| `gated_adaptive_range+front` | 31.774 | [24.623, 39.366] |
| `CONTROL_never_switch` | 2.894 | [1.192, 4.318] |
| `xu_acquisition_only` | 6.848 | [3.678, 10.056] |

## F3_reversal_800@B100

| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |
|---|---:|---:|---:|---:|---:|---:|
| `P6_LRMD_BETA2` | 358.404 | 352.910 | 99.88 | 0.100 | 9.0% | 837.3 |
| `P6_LRMD_U` | 372.214 | 365.620 | 99.88 | 0.320 | 25.0% | 748.9 |
| `PFA-SR:gated_adaptive_range` | 402.840 | 393.690 | 100.00 | 0.830 | 70.0% | 558.4 |
| `rmm:gated_adaptive_range+RMM` | 401.790 | 392.540 | 100.00 | 0.850 | 65.0% | 630.1 |
| `E_rb:gated_adaptive_range+front` | 412.860 | 403.210 | 100.00 | 0.930 | 93.0% | 382.1 |
| `gated_adaptive_range+front` | 409.996 | 401.650 | 78.92 | 0.880 | 88.0% | 390.8 |
| `CONTROL_never_switch` | 345.350 | 345.350 | 0.00 | 0.000 | 0.0% | NA |
| `xu_acquisition_only` | 380.226 | 372.630 | 95.93 | 0.560 | 40.0% | 620.0 |

| Paired comparator | Mean difference | 95% bootstrap CI |
|---|---:|---:|
| `P6_LRMD_U` | -13.810 | [-20.860, -7.260] |
| `PFA-SR:gated_adaptive_range` | -44.436 | [-53.164, -35.445] |
| `rmm:gated_adaptive_range+RMM` | -43.386 | [-52.677, -34.259] |
| `E_rb:gated_adaptive_range+front` | -54.456 | [-61.462, -46.757] |
| `gated_adaptive_range+front` | -51.592 | [-59.387, -43.415] |
| `CONTROL_never_switch` | 13.054 | [8.293, 18.584] |
| `xu_acquisition_only` | -21.823 | [-30.777, -12.691] |

## F0_better@B100

| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |
|---|---:|---:|---:|---:|---:|---:|
| `P6_LRMD_BETA2` | 415.743 | 409.050 | 99.85 | 0.340 | 34.0% | 1515.7 |
| `P6_LRMD_U` | 405.733 | 398.440 | 99.85 | 0.460 | 46.0% | 1258.7 |
| `PFA-SR:gated_adaptive_range` | 388.030 | 380.180 | 100.00 | 0.570 | 57.0% | 872.2 |
| `rmm:gated_adaptive_range+RMM` | 393.109 | 385.310 | 99.99 | 0.560 | 56.0% | 995.6 |
| `E_rb:gated_adaptive_range+front` | 372.940 | 365.090 | 100.00 | 0.570 | 57.0% | 441.8 |
| `gated_adaptive_range+front` | 384.368 | 377.530 | 92.75 | 0.440 | 44.0% | 449.7 |
| `CONTROL_never_switch` | 419.060 | 419.060 | 0.00 | 0.000 | 0.0% | NA |
| `xu_acquisition_only` | 388.024 | 379.870 | 97.09 | 0.660 | 66.0% | 1030.4 |

| Paired comparator | Mean difference | 95% bootstrap CI |
|---|---:|---:|
| `P6_LRMD_U` | 10.010 | [6.250, 14.220] |
| `PFA-SR:gated_adaptive_range` | 27.712 | [20.180, 35.344] |
| `rmm:gated_adaptive_range+RMM` | 22.633 | [15.735, 29.735] |
| `E_rb:gated_adaptive_range+front` | 42.803 | [33.444, 52.245] |
| `gated_adaptive_range+front` | 31.375 | [22.067, 40.712] |
| `CONTROL_never_switch` | -3.318 | [-6.723, -0.221] |
| `xu_acquisition_only` | 27.718 | [20.912, 34.831] |

## F5_dep_null_r8@B100

| Policy | Mean net | Loss | Labels | Switches | Promote % | First promotion time* |
|---|---:|---:|---:|---:|---:|---:|
| `P6_LRMD_BETA2` | 369.183 | 364.190 | 99.87 | 0.000 | 0.0% | NA |
| `P6_LRMD_U` | 369.183 | 364.190 | 99.87 | 0.000 | 0.0% | NA |
| `PFA-SR:gated_adaptive_range` | 369.150 | 364.100 | 100.00 | 0.010 | 1.0% | 744.0 |
| `rmm:gated_adaptive_range+RMM` | 369.720 | 364.470 | 100.00 | 0.050 | 5.0% | 1171.8 |
| `E_rb:gated_adaptive_range+front` | 369.130 | 363.180 | 100.00 | 0.190 | 16.0% | 364.8 |
| `gated_adaptive_range+front` | 369.416 | 364.360 | 98.12 | 0.030 | 3.0% | 388.3 |
| `CONTROL_never_switch` | 364.190 | 364.190 | 0.00 | 0.000 | 0.0% | NA |
| `xu_acquisition_only` | 369.522 | 364.590 | 95.64 | 0.030 | 3.0% | 878.7 |

| Paired comparator | Mean difference | 95% bootstrap CI |
|---|---:|---:|
| `P6_LRMD_U` | 0.000 | [0.000, 0.000] |
| `PFA-SR:gated_adaptive_range` | 0.033 | [-0.010, 0.116] |
| `rmm:gated_adaptive_range+RMM` | -0.537 | [-1.159, -0.083] |
| `E_rb:gated_adaptive_range+front` | 0.053 | [-2.136, 2.366] |
| `gated_adaptive_range+front` | -0.233 | [-0.659, 0.064] |
| `CONTROL_never_switch` | 4.993 | [4.989, 4.997] |
| `xu_acquisition_only` | -0.339 | [-1.077, 0.216] |

Candidate false promotions: 0/100 (0.000%; Wilson 95% CI [0.000%, 3.699%]); descriptive only, not a guarantee test.
