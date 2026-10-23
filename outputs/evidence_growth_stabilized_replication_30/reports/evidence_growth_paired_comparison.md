# Expected-evidence allocation: paired evaluation

This report analyzes `outputs/evidence_growth_stabilized_replication_30/metrics/method_comparison.parquet`. Independent stream seeds are the inferential units; all method contrasts are paired by seed. The monitor-period stream was not used to fit the outcome or decision-loss models.

## Detection, false escalation, budget use, and estimation

Rates have Wilson 95% intervals. `mean_query_propensity` is the average of predictable monitor propensities; labels are realized Bernoulli queries. The stream-mean RMSE is calculated across seed-level estimation errors.

| Scenario | Method | False escalations / streams (95% Wilson) | Detections / harmful streams (95% Wilson) | Labels/stream | Mean propensity | Stream-mean RMSE | Mean net cost |
|---|---|---:|---:|---:|---:|---:|---:|
| benign_nuisance | decision_value_proxy | 0/30 [0.000, 0.114] | 0/0 — | 349.6 | 0.1450 | 0.0503 | 190.30 |
| benign_nuisance | evidence_growth_stabilized_proxy | 0/30 [0.000, 0.114] | 0/0 — | 243.8 | 0.1009 | 0.0543 | 189.24 |
| benign_nuisance | uniform_proxy | 0/30 [0.000, 0.114] | 0/0 — | 241.6 | 0.1000 | 0.0504 | 189.22 |
| boundary_local_harm | decision_value_proxy | 0/30 [0.000, 0.114] | 0/30 [0.000, 0.114] | 245.2 | 0.1008 | 0.0894 | 648.19 |
| boundary_local_harm | evidence_growth_stabilized_proxy | 0/30 [0.000, 0.114] | 0/30 [0.000, 0.114] | 242.1 | 0.1000 | 0.0696 | 648.16 |
| boundary_local_harm | uniform_proxy | 0/30 [0.000, 0.114] | 3/30 [0.035, 0.256] | 241.6 | 0.1000 | 0.0727 | 648.16 |
| stationary | decision_value_proxy | 0/30 [0.000, 0.114] | 0/0 — | 250.7 | 0.1034 | 0.0666 | 189.31 |
| stationary | evidence_growth_stabilized_proxy | 0/30 [0.000, 0.114] | 0/0 — | 242.1 | 0.1000 | 0.0491 | 189.22 |
| stationary | uniform_proxy | 0/30 [0.000, 0.114] | 0/0 — | 241.6 | 0.1000 | 0.0493 | 189.22 |

## Paired differences versus uniform PPI

Intervals are percentile bootstrap intervals over paired seeds. They are descriptive, unadjusted across methods and metrics, and should not be read as confirmatory hypothesis tests.

| Scenario | Method | Metric | Difference vs uniform (95% paired bootstrap) | Seeds |
|---|---|---|---:|---:|
| benign_nuisance | decision_value_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| benign_nuisance | decision_value_proxy | labels_per_stream | +108.0333 [+83.8000, +131.9000] | 30 |
| benign_nuisance | decision_value_proxy | mean_query_propensity | +0.0450 [+0.0346, +0.0552] | 30 |
| benign_nuisance | decision_value_proxy | cumulative_net_cost | +1.0803 [+0.8410, +1.3187] | 30 |
| benign_nuisance | decision_value_proxy | stream_mean_rmse | -0.0001 [-0.0153, +0.0153] | 30 |
| benign_nuisance | evidence_growth_stabilized_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| benign_nuisance | evidence_growth_stabilized_proxy | labels_per_stream | +2.2333 [+1.2667, +3.2667] | 30 |
| benign_nuisance | evidence_growth_stabilized_proxy | mean_query_propensity | +0.0009 [+0.0006, +0.0014] | 30 |
| benign_nuisance | evidence_growth_stabilized_proxy | cumulative_net_cost | +0.0223 [+0.0127, +0.0327] | 30 |
| benign_nuisance | evidence_growth_stabilized_proxy | stream_mean_rmse | +0.0040 [-0.0040, +0.0132] | 30 |
| boundary_local_harm | decision_value_proxy | detection_rate | -0.1000 [-0.2333, +0.0000] | 30 |
| boundary_local_harm | decision_value_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| boundary_local_harm | decision_value_proxy | labels_per_stream | +3.6000 [-1.7333, +9.0000] | 30 |
| boundary_local_harm | decision_value_proxy | mean_query_propensity | +0.0008 [-0.0006, +0.0022] | 30 |
| boundary_local_harm | decision_value_proxy | cumulative_net_cost | +0.0360 [-0.0170, +0.0893] | 30 |
| boundary_local_harm | decision_value_proxy | stream_mean_rmse | +0.0166 [-0.0067, +0.0395] | 30 |
| boundary_local_harm | evidence_growth_stabilized_proxy | detection_rate | -0.1000 [-0.2333, +0.0000] | 30 |
| boundary_local_harm | evidence_growth_stabilized_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| boundary_local_harm | evidence_growth_stabilized_proxy | labels_per_stream | +0.5000 [-0.3333, +1.3000] | 30 |
| boundary_local_harm | evidence_growth_stabilized_proxy | mean_query_propensity | +0.0000 [-0.0001, +0.0001] | 30 |
| boundary_local_harm | evidence_growth_stabilized_proxy | cumulative_net_cost | +0.0050 [-0.0033, +0.0130] | 30 |
| boundary_local_harm | evidence_growth_stabilized_proxy | stream_mean_rmse | -0.0031 [-0.0122, +0.0066] | 30 |
| stationary | decision_value_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| stationary | decision_value_proxy | labels_per_stream | +9.1333 [+4.1667, +14.1667] | 30 |
| stationary | decision_value_proxy | mean_query_propensity | +0.0034 [+0.0020, +0.0049] | 30 |
| stationary | decision_value_proxy | cumulative_net_cost | +0.0913 [+0.0423, +0.1417] | 30 |
| stationary | decision_value_proxy | stream_mean_rmse | +0.0173 [-0.0015, +0.0359] | 30 |
| stationary | evidence_growth_stabilized_proxy | false_escalation_rate | +0.0000 [+0.0000, +0.0000] | 30 |
| stationary | evidence_growth_stabilized_proxy | labels_per_stream | +0.5000 [-0.3333, +1.3000] | 30 |
| stationary | evidence_growth_stabilized_proxy | mean_query_propensity | +0.0000 [-0.0001, +0.0001] | 30 |
| stationary | evidence_growth_stabilized_proxy | cumulative_net_cost | +0.0050 [-0.0033, +0.0130] | 30 |
| stationary | evidence_growth_stabilized_proxy | stream_mean_rmse | -0.0002 [-0.0063, +0.0075] | 30 |

## Interpretation boundary

The raw evidence-growth allocation may shift its average query rate under covariate shift because it is calibrated on the validation distribution. The stabilized version mixes it toward uniform; its stated rate-drift guarantee assumes every deployment propensity remains in `[q_min,q_max]`. Neither allocation changes the monitor's e-process validity conditions. The expected-log-growth optimization is exact only for its estimated outcome model and fixed stake-weighted surrogate; it is not an optimality claim for detection power or the exact log-mixture e-value.

Reproduce the underlying run with `uv run shiftlab-dive --seeds 30 --n 3200 --d 16 --query-rate 0.10 --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy decision_value_proxy evidence_growth_stabilized_proxy --device cuda --seed-offset 20272024 --evidence-rate-stability-tolerance 0.01 --output outputs/evidence_growth_stabilized_replication_30`, then run `uv run python scripts/analyze_evidence_growth_comparison.py`.
