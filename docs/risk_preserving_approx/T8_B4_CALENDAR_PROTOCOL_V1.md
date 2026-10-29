# T=8, B=4, delay-2 adaptive reservation comparison

Registered 2026-10-29 before execution. This is a six-cell deterministic
synthetic development grid over the previously exposed HMM transition/emission
family, with a new query budget `B=4`; it is not independent confirmation or a
new seed block.

For each of the six configurations in `cap_calendar_synthetic_v1.json`, use
`T=8`, `B=4`, `d=2`, `alpha=1/10`, query fee `1/100`, switch fee `1/10`, prior
`1/2`, and the recorded symmetric transition and emission pair. Compare the full
first-promotion decomposed reference, the pre-promotion cap `m=3` with the full
original budget available after promotion, exact-risk-calibrated stake-one
e-process planners with thresholds 4, 8 and 16, and all 57 subsets of
`{1,...,6}` of size at most four. The calendar policy may adaptively skip its
available dates; select the lowest exact-risk-safe recovered cost using the
known model.

For each recovered policy independently reconstruct exact expected metrics and
full-history causal-null risk. Record every cell and every calendar, including
failures, in a non-overwriting JSON artifact with protocol/source hashes, solver
residuals, costs, risks, runtime and state/sequence/node counts. Apply the same
never-promote root repair when required. This is a development comparison, not
a novelty claim. The decomposed reference remains a numerical LP solution unless
an independent rational certificate applies. No real observations, holdouts or
new seeds are accessed.
