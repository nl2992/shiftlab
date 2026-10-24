# Monitor signal diagnostic

Input trace: `outputs\monitor_signal_diagnostic_20_60_v2\metrics\event_traces.parquet`. The unit of aggregation is the stream seed. This is a descriptive re-analysis of the supplied run, not an independent replication, calibration study, or method-selection experiment.

`learner_*` values use only predictions and outcomes available under the run's query process. `evaluator_*` values use synthetic ground truth and full feedback for diagnosis only; they are not learner inputs. Expected excess cost is already centered at the configured harm margin, so positive values indicate expected harm above that margin.

The full-feedback comparator updates the same bounded betting mixture on every synthetic outcome. Its crossing rate is descriptive and does not establish a valid monitoring guarantee under the alternative. Null calibration must be assessed in separate null experiments.

## Seed-aggregated results

|Scenario|Method|Streams|Mean expected excess cost|Fraction positive|PPI increment variance|Full-feedback increment variance|Learner crossings|Full-feedback crossings|Learner post-onset crossings|Full-feedback post-onset crossings|Learner delay|Full-feedback delay|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|benign_nuisance|evidence_curve_a0.05_p0.5|60|-0.0205|0.080|5.9357|0.7378|0.000|0.000|0.000|0.000|nan|nan|
|benign_nuisance|uniform_proxy|60|-0.0205|0.079|4.0210|0.7371|0.000|0.000|0.000|0.000|nan|nan|
|boundary_local_harm|evidence_curve_a0.05_p0.5|60|0.1788|0.084|8.6693|1.4722|0.067|1.000|0.067|1.000|1502.2|395.5|
|boundary_local_harm|uniform_proxy|60|0.1781|0.084|7.6612|1.4686|0.100|1.000|0.100|1.000|1466.2|395.5|
|stationary|evidence_curve_a0.05_p0.5|60|-0.0207|0.080|5.7170|0.7395|0.000|0.000|0.000|0.000|nan|nan|
|stationary|uniform_proxy|60|-0.0206|0.080|3.9240|0.7400|0.000|0.000|0.000|0.000|nan|nan|

## Cumulative evidence snapshots

See `log_e_snapshots.csv` for mean and median cumulative log-e values at 25%, 50%, 75%, and 100% of each observed monitor path. These are descriptive trajectories; they are not additional independent test statistics.

No visual was generated. PaperBanana is not available in the active environment.
