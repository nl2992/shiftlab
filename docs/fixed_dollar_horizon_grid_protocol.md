# Fixed-dollar monitor horizon development grid

**Status:** frozen before the 30-seed development run. This grid estimates where the current
monitors gain power as observation time changes while the label-dollar cap stays fixed. It is not
a confirmatory comparison and will not be used to claim a universally best method.

## Question

At a common realized label-dollar cap, how do four mathematically specified monitoring procedures
trade off decision-harm detection, false escalation, censoring, and event efficiency when the same
generated stream is observed for different horizons? Prior horizon grids scaled the total dollar
budget with the number of events, confounding time with resources. This design keeps the full data
stream, source-model fit, validation data, random uniforms, and cap fixed across horizons.

## Frozen design

- Generated stream: `n=4000`, `d=16`; all horizons use the same full stream and same pre-monitor
  training/validation split (`monitor_start=1000`).
- Available monitor horizons: 1,000, 1,800, and 2,600 events. These correspond to end points 2,000,
  2,800, and 3,600 on the common generated stream.
- Development seed block: 30 common seeds, `56,100,000–56,100,029`. The one-seed CUDA smoke used
  offset `56,000,000` and is excluded from this block. This range is disjoint from previously
  registered calibration, confirmation, and development ranges in this repository.
- Scenarios: stationary and benign-nuisance controls; boundary-local harm at fractions 0.35 and
  0.65 (early and late onset on the common stream); recurring regimes; harmful adaptation.
- Every policy receives a fixed pathwise cap of **$720**. This is specified as 20% of a reference
  $1.50 tariff over 2,400 monitoring events; it does not change with horizon or scenario.
- Query target rate 0.20, propensity support `[0.20, 0.80]`, alpha 0.05, decision-harm margin 0.10,
  and common eventwise increment bound.
- Four monitors: eventwise fixed mixture, predictable-variance e-process, PM-EB, and fixed 10%
  CM-EB / positive-betting mixture over block PPI estimates. The first three share the eventwise
  uniform-query labels. Block PPI uses 20-event blocks and four labels per block; its realized
  queried indices differ, while its label fraction and dollar cap match the eventwise design.
- CUDA requested for synthetic generation and model fitting. Each cell manifest records the
  resolved device and software/code hashes. CPU remains available for smoke testing.

## Outcomes and analysis

Report false escalations on the two registered population-null controls with Wilson intervals.
For all evaluator-defined harmful streams report detection probability with all-stream denominators,
harm-onset reachability, detection conditional on reaching the onset, delay conditional on detection,
events processed, labels, realized spend, budget utilization, expected paired decision cost, and
stream-mean estimation RMSE. Keep a nondetection with an unreached onset in the all-harm denominator
and show the reachability separately. Cellwise intervals are descriptive and not multiplicity
adjusted. Do not select a winner or retune monitor/query parameters from this grid.

Eventwise monitor guarantees require the declared history-conditional mean null, predictable
querying, immediate feedback, and the configured bounded increments. Block-PPI inference concerns
its running-average estimand under the documented disjoint block-sampling design; it is not an
equivalent test of the stronger eventwise null. Neither procedure certifies an adapted replacement.
The synthetic data-generating process does not cover arbitrary dependence, delayed labels, or
real-world distribution shifts.

## Reproduction

```powershell
uv run python scripts/run_fixed_dollar_horizon_grid.py `
  --seeds 30 --seed-offset 56100000 --budget-dollars 720 --device cuda `
  --output outputs/fixed_dollar_horizon_grid_development

uv run python scripts/analyze_fixed_dollar_horizon_grid.py `
  --input outputs/fixed_dollar_horizon_grid_development
```

The 30-seed block is for mapping effects and variance. Any primary-method claim requires a separate
predeclared confirmation seed family, sample size based on paired power analysis, and calibration
for the complete policy-plus-monitor procedure.
