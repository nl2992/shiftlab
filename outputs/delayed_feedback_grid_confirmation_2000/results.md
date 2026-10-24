# Delayed decision-harm factorial confirmation

This alternative-only grid contains 12 cells and 2000 paired seeds per cell.
It varies query rate, harm onset and expected paired-cost increase, with CUDA stream generation
and independent uniform label delays from zero through six. Seeds are reused across cells as
common random numbers; they are paired within cell across the three registered e-processes.

- Seed interval per cell: 20270000–20271999.
- Resolved generation device: cuda.
- Primary cellwise contrast: restart mixture versus full-stream betting.
- Cellwise paired p-values: exact two-sided McNemar; familywise adjustment: Holm across 12 cells.
- Tiny p-values and Holm values are computed on the log scale to avoid numerical underflow.
- Marginal detection intervals: exact two-sided 95% Clopper–Pearson, reported per cell.

## Detection rates and censored-delay summaries

|   query_rate |   harm_onset_fraction |   harm_contrast_increase | method               |   detected |   streams |   detection_rate |   cp95_lower |   cp95_upper |   mean_event_delay_given_detection |   mean_wall_delay_given_detection |
|-------------:|----------------------:|-------------------------:|:---------------------|-----------:|----------:|-----------------:|-------------:|-------------:|-----------------------------------:|----------------------------------:|
|       0.1000 |                0.2000 |                   0.1200 | paired_cost_eprocess |          1 |      2000 |           0.0005 |       0.0000 |       0.0028 |                          2116.0000 |                         2122.0000 |
|       0.1000 |                0.2000 |                   0.1200 | paired_cost_betting  |        632 |      2000 |           0.3160 |       0.2957 |       0.3369 |                          1604.9652 |                         1608.0791 |
|       0.1000 |                0.2000 |                   0.1200 | restart_mixture_8    |        894 |      2000 |           0.4470 |       0.4251 |       0.4691 |                          1535.8915 |                         1539.0459 |
|       0.1000 |                0.2000 |                   0.2400 | paired_cost_eprocess |        380 |      2000 |           0.1900 |       0.1730 |       0.2079 |                          2139.6105 |                         2142.7079 |
|       0.1000 |                0.2000 |                   0.2400 | paired_cost_betting  |       1954 |      2000 |           0.9770 |       0.9694 |       0.9831 |                          1093.0169 |                         1096.1720 |
|       0.1000 |                0.2000 |                   0.2400 | restart_mixture_8    |       1989 |      2000 |           0.9945 |       0.9902 |       0.9973 |                           873.7345 |                          876.7396 |
|       0.1000 |                0.6000 |                   0.1200 | paired_cost_eprocess |          0 |      2000 |           0.0000 |       0.0000 |       0.0018 |                           nan      |                          nan      |
|       0.1000 |                0.6000 |                   0.1200 | paired_cost_betting  |         37 |      2000 |           0.0185 |       0.0131 |       0.0254 |                           843.9459 |                          847.1622 |
|       0.1000 |                0.6000 |                   0.1200 | restart_mixture_8    |        287 |      2000 |           0.1435 |       0.1284 |       0.1596 |                           803.9965 |                          806.9617 |
|       0.1000 |                0.6000 |                   0.2400 | paired_cost_eprocess |          1 |      2000 |           0.0005 |       0.0000 |       0.0028 |                           933.0000 |                          935.0000 |
|       0.1000 |                0.6000 |                   0.2400 | paired_cost_betting  |        514 |      2000 |           0.2570 |       0.2380 |       0.2767 |                           916.1848 |                          919.2412 |
|       0.1000 |                0.6000 |                   0.2400 | restart_mixture_8    |       1667 |      2000 |           0.8335 |       0.8164 |       0.8496 |                           690.0474 |                          693.0792 |
|       0.2500 |                0.2000 |                   0.1200 | paired_cost_eprocess |        158 |      2000 |           0.0790 |       0.0676 |       0.0917 |                          2054.4684 |                         2057.7215 |
|       0.2500 |                0.2000 |                   0.1200 | paired_cost_betting  |       1469 |      2000 |           0.7345 |       0.7146 |       0.7537 |                          1441.9544 |                         1445.3172 |
|       0.2500 |                0.2000 |                   0.1200 | restart_mixture_8    |       1757 |      2000 |           0.8785 |       0.8634 |       0.8925 |                          1257.9129 |                         1261.2368 |
|       0.2500 |                0.2000 |                   0.2400 | paired_cost_eprocess |       1993 |      2000 |           0.9965 |       0.9928 |       0.9986 |                          1327.0908 |                         1330.3864 |
|       0.2500 |                0.2000 |                   0.2400 | paired_cost_betting  |       1972 |      2000 |           0.9860 |       0.9798 |       0.9907 |                           614.4113 |                          617.7546 |
|       0.2500 |                0.2000 |                   0.2400 | restart_mixture_8    |       1996 |      2000 |           0.9980 |       0.9949 |       0.9995 |                           442.4148 |                          445.8507 |
|       0.2500 |                0.6000 |                   0.1200 | paired_cost_eprocess |          0 |      2000 |           0.0000 |       0.0000 |       0.0018 |                           nan      |                          nan      |
|       0.2500 |                0.6000 |                   0.1200 | paired_cost_betting  |         99 |      2000 |           0.0495 |       0.0404 |       0.0599 |                           907.2121 |                          910.3333 |
|       0.2500 |                0.6000 |                   0.1200 | restart_mixture_8    |        900 |      2000 |           0.4500 |       0.4280 |       0.4721 |                           760.1344 |                          763.5444 |
|       0.2500 |                0.6000 |                   0.2400 | paired_cost_eprocess |        124 |      2000 |           0.0620 |       0.0518 |       0.0735 |                          1053.7984 |                         1057.0161 |
|       0.2500 |                0.6000 |                   0.2400 | paired_cost_betting  |       1391 |      2000 |           0.6955 |       0.6748 |       0.7156 |                           861.0288 |                          864.3480 |
|       0.2500 |                0.6000 |                   0.2400 | restart_mixture_8    |       1989 |      2000 |           0.9945 |       0.9902 |       0.9973 |                           401.9316 |                          405.2574 |
|       0.5000 |                0.2000 |                   0.1200 | paired_cost_eprocess |       1032 |      2000 |           0.5160 |       0.4938 |       0.5381 |                          1839.6328 |                         1843.2393 |
|       0.5000 |                0.2000 |                   0.1200 | paired_cost_betting  |       1929 |      2000 |           0.9645 |       0.9554 |       0.9722 |                          1151.9383 |                         1155.5345 |
|       0.5000 |                0.2000 |                   0.1200 | restart_mixture_8    |       1988 |      2000 |           0.9940 |       0.9895 |       0.9969 |                           860.8934 |                          864.5171 |
|       0.5000 |                0.2000 |                   0.2400 | paired_cost_eprocess |       2000 |      2000 |           1.0000 |       0.9982 |       1.0000 |                           780.8510 |                          784.4100 |
|       0.5000 |                0.2000 |                   0.2400 | paired_cost_betting  |       1965 |      2000 |           0.9825 |       0.9757 |       0.9878 |                           421.1573 |                          424.7679 |
|       0.5000 |                0.2000 |                   0.2400 | restart_mixture_8    |       1996 |      2000 |           0.9980 |       0.9949 |       0.9995 |                           287.4925 |                          291.0426 |
|       0.5000 |                0.6000 |                   0.1200 | paired_cost_eprocess |          1 |      2000 |           0.0005 |       0.0000 |       0.0028 |                          1141.0000 |                         1145.0000 |
|       0.5000 |                0.6000 |                   0.1200 | paired_cost_betting  |        288 |      2000 |           0.1440 |       0.1289 |       0.1602 |                           924.9514 |                          928.5104 |
|       0.5000 |                0.6000 |                   0.1200 | restart_mixture_8    |       1656 |      2000 |           0.8280 |       0.8107 |       0.8443 |                           674.1123 |                          677.6117 |
|       0.5000 |                0.6000 |                   0.2400 | paired_cost_eprocess |        953 |      2000 |           0.4765 |       0.4544 |       0.4987 |                          1004.4029 |                         1008.0252 |
|       0.5000 |                0.6000 |                   0.2400 | paired_cost_betting  |       1921 |      2000 |           0.9605 |       0.9510 |       0.9686 |                           724.9563 |                          728.5289 |
|       0.5000 |                0.6000 |                   0.2400 | restart_mixture_8    |       1991 |      2000 |           0.9955 |       0.9915 |       0.9979 |                           238.9191 |                          242.4897 |

## Paired restart-mixture contrasts

|   query_rate |   harm_onset_fraction |   harm_contrast_increase |   restart_only |   betting_only |   discordant_pairs | mcnemar_exact_two_sided_p   |   mcnemar_log10_p |   holm_adjusted_log10_p | holm_adjusted_p        |
|-------------:|----------------------:|-------------------------:|---------------:|---------------:|-------------------:|:----------------------------|------------------:|------------------------:|:-----------------------|
|         0.1  |                   0.2 |                     0.12 |            326 |             64 |                390 | 2.19e-43                    |          -42.66   |                -41.881  | 1.314e-42              |
|         0.1  |                   0.2 |                     0.24 |             38 |              3 |                 41 | 1.048e-08                   |           -7.9797 |                 -7.6244 | 2.375e-08              |
|         0.1  |                   0.6 |                     0.12 |            256 |              6 |                262 | 1.172e-67                   |          -66.931  |                -66.086  | 8.202e-67              |
|         0.1  |                   0.6 |                     0.24 |           1160 |              7 |               1167 | <1e-300 (log10=-333.2)      |         -333.24   |               -332.2    | <1e-300 (log10=-332.2) |
|         0.25 |                   0.2 |                     0.12 |            303 |             15 |                318 | 7.407e-71                   |          -70.13   |                -69.227  | 5.926e-70              |
|         0.25 |                   0.2 |                     0.24 |             26 |              2 |                 28 | 3.032e-06                   |           -5.5182 |                 -5.5182 | 3.032e-06              |
|         0.25 |                   0.6 |                     0.12 |            808 |              7 |                815 | 4.264e-229                  |         -228.37   |               -227.37   | 4.264e-228             |
|         0.25 |                   0.6 |                     0.24 |            606 |              8 |                614 | 1.427e-167                  |         -166.85   |               -165.89   | 1.284e-166             |
|         0.5  |                   0.2 |                     0.12 |             61 |              2 |                 63 | 4.374e-16                   |          -15.359  |                -14.757  | 1.749e-15              |
|         0.5  |                   0.2 |                     0.24 |             32 |              1 |                 33 | 7.916e-09                   |           -8.1015 |                 -7.6244 | 2.375e-08              |
|         0.5  |                   0.6 |                     0.12 |           1370 |              2 |               1372 | <1e-300 (log10=-406.7)      |         -406.74   |               -405.66   | <1e-300 (log10=-405.7) |
|         0.5  |                   0.6 |                     0.24 |             75 |              5 |                 80 | 4.253e-17                   |          -16.371  |                -15.672  | 2.126e-16              |

This factorial confirmation supports comparisons only over the registered synthetic conditions.
The e-process guarantees still require the stated eventwise conditional-mean null, bounded
contrasts, predictable queries, and outcome-independent delays. Delay means are conditional on
detection and nondetections remain censored. No new algorithm or universal superiority claim is
made. No figure is included because project guidance requires PaperBanana for visuals and that
tool is unavailable in this session.
