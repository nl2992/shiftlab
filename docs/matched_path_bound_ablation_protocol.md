# Matched-path support-bound ablation

**Status:** frozen before running, 2026-10-24. Development screen only. Seed root `28404027`; do not tune schedules or interpretation after opening results.

## Objective

The prior delayed Markov confirmation compared complete monitor-query systems. Its query propensity adapted to each monitor's own evidence, so the result could not isolate whether the gain came from using the eventwise support bound or from the resulting change in the adaptive query path. This ablation fixes the query-propensity path independently of monitor wealth and compares fixed versus eventwise bounds on identical queried labels and event prefixes.

## Data and query schedules

- Use the registered two-state Markov-volatility generator, fixed action pair, independent source-trained proxy, 2,400-event horizon, 12-event deterministic outcome-independent delay, 20% hard cap (480 labels), and four harm effects `{0.04,0.20,0.40,0.60}` with two nonpositive-mean controls.
- Generate 60 paired streams per scenario on CUDA. Reuse the same states, contexts, training sample, outcome uniforms, and query uniforms across all schedules and bound modes.
- Compare four precommitted query schedules with a common target mean request rate of 0.20: constant `q=0.20`; and periodic schedules with `q_low=0.05`, `q_high` in `{0.35,0.55,0.80}`, period 10, and respectively 5, 3, or 2 high-propensity positions. Rotate schedule phase evenly over the ten stream IDs. The schedule depends only on event index and a preassigned stream phase, never current/past features, labels, monitor evidence, outcome, or delays.
- For every schedule compare (a) the fixed support bound `B=M(2/q_min-1)` using that schedule's minimum propensity and (b) the eventwise predictable bound `B_t=M(2/q_t-1)`. Query draws and event enrollment are identical between the two bound modes. Continue evidence updates after a crossing; stop enrolling only when the shared realized label budget is exhausted. This isolates bound choice while preserving a predictable query process and the pathwise cap.
- The constant `q=0.20` arm is an implementation identity check: its fixed and eventwise bounds are equal and all stream-level monitor outcomes must match exactly.

## Outcomes and gates

Record query counts, event prefix length, alarms, pre-onset alarms, post-onset detections and event/wall delay, bound violations, and evaluator-only expected exposure. Compare bound modes within each schedule using paired stream IDs. Summarize alternative results equally across harm doses with seed-cluster bootstrap intervals. Report null alarms as descriptive counts only; 60 streams per null cell do not calibrate a 5% error target. Any selected schedule/bound combination requires fresh independent null calibration and a disjoint confirmation before a performance claim.

This is a mechanism and propensity-heterogeneity screen, not a new algorithm or theorem. The eventwise betting guarantee still requires the event-time conditional-mean null given the full history, predictable propensities, independent randomized query coins, complete correct labels, and a frozen policy pair. Event-order prefix stopping is the only use of delayed feedback; delay is never evidence.

No figure is required. Any visual for this experiment must use PaperBanana; if unavailable, report the limitation and keep the result in numeric tables and Parquet.

## Reproduction

```powershell
uv run python scripts/run_matched_path_bound_ablation.py --streams 60 --seed 28404027 --device cuda --output outputs/matched_path_bound_ablation_60
uv run pytest tests/test_matched_path_bound_ablation.py tests/test_delayed_feedback.py -q
```
