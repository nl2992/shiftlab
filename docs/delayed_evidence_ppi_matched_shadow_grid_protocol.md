# Delayed PPI fixed-start mixture: matched-acquisition shadow development

**Status: frozen before execution.** This is a separate development screen on seeds 20320000–20320059. It follows the closed-loop start-mixture screen, which increased detection but used more labels and therefore failed its registered advancement gate. This design isolates monitor power by fixing the acquisition path.

Use the same 60-seed persistent-scale Markov harm design as the [first start-mixture screen](delayed_evidence_ppi_start_mixture_grid_protocol.md): 1,200 source events, 2,400 target events, 20% target-rate query policy with 480 hard requests, alpha 0.05, epsilon 0.05, propensity support `[0.05,0.80]`, regime flip probability 0.05, amplitudes `{0.55,1.0}`, conditional mean shift +0.20, independent uniform delays 0–12, and harm onsets at 25%, 50%, or 75% of the event horizon. The hidden regime remains evaluator-only.

Compare the same two query policies (uniform and `evidence_a0p025_p0p5_eventwise`) and two shadow monitors (full-stream predictable-bound e-process and the fixed equal-weight eight-start mixture at `(0,300,600,900,1200,1500,1800,2100)`). For each evidence-directed pair, the full-stream monitor alone determines the predictable query propensity in both arms. Both monitor processes receive the same event-order-resolved increments and event-specific predictable bounds. Both arms continue querying and updating through the common event horizon after an alarm, subject to the same realized 480-label cap. Uniform-query pairs also share their query uniforms and continue to the common horizon. Therefore, queried labels, processed events, query propensities, delays, and costs must match exactly within every monitor pair.

The primary descriptive contrast is the seed-cluster paired difference in post-onset detection between the start mixture and full-stream monitor under evidence-directed acquisition, equally weighted over the three onset fractions. Report onset-specific detection, pre-onset alarms, detection delay, labels, processed events, and all cap/prefix invariants. A fixed start mixture is an e-process by convexity when each component is an e-process under the same filtration and null; this screen does not validate that assumption for environments outside the registered model.

Advance to independent null calibration only if the pooled paired detection difference is positive, the seed-cluster bootstrap 95% lower endpoint is above zero, per-pair label and event counts match exactly, and all cap/prefix checks pass. This is still a development screen; do not present its intervals as confirmatory inference. No start times or weights are tuned in this run. No visual is planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-start-grid --matched-shadow --seeds 60 --seed-offset 20320000 --device cuda --protocol docs/delayed_evidence_ppi_matched_shadow_grid_protocol.md --output-dir outputs/delayed_evidence_ppi_matched_shadow_grid_60`
