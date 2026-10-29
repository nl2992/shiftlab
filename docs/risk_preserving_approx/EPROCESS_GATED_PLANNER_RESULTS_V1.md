# E-process-gated HMM planner comparison

Executed on 2026-10-29 under the frozen protocol in
`EPROCESS_GATED_PLANNER_PROTOCOL_V1.md`. The six cells reuse the exposed
development family; this is neither new-seed confirmation nor real-data evidence.
Exact fractions and provenance are in `eprocess_gated_planner_synthetic_v1.json`.

## Verification

The implementation uses a product state containing the exact alternative belief,
pending labels, remaining query rights, time, and e-process wealth. For each
released label it multiplies wealth by `1 + (2Y-1)` and permits promotion only
after reaching four. A first-promotion event is therefore contained in the
wealth-crossing event. Under any causal null whose conditional queried-label
mean is at most one half given its full past, each predictable query update has
conditional expectation at most one; skipped rounds leave wealth unchanged.
Ville's inequality gives raw risk at most `1/4`. This is a PROVED argument under
the stated conditional-mean null and predictable-query assumptions. Here the
fixed delay preserves release order and each event is queried at most once.

All six exact causal-null evaluations were at most `1/4`; four were exactly
`1/4`, and two candidate policies never promoted. The rational root activation
`min(1, alpha/R)` produced risk at most `1/10` in every cell. Independent
full-history expected metrics exactly equaled the weighted raw/safe branch
metrics. The hard query cap is inherited by both branches. Focused test:
`uv run --no-sync pytest -q tests/test_eprocess_gated_planner.py` (1 passed).

The dynamic program stored 123 pre-promotion value states, 171 decision states,
and 24 post-promotion continuation states in each registered cell. Solve time
was approximately 0.012–0.051 seconds in this environment; no peak-memory
measurement was taken. These small-cell counts do not establish a general
complexity advantage.

## Matched comparison

All six calibrated costs match the unrestricted decomposed oracle in three
cells; in the other three the excess costs are respectively
`113637/7812500`, `199508757/4882812500`, and `1/6250`. The best calendar is
equal to the oracle in all six cells. Consequently, the gated planner ties the
strongest calendar baseline in three cells and loses in three; it beats it in
none. No statistical or methodological advantage is established.

## Decision

Retain this as the required source-matched sequential-test plus economic-planner
baseline. It verifies the implementation and a familiar Ville-risk composition,
but it does not advance the novelty claim. The fixed `lambda=1`, threshold-four
rule is conservative and may be economically suboptimal; adapting the test or
optimizing it jointly would require a new preregistered method and source-level
equivalence audit. No real outcomes or holdouts were accessed.
