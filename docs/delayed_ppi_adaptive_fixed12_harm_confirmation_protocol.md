# Adaptive PPI fixed-delay harm confirmation

**Status: frozen before execution.** This disjoint positive-signal confirmation follows the passing 2,000-stream fixed-delay null calibration. It compares the registered evidence-directed query rule against uniform querying on a single prespecified boundary-harm alternative.

## Frozen design

- Use 1,000 fresh paired seed clusters, 20430000–20430999, disjoint from the prior null calibration (20420000–20421999) and the earlier selected calibration block (20410000–20410249).
- Generate 1,200 source and 2,400 target observations, with boundary-local expected paired-cost increase `+0.20` beginning at target event 1,200. Use alpha 0.05, epsilon 0.05, 20% nominal query rate, and the pathwise 480-label cap.
- Compare `evidence_a0p025_p0p5_eventwise` with `uniform_eventwise`, each using the full-stream predictable-bound PPI e-process. Use a fixed 12-event feedback delay for every queried target label. Continue sampling after an alarm while budget remains so each method is evaluated through the same event horizon or its own cap exhaustion.
- Reuse each seed's generated source, target contexts, and outcomes across both query rules. The query coins are generated from the same seed-specific stream; their realized request schedules may differ because the policies differ.
- The primary endpoint is the paired difference in post-onset detection probability (evidence-directed minus uniform) over 1,000 seed pairs. Report a percentile paired bootstrap 95% interval, one-sided exact McNemar p-value, label difference, processed events, pre-onset alarms, and event/wall detection delays. Count pre-onset alarms as competing events, not post-onset detections.

## Advancement gate

Advance this query rule for the registered alternative only if the paired detection interval's lower endpoint is above zero, mean labels are no greater than uniform, every stream respects the 480-label cap, all labels resolve, all registered event prefixes are updated, and all expected seed/method keys are unique. This is not a guarantee of avoided decision harm, nor evidence for other onset times, effect sizes, delay profiles, dependence structures, or real data. No novelty claim follows from comparing established components.

No visual is planned. Use PaperBanana for any future research visual.

## Reproduction

```powershell
uv run shiftlab-dive-delayed-ppi-fixed12-confirm --device cuda --calibration-manifest outputs/delayed_ppi_adaptive_fixed12_replication_2000/manifest.json --output-dir outputs/delayed_ppi_adaptive_fixed12_harm_confirmation_1000
```
