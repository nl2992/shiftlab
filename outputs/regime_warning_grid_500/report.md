# Regime-warning reliability and cost development grid

Status: **development_only_no_independent_selection_or_confirmation**.

Rows: 264,000; paired contrasts: 2,187; seeds per scenario: 500; device: cuda.

The warning cue is a prediction-time feature. Its measured distribution is N(0,1) in the controls and N(delta,1) in harmful-adaptation deployment. Missing reads are MCAR and trigger incumbent fallback. The run varies signal strength [0.0, 0.5, 1.0, 2.0], conditional per-read false-warning target [0.01, 0.05, 0.1], missingness [0.0, 0.1, 0.3], and acquisition cost per attempted event [0.0, 0.0005, 0.002]. Static coverage is an independent randomized incumbent mixture. Evaluator truth is used only to score utility.

## Harmful adaptation: warning-rule operating points

The table fixes the conditional false-warning target at 5% and sensor cost at 0.0005 per attempted event; missing reads trigger fallback.

| Signal shift delta | Missing reads | Expected net utility | Mean realized utility | Candidate coverage | Mean warnings / 400 events |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 0% | -133.25 | -133.80 | 0.950 | 19.9 |
| 0.00 | 10% | -119.95 | -120.35 | 0.855 | 17.9 |
| 0.00 | 30% | -93.35 | -94.32 | 0.667 | 13.8 |
| 0.50 | 0% | -122.59 | -123.42 | 0.875 | 50.0 |
| 0.50 | 10% | -110.36 | -111.10 | 0.787 | 44.9 |
| 0.50 | 30% | -85.89 | -87.13 | 0.614 | 34.7 |
| 1.00 | 0% | -103.92 | -104.26 | 0.742 | 103.3 |
| 1.00 | 10% | -93.55 | -93.91 | 0.667 | 92.8 |
| 1.00 | 30% | -72.82 | -73.56 | 0.521 | 72.1 |
| 2.00 | 0% | -50.82 | -51.15 | 0.362 | 255.2 |
| 2.00 | 10% | -45.77 | -46.08 | 0.326 | 229.4 |
| 2.00 | 30% | -35.65 | -36.13 | 0.254 | 178.8 |

The regime-warning feature does not beat continuing with the incumbent in the harmful-reversal scenario at any tested signal strength. Its best utility can still improve on promotion/rollback or a similarly low static coverage in some cells.

The `matched_coverage_oracle` row is evaluator-only and cannot be selected by the learner. For every grid cell, expected warning-rule utility minus expected oracle-matched-coverage utility equals exactly `-H * warning_event_cost`; the runner checks this identity. Since the warning and missingness are independent of event-level gain in this DGP, the warning feature adds no expected utility beyond reducing candidate coverage, and positive sensing cost lowers utility further.

## No-warning controls

Observed conditional warning rates divide warning events by available reads. They are marginal per-event rates, not run-level false-alarm probabilities.

| Scenario | Missing reads | Target conditional rate | Observed conditional rate |
|---|---:|---:|---:|
| benign_nuisance | 0% | 1% | 1.02% |
| benign_nuisance | 0% | 5% | 5.01% |
| benign_nuisance | 0% | 10% | 10.01% |
| benign_nuisance | 10% | 1% | 1.01% |
| benign_nuisance | 10% | 5% | 5.00% |
| benign_nuisance | 10% | 10% | 10.00% |
| benign_nuisance | 30% | 1% | 0.98% |
| benign_nuisance | 30% | 5% | 5.00% |
| benign_nuisance | 30% | 10% | 10.01% |
| persistent_benefit | 0% | 1% | 1.03% |
| persistent_benefit | 0% | 5% | 4.99% |
| persistent_benefit | 0% | 10% | 9.95% |
| persistent_benefit | 10% | 1% | 1.03% |
| persistent_benefit | 10% | 5% | 5.01% |
| persistent_benefit | 10% | 10% | 9.98% |
| persistent_benefit | 30% | 1% | 1.02% |
| persistent_benefit | 30% | 5% | 5.02% |
| persistent_benefit | 30% | 10% | 10.03% |
| stationary | 0% | 1% | 1.03% |
| stationary | 0% | 5% | 5.02% |
| stationary | 0% | 10% | 10.00% |
| stationary | 10% | 1% | 1.03% |
| stationary | 10% | 5% | 5.03% |
| stationary | 10% | 10% | 9.99% |
| stationary | 30% | 1% | 1.02% |
| stationary | 30% | 5% | 5.02% |
| stationary | 30% | 10% | 9.94% |

## Paired utility contrasts at delta=2, 5% warning target, 0.0005 sensor cost

Intervals are seed-cluster bootstrap 95% intervals, unadjusted across this development grid.

| Missing reads | Reference policy | Mean paired utility difference | 95% interval |
|---:|---|---:|---:|
| 0% | continue | -51.15 | [-52.17, -50.05] |
| 0% | matched_coverage_oracle | -0.59 | [-1.90, 0.69] |
| 0% | promotion_rollback | 18.93 | [16.25, 21.85] |
| 0% | static_coverage_0.25 | -15.26 | [-16.46, -14.03] |
| 10% | continue | -46.08 | [-47.11, -45.04] |
| 10% | matched_coverage_oracle | -0.52 | [-1.77, 0.73] |
| 10% | promotion_rollback | 23.99 | [21.33, 26.63] |
| 10% | static_coverage_0.25 | -10.19 | [-11.40, -8.95] |
| 30% | continue | -36.13 | [-37.04, -35.22] |
| 30% | matched_coverage_oracle | -0.83 | [-1.95, 0.36] |
| 30% | promotion_rollback | 33.94 | [31.42, 36.57] |
| 30% | static_coverage_0.25 | -0.24 | [-1.41, 0.95] |

This is an exploratory sensitivity grid with a deliberately informative feature shift and MCAR missingness. It does not show that warning reliability is known in real deployment. The warning and fixed-coverage policies use no labels and incur different information costs from the queried promotion/rollback gate; utility and resource use must be interpreted together. Contrasts are unadjusted across the development grid. Do not select a policy from these intervals. Any selected rule requires a fresh calibration and disjoint confirmation block.

No figure was generated because PaperBanana is unavailable in this session; no substitute visual generator was used.

## Reproduction

```powershell
uv run shiftlab-dive-regime-warning-grid --seeds 500 --horizon 400 --device cuda --output-dir outputs/regime_warning_grid_500
```
