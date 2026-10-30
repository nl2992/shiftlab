# E-process maximum-attainable-wealth boundary screen

**Registered:** 2026-10-29 before the threshold-eight run. This is a bounded
development screen on the six exposed T=6 synthetic cells, not confirmation and
not a novelty claim.

## Hypothesis

For `T=6`, `B=3`, `d=2`, `alpha=1/10`, the existing stake-one e-process planner
with promotion threshold `8=2^B` may improve economic cost over the fixed
threshold-four screen. Under the causal null, each released-label update
`M <- M * (1 + (2Y-1))` is a nonnegative supermartingale increment when the
conditional label mean is at most one half. Crossing eight therefore has
Ville risk bound `1/8`; exact robust-null verification and a root mixture with
never-promote behavior calibrate the returned policy to alpha.

## Frozen design

Use exactly the six transition/emission cells in
`CAP_CALENDAR_PROTOCOL_V1.md`: symmetric transitions in `{1/10,1/4,9/20}` and
emission pairs `(1/10,9/10)` or `(1/50,49/50)`, prior state probability `1/2`.
Keep query cost `1/100`, switching cost `1/10`, fixed stake `1`, and set the
single tested threshold to `8`. Compare to the saved threshold-four e-process
results, the exact decomposed oracle, and the best registered calendar for each
cell. Do not add another threshold or tune after results.

For each cell, independently evaluate exact alternative cost and full-history
causal-null first-promotion risk, verify raw risk at most `1/8`, calibrate by
`min(1,alpha/R)`, and verify the resulting mixture's risk and expected metrics.
Record state/cache counts, solve time, cost gaps, query use and source hashes.
Preserve output at `docs/risk_preserving_approx/eprocess_threshold8_t6_v1.json`;
refuse to overwrite it.

## Decision rule and scope

This screen is useful only if the threshold-eight policies are exactly
risk-safe and reduce cost relative to threshold four or the strongest calendar
in at least one nondegenerate cell without a larger end-to-end compute burden.
Any pass justifies a theorem/prior-art audit of optimizing e-process boundary
and betting controls; it does not establish novelty or the project objective.
If it does not improve, stop threshold-only variations and formulate a
mathematically distinct candidate. No new seeds, real data, reserved holdouts,
T=8/T=10 runs, or overnight jobs are in scope.
