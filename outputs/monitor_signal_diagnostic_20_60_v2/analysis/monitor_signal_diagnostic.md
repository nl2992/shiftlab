# Monitor signal diagnostic

Input trace: `outputs\monitor_signal_diagnostic_20_60_v2\metrics\event_traces.parquet`. The unit of aggregation is the stream seed. This is a descriptive re-analysis of the supplied run, not an independent replication, calibration study, or method-selection experiment.

`learner_*` values use only predictions and outcomes available under the run's query process. `evaluator_*` values use synthetic ground truth and full feedback for diagnosis only; they are not learner inputs. Expected excess cost is already centered at the configured harm margin, so positive values indicate expected harm above that margin.

The full-feedback comparator updates the same bounded betting mixture on every synthetic outcome. Its crossing rate is descriptive and does not establish a valid monitoring guarantee under the alternative. Null calibration must be assessed in separate null experiments.
For each evaluator-complete event, the exact conditional query-randomization variance is `(1-q)/q * (Z-h)^2`. The variance decomposition compares its stream average with the empirical PPI and full-feedback variances. This uses the realized synthetic stream and predictable q/h path; it is descriptive, not a confidence procedure.
An existing predictable-variance e-process is replayed on the exact same PPI increments and support bound as the fixed mixture. Propensities, proxies, labels, and horizons are unchanged. This is a paired development diagnostic; the process has its conditional-mean guarantee only under its declared bounded-support and predictability assumptions, and these reused seeds do not independently calibrate it.
The existing plug-in empirical-Bernstein process is replayed on those same increments as another variance-sensitive established comparator. It also uses the global support bound. No monitor replay changes the acquisition path or constitutes independent calibration.

## Seed-aggregated results

|Scenario|Method|Streams|Mean expected excess cost|PPI increment variance|Fixed-mixture crossings|Predictable-variance crossings|PM-EB crossings|Full-feedback crossings|Fixed-mixture delay|Predictable-variance delay|PM-EB delay|Full-feedback delay|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.05_p0.5|60|-0.0205|5.9357|0.000|0.000|0.000|0.000|nan|nan|nan|nan|
|benign_nuisance|uniform_proxy|60|-0.0205|4.0210|0.000|0.000|0.000|0.000|nan|nan|nan|nan|
|boundary_local_harm|evidence_curve_a0.05_p0.5|60|0.1788|8.6693|0.067|0.017|0.000|1.000|1502.2|1520.0|nan|395.5|
|boundary_local_harm|uniform_proxy|60|0.1781|7.6612|0.100|0.017|0.000|1.000|1466.2|1422.0|nan|395.5|
|stationary|evidence_curve_a0.05_p0.5|60|-0.0207|5.7170|0.000|0.000|0.000|0.000|nan|nan|nan|nan|
|stationary|uniform_proxy|60|-0.0206|3.9240|0.000|0.000|0.000|0.000|nan|nan|nan|nan|

## Cumulative evidence snapshots

See `log_e_snapshots.csv` for mean and median cumulative log-e values at 25%, 50%, 75%, and 100% of each observed monitor path. These are descriptive trajectories; they are not additional independent test statistics.

See `variance_decomposition.csv` for the query-randomization variance, proxy residual RMSE, predicted total variance, and the PPI scale relative to its e-process support bound.

No visual was generated. PaperBanana is not available in the active environment.
