# Null stress results (X01-X14)
False-alarm rate (alarm before the first harmful step; any alarm in a no-harm world), 2000 independent paths per cell (Wilson 95% half-width <= 0.02). Label rate 0.2, delay 5, alpha 0.05, repaired engine; `HG_arrived` = naive release, `HG_xcap_legacy` = earlier covariate-dependent cap.

| world | HG | HG_arrived | HG_xcap_legacy | pprm | cost | HG 95% CI | exceeds_alpha_HG | exceeds_alpha_pprm | exceeds_alpha_cost |
|---|---|---|---|---|---|---|---|---|---|
| G3|K2_null | 0.018 | 0.018 | 0.018 | 0.016 | 0.019 | [0.013, 0.025] | no | no | no |
| G4|fin_null | 0.089 | 0.094 | 0.104 | 0.130 | 0.030 | [0.077, 0.102] | YES | YES | no |
| X01|null|delay=fixed | 0.011 | 0.011 | 0.009 | 0.012 | 0.014 | [0.007, 0.017] | no | no | no |
| X01|null|delay=geometric | 0.013 | 0.013 | 0.014 | 0.018 | 0.011 | [0.008, 0.018] | no | no | no |
| X01|null|delay=uniform | 0.015 | 0.015 | 0.014 | 0.013 | 0.008 | [0.010, 0.021] | no | no | no |
| X02|null|delay=burst | 0.011 | 0.011 | 0.010 | 0.015 | 0.012 | [0.007, 0.017] | no | no | no |
| X02|null|delay=heavy | 0.004 | 0.013 | 0.004 | 0.007 | 0.007 | [0.002, 0.008] | no | no | no |
| X02|null|delay=outcome | 0.011 | 0.016 | 0.007 | 0.014 | 0.021 | [0.007, 0.017] | no | no | no |
| X02|null|delay=outcome_rev | 0.008 | 0.007 | 0.008 | 0.011 | 0.009 | [0.005, 0.013] | no | no | no |
| X03|null|ar0.5_s1.0 | 0.015 | 0.014 | 0.013 | 0.019 | 0.014 | [0.010, 0.021] | no | no | no |
| X03|null|ar0.98_s1.5 | 0.038 | 0.038 | 0.038 | 0.019 | 0.044 | [0.031, 0.048] | no | no | no |
| X03|null|ar0.9_s1.0 | 0.016 | 0.015 | 0.015 | 0.013 | 0.018 | [0.011, 0.022] | no | no | no |
| X04|null|cluster100_s1.5 | 0.088 | 0.088 | 0.087 | 0.052 | 0.055 | [0.076, 0.101] | YES | no | no |
| X04|null|cluster20_s1.0 | 0.013 | 0.013 | 0.013 | 0.012 | 0.013 | [0.009, 0.019] | no | no | no |
| X04|null|cluster400_s1.5 | 0.190 | 0.190 | 0.188 | 0.121 | 0.163 | [0.173, 0.208] | YES | YES | YES |
| X05|null|adaptive_neg | 0.022 | 0.022 | 0.018 | 0.015 | 0.015 | [0.016, 0.029] | no | no | no |
| X05|null|adaptive_pos | 0.029 | 0.029 | 0.024 | 0.021 | 0.021 | [0.023, 0.037] | no | no | no |
| X06|null|hetero_calibrated | 0.032 | 0.033 | 0.026 | 0.021 | 0.021 | [0.025, 0.040] | no | no | no |
| X06|null|hetero_rearranged | 0.022 | 0.024 | 0.026 | 0.018 | 0.018 | [0.017, 0.030] | no | no | no |
| X07|null|proxy=anti | 0.025 | 0.025 | 0.026 | 0.018 | 0.021 | [0.019, 0.033] | no | no | no |
| X07|null|proxy=calibration | 0.025 | 0.028 | 0.022 | 0.021 | 0.021 | [0.019, 0.033] | no | no | no |
| X07|null|proxy=static_bias | 0.025 | 0.025 | 0.019 | 0.025 | 0.023 | [0.019, 0.032] | no | no | no |
| X08|null|G1 | 0.017 | 0.018 | 0.013 | 0.017 | 0.015 | [0.012, 0.023] | no | no | no |
| X08|null|G2 | 0.013 | 0.013 | 0.012 | 0.015 | 0.013 | [0.009, 0.020] | no | no | no |
| X09|cov_benign3 | 0.013 | 0.012 | 0.013 | 0.011 | 0.009 | [0.008, 0.018] | no | no | no |
| X09|cov_inform2 | 0.006 | 0.006 | 0.005 | 0.007 | 0.011 | [0.004, 0.011] | no | no | no |
| X09|prior1 | 0.046 | 0.046 | 0.038 | 0.047 | 0.012 | [0.038, 0.057] | no | no | no |
| X14|null|cost_fn=5 | 0.015 | 0.015 | 0.011 | 0.015 | 0.015 | [0.010, 0.021] | no | no | no |
| X14|null|fin_heavy_tail_clip | 0.089 | 0.101 | 0.099 | 0.116 | 0.025 | [0.077, 0.102] | YES | YES | no |

Empirical calibration is **not** a validity proof. Rows marked YES contradict the nominal alpha: the e-process guarantee does not extend to those null classes, which the null-class specification says in advance.
