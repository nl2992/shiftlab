# Candidate D adversarial gadget toy: result and limits

**Date:** 2026-10-29. **Status:** corrected v2 extraction check passed; no ShiftLab pilot.

The frozen matching-pennies OS-POSG has exact security value zero. The first fixture attempt failed
before solver initialization because the declared observation/transition counts did not match the
file contents. Its error and log are retained under
`.aris/runs/candidate_d_adversarial_toy/`; it is not a solver result. The corrected isolated v2
fixture and run passed the registered checks in
`CANDIDATE_D_ADVERSARIAL_GADGET_PROTOCOL_V1.md`.

HSVI returned interval `[-8.844670557062173e-8, 8.844670554711804e-8]`, width
`1.7689341111773978e-7`. The extracted learner strategy chooses each row with probability `0.5`;
its payoff against each pure opponent column is exactly zero, so its independently evaluated
security value is zero. The gadget residual is zero. The run took 5.303 seconds and required no
HSVI exploration beyond its presolve. Raw log and JSON are under the ignored
`.aris/runs/candidate_d_gadget_toy_v2/`.

SHA-256 values:

- v2 adapter script: `e11e1fbf4761ddb21e3f1458c8abec359606f9dbebb6fe4b18e8071afb6351d6`
- v2 game fixture: `89c3a01939449e07587766202ab52130fecee4b170cc7eb29da6fb720924fe31`
- protocol: `32815970e084e6411e11e8c204d85c4c3addb91e7319c870d19bc5fb9516b96d`
- JSON result: `9c7c688758c3ae6b02c355bb056e4ec8d6789bf4c3b4ff7c5cfc2b0fa4d2b68a`
- upstream implementation: `HSVIforOSPOSGs.jl` commit `05eaf101b38c1c9b301a1a5fb298bfe8b97f757d`

This check validates root action randomization against a one-step adversarial choice. It does not
test opponent history-dependent strategies, multi-stage gadget recursion under adversarial
observations, ShiftLab's request/release chronology, or exact two-law risk/cost verification. The
candidate remains comparator plumbing only; no novelty, resource advantage, or ShiftLab pilot gate
is established.

