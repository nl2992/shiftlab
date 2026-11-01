# Independent calibrated CUSUM comparison

2026-10-30. Previous goal turn: progress (committed real-action diagnostics). This continuation closes one missing empirical baseline slice; exhaustive source/baseline coverage remains incomplete. Goal remains active.

## Design and implementation

Classical one-sided CUSUM on queried paired gain minus the .01 benefit margin and a slack in {0,.01,.05,.1}. Recurrence is max(0, previous + observed gain − margin − slack), updated only when the queried label is released. This is an operational paired-cost adaptation of [the standard CUSUM recurrence](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/cusum.htm), not a new algorithm or a full published SOTA reproduction.

Uniform Bernoulli query rate.2; hard cap400 over2,000 observations; fixed delay5; query cost.001; switch cost1. Queries stop at first promotion and pending requests are charged. Both classical and betting controls share outcomes and query random numbers. The same remaining-horizon economic eligibility is used; it presumes persistence and is not a guarantee of future utility.

For each slack, calibrate on1,000 independent paths for each of three null cases. Threshold is the maximum of the three ceil(.95*(n+1)) order statistics of maximum CUSUM. Strict crossing handles ties. Calibration includes all visible horizon events, a conservative extension beyond the economic eligibility cutoff. Test uses fresh seeds:2,000 paths per null and500 per alternative, totaling8,500 test paths. Together with calibration,11,500 paths. Compare the previously selected Kelly finalist and tuned FTL comparator without retuning. All four CUSUM settings are reported; no winner is selected on the new test data.

Registration: cusum_comparison_registration.json. Thresholds: cusum_calibrated_thresholds.json. Completed run: cusum_comparison_status.json. Full results: cusum_comparison_results.json. Per-path arrays: outputs/exhaustive_evaluation/cusum_comparison. Threshold calibration is empirical and distribution-specific; it provides no arbitrary conditional-null anytime guarantee. An unconditional order-statistic calibration statement also does not give an exact conditional guarantee for the one realized calibration set.

## Findings

Primary cost averages the four persistent cases equally: useful_initial, useful, late and small. Reversal is separate. The last column is a simultaneous one-sided null-rate upper bound, using Bonferroni over6 methods ×3 nulls. Lower cost is better.

| Method | Mean persistent total cost | Reversal excess versus incumbent | Tie-null promotion rate | Tie-null simultaneous upper |
|---|---:|---:|---:|---:|
| CUSUM slack0 | 226.340 | +29.523 | .0510 | .0662 |
| CUSUM slack.01 | 218.543 | +20.123 | .0540 | .0695 |
| CUSUM slack.05 | 201.906 | −.693 | .0515 | .0667 |
| CUSUM slack.1 | 196.433 | −8.033 | .0565 | .0723 |
| Paired Kelly finalist | 203.832 | +5.205 | .0275 | .0393 |
| Tuned FTL | 206.041 | +9.285 | .0200 | .0303 |

All methods have zero observed harmful-source promotions. For harmful-after-shift, CUSUM slack.05/.1 promote at.0015/.0175; other settings and betting controls have zero. The corresponding simultaneous upper bounds are.0059/.0273 versus.00294 for zero counts.

The high-slack classical settings are competitive on cost and better on this reversal case. They also spend a larger empirical type-I allowance near the tie boundary. Their simultaneous upper bounds exceed the earlier .06 safety-screen tolerance. This is insufficient evidence to pass that screen; it is not proof that their true rate exceeds.05 or that the recurrence is invalid. Do not claim an equal-safety classical win or a betting win over all classical controls from this comparison. Simulation-specific threshold selection and theorem-backed conditional-null control are different contracts.

## Common bottleneck and next action

Evidence points to a safety/power/timeliness tradeoff rather than a uniquely beneficial betting heuristic. More aggressive local accumulation reacts sooner and helps reversal utility, while nominal empirical threshold calibration has uncertainty. No method here controls future loss after an unobserved abrupt reversal. Fixed one-promotion policies cannot actively roll back.

Next bounded comparison: prospectively calibrate the same four classical slacks to a lower tail probability (e.g..025) using fresh calibration seeds, then test with fresh seeds and the same cost/null contracts. Report the full frontier rather than choose the best slack retrospectively. This is a new registration, not a replacement of these results. Add Page-Hinkley only after specifying a genuinely distinct target/recurrence; a fixed-target cumulative-minimum version equals CUSUM and should not be counted as a separate method.

Full learned active-RCPS, applicable Hsu–Shekhar querying, prediction-guided betting, Markov scope and robust-controller synthesis comparisons still require source/contract mapping. The completed≥500-configuration rounds do not settle these obligations or establish novelty. No new broad sweep is justified by this baseline result alone.

## Verification

Three focused tests check no early feedback, charging pending queries, hard-budget exhaustion and independent scalar recurrence agreement. Ruff0.17.1 check/format passed before registration. Source hashes were frozen before calibration; registration and run artifacts are preserved. No real reserved windows were read, no new data downloaded, and no historical runs overwritten.
