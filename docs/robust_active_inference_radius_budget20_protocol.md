# Robust active-inference radius grid at a 20% label-dollar budget

**Status: frozen development screen.** This extends the earlier 10% radius grid to a budget and
propensity design used in the project's independent policy-specific calibration work. It is a
development screen only: 30 seeds per scenario cannot establish calibration or confirm a selected
method. The six radius values and the validation-only path selection remain defined in
[`robust_active_inference_radius_grid_protocol.md`](robust_active_inference_radius_grid_protocol.md).

## Question

At a 20% expected dollar-rate target, does validation-selected robust active-inference acquisition
improve harm detection or reduce evaluator-known decision-harm exposure relative to uniform,
variance, and cost-variance querying under the same monitor support bound and pathwise label cap?
This tests the existing batch-inspired allocation adaptation. It does not add a sequential guarantee
or assert novelty.

## Frozen design

- 30 matched seeds per each of `stationary`, `benign_nuisance`, and `boundary_local_harm`; seed
  block `56300000–56300029`, disjoint from the prior radius development block `56220000–56220029`.
- `n=3200`, `d=16`, budget rate `0.20`, `q_min=0.10`, `q_max=0.80`, alpha `0.05`, harm margin
  `0.10`, common e-process bound enabled, maximum label tariff `2.5`.
- Nine methods: `uniform_proxy`, `variance_proxy`, `cost_variance_proxy`, and robust active-inference
  radius fractions `{0, 0.1, 0.25, 0.5, 1, 2}`. Use common generated streams and per-seed query
  uniforms. The same q-floor-derived support bound applies to every method; report the recorded
  bound from each result row.
- Generate streams on CUDA, two workers, and `--skip-figure`. Do not draw or substitute a figure;
  any future research visual must use PaperBanana.
- Do not tune from null counts or replace seeds. Keep oracle expected costs and harm onset evaluator-
  only.

## Outcomes and selection rule

The decision-relevant development outcomes are detection among all evaluator-defined material-harm
streams, harm-onset reachability, and evaluator exposure under the **alarm-only fallback** rule: the
reference policy follows an alarm, while monitoring-budget exhaustion without an alarm does not
change the deployed policy. Also report the frozen budget-stop-fallback exposure as a separate
operational sensitivity, not as evidence-triggered intervention. Secondary measures are macro and
scenario-specific stream-mean RMSE, false escalations on both null controls, realized label spend,
labels, processed events, and selected path `rho`.

Use paired seed-cluster bootstrap intervals for continuous contrasts against uniform, equal-weight
scenario macro-averages for detection, and show all six radii and both heuristic references. These
30-seed intervals are descriptive and unadjusted; null alarms are diagnostics only. Do not select a
radius from estimator RMSE if it does not improve or preserve the decision outcomes. If the grid
shows a credible development candidate, freeze it before conducting fresh null calibration and
disjoint harm confirmation. If all methods fail to detect harm, do not claim an intervention gain;
the result identifies an evidence-collection/monitoring limitation for the next method-development
step.

## Reproduction

```powershell
uv run shiftlab-dive-hard-budget --seeds 30 --seed-offset 56300000 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --device cuda --workers 2 --common-eprocess-bound --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy variance_proxy cost_variance_proxy robust_active_inference_r0 robust_active_inference_r0.1 robust_active_inference_r0.25 robust_active_inference_r0.5 robust_active_inference_r1 robust_active_inference_r2 --skip-figure --output outputs/robust_active_inference_radius_budget20_development
uv run python scripts/analyze_radius_decision_harm_exposure.py --input outputs/robust_active_inference_radius_budget20_development/metrics/hard_budget_comparison.parquet --output-dir outputs/robust_active_inference_radius_budget20_development/analysis
```

The first command must refuse to overwrite an existing output directory. Verify the run and analysis
checksums, CUDA manifest, row counts, method/scenario completeness, hard-budget constraints, and
learner/evaluator separation before interpreting results.
