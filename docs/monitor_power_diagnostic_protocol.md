# Monitor power diagnostic protocol

**Purpose:** development-only diagnostic following the paired acquisition frontier, frozen before running its seeds. It tests whether predictable variance adaptation or predictable plug-in empirical-Bernstein (PM-EB) improves power over the existing fixed mixture when all monitors receive exactly the same prediction-powered estimates.

## Frozen design

- 30 independent streams per scenario; seeds `39102026` through `39102055`, distinct from the completed frontier and prior predictable-stake calibration seeds.
- `n=3200`, `d=16`, 20% hard label-dollar cap, `q_min=0.05`, `q_max=0.80`, alpha 0.05, and the existing 0.10 materiality margin.
- Scenarios: stationary and benign-nuisance population-null controls; boundary-local harm and recurring regimes.
- Query policies: uniform, cost-stabilized, and exact mixture-growth. For each policy, fixed-mixture, predictable variance-adaptive, and PM-EB monitors process the same stream, queried labels, prediction-powered increments, global bound, and stopping path.
- Requested device: CUDA for random feature generation. All monitor comparisons use common random numbers and fresh seeds.

## Validity and outcomes

All three monitors retain the same global prediction-powered increment bound `M * (2/q_min - 1)` and test the history-conditional upper-mean null using predictable stakes. No bound is normalized by current covariates. The predictable variance and PM-EB algorithms are established comparators, not proposed novelties.

Report harm detection, onset reachability, delay conditional on detection, false escalation on each control, realized spend, labels, processed horizon, and paired exact McNemar contrasts against the fixed mixture. Use Wilson intervals for event rates. This 30-stream diagnostic is not a calibration study and cannot establish a 5% false-escalation rate. It will not select a final method; any promising monitor requires independent null calibration and a separately seeded confirmation.

## Reproduction

```powershell
uv run python scripts/diagnose_hard_budget_monitors.py `
  --output outputs/monitor_power_diagnostic_30 `
  --seeds 30 `
  --seed-offset 39102026 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --device cuda
```
