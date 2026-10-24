# Matched-path support-bound ablation results

The frozen development grid evaluated 2,880 stream-arm rows (60 paired streams × six Markov scenarios × four propensity schedules × two support bounds). Data generation ran on the RTX 4060 Laptop GPU; the ordered delayed-label monitor used CPU NumPy replay. Every fixed/eventwise pair shared the same query probabilities, query uniforms, requested labels, and processed event prefix. All 2,880 rows respected the 480-label cap, and no event increment exceeded its registered bound.

## Isolated bound effect

At constant `q=0.20`, the fixed and eventwise bounds are both `9M`, and all stream-level outcomes matched exactly. Under periodic propensity schedules, the fixed arm used the conservative `39M` bound implied by `q_min=0.05`, while the eventwise arm used `M(2/q_t-1)` at each event. The primary descriptive endpoint is the paired eventwise-minus-fixed detection difference, averaged equally across the four harm doses and bootstrapped over the 60 common streams.

| Precommitted schedule | Fixed macro detection | Eventwise macro detection | Paired difference (95% bootstrap interval) | Mean labels per stream |
|---|---:|---:|---:|---:|
| Constant `q=0.20` | 6.67% | 6.67% | 0.00 pp [0.00, 0.00] | 472.05 |
| Periodic `q∈{0.05,0.35}` | 0.83% | 7.92% | +7.08 pp [+3.33,+11.25] | 473.75 |
| Periodic `q∈{0.05,0.55}` | 1.67% | 6.25% | +4.58 pp [+1.25,+8.75] | 474.68 |
| Periodic `q∈{0.05,0.80}` | 0.83% | 8.33% | +7.50 pp [+3.75,+11.67] | 475.80 |

Every schedule has a precommitted mean propensity of 0.20 over its ten-event cycle and stream phase. The arm-specific detection rates by dose and the complete paired intervals are in the output summary and `paired_bound_effects.csv`. These four schedule comparisons were selected on this development block; their intervals are descriptive and are not adjusted for selecting among schedules.

The two 60-stream null blocks had between zero and two alarms per cell (at most 3.33%). These counts do not calibrate the nominal 5% error target. The eventwise gain under variable q is consistent with the mathematical role of predictable, event-specific support bounds: high-query events need not inherit the worst-case range from low-query events. The constant-q identity check is a useful implementation control. This does not establish a universally better propensity schedule, calibration, external validity, or a new betting method.

The next step is fresh null calibration and disjoint confirmation for a preselected periodic schedule, with the constant-q arm retained as a negative control for bound differences. Freeze the schedule before those runs and do not tune it on their outcomes. No figure was generated; this development result is fully represented by its tables and stream-level Parquet, and PaperBanana remains the required tool for any future visual.

See the [frozen protocol](matched_path_bound_ablation_protocol.md), [full stream metrics](../outputs/matched_path_bound_ablation_60/metrics/stream_metrics.parquet), [cell summaries](../outputs/matched_path_bound_ablation_60/metrics/summary.csv), [paired effects](../outputs/matched_path_bound_ablation_60/metrics/paired_bound_effects.csv), and [manifest](../outputs/matched_path_bound_ablation_60/reports/manifest.json).
