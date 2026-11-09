# FLQ two-tier re-test: registered analysis output

Primary verdict (`gated_adaptive_range+front`): **NOT_SUPPORTED**

## gated_adaptive_range+front (host `gated_adaptive_range`): NOT_SUPPORTED

Tier A pass: True; Tier B pass: True; region wins 2/6 (need 4); replication wins 3/6; framing: front-loading (3/6 pace-equivalent).

| Tier A null | promotion | bound | pass |
|---|---:|---:|---|
| V_null | 0.003 | 0.0638 | True |
| V_worse | 0.000 | 0.0638 | True |
| F0_null | 0.003 | 0.0638 | True |
| N_null | 0.002 | 0.0638 | True |

| Tier B null | promotion (host) | ΔJ vs host | ΔJ vs never | pass (≤ +5) |
|---|---:|---:|---:|---|
| V_null_dep_r5 | 0.002 (0.000) | -0.1 [-0.2, +0.0] | +9.9 [+9.8, +10.0] | True |
| V_null_dep_r8 | 0.102 (0.010) | -1.5 [-2.4, -0.6] | +8.4 [+7.5, +9.3] | True |
| N_null_dep_r7 | 0.064 (0.006) | -0.5 [-0.9, -0.0] | +9.4 [+8.9, +9.9] | True |
| N_null_dep_r9 | 0.204 (0.056) | -2.8 [-4.3, -1.3] | +7.4 [+5.8, +9.1] | True |
| W_null_dep_r95 | 0.376 (0.104) | -1.0 [-4.0, +2.0] | +6.4 [+3.0, +9.9] | True |
| O_null_order2 | 0.238 (0.030) | -2.0 [-3.7, -0.3] | +7.9 [+6.2, +9.6] | True |
| O_null_semimarkov | 0.158 (0.046) | -0.6 [-2.4, +1.3] | +6.3 [+3.2, +9.4] | True |

| region regime | win | max simultaneous upper bound | ΔJ vs host | ΔJ vs pace_tuned |
|---|---|---:|---:|---:|
| N_better_a | False | +0.19 | -32.4 [-37.4, -27.5] | -0.1 [-1.2, +1.1] |
| N_better_b | False | +0.83 | -20.6 [-22.8, -18.3] | +0.0 [+0.0, +0.0] |
| N_better_c | False | +5.64 | -27.9 [-34.4, -21.3] | -2.6 [-6.3, +1.1] |
| N_dep_better_r6 | True | -6.48 | -38.8 [-44.0, -33.7] | -1.1 [-2.3, +0.1] |
| N_near | False | +4.75 | -4.7 [-7.2, -2.2] | -0.3 [-0.7, +0.2] |
| N_bursty | True | -2.66 | -32.0 [-37.5, -26.5] | -1.3 [-3.1, +0.5] |

| replication regime | win | max simultaneous upper bound | ΔJ vs host | ΔJ vs pace_tuned |
|---|---|---:|---:|---:|
| V_better_a | False | +3.57 | -31.3 [-37.1, -25.5] | +0.7 [-1.5, +3.0] |
| V_better_b | True | -4.98 | -33.8 [-36.8, -30.8] | -0.1 [-0.8, +0.6] |
| V_better_c | True | -19.39 | -91.4 [-99.4, -83.3] | -4.2 [-8.5, +0.1] |
| V_dep_better_r5 | True | -5.37 | -36.8 [-41.8, -31.7] | -0.9 [-2.3, +0.6] |
| V_near | False | +8.99 | -4.3 [-7.0, -1.7] | +0.2 [-0.8, +1.1] |
| V_bursty | False | +2.50 | -27.8 [-33.3, -22.2] | -1.6 [-3.7, +0.6] |

| outside regime | ΔJ vs host | ΔJ vs never | ΔJ vs best comparator (mean) |
|---|---:|---:|---:|
| V_late_600 | +1.3 [-0.1, +2.7] | +9.7 [+9.5, +9.9] | -0.3 |
| V_reversal_1000 | +3.2 [-5.0, +11.5] | +41.8 [+37.6, +46.1] | -14.2 |
| V_recurrent | -14.0 [-17.4, -10.5] | -8.2 [-12.2, -4.1] | -18.2 |
| W_late_1000 | -0.4 [-0.8, -0.1] | +9.3 [+8.9, +9.6] | -0.7 |
| W_reversal_700 | +41.5 [+32.9, +50.2] | +71.7 [+65.5, +77.9] | +0.7 |
| N_late_800 | -0.6 [-1.3, +0.0] | +8.7 [+8.3, +9.1] | -1.3 |
| N_reversal_900 | +28.1 [+20.0, +36.2] | +59.8 [+54.4, +65.1] | +5.4 |

## gated_deployment+QCE+front (host `gated_deployment`): NOT_SUPPORTED

Tier A pass: True; Tier B pass: True; region wins 2/6 (need 4); replication wins 3/6; framing: front-loading (2/6 pace-equivalent).

| Tier A null | promotion | bound | pass |
|---|---:|---:|---|
| V_null | 0.003 | 0.0638 | True |
| V_worse | 0.000 | 0.0638 | True |
| F0_null | 0.002 | 0.0638 | True |
| N_null | 0.002 | 0.0638 | True |

| Tier B null | promotion (host) | ΔJ vs host | ΔJ vs never | pass (≤ +5) |
|---|---:|---:|---:|---|
| V_null_dep_r5 | 0.004 (0.000) | -0.1 [-0.2, +0.0] | +9.9 [+9.8, +10.0] | True |
| V_null_dep_r8 | 0.114 (0.000) | -1.7 [-2.7, -0.7] | +8.3 [+7.3, +9.3] | True |
| N_null_dep_r7 | 0.068 (0.000) | -0.7 [-1.3, -0.2] | +9.3 [+8.7, +9.8] | True |
| N_null_dep_r9 | 0.228 (0.002) | -2.9 [-4.5, -1.3] | +6.9 [+5.3, +8.5] | True |
| W_null_dep_r95 | 0.432 (0.014) | -3.0 [-6.7, +0.7] | +6.8 [+3.0, +10.6] | True |
| O_null_order2 | 0.264 (0.000) | -1.9 [-3.8, -0.0] | +8.1 [+6.2, +9.9] | True |
| O_null_semimarkov | 0.166 (0.012) | -2.6 [-4.9, -0.2] | +6.1 [+3.0, +9.2] | True |

| region regime | win | max simultaneous upper bound | ΔJ vs host | ΔJ vs pace_tuned |
|---|---|---:|---:|---:|
| N_better_a | False | +0.54 | -41.4 [-46.8, -36.1] | +0.2 [-2.0, +2.5] |
| N_better_b | False | +1.74 | -27.7 [-30.7, -24.6] | +0.9 [+0.3, +1.5] |
| N_better_c | False | +5.75 | -30.0 [-36.7, -23.4] | -2.8 [-6.7, +1.0] |
| N_dep_better_r6 | True | -8.42 | -64.1 [-70.0, -58.1] | -3.0 [-5.1, -0.9] |
| N_near | False | +4.10 | -5.3 [-7.8, -2.7] | -0.8 [-1.7, +0.1] |
| N_bursty | True | -2.42 | -46.5 [-52.1, -41.0] | -1.0 [-2.9, +0.9] |

| replication regime | win | max simultaneous upper bound | ΔJ vs host | ΔJ vs pace_tuned |
|---|---|---:|---:|---:|
| V_better_a | False | +3.81 | -36.7 [-42.8, -30.6] | +1.1 [-1.3, +3.5] |
| V_better_b | True | -4.89 | -61.1 [-64.9, -57.3] | -0.2 [-1.2, +0.8] |
| V_better_c | True | -17.32 | -119.4 [-127.0, -111.8] | -2.2 [-6.4, +2.0] |
| V_dep_better_r5 | True | -6.13 | -51.5 [-57.0, -46.0] | -1.7 [-3.3, -0.1] |
| V_near | False | +9.10 | -5.6 [-8.0, -3.1] | +0.2 [-0.7, +1.1] |
| V_bursty | False | +2.22 | -38.6 [-44.5, -32.7] | -1.6 [-3.7, +0.5] |

| outside regime | ΔJ vs host | ΔJ vs never | ΔJ vs best comparator (mean) |
|---|---:|---:|---:|
| V_late_600 | -0.2 [-0.4, -0.0] | +9.7 [+9.5, +9.9] | -0.3 |
| V_reversal_1000 | +27.5 [+21.8, +33.2] | +42.1 [+37.9, +46.3] | -14.0 |
| V_recurrent | -17.3 [-21.1, -13.5] | -7.6 [-11.6, -3.7] | -17.6 |
| W_late_1000 | -0.6 [-0.9, -0.2] | +9.4 [+9.0, +9.7] | -0.6 |
| W_reversal_700 | +59.9 [+52.9, +66.8] | +72.2 [+65.8, +78.6] | +1.2 |
| N_late_800 | -1.2 [-1.6, -0.8] | +8.8 [+8.4, +9.2] | -1.2 |
| N_reversal_900 | +47.8 [+42.2, +53.5] | +60.2 [+54.8, +65.7] | +5.8 |

## Uncertified context (`model_selector_causal`)

| null | promotion | ΔJ vs never |
|---|---:|---:|
| V_null | 0.956 | +38.1 [+36.4, +39.9] |
| V_worse | 0.651 | +27.3 [+26.1, +28.4] |
| F0_null | 0.952 | +36.2 [+34.5, +37.9] |
| N_null | 0.946 | +38.8 [+37.0, +40.7] |
| V_null_dep_r5 | 0.948 | +36.3 [+33.7, +38.9] |
| V_null_dep_r8 | 0.946 | +33.7 [+30.4, +37.0] |
| N_null_dep_r7 | 0.966 | +39.1 [+36.1, +42.2] |
| N_null_dep_r9 | 0.936 | +33.6 [+30.2, +36.9] |
| W_null_dep_r95 | 0.932 | +32.8 [+27.8, +37.7] |
| O_null_order2 | 0.940 | +35.9 [+31.9, +39.8] |
| O_null_semimarkov | 0.934 | +28.1 [+23.1, +33.1] |
