# T=8, delay-2 cap versus full calendar family

Registered 2026-10-29 before execution. This is a bounded synthetic development
grid over six previously exposed HMM parameterizations, extended to T=8 and
delay two; it is not an independent seed or confirmation study.

For each of the six cells in `cap_calendar_synthetic_v1.json`, reuse its
symmetric transition and emission pair, prior 1/2, with `T=8`, `B=3`, `d=2`,
`alpha=1/10`, query fee `1/100`, switch fee `1/10`, and the existing 200,000
builder-node / 60-second LP limits. Compare the decomposed reference, the
pre-promotion cap `m=2` (full original post-promotion rights retained), fixed
stake-one e-process gates at thresholds 4 and 8 (each root-calibrated using the
exact full-history null evaluator), and all 42 calendar subsets of
`{1,...,6}` of size at most three. Select the lowest recovered exact-risk-safe
calendar cost per cell using the known model.

Independently reconstruct exact expected metrics and causal-null risk. Preserve
all failures and rows in a new non-overwriting output with code, protocol and
input hashes, exact cost/risk, node/sequence/state counts, numerical residuals
and timings. This is a model-known development comparison; no new seeds, real
observations or holdouts are accessed. The T=8 full sequence-form oracle did not
complete in prior registered work, so the decomposed reference's recovered
policy is not an independent full-optimum certificate. Do not claim T=8
optimality, a general value guarantee or novelty from this grid.
