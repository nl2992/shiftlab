# Delayed-feedback decision-harm benchmark (development pilot)

This benchmark compares a paired-cost bounded e-process with a source-upper / target-lower
confidence-bound monitor on the same randomly queried labels. The latter applies the
risk-monitoring architecture of [Podkopaev and Ramdas (2022)]
(https://arxiv.org/abs/2110.06177) to a bounded transform of paired cost contrasts.
It uses this repository's CM-EB confidence-sequence implementation and Hoeffding source
bound; it is a comparator implementation, not a full reproduction of their paper.

## Frozen development configuration

- Seeds: `20261024` through `20261053` (30 paired seeds per cell).
- Source/target lengths: `3000` / `3000`; query probability: `0.5`; materiality margin: `0.02`.
- Scenarios: `stationary, benign_variance_shift, boundary_harm`. Delays: `fixed_3, uniform_0_6`.
- Resolved generation device: `cuda`.
- Query selection and delays are generated independently of outcomes. Delays are fixed at
  three event-time units or uniform on integers 0 through 6 (mean three). Both monitors
  process queried observations in event order; wall delay records when the buffered evidence
  could actually be released.
- Boundary harm starts at 40% of the target stream. Its expected paired contrast rises
  from 0 to 0.24 (normalized bounded-risk increase 0.12); the variance-shift control lowers
  the contrast amplitude from 0.60 to 0.25 while keeping its mean at zero.

## Results

| scenario              | delay_scheme   | method                |   streams |   detection_rate |   false_escalation_rate |   median_event_delay |   median_wall_delay |   mean_labels_queried |   mean_shared_stream_labels_queried |   mean_labels_processed_at_alarm |   mean_pending_at_alarm |
|:----------------------|:---------------|:----------------------|----------:|-----------------:|------------------------:|---------------------:|--------------------:|----------------------:|------------------------------------:|---------------------------------:|------------------------:|
| benign_variance_shift | fixed_3        | no_query_hold         |        30 |            0.000 |                   0.000 |              nan     |             nan     |                 0.000 |                            1506.133 |                            0.000 |                 nan     |
| benign_variance_shift | fixed_3        | paired_cost_eprocess  |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| benign_variance_shift | fixed_3        | source_target_risk_cs |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| benign_variance_shift | uniform_0_6    | no_query_hold         |        30 |            0.000 |                   0.000 |              nan     |             nan     |                 0.000 |                            1506.133 |                            0.000 |                 nan     |
| benign_variance_shift | uniform_0_6    | paired_cost_eprocess  |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| benign_variance_shift | uniform_0_6    | source_target_risk_cs |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| boundary_harm         | fixed_3        | no_query_hold         |        30 |            0.000 |                   0.000 |              nan     |             nan     |                 0.000 |                            1506.133 |                            0.000 |                 nan     |
| boundary_harm         | fixed_3        | paired_cost_eprocess  |        30 |            1.000 |                   0.000 |             1010.500 |            1013.500 |              1506.133 |                            1506.133 |                         1116.733 |                   0.000 |
| boundary_harm         | fixed_3        | source_target_risk_cs |        30 |            0.767 |                   0.000 |             1342.000 |            1345.000 |              1506.133 |                            1506.133 |                         1327.767 |                   0.000 |
| boundary_harm         | uniform_0_6    | no_query_hold         |        30 |            0.000 |                   0.000 |              nan     |             nan     |                 0.000 |                            1506.133 |                            0.000 |                 nan     |
| boundary_harm         | uniform_0_6    | paired_cost_eprocess  |        30 |            1.000 |                   0.000 |             1010.500 |            1013.500 |              1506.133 |                            1506.133 |                         1116.733 |                   0.000 |
| boundary_harm         | uniform_0_6    | source_target_risk_cs |        30 |            0.767 |                   0.000 |             1342.000 |            1348.000 |              1506.133 |                            1506.133 |                         1327.767 |                   0.261 |
| stationary            | fixed_3        | no_query_hold         |        30 |            0.000 |                   0.000 |              nan     |             nan     |                 0.000 |                            1506.133 |                            0.000 |                 nan     |
| stationary            | fixed_3        | paired_cost_eprocess  |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| stationary            | fixed_3        | source_target_risk_cs |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| stationary            | uniform_0_6    | no_query_hold         |        30 |            0.000 |                   0.000 |              nan     |             nan     |                 0.000 |                            1506.133 |                            0.000 |                 nan     |
| stationary            | uniform_0_6    | paired_cost_eprocess  |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |
| stationary            | uniform_0_6    | source_target_risk_cs |        30 |            0.000 |                   0.000 |              nan     |             nan     |              1506.133 |                            1506.133 |                         1506.133 |                 nan     |

## Paired boundary-harm comparison

For `fixed_3`, paired detections were 30/30 (paired-cost e-process) and 23/30 (source/target risk CS); discordant streams were 7 vs. 0. The unadjusted exact two-sided McNemar/binomial p-value is `0.01562`. Treat this as exploratory: the same seed streams are reused across delay schemes, and the sample is not a confirmatory study.
For `uniform_0_6`, paired detections were 30/30 (paired-cost e-process) and 23/30 (source/target risk CS); discordant streams were 7 vs. 0. The unadjusted exact two-sided McNemar/binomial p-value is `0.01562`. Treat this as exploratory: the same seed streams are reused across delay schemes, and the sample is not a confirmatory study.

## Interpretation and limits

The paired-cost e-process detected the boundary-local mean increase earlier and on more
development streams than the source/target risk confidence-bound comparator. Neither
monitor escalated in the stationary or benign-variance controls in this small pilot.
The null result is weak evidence: 0/30 errors in a cell still permits a one-sided exact
95% false-escalation probability as high as 9.5%. The source/target method is naturally
slower here because its running target-risk bound includes the pre-change period.

The paired e-process guarantee requires its configured bounded increment and eventwise
conditional-mean null. The risk confidence-bound comparator uses an independent fixed
source sample, bounded losses, a source Hoeffding upper bound, and the target CM-EB lower
confidence sequence with alpha split across source and target. Both use random query
sampling independent of outcomes and outcome-independent label delays; event-order buffering
preserves the chronological evidence sequence. The no-query/hold row spends zero labels
and is a resource floor, not a label-matched monitor. This pilot does not test serial
dependence, outcome-dependent delay, adaptive model updates, policy-induced outcomes, or
candidate-selection multiplicity. It does not establish a novel algorithm or calibrated
false-alarm performance.

## Artifacts and reproducibility

- `delayed_feedback_metrics.parquet` and `delayed_feedback_metrics.csv`: stream-level outcomes.
- `summary.csv`: aggregate outcomes by scenario, delay and method.
- `manifest.json`: configuration, environment, metric checksum and source-code hashes.
- Metrics SHA-256: `f22eed636513d829b09fd73169cf9269900a6a2d3d1234d63b7948c656c0b55e`.
- Reproduce with: `python -m shiftlab.dive.delayed_benchmark --device cuda --output-dir outputs/delayed_feedback_development` (set `PYTHONPATH=src` in a source checkout).
- No figure is included: PaperBanana is not available as a callable tool in this session,
  and project guidance requires PaperBanana for visuals.
