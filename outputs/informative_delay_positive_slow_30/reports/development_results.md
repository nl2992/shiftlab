# Delayed history-predictable bound development screen

- Streams per scenario and arm: 30
- Horizon: 2400; onset index: 1200
- Feedback delay profile: positive_slow; fixed/slow delay: 12 events
- Hard query cap: 480 labels per stream
- Stream generation device: cuda; sequential monitor replay: CPU NumPy.
- This is a development screen; it is not confirmatory evidence or a method novelty claim.
- Under the iid event DGP, each q_t and its support bound are determined by previously committed prefix evidence and query spend. The monitor commits evidence in event order; latency is never included as a model feature or evidence increment.
- In positive_fast/positive_slow, the evaluator assigns 1-event versus configured-delay labels based on the sign of the queried decision-cost contrast. These are informative-delay power/latency stress conditions, not new validity calibration.
- The null guarantee requires the event-time conditional-mean null and a valid predictable bound given the full history used by querying. See docs/delayed_event_prefix_validity.md; no serial-dependence or policy-adaptation claim is made.
- Calibration must be evaluated on fresh independent nonpositive-mean controls before a separate harm confirmation.
- No figure was generated: PaperBanana is not available in the active environment.

| scenario                       | bound_mode   | delay_profile   |   streams |   false_escalations |   detection_rate |   onset_reach_rate |   mean_labels |   mean_events_processed |   mean_event_delay |   mean_wall_delay |
|:-------------------------------|:-------------|:----------------|----------:|--------------------:|-----------------:|-------------------:|--------------:|------------------------:|-------------------:|------------------:|
| high_cost_local_harm_d0.04     | fixed        | positive_slow   |        30 |                   0 |           0.0000 |             1.0000 |      269.0333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     | predictable  | positive_slow   |        30 |                   0 |           0.0000 |             1.0000 |      158.5667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | fixed        | positive_slow   |        30 |                   0 |           0.0000 |             1.0000 |      277.2667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | predictable  | positive_slow   |        30 |                   0 |           0.0000 |             1.0000 |      153.2333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | fixed        | positive_slow   |        30 |                   0 |           0.0000 |             1.0000 |      301.7667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | predictable  | positive_slow   |        30 |                   0 |           0.0333 |             1.0000 |      183.8000 |               2370.6333 |           307.0000 |          319.0000 |
| high_cost_local_harm_d0.60     | fixed        | positive_slow   |        30 |                   0 |           0.0000 |             1.0000 |      297.3667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.60     | predictable  | positive_slow   |        30 |                   0 |           0.2000 |             1.0000 |      185.7667 |               2345.5333 |           915.6667 |          927.6667 |
| mixed_sign_exact_marginal_null | fixed        | positive_slow   |        30 |                   0 |           0.0000 |             0.0000 |      305.0000 |               2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null | predictable  | positive_slow   |        30 |                   0 |           0.0000 |             0.0000 |      180.2000 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | fixed        | positive_slow   |        30 |                   0 |           0.0000 |             0.0000 |      277.2667 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | predictable  | positive_slow   |        30 |                   0 |           0.0000 |             0.0000 |      153.1667 |               2400.0000 |           nan      |          nan      |
