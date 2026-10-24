# Delayed decision-harm null calibration

Independent null calibration with disjoint seeds from both development runs. Every method
receives the same outcomes and query random numbers within a scenario/seed/query-rate cell.
The 95% intervals are exact two-sided Clopper–Pearson intervals; cells are reported
separately and are not pooled.

- Seeds: `20264000`–`20265999` per scenario.
- Query rates: `0.1, 0.25, 0.5`; horizon: `3000`.
- Delay: `uniform_0_6`; resolved generator device: `cuda`.
- Independent stream cells: `12000`.

| scenario              |   query_rate | method               |   false_escalations |   streams |   false_escalation_rate |   cp95_lower |   cp95_upper |   max_observed_wall_alarm |
|:----------------------|-------------:|:---------------------|--------------------:|----------:|------------------------:|-------------:|-------------:|--------------------------:|
| benign_variance_shift |      0.10000 | paired_cost_betting  |                  29 |      2000 |                 0.01450 |      0.00973 |      0.02076 |                 933.00000 |
| benign_variance_shift |      0.10000 | paired_cost_eprocess |                   0 |      2000 |                 0.00000 |      0.00000 |      0.00184 |                 nan       |
| benign_variance_shift |      0.10000 | restart_mixture_8    |                  13 |      2000 |                 0.00650 |      0.00347 |      0.01109 |                2301.00000 |
| benign_variance_shift |      0.25000 | paired_cost_betting  |                  27 |      2000 |                 0.01350 |      0.00891 |      0.01958 |                 861.00000 |
| benign_variance_shift |      0.25000 | paired_cost_eprocess |                   0 |      2000 |                 0.00000 |      0.00000 |      0.00184 |                 nan       |
| benign_variance_shift |      0.25000 | restart_mixture_8    |                  13 |      2000 |                 0.00650 |      0.00347 |      0.01109 |                1312.00000 |
| benign_variance_shift |      0.50000 | paired_cost_betting  |                  27 |      2000 |                 0.01350 |      0.00891 |      0.01958 |                 684.00000 |
| benign_variance_shift |      0.50000 | paired_cost_eprocess |                   0 |      2000 |                 0.00000 |      0.00000 |      0.00184 |                 nan       |
| benign_variance_shift |      0.50000 | restart_mixture_8    |                   4 |      2000 |                 0.00200 |      0.00055 |      0.00511 |                1179.00000 |
| stationary            |      0.10000 | paired_cost_betting  |                  30 |      2000 |                 0.01500 |      0.01014 |      0.02134 |                2833.00000 |
| stationary            |      0.10000 | paired_cost_eprocess |                   0 |      2000 |                 0.00000 |      0.00000 |      0.00184 |                 nan       |
| stationary            |      0.10000 | restart_mixture_8    |                  21 |      2000 |                 0.01050 |      0.00651 |      0.01601 |                2908.00000 |
| stationary            |      0.25000 | paired_cost_betting  |                  27 |      2000 |                 0.01350 |      0.00891 |      0.01958 |                 861.00000 |
| stationary            |      0.25000 | paired_cost_eprocess |                   0 |      2000 |                 0.00000 |      0.00000 |      0.00184 |                 nan       |
| stationary            |      0.25000 | restart_mixture_8    |                  27 |      2000 |                 0.01350 |      0.00891 |      0.01958 |                2987.00000 |
| stationary            |      0.50000 | paired_cost_betting  |                  27 |      2000 |                 0.01350 |      0.00891 |      0.01958 |                 684.00000 |
| stationary            |      0.50000 | paired_cost_eprocess |                   0 |      2000 |                 0.00000 |      0.00000 |      0.00184 |                 nan       |
| stationary            |      0.50000 | restart_mixture_8    |                  14 |      2000 |                 0.00700 |      0.00383 |      0.01172 |                2941.00000 |

These finite-sample rates are calibration evidence for the registered synthetic nulls, not
a substitute for the e-process proof. The betting and restart mixture must satisfy the
bounded eventwise conditional-mean null; queries and delays are generated independently of
the current outcome. The result does not cover informative delay, serial dependence,
selective query rules that violate the stated filtration, or policy-induced outcomes.

No figure is included because project guidance requires PaperBanana for visuals, and no
PaperBanana tool is available in this session.
