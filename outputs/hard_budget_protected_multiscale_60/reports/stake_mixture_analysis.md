# Betting-mixture paired analysis

Candidate: **Protected multiscale**; comparator: the fixed five-stake mixture.

Across 60 independent seed clusters and 1200 evaluator-harm scenario-policy rows, the fixed mixture detected 39 (3.250%) and the candidate detected 32 (2.667%). The paired candidate-minus-fixed difference was -0.583% (95% percentile bootstrap interval [-1.000%, -0.250%]), resampling whole seeds across all 20 scenario-policy cells.

Discordant outcomes: candidate-only 0; fixed-only 7. Harm onsets were reached in 1200/1200 evaluator-harm rows.

The interval is descriptive for this predeclared synthetic block. It is not adjusted for any follow-on selection, and does not establish power or a general ordering.

## By scenario

|Scenario|Rows|Fixed detections|Candidate detections|Candidate-only|Fixed-only|Onsets reached|
|---|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|300|19|15|0|4|300|
|harmful_adaptation|300|2|1|0|1|300|
|recurring_regimes|300|18|16|0|2|300|
|residual_variance|300|0|0|0|0|300|

## By scenario and query policy

|Scenario|Policy|Rows|Fixed detections|Candidate detections|Candidate-only|Fixed-only|Onsets reached|
|---|---|---:|---:|---:|---:|---:|---:|
|boundary_local_harm|cost_stabilized_proxy|60|3|3|0|0|60|
|boundary_local_harm|cost_variance_proxy|60|3|2|0|1|60|
|boundary_local_harm|decision_value_proxy|60|4|4|0|0|60|
|boundary_local_harm|uniform_proxy|60|4|3|0|1|60|
|boundary_local_harm|variance_proxy|60|5|3|0|2|60|
|harmful_adaptation|cost_stabilized_proxy|60|1|0|0|1|60|
|harmful_adaptation|cost_variance_proxy|60|1|1|0|0|60|
|harmful_adaptation|decision_value_proxy|60|0|0|0|0|60|
|harmful_adaptation|uniform_proxy|60|0|0|0|0|60|
|harmful_adaptation|variance_proxy|60|0|0|0|0|60|
|recurring_regimes|cost_stabilized_proxy|60|4|4|0|0|60|
|recurring_regimes|cost_variance_proxy|60|5|3|0|2|60|
|recurring_regimes|decision_value_proxy|60|2|2|0|0|60|
|recurring_regimes|uniform_proxy|60|4|4|0|0|60|
|recurring_regimes|variance_proxy|60|3|3|0|0|60|
|residual_variance|cost_stabilized_proxy|60|0|0|0|0|60|
|residual_variance|cost_variance_proxy|60|0|0|0|0|60|
|residual_variance|decision_value_proxy|60|0|0|0|0|60|
|residual_variance|uniform_proxy|60|0|0|0|0|60|
|residual_variance|variance_proxy|60|0|0|0|0|60|

## Controls and budget audit

|Scenario|Policy|Rows|Fixed any alarms|Candidate any alarms|Pathwise oracle materiality flags|Population-null harm onsets|Budget violations|
|---|---|---:|---:|---:|---:|---:|---:|
|benign_nuisance|cost_stabilized_proxy|60|0|0|7|0|0|
|benign_nuisance|cost_variance_proxy|60|0|0|7|0|0|
|benign_nuisance|decision_value_proxy|60|0|0|7|0|0|
|benign_nuisance|uniform_proxy|60|0|0|7|0|0|
|benign_nuisance|variance_proxy|60|0|0|7|0|0|
|stationary|cost_stabilized_proxy|60|0|0|1|0|0|
|stationary|cost_variance_proxy|60|0|0|1|0|0|
|stationary|decision_value_proxy|60|0|0|1|0|0|
|stationary|uniform_proxy|60|0|0|1|0|0|
|stationary|variance_proxy|60|0|0|1|0|0|

Across all 1800 rows, budget violations: 0.

## Reproduction

Run `uv run python scripts/analyze_betting_mixture.py --input <run>/metrics/hard_budget_comparison.parquet --candidate-column protected_e_detected`. Bootstrap seed: `7731`; replicates: `20000`.

Analysis script SHA-256: `e7becb009de9876d3795751db370e2403ee503cac6432d4950e94366ebff2be2`.
