# Paired monitor bound sensitivity results

This is a development diagnostic, not a confirmatory experiment. It compares the same 30 generated streams (`39102026–39102055`) for uniform querying at a 20% label-dollar budget, with only the prediction-powered minimum propensity used in the global increment bound changed from 0.05 to 0.20. The bound falls from 198.9 to 45.9 for the registered cost range. The runs use CUDA for generation.

The paired check verified exact agreement on the 120 scenario-seed rows for labels queried, realized label spend, events processed, remaining budget, and budget compliance. All harm onsets were reached in both runs.

| Scenario | Monitor | Detections, q_min=.05 | Detections, q_min=.20 | q_min=.20 median delay |
|---|---|---:|---:|---:|
| Boundary-local harm | Fixed mixture | 0/30 | 19/30 (95% Wilson 0.455–0.781) | 1,129 |
| Boundary-local harm | Predictable variance | 0/30 | 19/30 (0.455–0.781) | 1,191 |
| Boundary-local harm | Predictable empirical Bernstein | 0/30 | 0/30 (0–0.114) | — |
| Recurring regimes | Fixed mixture | 0/30 | 20/30 (0.488–0.808) | 2,052.5 |
| Recurring regimes | Predictable variance | 0/30 | 19/30 (0.455–0.781) | 2,062 |
| Recurring regimes | Predictable empirical Bernstein | 0/30 | 1/30 (0.006–0.167) | 2,263 |

All monitors had zero false escalations in 30 stationary streams and zero in 30 benign-nuisance streams at both bounds. The 95% Wilson upper endpoint for 0/30 is 11.35%, so this does not establish the target 5% false-escalation rate. Reusing seeds makes this a well-matched diagnostic, not independent evidence. The paired exact McNemar test favors q_min=.20 over .05 for the fixed and variance monitors in the two harmful scenarios (p-values from 1.9e-6 to 3.8e-6); those unadjusted exploratory tests should not be treated as confirmatory inference.

The result supports a practical diagnosis: excessive global-bound width is a plausible power bottleneck in this design. It does not establish that either monitor is calibrated, that the q_min=.20 design is universally preferable, or that the research programme has a new method. PM-EB remains very conservative here. An independent, nondegenerate null-calibration experiment and a disjoint harm-confirmation block are required before selecting a primary procedure.

Reproduce the analysis with:

```powershell
uv run python scripts/analyze_monitor_bound_sensitivity.py
```

The command verifies pair alignment and writes `outputs/monitor_bound_sensitivity_qmin020/metrics/paired_qmin_sensitivity.csv`, a Markdown report, and updated artifact hashes. Source runs are described in [`monitor_power_diagnostic_protocol.md`](monitor_power_diagnostic_protocol.md).
