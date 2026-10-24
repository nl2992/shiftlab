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

|Scenario|Method|Expected excess above ε|Expected-positive event fraction|PPI increment variance|Full-feedback increment variance|Learner e-process crossing|Full-feedback crossing|Mean delay, learner / full feedback|
|---|---|---:|---:|---:|---:|---:|---:|---:|
|Stationary|Uniform|−0.0206|7.95%|3.924|0.740|0/60|0/60|— / —|
|Stationary|Evidence curve|−0.0207|7.96%|5.717|0.740|0/60|0/60|— / —|
|Benign nuisance|Uniform|−0.0205|7.94%|4.021|0.737|0/60|0/60|— / —|
|Benign nuisance|Evidence curve|−0.0205|7.97%|5.936|0.738|0/60|0/60|— / —|
|Boundary-local harm|Uniform|+0.1781|8.36%|7.661|1.469|6/60|60/60|1,466 / 396 events|
|Boundary-local harm|Evidence curve|+0.1788|8.38%|8.669|1.472|4/60|60/60|1,502 / 396 events|

For boundary-local harm, mean expected excess after the evaluator-defined onset was `+0.2767`
(uniform) and `+0.2782` (evidence curve). The candidate does not improve over uniform. The learner
crossing counts match the original comparison (6/60 and 4/60). All 60 full-feedback comparator
paths crossed after onset, with a mean delay of about 396 events, while sparse-feedback learner
paths crossed in only 10% and 6.7% of streams.

The mean PPI increment variance is about 5.2 times the full-feedback outcome variance under
boundary harm (7.66 vs 1.47 for uniform; 8.67 vs 1.47 for the evidence curve). This is a major
source of lost evidence efficiency under sparse labels and the current proxy/support bound. The
result is descriptive: it does not isolate proxy error from inverse-propensity correction,
time-varying propensities, or the e-process's fixed worst-case support.

The 7.9%–8.4% of events with positive expected excess are not stream-level null violations by
themselves. Under the registered controls, the average expected excess remains around `−0.021`,
below zero, while individual feature contexts can have positive conditional excess. The control
crossing counts remain diagnostics and do not replace independent null calibration.

## Interpretation and next step

The main signal bottleneck is the variance inflation from prediction-powered correction, not a
failure of the chosen propensity curve to reach the harmful regime. The evidence curve has slightly
higher increment variance and no detection advantage. Further tuning of its urgency curve is not
justified by this block.

Next, quantify the variance decomposition into proxy residual, inverse-propensity correction, and
support-bound dilution on a development-only design. Compare fixed mixture and established
predictable-variance e-processes using identical full-feedback outcomes and query paths. Any
variance-adaptive procedure must be checked against the exact conditional-mean null and
predictability assumptions; it should then receive independent nondegenerate null calibration and
a fresh alternative confirmation before promotion. Do not use these reused seeds for selection.

Reproduce with:

```powershell
uv run shiftlab-dive-hard-budget --seeds 60 --seed-offset 20373024 --n 3200 --d 16 --budget-rate 0.20 --q-min 0.10 --q-max 0.80 --common-eprocess-bound --device cuda --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy evidence_curve_a0.05_p0.5 --skip-figure --record-event-traces --output outputs/monitor_signal_diagnostic_20_60_v2
uv run python scripts/analyze_monitor_signal.py outputs/monitor_signal_diagnostic_20_60_v2/metrics/event_traces.parquet --output outputs/monitor_signal_diagnostic_20_60_v2/analysis
```

The eventwise traces, seed diagnostics, grouped summary, cumulative-log-e snapshots, report, and
hash manifest are stored under [`outputs/monitor_signal_diagnostic_20_60_v2/`](../outputs/monitor_signal_diagnostic_20_60_v2/).
