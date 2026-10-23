# Repeated-candidate nondegenerate null calibration

This frozen benchmark used 2000 independent streams, horizon 1000, seed 27102026, and `cuda`. It tests 1, 5, and 13 distinct fixed candidate policies; 10%, 20%, and 40% hard query caps; and globally valid support bounds multiplied by 1, 1.5, and 2. Six sequential monitors share each queried outcome path. Candidate hypotheses receive equal Bonferroni alpha `0.05 / C`.

The null is nondegenerate: each candidate changes its action on half the contexts, with conditional mean gains balanced at +0.4 and −0.4 cost units on the changed contexts, yielding exactly zero history-conditional average gain and nonzero paired-cost variance. The positive and negative alternatives have exact mean gains +0.12 and −0.12 per event. Query propensities are fixed and independent of the visible context. The gate uses one global support bound and does not condition its stake or stopping rule on the current context. These results address the history-conditional average-gain null; they do not establish conditional-on-current-context validity.

## Nondegenerate null: 13 candidates

| Query cap | Bound multiplier | Monitor | Familywise false promotion (95% Wilson CI) | Mean labels |
|---:|---:|---|---:|---:|
| 10% | 1× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 1× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 1× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 1× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 1× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 10% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 96.2 |
| 20% | 1× | fixed_mixture | 3/2000 (0.002; 0.001–0.004) | 195.0 |
| 20% | 1× | fixed_mixture_half_alpha | 1/2000 (0.001; 0.000–0.003) | 195.0 |
| 20% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 1× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 1× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 1× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 20% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 195.0 |
| 40% | 1× | fixed_mixture | 11/2000 (0.005; 0.003–0.010) | 393.8 |
| 40% | 1× | fixed_mixture_half_alpha | 5/2000 (0.003; 0.001–0.006) | 393.8 |
| 40% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 1× | online_process_mixture | 3/2000 (0.002; 0.001–0.004) | 393.8 |
| 40% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 1× | positive_betting | 5/2000 (0.003; 0.001–0.006) | 393.8 |
| 40% | 1× | predictable_kelly | 9/2000 (0.004; 0.002–0.009) | 393.8 |
| 40% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 2× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | 393.8 |
| 40% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | 393.8 |

## Positive alternative: 13 candidates

| Query cap | Bound multiplier | Monitor | Detection power (95% Wilson CI) | Mean first crossing event among detections |
|---:|---:|---|---:|---:|
| 10% | 1× | fixed_mixture | 1/2000 (0.001; 0.000–0.003) | 999.0 |
| 10% | 1× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | positive_betting | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 1× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | nan |
| 10% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 1× | fixed_mixture | 142/2000 (0.071; 0.061–0.083) | 785.3 |
| 20% | 1× | fixed_mixture_half_alpha | 71/2000 (0.035; 0.028–0.045) | 827.0 |
| 20% | 1× | hedged_positive | 8/2000 (0.004; 0.002–0.008) | 847.8 |
| 20% | 1× | online_process_mixture | 47/2000 (0.024; 0.018–0.031) | 844.8 |
| 20% | 1× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 1× | positive_betting | 33/2000 (0.017; 0.012–0.023) | 842.6 |
| 20% | 1× | predictable_kelly | 56/2000 (0.028; 0.022–0.036) | 844.9 |
| 20% | 2× | fixed_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | fixed_mixture_half_alpha | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | hedged_positive | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | online_process_mixture | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | positive_betting | 0/2000 (0.000; 0.000–0.002) | nan |
| 20% | 2× | predictable_kelly | 0/2000 (0.000; 0.000–0.002) | nan |
| 40% | 1× | fixed_mixture | 615/2000 (0.307; 0.288–0.328) | 646.8 |
| 40% | 1× | fixed_mixture_half_alpha | 441/2000 (0.221; 0.203–0.239) | 680.6 |
| 40% | 1× | hedged_positive | 212/2000 (0.106; 0.093–0.120) | 771.4 |
| 40% | 1× | online_process_mixture | 479/2000 (0.239; 0.221–0.259) | 721.7 |
| 40% | 1× | pm_eb | 1/2000 (0.001; 0.000–0.003) | 917.0 |
| 40% | 1× | positive_betting | 443/2000 (0.222; 0.204–0.240) | 724.4 |
| 40% | 1× | predictable_kelly | 652/2000 (0.326; 0.306–0.347) | 732.4 |
| 40% | 2× | fixed_mixture | 104/2000 (0.052; 0.043–0.063) | 860.6 |
| 40% | 2× | fixed_mixture_half_alpha | 34/2000 (0.017; 0.012–0.024) | 876.4 |
| 40% | 2× | hedged_positive | 1/2000 (0.001; 0.000–0.003) | 921.0 |
| 40% | 2× | online_process_mixture | 11/2000 (0.005; 0.003–0.010) | 927.0 |
| 40% | 2× | pm_eb | 0/2000 (0.000; 0.000–0.002) | nan |
| 40% | 2× | positive_betting | 17/2000 (0.009; 0.005–0.014) | 909.5 |
| 40% | 2× | predictable_kelly | 11/2000 (0.005; 0.003–0.010) | 932.9 |

The complete 1/5/13-candidate grid, strict negative control, all bound scales, and paired comparisons are in the Parquet files. Confidence intervals are pointwise; no monitor is selected from this grid. The exact mathematical validity still follows from each process's one-step supermartingale argument, predictable stakes, globally correct support bounds, randomized query design, and the union bound over frozen candidates. Monte Carlo rates are diagnostics, not the proof. This synthetic setup assumes immediate labels, i.i.d. contexts/outcomes, fixed policies, and no action-dependent outcomes.

## Reproduction

`uv run python scripts/calibrate_repeated_candidate_nulls.py --streams 2000 --horizon 1000 --seed 27102026 --device cuda --output outputs/online_process_mixture_2000`
