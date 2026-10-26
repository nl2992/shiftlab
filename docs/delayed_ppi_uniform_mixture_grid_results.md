# Fixed-delay PPI predictable uniform-mixture development results

## Finding

None of the three fixed convex mixtures cleared the registered nomination gate for independent confirmation. The 25% uniform blend came closest: its equal-weight macro detection difference versus uniform querying was +0.22 percentage points, with a 95% seed-cluster interval [-1.78, +2.33] points. It used 208.5 fewer labels on average. The 50% and 75% blends had macro differences of -0.56 and -0.33 points, respectively; their intervals also included zero. The pure evidence-directed rule had a -1.22-point macro difference.

Blending did reduce the worst loss in the early, strongest-harm cell. The pure evidence-directed rule lost 10 points there (74% vs 84% detections); the 25%, 50%, and 75% blends lost 2, 2, and 1 point. Label savings fell with greater uniform weight: 208.5, 135.4, and 65.8 fewer labels per stream. There was no setting that met the registered requirement of a positive macro interval, fewer labels than uniform, and no cell loss worse than five points. Do not treat the 25% blend as a selected winner or spend an independent confirmatory block on it under this gate.

| Query rule | Macro detection difference vs uniform (95% seed-cluster interval) | Mean label difference | Worst cell detection difference | Gate |
| --- | ---: | ---: | ---: | --- |
| Evidence-directed | -1.22 pp [-4.22, +1.78] | -287.1 | -10 pp | Fail |
| 25% uniform blend | +0.22 pp [-1.78, +2.33] | -208.5 | -3 pp | Fail |
| 50% uniform blend | -0.56 pp [-2.44, +1.33] | -135.4 | -3 pp | Fail |
| 75% uniform blend | -0.33 pp [-1.78, +1.11] | -65.8 | -1 pp | Fail |

## Design and integrity

The frozen CUDA development grid crossed three paired-cost harm shifts (0.10, 0.20, 0.30) with onset fractions 0.25, 0.50, and 0.75. Each of 100 seed clusters (20450000–20450099) was reused across all nine cells. Five query rules—uniform, pure evidence-directed, and three fixed blends—produced 4,500 method-stream records. The full-stream predictable-bound PPI monitor used fixed 12-event feedback, alpha 0.05, epsilon 0.05, and the shared 480-label cap. Data generation used the RTX 4060 CUDA device; event-ordered delayed-feedback replay used four CPU workers.

All 4,500 seed/cell/method keys are unique; every label cap and event-prefix invariant passed. The manifest protocol hash matches the frozen protocol and all eight artifact checksums verify. Exact runner and simulator source snapshots are preserved in the output directory, and the mixture simulator was isolated from the shared historical simulator so existing source-hash-pinned calibrations remain reproducible. Intervals are development-screen summaries after trying three blend weights; no confirmatory interpretation is warranted. Detection is not evidence that decision harm was prevented, and validity still depends on the stated conditional-mean and feedback assumptions.

## Implication for the research sequence

The predictable convex mixture is mathematically admissible under the same PPI assumptions because its propensity is fixed-weight, learner-history-predictable, and its realized value is used in the inverse-probability increment and eventwise bound. The experiment supplies no evidence that it improves the registered macro detection objective over uniform querying. Retire this blend search for the present design. The next useful progress is to benchmark already supported candidates on available real data under honest retrospective protocols, then use those findings to identify a theoretical target. Do not claim that real-data performance validates anytime guarantees.

## Reproduction and artifacts

```powershell
uv run shiftlab-dive-delayed-ppi-uniform-mixture-grid --device cuda --output-dir outputs/delayed_ppi_uniform_mixture_grid_100
```

The frozen [protocol](delayed_ppi_uniform_mixture_grid_protocol.md), metrics in CSV and Parquet, aggregate method summary, manifest, and checksums are under `outputs/delayed_ppi_uniform_mixture_grid_100/`. No figure was generated; use PaperBanana for any future research visual and verify plotted values against the saved outputs.
