# Markov state sensing costs: AISTATS 2026 prior audit

**Date:** 2026-10-29. **Status:** primary-source model and theorem audit; generic Markov state
sensing with recurring observation costs and truncation guarantees is occupied.

## Source and theorem checked

Kapoor and Nair, [*MDPs with a State Sensing Cost*](https://proceedings.mlr.press/v300/kapoor26a.html), AISTATS 2026, PMLR 300:1648–1656. The official PMLR PDF was downloaded and text-extracted; hash and provenance are in `switching_source_manifest_v26.json`. I inspected the model protocol and state expansion, Selective Policy Improvement (SPI), Theorem 4.1, and the state-truncation results in Theorems 4.2 and 4.4.

Their controller acts on a finite-state discounted MDP. At each step it selects an ordinary control and whether to sense the next state; a sensing action pays a fixed cost and reveals that next state, while a blind action leaves it hidden. The exact reformulation is a countable-state MDP whose state stores the last sensed root state and the sequence of blind actions since then. SPI improves a reference policy by searching for finite sequences of blind actions before sensing. Theorem 4.1 gives a sufficient condition under which always sensing is optimal. Theorem 4.2 bounds the loss from truncating the number of consecutive blind actions at depth `N` by `alpha^N k/(1-alpha)`. Theorem 4.4 gives a sharper computable gap and a sufficient condition for a truncated policy to be optimal in the full countable-state model.

## Contract mismatch

This is a genuine Markov sensing-cost control prior, but it has no pathwise total request cap, no delayed release queue, and no paired candidate-loss labels. Sensing directly reveals the latent Markov state; ShiftLab queries reveal a noisy common outcome, not the regime. Its objective is a single discounted cost law, not expected economic cost under an alternative HMM subject to any-promotion probability under a separate history-adaptive causal null. It does not model a deployment switch charge or anytime false promotion.

Therefore the source closes novelty from adding a Markov belief, a sensing-cost threshold, or a truncated look-ahead planner to the task. The truncation theorem is a relevant comparator concept, but substituting an observation queue and budget into its state would not prove ShiftLab's two-law risk constraint or a regret bound against its full-history oracle. A method contribution must establish a new bound for that precise interaction, not restate countable-state MDP planning with additional state variables.

## Decision

Continue G1 only for a reduction or separation against both the two-phase costly-bandit model and this Markov sensing-cost model. The remaining candidate class is recurrent hidden regimes with delayed, budgeted paired outcomes, reversible switching charges, and causal-null reachability control. No algorithm has passed this gate; G2–G5 remain held. Statistical evidence for a promotion remains separate from post-reversal current-value evidence.

## Primary source

- Kapoor and Nair (2026), [PMLR paper record and abstract](https://proceedings.mlr.press/v300/kapoor26a.html). The PDF cache path and SHA256 are recorded in `switching_source_manifest_v26.json`; inspected proofs were not independently reproduced.
