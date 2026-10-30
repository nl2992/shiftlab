# Q2 generalisation: ranking dynamics, number of models, labels, delay, horizon
Correct-certification probability by ranking (core grid, moderate+large gaps, pooled over K):

| method | one_reversal | recurrent | stationary |
|---|---|---|---|
| S09a_ctxvar | 0.000 | 0.000 | 0.028 |
| S09a_ctxvar_shared | 0.000 | 0.000 | 0.027 |
| S09b_disc | 0.001 | 0.001 | 0.014 |
| S09b_disc_cams | 0.056 | 0.025 | 0.112 |
| S09c_shared | 0.002 | 0.001 | 0.016 |
| S09c_shared_cams | 0.055 | 0.023 | 0.103 |
| S09d_budget | 0.060 | 0.022 | 0.117 |
| S09e_alloc | 0.002 | 0.001 | 0.017 |
| S09e_alloc_cams | 0.056 | 0.011 | 0.117 |
| cams | 0.058 | 0.024 | 0.122 |
| indep_labels | 0.001 | 0.001 | 0.015 |
| paired_cs | 0.000 | 0.000 | 0.000 |
| paired_e | 0.009 | 0.006 | 0.048 |
| paired_e_bonf | 0.003 | 0.001 | 0.018 |
| pp_paired | 0.000 | 0.000 | 0.001 |
| seqmcs | 0.000 | 0.001 | 0.008 |

By number of models K:

| method | 2 | 5 | 10 |
|---|---|---|---|
| S09a_ctxvar | 0.062 | 0.004 | 0.000 |
| S09a_ctxvar_shared | 0.062 | 0.003 | 0.000 |
| S09b_disc | 0.032 | 0.003 | 0.002 |
| S09b_disc_cams | 0.339 | 0.064 | 0.012 |
| S09c_shared | 0.039 | 0.004 | 0.000 |
| S09c_shared_cams | 0.329 | 0.054 | 0.003 |
| S09d_budget | 0.342 | 0.072 | 0.015 |
| S09e_alloc | 0.036 | 0.008 | 0.002 |
| S09e_alloc_cams | 0.308 | 0.079 | 0.020 |
| cams | 0.329 | 0.092 | 0.020 |
| indep_labels | 0.039 | 0.000 | 0.000 |
| paired_cs | 0.000 | 0.000 | 0.000 |
| paired_e | 0.039 | 0.044 | 0.042 |
| paired_e_bonf | 0.039 | 0.008 | 0.002 |
| pp_paired | 0.003 | 0.000 | 0.000 |
| seqmcs | 0.021 | 0.000 | 0.000 |

Off-core sweeps (fraction .01/.05/.20, delay 0/20, horizon 200/500; P(correct) | P(incorrect) | P(certified) by group):

| ('method', '') | ('P(correct)', 'delay') | ('P(correct)', 'frac') | ('P(correct)', 'horizon') | ('P(incorrect)', 'delay') | ('P(incorrect)', 'frac') | ('P(incorrect)', 'horizon') | ('P(certified)', 'delay') | ('P(certified)', 'frac') | ('P(certified)', 'horizon') |
|---|---|---|---|---|---|---|---|---|---|
| S09a_ctxvar | 0.000 | 0.002 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.002 | 0.000 |
| S09a_ctxvar_shared | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 |
| S09b_disc | 0.002 | 0.002 | 0.000 | 0.000 | 0.000 | 0.000 | 0.004 | 0.004 | 0.000 |
| S09b_disc_cams | 0.005 | 0.008 | 0.011 | 0.000 | 0.000 | 0.000 | 0.008 | 0.011 | 0.012 |
| S09c_shared | 0.004 | 0.002 | 0.000 | 0.000 | 0.000 | 0.000 | 0.005 | 0.004 | 0.000 |
| S09c_shared_cams | 0.006 | 0.008 | 0.008 | 0.000 | 0.000 | 0.000 | 0.013 | 0.012 | 0.009 |
| S09d_budget | 0.010 | 0.009 | 0.004 | 0.000 | 0.000 | 0.000 | 0.014 | 0.011 | 0.006 |
| S09e_alloc | 0.005 | 0.003 | 0.000 | 0.000 | 0.000 | 0.000 | 0.006 | 0.005 | 0.000 |
| S09e_alloc_cams | 0.013 | 0.008 | 0.004 | 0.000 | 0.000 | 0.000 | 0.020 | 0.010 | 0.004 |
| cams | 0.012 | 0.012 | 0.012 | 0.000 | 0.000 | 0.000 | 0.019 | 0.014 | 0.013 |
| indep_labels | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| paired_cs | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| paired_e | 0.020 | 0.012 | 0.002 | 0.000 | 0.000 | 0.000 | 0.030 | 0.019 | 0.004 |
| paired_e_bonf | 0.005 | 0.003 | 0.000 | 0.000 | 0.000 | 0.000 | 0.006 | 0.005 | 0.000 |
| pp_paired | 0.000 | 0.001 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 |
| seqmcs | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.001 | 0.000 |

Limits: the benchmark has low absolute power (the best method certifies ~49% of large-gap runs at 10% labels); K=10 weakens Bonferroni methods; recurrent / reversal rankings reward discounting only weakly. Seed counts are modest (100-300 per world), so differences below ~0.05 are noise. The synthetic gap scale (0.02-0.15 decision cost per step) was chosen so the large gap is certifiable; "tiny" is not certifiable at these label rates by any method.
