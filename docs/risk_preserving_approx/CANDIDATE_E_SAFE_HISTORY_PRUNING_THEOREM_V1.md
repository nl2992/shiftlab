# Candidate E: safe continuation at selected rare histories

**Registered:** 2026-10-29. **Status:** risk/value lemma PROVED conditionally;
policy-independent envelope and useful complexity advantage UNRESOLVED. This is
a bounded theory screen, not an efficacy result or novelty claim.

## Construction

Keep the complete learner public history, delayed-feedback order, query budget,
and unrestricted full-history causal null. Select a set `S` of pre-promotion
learner information histories. At the first visit to any `h in S`, force the
learner to keep the incumbent, make no further query, and never promote for the
rest of the horizon. Outside `S`, use the original policy class. Denote the
result of applying this transformation to policy `pi` by `pi^S`.

Assume each event's total economic cost is in `[0,L]`. Let
`p_S(pi) = P_alt^pi(first visit to S by T)`. The public histories in `S` must
still be specified using only learner-visible actions and released outcomes;
pending labels remain hidden from the learner. The alternative probability is
computed under the true HMM and request-time chronology.

## Conditional theorem

For every policy `pi` and every causal-null strategy `nu`:

1. `R_null(pi^S, nu) <= R_null(pi, nu)`. Therefore
   `R_null(pi^S) <= R_null(pi)` for the supremum over the unrestricted null.
2. `C_alt(pi^S) <= C_alt(pi) + L T p_S(pi)`.

If the selected set has a policy-uniform envelope
`sup_pi p_S(pi) <= epsilon`, and the restricted two-law problem over policies
that take the safe continuation at `S` is solved exactly, its optimizer `pi_S`
is feasible whenever the original optimum is feasible and satisfies

`0 <= C_alt(pi_S) - V* <= L T epsilon`.

**Proof.** Couple `pi` and `pi^S` with the same learner randomization and null
randomization. Their interaction is identical until the first visit to `S`.
On paths that never visit `S`, both promotion indicators and costs agree. On a
path that visits `S` before any promotion, `pi^S` cannot promote afterward,
whereas `pi` may; pointwise the modified first-promotion event is a subset of
the original event. This holds for each history-adaptive `nu`, so it survives
the supremum. On a path entering `S`, at most `T` event costs differ and their
per-event difference is at most `L`; elsewhere costs agree. Taking expectation
gives the cost inequality. Apply the transformation to a feasible full optimum
`pi*`: `pi*^S` is feasible and lies in the restricted class, so the restricted
optimum is no worse than `C_alt(pi*^S)`. Since it is also a feasible original
policy, its cost is at least `V*`, proving the interval.

The lemma does not itself provide an efficient way to choose `S` or certify a
small policy-uniform `epsilon`. For an information history `h`, a simple
policy-independent envelope is the exact alternative likelihood of its
released-label transcript conditional on its fixed action/query history,
because the probability of the learner taking that action history is at most
one. A union bound over a prefix-free set `S` is valid but may be loose. A
useful algorithm must compute such an envelope without first building the full
learner/null history tree, or show that pruning reduces solver resources after
including envelope construction.

## Counterexample coverage

- **Posterior aliasing:** no histories are merged; the risk-relevant public
  transcript is retained outside the explicitly forced-safe set. The
  transformation is a restriction with a certificate, not a belief quotient.
- **Signed future value and rollback:** no monotonicity assumption is used.
  The `LT epsilon` regret bound covers every continuation cost, including
  rollback, re-promotion, pending-label costs and switching charges, provided
  each event's total cost lies in `[0,L]`.
- **Null information:** the null may still use the full generated history and
  pending outcomes. The risk argument is pointwise pathwise under the same null
  strategy until entry into `S` and then removes promotion opportunities.

## Prior-art boundary and decision

RAO* already uses admissible execution-risk heuristics to prune overly risky
branches in chance-constrained POMDP search. POMDP hypothesis-pruning work gives
value-loss bounds for discarded hypothesis mass. Therefore safe pruning, bounded
cost loss, or exact risk verification alone are not novelty. The candidate-specific
question is whether an **alternative-law public-history reach envelope** can
prune a two-law switching sequence game while keeping the full adaptive-null
response model exact, with an end-to-end benefit over the exact decomposed LP and
the best calendar/sequential-test baselines.

Decision: permit one preregistered development-only envelope/tree-size screen.
Do not build a solver or claim a method unless the screen finds a nontrivial
pruning set at a useful certified cost tolerance and the source-matched audit
finds a precise gap from existing pruning methods. Synthetic holdouts and real
data remain closed.

Primary sources inspected: Santana, Thiebaux & Williams, [RAO*: an Algorithm for
Chance-Constrained POMDPs](https://dspace.mit.edu/entities/publication/839ffa98-84e4-4d87-8b3d-1499a1f5cdcb);
Barenboim et al., [Data Association Aware POMDP Planning With Hypothesis Pruning
Performance Guarantees](https://anpl-technion.github.io/Publications/Barenboim23ral2.pdf).
