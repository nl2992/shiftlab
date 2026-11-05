# R5 all-14-source real-stream cost replay

Post-development descriptive replay; 20 policy-randomness seeds per fixed episode. All sources are previously exposed. t intervals are computed across within-source chronological episodes and may be optimistic. No event is labeled late, reversal, or null from its realized outcome. See JSON for per-source costs, resource use, promotion rates, and limitations.

## Paired R5 cost differences by source

| Source | Episodes | Comparator | R5 − comparator, mean [95% t CI] | Episodes favoring R5 |
|---|---:|---|---:|---:|
| rialto | 16 | D2 | 0.87 [0.24, 1.50] | 1/16 |
| rialto | 16 | A5b | -100.94 [-133.83, -68.05] | 16/16 |
| rialto | 16 | economic_replacement | -9.51 [-11.13, -7.88] | 16/16 |
| rialto | 16 | R:economic_stop | -12.12 [-14.97, -9.26] | 16/16 |
| rialto | 16 | cams_adapter | 10.32 [9.33, 11.32] | 0/16 |
| rialto | 16 | gated_adaptive_range+front | -5.91 [-7.78, -4.05] | 16/16 |
| spam | 1 | D2 | -6.70 not estimable (1 episode) | 1/1 |
| spam | 1 | A5b | -82.24 not estimable (1 episode) | 1/1 |
| spam | 1 | economic_replacement | -25.99 not estimable (1 episode) | 1/1 |
| spam | 1 | R:economic_stop | -169.12 not estimable (1 episode) | 1/1 |
| spam | 1 | cams_adapter | 6.26 not estimable (1 episode) | 0/1 |
| spam | 1 | gated_adaptive_range+front | -16.84 not estimable (1 episode) | 1/1 |
| weather | 3 | D2 | -12.15 [-15.85, -8.45] | 3/3 |
| weather | 3 | A5b | -18.84 [-29.77, -7.92] | 3/3 |
| weather | 3 | economic_replacement | -1.77 [-53.56, 50.02] | 2/3 |
| weather | 3 | R:economic_stop | -59.30 [-158.14, 39.54] | 3/3 |
| weather | 3 | cams_adapter | -3.26 [-7.84, 1.32] | 3/3 |
| weather | 3 | gated_adaptive_range+front | -21.57 [-47.90, 4.76] | 3/3 |
| openml_ldpa | 32 | D2 | 3.27 [-9.64, 16.18] | 16/32 |
| openml_ldpa | 32 | A5b | -92.30 [-135.32, -49.29] | 29/32 |
| openml_ldpa | 32 | economic_replacement | 0.28 [-12.51, 13.08] | 25/32 |
| openml_ldpa | 32 | R:economic_stop | -93.61 [-120.74, -66.47] | 30/32 |
| openml_ldpa | 32 | cams_adapter | 14.01 [4.13, 23.89] | 6/32 |
| openml_ldpa | 32 | gated_adaptive_range+front | -12.59 [-20.55, -4.62] | 26/32 |
| uci_occupancy | 4 | D2 | 0.47 [-6.47, 7.41] | 1/4 |
| uci_occupancy | 4 | A5b | -349.71 [-1458.71, 759.28] | 4/4 |
| uci_occupancy | 4 | economic_replacement | -24.75 [-91.86, 42.35] | 4/4 |
| uci_occupancy | 4 | R:economic_stop | -66.75 [-281.42, 147.93] | 3/4 |
| uci_occupancy | 4 | cams_adapter | 1.70 [-10.62, 14.01] | 2/4 |
| uci_occupancy | 4 | gated_adaptive_range+front | -0.69 [-5.24, 3.86] | 3/4 |
| airlines | 50 | D2 | -2.68 [-5.07, -0.28] | 22/50 |
| airlines | 50 | A5b | -5.99 [-11.37, -0.62] | 31/50 |
| airlines | 50 | economic_replacement | -9.22 [-14.93, -3.51] | 32/50 |
| airlines | 50 | R:economic_stop | -4.80 [-10.39, 0.80] | 24/50 |
| airlines | 50 | cams_adapter | -17.18 [-22.26, -12.10] | 42/50 |
| airlines | 50 | gated_adaptive_range+front | -3.11 [-6.31, 0.08] | 25/50 |
| bank | 8 | D2 | -3.40 [-11.43, 4.63] | 1/8 |
| bank | 8 | A5b | -5.93 [-19.94, 8.09] | 1/8 |
| bank | 8 | economic_replacement | -6.36 [-17.31, 4.59] | 2/8 |
| bank | 8 | R:economic_stop | -1.86 [-16.82, 13.11] | 1/8 |
| bank | 8 | cams_adapter | -15.71 [-33.63, 2.21] | 5/8 |
| bank | 8 | gated_adaptive_range+front | 1.77 [-1.14, 4.68] | 1/8 |
| elec2 | 4 | D2 | 0.97 [-8.81, 10.76] | 1/4 |
| elec2 | 4 | A5b | -8.20 [-37.48, 21.08] | 2/4 |
| elec2 | 4 | economic_replacement | -7.44 [-24.92, 10.04] | 4/4 |
| elec2 | 4 | R:economic_stop | -9.87 [-39.75, 20.01] | 2/4 |
| elec2 | 4 | cams_adapter | -14.56 [-33.09, 3.97] | 3/4 |
| elec2 | 4 | gated_adaptive_range+front | -12.31 [-44.31, 19.69] | 2/4 |
| criteo | 50 | D2 | -8.85 [-11.03, -6.66] | 50/50 |
| criteo | 50 | A5b | -11.29 [-14.05, -8.52] | 50/50 |
| criteo | 50 | economic_replacement | 4.50 [2.40, 6.60] | 16/50 |
| criteo | 50 | R:economic_stop | -11.67 [-14.84, -8.51] | 49/50 |
| criteo | 50 | cams_adapter | -6.58 [-10.06, -3.11] | 31/50 |
| criteo | 50 | gated_adaptive_range+front | -11.01 [-13.63, -8.38] | 50/50 |
| metro | 16 | D2 | -0.19 [-1.19, 0.80] | 6/16 |
| metro | 16 | A5b | -101.84 [-177.52, -26.17] | 16/16 |
| metro | 16 | economic_replacement | -36.96 [-39.96, -33.96] | 16/16 |
| metro | 16 | R:economic_stop | -196.07 [-219.37, -172.76] | 16/16 |
| metro | 16 | cams_adapter | 2.51 [0.93, 4.09] | 3/16 |
| metro | 16 | gated_adaptive_range+front | -6.59 [-9.34, -3.83] | 16/16 |
| beijing_pm25 | 14 | D2 | 27.93 [-9.73, 65.60] | 6/14 |
| beijing_pm25 | 14 | A5b | -80.06 [-135.73, -24.39] | 12/14 |
| beijing_pm25 | 14 | economic_replacement | 29.42 [-12.38, 71.21] | 7/14 |
| beijing_pm25 | 14 | R:economic_stop | -59.31 [-109.67, -8.95] | 13/14 |
| beijing_pm25 | 14 | cams_adapter | 17.25 [-22.72, 57.21] | 7/14 |
| beijing_pm25 | 14 | gated_adaptive_range+front | -22.92 [-79.04, 33.20] | 11/14 |
| bike_hour | 6 | D2 | -4.72 [-14.77, 5.33] | 4/6 |
| bike_hour | 6 | A5b | -92.95 [-145.85, -40.05] | 6/6 |
| bike_hour | 6 | economic_replacement | -18.56 [-33.28, -3.85] | 5/6 |
| bike_hour | 6 | R:economic_stop | -169.24 [-223.94, -114.53] | 6/6 |
| bike_hour | 6 | cams_adapter | -2.34 [-6.09, 1.41] | 5/6 |
| bike_hour | 6 | gated_adaptive_range+front | -13.79 [-21.08, -6.50] | 6/6 |
| appliances | 6 | D2 | -2.40 [-9.09, 4.28] | 3/6 |
| appliances | 6 | A5b | -258.63 [-399.18, -118.08] | 6/6 |
| appliances | 6 | economic_replacement | -6.16 [-16.91, 4.59] | 4/6 |
| appliances | 6 | R:economic_stop | -212.59 [-305.33, -119.85] | 6/6 |
| appliances | 6 | cams_adapter | -21.58 [-59.02, 15.86] | 5/6 |
| appliances | 6 | gated_adaptive_range+front | -2.07 [-7.81, 3.68] | 4/6 |
| household_power | 20 | D2 | -1.98 [-21.47, 17.51] | 9/20 |
| household_power | 20 | A5b | -71.39 [-114.15, -28.63] | 14/20 |
| household_power | 20 | economic_replacement | -1.85 [-24.00, 20.30] | 13/20 |
| household_power | 20 | R:economic_stop | -60.49 [-96.49, -24.49] | 15/20 |
| household_power | 20 | cams_adapter | -3.37 [-24.96, 18.22] | 11/20 |
| household_power | 20 | gated_adaptive_range+front | -11.18 [-28.17, 5.81] | 16/20 |

## Equal-source descriptive averages

| Policy | Mean net cost across 14 source means |
|---|---:|
| R5 | 404.22 |
| D2 | 404.91 |
| A5b | 495.68 |
| economic_replacement | 412.39 |
| R:economic_stop | 484.71 |
| cams_adapter | 406.55 |
| gated_adaptive_range+front | 414.14 |

| Comparator | Mean of 14 source-level R5 − comparator contrasts |
|---|---:|
| D2 | -0.68 |
| A5b | -91.45 |
| economic_replacement | -8.17 |
| R:economic_stop | -80.48 |
| cams_adapter | -2.32 |
| gated_adaptive_range+front | -9.91 |

This replay covers economic replay only. It cannot establish genuine late-improvement transfer, application-level utility, an anytime guarantee, or independent generalization.
