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

## Exact solver prototype and checks

`src/shiftlab/dive/first_promotion_decomposition.py` implements the reduction without changing the
full sequence-form reference. It computes the post-promotion value with an exact-rational belief DP
over the current HMM state and pending queried outcomes, then leaves only pre-promotion learner
sequences and the full-history null response in the sequence-form LP. The continuation policy is
recovered from that DP. Focused tests independently compare the full and reduced optimizers, their
forward expected metrics, and their exact causal-null risks on three small configurations:

| `T,B,d` | Full learner sequences | Reduced learner sequences | Full nodes | Reduced nodes | Recovered cost | Null risk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `5,2,2` | 1,509 | 141 | 2,586 | 347 | `7713/3125` | `1/10` |
| `5,2,1` | 1,901 | 181 | 2,586 | 347 | `193099/80000` | `1/10` |
| `6,3,1` | 15,693 | 705 | 21,733 | 1,799 | `461083/160000` | `1/10` |

All five independently evaluated expected metrics match the full reference exactly in each case;
the six-round value also matches the certified full-oracle bracket of width `4.5e-11`. At
`T=6,B=3,d=1`, the reduced LP has 95.5% fewer learner realization variables and the builder
visits 91.7% fewer nodes. Focused validation: `uv run pytest -q
tests/test_first_promotion_decomposition.py` (3 passed), Ruff, and mypy.

For fixed query budget `B`, a crude history count bounds the pre-promotion learner/null trees by
`O(T * sum_{q=0}^B binom(T,q) 2^q)`, since the incumbent action is fixed before promotion and
each requested binary label contributes one outcome bit. The post-promotion DP can merge action
histories by `(time, current action, remaining budget, delayed-HMM belief)`; its reachable beliefs
are indexed by query times and queried outcomes and obey the same XP-in-`B` history bound. This is
polynomial in `T` for fixed `B`, but exponential in `B`; it is not an FPT or uniform-polynomial
result. The implementation's measured small-cell reduction supports feasibility, not a practical
scaling claim.

The registered fixed-`B=3`, `d=1` scaling run extended this comparison to `T=7,8`. At `T=7`, the
full and reduced solvers again return exactly the same rational cost `10788127/3200000`, all five
metrics, and risk `1/10`; realization variables fall from 54,861 to 1,317 and nodes from 71,401 to
3,334. At `T=8`, the generic builder exceeds its frozen 200,000-node cap, while the reduced solver
completes with 2,273 learner sequences, 848 information sets, 5,700 builder nodes, recovered cost
`24735833/6400000`, and exact risk `1/10`. The T8 cost has no direct full-oracle comparison because
the reference hit its registered limit; the structural proposition and smaller exact comparisons
support the reduction, but this cell alone does not independently certify equality to the generic
oracle optimum. Full output is
`outputs/first_promotion_decomposition_scaling_v1/results.json` (3,424 bytes; SHA256
`65E823B198C81EFE32C824D3BF4A5FB7967563CBFDD96CFA14C5B23AF3613C32`).

## Novelty gate and next test

The first-promotion proposition and backward-induction decomposition are standard. The current
prototype is an exact optimization algorithm for the desired policy class, but it does not define
a new policy or establish an advantage over a source-matched safe sequential-design plus delayed-
POMDP method. The next G1 step is a source-level audit of exact event-tree elimination / robust
optimal-stopping decompositions under separate alternative utility and full-information null risk,
then the fixed-budget scaling protocol in
[`switching_first_promotion_scaling_protocol_v1.md`](switching_first_promotion_scaling_protocol_v1.md).
A method claim survives only if this implementation has a nontrivial complexity/value guarantee
beyond that prior work and the selected policy has a matched-budget utility advantage. Otherwise
retain the solver as a verification tool and revise G1; do not open G3–G5.

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
