# Expected-evidence allocation: paired evaluation

This report analyzes `outputs/evidence_growth_replication_30/metrics/method_comparison.parquet`. Independent stream seeds are the inferential units; all method contrasts are paired by seed. The monitor-period stream was not used to fit the outcome or decision-loss models.

## Detection, false escalation, budget use, and estimation

Rates have Wilson 95% intervals. `mean_query_propensity` is the average of predictable monitor propensities; labels are realized Bernoulli queries. The stream-mean RMSE is calculated across seed-level estimation errors.

| Scenario | Method | False escalations / streams (95% Wilson) | Detections / harmful streams (95% Wilson) | Labels/stream | Mean propensity | Stream-mean RMSE | Mean net cost |
|---|---|---:|---:|---:|---:|---:|---:|
| benign_nuisance | decision_value_proxy | 0/30 [0.000, 0.114] | 0/0 — | 329.9 | 0.1373 | 0.0669 | 194.75 |
| benign_nuisance | evidence_growth_proxy | 0/30 [0.000, 0.114] | 0/0 — | 335.0 | 0.1386 | 0.0241 | 194.80 |
| benign_nuisance | uniform_proxy | 0/30 [0.000, 0.114] | 0/0 — | 235.9 | 0.1000 | 0.0724 | 193.81 |
| boundary_local_harm | decision_value_proxy | 0/30 [0.000, 0.114] | 0/30 [0.000, 0.114] | 238.3 | 0.1008 | 0.0834 | 671.24 |
| boundary_local_harm | evidence_growth_proxy | 0/30 [0.000, 0.114] | 0/30 [0.000, 0.114] | 237.8 | 0.0990 | 0.0224 | 671.24 |
| boundary_local_harm | uniform_proxy | 0/30 [0.000, 0.114] | 1/30 [0.006, 0.167] | 235.9 | 0.1000 | 0.0698 | 671.22 |
| stationary | decision_value_proxy | 0/30 [0.000, 0.114] | 0/0 — | 242.9 | 0.1029 | 0.0733 | 193.88 |
| stationary | evidence_growth_proxy | 0/30 [0.000, 0.114] | 0/0 — | 237.8 | 0.0990 | 0.0174 | 193.83 |
| stationary | uniform_proxy | 0/30 [0.000, 0.114] | 0/0 — | 235.9 | 0.1000 | 0.0695 | 193.81 |

## Paired differences versus uniform PPI

Intervals are percentile bootstrap intervals over paired seeds. They are descriptive, unadjusted across methods and metrics, and should not be read as confirmatory hypothesis tests.

| Scenario | Method | Metric | Difference vs uniform (95% paired bootstrap) | Seeds |
|---|---|---|---:|---:|
| benign_nuisance | decision_value_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| benign_nuisance | decision_value_proxy | labels_per_stream | +94.0000 [+75.3333, +112.9667] | 30 |
| benign_nuisance | decision_value_proxy | mean_query_propensity | +0.0373 [+0.0299, +0.0448] | 30 |
| benign_nuisance | decision_value_proxy | cumulative_net_cost | +0.9400 [+0.7517, +1.1273] | 30 |
| benign_nuisance | decision_value_proxy | stream_mean_rmse | -0.0055 [-0.0236, +0.0131] | 30 |
| benign_nuisance | evidence_growth_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| benign_nuisance | evidence_growth_proxy | labels_per_stream | +99.0667 [+62.0000, +139.2008] | 30 |
| benign_nuisance | evidence_growth_proxy | mean_query_propensity | +0.0386 [+0.0238, +0.0549] | 30 |
| benign_nuisance | evidence_growth_proxy | cumulative_net_cost | +0.9907 [+0.6240, +1.3953] | 30 |
| benign_nuisance | evidence_growth_proxy | stream_mean_rmse | -0.0483 [-0.0628, -0.0313] | 30 |
| boundary_local_harm | decision_value_proxy | detection_rate | -0.0333 [-0.1000, +0.0000] | 30 |
| boundary_local_harm | decision_value_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| boundary_local_harm | decision_value_proxy | labels_per_stream | +2.3667 [-1.5333, +6.1333] | 30 |
| boundary_local_harm | decision_value_proxy | mean_query_propensity | +0.0008 [-0.0000, +0.0016] | 30 |
| boundary_local_harm | decision_value_proxy | cumulative_net_cost | +0.0237 [-0.0153, +0.0617] | 30 |
| boundary_local_harm | decision_value_proxy | stream_mean_rmse | +0.0135 [-0.0051, +0.0330] | 30 |
| boundary_local_harm | evidence_growth_proxy | detection_rate | -0.0333 [-0.1000, +0.0000] | 30 |
| boundary_local_harm | evidence_growth_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| boundary_local_harm | evidence_growth_proxy | labels_per_stream | +1.9000 [-5.2333, +9.2000] | 30 |
| boundary_local_harm | evidence_growth_proxy | mean_query_propensity | -0.0010 [-0.0031, +0.0011] | 30 |
| boundary_local_harm | evidence_growth_proxy | cumulative_net_cost | +0.0190 [-0.0520, +0.0910] | 30 |
| boundary_local_harm | evidence_growth_proxy | stream_mean_rmse | -0.0474 [-0.0625, -0.0312] | 30 |
| stationary | decision_value_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| stationary | decision_value_proxy | labels_per_stream | +7.0000 [+2.8000, +11.3667] | 30 |
| stationary | decision_value_proxy | mean_query_propensity | +0.0029 [+0.0018, +0.0040] | 30 |
| stationary | decision_value_proxy | cumulative_net_cost | +0.0700 [+0.0283, +0.1137] | 30 |
| stationary | decision_value_proxy | stream_mean_rmse | +0.0038 [-0.0069, +0.0151] | 30 |
| stationary | evidence_growth_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| stationary | evidence_growth_proxy | labels_per_stream | +1.9000 [-5.2000, +9.2667] | 30 |
| stationary | evidence_growth_proxy | mean_query_propensity | -0.0010 [-0.0031, +0.0011] | 30 |
| stationary | evidence_growth_proxy | cumulative_net_cost | +0.0190 [-0.0523, +0.0927] | 30 |
| stationary | evidence_growth_proxy | stream_mean_rmse | -0.0522 [-0.0660, -0.0374] | 30 |

## Interpretation boundary

The raw evidence-growth allocation may shift its average query rate under covariate shift because it is calibrated on the validation distribution. The stabilized version mixes it toward uniform; its stated rate-drift guarantee assumes every deployment propensity remains in `[q_min,q_max]`. Neither allocation changes the monitor's e-process validity conditions. The expected-log-growth optimization is exact only for its estimated outcome model and fixed stake-weighted surrogate; it is not an optimality claim for detection power or the exact log-mixture e-value.

Reproduce the underlying run with `uv run shiftlab-dive --seeds 30 --n 3200 --d 16 --query-rate 0.10 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy decision_value_proxy evidence_growth_stabilized_proxy --device cuda --seed-offset 20272024 --evidence-rate-stability-tolerance 0.01 --output outputs/evidence_growth_stabilized_replication_30`, then run `uv run python scripts/analyze_evidence_growth_comparison.py`.
