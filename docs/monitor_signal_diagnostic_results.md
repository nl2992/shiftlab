# Monitor signal diagnostic: 20% hard-budget run

**Status:** Descriptive diagnosis of the frozen 20% evidence-allocation comparison. The diagnostic
reuses seeds `20373024`–`20373083` from the comparison and is not an independent replication or a
method-selection block. No visual was generated; PaperBanana was unavailable in the active
environment.

## Design and artifacts

The CUDA run used the RTX 4060 Laptop GPU, 60 streams in each of stationary, benign-nuisance, and
boundary-local-harm scenarios, 3,200 events per stream, a 20% target label-dollar rate, a common
pathwise cap, and the same query uniforms for uniform and the preselected evidence curve. It
records 812,700 event rows across 360 method-stream paths. Every stream respected its cap. The
source and artifact hashes are in [`manifest.json`](../outputs/monitor_signal_diagnostic_20_60_v2/reports/manifest.json).

The event trace stores learner-observed excess cost only when a label was queried. Expected paired
cost, harm-margin-centered expected excess, realized full-feedback outcomes, and the full-feedback
e-process are explicitly evaluator-only. Those fields never enter propensity selection, the proxy,
or the learner monitor. The analyzer checks that expected excess equals expected paired cost minus
the configured margin.

## Results

|Scenario|Method|Expected excess above ε|PPI increment variance|Fixed-mixture crossing|Predictable-variance crossing|Full-feedback crossing|Mean delay: fixed / predictable-variance / full feedback|
|---|---|---:|---:|---:|---:|---:|---:|
|Stationary|Uniform|−0.0206|3.924|0/60|0/60|0/60|— / — / —|
|Stationary|Evidence curve|−0.0207|5.717|0/60|0/60|0/60|— / — / —|
|Benign nuisance|Uniform|−0.0205|4.021|0/60|0/60|0/60|— / — / —|
|Benign nuisance|Evidence curve|−0.0205|5.936|0/60|0/60|0/60|— / — / —|
|Boundary-local harm|Uniform|+0.1781|7.661|6/60|1/60|60/60|1,466 / 1,422 / 396 events|
|Boundary-local harm|Evidence curve|+0.1788|8.669|4/60|1/60|60/60|1,502 / 1,520 / 396 events|

For boundary-local harm, mean expected excess after the evaluator-defined onset was `+0.2767`
(uniform) and `+0.2782` (evidence curve). The candidate does not improve over uniform. The learner
crossing counts match the original comparison (6/60 and 4/60). All 60 full-feedback comparator
paths crossed after onset, with a mean delay of about 396 events, while sparse-feedback learner
paths crossed in only 10% and 6.7% of streams.

The conditional randomization-variance identity gives a direct decomposition:
`Var_Q[h + Q/q (Z-h) | Z,h,q] = (1-q)/q (Z-h)^2`. On boundary harm, the mean across-stream
full-feedback variance was 1.469 (uniform), and the mean query-randomization contribution was
6.044, predicting total variance 7.512; observed PPI increment variance was 7.661. For the evidence
curve, the corresponding values were 1.472 + 6.884 = 8.357 predicted versus 8.669 observed. Thus
the query-randomization term accounts for about 98% and 96% of the observed variance increase,
respectively. Mean proxy-residual RMSE was 1.228–1.230. The predicted totals are close to, but do
not exactly equal, the observed cross-event variances because this is a finite, adaptive path and
the decomposition is conditional on its realized stream and predictable acquisition path.

The common PPI support bound was 96.9. Mean absolute PPI increments used only 0.58% of that
bound (maximum observed fractions averaged 26.6% for uniform and 46.3% for the evidence curve).
This indicates substantial scale mismatch between observed increments and the global worst-case
support. It is a diagnostic, not proof that replacing the bound with a smaller or data-dependent one
would preserve validity. The machine-readable decomposition is in
[`variance_decomposition.csv`](../outputs/monitor_signal_diagnostic_20_60_v2/analysis/variance_decomposition.csv).

I also replayed the existing predictable-variance e-process on the same PPI values and support
bound, leaving query propensities, proxies, feedback and horizons unchanged. It crossed in only
1/60 boundary-harm streams for each allocation method, compared with 6/60 for the fixed mixture
under uniform queries and 4/60 for the evidence curve. This established stake adaptation did not
recover the lost evidence on these paths. It remains a valid comparator under the same
bounded-increment conditional-mean assumptions, but does not advance.

The 7.9%–8.4% of events with positive expected excess are not stream-level null violations by
themselves. Under the registered controls, the average expected excess remains around `−0.021`,
below zero, while individual feature contexts can have positive conditional excess. The control
crossing counts remain diagnostics and do not replace independent null calibration.

## Interpretation and next step

The main signal bottleneck is the variance inflation from prediction-powered correction, not a
failure of the chosen propensity curve to reach the harmful regime. The evidence curve has slightly
higher increment variance and no detection advantage. Further tuning of its urgency curve is not
justified by this block.

The exact decomposition now attributes nearly all empirical variance inflation to Bernoulli query
randomization on this stream. The predictable-variance replay also failed to improve detection.
Next, diagnose whether valid predictable bounds or stake schedules improve signal without relying
on evaluator residuals. This paired trace replay is development-only;
any selected procedure requires independent nondegenerate null calibration and a fresh alternative
confirmation. Do not use these reused seeds for selection or claim a smaller bound from the observed
increment range.

Reproduce with:

```powershell
uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20373024 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0.05_p0.5 --skip-figure --record-event-traces --output outputs/monitor_signal_diagnostic_20_60_v2
uv run python scripts/analyze_monitor_signal.py outputs/monitor_signal_diagnostic_20_60_v2/metrics/event_traces.parquet --output outputs/monitor_signal_diagnostic_20_60_v2/analysis
```

The eventwise traces, seed diagnostics, grouped summary, cumulative-log-e snapshots, report, and
hash manifest are stored under [`outputs/monitor_signal_diagnostic_20_60_v2/`](../outputs/monitor_signal_diagnostic_20_60_v2/).
