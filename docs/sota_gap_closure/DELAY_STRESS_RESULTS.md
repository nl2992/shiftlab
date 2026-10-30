# Delay stress results (X01, X02)
False-alarm rate (alarm before the first harmful step; any alarm in a no-harm world), 2000 independent paths per cell (Wilson 95% half-width <= 0.02). Label rate 0.2, delay 5, alpha 0.05, repaired engine; `HG_arrived` = naive release, `HG_xcap_legacy` = earlier covariate-dependent cap.

| world | HG | HG_arrived | pprm | cost | HG 95% CI |
|---|---|---|---|---|---|
| X01|null|delay=fixed | 0.011 | 0.011 | 0.012 | 0.014 | [0.007, 0.017] |
| X01|null|delay=geometric | 0.013 | 0.013 | 0.018 | 0.011 | [0.008, 0.018] |
| X01|null|delay=uniform | 0.015 | 0.015 | 0.013 | 0.008 | [0.010, 0.021] |
| X02|null|delay=burst | 0.011 | 0.011 | 0.015 | 0.012 | [0.007, 0.017] |
| X02|null|delay=heavy | 0.004 | 0.013 | 0.007 | 0.007 | [0.002, 0.008] |
| X02|null|delay=outcome | 0.011 | 0.016 | 0.014 | 0.021 | [0.007, 0.017] |
| X02|null|delay=outcome_rev | 0.008 | 0.007 | 0.011 | 0.009 | [0.005, 0.013] |

No delay mechanism inflates the repaired HG beyond alpha. Naive arrived-subset release (`HG_arrived`) is not distinguishable here (largest difference: `delay=heavy`, 0.013 vs 0.004). Cost of validity: with in-order release a heavy-tailed pending queue blocks the prefix (head-of-line blocking). Power under the six delay models on a harmful concept shift (`scripts/gap/e5_s06_pacing.py` and `pools.g6_specs`) is reported in `FINAL_SYNTHETIC_CONFIRMATION_RESULTS.md`.
