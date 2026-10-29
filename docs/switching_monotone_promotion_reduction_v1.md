# Monotone promotion events reduce the causal null to its IID boundary

**Date:** 2026-10-28. **Status:** exact safety lemma and candidate tractability restriction; no
novelty or utility claim.

## Contract and proposition

Let `Y_1,...,Y_T` be binary potential common-outcome labels. The learner may query adaptively,
with fixed delayed release, and its deterministic pure policy maps the complete history it has
observed into query and deployment decisions. The null environment may choose each conditional
success probability after seeing its full past and current public choices, but it must satisfy

    P(Y_t=1 | full past, current public choices) <= 1/2.

The pathwise promotion event of a deterministic learner plan is a Boolean function
`g(y_1,...,y_T)`. Unqueried potential outcomes are included in this tape only for the coupling;
the learner never observes them. Say the plan has a **monotone promotion event** if
`g(y)<=g(y')` whenever `y_t<=y'_t` for every `t`.

**Proposition.** For every pure plan with a monotone promotion event,

    sup_{causal conditional nulls} P(any promotion) = P_{IID(1/2)}(any promotion).

The equality also holds for any upfront mixture supported entirely on such pure plans.

**Proof.** Draw common independent uniforms `U_t~Unif[0,1]`. Under any causal null, generate
`Y_t=1{U_t<=p_t(H_{t-1},C_t,Q_t)}`, where the chosen conditional probability is always at most
`1/2`. On the same uniforms define `Y*_t=1{U_t<=1/2}`. Pointwise, `Y_t<=Y*_t` for every event
time, regardless of how the null adapts `p_t` to hidden past outcomes or public queries. Run the
same deterministic learner plan on both tapes. Monotonicity gives `g(Y)<=g(Y*)`, hence every
causal-null promotion probability is at most the IID-boundary probability. The IID boundary is
itself an admissible conditional null, so it attains the supremum. Condition on the upfront plan
lottery and average to obtain the mixture claim. Fixed delay and the hard query cap do not affect
the comparison; they are properties of the plan and its observable execution. QED.

## Why the event condition matters

The condition is on the *promotion event*, not on query frequency. For example, query at round 1;
if its released label is positive, promote at the next decision and stop acquiring; if it is
negative, wait and query again later, promoting only if that later label is positive. Querying is
more likely after the negative first label, yet the promotion event is `Y_1=1 or Y_2=1`, an
increasing function of the potential-outcome tape. The causal-null supremum is therefore attained
at IID `Ber(1/2)`.

By contrast, the existing counterexample queries at round 1, queries at round 2 only when
`Y_1=0`, and promotes only when `Y_1=0,Y_2=1`. Its rejection event is not monotone. IID risk is
`1/4`, but the causal null chooses `p_1=0,p_2=1/2`, giving risk `1/2`. Thus IID calibration is
not valid for arbitrary adaptive acquisition rules; the event-level monotonicity restriction is
doing necessary work.

## Algorithmic implication and unresolved obligation

For a policy class whose pure plans all have monotone promotion events, robust safety can be
checked under one boundary-IID null instead of enumerating every causal null strategy. The
alternative objective can still use the declared recurrent hidden-regime model, and the policy
can still adapt query timing, reserve a hard budget and roll back. This gives a concrete route to
compressing the risk side of the finite causal game.

It does **not** show that a net-cost-optimal or near-optimal policy has a monotone promotion
event. Nor does it by itself provide a scalable optimizer for the constrained alternative-
utility/IID-risk problem, an approximation guarantee to the robust oracle, or a strict gain over
known sequential-design methods. The condition can be checked exhaustively for small deterministic
plans, but the `2^T` event table is not a scalable representation. The next gate is to derive a
compact acquisition-and-switching policy parameterization that enforces event monotonicity and
then prove either a useful approximation to the robust oracle or an explicit counterexample
showing why the restriction is too costly. Do not call this lemma the novel contribution.

## Cost screen on the registered recurrent cell

The saved `switching_causal_game_v1/verification.json` gives one useful feasible comparison in
the registered `T=5, B=2, d=2, alpha=1/10` recurrent-HMM cell. The recovered unrestricted policy
simplifies exactly to: with probability `2/5`, query events 1 and 2, promote at round 4 iff both
labels are 1, then hold; otherwise do nothing. Conditional on activation its promotion event is
`Y_1 Y_2=1`, which is monotone. The upfront mixture has robust risk `1/10`, uses at most two
queries, and its exact expected decision/query/switch costs and counts match the independently
enumerated unrestricted recovered policy on all 2,048 hidden-state/outcome worlds. Its total cost
is `184103/78125 = 2.3565184`.

Thus the monotone-event restriction has **zero observed cost** relative to the solver's recovered
policy in this one registered cell. This does not certify zero cost relative to the exact
unrestricted optimum: the sequence-form LP output is numerical and has no exact rational dual
certificate. Nor does the example test an adaptively acquired monotone policy or show that the
monotone class remains competitive across regimes, delays and budgets. It only establishes a
non-vacuous safe feasible policy in a recurrent model with no observed loss on the existing
reference cell.

The new exact pure-plan screen `scripts/screen_monotone_switching_policy_cost.py` checks a
separate analytic cell (`T=2, B=1, d=1`, static hidden regime with emissions `1/4,3/4`,
`alpha=1/10`, `c=1/100`, `k=1/10`). It enumerates all 16 deterministic plans, retains all 15
with monotone promotion events, and solves their mixture LP using the single IID-boundary risk
constraint. The optimum is `987/1000`: use probability `4/5` on no query/no switch and probability
`1/5` on query-at-round-1, promote at round 2 iff the label is positive. Independent forward
evaluation gives cost `987/1000`; the causal endpoint best response gives risk `1/10`. The
unrestricted game solver returns the same cost, consistent with the repository's analytic
two-round benchmark. This validates the small constrained solver and shows zero restriction cost
in this toy cell; it does not demonstrate a new acquisition advance or finite-horizon scalability.

The exhaustive unrestricted pure-plan mixture LP now has an exact rational dual certificate too:
the dual has `nu=1`, one nonzero null-response multiplier `mu=13/100`, and gives lower bound
`nu-alpha*mu=987/1000`. Its inequalities hold for all 16 pure plans, so the unrestricted optimum
in this two-round extensive form is exactly `987/1000`, matching the monotone-class optimum.
This closes the optimality gap for this toy comparison only; it does not upgrade the recurrent
T=5 numerical solver result or establish any general approximation guarantee.
