# Robust active-inference radius grid: development results

This frozen development screen compares six L2 uncertainty-radius fractions for the
validation-selected robust active-inference allocation. The design and reproduction command are
in [the protocol](robust_active_inference_radius_grid_protocol.md); the preceding method mapping
and theorem limits are in [closest competitors](../references/closest_competitors.md).

## Results

The CUDA run completed **810 method-stream rows** (30 seeds × three scenarios × nine policies).
Every stream respected its hard dollar cap. Every one of the 30 boundary-local harm onsets was
reached for every policy. The single-start paired-cost monitor detected **0/30** harms at every
radius and on each matched reference. Each policy had zero false escalations in each 30-stream
stationary and benign-nuisance control cell; those small counts do not establish calibration.

| Radius fraction | Stationary RMSE | Benign nuisance RMSE | Boundary harm RMSE | Macro RMSE, equal scenario MSE |
|---:|---:|---:|---:|---:|
| 0.00 | 0.0653 | 0.0755 | 0.0795 | 0.0737 |
| 0.10 | 0.0639 | 0.0755 | 0.0716 | 0.0705 |
| 0.25 | 0.0575 | **0.0726** | 0.0747 | 0.0687 |
| 0.50 | **0.0565** | 0.0763 | **0.0713** | **0.0686** |
| 1.00 | 0.0592 | 0.0781 | 0.0755 | 0.0715 |
| 2.00 | 0.0597 | 0.0792 | 0.0802 | 0.0736 |

The primary macro development score ranks radius fraction 0.50 first, but only narrowly ahead of
0.25. The paired seed-cluster bootstrap interval for their macro RMSE difference (0.50 minus
0.25) is **−0.0042 to +0.0041**, including zero. Relative to uniform, radius 0.50's macro RMSE
difference is **−0.0092** (95% seed-cluster bootstrap interval **−0.0148 to −0.0030**); relative to
the square-root variance rule it is **−0.0044** (**−0.0131 to +0.0033**). The intervals are
descriptive development comparisons and are not adjusted for selecting among six radii and other
methods.

As expected from the criterion, larger radius fractions shifted the selected geometric-path
parameter toward uniform: mean `rho` was 0.000, 0.177, 0.373, 0.548, 0.675, and 0.780 for fractions
0, 0.1, 0.25, 0.5, 1, and 2. This did not create a monotone RMSE improvement. The 0.25 radius had
the lowest benign-nuisance RMSE; 0.50 had the lowest stationary and boundary-harm RMSE. All six
allocations had zero harm detections, so estimator accuracy did not translate into more useful
harm evidence under this monitor and budget.

This screen does **not** justify promoting 0.50 as a general default. Keep it as a development
candidate, with 0.25 as a near-tied alternative. The result supports testing the uncertainty radius
as a sensitivity parameter; it does not support a new sequential method or a false-alarm guarantee.

## Artifacts

The seed-level Parquet file, scenario summaries, paired contrasts, text report, and code/environment
manifest are in [`outputs/robust_active_inference_radius_development/`](../outputs/robust_active_inference_radius_development/).
No figure was generated; PaperBanana is unavailable in the current session.
