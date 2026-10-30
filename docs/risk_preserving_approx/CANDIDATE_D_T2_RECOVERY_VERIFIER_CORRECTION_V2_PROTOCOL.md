# Candidate D T=2 recovery verifier correction v2

**Registered:** 2026-10-29, after preserving the v1 verifier failure. This
re-evaluates the already generated lambda-`1/100` controller and reuses the
already verified lambda-one controller. It does not rerun HSVI or change either
candidate policy.

## Frozen correction

The v1 verifier stored policy probabilities in the fixed order
`(incumbent,q0)`, `(incumbent,q1)`, `(challenger,q0)`, `(challenger,q1)`, but
indexed that vector by the position in a later budget-restricted legal-action
list. V2 must look up each `(deployment,query)` pair in the fixed action order
before evaluating the policy. Keep the original model, exact-rational metrics,
alpha `1/10`, scalarized LP checks and thresholds unchanged.

Run only the corrected exact verifier on the preserved lambda-`1/100` bundle,
then run the exact two-law constrained LP audit and the frozen two-policy
mixture calculation. Reuse the existing lambda-one policy verification and its
model/compile record without modification. Preserve v1's error log. If the
corrected metric still violates the scalarized LP lower bound, investigate the
policy/model mapping and do not issue a risk-bracket claim.

This correction cannot establish an empirical or theoretical advantage. No
extra multipliers, solver reruns, T=6 run, calendars, seeds, or real data are in
scope.
