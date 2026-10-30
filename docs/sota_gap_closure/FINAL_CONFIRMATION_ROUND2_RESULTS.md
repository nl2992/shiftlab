# Final confirmation, round 2 (corrected-floor candidates; frozen in `frozen_confirmation_v2.json` before running; fresh seeds 1,100,000+)
Same confirmation pool parameters as round 1 (15 harm worlds, 6 null worlds, 400 / 1000 seeds). Uniform power-vs-labels curve: HG at nominal fractions .08 .10 .12 .16 .20 .25 .30 (same seeds) and the hard-capped HG arm. `label_matched_gain` = arm power minus the curve interpolated at the arm's realised labels (linear; the uniform curve is concave in this range, so linear interpolation slightly *overstates* the uniform comparator, i.e. is conservative for the candidates).

## Summary per arm (power over harm worlds, equally weighted)
| index | power | labels | harm_before | FA_in_scope_null_max | FA_dependence_nulls_max | uniform_power_at_same_labels | label_matched_gain |
|---|---|---|---|---|---|---|---|
| HG@0.1 | 0.697 | 199.510 | 159.281 | 0.017 | 0.037 | 0.697 | 0.000 |
| HG@0.2 | 0.810 | 398.543 | 100.456 | 0.028 | 0.141 | 0.810 | 0.000 |
| HG_growth_floor@0.1 | 0.725 | 235.344 | 145.733 | 0.004 | 0.025 | 0.735 | -0.010 |
| HG_growth_floor@0.2 | 0.802 | 463.758 | 87.477 | 0.019 | 0.084 | 0.823 | -0.021 |
| HG_growthlook_floor@0.1 | 0.733 | 250.335 | 138.226 | 0.006 | 0.019 | 0.746 | -0.013 |
| HG_growthlook_floor@0.2 | 0.806 | 495.320 | 84.834 | 0.015 | 0.093 | 0.829 | -0.023 |
| HG_hardcap@0.1 | 0.689 | 194.018 | 159.477 | 0.017 | 0.036 | 0.689 | 0.000 |
| HG_hardcap@0.2 | 0.808 | 392.033 | 100.475 | 0.028 | 0.140 | 0.808 | 0.000 |
| HG_infovalue_pace@0.1 | 0.709 | 199.988 | 155.575 | 0.008 | 0.012 | 0.697 | 0.011 |
| HG_infovalue_pace@0.2 | 0.794 | 399.972 | 95.520 | 0.017 | 0.069 | 0.810 | -0.016 |
| HG_robustmix@0.1 | 0.714 | 200.278 | 151.179 | 0.014 | 0.024 | 0.698 | 0.016 |
| HG_robustmix@0.2 | 0.806 | 399.858 | 93.781 | 0.024 | 0.073 | 0.810 | -0.004 |
| HG_variance_floor@0.1 | 0.715 | 202.006 | 155.442 | 0.008 | 0.011 | 0.700 | 0.015 |
| HG_variance_floor@0.2 | 0.793 | 403.775 | 96.133 | 0.017 | 0.070 | 0.811 | -0.018 |
| HGu@0.08 | 0.632 | 159.697 | 182.706 | 0.021 | 0.026 | 0.632 | 0.000 |
| HGu@0.12 | 0.740 | 239.695 | 140.987 | 0.019 | 0.060 | 0.740 | 0.000 |
| HGu@0.16 | 0.784 | 318.440 | 116.541 | 0.021 | 0.113 | 0.784 | 0.000 |
| HGu@0.25 | 0.829 | 498.440 | 88.246 | 0.029 | 0.187 | 0.829 | 0.000 |
| HGu@0.3 | 0.846 | 598.305 | 79.627 | 0.030 | 0.222 | 0.846 | 0.000 |

## Primary paired comparisons at the same NOMINAL fraction (cluster bootstrap over worlds then seeds; Holm over 10 comparisons)
| index | A | B | frac | power A-B | ci_lo | ci_hi | p_raw | extra labels A-B | p_holm |
|---|---|---|---|---|---|---|---|---|---|
| 0 | HG_growth_floor | HG | 0.1000 | 0.0282 | -0.0003 | 0.0530 | 0.0553 | 35.8343 | 0.4427 |
| 1 | HG_growthlook_floor | HG | 0.1000 | 0.0363 | 0.0047 | 0.0638 | 0.0227 | 50.8253 | 0.2040 |
| 2 | HG_variance_floor | HG | 0.1000 | 0.0182 | -0.0088 | 0.0398 | 0.1593 | 2.4955 | 0.9560 |
| 3 | HG_infovalue_pace | HG_hardcap | 0.1000 | 0.0197 | -0.0048 | 0.0408 | 0.1093 | 5.9703 | 0.7653 |
| 4 | HG_growthlook_floor | HG_variance_floor | 0.1000 | 0.0182 | 0.0058 | 0.0308 | 0.0047 | 48.3298 | 0.0467 |
| 5 | HG_growth_floor | HG | 0.2000 | -0.0078 | -0.0512 | 0.0322 | 0.7653 | 65.2155 | 1.0000 |
| 6 | HG_growthlook_floor | HG | 0.2000 | -0.0038 | -0.0502 | 0.0372 | 0.9287 | 96.7772 | 1.0000 |
| 7 | HG_variance_floor | HG | 0.2000 | -0.0168 | -0.0538 | 0.0122 | 0.3453 | 5.2323 | 1.0000 |
| 8 | HG_infovalue_pace | HG_hardcap | 0.2000 | -0.0140 | -0.0503 | 0.0153 | 0.4147 | 7.9395 | 1.0000 |
| 9 | HG_growthlook_floor | HG_variance_floor | 0.2000 | 0.0130 | -0.0048 | 0.0372 | 0.2087 | 91.5448 | 1.0000 |

A comparison counts as a label-efficiency gain only if the label-matched gain is >= +0.03 (the registered practical threshold) as well. In-scope null false alarm (columns `FA_in_scope_null_max`) must stay <= 0.07; dependent nulls are reported separately and are expected to be inflated.
