# A1c registered protocol: what creates the A1b gap — the risk constraint or plain adaptivity?

Registered 2026-10-30 after A1b, before execution. Development and theory probe; no method claim.

## Background

In A1b's family (B = 3, d = 1, transition 1/20 both ways, emissions (1/50, 49/50), prior1 = 1/5,
cq = 1/100, cs = 1/20), the joint-vs-calendar relative gap g grows from 0.50% to 4.64% over
T = 6..11 at alpha = 1/5. The gap is exactly 0 at alpha = 1/10 for T = 9..11.

The solver (`2bd2e8e`) imposes `risk <= alpha` in the LP and then applies the root-mixture
activation `min(1, alpha/risk)`. Setting alpha = 1 therefore gives the risk-unconstrained
reference.

Two hypotheses:

- **H-slack.** The gap is an ordinary POMDP timing-adaptivity gap that exists without any risk
  constraint. A tight alpha suppresses it, because the constrained optimum is forced towards
  conservative early queries, where calendars are already optimal.
- **H-risk.** The risk constraint itself creates value for adaptive timing. For example, adaptive
  re-checking might be what makes promotion feasible at an intermediate alpha.

Under H-slack, Lane A is closed with no risk-specific structure: the gap is the X2-type
unconstrained effect. Under H-risk, there is a candidate for a risk-specific separation
(gate A2).

## Parts (fixed before execution)

Solver, runner and comparator are unchanged from A1/A1b (`solve_cell`, best slot-skippable
calendar in 1..T−d with exact risk-constrained switching), except where P4 states otherwise.

| Part | Cells | Settings |
|---|---|---|
| P1 alpha scan | 10 | T = 9, alpha in {1/10, 1/8, 3/20, 1/6, 9/50, 1/5, 1/4, 3/10, 1/2, 1} |
| P2 prior coupling | 14 | T = 9, prior1 in {1/10, 3/10} × alpha in {1/10, 3/20, 1/5, 1/4, 3/10, 1/2, 1} |
| P3 unconstrained trend | 6 | alpha = 1, T = 6..11 |
| P4 horizon extension | 1 | alpha = 1/5, T = 12, max_nodes = 2,000,000 |
| P5 mechanism (descriptive) | — | T = 8, alpha = 1/5 |

P4 raises max_nodes from 200,000 to 2,000,000 for this single cell. This is a registered
settings change. It is run only after P1–P3 and within a 2-hour cap. A failure (node cap, LP
time limit, memory) is recorded and is not retried with further changes.

P5 is descriptive. It is done only if the recovered joint policy exposes query decisions per
history. It reports, for the joint policy and for the best calendar's policy:
- the query-time distribution conditional on the first released label;
- the promotion and rollback probabilities;
- the realised null risk before activation, and the activation probability.
If the policy object does not expose query decisions, P5 is reported as not feasible.

Every cell also records the joint planner's pre-activation risk and its activation probability,
plus the same two quantities for the best calendar.

Compute: at most 2 workers for P1–P3, 1 worker for P4, and 4 hours wall clock in total.

## Decision rules

Let g(alpha) be the relative gap at T = 9 with prior1 = 1/5.

| Outcome | Condition | Consequence |
|---|---|---|
| **H-risk SUPPORTED** | Some alpha < 1 in P1 or P2 has g(alpha) ≥ g(1) + 0.005 at the same prior1, i.e. the constrained gap exceeds the unconstrained gap by at least 0.5 percentage points | Proceed to an A2 theory attempt on why constraint-induced adaptivity arises. A method claim still requires the 10% practical threshold. |
| **H-slack SUPPORTED** | (a) for every prior1 there is a threshold alpha* with g = 0 below it and g nondecreasing in alpha above it, up to 1e-9; and (b) g(alpha) ≤ g(1) + 0.005 everywhere | Lane A closed for good: the only information-matched separation is the unconstrained timing-adaptivity gap, suppressed by the risk constraint |
| **MIXED** | Otherwise | Record the exact pattern |

Descriptive outputs, not decisions:
- whether alpha* moves monotonically with prior1;
- whether g(1) over T = 6..11 (P3) grows or plateaus;
- g(12) at alpha = 1/5 (P4), assessed against A1b's CONTINUE thresholds.
