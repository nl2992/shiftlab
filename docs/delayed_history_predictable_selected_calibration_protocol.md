# Fresh calibration of the selected delayed eventwise-bound configuration

**Status:** frozen after the development grid, before running the new seed block; 2026-10-24.

The development grid selected one candidate for a separate test: evidence-directed query propensities with `q_min=0.05`, `q_max=0.80`, 12-event deterministic outcome-independent delay, event-order prefix updates, eventwise bound `B_t=M(2/q_t−1)`, 20% request cap, horizon 2,400, and the registered fixed action pair. The fixed-bound arm uses the same propensity rule and `B=M(2/q_min−1)`.

This is a fresh replication of the two-null calibration on a post-grid seed block. It uses 2,000 independent streams per scenario and arm, root seed `27504027`, with the exact-zero mixed-sign and strict-negative controls. Scenario blocks are disjoint; arms share random numbers within a scenario. The four-cell family uses one-sided Clopper–Pearson upper limits with per-cell alpha `0.0125`, for at least 95% simultaneous coverage. Each arm passes only if both simultaneous upper limits are no greater than 5% and every budget, support, and ordering invariant passes.

No query propensity, delay, threshold, bound, or label budget may be adjusted after these results. A pass allows one disjoint harm confirmation under the fixed configuration. Confirmation uses fresh streams and the frozen rule: equal-weight mean post-onset detection difference (eventwise minus fixed) across four registered doses; retain only if its two-sided 95% paired stream-cluster bootstrap lower limit exceeds +2 percentage points, the paired label-count difference upper limit is at most zero, and all independent null-calibration upper limits are at most 5%. Otherwise report the failure and stop this candidate. The calibration does not prove the filtration assumptions or cover serial dependence, informative delays, policy changes, or missing labels.

No visual is required; any research figure must use PaperBanana.

## Reproduction

```powershell
uv run python scripts/calibrate_delayed_history_predictable_bounds.py --streams 2000 --seed 27504027 --delay 12 --device cuda --output outputs/delayed_history_predictable_selected_calibration_2000
```
