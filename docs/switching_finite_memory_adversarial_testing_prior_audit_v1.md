# Finite-memory adversarial testing prior audit

**Date:** 2026-10-28. **Status:** focused primary-source audit. Generic finite-state robust
hypothesis testing and memory/error tradeoffs are occupied; no transfer to the ShiftLab objective
is established.

## Source and theorem scope

Managoli and Prabhakaran, *Memory Constrained Adversarial Hypothesis Testing*, arXiv:2605.12063
(2026 preprint), study a randomized, time-invariant finite-state machine with \(S\) states and a
finite sample alphabet. Under each binary hypothesis, an adaptive adversary selects each sample
law from a closed convex set using past samples and the full past FSM-state sequence. Their
performance measure is asymptotic average classification error over time. Theorem 1 bounds the
minimax error in terms of \(S\), and Corollary 1 identifies its error exponent; Theorem 2 gives
an exact expression when a weak least-favourable-distribution pair exists. The construction uses
a randomized birth-death FSM and martingale analysis. Model, theorem statements and proof sections
were inspected in the primary HTML source; no independent proof reproduction was performed.

This is close prior art for claims based only on bounded-memory adversarial testing, robust FSM
verification, or an error-versus-memory tradeoff. The adversary's access to the FSM-state sequence
is stronger than the ShiftLab null's stated visibility in some respects, but that does not close
the objective mismatch.

## Contract mismatch

ShiftLab's risk is the finite-horizon event \(P(\exists t:\text{first promotion by }t)\leq\alpha\)
under a one-sided conditional null. The economic objective is expected cumulative cost under a
separate known recurrent HMM. Queries are chosen by the learner, charged against a pathwise total
cap at request time, and their labels arrive after a delay. Deployment is reversible and pays a
switch charge. The adversarial-testing theorem instead treats samples as arriving every step,
has no query price or pathwise acquisition budget, no pending-feedback queue, no switching/rollback
loss, no alternative-model economic objective, and controls long-run average classification error
rather than a one-time familywise false-promotion event.

Consequently its memory/error exponent cannot be read as a false-switch bound, delay-regret bound,
or cost guarantee for a budgeted switching policy. Adding an FSM to a paid delayed tester would be
an ingredient composition until a finite-time theorem proves the costed acquisition-and-switching
advantage under the same risk contract.

## Research decision

Reject “finite-memory adversarial testing” or a generic FSM risk controller as the novel mechanism.
Do not treat the paper's asymptotic exponent as the desired theorem. The remaining candidate must
be an acquisition-and-deployment result: a finite-horizon, pathwise-budgeted, delayed-feedback
policy with (i) exact anytime/ever-promotion risk control, (ii) reversible switching economics,
and (iii) a nontrivial cost/regret guarantee against the full constrained oracle and established
delayed-safe baselines. If these features only compose known bounds with additive delay and query
terms, revise or stop the method hypothesis. Current-regime forecasts still require post-reversal
evidence or a persistence model; historical test memory only addresses its declared null.

## Primary source

- Managoli and Prabhakaran (2026), [arXiv:2605.12063](https://arxiv.org/abs/2605.12063), especially
  Section II for the adversary/FSM information structure, Theorem 1 and Corollary 1 for the
  \(S\)-dependent minimax error, Theorem 2 for the least-favourable-pair case, and Sections IV–V
  for achievability and converse.
