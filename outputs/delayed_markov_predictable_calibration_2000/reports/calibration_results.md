# Delayed Markov null calibration

- Streams per cell: 2000; delay: 12; horizon: 2400; labels capped at 480.
- Device: cuda; generation uses PyTorch; event-prefix monitor replay uses CPU NumPy.
- Family: two nonpositive-mean controls crossed with two monitor systems (four cells); exact one-sided Clopper-Pearson bounds use Bonferroni per-cell alpha 0.0125.
- Calibration gate: PASS; all simultaneous upper limits must be at most 5%.
- Monte Carlo calibration is specific to the registered two-state Markov DGP and implementation; the supermartingale argument supplies the stated mathematical guarantee under its assumptions.
- No figure was generated; this calibration is reported as a numeric table and Parquet stream file.

| scenario                                  | arm                  |   streams |   false_escalations |   false_escalation_rate |   simultaneous_one_sided_95_upper | passes_5pct_gate   |   mean_labels |   mean_processed_events |
|:------------------------------------------|:---------------------|----------:|--------------------:|------------------------:|----------------------------------:|:-------------------|--------------:|------------------------:|
| markov_volatility_exact_marginal_null     | delay_12_fixed       |      2000 |                   0 |                 0.00000 |                           0.00219 | True               |     303.27100 |              2399.99950 |
| markov_volatility_exact_marginal_null     | delay_12_predictable |      2000 |                  28 |                 0.01400 |                           0.02112 | True               |     177.53800 |              2374.57050 |
| markov_volatility_strict_negative_control | delay_12_fixed       |      2000 |                   0 |                 0.00000 |                           0.00219 | True               |     290.07150 |              2400.00000 |
| markov_volatility_strict_negative_control | delay_12_predictable |      2000 |                  25 |                 0.01250 |                           0.01930 | True               |     172.06100 |              2375.78550 |
