# Reyzin et al. (UAI 2026): costly-observation audit

**Date:** 2026-10-28. **Status:** primary-source model and selected theorem/proof sections inspected; no novelty claim.

## Source and results checked

Lev Reyzin, Aadirupa Saha and Shuo Wu, [“Expert Advice with Costly Observations,” UAI 2026, PMLR 337](https://proceedings.mlr.press/v337/reyzin26a.html). The accepted primary PDF was downloaded and extracted; byte count and SHA256 are in [`switching_source_manifest_v14.json`](switching_source_manifest_v14.json), and the local cache is `outputs/switching_source_audit_v1/reyzin26_costly_observations.pdf`.

I inspected the formal model in Section 2, Algorithms 1–2, Theorems 1, 2 and 4, Corollaries 3 and 5, and the corresponding Theorem 2 and Theorem 4 proofs. Each round, the learner selects a nonempty subset `S_t` of experts to observe, pays the sum of their known fixed costs, then plays an expert in `S_t` and immediately sees the selected experts' losses. Regret is against the best fixed expert with its per-round observation cost included. Losses are either adversarial or IID, depending on the section.

For adversarial losses, `m`-EXP3 samples a subset containing the played expert and uses importance-weighted losses. Theorem 2 bounds expected regret by a variance term of order `sqrt((K-1) T log K/(m-1))` plus `(m-1) p_bar T`; the selected observation size is a design choice. Corollary 3 optimizes this tradeoff. In the stochastic IID section, `m`-ELIM queries groups of up to `m` experts and obtains a gap-dependent bound with an explicit observation-cost term (Theorem 4, Corollary 5). This is direct evidence that adaptive costly observation and its allocation across alternatives are active, developed online-learning topics.

## Exact mismatch to ShiftLab

The paper does **not** impose a hard total count of labels. Its observation costs are paid every round and included in regret; observation feedback is immediate. The learner must play an expert from the subset it observed. The comparator is a single fixed expert, not a changing deployment path, and the results do not control a time-uniform false-promotion event. It does not include a pending-label queue, model-switch charges or a reversal decision.

Thus its results do not establish the target joint guarantee. They also rule out claims that cost-sensitive acquisition or adaptive allocation among experts is itself novel. A reduction from a hard query cap to a Lagrange-priced observation cost would need to preserve the pathwise cap, delays, comparator and risk event; a generic multiplier argument does not establish that. Any candidate must be compared against a cost-adaptive observation baseline under a justified common budget semantics.

## Research consequence

Add Reyzin et al. to the required prior-art comparison. Do not claim novelty from selecting which policy to query, optimizing an average query cost, or obtaining a gap-dependent acquisition rule. G1 remains open: a viable method still needs a theorem-level advantage under pathwise total paired-query budget, delayed releases and anytime-safe repeated deployment, with economically charged switches. No prototype or efficacy experiment follows from this audit.
