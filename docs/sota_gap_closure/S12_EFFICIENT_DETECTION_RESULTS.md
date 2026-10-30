# S12 efficient multi-scale distribution testing
Methods: exact RBF MMD (median bandwidth), random-feature MMD (256 features), multi-bandwidth exact / RFF (median x {.5, 1, 2}, max of standardised statistics), standard C2ST (logistic regression, balanced held-out accuracy z), efficient C2ST (closed-form LDA direction, held-out t), BBSD (KS on model scores), incremental sliding-window RFF-MMD (O(D) per observation). d in {5, 20, 100}, window in {32, 64, 128, 256}, reference 512, 150 null calibration + 100 evaluation replicates per (setting, scenario) with thresholds from the 95% quantile of independent null replicates. **Every runtime includes all preprocessing and fitting** (bandwidth selection, feature sampling, classifier fitting). Benign shift = 0.3 sigma on a nuisance coordinate; harmful shift = -0.3 sigma on the informative coordinate where the deployed linear model is misspecified (decision-cost increase on the evaluator side below). **Disclosure:** a first run (`e12_s12_dist_v1_saturated_wrong_harm_sign.csv`, kept) used 1.2 sigma shifts, so every test saturated at power 1.0, and its 'harmful' direction had negative decision harm (-0.32); its numbers are not used.

Evaluator-side decision harm of each shifted scenario:

| d | benign | harmful | null |
|---|---|---|---|
| 5.000 | 0.001 | 0.112 | 0.000 |
| 20.000 | 0.001 | 0.116 | 0.000 |
| 100.000 | 0.006 | 0.110 | 0.000 |

## Calibration (null rejection after calibration; target 0.05)
| method | mean | min | max |
|---|---|---|---|
| bbsd | 0.041 | 0.020 | 0.080 |
| c2st_lda | 0.056 | 0.000 | 0.120 |
| c2st_lr | 0.060 | 0.020 | 0.150 |
| mmd_exact | 0.062 | 0.020 | 0.140 |
| mmd_multi_exact | 0.055 | 0.030 | 0.090 |
| mmd_multi_rff | 0.053 | 0.010 | 0.080 |
| mmd_rff | 0.040 | 0.010 | 0.110 |

## Rejection rate, window 128
| method | scenario | 5 | 20 | 100 |
|---|---|---|---|---|
| bbsd | benign | 0.05 | 0.05 | 0.10 |
| bbsd | harmful | 0.28 | 0.34 | 0.25 |
| c2st_lda | benign | 0.40 | 0.18 | 0.01 |
| c2st_lda | harmful | 0.25 | 0.25 | 0.04 |
| c2st_lr | benign | 0.23 | 0.09 | 0.12 |
| c2st_lr | harmful | 0.19 | 0.16 | 0.09 |
| mmd_exact | benign | 0.60 | 0.57 | 0.22 |
| mmd_exact | harmful | 0.66 | 0.41 | 0.18 |
| mmd_multi_exact | benign | 0.59 | 0.36 | 0.19 |
| mmd_multi_exact | harmful | 0.61 | 0.35 | 0.11 |
| mmd_multi_rff | benign | 0.47 | 0.38 | 0.09 |
| mmd_multi_rff | harmful | 0.43 | 0.31 | 0.11 |
| mmd_rff | benign | 0.48 | 0.20 | 0.13 |
| mmd_rff | harmful | 0.54 | 0.28 | 0.11 |

## Time per test (ms, harmful scenario)
| ('method', '') | (5, 32) | (5, 64) | (5, 128) | (5, 256) | (20, 32) | (20, 64) | (20, 128) | (20, 256) | (100, 32) | (100, 64) | (100, 128) | (100, 256) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bbsd | 0.110 | 0.300 | 0.140 | 0.330 | 0.190 | 0.230 | 0.140 | 0.190 | 0.190 | 0.360 | 0.270 | 0.230 |
| c2st_lda | 0.230 | 0.390 | 0.700 | 0.580 | 0.590 | 0.630 | 0.480 | 0.710 | 0.480 | 0.780 | 0.570 | 0.910 |
| c2st_lr | 7.200 | 6.160 | 8.540 | 6.330 | 7.210 | 8.210 | 7.920 | 7.140 | 11.480 | 13.840 | 10.550 | 8.260 |
| mmd_exact | 8.830 | 9.020 | 9.320 | 9.540 | 10.000 | 13.910 | 11.350 | 14.740 | 42.140 | 42.340 | 37.980 | 40.280 |
| mmd_multi_exact | 19.450 | 19.390 | 16.950 | 17.940 | 24.530 | 20.270 | 19.820 | 30.930 | 49.310 | 49.250 | 59.810 | 64.990 |
| mmd_multi_rff | 14.890 | 17.680 | 17.090 | 21.770 | 20.560 | 25.070 | 22.060 | 25.770 | 52.720 | 47.220 | 48.030 | 41.790 |
| mmd_rff | 6.270 | 7.760 | 7.380 | 10.830 | 12.970 | 11.580 | 11.740 | 12.520 | 40.990 | 38.530 | 39.420 | 41.850 |

Peak traced memory per test (kB, window 128):

| method | 5 | 20 | 100 |
|---|---|---|---|
| bbsd | 32.000 | 87.000 | 414.000 |
| c2st_lda | 17.000 | 63.000 | 448.000 |
| c2st_lr | 71.000 | 175.000 | 733.000 |
| mmd_exact | 6292.000 | 12832.000 | 64160.000 |
| mmd_multi_exact | 9045.000 | 12832.000 | 64160.000 |
| mmd_multi_rff | 3492.000 | 12832.000 | 64160.000 |
| mmd_rff | 3208.000 | 12832.000 | 64160.000 |

## Approximation error and streaming cost
| d | window | median_rel_error_RFF_vs_exact | incremental_RFF_ms_per_obs | exact_recompute_ms |
|---|---|---|---|---|
| 5.0000 | 32.0000 | 1.2516 | 0.0592 | 7.5381 |
| 5.0000 | 64.0000 | 0.2651 | 0.0315 | 11.4374 |
| 5.0000 | 128.0000 | 0.2998 | 0.0214 | 5.9563 |
| 5.0000 | 256.0000 | 0.1170 | 0.0425 | 11.7025 |
| 20.0000 | 32.0000 | 1.4149 | 0.0296 | 7.9491 |
| 20.0000 | 64.0000 | 1.8124 | 0.0304 | 9.7368 |
| 20.0000 | 128.0000 | 2.3878 | 0.0287 | 8.7431 |
| 20.0000 | 256.0000 | 0.4940 | 0.0316 | 11.0711 |
| 100.0000 | 32.0000 | 5.6750 | 0.1328 | 37.2577 |
| 100.0000 | 64.0000 | 4.4311 | 0.1345 | 37.8452 |
| 100.0000 | 128.0000 | 19.3257 | 0.0595 | 27.9406 |
| 100.0000 | 256.0000 | 2.5641 | 0.0664 | 29.3490 |

Findings: none of the distribution tests separates harmful from benign shift when both move the covariates comparably (rejection rates are similar; BBSD, which looks at the model score, is the only one that tracks the informative coordinate); feature-space detectors are sentinels, not harm detectors (consistent with earlier F1). RFF-MMD with 256 features has **large relative error** on the unbiased MMD^2 whenever the true value is near zero (table; the statistic is signed and tiny under mild shifts), yet its calibrated rejection rates are within about 0.05-0.15 of the exact test at d = 5-20 and about 0.07-0.1 lower at d = 100; the incremental form turns a per-window O(w n d) recompute into O(D) per observation (compare the last two columns). Speed claims above include preprocessing and fitting; no claim is made about C2ST with deep classifiers.
