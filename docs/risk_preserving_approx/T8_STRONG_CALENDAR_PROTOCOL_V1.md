# T=8 pre-promotion cap versus full calendar family

Registered 2026-10-29 before execution. This is a one-cell deterministic
synthetic development comparison using the previously exposed fixed-budget HMM;
it is not independent confirmation, a new seed or a novelty claim.

Use `T=8`, `B=3`, `d=1`, `alpha=1/10`, query cost `1/100`, switch cost `1/10`,
symmetric transitions `1/4`, emissions `(1/20,19/20)`, and prior `1/2`, matching
`PREPROMOTION_CAP_PROTOCOL_V1.md`. Compare the decomposed reference, the
pre-promotion query cap `m=2` with all original post-promotion budget rights, the
fixed e-process gate (stake 1, threshold 4), the wealth-maximal gate (stake 1,
threshold `2^B=8`) with exact root-risk calibration, and every calendar subset of
`{1,...,7}` of size at most three (64 calendars). All policies receive the same
hard pathwise cap and delay semantics. Independently reconstruct exact expected
metrics and full-history causal-null risk for every recovered policy, applying
the registered never-promote root repair if needed. Record all rows, numerical
LP residuals, exact risk/cost, state/sequence/node counts, runtime and source
hashes in a new non-overwriting output.

The full sequence-form reference is known not to finish under its registered
node limit at T=8. The decomposed solver's recovered policy is a comparator, not
an independent full-oracle optimality certificate. No T=8 optimality or general
approximation claim may be inferred from it. No new seeds, real data or holdouts
are accessed.
