# Strong calendar screens: T=7 and T=8

Executed on 2026-10-29 under the frozen per-cell protocols
`T7_STRONG_CALENDAR_PROTOCOL_V1.md`, `T8_STRONG_CALENDAR_PROTOCOL_V1.md`, and
`T8_DELAY2_CALENDAR_PROTOCOL_V1.md`. These are deterministic known-HMM
development comparisons on already exposed transition/emission families, not
new-seed confirmation or real-data evidence. The cell-level rational metrics,
all calendar rows and source hashes are in the linked JSON artifacts below.

## T=7, delay 1

All 42 calendars completed with no failures. The best calendar is `[1,2,3]` and
has recovered exact cost `10788127/3200000`, the same as the full decomposed
reference upper policy. The independently checked full-oracle bracket is
`3.371289687498436... <= V* <= 10788127/3200000`, with width below
`1.57e-12`. The `m=2` pre-promotion cap costs `1349103/400000`, exactly
`4697/3200000` above the calendar/full upper policy; its certified distance
above the full-oracle lower bound is that difference plus at most the oracle
bracket width. The threshold-4 e-process planner recovers the same cost as the
cap. It has exact null risk `1/4` before root activation and `1/10` after
activation `2/5`. No candidate beats the best calendar.

Artifact: `t7_strong_calendar_v1.json`; the registered exact certificate was
reverified with `uv run --no-sync python
scripts/research_risk_approx/verify_full_t7_certificate.py`.

## T=8, delay 1

All 64 calendars completed with no failures. The best calendar is `[1,2,5]`.
The cap, full decomposed reference and threshold-4 e-process policy all recover
cost `24735833/6400000` and exact calibrated null risk `1/10`. The cap uses 1,290
builder nodes and about `0.506s`, against 5,700 nodes and `1.550s` for the full
decomposed reference in this single run. A subsequent exact rational dual
certificate brackets the original optimum within `4.7869475491e-12` and verifies
that the `m=2` cap policy has the same cost and risk; see
`FULL_T8_DECOMPOSED_CERT_RESULTS_V1.md`. This certificate uses the proved
first-promotion decomposition and exact decomposed LP, not a completed generic
full-sequence builder run. Threshold 8 is worse by `551/640000`. No candidate
beats the best calendar in economic cost.

Artifact: `t8_strong_calendar_v1.json`. The full generic sequence-form builder
still does not complete under its registered node limit; the decomposed-LP
certificate supplies the exact bracket through the proved equivalent formulation.

## T=8, delay 2: six HMM cells

All six cells and all 42 calendars per cell completed. The best calendar matched
the decomposed reference's recovered cost in every cell. The `m=2` cap lost to
the best calendar in four informative cells and tied in the two cells where the
reference selected no queries. Threshold-4 e-process gates tied the best
calendar in the two `transition=1/4` informative cells but lost in the two
`transition=1/10` cells; threshold-8 gates tied in the two `transition=1/10`
cells and lost in the two informative `transition=1/4` cells. All methods tied
the no-query calendar in the two `transition=9/20` cells. No candidate strictly
beat the calendar baseline in any cell. Exact table and all 252 calendar rows:
`t8_delay2_calendar_deduplicated_v1.json`.

The first raw run artifact, `t8_delay2_calendar_v1.json`, is deliberately
preserved. Its runner appended the same mutable cell record once per calendar,
so it serialized each final cell 42 times. Every duplicate group was verified
identical and complete before generating the deduplicated artifact; the exact
executed runner source is preserved in
`t8_delay2_calendar_executed_source_v1.txt`, and its recorded SHA-256 matches.
The tracked runner was lint-fixed after execution; the corrected output is a
deduplication of the verified raw results, not a rerun.

## Research decision

These screens strengthen the computational case for the exact pre-promotion
cap on one T=8 delay-1 cell, but they falsify an economic-win claim against the
strong oracle-aware calendar family on all tested cells. They do not pass the
method novelty gate: the cap is a standard restricted-policy/budget split, and
the e-process planner is a standard sequential-test plus HMM-planner composition.
The six-cell T=8 delay-2 grid provides no strict calendar win. Per the upstream
G1–G3 gates, do not open the CRSP replay yet: no algorithm has passed the
source-level novelty and matched-baseline synthetic efficacy gates. Continue
with a theorem-level candidate or make a documented stop/reformulation decision;
do not turn these ties or compute reductions into an economic superiority
claim.
