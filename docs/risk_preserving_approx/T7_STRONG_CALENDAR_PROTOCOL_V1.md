# T=7 pre-promotion cap versus full calendar family

Registered 2026-10-29 at starting revision `b1aadb2`, before this comparison.
This is a one-cell deterministic synthetic development comparison using an
already exposed HMM, not independent confirmation, a seed allocation or a
novelty claim.

## Fixed cell and methods

Use `T=7`, `B=3`, `d=1`, `alpha=1/10`, query cost `1/100`, switch cost `1/10`,
symmetric transitions `1/4`, emissions `(1/20,19/20)`, and prior `1/2`, exactly
as in `PREPROMOTION_CAP_PROTOCOL_V1.md` and the verified
`full_t7_certificate_v1.json`. Compare:

1. The exact first-promotion decomposed LP (full reference).
2. The pre-promotion acquisition cap `m=2`, with the full original budget after
   first promotion.
3. The best of every fixed calendar subset of `{1,2,3,4,5,6}` of size at most
   three (42 calendars), with adaptive skipping and the same causal-null LP.
4. The registered fixed e-process planner with stake `1`, wealth threshold `4`,
   and exact root-risk calibration.

All policy metrics are reconstructed by exact-rational forward evaluation and
all worst-case null risks by the full-history causal recursion. Calendar choice
is selected using the known model, making it an intentionally strong oracle-aware
development comparator. Verify the saved T=7 rational full-oracle certificate
with its existing optimizer-free verifier; do not alter that certificate. Record
all calendar rows, candidate costs and risks, LP residuals, node/sequence counts,
DP states, timings, code/protocol hashes and failures. No output may be
overwritten. No new seeds, real observations or holdouts are used.

## Interpretation

This comparison tests whether the m=2 cap is useful against the stronger
calendar family on the certified T=7 cell. It does not establish new asymptotic
complexity, generalization, real-data efficacy or novelty. A failed or losing
result remains in the output and ledger.
