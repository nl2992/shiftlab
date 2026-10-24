# Delayed decision-harm alternative confirmation

This independent confirmation tests the frozen primary comparison registered after null
calibration. It uses 2,000 paired seeds, late-onset weaker harm (onset 0.60, expected paired
contrast increase 0.12), a 0.25 query probability, and independent uniform delays 0–6.
All methods receive the same outcomes, query masks and delay stream within each seed.

- Seed interval: `20268000`–`20269999`.
- Resolved generation device: `cuda`.
- Primary paired test: exact two-sided McNemar test of restart mixture versus full-stream betting.
- Discordant pairs, restart-only / betting-only: `801` / `6`.
- Primary exact p-value: `8.88994e-229`.

| method               |   detected |   streams |   detection_rate |   cp95_lower |   cp95_upper |   mean_labels_processed_at_alarm_or_end |   mean_event_delay_detected |   mean_wall_delay_detected |
|:---------------------|-----------:|----------:|-----------------:|-------------:|-------------:|----------------------------------------:|----------------------------:|---------------------------:|
| paired_cost_eprocess |          1 |      2000 |          0.00050 |      0.00001 |      0.00278 |                               750.22200 |                  1195.00000 |                 1197.00000 |
| paired_cost_betting  |        100 |      2000 |          0.05000 |      0.04086 |      0.06048 |                               737.21900 |                   932.48000 |                  935.92000 |
| restart_mixture_8    |        895 |      2000 |          0.44750 |      0.42555 |      0.46961 |                               699.89300 |                   774.01229 |                  777.32626 |

The exact marginal intervals do not replace the paired primary test. Delay summaries are
conditional on detection; nondetections remain censored and are not assigned a numeric delay.
The source/target risk-CS comparator is excluded because it tests a different running-risk null.
The experiment establishes behavior only in this independent synthetic design; it does not
validate outcome-dependent delay, serial dependence, adaptive model updates, or real-data
assumptions. No algorithmic novelty is claimed.

Stream metrics, paired analysis, summary and manifest are all in this directory. No figure
is included because project guidance requires PaperBanana for visuals, and that tool is
unavailable here.
