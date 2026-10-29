# Rational dual follow-up for the asymmetric query-timing screen

**Registered:** 2026-10-29 before certificate execution. This checks only the four already-run
cells in `switching_asymmetric_timing_protocol_v1.md`; it is not a new parameter search.

For each unrestricted full-history LP, rebuild the alternative cost coefficients exactly with
`Fraction` arithmetic, then use HiGHS only to propose dual inequality/equality multipliers. Recover
rational multipliers with denominator at most `10^9`. Verify all dual signs, equality on every free
null-realization column, and all learner-sequence inequalities exactly. Since each realization
weight lies in `[0,1]`, charge the sum of positive rationalized column residuals against the upper
bounds to obtain a rigorous dual lower bound. Independently recover and forward-evaluate the solver
policy; verify its causal-null risk and compare its exact feasible cost with the selected fixed-
calendar feasible policy from the saved screen.

If an exact dual certificate and the exact feasible upper coincide in a cell, this proves that the
selected fixed-calendar policy is optimal over the full adaptive class for that cell. If rational
dual recovery fails or the bracket remains open, report the remaining width; do not claim equality.
No optimizer limit is to be raised. Reproduce the proposed multipliers with
`python scripts/certify_switching_asymmetric_timing.py`, then verify the saved witnesses without
optimization with `python scripts/verify_switching_asymmetric_timing_certificates.py`.

## Result

The four exact brackets passed the optimizer-free verifier, including source hashes, null
realization-flow constraints, every free-column equality, learner-sequence dual inequalities,
the residual correction, and independent forward evaluation of each saved policy. The verifier
also checks that each feasible policy matches the corresponding best fixed-calendar witness in the
registered screen. The full adaptive optimum is therefore within the following exact widths of
those fixed-calendar policies:

| `(p01,p10,prior1)` | fixed-calendar feasible cost | exact bracket width | null risk |
|---|---:|---:|---:|
| `(1/10,3/10,1/2)` | `616173/312500` | `1/10^12` | `0` |
| `(3/10,1/10,1/2)` | `1441738869/390625000` | `286601917/286722237000000000000` | `1/10` |
| `(1/10,3/10,4/5)` | `3684153/1562500` | `1/10^12` | `0` |
| `(3/10,1/10,1/5)` | `6655587789/1953125000` | `663207369/662982601000000000000` | `1/10` |

Thus there is no economically meaningful query-opportunity timing gain in these four cells: the
best registered fixed calendars are optimal over the unrestricted adaptive class to a certified
width below `1.001e-12`. This is a finite-instance no-go for this candidate and setup, not a
general theorem over recurrent HMMs or evidence for a new method. The full certificate arrays and
source digests are emitted in the ignored `outputs/switching_asymmetric_timing_v1/` directory.
