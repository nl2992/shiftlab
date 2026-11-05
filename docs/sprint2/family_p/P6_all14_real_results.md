# P6 all-14-source real-stream cost replay

Post-development descriptive replay; 20 policy-randomness seeds per fixed episode. All sources are previously exposed. t intervals are computed across within-source chronological episodes and may be optimistic. No event is labeled late, reversal, or null from its realized outcome. See JSON for per-source costs, resource use, promotion rates, and limitations.

## Paired P6 cost differences by source

| Source | Episodes | Comparator | P6 − comparator, mean [95% t CI] | Episodes favoring P6 |
|---|---:|---|---:|---:|
| rialto | 16 | M_LRMD_SUI | 9.00 [-5.00, 23.01] | 1/16 |
| rialto | 16 | A5b | 2.48 [-13.48, 18.44] | 7/16 |
| rialto | 16 | D2 | 104.08 [72.75, 135.42] | 0/16 |
| rialto | 16 | rmm:gated_deployment+RMM | 90.44 [59.37, 121.52] | 1/16 |
| rialto | 16 | gated_adaptive_range+front | 97.51 [65.89, 129.13] | 0/16 |
| rialto | 16 | CONTROL_never_switch | -13.61 [-30.28, 3.06] | 6/16 |
| spam | 1 | M_LRMD_SUI | 185.90 not estimable (1 episode) | 0/1 |
| spam | 1 | A5b | 256.80 not estimable (1 episode) | 0/1 |
| spam | 1 | D2 | 333.21 not estimable (1 episode) | 0/1 |
| spam | 1 | rmm:gated_deployment+RMM | 307.00 not estimable (1 episode) | 0/1 |
| spam | 1 | gated_adaptive_range+front | 322.20 not estimable (1 episode) | 0/1 |
| spam | 1 | CONTROL_never_switch | -293.20 not estimable (1 episode) | 1/1 |
| weather | 3 | M_LRMD_SUI | 10.88 [-22.37, 44.13] | 1/3 |
| weather | 3 | A5b | 19.71 [-24.02, 63.43] | 1/3 |
| weather | 3 | D2 | 26.35 [-25.11, 77.80] | 0/3 |
| weather | 3 | rmm:gated_deployment+RMM | 7.48 [-15.35, 30.31] | 0/3 |
| weather | 3 | gated_adaptive_range+front | 17.01 [-22.81, 56.82] | 1/3 |
| weather | 3 | CONTROL_never_switch | -18.23 [-78.59, 42.13] | 2/3 |
| openml_ldpa | 32 | M_LRMD_SUI | 22.83 [10.58, 35.08] | 7/32 |
| openml_ldpa | 32 | A5b | 30.34 [-2.01, 62.69] | 12/32 |
| openml_ldpa | 32 | D2 | 126.02 [88.52, 163.52] | 0/32 |
| openml_ldpa | 32 | rmm:gated_deployment+RMM | 105.34 [68.51, 142.17] | 4/32 |
| openml_ldpa | 32 | gated_adaptive_range+front | 110.08 [71.20, 148.96] | 3/32 |
| openml_ldpa | 32 | CONTROL_never_switch | -91.85 [-127.45, -56.26] | 28/32 |
| uci_occupancy | 4 | M_LRMD_SUI | 0.00 [0.00, 0.00] | 0/4 |
| uci_occupancy | 4 | A5b | 0.16 [-2.02, 2.34] | 2/4 |
| uci_occupancy | 4 | D2 | 350.34 [-759.63, 1460.32] | 1/4 |
| uci_occupancy | 4 | rmm:gated_deployment+RMM | 338.19 [-724.69, 1401.07] | 1/4 |
| uci_occupancy | 4 | gated_adaptive_range+front | 349.18 [-755.27, 1453.64] | 1/4 |
| uci_occupancy | 4 | CONTROL_never_switch | 5.07 [-2.35, 12.50] | 0/4 |
| airlines | 50 | M_LRMD_SUI | 0.24 [-0.30, 0.78] | 3/50 |
| airlines | 50 | A5b | -1.20 [-2.84, 0.45] | 31/50 |
| airlines | 50 | D2 | 2.30 [-1.26, 5.86] | 12/50 |
| airlines | 50 | rmm:gated_deployment+RMM | 1.18 [-0.76, 3.13] | 31/50 |
| airlines | 50 | gated_adaptive_range+front | 1.68 [-1.86, 5.23] | 25/50 |
| airlines | 50 | CONTROL_never_switch | 6.01 [2.65, 9.37] | 4/50 |
| bank | 8 | M_LRMD_SUI | 0.12 [-0.16, 0.40] | 0/8 |
| bank | 8 | A5b | -0.03 [-0.11, 0.04] | 2/8 |
| bank | 8 | D2 | 3.61 [-4.93, 12.15] | 1/8 |
| bank | 8 | rmm:gated_deployment+RMM | -0.05 [-0.17, 0.07] | 2/8 |
| bank | 8 | gated_adaptive_range+front | 7.66 [-3.97, 19.29] | 0/8 |
| bank | 8 | CONTROL_never_switch | 8.72 [5.77, 11.66] | 0/8 |
| elec2 | 4 | M_LRMD_SUI | -1.30 [-4.47, 1.87] | 2/4 |
| elec2 | 4 | A5b | 3.40 [-0.42, 7.22] | 0/4 |
| elec2 | 4 | D2 | 10.07 [-9.57, 29.71] | 1/4 |
| elec2 | 4 | rmm:gated_deployment+RMM | 0.82 [-3.69, 5.34] | 3/4 |
| elec2 | 4 | gated_adaptive_range+front | -0.71 [-13.94, 12.52] | 3/4 |
| elec2 | 4 | CONTROL_never_switch | 6.44 [3.55, 9.33] | 0/4 |
| criteo | 50 | M_LRMD_SUI | 1.21 [0.18, 2.23] | 5/50 |
| criteo | 50 | A5b | 0.21 [-0.16, 0.57] | 35/50 |
| criteo | 50 | D2 | 2.66 [1.22, 4.09] | 5/50 |
| criteo | 50 | rmm:gated_deployment+RMM | 0.36 [-0.12, 0.83] | 36/50 |
| criteo | 50 | gated_adaptive_range+front | 0.49 [-0.34, 1.31] | 36/50 |
| criteo | 50 | CONTROL_never_switch | 5.68 [4.65, 6.71] | 4/50 |
| metro | 16 | M_LRMD_SUI | 58.01 [46.39, 69.63] | 0/16 |
| metro | 16 | A5b | 101.46 [44.79, 158.12] | 1/16 |
| metro | 16 | D2 | 203.30 [162.59, 244.01] | 0/16 |
| metro | 16 | rmm:gated_deployment+RMM | 170.66 [130.46, 210.86] | 0/16 |
| metro | 16 | gated_adaptive_range+front | 196.71 [155.60, 237.82] | 0/16 |
| metro | 16 | CONTROL_never_switch | -396.99 [-442.55, -351.44] | 16/16 |
| beijing_pm25 | 14 | M_LRMD_SUI | -2.99 [-11.88, 5.90] | 6/14 |
| beijing_pm25 | 14 | A5b | -8.48 [-18.23, 1.27] | 7/14 |
| beijing_pm25 | 14 | D2 | 99.53 [26.41, 172.65] | 1/14 |
| beijing_pm25 | 14 | rmm:gated_deployment+RMM | 82.95 [22.12, 143.79] | 4/14 |
| beijing_pm25 | 14 | gated_adaptive_range+front | 48.88 [-10.03, 107.78] | 4/14 |
| beijing_pm25 | 14 | CONTROL_never_switch | -16.84 [-52.60, 18.92] | 5/14 |
| bike_hour | 6 | M_LRMD_SUI | 24.31 [14.71, 33.90] | 0/6 |
| bike_hour | 6 | A5b | 22.77 [-11.76, 57.31] | 1/6 |
| bike_hour | 6 | D2 | 111.84 [52.05, 171.63] | 0/6 |
| bike_hour | 6 | rmm:gated_deployment+RMM | 79.08 [22.22, 135.95] | 0/6 |
| bike_hour | 6 | gated_adaptive_range+front | 101.93 [44.32, 159.53] | 0/6 |
| bike_hour | 6 | CONTROL_never_switch | -185.28 [-315.68, -54.88] | 6/6 |
| appliances | 6 | M_LRMD_SUI | 22.04 [-37.20, 81.29] | 2/6 |
| appliances | 6 | A5b | -29.77 [-73.68, 14.14] | 3/6 |
| appliances | 6 | D2 | 226.09 [111.47, 340.72] | 0/6 |
| appliances | 6 | rmm:gated_deployment+RMM | 164.12 [34.96, 293.29] | 0/6 |
| appliances | 6 | gated_adaptive_range+front | 226.80 [114.42, 339.17] | 0/6 |
| appliances | 6 | CONTROL_never_switch | -20.24 [-63.64, 23.17] | 3/6 |
| household_power | 20 | M_LRMD_SUI | 11.42 [1.09, 21.75] | 2/20 |
| household_power | 20 | A5b | 15.76 [-2.71, 34.23] | 4/20 |
| household_power | 20 | D2 | 84.99 [28.09, 141.90] | 5/20 |
| household_power | 20 | rmm:gated_deployment+RMM | 77.14 [27.54, 126.74] | 7/20 |
| household_power | 20 | gated_adaptive_range+front | 75.97 [20.56, 131.37] | 6/20 |
| household_power | 20 | CONTROL_never_switch | -12.85 [-35.30, 9.60] | 5/20 |

## Equal-source descriptive averages

| Policy | Mean net cost across 14 source means |
|---|---:|
| P6_LRMD_U | 525.24 |
| M_LRMD_SUI | 500.83 |
| A5b | 495.69 |
| D2 | 404.92 |
| rmm:gated_deployment+RMM | 423.47 |
| gated_adaptive_range+front | 414.14 |
| CONTROL_never_switch | 597.89 |

| Comparator | Mean of 14 source-level P6 − comparator contrasts |
|---|---:|
| M_LRMD_SUI | 24.40 |
| A5b | 29.54 |
| D2 | 120.31 |
| rmm:gated_deployment+RMM | 101.77 |
| gated_adaptive_range+front | 111.10 |
| CONTROL_never_switch | -72.65 |

This replay covers economic replay only. It cannot establish genuine late-improvement transfer, application-level utility, an anytime guarantee, or independent generalization.
