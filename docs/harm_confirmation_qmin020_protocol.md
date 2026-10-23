# Disjoint harmful-regime confirmation at q_min=.20

**Status:** frozen before execution. This confirms the development-screen signal; it does not claim a novel method.

## Question and primary comparison

On independent synthetic streams, estimate the detection probability and delay of the fixed-mixture decision-harm gate at `q_min=.20` in boundary-local harm and recurring-regime harm. The fixed-mixture gate is the primary procedure; predictable variance is the pre-specified secondary comparator; PM-EB is exploratory. All monitors receive the same uniform-query labels, prediction-powered increments, filtration, global bound, alpha=.05, epsilon=.10, and 20% hard label-dollar budget.

The primary endpoint is the fraction of evaluator-defined harmful streams detected by budget stopping, with all streams counted in the denominator. Report material-harm onset reachability; nondetections remain nondetections and are not dropped. Secondary endpoints are delay conditional on detection, queried labels, realized spend, events processed, cap violations, and paired monitor discordances. Use 95% Wilson intervals for marginal rates and exact paired McNemar tests for fixed-mixture versus predictable-variance and PM-EB within each scenario; apply Holm adjustment across the four paired tests. These secondary tests are descriptive because method selection was informed by earlier development evidence.

## Frozen design

- 200 independent streams per scenario, seed block `53000000–53000199`; disjoint from development and calibration blocks.
- `n=3200`, `d=16`, 20% hard label-dollar cap, uniform query policy, `q_min=.20`, `q_max=.80`, common e-process bound, alpha=.05, epsilon=.10.
- Scenarios: `boundary_local_harm` and `recurring_regimes`; method: `uniform_proxy`.
- CUDA requested for synthetic generation; record device/software manifest.
- No early stopping, seed replacement, monitor tuning, or threshold adjustment based on interim findings.

## Validity and limits

This evaluates detection in the registered synthetic scenarios only. The e-process interpretation still requires the history-conditional upper-mean null and correctly bounded prediction-powered increments. The sample-size block does not repair violations of that assumption. It does not test delayed/selected feedback, serial dependence outside the scenarios, policy selection, or candidate promotion. The null-calibration result is not reused for tuning; this block is reserved for the frozen alternative comparison.

## Reproduction

```powershell
uv run python scripts/diagnose_hard_budget_monitors.py `
  --output outputs/harm_confirmation_qmin020_200 `
  --seeds 200 `
  --seed-offset 53000000 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.20 `
  --scenarios boundary_local_harm recurring_regimes `
  --methods uniform_proxy `
  --device cuda
```
