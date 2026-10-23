# Persistence-certified promotion grid

This benchmark compares the existing sequential full-start, three-start, empirical-Bernstein and Hoeffding gates with a two-phase intersection-union gate across 5 fixed benefit schedules and 1000 independent CUDA-generated streams per schedule. The frozen candidate is evaluated on the same paired outcomes for every method. The three discovery windows use (0.25, 0.5, 0.75) of the fixed shadow horizon; the remaining shadow events form the disjoint persistence window. Promotion may occur only after both windows' separate bounded-mean e-processes have crossed their thresholds.

Each phase process uses level alpha=0.05. The promotion null is a union: the candidate has nonpositive eventwise conditional expected net gain throughout the discovery phase, OR throughout the confirmation phase. The alternative requires evidence against both phase nulls. This is an intersection-union test: under either part of the union null, the probability of promoting is bounded by the corresponding phase e-process's alpha level. No Bonferroni split is needed for the conjunctive decision. The argument requires a candidate frozen before both phases, predictable phase boundaries, bounded increments, and the stated conditional-mean null within whichever phase is null. It is a standard construction, not a novelty claim.

The discovery cut is fixed before any monitor costs are observed. The confirmation process starts at that fixed boundary, not at the discovery crossing, so early positive samples cannot be reused as persistence evidence. A promotion begins on the event after the confirmation crossing. The final stream tail is untouched by testing and is scored with evaluator-only potential costs. This synthetic setup assumes no action-dependent outcomes and independent event noise; the e-process validity argument itself only needs its conditional supermartingale assumptions.

## Performance grid

Promotion rates and mean oracle post-promotion net gains use independent seeds as experimental units. The paired stream-level Parquet preserves baseline comparisons and every discovery fraction.

| Scenario | Rule | Promotion rate (95% CI) | Mean oracle future net gain (95% CI) | Harmful promotion rate | Mean promotion event |
|---|---|---:|---:|---:|---:|
| no_benefit | sequential_full_start | 0.032 [0.023, 0.045] | -0.002 [-0.002, -0.001] | 0.032 | 274.8 |
| no_benefit | sequential_multi_start_3 | 0.032 [0.023, 0.045] | -0.002 [-0.002, -0.001] | 0.032 | 649.9 |
| no_benefit | empirical_bernstein_fixed_horizon | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| no_benefit | hoeffding_fixed_horizon | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| no_benefit | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| no_benefit | persistence_intersection_d=0.25 | 0.001 [0.000, 0.006] | -0.000 [-0.000, 0.000] | 0.001 | 510.0 |
| no_benefit | persistence_intersection_d=0.5 | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| no_benefit | persistence_intersection_d=0.75 | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| early_transient | sequential_full_start | 1.000 [0.996, 1.000] | 53.079 [52.378, 53.781] | 0.000 | 77.5 |
| early_transient | sequential_multi_start_3 | 0.997 [0.991, 0.999] | 47.855 [47.057, 48.653] | 0.002 | 100.6 |
| early_transient | empirical_bernstein_fixed_horizon | 0.214 [0.190, 0.240] | -0.011 [-0.012, -0.009] | 0.214 | 1599.0 |
| early_transient | hoeffding_fixed_horizon | 0.171 [0.149, 0.196] | -0.009 [-0.010, -0.007] | 0.171 | 1599.0 |
| early_transient | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| early_transient | persistence_intersection_d=0.25 | 0.032 [0.023, 0.045] | -0.002 [-0.002, -0.001] | 0.032 | 590.8 |
| early_transient | persistence_intersection_d=0.5 | 0.027 [0.019, 0.039] | -0.001 [-0.002, -0.001] | 0.027 | 975.7 |
| early_transient | persistence_intersection_d=0.75 | 0.024 [0.016, 0.035] | -0.001 [-0.002, -0.001] | 0.024 | 1305.9 |
| benefit_reversal | sequential_full_start | 0.997 [0.991, 0.999] | -30.131 [-30.841, -29.420] | 0.997 | 78.0 |
| benefit_reversal | sequential_multi_start_3 | 0.996 [0.990, 0.998] | -35.223 [-36.008, -34.438] | 0.996 | 101.5 |
| benefit_reversal | empirical_bernstein_fixed_horizon | 0.001 [0.000, 0.006] | -0.032 [-0.095, 0.031] | 0.001 | 1599.0 |
| benefit_reversal | hoeffding_fixed_horizon | 0.001 [0.000, 0.006] | -0.032 [-0.095, 0.031] | 0.001 | 1599.0 |
| benefit_reversal | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| benefit_reversal | persistence_intersection_d=0.25 | 0.005 [0.002, 0.012] | -0.391 [-0.734, -0.049] | 0.005 | 444.6 |
| benefit_reversal | persistence_intersection_d=0.5 | 0.006 [0.003, 0.013] | -0.372 [-0.669, -0.075] | 0.006 | 852.2 |
| benefit_reversal | persistence_intersection_d=0.75 | 0.007 [0.003, 0.014] | -0.325 [-0.565, -0.085] | 0.007 | 1240.3 |
| persistent_benefit | sequential_full_start | 1.000 [0.996, 1.000] | 255.727 [254.309, 257.145] | 0.000 | 267.5 |
| persistent_benefit | sequential_multi_start_3 | 1.000 [0.996, 1.000] | 246.142 [244.617, 247.667] | 0.000 | 347.4 |
| persistent_benefit | empirical_bernstein_fixed_horizon | 1.000 [0.996, 1.000] | 95.950 [95.950, 95.950] | 0.000 | 1599.0 |
| persistent_benefit | hoeffding_fixed_horizon | 0.999 [0.994, 1.000] | 95.854 [95.666, 96.042] | 0.000 | 1599.0 |
| persistent_benefit | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| persistent_benefit | persistence_intersection_d=0.25 | 0.784 [0.757, 0.808] | 164.635 [159.130, 170.141] | 0.000 | 648.6 |
| persistent_benefit | persistence_intersection_d=0.5 | 0.974 [0.962, 0.982] | 155.950 [153.885, 158.015] | 0.000 | 1064.3 |
| persistent_benefit | persistence_intersection_d=0.75 | 0.802 [0.776, 0.826] | 97.639 [94.543, 100.735] | 0.000 | 1384.0 |
| late_persistent | sequential_full_start | 0.688 [0.659, 0.716] | 120.536 [115.364, 125.709] | 0.000 | 1398.9 |
| late_persistent | sequential_multi_start_3 | 0.998 [0.993, 0.999] | 212.645 [211.499, 213.791] | 0.000 | 1208.3 |
| late_persistent | empirical_bernstein_fixed_horizon | 0.520 [0.489, 0.551] | 74.854 [70.389, 79.319] | 0.000 | 1599.0 |
| late_persistent | hoeffding_fixed_horizon | 0.455 [0.424, 0.486] | 65.497 [61.047, 69.948] | 0.000 | 1599.0 |
| late_persistent | never_promote | 0.000 [0.000, 0.004] | 0.000 [0.000, 0.000] | 0.000 | — |
| late_persistent | persistence_intersection_d=0.25 | 0.011 [0.006, 0.020] | 1.992 [0.814, 3.170] | 0.000 | 1392.5 |
| late_persistent | persistence_intersection_d=0.5 | 0.020 [0.013, 0.031] | 4.010 [2.257, 5.763] | 0.000 | 1269.4 |
| late_persistent | persistence_intersection_d=0.75 | 0.042 [0.031, 0.056] | 8.293 [5.829, 10.758] | 0.000 | 1301.7 |

The conclusion must be based on the complete scenario grid and confidence intervals, not the best-performing split. A persistence window can suppress a harmful reversal by withholding promotion after discovery-only benefit, but it also delays or misses benefit that begins late. No split is selected on these evaluation outcomes; any data-driven split choice needs a separate pilot/validation stream and a fresh test stream.

## Reproduction

`uv run shiftlab-dive-persistence-grid --seeds 1000 --seed-offset 20401023 --n 3200 --device cuda --output outputs/persistence_promotion_grid`
