# Predictable stake portfolio independent null calibration

- Streams per method and null: 2000; horizon: 2400; delay: 12.
- Device: cuda; generation and sequential delayed-feedback replay used the selected device.
- Family: two methods × two nonpositive-mean null/control scenarios; one-sided exact limits use Bonferroni alpha 0.05/4.
- Frozen calibration gate passed: `False`.
- Only if all four simultaneous upper limits are at most 5%, with no support/budget violations, may the disjoint confirmation run.
- The eta=0 and eta=1 procedures share query, label, enrollment, and event-prefix paths by construction.
- No figure was generated; PaperBanana is required for research visuals and unavailable in this session.

| scenario                                  | method                  |   streams |   false_escalations |   false_escalation_rate |   simultaneous_one_sided_95_upper |   budget_violations |   support_violations |
|:------------------------------------------|:------------------------|----------:|--------------------:|------------------------:|----------------------------------:|--------------------:|---------------------:|
| markov_volatility_exact_marginal_null     | fixed_mixture_eta1      |      2000 |                  48 |                 0.02400 |                           0.03286 |                   0 |                    0 |
| markov_volatility_exact_marginal_null     | uniform_rebalanced_eta0 |      2000 |                  88 |                 0.04400 |                           0.05541 |                   0 |                    0 |
| markov_volatility_strict_negative_control | fixed_mixture_eta1      |      2000 |                   4 |                 0.00200 |                           0.00563 |                   0 |                    0 |
| markov_volatility_strict_negative_control | uniform_rebalanced_eta0 |      2000 |                   5 |                 0.00250 |                           0.00637 |                   0 |                    0 |

Calibration failed; the alternative confirmation was not run.
