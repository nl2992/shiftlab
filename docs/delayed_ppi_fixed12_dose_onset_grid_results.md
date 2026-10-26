# Fixed-delay adaptive PPI dose-by-onset development results

## Result

The registered nine-cell CUDA development screen did **not** nominate the evidence-directed query rule for a broad independent confirmation. Across the equally weighted dose-by-onset design, its paired detection difference versus uniform querying was -0.17 percentage points (seed-cluster 95% bootstrap interval -2.33 to +2.06 points). The worst cell was a 0.30 harm shift beginning at 25% of the horizon, where evidence-directed querying detected 70.5% and uniform querying 87.5%, a -17-point difference (descriptive cellwise interval -24 to -10 points).

The result is heterogeneous. At the registered center design (shift 0.20, onset 0.50), evidence-directed querying detected 9.0% versus 2.0% for uniform (+7 points; descriptive interval +3 to +11.5). At shift 0.30 and onset 0.50 the difference was +8 points; at shift 0.30 and onset 0.75 it was +3.5 points. Early strong harm favors uniform allocation, while the evidence-directed policy generally uses fewer labels. Its equal-weight mean label difference was -282.42 labels per stream (95% seed-cluster interval -290.68 to -273.79); the largest detection loss and near-zero macro effect mean this is an efficiency tradeoff, not a generally superior policy.

## Design and checks

The frozen design crossed paired-cost harm shifts 0.10/0.20/0.30 with onsets at 25%/50%/75% of a 2,400-event horizon. It used 200 common-random-number seed clusters per cell (seeds 20440000–20440199), fixed 12-event label delay, a 480-label cap, and the full-stream predictable-bound PPI monitor. CUDA generated streams; four CPU workers replayed the feedback process. The run produced 3,600 method-stream records across nine cells.

All registered invariants passed: stream keys were complete, event and feedback prefixes were valid, the hard label cap held, and checksums and protocol/source hashes were recorded in the manifest. The cellwise intervals and p-values are descriptive and unadjusted. The macro interval applies only to the registered equally weighted nine-cell design. The nomination gate failed, so these data do not support a broad confirmatory claim.

## Interpretation and next step

The candidate's gains concentrate in middle and later onsets, whereas uniform querying protects power for early, high-dose harm. The current evidence-directed policy therefore has no general advantage across onset and dose. Do not promote it as the default. A convex predictable mixture with uniform querying is a plausible next *development candidate*: predictable propensities retain the established PPI validity argument when each realized propensity is used in its corresponding increment bound. It would need a newly frozen development screen, its own independent null calibration, and disjoint confirmation before any performance claim. No novelty claim follows from this experiment.

## Reproduction and artifacts

```powershell
uv run shiftlab-dive-delayed-ppi-fixed12-dose-onset-grid --device cuda --output-dir outputs/delayed_ppi_fixed12_dose_onset_grid_200
```

Protocol: [delayed PPI dose-by-onset grid](delayed_ppi_fixed12_dose_onset_grid_protocol.md). Checksummed metrics, cell summary, manifest, and aggregate macro result are in `outputs/delayed_ppi_fixed12_dose_onset_grid_200/`. No figure was generated; any future research visual must use PaperBanana and be checked against these saved metrics.
