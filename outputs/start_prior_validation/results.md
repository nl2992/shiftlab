# Fresh validation of the frozen center start-time prior

The center Beta(2,2) prior was chosen using the disjoint development block and frozen before these runs. It is compared with the uniform eight-start mixture on independent null and paired alternative seed blocks.

- Null seeds: 20274000–20275999 per scenario.
- Alternative seeds: 20276000–20277999 per cell.
- Generator device(s): cuda.
- Alternative inference: exact paired two-sided McNemar tests with Holm adjustment across 12 cells.
- Null bounds: one-sided exact Clopper–Pearson, simultaneous 95% Bonferroni coverage over 12 cells.

## Null calibration

| scenario              |   query_rate | method                |   false_escalations |   streams |   false_escalation_rate |   simultaneous_cp95_upper |
|:----------------------|-------------:|:----------------------|--------------------:|----------:|------------------------:|--------------------------:|
| benign_variance_shift |      0.10000 | center_restart_beta22 |                   3 |      2000 |                 0.00150 |                   0.00560 |
| benign_variance_shift |      0.10000 | uniform_restart_8     |                   4 |      2000 |                 0.00200 |                   0.00641 |
| benign_variance_shift |      0.25000 | center_restart_beta22 |                   9 |      2000 |                 0.00450 |                   0.01013 |
| benign_variance_shift |      0.25000 | uniform_restart_8     |                  12 |      2000 |                 0.00600 |                   0.01220 |
| benign_variance_shift |      0.50000 | center_restart_beta22 |                   7 |      2000 |                 0.00350 |                   0.00869 |
| benign_variance_shift |      0.50000 | uniform_restart_8     |                   6 |      2000 |                 0.00300 |                   0.00795 |
| stationary            |      0.10000 | center_restart_beta22 |                  17 |      2000 |                 0.00850 |                   0.01553 |
| stationary            |      0.10000 | uniform_restart_8     |                  14 |      2000 |                 0.00700 |                   0.01355 |
| stationary            |      0.25000 | center_restart_beta22 |                  16 |      2000 |                 0.00800 |                   0.01487 |
| stationary            |      0.25000 | uniform_restart_8     |                  18 |      2000 |                 0.00900 |                   0.01618 |
| stationary            |      0.50000 | center_restart_beta22 |                  16 |      2000 |                 0.00800 |                   0.01487 |
| stationary            |      0.50000 | uniform_restart_8     |                  13 |      2000 |                 0.00650 |                   0.01288 |

## Paired alternative confirmation

|   query_rate |   harm_onset_fraction |   harm_contrast_increase |   center_detected |   uniform_detected |   streams |   center_rate |   uniform_rate |   rate_difference |   center_only |   uniform_only |   mcnemar_p |   holm_adjusted_p |
|-------------:|----------------------:|-------------------------:|------------------:|-------------------:|----------:|--------------:|---------------:|------------------:|--------------:|---------------:|------------:|------------------:|
|         0.1  |                   0.2 |                     0.12 |               900 |                876 |      2000 |        0.45   |         0.438  |            0.012  |            36 |             12 |   0.0007173 |         0.005738  |
|         0.1  |                   0.2 |                     0.24 |              1992 |               1991 |      2000 |        0.996  |         0.9955 |            0.0005 |             1 |              0 |   1         |         1         |
|         0.1  |                   0.6 |                     0.12 |               327 |                296 |      2000 |        0.1635 |         0.148  |            0.0155 |            40 |              9 |   9.264e-06 |         9.264e-05 |
|         0.1  |                   0.6 |                     0.24 |              1700 |               1667 |      2000 |        0.85   |         0.8335 |            0.0165 |            39 |              6 |   5.418e-07 |         5.96e-06  |
|         0.25 |                   0.2 |                     0.12 |              1797 |               1783 |      2000 |        0.8985 |         0.8915 |            0.007  |            19 |              5 |   0.006611  |         0.04628   |
|         0.25 |                   0.2 |                     0.24 |              1996 |               1996 |      2000 |        0.998  |         0.998  |            0      |             0 |              0 |   1         |         1         |
|         0.25 |                   0.6 |                     0.12 |               940 |                889 |      2000 |        0.47   |         0.4445 |            0.0255 |            64 |             13 |   3.024e-09 |         3.628e-08 |
|         0.25 |                   0.6 |                     0.24 |              1985 |               1986 |      2000 |        0.9925 |         0.993  |           -0.0005 |             0 |              1 |   1         |         1         |
|         0.5  |                   0.2 |                     0.12 |              1993 |               1986 |      2000 |        0.9965 |         0.993  |            0.0035 |             7 |              0 |   0.01563   |         0.09375   |
|         0.5  |                   0.2 |                     0.24 |              1997 |               1994 |      2000 |        0.9985 |         0.997  |            0.0015 |             3 |              0 |   0.25      |         1         |
|         0.5  |                   0.6 |                     0.12 |              1690 |               1671 |      2000 |        0.845  |         0.8355 |            0.0095 |            24 |              5 |   0.0005461 |         0.004915  |
|         0.5  |                   0.6 |                     0.24 |              1987 |               1988 |      2000 |        0.9935 |         0.994  |           -0.0005 |             3 |              4 |   1         |         1         |

This validates finite-sample behavior only for the registered synthetic generator, bounded contrasts, predictable label query masks and outcome-independent delays. It does not cover serial dependence, informative query/delay mechanisms, or deployment-induced outcomes. A non-significant or mixed comparison retains the uniform mixture. No figure is generated; future visuals must use PaperBanana.
