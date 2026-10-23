# ShiftLab Phase 2 decision-harm baseline

Run: `20261023T0230Z-final-30seed`. This report is generated from 30 independent evaluation seeds per scenario; calibration used 60 disjoint stationary seeds.

## Scientific scope

The benchmark separates feature-distribution discrepancy, predictive loss change, and expected deployed-versus-reference decision cost. The deployed classifier is an idealized fixed linear-signal rule at threshold 0.5; its explicit challenger is the fixed source cost-minimizing rule. Harmful adaptation deliberately intervenes by always taking action 1. Scenarios are controlled synthetic examples; imposed costs are research utilities, not validated application costs. This isolates monitor behavior and is not a learned-model comparison.

## Aggregate metrics

| Scenario | Mean MMD² | Predictive loss change | Expected harm vs reference | Mean cumulative regret (SD) |
|---|---:|---:|---:|---:|
| stationary | -0.0021136 | 0.00079191 | 0.078428 | 188.2 (19.8) |
| benign_nuisance | 0.49112 | 0.00079191 | 0.078428 | 188.2 (19.8) |
| boundary_local_harm | -0.0021136 | 0.089038 | 0.27585 | 737.5 (57.8) |
| residual_variance | -0.0021136 | 0.31837 | 0.11314 | 370.8 (25.4) |
| recurring_regimes | -0.0021136 | 0.089649 | 0.27228 | 729.2 (63.5) |
| harmful_adaptation | -0.0021136 | 0.00079191 | 0.27289 | 654.9 (18.7) |

## Harm-monitor false escalation, detection and delay

False escalation is an alarm before the known evaluator-defined harm onset or any alarm in a scenario whose expected harm does not exceed epsilon. Detection rates count alarms at or after onset; nondetections remain in the denominator and are right-censored at the horizon. Median delays are conditional on detection.

| Scenario | Monitor | False escalation rate | Detection rate | Median delay |
|---|---|---:|---:|---:|
| benign_nuisance | paired_cost_cusum | 0.033 | 0.000 | not detected |
| benign_nuisance | paired_cost_eprocess | 0.000 | 0.000 | not detected |
| benign_nuisance | predictive_cusum | 0.033 | 0.000 | not detected |
| boundary_local_harm | paired_cost_cusum | 0.000 | 1.000 | 207.0 |
| boundary_local_harm | paired_cost_eprocess | 0.000 | 0.000 | not detected |
| boundary_local_harm | predictive_cusum | 0.000 | 1.000 | 31.0 |
| harmful_adaptation | paired_cost_cusum | 0.000 | 0.167 | 223.0 |
| harmful_adaptation | paired_cost_eprocess | 0.000 | 0.000 | not detected |
| harmful_adaptation | predictive_cusum | 0.000 | 0.033 | 383.0 |
| recurring_regimes | paired_cost_cusum | 0.000 | 1.000 | 239.0 |
| recurring_regimes | paired_cost_eprocess | 0.000 | 0.000 | not detected |
| recurring_regimes | predictive_cusum | 0.000 | 1.000 | 63.0 |
| residual_variance | paired_cost_cusum | 0.000 | 0.033 | 1407.0 |
| residual_variance | paired_cost_eprocess | 0.000 | 0.000 | not detected |
| residual_variance | predictive_cusum | 0.000 | 1.000 | 31.0 |
| stationary | paired_cost_cusum | 0.033 | 0.000 | not detected |
| stationary | paired_cost_eprocess | 0.000 | 0.000 | not detected |
| stationary | predictive_cusum | 0.033 | 0.000 | not detected |

## Distribution-change sentinel

MMD alarm performance is evaluated against known feature-distribution changes, separately from decision harm. Only the nuisance scenario changes P(X); all other scenarios have fixed feature marginals.

| Scenario | False distribution alarm rate | Feature-shift detection rate | Median delay |
|---|---:|---:|---:|
| benign_nuisance | 0.033 | 0.967 | 31.0 |
| boundary_local_harm | 0.033 | 0.000 | not applicable/detected |
| harmful_adaptation | 0.033 | 0.000 | not applicable/detected |
| recurring_regimes | 0.033 | 0.000 | not applicable/detected |
| residual_variance | 0.033 | 0.000 | not applicable/detected |
| stationary | 0.033 | 0.000 | not applicable/detected |

## Figures and data

- `estimands_by_scenario.png` compares the three distinct estimands.
- `alarms_and_delay.png` summarizes false harm escalations and detection delays.
- `cumulative_regret.png` shows evaluator-oracle regret.
- `metrics.parquet`, `alarm_metrics.parquet`, and `monitor_trace.parquet` contain seed-level results and traces.
- `manifest.json` records configuration, seeds, thresholds, assumptions, software versions and source hashes.

## Limitations

The rank calibration is marginal under exchangeability of independent stationary calibration and evaluation streams, at a fixed horizon and scenario family; it is not robust to serial dependence, drift in the null, tuning on evaluation results, or post-selection. The paired e-process is only a valid example under the bounded full-feedback conditional null stated in the manifest and source, with the fixed prespecified epsilon=0.10 cost-unit threshold; it is not valid for selective missing labels or unknown counterfactuals. No asymptotic/finite-sample guarantee is claimed for discrepancy or CUSUM aside from the stated independent-run rank calibration. The benchmark does not settle adaptation selection, delayed or adaptively sampled labels, or utility misspecification.
