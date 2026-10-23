# Repeated-candidate nondegenerate null calibration

This frozen benchmark used 2000 independent streams, horizon 1000, seed 26102026, and `cuda`. It tests 1, 5, and 13 distinct fixed candidate policies; 10%, 20%, and 40% hard query caps; and globally valid support bounds multiplied by 1, 1.5, and 2. Six sequential monitors share each queried outcome path. Candidate hypotheses receive equal Bonferroni alpha `0.05 / C`.

The null is nondegenerate: each candidate changes its action on half the contexts, with conditional mean gains balanced at +0.4 and −0.4 cost units on the changed contexts, yielding exactly zero history-conditional average gain and nonzero paired-cost variance. The positive and negative alternatives have exact mean gains +0.12 and −0.12 per event. Query propensities are fixed and independent of the visible context. The gate uses one global support bound and does not condition its stake or stopping rule on the current context. These results address the history-conditional average-gain null; they do not establish conditional-on-current-context validity.

## Nondegenerate null: 13 candidates

| Query cap | Bound multiplier | Monitor | Familywise false promotion (95% Wilson CI) | Mean labels |
|---:|---:|---|---:|---:|
| 10% | 1× | fixed_mixture | 1/2000 (0.001; 0.000–0.003) | 96.0 |
| 10% | 1× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 1× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 1× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 10% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 96.0 |
| 20% | 1× | fixed_mixture | 7/2000 (0.004; 0.002–0.007) | 194.7 |
| 20% | 1× | fixed_mixture_half_alpha | 2/2000 (0.001; 0.000–0.004) | 194.7 |
| 20% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 1× | positive_betting | 1/2000 (0.001; 0.000–0.003) | 194.7 |
| 20% | 1× | predictable_kelly | 1/2000 (0.001; 0.000–0.003) | 194.7 |
| 20% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 20% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 194.7 |
| 40% | 1× | fixed_mixture | 18/2000 (0.009; 0.006–0.014) | 393.6 |
| 40% | 1× | fixed_mixture_half_alpha | 8/2000 (0.004; 0.002–0.008) | 393.6 |
| 40% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 1× | positive_betting | 7/2000 (0.004; 0.002–0.007) | 393.6 |
| 40% | 1× | predictable_kelly | 11/2000 (0.005; 0.003–0.010) | 393.6 |
| 40% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 393.6 |
| 40% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 393.6 |

## Positive alternative: 13 candidates

| Query cap | Bound multiplier | Monitor | Detection power (95% Wilson CI) | Mean first crossing event among detections |
|---:|---:|---|---:|---:|
| 10% | 1× | fixed_mixture | 9/2000 (0.004; 0.002–0.009) | 808.9 |
| 10% | 1× | fixed_mixture_half_alpha | 2/2000 (0.001; 0.000–0.004) | 780.0 |
| 10% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | positive_betting | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 1× | fixed_mixture | 143/2000 (0.071; 0.061–0.084) | 765.0 |
| 20% | 1× | fixed_mixture_half_alpha | 81/2000 (0.041; 0.033–0.050) | 789.7 |
| 20% | 1× | hedged_positive | 6/2000 (0.003; 0.001–0.007) | 837.3 |
| 20% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 1× | positive_betting | 42/2000 (0.021; 0.016–0.028) | 794.1 |
| 20% | 1× | predictable_kelly | 71/2000 (0.035; 0.028–0.045) | 822.2 |
| 20% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | nan |
| 40% | 1× | fixed_mixture | 589/2000 (0.294; 0.275–0.315) | 650.7 |
| 40% | 1× | fixed_mixture_half_alpha | 435/2000 (0.217; 0.200–0.236) | 691.5 |
| 40% | 1× | hedged_positive | 233/2000 (0.117; 0.103–0.131) | 785.1 |
| 40% | 1× | pm_eb | 1/2000 (0.001; 0.000–0.003) | 900.0 |
| 40% | 1× | positive_betting | 433/2000 (0.216; 0.199–0.235) | 724.0 |
| 40% | 1× | predictable_kelly | 609/2000 (0.304; 0.285–0.325) | 727.3 |
| 40% | 2× | fixed_mixture | 96/2000 (0.048; 0.039–0.058) | 865.0 |
| 40% | 2× | fixed_mixture_half_alpha | 34/2000 (0.017; 0.012–0.024) | 889.7 |
| 40% | 2× | hedged_positive | 1/2000 (0.001; 0.000–0.003) | 914.0 |
| 40% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 40% | 2× | positive_betting | 19/2000 (0.009; 0.006–0.015) | 909.8 |
| 40% | 2× | predictable_kelly | 13/2000 (0.006; 0.004–0.011) | 918.1 |

The complete 1/5/13-candidate grid, strict negative control, all bound scales, and paired comparisons are in the Parquet files. Confidence intervals are pointwise; no monitor is selected from this grid. The exact mathematical validity still follows from each process's one-step supermartingale argument, predictable stakes, globally correct support bounds, randomized query design, and the union bound over frozen candidates. Monte Carlo rates are diagnostics, not the proof. This synthetic setup assumes immediate labels, i.i.d. contexts/outcomes, fixed policies, and no action-dependent outcomes.

## Reproduction

`uv run python scripts/calibrate_repeated_candidate_nulls.py --streams 2000 --horizon 1000 --seed 26102026 --device cuda --output outputs/repeated_candidate_null_calibration_2000`
