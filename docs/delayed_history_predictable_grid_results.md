# Delayed history-predictable development grid: results

**Status:** exploratory development result; 30 paired streams per scenario/configuration/arm. No confirmation or novelty claim.

## Integrity and implementation checks

The frozen grid completed all 144 scenario × delay × propensity-floor × bound cells, yielding 4,320 stream-arm rows. Every arm shared generated context, outcome, and query random numbers within scenario; all query caps and support checks passed. CUDA generated the synthetic streams, and the event/arrival recursion ran with the NumPy CPU implementation. On the preceding 30-stream full-horizon comparison, the optimized monitor replay matched the Torch reference exactly for labels, event counts, alarm indices, alarm wall times, and detection indicators. Mean query-propensity and bound differences were at most `1.6e-14` and `3.2e-13`, respectively.

## Selected development point

The most attractive tested detection-label point for the eventwise-bound arm was `q_min=0.05`, `D=12`, the configuration already evaluated in the independent calibration. Across the four harm doses (30 streams each), eventwise-bound detection was 0/30, 1/30, 3/30, and 9/30; the matched fixed-bound arm detected 0/30, 0/30, 0/30, and 4/30. Mean detection was 10.83% versus 3.33%, a paired difference of +7.50 percentage points. A descriptive seed-cluster bootstrap interval was [+2.50, +13.33] points. This screen is small and selected across a parameter grid, so it is a development signal only.

The eventwise arm used a mean 194.63 labels per stream versus 338.84 for the fixed-bound arm, a paired difference of −144.21 labels (95% descriptive bootstrap interval [−163.33, −125.33]). Evaluator-known cumulative expected harm exposure was lower by 31.73 cost units on average (95% descriptive interval [−53.26, −13.65]). The eventwise arm reached the harm onset in 116/120 streams (96.7%), versus 120/120 for the fixed arm. Non-reached onsets remain nondetections in the reported denominator.

Across the full grid, pooled harm detection ranged from 8.3% to 10.8% for the eventwise arm. Its mean label use ranged from 188 to 404 labels per stream over the q-floor/delay cells. Matched fixed-bound detection ranged from 3.3% to 10.8%, with 329 to 441 labels. The small differences across delay values do not establish a latency effect. The 30-stream null cells had occasional alarms (up to 1/30 in individual eventwise cells); they are too small for calibration and are not compared as error-rate estimates.

## Decision

Do not use the grid's most favorable cell as a result. The selected `q_min=0.05, D=12` candidate already passed an independent 2,000-stream-per-cell null calibration, but a fresh calibration block is required after the grid selection. If the fresh calibration passes the frozen simultaneous 5% upper-limit gate, run a disjoint four-dose harm confirmation with no further tuning. If the power-retention rule fails, stop this delayed eventwise-bound candidate for this DGP and report the negative result. No serial-dependence, outcome-dependent-delay, intervention, or broader method claim follows.

Research figures were not generated because PaperBanana is unavailable in the active environment.

## Artifacts

- Frozen design: [`delayed_history_predictable_grid_protocol.md`](delayed_history_predictable_grid_protocol.md)
- Full 144-cell summary: [`../outputs/delayed_history_predictable_grid_30/metrics/grid_summary.csv`](../outputs/delayed_history_predictable_grid_30/metrics/grid_summary.csv)
- Paired per-dose differences: [`../outputs/delayed_history_predictable_grid_30/metrics/paired_harm_differences.csv`](../outputs/delayed_history_predictable_grid_30/metrics/paired_harm_differences.csv)
- Stream metrics: [`../outputs/delayed_history_predictable_grid_30/metrics/stream_metrics.parquet`](../outputs/delayed_history_predictable_grid_30/metrics/stream_metrics.parquet)
- Manifest and source/artifact hashes: [`../outputs/delayed_history_predictable_grid_30/reports/manifest.json`](../outputs/delayed_history_predictable_grid_30/reports/manifest.json)
