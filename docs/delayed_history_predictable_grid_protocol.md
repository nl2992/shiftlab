# Delayed history-predictable propensity and latency grid

**Status:** frozen development screen, 2026-10-24. This is exploratory hyperparameter selection, not calibration or confirmation.

## Purpose

The independently calibrated `q_min=0.05`, 12-event design had low observed harm detection despite lower label use. This screen maps whether a higher propensity floor or shorter feedback delay changes the detection-label trade-off. It does not infer that a candidate is statistically valid from its grid-cell false-alarm count.

## Frozen grid

- 30 paired synthetic streams per scenario; horizon 2,400; onset index 1,200.
- Scenarios: exact-zero and strict-negative controls plus the four registered localized-harm doses.
- Propensity floors: `q_min ∈ {0.05, 0.10, 0.15}`; `q_max=0.80`.
- Deterministic, outcome-independent delays: `D ∈ {1, 3, 12, 24}` events.
- Arms: fixed bound `M(2/q_min−1)` and eventwise predictable bound `M(2/q_t−1)`.
- 20% hard request cap, query requests reserve budget immediately, and pending evidence is committed only in event order.
- Each scenario generates one shared CUDA random-number block. Both arms, all q floors and all delays reuse the same context, outcome, and query uniforms. The per-scenario seed blocks are disjoint from the earlier development screen and calibration.
- Sequential monitor replay uses the tested CPU NumPy implementation after one transfer from CUDA. The benchmark records GPU stream generation and CPU replay separately.

## Reporting and selection discipline

Report all 144 method-configuration-scenario cells, including per-cell false alarms, detection, onset reach, labels, processed events, event-time delay and wall-time delay. Summarize the harm detection-label Pareto frontier and paired per-stream differences for the four harm doses. The 30-stream null cells are diagnostic only. No cell is called calibrated based on this screen; any selected configuration needs its own fresh independent null calibration before a disjoint harm confirmation.

No adaptive query or bound parameters may be tuned after examining this grid. A candidate is chosen only as a development hypothesis based on the full detection-label-delay profile, not on a single maximum detection cell. Preserve fixed-bound and fixed-propensity references. Do not make a novelty claim: both the predictable bounded-factor construction and adaptive sampling are standard tools.

Research figures must use PaperBanana. If unavailable, retain tables and metrics without creating a substitute figure.

## Reproduction

```powershell
uv run python scripts/grid_delayed_history_predictable_bounds.py --streams 30 --seed 27404027 --device cuda --output outputs/delayed_history_predictable_grid_30
uv run pytest tests/test_delayed_history_predictable_bounds.py tests/test_delayed_feedback.py -q
```
