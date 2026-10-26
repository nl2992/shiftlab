# Fixed-delay adaptive PPI dose-by-onset development grid

**Status: frozen before execution; descriptive development screen.** This extends the disjoint fixed-delay confirmation across a prespecified harm-dose and onset grid. The evidence-directed rule remains frozen; this is not hyperparameter tuning and cannot establish a broad claim without an independent confirmation.

## Design

- Compare `evidence_a0p025_p0p5_eventwise` with `uniform_eventwise`; both use the full-stream predictable-bound PPI monitor, fixed 12-event feedback delay, alpha 0.05, epsilon 0.05, and the same 480-label hard cap.
- Cross expected paired-cost increases `0.10`, `0.20`, and `0.30` with onset fractions `0.25`, `0.50`, and `0.75` over a 2,400-event horizon. Use 200 paired seeds per cell, 20440000–20440199, for 1,800 seed-cell streams and 3,600 method-stream rows. Each seed is reused across all nine cells as a common-random-number cluster; inference on the macro endpoint resamples seeds as clusters.
- Use 1,200 source events. Generate streams on CUDA when available, then parallelize independent event-order replays across four CPU workers. Continue after alarms while budget remains. Both methods receive the same source/target stream within each cell and seed; policy-specific query paths may differ.
- The primary development endpoint is the equal-weight macro paired difference in post-onset detection across the nine cells, averaged within each seed before computing a 20,000-resample seed-cluster bootstrap 95% interval. Also report cellwise detection, label use, pre-onset alarms, event/wall delay, cap and prefix checks. Cellwise intervals and tests are descriptive and are not multiplicity-adjusted.

## Interpretation gate

Nominate the frozen rule for an independent macro confirmation only if the macro detection interval's lower endpoint is above zero, macro mean label use is no higher than uniform, and no cell has a detection point-estimate loss below −5 percentage points. This screen does not authorize a broad claim. The fixed-delay IID null calibration is separate; no alternative cell is treated as a null. Report the calibration and harm outcomes separately. Detection is not direct evidence of prevented harm; no novelty claim follows from established query and e-process components.

No visual is planned. Use PaperBanana for any future research visual.

## Reproduction

```powershell
uv run shiftlab-dive-delayed-ppi-fixed12-dose-onset-grid --device cuda --output-dir outputs/delayed_ppi_fixed12_dose_onset_grid_200
```
