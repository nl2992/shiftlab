# Uniform-start restart mixture dormant-mass audit (2026-11-07)

## Question and status

Does `scripts/sota_sprint/fam_p.py::UniformStartSUI` retain the claimed nonnegative
supermartingale/e-process property when it adds each start-time component only after the start is
reached? The audit compares the implementation as written with the same weighted components plus
the not-yet-started mixture mass carried at value 1. This is a software/guarantee-fidelity diagnostic,
not a method proposal or an evaluation on research holdouts.

## Frozen diagnostic

- Nulls: iid Bernoulli(0.5), and stationary symmetric first-order Markov Bernoulli with transition
  `P(Z_t=1 | Z_{t-1}) = 0.8 Z_{t-1} + 0.1` (correlation 0.8). Both are within the stated free-rho
  Markov null family.
- Streams: 5,000 independent streams per null, 200 observed labels per stream, NumPy PCG64,
  seed base `2026110707` plus the null index.
- Evidence settings: `n_starts=20`, `stride=10`, `n_rho=40`, `n_p=20`, the repository's default
  alternative prior, and threshold `1/0.05=20`.
- Paired policies: the checked-in implementation; a diagnostic augmented value which at every step
  adds the remaining fixed mixture weight at e-value 1. No thresholds or parameters are tuned.
- Outcomes: streamwise maximum e-value, ever-crossed indicator, final e-value, and paired any-cross
  difference. Report Wilson intervals and exact artifact hashes.

## Interpretation rule

This diagnostic can flag a fidelity defect if the as-written implementation materially violates its
nominal any-cross bound in either correctly specified null. A non-rejection does not prove a
guarantee. The augmented process is a diagnostic construction; its formal validity still needs a
proof against the exact MarkovSUI component definition. All earlier registered records remain
unchanged. If a defect is found, affected claims must be quarantined and future comparisons rerun
under a prospectively corrected implementation; prior outcomes must not be silently rewritten.

## Reproduction

`python research/scoped_method/pilots/uniform_restart_dormant_mass_audit_20261107/run_audit.py`
