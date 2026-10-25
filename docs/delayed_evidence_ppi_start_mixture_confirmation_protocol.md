# Delayed PPI fixed-start mixture: disjoint Markov-scale confirmation

**Status: frozen after development and passing null calibration.** Confirm the fixed equal-weight eight-start mixture against the full-stream predictable-bound e-process using 300 fresh seed clusters, 20322000–20322299. The separate calibration used seeds 20321000–20321499; the matched-shadow development screen used 20320000–20320059.

Use the same 2,400-event persistent-scale Markov harm generator and the same three onset fractions (0.25, 0.50, 0.75) as the matched-acquisition development protocol. Retain flip probability 0.05, amplitudes `{0.55,1.0}`, shift +0.20, independent delays uniform on 0–12, alpha 0.05, epsilon 0.05, the selected evidence-directed query policy, and the 480-label cap. For each seed and onset, simulate both monitors together. The full-stream process alone chooses the evidence-directed propensity; both monitors receive the same event-order-resolved PPI increments and predictable bounds, and sampling continues to the horizon after any alarm. Verify exact query-schedule hashes, label counts, and event counts for every pair. Validate the calibration gate, matching source hashes/configuration, and disjoint seed block before starting.

The sole primary endpoint is the mean paired detection difference (start mixture minus full stream), first averaged equally over the three onset fractions within each seed and then over the 300 independent seed clusters. Report a percentile bootstrap 95% cluster interval from 20,000 resamples. Retain the performance claim only if the point estimate is positive, the lower interval endpoint exceeds zero, per-pair query schedules/labels/events match, the label cap and event-prefix checks all pass, and the calibration manifest remains valid. Do not use rowwise McNemar inference because the three onset observations reuse the same seed cluster. Onset-specific rates and delays are secondary descriptive results.

This confirms only the registered synthetic alternative and acquisition/filtration design. The start mixture is standard fixed convex composition of e-processes; no novelty claim follows. No figure is planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-start-confirm --seeds 300 --seed-offset 20322000 --device cuda --protocol docs/delayed_evidence_ppi_start_mixture_confirmation_protocol.md --calibration-manifest outputs/delayed_evidence_ppi_start_mixture_calibration_500/manifest.json --output-dir outputs/delayed_evidence_ppi_start_mixture_confirmation_300`
