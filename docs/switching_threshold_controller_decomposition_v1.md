# Threshold-and-hold controller: exact economic decomposition

2026-10-28. **Status:** baseline identity, not a new algorithm or theorem claim. This makes the
standard e-detector plus one-switch controller comparable to the registered economic objective.

## Contract cell

Fix one alternative onset `nu`, persistent iid `Y_t~Bernoulli(1/2+epsilon)` for `t>=nu`, and
the global conditional null `P(Y_t=1 | full past, predictable query)<=1/2`. Set policy losses to
`l_t(0)=Y_t`, `l_t(1)=1-Y_t`. A one-switch oracle stays at 0 before nu, switches to 1 at nu,
and pays k once. The learner starts at 0, issues at most B queries on every path, pays c per
query, uses a valid one-sided e-detector, switches 0->1 only when that detector crosses its
threshold, and holds policy 1 for the rest of the horizon. There is no rollback in this baseline.

Let `tau` be the calendar round at whose start the evidence crossing is first visible and the
learner promotes; set `tau=+infinity` if no crossing is visible by T. The feedback delay is fixed
at d and labels arriving at the start of round t are precisely those queried at event time t-d.
Let `N` be the total number of queries issued, including unresolved queries.

## Exact net-cost identity

Write `H=T-nu+1` and `Delta=E[l_t(0)-l_t(1)]=2*epsilon` in the persistent alternative. Conditional
on the evidence-driven action, the expected per-round loss gap after onset is Delta while the
learner remains at 0 and zero after promotion. The oracle and learner each pay k on paths where
the learner promotes; if the learner never promotes, the oracle alone pays k. Therefore

`E[J_learner-J_oracle] = Delta*E[min((tau-nu)_+, H)] + c*E[N] - k*P(tau=+infinity)`.

The formula includes all calendar time before any post-onset label is released, the full delay of
the statistical test, failure to cross before budget/horizon exhaustion, label charges for
pending queries, and the comparator's one-time switch charge. It is an identity for this
persistent Bernoulli cell, not a bound for arbitrary nonstationarity or rollback policies.

Under the global conditional null, the e-detector crossing rule controls
`P(any 0->1 promotion)<=alpha`. A fixed delay and predictable query schedule preserve that
validity. The risk guarantee does not bound any of the three terms in the economic identity:
query volume, expected crossing delay under the alternative, or probability of no crossing.
The fixed-cohort and randomized-alpha calculations already quantify selected examples of these
terms; neither establishes a rate-optimal threshold-and-hold policy.

## Research consequence

This closes a bookkeeping gap in the baseline comparison. Any claimed benefit over the standard
composition must improve the right-hand side by a proved amount under the same alternative class,
hard cap, delay, and null risk. The mechanism would have to improve the distribution of `tau` or
reduce `E[N]` without increasing no-cross probability or invalidating alpha. For reversal
environments, the identity must be replaced: stale historical wealth cannot certify the current
regime, rollback delay adds further regret, and an episode-wise risk allocation is required.

The identity and e-detector composition are standard. They do not resolve whether a novel
acquisition policy can beat constrained sequential design; G1 remains open and no efficacy run
follows.
