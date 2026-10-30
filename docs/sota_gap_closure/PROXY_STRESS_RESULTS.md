# Proxy stress results (X07 and G5)
False-alarm rate (alarm before the first harmful step; any alarm in a no-harm world), 2000 independent paths per cell (Wilson 95% half-width <= 0.02). Label rate 0.2, delay 5, alpha 0.05, repaired engine; `HG_arrived` = naive release, `HG_xcap_legacy` = earlier covariate-dependent cap.

| world | HG | pprm | cost | HG 95% CI |
|---|---|---|---|---|
| X07|null|proxy=anti | 0.025 | 0.018 | 0.021 | [0.019, 0.033] |
| X07|null|proxy=calibration | 0.025 | 0.021 | 0.021 | [0.019, 0.033] |
| X07|null|proxy=static_bias | 0.025 | 0.025 | 0.023 | [0.019, 0.032] |

The unbiasedness of the IPW correction is proxy-free, so severe or anti-informative proxies do not break size (all <= 0.03). They cost power only: `outputs/gap_closure/e2b_s03_sensitivity` shows HG at 10% labels falling from 0.78 (accurate) to 0.67 (fully anti-informative after the shift); S03's reliability adaptation did not recover it (`S03_RESULTS.md`).
