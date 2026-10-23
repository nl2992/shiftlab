# Null calibration protocol for q_min=.20

**Status:** frozen before execution. This is a synthetic-model calibration study, not a real-world guarantee.

## Question and procedures

Estimate the false-escalation probability of the fixed-mixture decision-harm gate at alpha=.05 under the registered stationary and benign-nuisance population-null controls. The predictable-variance gate is a secondary comparator. Both use the q_min=.20 globally bounded prediction-powered increments. PM-EB is excluded from the primary calibration because its paired development screen showed near-zero power; it remains in the repository as a comparator.

The population controls are defined in `src/shiftlab/decision_harm_experiment.py` and the e-process tests the history-conditional upper-mean null for paired deployed-minus-reference cost, with materiality margin epsilon=.10. Validity relies on the experiment's predictable policy, immediate feedback, correct bounded increments, and the specified conditional null. This run does not cover delayed or selectively sampled outcomes, temporal dependence beyond the generated scenario, policy/candidate selection after looking at outcomes, or a misspecified reference policy.

## Frozen design

- 2,000 independently generated streams per null scenario; seed block `52000000–52001999`.
- `n=3200`, `d=16`, alpha=.05, materiality margin=.10, label-dollar cap=.20, uniform query policy, q_min=.20, q_max=.80.
- Scenarios: `stationary` and `benign_nuisance`; both are designated population-null controls.
- Fixed-mixture primary; predictable-variance secondary. Both process the same queried labels and paired-loss increments.
- CUDA requested for synthetic generation; record actual resolved device and software versions in the manifest.
- No early stopping, parameter tuning, or seed replacement based on interim results.

## Endpoints and interpretation

Primary endpoint: stream-level false escalation by the horizon for the fixed-mixture gate, separately by scenario. Secondary endpoint: the same rate for predictable variance. Report counts, observed rates, two-sided 95% Wilson intervals, and one-sided exact Clopper–Pearson upper confidence limits. Also report processed events, queried labels, realized spend, and any cap violations. Use the independent stream as the unit of analysis.

The calibration target is a false-escalation probability no greater than .05. A confidence interval that includes .05 is inconclusive; a point estimate below .05 is not by itself evidence that the target is met. An upper confidence limit below .05 is evidence for that scenario and procedure under the simulator assumptions. The four monitor-scenario cells are all reported; no post hoc selection of a favorable cell is allowed. Any simultaneous claim across cells must account for multiplicity.

This is a calibration run only. Do not use its null outcomes to tune q_min, alpha, margin, stake family, scenarios, or monitor choice. A disjoint harmful-stream confirmation remains a separate next step. If the observed false-alarm rate is too high or inconclusive, diagnose validity and implementation assumptions on new development streams before running any final block.

## Reproduction

```powershell
uv run python scripts/diagnose_hard_budget_monitors.py `
  --output outputs/null_calibration_qmin020_2000 `
  --seeds 2000 `
  --seed-offset 52000000 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.20 `
  --scenarios stationary benign_nuisance `
  --methods uniform_proxy `
  --device cuda
```
