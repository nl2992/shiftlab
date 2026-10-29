# Translating DAL to paired, delayed and budgeted model decisions

2026-10-28. **Status:** theorem-transfer screen and baseline protocol; not a new algorithm or a
proved regret transfer.

## Contract-matched adapter

For two frozen models, define the queried paired difference
`Z_t = loss_t(0)-loss_t(1) in [-1,1]`. A single common-outcome query observes this scalar
regardless of which model is deployed. DAL's action-forcing exploration is therefore replaced by
a deterministic query calendar. For `1<=B<=T`, set `L=ceil(T/B)` and request labels at
`q_j=1+(j-1)L<=T`; the total is `q=ceil(T/L)<=B` on every path. Each label is released at
`q_j+d` with fixed known delay `d` and updates monitors only when available.

Run a scalar, directional change detector on the queried `Z` history. A change detector that
needs `m_D` pre-change and `ell_D` post-change queried samples has a conservative calendar-time
window of at most `(m_D+ell_D+1)L+d`; the `+L` covers phase relative to the query calendar and
`d` covers the last label release. Thus DAL's sample-count separation condition becomes a
calendar dwell-time condition on this order. This is the direct cost of replacing forced
observations each cycle with a total-query schedule. Changes that alter the distribution but not
the mean of `Z` need not be detected for choosing between these two fixed models.

Use the delayed e-process composition in `switching_safe_composition_boundary_v1.md` as a
separate promotion-validity gate. Under the full-history conditional null
`E[Z_t|F_(t-1),Q_t=1]<=0`, predictable queries and fixed order-preserving delay preserve
`P(any promotion)<=alpha`. Require current-window evidence from the directional change monitor as
well as a valid promotion crossing if the purpose is to avoid treating historical positive
evidence as current benefit. The monitor's forecast and the risk process have different claims.

If one also runs a nontrivial stationary learner, keep its observation history separate from the
detector's history, as DAL's Appendix E conditions on forced observations when bounding stationary
learner regret. Split the total query cap between the two streams or prove a dependence-aware
extension. Sharing the same adaptively selected labels and importing DAL's theorem without this
step is not justified.

## What transfers and what does not

The deterministic schedule proves pathwise total-query feasibility. The calendar-window bound
follows from the maximum gap `L` between query events plus release delay `d`. The e-process gives
the global-null promotion guarantee independently of detector correctness. These facts form a
valid, simple comparator protocol.

Theorem III.9 of DAL does **not** directly give this adapter a regret bound. Its stationary learner
receives immediate feedback, its observations are action/cover based, it has no paid total-query
cap or deployment-switch cost, and its detector/learner proof uses separate histories. Replacing
its detector with an e-process can increase decision delay, and gating its action sequence can
change the stationary learner's regret. A complete bound would have to add the delayed stationary
learning term, query-calendar detection delay, gate-crossing delay, false/late-detection cost,
query charges and deployment-switch charges under the same piecewise-stationary contract.
Assumption III.8's minimum-separation logic also has to include the total-query and label-release
clock. None of these terms is covered merely by the source theorem.

This adapter is a fair comparator for the later method comparison, not a candidate contribution.
It is still a composition of a scheduled paired-query stream, a standard detector and an e-process
gate. Promotion validity under the global null does not certify positive utility after an
unobserved reversal; all current-regime performance claims must use fresh post-change queried
labels or an explicit regime model.

## Decision

The DAL source audit closes generic detector/exploration/restart novelty. This screen shows that a
risk-valid, pathwise-budgeted paired-query analogue is straightforward to define, but its regret
transfer has not been proved and no evidence says it is weak enough to create a contribution gap.
G1 remains open. Before G2 or experiments, derive the complete upper bound for this adapter and
compare it with the existing lower bounds and exact causal oracle. A new method must then improve a
specific term under identical risk, budget, delay and switch costs.
