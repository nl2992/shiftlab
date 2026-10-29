# First-promotion decomposition of the two-law switching objective

**Date:** 2026-10-29. **Status:** exact structural reduction; not a novelty claim.

## Contract

Use a finite horizon, a pathwise query cap charged at request time, fixed known label delay,
learner information containing only released labels, and the full-history causal null from the
two-law game. Under the alternative, a known finite-state HMM determines economic outcomes and
deployment costs. Let `tau` be the first event at which the learner chooses the challenger;
`tau=+infinity` if it never promotes. The constraint is

`sup_nu P_nu(tau <= T) <= alpha`,

where `nu` ranges over the history-adaptive conditional-null label kernels. Once `tau` has
occurred, the event is already determined on that path. Later rollback, re-promotion, query
choices, pending-label releases and deployment costs cannot change its indicator.

## Proposition: exact first-promotion decomposition

For each learner information history `h` just before the choice at a first-promotion event `t`,
let `V_t(h,q)` be the minimum alternative-law expected cost from event `t` through `T`, conditional
on choosing the challenger at event `t`. The state `h` supplies the alternative belief over the
current HMM mode and pending outcomes, the labels released to the learner, and the public history;
`q` is the unspent query budget before the event. The continuation chooses the query at `t` and
later queries, and allows rollback and re-promotion subject to the pathwise cap. It includes the
switching charge and decision cost at `t` and has no false-promotion constraint.

Then the original optimum equals the value of the following pre-promotion problem: choose a
nonanticipating policy that keeps the incumbent deployed until its first promotion, pays the
alternative-law costs before that event, and on promotion history `h` receives terminal
continuation cost `V_t(h,q)`, subject to the same global robust constraint
`sup_nu P_nu(tau <= T) <= alpha`. Query cost, any query made on the promotion event, the switching
charge and the event's decision cost are included in `V_t`.

**Proof.** Take any feasible policy in the original game. Restrict it to histories before `tau` to
obtain its pre-promotion policy. At each first-promotion information history, its conditional
continuation is feasible for the ordinary delayed alternative-HMM control problem, so replacing
that continuation with `V_t` can only weakly lower expected alternative cost. The robust event
probability is unchanged because `1{tau <= T}` is fixed at first promotion. This proves that the
decomposed optimum is no larger. Conversely, concatenate any feasible pre-promotion policy with
an optimal continuation attaining each `V_t`. The concatenated policy has the same first-promotion
event under every causal-null strategy and the same alternative expected cost, so it is feasible
and attains the decomposed objective. The two optima are equal. The argument permits delayed labels
pending at `tau`: they belong to the alternative continuation state but remain hidden from the
learner until release, while the causal-null risk event is already absorbing.

## Consequence for the candidate

This makes a history-dependent query-budget split an exact Bellman decomposition, rather than a
new acquisition/switching mechanism. It explains why the certified six-round policy is already
captured by its two-query promotion phase and one-query continuation. The reduction may help
computation if the continuation values can be represented compactly and the pre-promotion robust
stopping problem can be solved more efficiently than the generic sequence-form LP. Those are
algorithmic hypotheses requiring complexity and value/risk guarantees; the proposition alone is
standard and does not pass G1.

The decomposition also preserves the scientific distinction central to the project: the
pre-promotion causal-null constraint certifies only the event of first promotion. `V_t` is an
alternative-model economic forecast that uses the current posterior and subsequent labels; no
pre-promotion likelihood-ratio wealth is treated as evidence that the challenger remains
beneficial after a reversal.

## Next test and stop condition

Implement the two stages without changing the full sequence-form reference: (1) compute the exact
delayed-HMM continuation table `V_t` over promotion information histories, remaining budget and
pending feedback; (2) optimize the robust pre-promotion stopping game against the full-history null.
On the registered small cell, require equality with the certified oracle bracket and exact
independent risk verification. Then compare tree/state growth as `T` and `B` increase against the
generic oracle and the best established safe sequential-design / delayed-POMDP composition. A
method claim survives only if a source-audited theorem proves a meaningful computational or
approximation advantage while preserving the same value and risk. If this is simply standard
optimal stopping plus a delayed-POMDP continuation table with no new guarantee, reject the route;
do not open G3–G5.

## Existing source boundary

- The repository audits delayed economic sampling/adoption, cost-aware sequential testing, and
  exact delayed-POMDP Bellman states in
  [`switching_composed_prior_boundary_v1.md`](switching_composed_prior_boundary_v1.md),
  [`switching_delayed_comparator_audit_v1.md`](switching_delayed_comparator_audit_v1.md), and
  [`switching_delayed_pomdp_information_state_audit_v1.md`](switching_delayed_pomdp_information_state_audit_v1.md).
- The generic two-law sequence-form oracle and its asymmetrical information contract are in
  [`switching_two_law_game_duality_v1.md`](switching_two_law_game_duality_v1.md).
- The registered six-round oracle bracket is in
  [`switching_reversal_lp_certificate_v1.md`](switching_reversal_lp_certificate_v1.md).
