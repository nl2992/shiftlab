# Contextual weighted-alpha robustness development grid

Status: **development_only_no_independent_calibration_or_confirmation**; 324,000 stream-method rows; 2,916 paired contrasts; device cuda; 200 seeds per cell.

The grid stresses context-local promotion and rollback as the harmful latent context becomes rare, the learner-visible proxy label becomes noisy, intervention costs vary, and the shared hard label budget changes. The learner sees only the proxy context. An independent pre-stream pilot contains proxy labels but no outcomes; alpha weights are fixed from that pilot before testing. The evaluator alone knows the latent context and scores expected utility.

## Allocation method

Each group runs the existing bounded anytime e-process. For fixed pilot-measurable weights `w_j >= 0` summing to one, group `j` receives `alpha*w_j`; promotion and rollback split each group's allocation in half. Ville's inequality and a union bound give familywise error at most alpha across groups within each stage. Pilot-based, outcome-independent weights preserve that guarantee conditional on the pilot, assuming each group's bounded conditional-mean null and predictable query mechanism. Equal, proxy-volume-weighted, and inverse-volume (rare-protected) allocations are standard weighted Bonferroni comparators, not new tests.

## Heterogeneous reversal at unit intervention cost and 40% label cap

The table reports means over seeds for each truth prevalence and proxy error. It is a development slice, not a selected confirmation result.

|   true_harmful_prevalence |   proxy_error_rate | method                |   expected_utility |   realized_utility |   harmful_rollbacks |   safe_retained |   mean_labels |
|--------------------------:|-------------------:|:----------------------|-------------------:|-------------------:|--------------------:|----------------:|--------------:|
|                     0.050 |              0.000 | equal_alpha           |            148.756 |            151.716 |               0.000 |           1.000 |       319.365 |
|                     0.050 |              0.000 | global_gate           |            139.350 |            142.030 |               0.000 |           1.000 |       320.000 |
|                     0.050 |              0.000 | rare_protected_alpha  |            147.997 |            150.587 |               0.000 |           0.995 |       319.365 |
|                     0.050 |              0.000 | volume_weighted_alpha |            148.756 |            151.716 |               0.000 |           1.000 |       319.365 |
|                     0.050 |              0.050 | equal_alpha           |            140.609 |            143.465 |               0.000 |           1.000 |       318.160 |
|                     0.050 |              0.050 | global_gate           |            139.350 |            143.380 |               0.000 |           1.000 |       319.990 |
|                     0.050 |              0.050 | rare_protected_alpha  |            140.581 |            143.364 |               0.000 |           1.000 |       318.160 |
|                     0.050 |              0.050 | volume_weighted_alpha |            140.692 |            143.768 |               0.000 |           1.000 |       318.135 |
|                     0.050 |              0.100 | equal_alpha           |            133.218 |            133.137 |               0.000 |           1.185 |       318.360 |
|                     0.050 |              0.100 | global_gate           |            139.350 |            138.850 |               0.000 |           2.000 |       320.000 |
|                     0.050 |              0.100 | rare_protected_alpha  |            133.920 |            133.701 |               0.000 |           1.290 |       318.420 |
|                     0.050 |              0.100 | volume_weighted_alpha |            132.383 |            132.765 |               0.000 |           1.060 |       318.230 |
|                     0.250 |              0.000 | equal_alpha           |             88.757 |             90.637 |               0.010 |           1.000 |       319.245 |
|                     0.250 |              0.000 | global_gate           |             69.750 |             72.130 |               0.000 |           1.000 |       320.000 |
|                     0.250 |              0.000 | rare_protected_alpha  |             86.552 |             88.679 |               0.015 |           1.000 |       319.285 |
|                     0.250 |              0.000 | volume_weighted_alpha |             91.822 |             93.792 |               0.000 |           1.000 |       319.195 |
|                     0.250 |              0.050 | equal_alpha           |             80.757 |             78.020 |               0.000 |           0.995 |       319.545 |
|                     0.250 |              0.050 | global_gate           |             69.750 |             67.030 |               0.000 |           1.000 |       320.000 |
|                     0.250 |              0.050 | rare_protected_alpha  |             78.653 |             76.097 |               0.010 |           0.990 |       319.590 |
|                     0.250 |              0.050 | volume_weighted_alpha |             85.598 |             83.320 |               0.000 |           0.995 |       319.195 |
|                     0.250 |              0.100 | equal_alpha           |             76.200 |             72.695 |               0.015 |           1.000 |       319.400 |
|                     0.250 |              0.100 | global_gate           |             69.750 |             66.580 |               0.000 |           1.000 |       320.000 |
|                     0.250 |              0.100 | rare_protected_alpha  |             75.147 |             71.680 |               0.015 |           1.000 |       319.320 |
|                     0.250 |              0.100 | volume_weighted_alpha |             77.378 |             73.599 |               0.005 |           1.000 |       319.305 |
|                     0.500 |              0.000 | equal_alpha           |            -10.394 |            -11.735 |               0.115 |           0.965 |       315.780 |
|                     0.500 |              0.000 | global_gate           |            -17.051 |            -18.616 |               0.020 |           0.980 |       317.490 |
|                     0.500 |              0.000 | rare_protected_alpha  |            -10.406 |            -11.760 |               0.115 |           0.965 |       315.795 |
|                     0.500 |              0.000 | volume_weighted_alpha |            -10.368 |            -11.710 |               0.115 |           0.965 |       315.730 |
|                     0.500 |              0.050 | equal_alpha           |            -11.438 |             -9.403 |               0.080 |           0.975 |       317.210 |
|                     0.500 |              0.050 | global_gate           |            -17.112 |            -15.743 |               0.010 |           0.990 |       318.245 |
|                     0.500 |              0.050 | rare_protected_alpha  |            -11.173 |             -9.202 |               0.085 |           0.975 |       317.085 |
|                     0.500 |              0.050 | volume_weighted_alpha |            -11.449 |             -9.428 |               0.080 |           0.975 |       317.235 |
|                     0.500 |              0.100 | equal_alpha           |            -14.513 |            -13.733 |               0.085 |           0.950 |       316.755 |
|                     0.500 |              0.100 | global_gate           |            -17.048 |            -16.189 |               0.015 |           0.985 |       318.315 |
|                     0.500 |              0.100 | rare_protected_alpha  |            -14.513 |            -13.733 |               0.085 |           0.950 |       316.765 |
|                     0.500 |              0.100 | volume_weighted_alpha |            -14.511 |            -13.728 |               0.085 |           0.950 |       316.750 |

`harmful_rollbacks` and `safe_retained` are mean counts of proxy strata per stream (maximum two), not proportions.

## Direct allocation comparison

For volume-weighted alpha minus equal alpha in heterogeneous reversal, the unadjusted per-cell paired mean was positive in 68.5% of cells, with median 0.42 and range [-0.43, 5.60]. The intervals are unadjusted across the grid, so they are exploratory rather than selection-adjusted superiority tests.

Across the full heterogeneous-reversal grid, the rare-protected allocation's paired contrast against the global gate ranged from -20.58 to 22.94 utility units (unadjusted per-cell seed-bootstrap intervals, 1000 replicates). These exploratory intervals do not correct for grid selection.

No null calibration or independent confirmation is claimed. The global gate is a utility comparator under context-dependent gains; the per-context methods are the procedures whose stagewise familywise control follows from the stated weighted Bonferroni construction. A changed proxy model, context partition, or selected allocation requires fresh calibration on independent streams before error-control claims.

No figure was generated. Any future research visual must be made with PaperBanana and checked against the saved metrics.
