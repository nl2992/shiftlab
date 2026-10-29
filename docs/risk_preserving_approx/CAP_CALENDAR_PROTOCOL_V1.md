# Strong calendar-opportunity comparison: development protocol v1

Registered before execution on 2026-10-29, starting commit d336e59. Reuse the
six previously exposed HMM cells and T=6, B=3, d=2, alpha=1/10, c=1/100,
k=1/10 contract in `CAP_EPISODE_SYNTHETIC_PROTOCOL_V1.md`. Compare the m=2
pre-promotion capped planner against the *stronger* existing
`CalendarOpportunityGame` (`scripts/decompose_switching_calendar_gap.py`).
This baseline may adaptively skip each of its allowed query times and optimize
randomized promotion, rollback, re-promotion and query decisions under the same
causal null and total budget. Enumerate all 15 calendar subsets of {1,2,3,4}
with at most B slots; choose the lowest exact-risk-calibrated recovered cost
per known model, as in the original predeclared study. Also compute the
unrestricted first-promotion oracle. The selection uses each evaluated model and
is a generous development comparator, not a deployable learned calendar.

For each cell record the 15 calendars, objective, exact-risk-calibrated cost,
risk, actual selected calendar, node and learner/null sequence counts, solver
residuals, timings, and capped/full results; report calendar minus cap, cap
minus full. Preserve all failures. Independently re-evaluate risk and costs
using each policy's own full-history recursion and require calibrated risk at
most alpha. LP optima remain numerical; comparisons concern recovered feasible
policies and not certified class optima. Record source hashes and retain original
outputs. This is a structural synthetic development diagnostic, not independent
confirmation, a novel method claim, real-data efficacy, or a substitute for
robust-FSC and source-matched sequential-test competitors. No seeds or real data.
