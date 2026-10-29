# IID delayed terminal-test screen for the G1 memory hypothesis

**Date:** 2026-10-29. **Status:** exact reduction for a growing subfamily; negative novelty
screen, not a proposed method.

## Family and information structure

For each integer `B>=1`, query one binary paired-outcome label at each of rounds `1,...,B`.
Every query is charged immediately against the hard budget `B`; its label is released at the
start of the next round. Keep the incumbent deployed while labels are pending and make one
promotion decision only after the final label releases. Under the economic alternative the labels
are IID `Bernoulli(q)` for known `q>1/2`. Under the causal null, each label may have a history-
dependent conditional success probability `p_t<=1/2`. A promotion yields known post-decision
gross value `V` and incurs one switching charge `K`; querying costs `c` per label. There is no
post-promotion feedback or reversal in this screening family.

The rule is a randomized terminal test `phi(y_1,...,y_B) in [0,1]`, the conditional probability
of promotion after observing all labels. Its safety constraint is

```text
sup over causal nulls P(promote) <= alpha.
```

## Exact reduction and optimizer

For any test whose promotion probability is nondecreasing in every label, coupling each
causal-null label with a common uniform and the boundary label `1{U_t<=1/2}` gives the pointwise
ordering `Y_t<=Y*_t`. Therefore every such test has worst causal-null risk exactly at IID
`Bernoulli(1/2)`. This is the event-level monotonicity lemma in
[`switching_monotone_promotion_reduction_v1.md`](switching_monotone_promotion_reduction_v1.md),
which includes randomized upfront mixtures and arbitrary predictable query schedules.

Under the alternative, the likelihood ratio against the boundary IID null is

```text
L(y) = (2q)^S (2(1-q))^(B-S),   S = sum_t y_t,
```

which is increasing in `S`. By the Neyman–Pearson lemma, among all tests with boundary-null size
at most `alpha`, a most powerful test is an upper-tail count test, randomized only at its cutoff:

```text
phi(y) = 1{S > r} + gamma * 1{S = r},   0 <= gamma <= 1.
```

Choose `r,gamma` so `P_{1/2}(S>r)+gamma*P_{1/2}(S=r)=alpha` (randomization at the cutoff attains
any `alpha` in `[0,1]`). This test is coordinatewise nondecreasing, so its causal-null risk equals
its IID-boundary size. Every causal-null-feasible test also has IID-boundary size at most `alpha`;
Neyman–Pearson therefore bounds its alternative power by this test's power. Since the test itself
is causal-null feasible, it is globally optimal over the full robust test class. Its alternative
promotion probability is the corresponding upper-tail probability under `Binomial(B,q)`. The net
expected gain against never promoting is `(V-K)*P_q(promote)-cB`; thus this entire terminal
subproblem has a closed-form test and a transparent acquisition break-even comparison.

For implementation, the learner needs the released-positive count `S` plus a one-label pending
queue and the public clock/request schedule. This is `B+1` count values at each clock time (and
`O(B^2)` unrolled clock/count states), rather than `2^B` resolved histories. It obeys the one-step
release rule and the request-time hard cap. The delayed queue changes when the count updates, but
does not change the terminal statistic once all labels are released.

## Decision and limits

This growing family does **not** support a memory lower bound: the count is sufficient and gives an
exact zero-gap compact controller. It also does **not** establish a new acquisition-and-switching
algorithm. Query times are fixed; there are no recurring regimes, within-run deployment actions,
reversal loss, or online post-promotion feedback. The reduction is classical simple-hypothesis
testing, and finite-horizon adaptive sensing/stopping with a maximum sample count is already covered
by the source-level prior audit in
[`switching_usage_constrained_sequential_testing_prior_audit_v1.md`](switching_usage_constrained_sequential_testing_prior_audit_v1.md).
The monotone causal-null reduction is supporting safety algebra, not novelty.

**G1 consequence:** reject the IID terminal-test family as the target theorem. Any memory lower
bound or compact-state approximation candidate must exploit something absent here: at minimum,
recurrent economic regimes with reversible costed deployment and decisions made before all pending
labels clear, while retaining the separate causal-null any-promotion constraint. The full-history
alternative value and causal-null risk must both be compared on that growing family. Promotion-risk
validity still says nothing about current-regime benefit after an unobserved reversal; that requires
post-change evidence or an explicit persistence/predictive-signal assumption.
