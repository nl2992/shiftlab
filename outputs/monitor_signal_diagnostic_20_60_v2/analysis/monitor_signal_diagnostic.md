# Monitor signal diagnostic

Input trace: `outputs\monitor_signal_diagnostic_20_60_v2\metrics\event_traces.parquet`. The unit of aggregation is the stream seed. This is a descriptive re-analysis of the supplied run, not an independent replication, calibration study, or method-selection experiment.

`learner_*` values use only predictions and outcomes available under the run's query process. `evaluator_*` values use synthetic ground truth and full feedback for diagnosis only; they are not learner inputs. Expected excess cost is already centered at the configured harm margin, so positive values indicate expected harm above that margin.

The full-feedback comparator updates the same bounded betting mixture on every synthetic outcome. Its crossing rate is descriptive and does not establish a valid monitoring guarantee under the alternative. Null calibration must be assessed in separate null experiments.
For each evaluator-complete event, the exact conditional query-randomization variance is `(1-q)/q * (Z-h)^2`. The variance decomposition compares its stream average with the empirical PPI and full-feedback variances. This uses the realized synthetic stream and predictable q/h path; it is descriptive, not a confidence procedure.
An existing predictable-variance e-process and a plug-in empirical-Bernstein process are replayed on the exact same PPI increments and common support bound as the original fixed mixture. Propensities, proxies, labels, and horizons are unchanged. This is a paired development diagnostic; the processes have their conditional-mean guarantees only under their declared bounded-support and predictability assumptions, and these reused seeds do not independently calibrate them.
A further fixed-mixture replay uses the registered method-specific propensity lower bound: the target query rate for uniform policies and q_min for adaptive policies. The bound is fixed by the declared policy before evaluation and is not inferred from observed increment ranges. This sensitivity is valid only under the same stated null and filtration assumptions.
The existing plug-in empirical-Bernstein process is replayed on those same increments as another variance-sensitive established comparator. It also uses the global support bound. No monitor replay changes the acquisition path or constitutes independent calibration.

## Seed-aggregated results

|Scenario|Method|Streams|Mean expected excess cost|Bounded mean crossings: common / policy-specific bound|Predictable-variance crossings|PM-EB crossings|Full-feedback crossings|Bounded mean delay: common / policy-specific; other delays: PVA / PM-EB / full feedback|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.05_p0.5|60|-0.0205|0.000 / 0.000|0.000|0.000|0.000|nan / nan; nan / nan / nan|
|benign_nuisance|uniform_proxy|60|-0.0205|0.000 / 0.000|0.000|0.000|0.000|nan / nan; nan / nan / nan|
|boundary_local_harm|evidence_curve_a0.05_p0.5|60|0.1788|0.067 / 0.067|0.017|0.000|1.000|1502.2 / 1502.2; 1520.0 / nan / 395.5|
|boundary_local_harm|uniform_proxy|60|0.1781|0.100 / 0.783|0.017|0.000|1.000|1466.2 / 1164.2; 1422.0 / nan / 395.5|
|stationary|evidence_curve_a0.05_p0.5|60|-0.0207|0.000 / 0.000|0.000|0.000|0.000|nan / nan; nan / nan / nan|
|stationary|uniform_proxy|60|-0.0206|0.000 / 0.000|0.000|0.000|0.000|nan / nan; nan / nan / nan|

## Cumulative evidence snapshots

See `log_e_snapshots.csv` for mean and median cumulative log-e values at 25%, 50%, 75%, and 100% of each observed monitor path. These are descriptive trajectories; they are not additional independent test statistics.

See `variance_decomposition.csv` for the query-randomization variance, proxy residual RMSE, predicted total variance, and the PPI scale relative to its e-process support bound.

No visual was generated. PaperBanana is not available in the active environment.
