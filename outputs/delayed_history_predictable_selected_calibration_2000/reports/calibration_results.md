# Delayed history-predictable independent null calibration

- Streams per scenario and arm: 2000
- Total stream-arm rows: 8000
- Horizon / fixed delay / hard cap: 2400 / 12 / 480 labels
- Root seed: 27504027; stream generation: cuda; sequential monitor replay: CPU NumPy.
- Four-cell Bonferroni family uses per-cell alpha 0.01250.
- Frozen protocol: `docs/delayed_history_predictable_selected_calibration_protocol.md`.
- Calibration gate: PASS.
- A pass applies only to the registered iid synthetic controls and stated filtration. It does not establish power, serial-dependence validity, or novelty.
- No figure was generated; PaperBanana is unavailable in this environment.

| scenario                       | arm         |   streams |   false_escalations |   false_rate |   simultaneous_one_sided_95_upper |   per_cell_alpha | passes_5pct_calibration_gate   |   mean_labels |   mean_events_processed |
|:-------------------------------|:------------|----------:|--------------------:|-------------:|----------------------------------:|-----------------:|:-------------------------------|--------------:|------------------------:|
| mixed_sign_exact_marginal_null | fixed       |      2000 |                   5 |      0.00250 |                           0.00637 |          0.01250 | True                           |     298.69650 |              2399.29900 |
| mixed_sign_exact_marginal_null | predictable |      2000 |                  44 |      0.02200 |                           0.03054 |          0.01250 | True                           |     172.13300 |              2359.90100 |
| strict_negative_control        | fixed       |      2000 |                   1 |      0.00050 |                           0.00319 |          0.01250 | True                           |     283.55850 |              2399.92850 |
| strict_negative_control        | predictable |      2000 |                  30 |      0.01500 |                           0.02231 |          0.01250 | True                           |     167.13450 |              2372.02500 |
