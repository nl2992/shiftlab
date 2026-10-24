# Delayed decision-harm alternative confirmation

This independent confirmation tests the frozen primary comparison registered after null
calibration. It uses 2,000 paired seeds, late-onset weaker harm (onset 0.60, expected paired
contrast increase 0.12), a 0.25 query probability, and independent uniform delays 0–6.
All methods receive the same outcomes, query masks and delay stream within each seed.

- Seed interval: `20266000`–`20267999`.
- Resolved generation device: `cuda`.
- Primary paired test: exact two-sided McNemar test of restart mixture versus full-stream betting.
- Discordant pairs, restart-only / betting-only: `836` / `3`.
- Primary exact p-value: `5.37033e-245`.

| method               |   detected |   streams |   detection_rate |   cp95_lower |   cp95_upper |   mean_labels_processed_at_alarm_or_end |   mean_event_delay_detected |   mean_wall_delay_detected |
|:---------------------|-----------:|----------:|-----------------:|-------------:|-------------:|----------------------------------------:|----------------------------:|---------------------------:|
| paired_cost_eprocess |          1 |      2000 |          0.00050 |      0.00001 |      0.00278 |                               750.14300 |                  1044.00000 |                 1047.00000 |
| paired_cost_betting  |        100 |      2000 |          0.05000 |      0.04086 |      0.06048 |                               737.30800 |                   909.66000 |                  913.22000 |
| restart_mixture_8    |        933 |      2000 |          0.46650 |      0.44445 |      0.48865 |                               699.02500 |                   778.17256 |                  781.50268 |

The exact marginal intervals do not replace the paired primary test. Delay summaries are
conditional on detection; nondetections remain censored and are not assigned a numeric delay.
The source/target risk-CS comparator is excluded because it tests a different running-risk null.
The experiment establishes behavior only in this independent synthetic design; it does not
validate outcome-dependent delay, serial dependence, adaptive model updates, or real-data
assumptions. No algorithmic novelty is claimed.

Stream metrics, paired analysis, summary and manifest are all in this directory. No figure
is included because project guidance requires PaperBanana for visuals, and that tool is
unavailable here.
