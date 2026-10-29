# Exact reduction boundary: usage-constrained testing versus delayed robust switching

**Date:** 2026-10-28. **Status:** analytical contract comparison; no novel candidate selected.

## A nontrivial subproblem is already covered

Take a single fixed regime, known IID outcome laws under a simple null and simple alternative, no feedback delay, one queried common outcome per sample, and at most B samples before a terminal decision. Let D=1 mean adopt the challenger. Assign terminal Bayes loss `mu_0 * 1{D=1,H=0} + mu_1 * 1{D=0,H=1}`, unit query cost, and stopping time `tau<=B`. This is Li et al.'s finite-horizon sequential test with K=1 sensor (or K known observation channels if acquisition selects among sensors): minimize expected sample cost plus terminal decision loss, and optionally impose type-I/type-II constraints. A fixed adoption/switch charge can be included as an additional terminal cost for D=1. Therefore posterior-dependent query timing, sequential stopping, and a one-shot promotion decision are not novel even under a hard per-realization sample cap.

Li et al.'s multichannel version additionally optimizes sensor identity from the current posterior. Its per-sensor usage constraints are expectation constraints, but its finite horizon bounds the total number of samples pathwise. Its guarantee is Bayesian/simple-hypothesis and immediate-feedback, not the ShiftLab robustness contract.

## Exact points where that reduction fails for the full target

1. **Conditional-null adversary:** Li et al. specify IID laws under each hypothesis. ShiftLab's risk supremum allows each queried outcome's conditional success probability to depend on the full event-time past, including outcomes still pending at the learner. A single IID null distribution is not equivalent. The exact two-label example in `switching_causal_risk_planner_audit_v1.md` has an IID-calibrated promotion probability 1/4 but worst causal-null risk 1/2.
2. **Delayed observation clock:** Li et al. update the posterior immediately after each selected sensor sample. ShiftLab's learner reserves rights at query time but cannot use the outcome until its release time. Pending samples change which actions are feasible and what evidence is available. State augmentation can express this in a finite POMDP/game, but does not inherit Li et al.'s posterior-only recursion or theorem.
3. **Repeated economic control:** Their terminal decision is one stop/declaration. ShiftLab incurs running policy loss and costs for promotion and rollback, with latent regimes that can reverse. Bayraktar–Ludkovski cover known-model recurrent hidden-state economic switching, but not the robust null or paid delayed acquisition.
4. **Anytime repeated risk:** A terminal type-I error bound is not, by itself, a bound on any false promotion over repeated episodes. Weighted e-detectors and alpha composition supply established safety tools, but not the costed decision-regret theorem.

The reduction therefore succeeds for stationary one-shot subproblems and fails at the full information/risk/economic contract. Those failures are comparison obligations, not evidence of novelty: delayed constrained planning and robust partially observed games are already expressible by standard state augmentation and sequence form, albeit with exponential worst-case size. A candidate now needs a scalable structural theorem or a strict, proved frontier improvement over the combination of (i) optimal/near-optimal sequential sensor selection on the one-shot subproblem, (ii) a valid anytime test, and (iii) delayed robust constrained planning. A merely larger augmented-state DP or a custom LP encoding does not qualify.

## Decision and next gate

Reject one-shot adaptive acquisition/stopping as the contribution. Preserve the full delayed robust switching objective, but do not claim the remaining conjunction is an open gap. Before any prototype efficacy study, identify a nontrivial exploitable structure that yields a polynomial/controlled-complexity method and a bound relative to the finite extensive-form oracle, then audit that exact structure against robust POMDP/game algorithms. If no such structure survives, revise or stop the algorithm hypothesis; do not substitute the benchmark manuscript.
