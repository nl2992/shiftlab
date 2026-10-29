# Exact LP bracket for the registered delayed-reversal cell

**Status:** exact rational certificate for one finite reference instance; no novel method claim.

## Result

For the registered `T=6, B=3, d=1, alpha=1/10` recurrent-HMM cell, the optimum of the
full-history sequence-form causal-risk LP lies in

```text
2.881768749955 <= optimum <= 461083/160000 = 2.88176875,
```

so the certified bracket is at most `4.5e-11`. The lower endpoint is a decimal rational
rounded down after an exact dual calculation and exact residual correction. The upper endpoint
is the exact expected cost of a feasible two-mode controller. It has causal-null promotion risk
`1/10`, expected decision cost `1141923/400000`, query cost `1481/200000`, switching cost
`3129/160000`, and pathwise query use at most three.

## What was certified

The LP has nonnegative learner realization variables and free adversary-flow dual variables.
The source accumulates alternative costs using floating point, so this checker rebuilds the
terminal-sequence objective coefficients from the same HMM tree with `Fraction` arithmetic.
It uses HiGHS only to propose LP dual multipliers. The proposed multipliers are rationalized;
the checker then verifies the inequality-dual signs, every equality on free columns, and every
inequality on nonnegative learner columns with exact arithmetic. Any positive residual on a
learner column is charged against its realization weight, which is at most one by sequence-flow
conservation. A rational upper bound on the total residual gives the certified lower endpoint.
The fixed controller independently supplies the exact feasible upper endpoint.

The complete rational dual vectors and hashes are in
`outputs/switching_reversal_lp_certificate_v1/results.json`. Reproduce by running
`PYTHONPATH=src python scripts/certify_switching_reversal_lp_bound.py`. Then independently check
the saved certificate, without invoking an optimizer, with
`PYTHONPATH=src;. python scripts/verify_switching_reversal_lp_certificate.py`. The verifier checks
every dual constraint and the feasible upper policy from the saved rational vectors.

## Interpretation

This upgrades the registered instance's sequence-form LP value from a numerical proposal to a
near-exactly certified optimum. It makes that cell a defensible small-instance oracle for later
matched comparisons. It does not establish a scalable solution, generalization across instances,
a new acquisition rule, or an ICML-level methodological contribution. The controller was
identified from the same cell's recovered policy; the upper-bound role is mathematical
feasibility, not independent efficacy evidence.
