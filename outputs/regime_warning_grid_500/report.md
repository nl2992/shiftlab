# Regime-warning versus abstention development grid

Status: **development_only_no_independent_selection_or_confirmation**.

Rows: 66,000; paired contrasts: 756; seeds per scenario: 500; device: cuda.

The warning cue is an ordinary prediction-time feature. It follows N(0,1) in all null and persistent-benefit profiles and shifts to N(delta,1) only during harmful-adaptation deployment. The threshold is frozen from a standard-normal false-warning target. Static coverage is an independent randomized mixture with the incumbent. The evaluator's future gain is used only to score utility.

## Harmful adaptation: warning-rule operating points

| Signal shift delta | Target per-event warning rate | Expected net utility | Mean realized utility | Candidate coverage | Mean warnings / 400 events |
|---:|---:|---:|---:|---:|---:|
| 0.00 | 1% | -138.85 | -139.40 | 0.990 | 3.9 |
| 0.00 | 5% | -133.25 | -133.80 | 0.950 | 19.9 |
| 0.00 | 10% | -126.25 | -127.07 | 0.901 | 39.6 |
| 0.50 | 1% | -135.50 | -136.07 | 0.966 | 13.5 |
| 0.50 | 5% | -122.59 | -123.42 | 0.875 | 50.0 |
| 0.50 | 10% | -109.84 | -110.32 | 0.784 | 86.3 |
| 1.00 | 1% | -127.32 | -128.29 | 0.909 | 36.4 |
| 1.00 | 5% | -103.92 | -104.26 | 0.742 | 103.3 |
| 1.00 | 10% | -85.77 | -86.16 | 0.611 | 155.6 |
| 2.00 | 1% | -88.16 | -88.40 | 0.628 | 148.8 |
| 2.00 | 5% | -50.82 | -51.15 | 0.362 | 255.2 |
| 2.00 | 10% | -33.32 | -33.29 | 0.236 | 305.4 |

The regime-warning feature does not beat continuing with the incumbent in the harmful-reversal scenario at any tested signal strength. Its best utility can still improve on promotion/rollback or a similarly low static coverage in some cells.

## No-warning controls

Observed warning rates are marginal event rates; they are not run-level false-alarm probabilities.

| Scenario | Target per-event rate | Observed per-event rate |
|---|---:|---:|
| benign_nuisance | 1% | 1.02% |
| benign_nuisance | 5% | 5.01% |
| benign_nuisance | 10% | 10.01% |
| persistent_benefit | 1% | 1.03% |
| persistent_benefit | 5% | 4.99% |
| persistent_benefit | 10% | 9.95% |
| stationary | 1% | 1.03% |
| stationary | 5% | 5.02% |
| stationary | 10% | 10.00% |

## Paired utility contrasts at delta=2

Intervals are seed-cluster bootstrap 95% intervals, unadjusted across this development grid.

| Warning target | Reference policy | Mean paired utility difference | 95% interval |
|---:|---|---:|---:|
| 5% | continue | -51.15 | [-52.16, -50.13] |
| 5% | promotion_rollback | 18.93 | [16.32, 21.67] |
| 5% | static_coverage_0.25 | -15.26 | [-16.45, -14.03] |
| 10% | continue | -33.29 | [-34.12, -32.44] |
| 10% | promotion_rollback | 36.79 | [34.09, 39.30] |
| 10% | static_coverage_0.25 | 2.60 | [1.52, 3.65] |

This is an exploratory grid with a deliberately informative feature shift. It is a sensitivity study of feature-gated abstention, not evidence that the shift can be forecast in real deployment. The warning and fixed-coverage policies use no labels and incur different information costs from the queried promotion/rollback gate; utility and resource use must be interpreted together. Do not select a policy from these intervals. Any selected rule requires a fresh calibration and disjoint confirmation block.

No figure was generated because PaperBanana is unavailable in this session; no substitute visual generator was used.

## Reproduction

```powershell
uv run shiftlab-dive-regime-warning-grid --seeds 500 --horizon 400 --device cuda --output-dir outputs/regime_warning_grid_500
```
