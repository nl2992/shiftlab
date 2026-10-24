# Delayed history-predictable bound development screen

- Streams per scenario and arm: 30
- Horizon: 2400; onset index: 1200
- Feedback delay profile: fixed; fixed/slow delay: 12 events
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
| high_cost_local_harm_d0.04     | fixed        | fixed           |        30 |                   0 |           0.0000 |             1.0000 |      274.0000 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     | predictable  | fixed           |        30 |                   0 |           0.0000 |             1.0000 |      158.4667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | fixed        | fixed           |        30 |                   0 |           0.0000 |             1.0000 |      296.2333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | predictable  | fixed           |        30 |                   0 |           0.0000 |             1.0000 |      157.7000 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | fixed        | fixed           |        30 |                   0 |           0.0000 |             1.0000 |      308.7000 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | predictable  | fixed           |        30 |                   0 |           0.0333 |             1.0000 |      185.9667 |               2370.6000 |           306.0000 |          318.0000 |
| high_cost_local_harm_d0.60     | fixed        | fixed           |        30 |                   0 |           0.0000 |             1.0000 |      303.1333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.60     | predictable  | fixed           |        30 |                   0 |           0.0667 |             1.0000 |      178.4667 |               2369.0000 |           723.0000 |          735.0000 |
| mixed_sign_exact_marginal_null | fixed        | fixed           |        30 |                   0 |           0.0000 |             0.0000 |      302.5333 |               2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null | predictable  | fixed           |        30 |                   0 |           0.0000 |             0.0000 |      178.3333 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | fixed        | fixed           |        30 |                   0 |           0.0000 |             0.0000 |      281.7333 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | predictable  | fixed           |        30 |                   1 |           0.0000 |             0.0000 |      175.5667 |               2352.7000 |           nan      |          nan      |
