# Delayed PPI fixed-start mixture: Markov-scale null calibration

**Status: frozen before execution.** Calibrate the exact matched-acquisition shadow design nominated by the disjoint development screen. Use 500 fresh streams, seeds 20321000–20321499, generated under the persistent-scale Markov conditional-mean null: regime flip probability 0.05, amplitudes `{0.55,1.0}`, independent fair signs, hidden regime, independent delays uniform on 0–12, 2,400 target events, and the same 1,200-event source and 480-request hard cap.

Run the primary `evidence_a0p025_p0p5_eventwise` acquisition crossed with the full-stream and equal-weight eight-start monitor. The full-stream process alone determines query propensities for both monitors. Continue querying and updating through the full event horizon after any alarm. The two monitors must have identical query-schedule hashes, queried-label counts, and processed-event counts for every paired seed. The conditional-mean null is `E[Z_t | complete event history]=0`; persistent scale alone does not violate it because signs are fresh and fair. This calibration makes no claim for serially dependent signs, informative delays, or changed filtration assumptions.

There are two simultaneously controlled monitor cells, each with 500 independent streams. Compute one-sided exact Clopper–Pearson upper limits with Bonferroni cell level `0.05/2`. The familywise calibration gate passes only if both upper limits are at most 0.05 and all row, hard-cap, delayed-prefix, and matched-query invariants pass. Failure ends this monitor's advancement under this registered design. Passing permits, but does not itself provide, a disjoint alternative confirmation. Finite Monte Carlo calibration is a diagnostic in addition to the e-process argument, not its proof.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-start-calibrate --seeds 500 --seed-offset 20321000 --device cuda --protocol docs/delayed_evidence_ppi_start_mixture_calibration_protocol.md --output-dir outputs/delayed_evidence_ppi_start_mixture_calibration_500`
