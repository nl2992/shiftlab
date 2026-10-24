# Residual-variance monitor power: diagnostic findings

## Main result

The earlier near-zero detection at label rates 0.20 and 0.40 persists even when the residual-variance shift is made much stronger. In 100 seeds per cell, no monitor detected any material-harm stream at q=0.20 for any tested severity. At the strongest severity (4.5), q=0.40 yielded 2/100 detections for fixed-mixture and predictable Kelly and 0/100 for plug-in empirical-Bernstein. Increasing q helped only modestly: at severity 4.5 and q=0.80, detection was 11/100, 7/100, and 1/100 respectively; at q=1.00, it was 10/100, 8/100, and 1/100.

| Severity | Mean paired excess cost | Mean excess over ε=.10 | Fixed-mixture detections at q=.2/.4/.6/.8/1.0 | Kelly detections at q=.2/.4/.6/.8/1.0 | Plug-in EB detections at q=.2/.4/.6/.8/1.0 |
| ---: | ---: | --- | --- | --- | --- |
| 0.75 | 0.1068 | 0.0068 | 0/100, 1/100, 1/100, 0/100, 0/100 | 0/100, 1/100, 0/100, 1/100, 0/100 | 0/100 throughout |
| 1.50 | 0.1189 | 0.0189 | 0/100, 1/100, 2/100, 3/100, 4/100 | 0/100, 1/100, 2/100, 1/100, 3/100 | 0/100, 0/100, 0/100, 0/100, 1/100 |
| 2.25 | 0.1256 | 0.0256 | 0/100, 2/100, 4/100, 5/100, 5/100 | 0/100, 2/100, 4/100, 3/100, 5/100 | 0/100, 0/100, 0/100, 0/100, 1/100 |
| 3.00 | 0.1298 | 0.0298 | 0/100, 2/100, 4/100, 8/100, 6/100 | 0/100, 2/100, 4/100, 3/100, 6/100 | 0/100, 0/100, 0/100, 0/100, 1/100 |
| 4.50 | 0.1348 | 0.0348 | 0/100, 2/100, 7/100, 11/100, 10/100 | 0/100, 2/100, 7/100, 7/100, 8/100 | 0/100, 0/100, 0/100, 1/100, 1/100 |

Mean paired excess cost averages the five query-rate arms; the expected mean changes slightly with q because the hard label budget can stop a stream at a slightly different event.

Detection counts are out of 100 streams. At severity 0.75, 94 streams crossed the per-stream material-harm criterion; the other six remain in the denominator and cannot count as detections. The other severities had 99–100 material-harm streams. This small denominator variation does not change the conclusion.

## Why detection remains low

The result is not explained by label sparsity alone. At severity 4.5, the mean expected paired loss is about 0.135 per event, only 0.035 above the decision margin. The mean variance of the centered realized paired outcomes is about 0.95. Even with all labels observed, the finite monitoring horizon is about 1,590 events and only 10% of fixed-mixture streams cross the anytime threshold. Thus the hard part is accumulating evidence for a small positive mean relative to substantial outcome noise under an anytime-valid threshold; increasing query rate removes imputation noise but cannot remove outcome noise.

At q=0.20 and severity 4.5, the diagnostic PPI variance approximation is 3.30 and estimator RMSE is 1.81. At q=0.80 these fall to 0.21 and 0.45, while detection rises only to 11% for fixed-mixture. At q=1.00 PPI estimation error is effectively zero, yet detection is only 10%. This is direct evidence that a lower proxy-estimation error does not by itself guarantee high monitoring power.

The plug-in empirical-Bernstein monitor is the most conservative in this design and rarely alarms. The fixed-mixture and Kelly processes have similar power here; neither dominates uniformly over these rates and severities. Given 100 seeds per cell, these are diagnostic rankings, not precise comparative claims. A few alarms occur before the evaluator-defined harm onset in some alternatives; this grid does not estimate null error control.

## What this says about the method and the next experiment

The immediate bottleneck is weak per-event excess loss, rather than a failure to query enough labels. More labels reduce PPI variance but cannot change the target's mean signal or outcome variance. The next scientifically useful experiment is a horizon-by-effect-size study with a registered population-null control, plus a separate evaluation of an anytime test calibrated for the exact finite-stream feedback assumptions. It should distinguish (a) more observations under the same small effect, (b) a genuinely larger action-dependent loss gap, and (c) a decision rule that chooses whether querying is worth its cost. Do not claim the existing monitors are ineffective in general: this is one deliberately noisy synthetic condition and one proxy.

## Reproducibility and artifacts

The grid was run with `uv run python -m shiftlab.dive.residual_variance_power_grid --device cuda --seeds 100` on an NVIDIA GeForce RTX 4060 Laptop GPU (CUDA 13.0, PyTorch 2.9.1+cu130). It produced 7,500 monitor-stream rows. The manifest records the SHA-256 of the Parquet metrics as `d38dc373843240662dcdc882642eef2e76f01f9a035d00c4cdade6d1dac81e44`.

The complete rows are in `outputs/residual_variance_power_grid/metrics.parquet` and `metrics.csv`; grouped results are in `power_summary.csv`. No plot is included in this diagnostic report.
