# A1b registered protocol: does the timing-adaptivity gap keep growing in the critic's family?

Registered 2026-10-30 after the adversarial review (`11_ADVERSARIAL_REVIEW.md`) and before
execution.

The A1 KILL stands under its own protocol; this protocol does not revise it. The slice tested
here was found post hoc by the critic, outside A1's grid. The result is therefore development
evidence about one family, not a grid-wide statement.

## Method and comparator

Unchanged from A1: the same solver commit `2bd2e8e`, the same runner
(`scripts/promising_directions/a1_exact_separation.py::solve_cell` at `b050f95`), the same J
(exact joint planner) and the same C* (best slot-skippable calendar of at most B slots in
1..T−d with exact risk-constrained switching). C* is the strongest separable comparator. The
critic's open-loop "forced" class is weaker and is not used for decisions.

## Family

Fixed parameters: B = 3, d = 1, transition 1/20 both ways, emissions (1/50, 49/50),
prior1 = 1/5, query cost 1/100, switch cost 1/20.

- Primary: alpha = 1/5, T = 6, 7, …, 12, solved sequentially with 1 worker.
- Secondary: alpha = 1/10, T = 9, 10, 11, if time remains.
- Compute cap: 4 hours wall clock. Unfinished horizons are reported as not run. A MemoryError
  is reported, not retried with altered settings.

Pre-execution verification by the orchestrator: T = 6, 7, 8 give relative gaps 0.004999,
0.007991, 0.011783.

## Decision rule

Let g(T) be the relative gap (C* − J)/J.

| Outcome | Condition | Consequence |
|---|---|---|
| CONTINUE to A2 theory | g(T) ≥ 0.10 for some solved T ≤ 12; or the last three solved increments are each ≥ 0.005 and g at the largest solved T is ≥ 0.05 | Requires a structural explanation and an attempt at a growing-family lower bound. It does not support a method claim on its own. |
| KILL | The increment at the largest solved T is < 0.0025, max g < 0.05, and alpha = 1/10 stays at 0 | The family is closed. |
| INCONCLUSIVE | Otherwise | Record it, together with the exact horizon at which tractability ended. |
