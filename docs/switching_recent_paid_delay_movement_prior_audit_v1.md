# Recent paid-observation, delay-capacity, and movement-cost prior audit

**Date:** 2026-10-30. **Status:** primary-source audit of three close methods; prior boundary,
not a novelty claim.

## Gong and Zhang (ICML 2026): paid observations and a finite free-observation budget

The primary ICML paper, [*The Cost of Information: Phase Transitions in Contextual Bandits with
Paid Observations*](https://proceedings.mlr.press/v306/gong26i.html), was read at the formal
protocol, Algorithm 1, Theorems 2.1–2.2, Theorems 3.1–3.2, and the stochastic function-class
protocol/Algorithm 3/Theorem 4.1.

At round `t`, the learner sees context and an action-specific observation-cost vector, chooses an
action and an observation subset `O_t`, pays for those action losses, and later uses the revealed
losses. The adversarial model allows the context and loss vector to depend on the entire past.
Regret is cumulative loss against the best fixed contextual policy plus observation expenditure.
Theorem 2.1 gives an adaptive paid-observation regret upper bound; Theorem 2.2 supplies a minimax
lower bound. Their hybrid extension additionally allows up to `B` free action-loss observations
over the horizon. Theorems 3.1–3.2 establish a budget-regime phase transition and a matching
meta-controller guarantee. In the stochastic function-approximation section, Theorem 4.1 uses
realizable conditional mean losses and a square-loss-regret online oracle for an oracle-efficient
algorithm.

This is close prior art for costly information acquisition, a pathwise-limited free-observation
resource in the hybrid protocol, paired action-loss learning, and regret that includes observation
cost. The authors also connect the paid-observation reduction to switching-cost bandits. The
formal setting still differs from ours: observations are subsets of per-action losses rather than
one common paired outcome; feedback is immediate; there is no delayed queue or current-regime
reversal objective; switching costs are not a repeated deploy/rollback utility contract; and there
is no time-uniform false-promotion event over a history-adaptive conditional null. Consequently,
the differences narrow the required theorem but do not establish a gap.

## Qiu et al. (ICML 2026): dynamic regret with movement costs and delay

The primary ICML paper, [*Parameter-free Dynamic Regret: Time-varying Movement Costs, Delayed
Feedback, and Memory*](https://proceedings.mlr.press/v306/qiu26k.html), was read at its movement-cost
model, Algorithm 3 and Theorems 3.1/4.1, and the delayed-feedback reduction (Algorithm 4,
Lemma 5.1, Theorem 5.2).

The method considers unconstrained online convex optimization with a time-varying movement
coefficient and a drifting comparator. Theorem 4.1 gives comparator-adaptive dynamic regret with
first-order movement-cost dependence. For delayed feedback, Algorithm 4 reduces delayed gradients
to aggregated arriving gradients plus a movement cost proportional to the number of outstanding
gradients; Theorem 5.2 obtains a parameter-free dynamic-regret bound involving total delay and
comparator path length. Feedback is full gradient feedback when it arrives; observations are not
actively purchased or subject to a total query cap.

This closes generic claims that delayed updates and deployment movement costs can be jointly
handled by a dynamic-regret wrapper. It does not give selective acquisition, a hard observation
budget, discrete switching economics, or any-promotion risk. Those exact elements must appear in
the new theorem's separation, not just its algorithm description.

## Ryabchenko, Attias, and Roy (COLT 2025): capacity-constrained delay scheduling

The primary COLT paper, [*Capacity-Constrained Online Learning with Delays: Scheduling Frameworks
and Regret Trade-offs*](https://proceedings.mlr.press/v291/ryabchenko25a.html), was read at the delay
scheduling protocol, fixed-delay capacity theorem/table, and clairvoyant/non-clairvoyant scheduling
results.

The learner can track at most `C` past rounds for delayed feedback. The adversary is oblivious,
selects the delay and loss vectors before the game, and feedback can be bandit (played-action loss)
or full information. For fixed delays, Theorem 3 and Table 1 give matching minimax bounds and show
that constant concurrent capacity suffices in the full-information regime; for varying delays,
Theorem 10 gives a logarithmic-capacity upper-bound regime, with variants for preemption and delay
knowledge. This capacity counts outstanding tracked rounds. It is not a pathwise total query/acquisition
budget: rounds that finish can free capacity for later tracking.

This is a required baseline for pending-label scheduling and delay-capacity claims. It has no paid
query choice, model-switching cost, reversible economic objective, or false-promotion risk.

## Consequence for G1

The close 2025–2026 literature now occupies paid observation/regret, switching-cost learning,
delayed movement-cost regret, and concurrent-capacity scheduling. A contribution cannot be the
unqualified intersection of these ingredients with an e-process or risk gate. Any reopened
candidate must state a structural condition that lets it improve on a matched composition of:

1. Gong–Zhang paid-observation/full-information methods (including their finite free-observation
   budget regime) with the applicable delayed wrapper;
2. Qiu et al.'s movement-cost delayed dynamic-regret method;
3. Ryabchenko et al.'s capacity-aware delayed-feedback scheduler;
4. the repository's risk-valid sequential-test/switching composition; and
5. the exact two-law oracle on small cells.

The remaining possible delta is not merely these methods' nonmatching assumptions. It must be a
provable joint interaction of selective paired labels, fixed release delay, a request-time total
budget, repeated reversible deployment value, and anytime conditional-null false-promotion control.
No such candidate or separation is selected by this audit. G1 remains open; G2–G5 and all locked
holdouts remain held. Historical false-promotion evidence remains separate from current-regime
value evidence after reversal.

## Source snapshots

The downloaded official PDFs were text-extracted locally for this audit. SHA-256:

- Gong–Zhang ICML 2026: `5d30ced568a0e959956906c41ac6df76b52201a9d14f6afbacf23797935e874f`
- Qiu et al. ICML 2026: `65aaa9262beb59be090c231f320b5e07886ed096eba989e3b46f850ea3b7ac6b`
- Ryabchenko et al. COLT 2025: `01e174ed7eec8a19cc2c9c16ea4a0e4588075101a469d7735e1980439436a311`
