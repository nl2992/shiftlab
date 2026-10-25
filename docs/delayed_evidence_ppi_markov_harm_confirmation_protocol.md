# Delayed evidence-directed PPI: Markov-scale harm confirmation protocol

**Status:** frozen before execution. This confirmation is conditional on the independent Markov-scale null calibration passing. It uses seeds 20292000–20292999, disjoint from the Markov null-calibration block 20290000–20290999 and all prior IID blocks.

## Candidate and generator

Compare `evidence_a0p025_p0p5_eventwise` with `uniform_eventwise` on 1,000 paired boundary-harm streams. Retain the 0.05 Markov regime-switch probability and amplitudes `{0.55,1.0}`. At every event, the sign is drawn independently conditional on the regime; before the onset it is fair, and after event 1,200 its positive probability is `0.5*(1+0.20/A_t)`, where `A_t` is the current regime amplitude. Therefore the event-history conditional mean is zero before onset and exactly `+0.20` after onset despite persistent variance. Outcomes remain within `[-1,1]`. Queries have independent delays uniform on 0–12.

The learner does not observe the regime. The source-only proxy, alpha 0.05, epsilon 0.05, propensity support `[0.05,0.80]`, evidence-urgency settings, 2,400-event horizon, 480-request hard cap, and event-prefix monitor are fixed to the already-confirmed IID method. Candidate and uniform arms share the target contexts/outcomes, query uniforms, delays, and seed within each pair. The calibration manifest must show a passing Markov-null gate and match the current Markov generator source hash before execution.

## Primary endpoint and retention gate

The primary endpoint is paired post-onset detection, with pre-onset alarms counted as misses. Test candidate-versus-uniform detection using a one-sided exact McNemar test at 0.05. Retain the candidate for further dependent-stream study only if the one-sided p-value is below 0.05, the paired bootstrap 95% lower bound for detection difference is above zero, candidate mean label use is no greater than uniform, and all cap/prefix checks pass. Otherwise record the result and stop the power claim for this generator. Report paired label use, processed events, pre-onset alarms, and event/arrival delay as secondary outcomes.

This is one frozen dependent-scale alternative and one candidate, so no grid-wide multiplicity correction applies to the independent confirmation. It does not test persistent outcome signs, informative delays, a drifting conditional null, or real-world costs. No novelty claim follows from this established query rule and e-process. No figure is planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-markov-confirm --seeds 1000 --seed-offset 20292000 --device cuda --calibration-manifest outputs/delayed_evidence_ppi_markov_calibration_1000/manifest.json --output-dir outputs/delayed_evidence_ppi_markov_confirmation_1000`
