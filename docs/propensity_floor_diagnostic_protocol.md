# Minimum-propensity floor diagnostic under a 20% hard budget

**Lock date:** 2026-10-24. This is a same-seed diagnostic to isolate support-scale and horizon
tradeoffs, not a confirmatory policy comparison.

## Question

With the target dollar rate and pathwise budget held at 20%, does increasing `q_min` from 0.10 to
0.20 improve decision-harm evidence by reducing the PPI increment support bound, and how much
monitor horizon or onset reachability does the higher query floor sacrifice?

## Frozen comparison

- Use the first 30 seeds `20373024`–`20373053` from the already completed 60-seed 20% diagnostic.
- Scenarios: stationary, benign nuisance, and boundary-local harm.
- Methods: uniform and the previously selected evidence curve `a=0.05, p=0.5`.
- Keep `n=3200`, `d=16`, `budget_rate=0.20`, `q_max=0.80`, `alpha=0.05`, harm margin `0.10`,
  tariff support `[0.5, 2.5]`, common random numbers, and a common e-process bound within each
  floor setting. Change only `q_min` to `0.20` from the existing `0.10` block.
- Generate with CUDA. Save event traces for learner/evaluator-separated PPI variance, log-e,
  support-bound, and onset-reachability diagnostics. Generate no figures; use PaperBanana for
  research visuals when available.

## Analysis rules

Compare paired seed-level streams against the matching 30-seed subset of the `q_min=0.10` run.
Report detection both over all harmful streams and among onsets reached before the hard-budget
stopping time. Also report realized dollar spend, labels, processed events, PPI increment variance,
support bound, and false escalations on both controls. Do not interpret this reused-seed diagnostic
as independent evidence, calibration, or a method-selection result. Any promising floor setting
requires a new frozen seed block and independent null calibration.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 20373024 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.20 --q-max 0.80 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0.05_p0.5 --skip-figure --record-event-traces --output outputs/propensity_floor_diagnostic_qmin020_30
uv run python scripts/analyze_monitor_signal.py outputs/propensity_floor_diagnostic_qmin020_30/metrics/event_traces.parquet --output outputs/propensity_floor_diagnostic_qmin020_30/analysis
```
