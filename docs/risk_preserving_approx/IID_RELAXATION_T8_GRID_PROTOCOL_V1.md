# IID relaxation paired T=8 synthetic grid follow-up

Registered 2026-10-29 before execution. Evaluate the IID-relaxation, exact-null
verification and repair pipeline on the five cells not yet evaluated by this
candidate. The sixth cell `(transition=1/10, emissions=(1/50,49/50))` is excluded
because it has its own registered run in
`iid_relaxation_certified_pipeline_v1.json`. No seeds are used; this is a fixed
finite-model synthetic family, not confirmation evidence. No real rows, CRSP or
reserved holdouts are accessed.

## Frozen cells and method

Use the existing six-cell T=8, B=4, delay-2 calendar comparison grid, with
`alpha=1/10`, query fee `1/100`, switching fee `1/10`, symmetric transition in
`{1/10,1/4,9/20}`, emissions in `{(1/10,9/10),(1/50,49/50)}`, and prior `1/2`.
For each of the five unrun cells, build the alternative continuation and learner
tree only; optimize alternative cost with one IID fair-label first-promotion risk
row. Use HiGHS at `1e-9` primal/dual tolerances and a 60-second time limit. Verify
the rationalized dual exactly with reduced-cost correction. Recompute policy cost,
IID risk and full history-adaptive causal-null risk independently; if needed, repair
by an upfront mixture with the never-promote policy and certify again.

## Frozen comparisons and reporting

Compare to the already recorded robust decomposed policy, best exhaustive fixed
calendar, finite calendar portfolio where available, m=3 cap, and e-process gate
baselines in `t8_b4_calendar_v1.json` and
`t8_b4_calendar_portfolio_v1.json`. Do not rerun any baseline. Report per-cell
candidate cost/risk, rational dual lower bound and gap, repair activation, solver
and end-to-end timings by phase, learner variables/equalities, builder nodes,
reference variables/nodes/time, and exact differences from the reference and best
calendar. Preserve failures and all phase timings.

This screen supports the candidate only if every returned policy is exactly
alpha-safe, all dual certificates verify, and it matches or improves the
registered calendar baseline on at least one of the two low-persistence cells
where the robust reference improves on calendars. Resource advantage is reported
only from matched end-to-end measurements. No novelty, general theorem, G3 pass or
real-data eligibility is implied; relaxation/repair remains a standard method
unless the equivalence audit finds a distinct guarantee.
