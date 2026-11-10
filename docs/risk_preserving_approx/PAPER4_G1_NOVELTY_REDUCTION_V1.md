# Paper 4 G1: formal reduction of the inversion-frontier certificate to robust-POMDP evaluation

**Date:** 2026-11-09. **Branch:** `research/paper4-value-shielded-causal-planning`.
**Close rule (fixed before reading, from `PAPER4_NOVELTY_AUDIT_NEGATIVE_INFLUENCE_V1.md` §5 G1):**
"If the inversion-frontier method is their Bellman evaluator plus pruning, CLOSE THE IDEA."

**Decision: CLOSE.** The inversion-frontier risk certificate is the Krale et al. (NeurIPS 2025)
nature-MDP best-response evaluator, specialised to a two-point extreme set, plus action elimination.
The one item not covered by prior work is an output-sensitive complexity bound. That is an analysis
question, not an algorithm, and nobody has proved it. It does not keep the idea open under the rule.

## Source read

Krale, Bovy, Galesloot, Simão, Jansen. *On Evaluating Policies for Robust POMDPs.* NeurIPS 2025.
Paper body read from the proceedings PDF, pp. 1–9 (Definition 1, the nature-policy assumptions in §2,
Theorem 3, Definition 3, Lemma 1, Corollary 1, Definition 4, Theorem 4).

Not fully read: Andriushchenko et al. (JAIR 2025), abstract only, which is synthesis, not
evaluation. Heck et al. (AAAI 2026) was blocked by the publisher's bot protection. Neither is
needed for the close decision, which rests on the evaluation step. Both remain relevant to any
synthesis claim.

## Mapping ShiftLab's causal null onto the Krale RPOMDP

| ShiftLab element | Krale et al. element |
|---|---|
| Causal null: conditional `P(Y_t = 1 | full past) = p_t in [0, 1/2]`, chosen adaptively | Interval uncertainty set, ⟨s,a⟩-rectangular, **dynamic** (zero stickiness) (§2) |
| Null sees its full past, including pending (unreleased) labels and public learner actions | Nature knows the history of states, agent memory states and agent actions (§2). Pending labels are part of the state |
| Fixed learner policy (controller memory / public history) | Agent policy `π = ⟨σ, τ⟩` with memory space `X` |
| Worst-case first-promotion probability of a fixed policy | Best-response nature `θ*_π = argmin_θ V^{π,θ}` for a 0/1 reachability reward with γ = 1 on a finite horizon (time encoded in state) |
| Recursion `v(h) = max{v(h0), (v(h0)+v(h1))/2}` | **Theorem 3:** a best-response nature exists that is Markov in `X` and picks only **extreme points** of the uncertainty set. Here the extremes are `p in {0, 1/2}`, and linearity in `p` gives the max-of-two form |
| Full adversarial evaluation over the response tree | **Definition 3 / Lemma 1 / Corollary 1:** the nature MDP on `S × X × A`. Finite `X` and polytope uncertainty give a finite MDP, and exact backward induction is the evaluator |

So Proposition A (`R_causal - R_IID = sum 2^-t [v(h0) - v(h1)]_+`) is an algebraic rewrite of the
value of Krale's nature MDP. It is measured against the stationary nature policy `p = 1/2`, which
Krale's §3.1 calls a naive/stationary nature class. The "inversion frontier" is the set of nature-MDP
states where the vertex `p = 0` strictly beats `p = 1/2`.

## The pruning component

Restricting computation to the inversion frontier means certifying, at the remaining states, that
`v(h0) <= v(h1)`, so that the vertex `p = 1/2` is optimal and the state contributes nothing to the
surcharge. That is dominated-action elimination in a finite MDP, a standard device (Puterman,
*Markov Decision Processes*, 1994). Where the event is monotone, `v(h0) <= v(h1)` holds everywhere
and the frontier is empty. ShiftLab already proved this exactly (`docs/switching_monotone_promotion_reduction_v1.md`).
The hull bound of Proposition B is stochastic domination. Under the pre-stated rule the method is
**the Bellman evaluator plus pruning**.

## What Krale et al. do not cover

These items are recorded so that the closure is not overstated:

1. **Two-law constrained optimisation.** Krale et al. evaluate one discounted reward under adversarial
   nature. They have no chance constraint, and no separate economic law (alternative HMM cost) next to an
   adversarial risk law. ShiftLab's IID-relaxation pipeline already handles that coupling with
   root-mixture repair (`IID_RELAXATION_CERTIFIED_PIPELINE_RESULTS_V1.md`), so it is not new to Paper 4.
2. **Complexity / output-sensitive bounds.** Krale et al. state none for evaluation. Their nature MDP is
   solved with MCTS in experiments. An output-sensitive bound for exact evaluation in terms of
   inversion-frontier size is **not proved** by them or by us. It would be an analysis of a known
   evaluator, and it is the only candidate contribution left.
3. **Private learner randomisation.** Krale et al. let nature know the agent's memory state. For a
   randomised controller with private memory, this makes their evaluation **conservative**
   (an upper bound on risk, a lower bound on agent value), which their footnote 2 acknowledges.
   This agrees with our counterexample (`check_negative_influence_identity.py`): averaging over
   private randomness is unsound, whereas letting nature see the coin is sound but conservative.
   It is a caution, not a contribution.

## Consequences

- The inversion-frontier certificate cannot be the Paper 4 contribution. It is retired as a component
  or baseline alongside value-sensitive pruning (`PAPER4_VALUE_SHIELD_DECISION_V1.md`).
- G2–G5 of the audit are **not run**, because the G1 exit has fired.
- Reopening would need a new pre-registered claim that is more than "evaluator plus pruning". For
  example, a proved output-sensitive bound with a family where the frontier is provably small while
  the nature MDP is provably large, plus a measured end-to-end win over the exact first-promotion
  decomposition. That is a separate research decision for the user, not a continuation of this one.

## Verification note

The mapping was checked against the paper text, not the abstract: the extreme-point property
(Theorem 3), the nature knowledge assumptions (§2), and the nature MDP construction (Definition 3).
Krale et al. phrase the objective as discounted reward maximisation. The 0/1 reachability event on a
finite horizon is a special case once time is in the state and γ = 1 on the finite tree. Their
γ < 1 contraction results (Theorem 4) are not needed for exact finite-horizon backward induction.
