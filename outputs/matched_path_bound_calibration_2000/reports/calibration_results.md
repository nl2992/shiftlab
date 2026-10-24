# Matched-path selected-schedule null calibration

- Streams per cell: 2000; selected schedule: `periodic_q080`; delay: 12; horizon: 2400.
- Requested/resolved data-generation device: cuda/cuda; replay device: CPU NumPy.
- Calibration family: two nonpositive-mean controls crossed with fixed/eventwise bounds; four exact one-sided limits use Bonferroni alpha 0.0125 per cell.
- Gate: PASS; every simultaneous upper limit must be at most 5%.
- Constant-q identity was verified in the preceding development block; this calibration tests only the selected variable-q schedule.
- No figure was generated; numerical tables and Parquet metrics are the prespecified outputs.

| scenario                                  | bound_mode   |   streams |   false_escalations |   false_escalation_rate |   simultaneous_one_sided_95_upper | passes_5pct_gate   |   mean_labels |   mean_events_processed |
|:------------------------------------------|:-------------|----------:|--------------------:|------------------------:|----------------------------------:|:-------------------|--------------:|------------------------:|
| markov_volatility_exact_marginal_null     | fixed        |      2000 |                  15 |                 0.00750 |                           0.01310 | True               |     474.74550 |              2373.74400 |
| markov_volatility_exact_marginal_null     | eventwise    |      2000 |                  48 |                 0.02400 |                           0.03286 | True               |     474.74550 |              2373.74400 |
| markov_volatility_strict_negative_control | fixed        |      2000 |                  10 |                 0.00500 |                           0.00984 | True               |     474.74550 |              2373.74400 |
| markov_volatility_strict_negative_control | eventwise    |      2000 |                  42 |                 0.02100 |                           0.02938 | True               |     474.74550 |              2373.74400 |
