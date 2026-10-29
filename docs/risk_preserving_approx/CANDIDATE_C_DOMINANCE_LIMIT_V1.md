# Candidate C dominance pruning: structural limit

**Date:** 2026-10-29. **Decision:** stop treating promotion-dominance pruning as
the main complexity mechanism. Its value/risk lemma is useful, but the current
pruning rule does not reduce the dominating pre-promotion history representation
on the checked cells.

## What the lemma removes

The registered rule compares an incumbent-only continuation upper bound `S(h)`
with a clairvoyant-future-state lower bound `L(h)` for immediate promotion. If
`L(h) >= S(h)-epsilon`, forbidding promotion at that information set preserves
the hard query cap and cannot increase worst-case first-promotion risk; it raises
alternative cost by at most epsilon. This is the established, model-specific
preprocessing baseline in `PROMOTION_DOMINANCE_RESULTS_V1.md`.

The rule removes promotion action variables and their post-promotion continuation
calls. It does not remove the information history `h` or its nonpromotion branch.
That branch remains necessary in the unrestricted comparison: the learner may
continue gathering information, and the causal null can condition future labels
on its full generated history, including pending labels. Eliminating those
histories would require an additional equivalence or approximation argument for
both laws; the promotion bound supplies neither.

## Evidence from the registered screens

At T=5,6,7, the exact screen marked 44/105, 93/236, and 172/469 histories as
strictly dominated. Integrating the restriction into the builder skipped 68,
132, 230, and 370 promotion-continuation calls at T=5,6,7,8 respectively. Yet
the pruned and reference builds had the same builder-node counts and the same
continuation-decision-cache sizes at every tested horizon. Fresh-process timing
was mixed: pruning was slower in some build/solve cells and faster in others.
The LP recovered the same small-cell cost and exact risk, but no compute advantage
or baseline win was established.

These observations falsify the claim that **this action-dominance rule, by itself,**
reduces the measured extensive-form history tree on these cells. They do not rule
out stronger lower bounds, a compact representation of nonpromotion histories, or
other pruning rules.

## Revised Candidate C requirement

A viable continuation must compact the pre-promotion state while retaining enough
information for:

1. alternative-HMM expected-cost prediction, including delayed pending outcomes;
2. all adaptive null responses that determine first-promotion risk; and
3. exact information available to the learner at each action.

The alternative posterior alone fails the recorded equal-posterior/different-risk
counterexample. A scalar risk budget is not known to repair this. Any state merger
must specify an equivalence or a quantified two-law error over *all* future
learner continuations and null responses. A candidate that only drops dominated
promotion columns cannot pass the computational gate if the shared history tree is
still built in full.

## Decision

Retain dominance pruning as a safe baseline and do not extend its epsilon sweep on
the same exposed HMM family. The next candidate must propose a pre-promotion
history abstraction with an explicit risk certificate, or an implicit optimizer
that avoids enumerating those histories. It must first be tested against the
posterior-alias counterexample and compared to the unchanged exact solver. Only
after that gate should a new synthetic scaling protocol or real-data replay be
registered. No real outcomes, seeds or holdouts were accessed in this audit.

## Provenance

Source evidence: `PROMOTION_DOMINANCE_PROTOCOL_V1.md`,
`promotion_dominance_screen_v1.json`, `PROMOTION_DOMINANCE_RESULTS_V1.md`,
`EARLY_PRUNING_RESULTS_V1.md`, and the branch-local history-alias counterexample
referenced in `PROBLEM_AND_THEOREM_TARGET.md`.
