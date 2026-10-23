# Synthetic null calibration at q_min=.20

The frozen run evaluated 2,000 independent streams in each registered population-null control (stationary and benign nuisance), using uniform querying, a 20% hard label-dollar cap, alpha=.05, and the common q_min=.20 increment bound. The primary monitor is fixed mixture; predictable variance is secondary. PM-EB is exploratory. Requested device was CUDA; the manifest records the resolved device and runtime.

|Scenario|Monitor|False escalations|Rate|95% Wilson interval|95% exact upper|Primary-familywise 95% exact upper|Mean labels|Mean spend / budget|Cap violations|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
|stationary|fixed_mixture|0/2000|0.00000|[0.00000, 0.00192]|0.00150|0.00219|470.68|706.11 / 720.10|0|
|stationary|predictable_variance|0/2000|0.00000|[0.00000, 0.00192]|0.00150|0.00219|470.68|706.11 / 720.10|0|
|stationary|predictable_empirical_bernstein|0/2000|0.00000|[0.00000, 0.00192]|0.00150|—|470.68|706.11 / 720.10|0|
|benign_nuisance|fixed_mixture|0/2000|0.00000|[0.00000, 0.00192]|0.00150|0.00219|362.76|718.79 / 720.10|0|
|benign_nuisance|predictable_variance|0/2000|0.00000|[0.00000, 0.00192]|0.00150|0.00219|362.76|718.79 / 720.10|0|
|benign_nuisance|predictable_empirical_bernstein|0/2000|0.00000|[0.00000, 0.00192]|0.00150|—|362.76|718.79 / 720.10|0|

## Interpretation and limits

All six monitor-scenario cells had 0/2,000 false escalations. For each cell, the two-sided 95% Wilson interval is [0, 0.00192], and the one-sided 95% Clopper–Pearson upper limit is 0.00150. For the four pre-specified primary/secondary monitor-scenario cells, the Bonferroni simultaneous one-sided 95% upper limit is 0.00219. Thus the simulation provides evidence that the false-escalation rate is below 5% for these procedures under these two generated nulls; it does not prove the theorem's assumptions hold outside this simulator.

The four-cell familywise upper-limit criterion below 5%: **True**. Exact binomial tests against a one-sided 5% excess-rate alternative are included in the CSV; no post-hoc monitor selection is used.

The 90 finite-stream sample-path materiality flags in the benign-nuisance scenario are evaluator diagnostics, not population-null violations; they are retained in the CSV for transparency. Immediate labels, synthetic tariffs, the registered reference policy, and this scenario family limit interpretation. Delayed labels, serial dependence, adaptive candidate search, and misspecification were not tested. The result calibrates monitoring only; it says nothing about harmful-regime detection power or the novelty of a method.

## Reproduction and artifacts

The stream simulation command is in `docs/null_calibration_qmin020_protocol.md`. Rebuild the table and figure from saved observations with `uv run python scripts/analyze_null_calibration_results.py`. Raw stream observations are not published; the aggregate CSV, report, figure, and manifest are versioned.
