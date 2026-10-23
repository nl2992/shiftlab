# Extended hard-budget scenario benchmark protocol

## Purpose and claim scope

This experiment tests whether the existing label-query policies behave similarly across several distinct synthetic shift mechanisms. It is exploratory scenario-generalization evidence, not a confirmatory ranking of policies, a power-calibrated test, or evidence that any policy is generally best. The primary research question remains whether distributional change predicts decision harm and whether evidence-guided interventions improve decision outcomes under explicit constraints.

## Locked configuration

- Scenarios: `boundary_local_harm`, `residual_variance`, `recurring_regimes`, and `harmful_adaptation`.
- Methods: `uniform_proxy`, `variance_proxy`, `decision_value_proxy`, `cost_variance_proxy`, and `cost_stabilized_proxy`.
- Replicates: 60 independent seeds per scenario, starting at seed offset `20363022`.
- Stream size and dimension: `n=3200`, `d=16`.
- Query budget: validation-tariff rate `0.20`; minimum and maximum query propensities `0.10` and `0.80`.
- Evidence process: `alpha=0.05`, with a common e-process bound derived from `q_min` for every method (`common_eprocess_bound=True`).
- Compute: CUDA where available; the run records the resolved device in its manifest.

All methods receive the same generated stream and common query random numbers within each scenario and seed. The hard label-dollar budget is computed from the validation-period mean label cost. The cost-stabilized method mixes its allocation with the cost-neutral propensity determined from validation data. Synthetic evaluator parameters, oracle actions, and expected losses are not used as learner inputs.

## Reproduction

From the repository root, run:

```powershell
uv run shiftlab-dive-hard-budget `
  --seeds 60 `
  --seed-offset 20363022 `
  --n 3200 `
  --d 16 `
  --budget-rate 0.20 `
  --q-min 0.10 `
  --q-max 0.80 `
  --common-eprocess-bound `
  --device cuda `
  --scenarios boundary_local_harm residual_variance recurring_regimes harmful_adaptation `
  --methods uniform_proxy variance_proxy decision_value_proxy cost_variance_proxy cost_stabilized_proxy `
  --output outputs/hard_budget_extended_scenarios_60
```

Expected metric cardinality is 1,200 method-scenario-seed rows. Inspect the Parquet metrics, generated summary, figure, and manifest under the output directory. The manifest contains configuration and source hashes; rerun the repository's manifest finalizer if any generated report or figure is changed after the experiment.

## Interpretation and limitations

Report per-scenario detection, decision loss, regret, label spend, and budget violations. A method's detection rate is conditional on this synthetic generator and the hard-budget stopping rule. The four scenarios do not cover every form of nonstationarity, dependence, label delay, or adaptive sampling. Sixty seeds are descriptive unless a separate power analysis is registered for a specific contrast and effect size. Do not pool the four mechanisms into a single universal policy ranking or present this benchmark as validating a real-world guarantee.
