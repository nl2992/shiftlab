# Robust active-inference radius grid at a 20% budget: development results

This is the development screen registered in
[`robust_active_inference_radius_budget20_protocol.md`](robust_active_inference_radius_budget20_protocol.md).
It uses 30 new matched seeds per scenario, independent of the earlier 10% radius development
block. It is not an independent calibration or confirmatory study.

## Verification

The CUDA run produced all 810 rows (30 seeds × three scenarios × nine methods), used the RTX 4060
Laptop GPU with PyTorch 2.9.1+cu130/CUDA 13.0, and respected every hard label-dollar budget. Each
method used the same recorded support bound, 96.9, with minimum propensity 0.10. Every harmful
onset was reached in 30/30 boundary-local streams per method. Metrics and derived analysis files
have checksummed manifests. No plot was generated; all research visuals must use PaperBanana.

## Decision-relevant results

The table reports evaluator exposure if fallback happens **only after an alarm**; without an alarm,
the deployed policy continues through the monitoring horizon. The paired difference and interval
compare that exposure with uniform querying. The interval is a descriptive 95% paired seed-cluster
bootstrap and is unadjusted across the grid.

| Method | Macro stream-mean RMSE | Mean harm exposure under alarm-only fallback | Exposure difference vs uniform (95% CI) | Harm detections / 30 | Candidate-only / uniform-only detections | Mean labels | Mean spend | Mean events processed |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform | 0.0383 | 625.45 | 0.00 [0.00, 0.00] | 1/30 | 0/0 | 471.8 | 706.33 | 2335.2 |
| Variance | 0.0432 | 622.27 | -3.18 [-9.04, 0.00] | 2/30 | 1/0 | 476.2 | 712.37 | 2318.9 |
| Cost-variance | 0.0459 | 617.03 | -8.41 [-21.49, 0.00] | 2/30 | 1/0 | 497.2 | 713.00 | 2323.3 |
| Robust radius 0 | 0.0459 | 617.03 | -8.41 [-21.49, 0.00] | 2/30 | 1/0 | 497.2 | 713.00 | 2323.3 |
| Robust radius 0.1 | 0.0441 | 621.34 | -4.10 [-11.22, 0.00] | 2/30 | 1/0 | 493.5 | 712.94 | 2320.7 |
| Robust radius 0.25 | 0.0439 | 621.64 | -3.81 [-10.44, 0.00] | 3/30 | 2/0 | 489.0 | 712.32 | 2325.0 |
| Robust radius 0.5 | 0.0413 | 620.89 | -4.56 [-11.63, 0.00] | 3/30 | 2/0 | 484.1 | 710.16 | 2328.8 |
| Robust radius 1 | 0.0402 | 623.26 | -2.19 [-6.07, 0.00] | 2/30 | 1/0 | 480.0 | 708.35 | 2326.2 |
| Robust radius 2 | **0.0377** | 624.46 | -0.99 [-4.09, 1.13] | 2/30 | 1/0 | 477.2 | 707.56 | 2331.3 |

The harmonic-mean acquisition result at radius 0 is identical to cost-variance querying, as expected
from its zero uncertainty-radius setting. Radius 0.25 and 0.5 each detected two streams that
uniform missed, with no uniform-only detections; the one-sided exact paired McNemar p-value is 0.25
for each. Their paired detection-rate bootstrap intervals include zero. No method had a single-e
false escalation in either 30-stream null control. These small counts are diagnostic, not evidence
of calibration or a reliable power gain.

Radius 2 had the lowest macro RMSE, but its paired macro RMSE difference from uniform was -0.0007
(95% interval [-0.0039, 0.0021]). It therefore does not establish improved estimation either. The
budget-stop fallback sensitivity produces larger apparent exposure reductions because most streams
trigger fallback when their label budget runs out; those values are not evidence-triggered utility.

The common 96.9 support bound intentionally isolates the allocation choice by applying the adaptive
floor to uniform as well. It is conservative for uniform's actual fixed propensity of 0.20, whose
bound is 45.9. Therefore this screen compares allocation policies under a matched monitor bound;
it does not claim the best deployable policy-specific monitoring system. A policy-specific bound
comparison would require a separate registered calibration for any added acquisition rule.

## Interpretation and next step

**No radius is nominated for independent confirmation.** The small detection differences and
alarm-only exposure contrasts are inconclusive, and no radius has a statistically distinguishable
macro RMSE improvement over uniform. That does not justify the extra radius selection. The radius
branch remains a tested batch-inspired allocation sensitivity, not a new algorithm or intervention
result.

The stronger next research step is to connect a calibrated evidence process to an explicit
intervention policy, keeping monitor alarms, budget exhaustion, fallback episodes, and intervention
costs as separate outcomes. Query allocation should be treated as a matched design factor rather
than selected by estimation RMSE alone.

## Artifacts and reproduction

Seed-level metrics, the run manifest, derived CSV summaries, paired intervals, and the analysis
manifest are in
[`outputs/robust_active_inference_radius_budget20_development/`](../outputs/robust_active_inference_radius_budget20_development/).
Reproduce the CUDA run and analysis using the commands in the frozen
[protocol](robust_active_inference_radius_budget20_protocol.md). The analysis command is:

```powershell
uv run python scripts/analyze_radius_decision_harm_exposure.py --input outputs/robust_active_inference_radius_budget20_development/metrics/hard_budget_comparison.parquet --output-dir outputs/robust_active_inference_radius_budget20_development/analysis
```
