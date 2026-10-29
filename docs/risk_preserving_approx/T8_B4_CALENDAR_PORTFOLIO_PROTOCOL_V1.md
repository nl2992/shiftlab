# Calendar-strategy portfolio: exact risk-frontier diagnostic

Registered 2026-10-29 before execution. This is a post-screen development
diagnostic on the largest adaptive-versus-calendar gap from the registered
T=8,B=4,d=2 grid; selection of this cell is exploratory and is not independent
confirmation.

Use `T=8`, `B=4`, `d=2`, `alpha=1/10`, fees `1/100` and `1/10`, symmetric
transition `1/10`, emissions `(1/50,49/50)`, and prior `1/2`. For each of the 57
calendar subsets of `{1,...,6}` with at most four dates, solve the calendar
restricted robust LP at working risk levels
`{1/40,1/20,1/10,1/5,2/5,1}`. Independently reconstruct every recovered
policy's exact alternative cost and full-history causal-null risk. Add the
never-query/never-promote strategy (cost 4, risk 0).

Construct a root portfolio minimizing expected alternative cost subject to the
conservative risk constraint `sum_i w_i R_i <= 1/10`, where `R_i` is each
component's exact worst-case causal-null risk. Since the master has one risk
inequality and one simplex equality, enumerate all single policies and all
two-policy mixtures exactly; an optimal extreme point needs at most two
components. Convert the selected root lottery to a behavioral learner policy
with Bayes-updated component weights from its observed action history. Then
independently verify exact expected metrics, full-history causal-null risk,
pathwise budget and the weighted-branch metric identity. The weighted worst-risk
bound proves safety even if it is conservative.

Compare against the best single alpha-safe calendar and the unrestricted
decomposed reference from `t8_b4_calendar_v1.json`. Preserve every component,
exact mixture weight, and source/protocol hash in a new non-overwriting output.
This tests whether the fixed-calendar baseline omitted useful root mixtures; it
does not claim a new algorithm or inspect real data, seeds or holdouts.
