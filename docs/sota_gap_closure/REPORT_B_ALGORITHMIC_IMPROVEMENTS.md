# Report B - ranking of methods (synthetic evidence only)
## Confirmation round 1 (frozen; new G3-G6 pools; power over 15 harm worlds; "in-scope" nulls exclude the dependent-outcome nulls)
| config | power (harm worlds, mean) | harm before alarm | FA before harm (harm worlds) | FA (null worlds, mean) | FA (null worlds, max) |
|---|---|---|---|---|---|
| HG@0.1 | 0.701 | 160.965 | 0.003 | 0.023 | 0.050 |
| HG@0.2 | 0.808 | 100.956 | 0.007 | 0.045 | 0.137 |
| HG_F2lrv100@0.1 | 0.640 | 200.271 | 0.001 | 0.007 | 0.021 |
| HG_F2lrv100@0.2 | 0.763 | 150.405 | 0.002 | 0.009 | 0.018 |
| HG_robustmix@0.1 | 0.719 | 151.220 | 0.001 | 0.012 | 0.028 |
| HG_robustmix@0.2 | 0.803 | 94.595 | 0.005 | 0.035 | 0.089 |
| cost@0.1 | 0.434 | 235.418 | 0.006 | 0.023 | 0.055 |
| cost@0.2 | 0.759 | 170.902 | 0.010 | 0.046 | 0.138 |
| cusum@0.1 | 0.683 | 181.912 | 0.010 | 0.052 | 0.075 |
| cusum@0.2 | 0.847 | 135.263 | 0.012 | 0.049 | 0.111 |
| ph@0.1 | 0.767 | 185.500 | 0.004 | 0.048 | 0.080 |
| ph@0.2 | 0.918 | 133.667 | 0.004 | 0.045 | 0.094 |
| pprm@0.1 | 0.672 | 189.816 | 0.008 | 0.028 | 0.089 |
| pprm@0.2 | 0.756 | 134.857 | 0.021 | 0.042 | 0.162 |

## Confirmation round 2 (corrected-floor candidates; fresh seeds)
| index | power | labels | harm_before | FA_in_scope_null_max | FA_dependence_nulls_max | label_matched_gain |
|---|---|---|---|---|---|---|
| HG@0.1 | 0.697 | 199.510 | 159.281 | 0.017 | 0.037 | 0.000 |
| HG@0.2 | 0.810 | 398.543 | 100.456 | 0.028 | 0.141 | 0.000 |
| HG_growth_floor@0.1 | 0.725 | 235.344 | 145.733 | 0.004 | 0.025 | -0.010 |
| HG_growth_floor@0.2 | 0.802 | 463.758 | 87.477 | 0.019 | 0.084 | -0.020 |
| HG_growthlook_floor@0.1 | 0.733 | 250.335 | 138.226 | 0.006 | 0.019 | -0.013 |
| HG_growthlook_floor@0.2 | 0.806 | 495.320 | 84.834 | 0.015 | 0.093 | -0.023 |
| HG_hardcap@0.1 | 0.689 | 194.018 | 159.477 | 0.017 | 0.036 | 0.000 |
| HG_hardcap@0.2 | 0.808 | 392.033 | 100.475 | 0.028 | 0.140 | 0.000 |
| HG_infovalue_pace@0.1 | 0.709 | 199.988 | 155.575 | 0.008 | 0.012 | 0.011 |
| HG_infovalue_pace@0.2 | 0.794 | 399.972 | 95.520 | 0.017 | 0.069 | -0.016 |
| HG_robustmix@0.1 | 0.714 | 200.278 | 151.179 | 0.014 | 0.024 | 0.016 |
| HG_robustmix@0.2 | 0.806 | 399.858 | 93.780 | 0.024 | 0.073 | -0.004 |
| HG_variance_floor@0.1 | 0.715 | 202.006 | 155.443 | 0.008 | 0.011 | 0.015 |
| HG_variance_floor@0.2 | 0.793 | 403.775 | 96.133 | 0.017 | 0.070 | -0.018 |
| HGu@0.08 | 0.632 | 159.697 | 182.706 | 0.021 | 0.026 | 0.000 |
| HGu@0.12 | 0.740 | 239.695 | 140.987 | 0.019 | 0.060 | 0.000 |
| HGu@0.16 | 0.784 | 318.440 | 116.541 | 0.021 | 0.113 | 0.000 |
| HGu@0.25 | 0.829 | 498.440 | 88.246 | 0.029 | 0.187 | 0.000 |
| HGu@0.3 | 0.846 | 598.305 | 79.627 | 0.030 | 0.222 | 0.000 |

| criterion | ranking (best first) | evidence |
|---|---|---|
| general detection (Q1, round 1, 20% labels) | PH 0.918 > CUSUM 0.847 > HG 0.808 ~ HG+robust mixture 0.803 > HG+LRV 0.763 ~ cost 0.759 ~ pprm 0.756. HG vs PH: -0.110 [-0.247, +0.005] (Holm p 0.323) (n.s. after Holm); HG vs pprm +0.052 [+0.020, +0.090] (Holm p 0.003) (significant). PH / CUSUM have no validity guarantee (thresholds calibrated on a null stream). | `FINAL_STATISTICAL_COMPARISONS.md` |
| earliest detection (harm accrued before alarm) | HG 101 < robust mixture 95 < CUSUM 135 ~ PH 134 < pprm 135 | round 1 |
| special-case performance | HG for benign-shift robustness (earlier phase); disagreement-focused querying where models agree most of the time (Q2) | S01, Q2 |
| label efficiency | uniform querying; all learned-allocation rules are within noise of it after label matching (round 2 label-matched gains -0.023..+0.016) | round 2 |
| false-alarm control (null mean, 20% labels) | HG+LRV 0.009 < robust mixture 0.035 < HG 0.045 ~ PH 0.045; in-scope maximum for HG 0.137 (dependence nulls inflate it) | `FINAL_VALIDITY_RESULTS.md` |
| model certification (Q2) | CAMS-style disagreement querying ~ S09d ~ S09e_alloc_cams > S09b/c_cams > uniform Bonferroni > seqmcs | `Q2_CANDIDATE_RESULTS.md` |
| intervention regret (Q3, persistent harm) | rolling recalibration (idealised) < certified promotion ~ hysteresis ~ PH < HG < frozen; frozen best when nothing is worthwhile | `Q3_BASELINE_RESULTS.md`, `Q3_HG_TRANSFER_RESULTS.md` |
| runtime (us per stream-step, T=2000, S=100) | PH 0.08 ~ CUSUM 0.07 < legacy pprm 0.06 < legacy HG 0.19 < engine pprm 0.78 < engine HG 1.06 < HG+LRV 1.99 < robust mixture 3.12 ~ multi-window 3.16 | `COMPUTE_ACCURACY_PARETO.md` |
| memory | PH / CUSUM 6.6 MB < engine HG 22.1 MB < allocation arms 72.0 MB (numpy peak for 100 streams x 2000 steps) | `MEMORY_SCALING.csv` |
| robustness | the repaired cap + in-order release is the only validity-safe configuration; nothing is robust to dependent outcomes (LRV scaling reduces but does not remove it and costs power) | `VALIDITY_SUPPORT_MATRIX.md`, `SECOND_ROUND_FIX_RESULTS.md` |
