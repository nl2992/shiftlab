# Betting-mixture paired analysis

Candidate: **Broad multiscale**; comparator: the fixed five-stake mixture.

Across 60 independent seed clusters and 1200 evaluator-harm scenario-policy rows, the fixed mixture detected 49 (4.083%) and the candidate detected 44 (3.667%). The paired candidate-minus-fixed difference was -0.417% (95% percentile bootstrap interval [-0.917%, -0.083%]), resampling whole seeds across all 20 scenario-policy cells.

Discordant outcomes: candidate-only 0; fixed-only 5. Harm onsets were reached in 1200/1200 evaluator-harm rows.

The interval is descriptive for this predeclared synthetic block. It is not adjusted for any follow-on selection, and does not establish power or a general ordering.

## By scenario

|Scenario|Rows|Fixed detections|Candidate detections|Candidate-only|Fixed-only|Onsets reached|
|---|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|300|19|17|0|2|300|
|harmful_adaptation|300|13|13|0|0|300|
|recurring_regimes|300|17|14|0|3|300|
|residual_variance|300|0|0|0|0|300|

## By scenario and query policy

|Scenario|Policy|Rows|Fixed detections|Candidate detections|Candidate-only|Fixed-only|Onsets reached|
|---|---|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|60|3|3|0|0|60|
|boundary_local_harm|cost_variance_proxy|60|3|3|0|0|60|
|boundary_local_harm|decision_value_proxy|60|4|3|0|1|60|
|boundary_local_harm|uniform_proxy|60|5|4|0|1|60|
|boundary_local_harm|variance_proxy|60|4|4|0|0|60|
|harmful_adaptation|cost_stabilized_proxy|60|5|5|0|0|60|
|harmful_adaptation|cost_variance_proxy|60|2|2|0|0|60|
|harmful_adaptation|decision_value_proxy|60|0|0|0|0|60|
|harmful_adaptation|uniform_proxy|60|3|3|0|0|60|
|harmful_adaptation|variance_proxy|60|3|3|0|0|60|
|recurring_regimes|cost_stabilized_proxy|60|2|1|0|1|60|
|recurring_regimes|cost_variance_proxy|60|4|3|0|1|60|
|recurring_regimes|decision_value_proxy|60|2|2|0|0|60|
|recurring_regimes|uniform_proxy|60|4|4|0|0|60|
|recurring_regimes|variance_proxy|60|5|4|0|1|60|
|residual_variance|cost_stabilized_proxy|60|0|0|0|0|60|
|residual_variance|cost_variance_proxy|60|0|0|0|0|60|
|residual_variance|decision_value_proxy|60|0|0|0|0|60|
|residual_variance|uniform_proxy|60|0|0|0|0|60|
|residual_variance|variance_proxy|60|0|0|0|0|60|

## Controls and budget audit

|Scenario|Policy|Rows|Fixed any alarms|Candidate any alarms|Evaluator-harm rows|Onsets reached|Budget violations|
|---|---|---:|---:|---:|---:|---:|---:|
|No control scenarios|n/a|0|n/a|n/a|n/a|n/a|n/a|

Across all 1200 rows, budget violations: 0.

## Reproduction

Run `uv run python scripts/analyze_betting_mixture.py --input <run>/metrics/hard_budget_comparison.parquet --candidate-column multiscale_e_detected`. Bootstrap seed: `7731`; replicates: `20000`.

Analysis script SHA-256: `0c5454638de0c107eab963b819ba6dc5dc4c9ae7adf8af35ae0262c016af2d9c`.
