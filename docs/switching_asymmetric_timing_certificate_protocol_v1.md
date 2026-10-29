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
No optimizer limit is to be raised. Reproduce with `python scripts/certify_switching_asymmetric_timing.py`.
