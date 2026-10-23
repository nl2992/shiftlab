# Common-budget acquisition frontier protocol

**Protocol locked:** 2026-10-23, before the full frontier run. This is a screening comparison of established and project-derived query policies, not a selection of a novel method.

## Question

How do the registered acquisition policies trade off decision-harm detection, estimation error, label use, and monitored horizon as the same hard dollar budget changes? The preceding comparisons evaluated only the 20% target rate. This grid tests 10%, 20%, and 30% while holding the e-process bound, sample size, DGP seeds, estimand, harm margin, alpha, and method set fixed.

## Frozen design

- 60 independent streams per scenario, seeds `28802026` through `28802085`.
- `n=3200`, `d=16`, evaluation device requested as CUDA.
- Target label-dollar budget rates: 10%, 20%, 30%.
- Scenarios: stationary and benign-nuisance population-null controls; boundary-local harm and recurring regimes as alternatives.
- Seven policies: uniform, variance, decision-value, cost-variance, cost-stabilized, exact mixture-growth, and robust mixture-growth (radius 0.20 selected only on the prior development grid).
- Common `q_min=0.05`, `q_max=0.80`, alpha 0.05, harm margin 0.10, common e-process support bound, and a pathwise cap based on maximum tariff 2.5.
- Identical streams and query random uniforms are reused within each budget. The same seed streams are also reused across budgets to pair the frontier contrasts. The target budget is the intervention changed across budget cells.
- No method or budget is selected on this evaluation block. All methods are reported.

## Outcomes and analysis

Report false escalations on each null scenario, detections over all materially harmful streams, detections among harmful streams reached before budget stopping, onset reachability, actual spend, labels, processed horizon, pathwise cap violations, and stream-mean estimation RMSE. Show Wilson intervals for binomial rates, paired stream-bootstrap intervals for RMSE differences versus uniform, and exact McNemar tests for paired detection versus uniform. Method-grid p-values are descriptive and are not multiplicity-adjusted. Small or zero event counts are not evidence of calibration.

## Reproduction

```powershell
uv run python scripts/grid_search_budget_frontier.py `
  --output outputs/budget_frontier_60 `
  --seeds 60 `
  --seed-offset 28802026 `
  --n 3200 `
  --d 16 `
  --budgets 0.10 0.20 0.30 `
  --scenarios stationary benign_nuisance boundary_local_harm recurring_regimes `
  --device cuda
```

The full grid is a discovery benchmark. Any apparent winner needs a separately seeded confirmation, a nondegenerate null calibration study large enough to assess the target error rate, and a matched realized-spend comparison before being promoted.
