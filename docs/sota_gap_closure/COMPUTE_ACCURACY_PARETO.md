# Compute vs accuracy
Machine: {'machine': 'x86_64', 'python': '3.13.17', 'nproc': 4}. Five repeats per case; `cold_s` = first call in the process, `warm_s` = median of the remaining calls (sd given). Stream generation cost is separate (`RUNTIME_SCALING.csv`, column `gen_s`) and excluded from detector time; "model fitting" is zero for the e-processes (plug-in Kelly bets), included inside every drift-test timing; "policy construction" for allocation rules is inside the engine loop. Memory: `tracemalloc` peak of numpy allocations per call (`MEMORY_TRACEMALLOC.csv`) and clean-process peak RSS (`MEMORY_SCALING.csv`).

## Base case (T=2000, S=100, 10% labels)
| method | cold_s | warm_s | warm_sd_s | us_per_obs | tracemalloc_peak_mb |
|---|---|---|---|---|---|
| pprm_parent(engine) | 0.1614 | 0.1563 | 0.0274 | 0.7813 | 17.3157 |
| HG | 0.2173 | 0.2120 | 0.0153 | 1.0598 | 22.1244 |
| discount_only | 0.1584 | 0.1619 | 0.0048 | 0.8095 | 17.3158 |
| costgate_only | 0.2278 | 0.2046 | 0.0265 | 1.0229 | 22.1245 |
| multiwindow(3) | 0.6814 | 0.6320 | 0.0235 | 3.1602 | 23.7409 |
| HG_growth_alloc | 0.6095 | 0.6033 | 0.0159 | 3.0167 | 71.9523 |
| HG_robustmix | 0.6189 | 0.6245 | 0.0736 | 3.1227 | 71.9542 |
| cost_discount | 0.1894 | 0.1829 | 0.0244 | 0.9144 | 17.3158 |
| HG_lrv100 | 0.4059 | 0.3978 | 0.0116 | 1.9891 | 22.5256 |
| pprm_tight(legacy cumsum) | 0.0127 | 0.0127 | 0.0015 | 0.0634 | 19.2197 |
| HG(legacy cumsum) | 0.0417 | 0.0389 | 0.0024 | 0.1947 | 33.6042 |
| page_hinkley | 0.0169 | 0.0152 | 0.0001 | 0.0761 | 6.6016 |
| cusum | 0.0153 | 0.0150 | 0.0006 | 0.0749 | 6.6016 |

Warm time (s) vs horizon T (S=100):
| method | 500.0 | 2000.0 | 8000.0 |
|---|---|---|---|
| HG | 0.0622 | 0.2120 | 0.8577 |
| HG(legacy cumsum) | 0.0089 | 0.0389 | 0.1966 |
| HG_growth_alloc | 0.1403 | 0.6033 | 2.4160 |
| HG_lrv100 | 0.0894 | 0.3978 | 1.5894 |
| HG_robustmix | 0.1591 | 0.6245 | 2.7030 |
| cost_discount | 0.0424 | 0.1829 | 0.7102 |
| costgate_only | 0.0520 | 0.2046 | 0.8545 |
| cusum | 0.0040 | 0.0150 | 0.0717 |
| discount_only | 0.0416 | 0.1619 | 0.7436 |
| multiwindow(3) | 0.1605 | 0.6320 | 2.5337 |
| page_hinkley | 0.0039 | 0.0152 | 0.0682 |
| pprm_parent(engine) | 0.0411 | 0.1563 | 0.6675 |
| pprm_tight(legacy cumsum) | 0.0025 | 0.0127 | 0.0474 |

vs number of parallel streams S (T=2000):
| method | 1.0 | 100.0 | 1000.0 |
|---|---|---|---|
| HG | 0.1944 | 0.2120 | 0.6084 |
| HG(legacy cumsum) | 0.0128 | 0.0389 | 0.4089 |
| HG_growth_alloc | 0.4130 | 0.6033 | 1.8098 |
| HG_lrv100 | 0.2362 | 0.3978 | 2.2525 |
| HG_robustmix | 0.5538 | 0.6245 | 1.8805 |
| cost_discount | 0.1668 | 0.1829 | 0.4720 |
| costgate_only | 0.1716 | 0.2046 | 0.5515 |
| cusum | 0.0094 | 0.0150 | 0.0634 |
| discount_only | 0.1617 | 0.1619 | 0.4630 |
| multiwindow(3) | 0.5750 | 0.6320 | 1.6988 |
| page_hinkley | 0.0098 | 0.0152 | 0.0634 |
| pprm_parent(engine) | 0.1296 | 0.1563 | 0.4237 |
| pprm_tight(legacy cumsum) | 0.0005 | 0.0127 | 0.1559 |

vs label fraction (T=2000, S=100):
| method | 0.01 | 0.1 | 0.5 |
|---|---|---|---|
| HG | 0.2288 | 0.2120 | 0.2111 |
| HG(legacy cumsum) | 0.0368 | 0.0389 | 0.0374 |
| HG_growth_alloc | 0.7680 | 0.6033 | 0.5854 |
| HG_lrv100 | 0.3745 | 0.3978 | 0.3513 |
| HG_robustmix | 0.6105 | 0.6245 | 0.6183 |
| cost_discount | 0.1600 | 0.1829 | 0.1532 |
| costgate_only | 0.2019 | 0.2046 | 0.2257 |
| cusum | 0.0139 | 0.0150 | 0.0168 |
| discount_only | 0.1661 | 0.1619 | 0.1560 |
| multiwindow(3) | 0.6075 | 0.6320 | 0.7468 |
| page_hinkley | 0.0172 | 0.0152 | 0.0159 |
| pprm_parent(engine) | 0.1793 | 0.1563 | 0.1541 |
| pprm_tight(legacy cumsum) | 0.0104 | 0.0127 | 0.0114 |

Certification methods vs number of models K (50 streams, T=2000), warm s:
| method | 2.0 | 5.0 | 10.0 |
|---|---|---|---|
| S09d_budget | 0.2306 | 0.1663 | 0.2154 |
| cams | 0.1100 | 0.1436 | 0.1301 |
| paired_e_bonf | 0.0831 | 0.1033 | 0.1302 |
| seqmcs | 0.1694 | 0.3045 | 0.6501 |

Drift tests vs feature dimension d (window 128), warm s per test:
| method | 5.0 | 20.0 | 100.0 |
|---|---|---|---|
| bbsd | 0.00006 | 0.00005 | 0.00007 |
| c2st_lda | 0.00007 | 0.00012 | 0.00039 |
| c2st_lr | 0.00171 | 0.00299 | 0.00415 |
| mmd_exact | 0.00475 | 0.00791 | 0.02253 |
| mmd_multi_exact | 0.01220 | 0.01670 | 0.02999 |
| mmd_multi_rff | 0.01528 | 0.01416 | 0.02676 |
| mmd_rff | 0.00560 | 0.00718 | 0.02200 |

Approximate DP (exact RPOQ solver with wealth snapping), seconds:
| method | T | cold_s | warm_s | warm_sd_s |
|---|---|---|---|---|
| approx_dp(delta=.25) | 6.000 | 0.106 | 0.111 | 0.001 |
| approx_dp(delta=.25) | 8.000 | 0.308 | 0.377 | 0.051 |
| approx_dp(delta=.25) | 10.000 | 0.639 | 0.722 | 0.099 |

Peak RSS in a clean process (MB):
| method | T | S | peak_rss_mb |
|---|---|---|---|
| pprm | 500 | 100 | 1169.4 |
| HG | 500 | 100 | 1169.4 |
| pprm | 2000 | 100 | 1169.4 |
| HG | 2000 | 100 | 1169.4 |
| pprm | 8000 | 100 | 1169.4 |
| HG | 8000 | 100 | 1169.4 |
| pprm | 2000 | 1 | 1169.4 |
| HG | 2000 | 1 | 1169.4 |
| pprm | 2000 | 1000 | 1169.4 |
| HG | 2000 | 1000 | 1169.4 |

## Compute / accuracy (confirmation pools, 20% labels; runtime: engine, T=2000, S=100, 10% labels; PH and CUSUM timed with their vectorised legacy implementation)
| index | us_per_obs | power_conf | FA_null_conf | pareto (power up, time down) |
|---|---|---|---|---|
| pprm_parent(engine) | 0.781 | 0.756 | 0.042 | False |
| HG | 1.060 | 0.808 | 0.045 | False |
| cost_discount | 0.914 | 0.759 | 0.047 | False |
| HG_robustmix | 3.123 | 0.803 | 0.035 | False |
| HG_lrv100 | 1.989 | 0.763 | 0.009 | False |
| page_hinkley | 0.076 | 0.918 | 0.045 | True |
| cusum | 0.075 | 0.847 | 0.049 | True |

Caution: the event-level engine loops over time, the legacy detectors use cumulative sums; compare within an implementation style, not across. PH / CUSUM have no validity guarantee (empirical thresholds); only the engine rows carry the e-process guarantee under its null.
