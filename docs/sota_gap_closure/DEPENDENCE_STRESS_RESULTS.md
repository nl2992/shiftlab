# Dependence stress results (X03, X04, X05, G4 GARCH)
False-alarm rate (alarm before the first harmful step; any alarm in a no-harm world), 2000 independent paths per cell (Wilson 95% half-width <= 0.02). Label rate 0.2, delay 5, alpha 0.05, repaired engine; `HG_arrived` = naive release, `HG_xcap_legacy` = earlier covariate-dependent cap.

| world | HG | pprm | cost | HG_arrived | HG 95% CI | exceeds_alpha_HG | exceeds_alpha_pprm | exceeds_alpha_cost |
|---|---|---|---|---|---|---|---|---|
| G4|fin_null | 0.089 | 0.130 | 0.030 | 0.094 | [0.077, 0.102] | YES | YES | no |
| X03|null|ar0.5_s1.0 | 0.015 | 0.019 | 0.014 | 0.014 | [0.010, 0.021] | no | no | no |
| X03|null|ar0.98_s1.5 | 0.038 | 0.019 | 0.044 | 0.038 | [0.031, 0.048] | no | no | no |
| X03|null|ar0.9_s1.0 | 0.016 | 0.013 | 0.018 | 0.015 | [0.011, 0.022] | no | no | no |
| X04|null|cluster100_s1.5 | 0.088 | 0.052 | 0.055 | 0.088 | [0.076, 0.101] | YES | no | no |
| X04|null|cluster20_s1.0 | 0.013 | 0.012 | 0.013 | 0.013 | [0.009, 0.019] | no | no | no |
| X04|null|cluster400_s1.5 | 0.190 | 0.121 | 0.163 | 0.190 | [0.173, 0.208] | YES | YES | YES |
| X05|null|adaptive_neg | 0.022 | 0.015 | 0.015 | 0.022 | [0.016, 0.029] | no | no | no |
| X05|null|adaptive_pos | 0.029 | 0.021 | 0.021 | 0.029 | [0.023, 0.037] | no | no | no |
| X14|null|cost_fn=5 | 0.015 | 0.015 | 0.015 | 0.015 | [0.010, 0.021] | no | no | no |
| X14|null|fin_heavy_tail_clip | 0.089 | 0.116 | 0.025 | 0.101 | [0.077, 0.102] | YES | YES | no |

**Finding:** all three e-process monitors lose their nominal size under slowly varying conditional risk (cluster-400: HG 0.190, pprm 0.121, cost 0.163; GARCH null: HG 0.089, pprm 0.130). Short-range dependence (AR 0.5/0.9, cluster-20) is harmless at these settings. The mechanism is the conditional null, not the cap or the delay. F2 (long-run-variance bet) is the tested heuristic repair (`SECOND_ROUND_FIX_CANDIDATES.md`).
