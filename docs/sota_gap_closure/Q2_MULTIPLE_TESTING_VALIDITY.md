# Q2 multiple-testing validity (zero-gap worlds: any promotion is an error)
Zero-gap worlds contain candidates with gap exactly 0 and candidates worse by 0.10; 300 seeds per world, 3 values of K x 3 rankings. FWER = P(any candidate crosses while its current gap <= 0).

| method | 2 | 5 | 10 | all K | P(any promotion | zero gap) |
|---|---|---|---|---|---|
| S09a_ctxvar | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S09a_ctxvar_shared | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S09b_disc | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0005 |
| S09b_disc_cams | 0.0056 | 0.0000 | 0.0033 | 0.0029 | 0.0157 |
| S09c_shared | 0.0011 | 0.0011 | 0.0000 | 0.0010 | 0.0029 |
| S09c_shared_cams | 0.0056 | 0.0000 | 0.0033 | 0.0029 | 0.0129 |
| S09d_budget | 0.0056 | 0.0000 | 0.0033 | 0.0029 | 0.0129 |
| S09e_alloc | 0.0011 | 0.0000 | 0.0000 | 0.0005 | 0.0019 |
| S09e_alloc_cams | 0.0056 | 0.0011 | 0.0033 | 0.0033 | 0.0124 |
| cams | 0.0056 | 0.0000 | 0.0033 | 0.0029 | 0.0129 |
| indep_labels | 0.0011 | 0.0000 | 0.0000 | 0.0005 | 0.0010 |
| paired_cs | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| paired_e | 0.0011 | 0.0022 | 0.0233 | 0.0048 | 0.0186 |
| paired_e_bonf | 0.0011 | 0.0000 | 0.0000 | 0.0005 | 0.0019 |
| pp_paired | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| seqmcs | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

All methods stay below alpha = 0.05 here (largest: uncorrected `paired_e` at K=10). The uncorrected test has no theoretical multiplicity control: its measured size at K=10 is 0.023, safely below alpha only because Kelly plug-in bets are conservative under a zero-drift null; the Bonferroni / elimination / closed variants are valid by construction (union bound). `S09c_shared` controls only the intersection null (weak control). Empirical zero-gap error is not a validity proof for nonstationary rankings: after a reversal, certification of a candidate whose *current* gap is negative is possible because e-process wealth does not forget:

| ('method', '') | ('P(correct)', 'one_reversal') | ('P(correct)', 'recurrent') | ('P(incorrect)', 'one_reversal') | ('P(incorrect)', 'recurrent') |
|---|---|---|---|---|
| S09a_ctxvar | 0.000 | 0.000 | 0.000 | 0.000 |
| S09a_ctxvar_shared | 0.000 | 0.000 | 0.000 | 0.000 |
| S09b_disc | 0.003 | 0.003 | 0.012 | 0.003 |
| S09b_disc_cams | 0.224 | 0.088 | 0.012 | 0.038 |
| S09c_shared | 0.009 | 0.003 | 0.015 | 0.006 |
| S09c_shared_cams | 0.224 | 0.062 | 0.012 | 0.029 |
| S09d_budget | 0.247 | 0.062 | 0.018 | 0.038 |
| S09e_alloc | 0.006 | 0.003 | 0.015 | 0.006 |
| S09e_alloc_cams | 0.221 | 0.032 | 0.009 | 0.035 |
| cams | 0.235 | 0.062 | 0.018 | 0.029 |
| indep_labels | 0.006 | 0.003 | 0.015 | 0.006 |
| paired_cs | 0.000 | 0.000 | 0.000 | 0.000 |
| paired_e | 0.021 | 0.015 | 0.032 | 0.021 |
| paired_e_bonf | 0.009 | 0.003 | 0.015 | 0.006 |
| pp_paired | 0.000 | 0.000 | 0.000 | 0.000 |
| seqmcs | 0.000 | 0.003 | 0.015 | 0.000 |
