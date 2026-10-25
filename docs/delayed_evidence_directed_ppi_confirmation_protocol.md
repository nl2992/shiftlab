# Delayed evidence-directed PPI: disjoint harm confirmation protocol

**Status:** frozen before calibration outcomes are opened. The confirmation is conditional on the frozen null-calibration gate passing. It uses seeds 20282000–20282999, disjoint from both development seeds 20272000–20272029 and calibration seeds 20280000–20280999. No query parameter or monitor threshold may be changed after calibration.

## Candidate and comparator

Compare `evidence_a0p025_p0p5_eventwise` with `uniform_eventwise` on 1,000 paired independent boundary-harm streams. The candidate rule, source-only proxy, e-process stakes, predictable support bound, delay process, query-uniform pairing, and 480-label cap are exactly those used in the development grid and independent null calibration. Harm onset remains event 1,200 of 2,400; the conditional mean shifts from `0.35 X_t` to `0.35 X_t+0.20` at onset, with materiality margin `epsilon=0.05`. Queries have independent delays uniform on `{0,...,12}`.

## Primary endpoint and retention gate

The primary endpoint is the paired difference in the probability of an alarm at or after the registered harm onset, with an alarm before onset counted as a non-detection. Compare the candidate and uniform arms by the one-sided exact McNemar test on discordant paired streams, at level 0.05. Retain the candidate for further study only if the one-sided p-value is below 0.05, the paired bootstrap 95% lower limit for the detection-rate difference is above zero, the candidate's mean label count is no greater than uniform's, and every cap/prefix integrity check passes. Otherwise report the result and do not claim a detection advantage.

Secondary outcomes are pre-onset alarms, total alarms, labels queried, events processed, event-time and arrival-time delay among post-onset detections, remaining budget, and paired label-count difference with a descriptive seed bootstrap interval. These outcomes do not replace the primary test. Because only one frozen candidate is compared with uniform, no grid-wide multiplicity correction is applied to this independent confirmation; development comparisons remain exploratory.

## Validity scope

This is a positive-signal power comparison, not a type-I calibration. Any monitoring validity statement still depends on the separate calibration and the event-history conditional-mean null, source-frozen proxy, predictable query probability and eventwise support bound, conditional query randomization, frozen policy pair, correct labels, and event-prefix update rule. The study does not cover serial dependence, non-random missingness, policy-induced outcomes, real decision costs, or general optimality. No novelty claim follows from confirming this registered combination of established components. No figure is planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-confirm --seeds 1000 --seed-offset 20282000 --device cuda --output-dir outputs/delayed_evidence_directed_ppi_confirmation_1000`
