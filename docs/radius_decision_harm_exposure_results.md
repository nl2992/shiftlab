# Radius-grid decision-harm exposure development replay

This is a replay of the frozen 30-seed development design in
[`robust_active_inference_radius_grid_protocol.md`](robust_active_inference_radius_grid_protocol.md)
with the evaluator-only fallback exposure endpoint specified in
[`radius_decision_harm_exposure_protocol.md`](radius_decision_harm_exposure_protocol.md). It reuses
the original seed block and is **not independent confirmation**.

## Design and verification

The CUDA run evaluated 30 matched seeds in each of stationary, benign-nuisance, and boundary-local
harm scenarios, with nine query policies per stream: uniform, variance, cost-variance, and six
robust active-inference radius fractions. It produced 810 rows. The runtime manifest records
`NVIDIA GeForce RTX 4060 Laptop GPU`, PyTorch 2.9.1+cu130 and CUDA 13.0. All 810 rows respected the
hard dollar cap; all 27 scenario-policy cells contained 30 unique seed rows. The Parquet checksum
and the executed `hard_budget.py` source checksum match the manifest.

The rerun exactly reproduces the earlier radius grid on labels queried, processed events, alarm
fields, stream-mean estimation errors, spend, and evaluator harm onset. The newly recorded evaluator
exposure is post hoc measurement only; it never enters the query policy, monitor, or learner-visible
state. No figure was generated. All research visuals must use PaperBanana.

## Findings

| Query policy | Macro stream-mean RMSE | Exposure difference vs uniform under budget-stop fallback (95% paired seed bootstrap CI) | Harm detections / 30 | Null false alarms / 60 | Mean labels on harm | Mean spend on harm | Mean events processed on harm |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uniform | 0.07771 | 0.00 [0.00, 0.00] | 0/30 | 0/60 | 232.6 | 348.88 | 2345.3 |
| Variance | 0.07296 | -0.73 [-7.84, 6.33] | 0/30 | 0/60 | 234.6 | 351.21 | 2337.1 |
| Cost-variance | 0.07367 | -0.59 [-7.74, 7.76] | 0/30 | 0/60 | 245.7 | 351.48 | 2337.4 |
| Robust radius 0 | 0.07367 | -0.59 [-7.74, 7.76] | 0/30 | 0/60 | 245.7 | 351.48 | 2337.4 |
| Robust radius 0.1 | 0.07051 | -3.84 [-10.26, 2.76] | 0/30 | 0/60 | 243.7 | 351.29 | 2329.5 |
| Robust radius 0.25 | 0.06870 | **-6.89 [-11.54, -2.87]** | 0/30 | 0/60 | 241.4 | 350.85 | 2323.9 |
| Robust radius 0.5 | **0.06856** | -4.86 [-9.95, -0.67] | 0/30 | 0/60 | 239.0 | 350.13 | 2329.9 |
| Robust radius 1 | 0.07146 | -2.83 [-5.70, 0.12] | 0/30 | 0/60 | 237.0 | 349.63 | 2335.9 |
| Robust radius 2 | 0.07365 | -1.29 [-4.23, 1.82] | 0/30 | 0/60 | 235.7 | 349.82 | 2338.9 |

Macro RMSE is the square root of the equal-scenario mean squared stream-mean estimation error. Its
paired seed-cluster bootstrap difference from uniform was -0.00902 [-0.01656, -0.00133] for radius
0.25 and -0.00915 [-0.01482, -0.00298] for radius 0.5. These percentile intervals are
development-only, unadjusted for searching six radii and several comparator methods. Radius 0.25
had the lowest boundary-harm exposure, while radius 0.5 had the lowest macro RMSE; the two remain
near-tied on the earlier RMSE score.

The mean full-horizon expected excess cost after harm onset was 621.53 cost units. Under the frozen
fallback counterfactual, mean excess cost through fallback was 598.75 for uniform, 591.86 for
radius 0.25, and 593.88 for radius 0.5. The corresponding avoided-exposure values were 22.79,
29.67, and 27.65. The apparent exposure advantage is coupled to fallback timing: **every policy had
0/30 alarm-triggered fallbacks, and all 30 fallbacks per policy occurred at budget stop**. Radius
0.25 processed 21.5 fewer events per harmful stream than uniform before that stop. Thus this result
does not show better harm detection or a transition from evidence to intervention; it measures the
predeclared consequence of stopping the monitor and switching to the reference policy when its
label budget is exhausted. A fixed per-stream fallback cost would cancel in these paired method
contrasts, but absolute net utility and the operational suitability of budget-stop fallback are
unmeasured.

Each policy reached all 30 harm onsets, yet none detected harm. Null controls had no monitor alarms,
but 0/60 is only a small development diagnostic and provides no calibration evidence. The run used a
10% target label budget and common support bound; these settings gave no useful harm-detection power
in this screen. The modest RMSE and fallback-exposure differences do not justify promoting a radius
or claiming a general utility improvement.

As a separate **post hoc policy sensitivity**, suppose the system falls back only after an evidence
alarm and continues its deployed policy when the query budget ends without an alarm. There were no
alarms in any harmful stream, so this policy fallback never occurred: mean excess cost stayed at the
full-horizon 621.53 for every method and each paired radius-versus-uniform exposure difference was
exactly zero. This distinguishes the observed budget-stop exposure reduction from an evidence-led
intervention benefit. The sensitivity uses the same evaluator streams and is not an independent or
pre-registered confirmation.

## Reproduction and artifacts

The original development replay command is in the radius-grid protocol. Recompute the summary and
paired, unadjusted bootstrap intervals with:

```powershell
uv run python scripts/analyze_radius_decision_harm_exposure.py
```

Seed-level metrics, full run manifest, derived summary CSVs, paired contrast CSVs, and analysis
manifest are in
[`outputs/robust_active_inference_radius_exposure_development/`](../outputs/robust_active_inference_radius_exposure_development/).

## Decision

**Do not advance a radius as a confirmed decision-aware intervention policy.** Radius 0.25 is the
development nominee for the narrower fixed-budget fallback-exposure estimand, with radius 0.5 as a
near-tied RMSE candidate. The next experiment must use disjoint seeds, a more informative monitoring
budget/support design, independent null calibration, and explicit accounting for fallback behavior.
Any inferential statement must separate monitoring-triggered fallback from budget-stop fallback.
