# Delayed evidence-directed PPI: independent null calibration protocol

**Status:** frozen before execution. This calibration uses seeds 20280000–20280999, disjoint from the 30-seed development grid (20272000–20272029). Do not tune the candidate or thresholds after opening calibration results.

## Candidate and controls

Calibrate the development-selected `evidence_a0p025_p0p5_eventwise` and `uniform_eventwise` methods on two null controls: `stationary` and `benign_variance_shift`. Each method/scenario cell receives 1,000 independent streams. Source, target contexts/outcomes, query uniforms, and independent delays are paired between methods within each seed. Both methods use the frozen source-only linear proxy, event-history e-process, `epsilon=0.05`, `alpha=0.05`, query support `[0.05,0.80]`, and pathwise cap of 480 requested labels over a 2,400-event horizon; queried labels have independent uniform delays 0–12.

For both controls, `E[Z_t | G_(t-1)]=0`, including after the variance decrease. The null is stronger than the tested inequality `E[Z_t | G_(t-1)]<=epsilon`. A false escalation is any event-prefix crossing during the full monitor horizon, including after a benign variance change. The query rule is frozen to activation 0.025, urgency power 0.5 and budget taper power 1.0. The candidate was selected using the independent development seeds; this calibration block is not used to tune it.

## Error-control gate

There are four calibration cells. For each cell, compute the one-sided Clopper–Pearson upper limit at confidence `1 - 0.05/4 = 98.75%`. The calibration gate passes only if every simultaneous upper limit is at most 0.05 and all implementation invariants pass: 1,000 unique streams per cell, all expected method/scenario keys present, no cap violations, no unresolved labels, and registered events equal monitor updates. The finite Monte Carlo result checks this implementation and registered generator; it does not replace the e-process proof or justify outcomes outside the stated filtration and assumptions.

Only after the gate passes may a separate protocol specify a disjoint boundary-harm confirmation. Calibration itself reports no power claim and does not retune query or monitor parameters. No figures are planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-calibrate --seeds 1000 --seed-offset 20280000 --device cuda --output-dir outputs/delayed_evidence_directed_ppi_calibration_1000`
