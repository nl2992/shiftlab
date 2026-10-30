# S11 / S04 / S06 exact oracle gaps on the toy instance
Per-policy gap to the exact optimum (power = probability of crossing the threshold within the horizon under the alternative), mean over unseen alternatives and budgets. `remaining` is the S06 pacing rule on the toy, `const_0.5` / `always_1` are constants, `neyman` is the variance-optimal constant-per-context table (the S04 variance arm).

| policy | gap_mean | gap_max | rel_gap | decision_error | null_alarm_mean |
|---|---|---|---|---|---|
| always_1 | 0.0234 | 0.1060 | 0.7041 | 0.9767 | 0.0208 |
| const_0.5 | 0.0948 | 0.4813 | 0.8998 | 1.0000 | 0.0054 |
| fsc | 0.1056 | 0.5251 | 0.9540 | 0.0233 | 0.0025 |
| lookup | 0.0863 | 0.5251 | 0.8146 | 0.0538 | 0.0079 |
| mlp_16 | 0.0623 | 0.3058 | 0.6283 | 0.0213 | 0.0119 |
| neyman | 0.0542 | 0.4010 | 0.7441 | 0.9860 | 0.0163 |
| remaining | 0.0779 | 0.4052 | 0.7802 | 0.9767 | 0.0095 |
| tree_d3 | 0.1104 | 0.5479 | 0.9796 | 0.0250 | 0.0013 |
| tree_d6 | 0.0943 | 0.4752 | 0.8970 | 0.0250 | 0.0052 |

The best learned approximator by mean gap is `mlp_16` (gap 0.062); the trivial always-query policy has gap 0.023 and the variance-optimal table gap 0.054; the exact optimum has mean power 0.115. Learned policies reproduce the optimal action on most sampled states (decision error 0.021-0.025) yet lose value: the few states where the optimal action matters (late, near the threshold, with pending labels) are rare in the training distribution, the standard imitation-learning failure. **S11 is negative on this instance: no compact approximator matched the exact oracle's value on unseen alternatives.** Amortisation cost: 398 s of exact solving to build the training set versus 19 s per exact solve of a test instance, so amortisation would pay off only after about 21 test instances even for a perfect approximator.

Per-instance values: `outputs/gap_closure/e11_s11_amortized_test.csv`. Exact value of information for the first-promotion problem: `e11_exact_voi.csv`.
