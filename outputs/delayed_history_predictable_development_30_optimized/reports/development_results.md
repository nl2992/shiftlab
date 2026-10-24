# Delayed history-predictable bound development screen

- Streams per scenario and arm: 30
- Horizon: 2400; onset index: 1200
- Deterministic outcome-independent feedback delay: 12 events
- Hard query cap: 480 labels per stream
- Stream generation device: cuda; sequential monitor replay: CPU NumPy.
- This is a development screen; it is not confirmatory evidence or a method novelty claim.
- Under the iid event DGP, each q_t and its support bound are determined by previously committed prefix evidence and query spend. The queried contrast is revealed only after the registered delay, and the buffer commits evidence in event order.
- Future event contexts are independent of earlier pending outcomes under this DGP. This does not establish validity under serial dependence, outcome-dependent delay, adaptive action changes, or missing labels.
- Calibration must be evaluated on fresh independent nonpositive-mean controls before a separate harm confirmation.
- No figure was generated: PaperBanana is not available in the active environment.

| scenario                       | bound_mode   |   streams |   false_escalations |   detection_rate |   onset_reach_rate |   mean_labels |   mean_events_processed |   mean_event_delay |   mean_wall_delay |
|:-------------------------------|:-------------|----------:|--------------------:|-----------------:|-------------------:|--------------:|------------------------:|-------------------:|------------------:|
| high_cost_local_harm_d0.04     | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      293.8000 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      166.6333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      309.1333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | predictable  |        30 |                   0 |           0.0000 |             1.0000 |      178.2667 |               2398.7667 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      323.2667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | predictable  |        30 |                   0 |           0.0333 |             1.0000 |      195.1000 |               2369.6000 |           276.0000 |          288.0000 |
| high_cost_local_harm_d0.60     | fixed        |        30 |                   0 |           0.0000 |             1.0000 |      321.7333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.60     | predictable  |        30 |                   0 |           0.0667 |             1.0000 |      183.6333 |               2364.5333 |           656.0000 |          668.0000 |
| mixed_sign_exact_marginal_null | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      330.8333 |               2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null | predictable  |        30 |                   2 |           0.0000 |             0.0000 |      184.6333 |               2248.6667 |           nan      |          nan      |
| strict_negative_control        | fixed        |        30 |                   0 |           0.0000 |             0.0000 |      294.5333 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | predictable  |        30 |                   0 |           0.0000 |             0.0000 |      196.3667 |               2400.0000 |           nan      |          nan      |
