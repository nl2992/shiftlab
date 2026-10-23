# Paired harm severity/onset/horizon grid

**Status:** frozen before the official run. This is an exploratory development screen; it does not select a confirmatory winner or establish a novel method.

## Research question

Map where the fixed-mixture decision-harm gate and its predictable-variance and PM-EB comparators gain or lose detection power as material harm grows, begins earlier or later, and has more or less time to accumulate evidence. This follows the independent q_min=.20 null calibration and harm confirmation. The candidate monitor and global bound remain fixed during this grid.

## Frozen factors and comparisons

- 30 common-random-number streams per cell; seed block `54000000–54000029`, disjoint from the calibration, confirmation, and smoke blocks.
- Boundary-local harm: severity `{0.75, 1.50, 2.25}` × abrupt `change_fraction` `{0.35, 0.50, 0.65}` × horizon `n` `{2400, 3200, 4000}` (27 cells).
- Recurring regimes: severity `{0.75, 1.50, 2.25}` × horizon `n` `{2400, 3200, 4000}` (9 cells). The registered four-regime recurrence schedule is preserved; onset fraction is not varied because that pattern starts at the beginning and does not use the abrupt-change parameter.
- Fixed-mixture primary; predictable variance secondary; PM-EB exploratory. All share uniform querying, labels, prediction-powered increments, the common `q_min=.20` bound, alpha=.05, epsilon=.10, and the 20% horizon-scaled dollar budget within a cell.
- CUDA requested for generation. Paired seed IDs and query uniforms are reused across parameter cells; the data generating parameters and horizon still differ by cell.

## Outcomes and interpretation

Primary grid endpoint: detected material-harm streams divided by all evaluator-classified material-harm streams. Report Wilson intervals, whether the onset was reached before budget stopping, and conditional delay among detections. An onset not reached remains a nondetection in the all-harm denominator. Also report realized spend, labels, processed events, and cap compliance. Report fixed-versus-comparator paired discordances; their cellwise exact tests are exploratory, unadjusted, and must not be used to pick a winning parameter cell as if confirmatory.

The hard-dollar budget is 20% of the expected tariff per monitoring event times the available monitoring horizon. Thus longer `n` provides more monitoring events and proportionally more total dollar budget; the horizon comparison is an operational horizon-plus-resource screen, not a fixed-total-spend causal estimate. The recurring onset is immediate by construction. Severity is a DGP parameter, not itself the realized cost-harm amount; the evaluator still determines material-harm onset from expected paired cost.

Use this screen to locate stable power regions and weak points, then narrow the next disjoint confirmation grid. Do not retune alpha, q_min, margin, or stake families on the final confirmation block. The e-process guarantee remains conditional on the history-conditional mean null and bounded corrected increments. The grid does not address delayed or selectively observed labels, external shift families, or adaptation certification.

## Reproduction

```powershell
uv run python scripts/run_harm_power_grid.py `
  --output outputs/harm_power_grid_30 `
  --seeds 30 `
  --seed-offset 54000000 `
  --device cuda
```
