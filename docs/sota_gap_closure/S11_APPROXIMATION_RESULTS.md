# S11 amortised approximation of exact acquisition (RPOQ toy instance, exact evaluation)
Training: 4,439,928 optimal (state, action) pairs from the exact solver on 18 training instances (6 alternatives x budgets 2, 3, 4; subsampled to 200,000 for fitting). The **oracle was not free**: 398 s of exact solving plus 16.6 s of fitting before any test instance. Approximators: decision trees (depth 6 and 3), shallow MLP (16 hidden, 60 iterations), quantised lookup, finite-state controller (t, context, remaining budget only), a pacing heuristic and constants. Features: step, context, remaining budget, log wealth, number of pending labels, alternative parameters (so the policy conditions on the unseen alternative's value).
Test: 5 alternatives never used in training x 3 budgets; policy values are evaluated **exactly** (policy plugged into the exact evaluator), not by simulation.

| policy | gap_mean | gap_max | rel_gap | null_alarm_mean | null_alarm_max | decision_error | latency_ms |
|---|---|---|---|---|---|---|---|
| always_1 | 0.0234 | 0.1060 | 0.7041 | 0.0208 | 0.0625 | 0.9767 | 0.0146 |
| const_0.5 | 0.0948 | 0.4813 | 0.8998 | 0.0054 | 0.0151 | 1.0000 | 0.0167 |
| fsc | 0.1056 | 0.5251 | 0.9540 | 0.0025 | 0.0069 | 0.0233 | 0.0177 |
| lookup | 0.0863 | 0.5251 | 0.8146 | 0.0079 | 0.0262 | 0.0538 | 0.0285 |
| mlp_16 | 0.0623 | 0.3058 | 0.6283 | 0.0119 | 0.0369 | 0.0213 | 0.1990 |
| neyman | 0.0542 | 0.4010 | 0.7441 | 0.0163 | 0.0625 | 0.9860 | 0.0106 |
| remaining | 0.0779 | 0.4052 | 0.7802 | 0.0095 | 0.0258 | 0.9767 | 0.0172 |
| tree_d3 | 0.1104 | 0.5479 | 0.9796 | 0.0013 | 0.0037 | 0.0250 | 0.1275 |
| tree_d6 | 0.0943 | 0.4752 | 0.8970 | 0.0052 | 0.0151 | 0.0250 | 0.1278 |

Exact optimal null alarm (false promotion) mean 0.0241; all approximate policies are evaluated under the same exact null calculation (columns `null_alarm_*`), so false-alarm validity is certified, not estimated (the null alarm of any predictable policy is bounded by the e-process threshold; values above the optimal policy's reflect different spending, not invalidity).

## Scaling of the exact solver (alternative (0.8, 0.7))
| horizon | budget | seconds | states | power_opt |
|---|---|---|---|---|
| 6.000 | 2.000 | 0.843 | 13226.000 | 0.000 |
| 6.000 | 4.000 | 1.516 | 50485.000 | 0.349 |
| 6.000 | 6.000 | 2.088 | 67091.000 | 0.349 |
| 8.000 | 2.000 | 0.834 | 51714.000 | 0.000 |
| 8.000 | 4.000 | 9.088 | 267035.000 | 0.364 |
| 8.000 | 6.000 | 23.906 | 482712.000 | 0.368 |
| 10.000 | 2.000 | 3.594 | 155361.000 | 0.001 |
| 10.000 | 4.000 | 43.766 | 902561.000 | 0.368 |
| 10.000 | 6.000 | 156.531 | 1970867.000 | 0.387 |
| 12.000 | 2.000 | 9.989 | 375753.000 | 0.001 |
| 12.000 | 4.000 | 146.619 | 2286939.000 | 0.370 |
| 12.000 | 6.000 | 794.362 | 5752557.000 | 0.399 |
