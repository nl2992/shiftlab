# Candidate D T=2 multiplier-recovery diagnostic results

**Protocols:** `CANDIDATE_D_T2_RECOVERY_PROTOCOL_V1.md` and its registered
verifier correction `CANDIDATE_D_T2_RECOVERY_VERIFIER_CORRECTION_V2_PROTOCOL.md`.
**Date:** 2026-10-29. **Status:** exact small-instance recovery works; Candidate D
is a no-go as a promising computational method under this test.

## Frozen policies and exact audit

The lambda-`1/100` HSVI solve returned interval
`[-0.9650000586,-0.9649999999]` (width `5.87e-8`) in `10.784s`; gadget
extraction took `0.171s`, produced six nodes and maximum residual
`9.99e-16`. Its independently verified policy has exact alternative cost
`24/25`, exact worst-case causal-null first-promotion risk `1/2`, and uses at
most one query. Its scalarized cost `193/200=0.965` equals the independent
sequence-LP optimum at that multiplier.

The pre-existing lambda-one controller is the no-query, never-promote policy:
cost `1`, risk `0`; its scalarized cost equals its exact scalarized optimum `1`.
The independently rebuilt exact constrained sequence-form LP at `alpha=1/10`
has objective and recovered cost `124/125=0.992`, recovered risk `1/10`,
39 flow nodes, 21 learner sequences, and 5 null sequences. Its alpha-constraint
dual gives `lambda_star=2/25=0.08` (numerical residuals below `6e-17`).

The endpoint risks bracket alpha and the exact LP dual lies in
`[1/100,1]`. Mixing the high-risk policy with weight `1/5` gives exact cost
`124/125` and a robust risk upper bound `1/10`, matching the exact constrained
oracle. This is a successful finite-instance recovery check. The stated
recovery theorem's multiplier-width term is nevertheless `delta=99/100`; with
zero endpoint scalarized gaps, its bound is `0.99`, far too loose to certify a
useful cost approximation. The observed exact equality relies on this small
instance's oracle audit and is not a general guarantee.

## Failed verifier preserved

The first v1 verification script used indices from a budget-restricted choice
list to read a fixed four-action probability vector. It reported impossible
scalarized cost `71/100`, below the LP optimum `193/200`. The failure was
reproduced and retained in
`.aris/runs/candidate_d_t2_recovery_lambda001/verifier_failure_v1.log`.
Corrected verifier v3 maps actions by `(deployment, query)` and gives the exact
metrics above. Neither HSVI nor extraction was rerun to obtain the correction.

## End-to-end computation and decision

Generating the pair requires `10.955s` for the lambda-`1/100` solve plus
extraction and `17.137s` for the already completed lambda-one solve plus
extraction: `28.092s` total before compilation, policy verification and oracle
bookkeeping. The exact constrained sequence-form LP, including game build,
completed in `0.00538s` on the same host. Peak memory was not measured, but the
wall-time difference already rules out a compute win on this registered
instance. The method ties the exact economic baseline and improves the trivial
never-promote policy by `0.008`, but does not beat the strongest exact baseline.

Candidate D's HSVI, gadget extraction, root mixture and exact causal-null
verification are established components; no novelty delta is identified. The
two-point multiplier interval also leaves a vacuous practical value bound. Stop
Candidate D as the lead algorithm. Preserve it as a correctness/plumbing
baseline and continue the mission with a new policy-side or implicit-search
candidate, requiring a nonvacuous joint cost/risk theorem before coding. No
real-data or holdout evaluation is authorized because G1–G3 have not passed.

The run bundles are ignored under `.aris/runs/candidate_d_t2_extraction_v1/`
and `.aris/runs/candidate_d_t2_recovery_lambda001/`. Key lambda-`1/100`
SHA-256 values:

- model: `e05c37da73c9ae27f081e84e0ef43c58a22101f499ea8904feb813a520bfae02`
- partition metadata: `53e8ff3bcffa227822464fd66a642fbf5581f891de7c385278cbeece08c113b5`
- HSVI/extraction log: `8e6585d1552b22ecc1e64c91bf1c1249bb9882cd289c188cf8290b1233e6c407`
- controller: `2db6042fb3c7a08bdf64781deb0389625a392a143c58eeb7802925df15be7d37`
- v1 failed verifier log: `b43341e2cd0eddd93664afee945e9d828d9ddba1e5c29da1e7be959f63877b44`
- corrected exact policy verification: `a095999e447967359e07499013ac62fbf398b6c9aef3b6b5aff139646f82655a`
- exact constrained recovery audit: `031cd9a96fa9efc7737f1e1f94f283a4760e211e7b8cdc0b31dbade695885bd3`
