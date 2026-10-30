# Q2 baseline-and-candidate results (core grid, T=2000, delay 5, 10% labels, stationary ranking)
Pooled over K in {2,5,10}; 120/100 seeds per world. S09a ctxvar (variance-weighted disagreement-only querying), S09b disc (discounted bets + currentness gate), S09c shared (wealth allocated across candidates; **weak control only**), S09d budget (hard budget B=frac*T + CAMS allocation), S09e alloc (pilot-based alpha allocation; `_cams` suffix = with CAMS allocation).

## large gap (0.15)
| method | P(correct) | P(incorrect) | FWER | labels@cert | t@cert | n_eliminated | ms/seed |
|---|---|---|---|---|---|---|---|
| S09a_ctxvar | 0.141 | 0.000 | 0.000 | 183.250 | 1725.042 | 0.000 | 3.685 |
| S09a_ctxvar_shared | 0.138 | 0.000 | 0.000 | 182.511 | 1722.191 | 0.000 | 4.968 |
| S09b_disc | 0.056 | 0.000 | 0.000 | 145.316 | 1406.368 | 0.000 | 3.119 |
| S09b_disc_cams | 0.424 | 0.000 | 0.000 | 110.979 | 1075.958 | 0.000 | 4.320 |
| S09c_shared | 0.071 | 0.000 | 0.000 | 149.680 | 1455.080 | 0.000 | 5.771 |
| S09c_shared_cams | 0.403 | 0.000 | 0.000 | 106.664 | 1044.912 | 0.000 | 7.009 |
| S09d_budget | 0.468 | 0.000 | 0.000 | 110.717 | 1097.522 | 0.000 | 5.213 |
| S09e_alloc | 0.076 | 0.000 | 0.000 | 154.231 | 1530.885 | 0.000 | 3.068 |
| S09e_alloc_cams | 0.479 | 0.000 | 0.000 | 119.957 | 1163.883 | 0.000 | 4.240 |
| cams | 0.494 | 0.000 | 0.000 | 116.988 | 1131.310 | 0.000 | 2.712 |
| indep_labels | 0.065 | 0.000 | 0.000 | 150.909 | 1479.727 | 0.000 | 2.660 |
| paired_cs | 0.000 | 0.000 | 0.000 |  |  |  | 3.617 |
| paired_e | 0.179 | 0.000 | 0.003 | 147.323 | 1463.369 | 0.000 | 3.051 |
| paired_e_bonf | 0.076 | 0.000 | 0.000 | 152.692 | 1501.500 | 0.000 | 2.837 |
| pp_paired | 0.006 | 0.000 | 0.000 | 160.500 | 1793.500 | 0.000 | 4.337 |
| seqmcs | 0.035 | 0.000 | 0.000 | 201.692 | 1575.000 | 1.077 | 17.104 |
## moderate gap (0.06)
| method | P(correct) | P(incorrect) | FWER | labels@cert | t@cert | n_eliminated | ms/seed |
|---|---|---|---|---|---|---|---|
| S09a_ctxvar | 0.000 | 0.000 | 0.000 |  |  |  | 5.480 |
| S09a_ctxvar_shared | 0.000 | 0.000 | 0.000 | 193.000 | 1654.000 | 0.000 | 7.236 |
| S09b_disc | 0.012 | 0.000 | 0.000 | 127.500 | 1230.000 | 0.000 | 2.840 |
| S09b_disc_cams | 0.091 | 0.000 | 0.000 | 119.031 | 1145.031 | 0.000 | 3.693 |
| S09c_shared | 0.009 | 0.000 | 0.000 | 105.667 | 976.333 | 0.000 | 5.259 |
| S09c_shared_cams | 0.074 | 0.000 | 0.000 | 109.815 | 1032.630 | 0.000 | 7.798 |
| S09d_budget | 0.074 | 0.000 | 0.000 | 105.480 | 1028.560 | 0.000 | 4.233 |
| S09e_alloc | 0.009 | 0.000 | 0.000 | 143.667 | 1290.333 | 0.000 | 2.278 |
| S09e_alloc_cams | 0.079 | 0.000 | 0.000 | 120.286 | 1135.929 | 0.000 | 2.544 |
| cams | 0.074 | 0.000 | 0.000 | 110.963 | 1042.000 | 0.000 | 2.973 |
| indep_labels | 0.009 | 0.000 | 0.000 | 105.667 | 976.333 | 0.000 | 2.291 |
| paired_cs | 0.000 | 0.000 | 0.000 |  |  |  | 3.216 |
| paired_e | 0.029 | 0.000 | 0.000 | 137.333 | 1370.600 | 0.000 | 3.813 |
| paired_e_bonf | 0.012 | 0.000 | 0.000 | 132.000 | 1202.750 | 0.000 | 3.284 |
| pp_paired | 0.000 | 0.000 | 0.000 |  |  |  | 2.689 |
| seqmcs | 0.006 | 0.000 | 0.000 | 202.000 | 1501.500 | 1.000 | 9.542 |
## tiny gap (0.02)
| method | P(correct) | P(incorrect) | FWER | labels@cert | t@cert | n_eliminated | ms/seed |
|---|---|---|---|---|---|---|---|
| S09a_ctxvar | 0.000 | 0.000 | 0.000 |  |  |  | 4.149 |
| S09a_ctxvar_shared | 0.000 | 0.000 | 0.000 |  |  |  | 5.646 |
| S09b_disc | 0.000 | 0.000 | 0.000 |  |  |  | 2.877 |
| S09b_disc_cams | 0.012 | 0.000 | 0.000 | 92.750 | 915.750 | 0.000 | 3.252 |
| S09c_shared | 0.000 | 0.000 | 0.000 |  |  |  | 4.508 |
| S09c_shared_cams | 0.018 | 0.000 | 0.000 | 95.667 | 920.500 | 0.000 | 4.857 |
| S09d_budget | 0.024 | 0.000 | 0.000 | 113.875 | 1121.250 | 0.000 | 3.813 |
| S09e_alloc | 0.000 | 0.000 | 0.000 |  |  |  | 2.589 |
| S09e_alloc_cams | 0.012 | 0.000 | 0.000 | 129.750 | 1237.250 | 0.000 | 3.628 |
| cams | 0.021 | 0.000 | 0.000 | 107.714 | 1029.857 | 0.000 | 3.102 |
| indep_labels | 0.000 | 0.000 | 0.000 |  |  |  | 2.282 |
| paired_cs | 0.000 | 0.000 | 0.000 |  |  |  | 2.875 |
| paired_e | 0.003 | 0.006 | 0.006 | 112.833 | 1122.167 | 0.000 | 3.177 |
| paired_e_bonf | 0.000 | 0.000 | 0.000 |  |  |  | 2.366 |
| pp_paired | 0.000 | 0.000 | 0.000 |  |  |  | 2.336 |
| seqmcs | 0.000 | 0.000 | 0.000 |  |  |  | 9.886 |

* Disagreement-focused querying (CAMS-style, S09b/c/d/e `_cams`) is the decisive component: it multiplies correct-certification power by 3-6x over uniform labelling at equal expected labels, because increments vanish when models agree and the cap can use the disagreement-event inclusion probability.
* No S09 extension beats the CAMS-style baseline beyond noise (S09d and S09e_alloc_cams are within +-0.03 of it); S09a (variance weighting) is worse (its predictable floor lowers the cap); S09c shared allocation gives weak control only; S09b discounting reduces power.
* seqmcs is much weaker and 3-4x slower (K(K-1)/2 pairs, Bonferroni).
