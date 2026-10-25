# Delayed evidence-directed PPI: persistent-scale null calibration protocol

**Status:** frozen before execution. This is a robustness calibration, not a power study. Its seeds begin at 20290000 and are disjoint from development (20272000–20272029), IID calibration (20280000–20280999), and the harm confirmation (20282000–20282999).

## Question and generator

Does the frozen delayed evidence-directed PPI monitor maintain its registered false-escalation bound when the scale of bounded paired costs is serially dependent but their conditional mean remains zero? Generate 1,000 independent 1,200-source / 2,400-target streams. A two-state Markov regime switches with probability 0.05 per event and sets the paired-cost amplitude to either 0.55 or 1.0. Conditional on the entire past and current regime, each event receives a fresh independent fair sign, so `Z_t = A_t S_t` satisfies `E[Z_t | G_(t-1)] = 0` despite persistent variance. Contexts are independent fair `{-1,+1}` values and do not reveal the evaluator-only regime. Labels, when queried, have independent uniform delays 0–12.

The learner sees contexts, a frozen proxy trained only on source labels, prior committed prefix evidence, remaining budget, randomized query decisions, and only arrived labels. The regime path remains evaluator-only and is not passed to the monitor or propensity rule. The candidate is `evidence_a0p025_p0p5_eventwise`; uniform PPI is the matched comparator. Both use alpha 0.05, epsilon 0.05, q support `[0.05,0.80]`, the same 480-label hard cap, and the existing event-prefix monitor implementation.

## Mathematical scope and gate

The candidate propensity depends only on prior committed evidence and remaining spend. The proxy is outcome-free for each target event, the Bernoulli query coin is conditionally independent of the current outcome, and `B_t=(M+epsilon)(2/q_t-1)` is predictable from prior history. Thus the eventwise bounded-mean construction targets the conditional null above. Persistent amplitude alone does not violate that null because the sign is freshly fair conditional on the regime. This DGP does not test persistent signs or serial dependence in the conditional mean.

There are two method cells. Use a one-sided Clopper–Pearson upper limit at confidence `1-0.05/2=97.5%` in each cell. Pass only if both simultaneous upper limits are at most 5%, every expected stream/method row is present, all pathwise caps hold, there are no unresolved labels, and registered event counts equal monitor updates. This is finite simulation evidence for this one Markov-scale generator; it neither replaces the proof nor establishes robustness to arbitrary dependence. No figures are planned.

## Reproduction

`uv run shiftlab-dive-delayed-evidence-ppi-markov-calibrate --seeds 1000 --seed-offset 20290000 --device cuda --output-dir outputs/delayed_evidence_ppi_markov_calibration_1000`
