# Delayed history-predictable bound development screen

- Streams per scenario and arm: 30
- Horizon: 2400; onset index: 1200
- Feedback delay profile: positive_fast; fixed/slow delay: 12 events
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
| high_cost_local_harm_d0.04     | fixed        | positive_fast   |        30 |                   0 |           0.0000 |             1.0000 |      278.2667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.04     | predictable  | positive_fast   |        30 |                   1 |           0.0000 |             0.9667 |      166.0000 |               2322.5667 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | fixed        | positive_fast   |        30 |                   0 |           0.0000 |             1.0000 |      312.7667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.20     | predictable  | positive_fast   |        30 |                   0 |           0.0000 |             1.0000 |      154.5333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | fixed        | positive_fast   |        30 |                   0 |           0.0000 |             1.0000 |      314.7667 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.40     | predictable  | positive_fast   |        30 |                   0 |           0.0333 |             1.0000 |      186.1667 |               2373.2333 |           389.0000 |          397.0000 |
| high_cost_local_harm_d0.60     | fixed        | positive_fast   |        30 |                   0 |           0.0000 |             1.0000 |      297.3333 |               2400.0000 |           nan      |          nan      |
| high_cost_local_harm_d0.60     | predictable  | positive_fast   |        30 |                   0 |           0.1667 |             1.0000 |      180.2333 |               2347.0667 |           879.4000 |          882.4000 |
| mixed_sign_exact_marginal_null | fixed        | positive_fast   |        30 |                   0 |           0.0000 |             0.0000 |      306.8333 |               2400.0000 |           nan      |          nan      |
| mixed_sign_exact_marginal_null | predictable  | positive_fast   |        30 |                   0 |           0.0000 |             0.0000 |      182.4667 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | fixed        | positive_fast   |        30 |                   0 |           0.0000 |             0.0000 |      290.4667 |               2400.0000 |           nan      |          nan      |
| strict_negative_control        | predictable  | positive_fast   |        30 |                   0 |           0.0000 |             0.0000 |      171.1667 |               2400.0000 |           nan      |          nan      |
