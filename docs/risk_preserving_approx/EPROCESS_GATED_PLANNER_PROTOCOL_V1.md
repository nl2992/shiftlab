# E-process-gated HMM planner: registered baseline comparison

Registered 2026-10-29 before implementation and execution. This is a
source-matched sequential-test plus economic-planner baseline, not a novelty claim.
It uses six previously exposed development HMM cells only; it allocates no seeds
and opens no real data or holdout.

## Fixed design

Use `T=6`, `B=3`, `d=2`, `alpha=1/10`, query fee `c=1/100`, and switch fee
`k=1/10`. Reuse the six transition/emission cells registered in
`CAP_CALENDAR_PROTOCOL_V1.md`: symmetric transition in `{1/10,1/4,9/20}` and
emission pairs `(1/10,9/10)` or `(1/50,49/50)`, with prior state probability
`1/2`.

Before first promotion, run a known-alternative HMM dynamic planner whose state
contains the exact posterior over current regime and pending queried outcomes,
remaining query rights, prior deployment, current time, and an e-process wealth.
For each released queried label `Y`, update `M <- M*(1 + (2Y-1))`, i.e. stake
`lambda=1`. Permit first promotion only once `M >= 4`. Continue to optimize query
timing and all economic continuation choices under the known HMM. After first
promotion, use the existing exact delayed-HMM continuation DP, including rollback
and re-promotion.

For every candidate policy, independently evaluate its exact full-history causal
null risk. Form an upfront root lottery between the candidate and never-query,
never-promote behavior, with candidate activation
`p=min(1,alpha/R)` where `R` is its exact robust-null risk. Thus the recovered
mixture is exactly alpha-safe even if the universal bound is conservative. Check
that the e-process argument also implies `R<=1/4`: for each predictable query,
`E[1+(2Y-1)|full past,query]<=1`; fixed release delay preserves queried-label
order, and any permitted promotion is contained in the event that the product
crosses 4, which Ville bounds by 1/4.

## Comparisons and measurements

Compare the calibrated recovered policy with (a) the full/decomposed recovered
oracle and (b) the best of all 15 adaptive-skip calendar planners saved by
`CAP_CALENDAR_PROTOCOL_V1.md`, at matched model, delay, query cap, costs, and risk.
Record raw and calibrated exact cost, exact causal-null risk, theoretical risk
bound, activation, expected and maximum queries, DP states/cache entries, build
and solve time, exact-reference and calendar gaps, and source hashes. Use exact
fractions for all recovered metrics. The oracle and calendar LP objectives remain
numerical unless their separate rational certificates apply. Report this as a
development baseline screen only; no independent confirmation is implied.

## Decision rule

The baseline passes implementation verification only if the returned controller
respects the hard cap and information filtration, its exact null risk is at most
`alpha`, its risk does not exceed the `1/4` crossing bound before activation, and
its expected cost matches an independent evaluation of the saved controller.
The experiment does not pass the research objective unless a later eligible
candidate establishes a defensible advantage against these baselines on synthetic
and pulled real data. Preserve all negative results and failed cells.
