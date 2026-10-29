# Partially observed risk-probability games: primary-source audit

2026-10-28. **Status:** close control-theoretic prior audited at source level; no novelty
conclusion for the full ShiftLab contract.

## Source and inspected scope

Wen, Xia and Yu, “Finite-Horizon Partially Observable Semi-Markov Games with Risk Probability
Criteria,” [arXiv:2508.17791](https://arxiv.org/abs/2508.17791) (2025 preprint). The complete
29-page v1 source was downloaded. I inspected its problem statement, finite-horizon game model,
information available to each player's policy, state augmentation by the joint posterior of the
hidden state and remaining payoff goal, and its comparison/Shapley-equation and equilibrium
results. This is a scope and fidelity audit, not an independent proof verification.

The paper studies a two-player zero-sum partially observed semi-Markov game. Players choose
actions based on the observable history and a common conditional distribution over the hidden
state and remaining goal. One player maximizes the probability that accumulated reward reaches a
target by a finite horizon; the other minimizes it. The paper derives a belief/goal-augmented
fully observed game, comparison result, Shapley equation, value existence and Nash equilibrium.
Its time/event-driven semi-Markov setting is broader than an immediate-feedback discrete POMDP.

## Comparison with ShiftLab's risk contract

This result rules out novelty from the broad ingredients “partially observed control + an
adversarial player + a finite-horizon probability objective,” or from augmenting a belief state
with a remaining threshold and solving a small game. A reachability event such as any promotion
can be represented as terminal accumulated reward, so the probability objective is a close
mathematical neighbor to a finite-horizon false-promotion constraint.

It does not directly prove our target. In the paper, both players condition on the same observable
history and common belief. In the causal-null contract, the environment may condition its next
outcome law on the complete event-time history, including queried outcomes still pending from the
learner's perspective; the adversary can therefore have strictly more information. Its objective
is a model-based terminal threshold probability in a zero-sum game, while ShiftLab maximizes
expected economic utility under a worst-case conditional-null *anytime* promotion constraint.
The paper does not impose a pathwise query cap or charge query and repeated deployment switches,
and it does not compare against a dynamic switching oracle or prove delayed-feedback regret.

These differences are not themselves a novelty argument. The exact causal-game LP already uses
the standard extensive-form approach to the stronger information asymmetry, but only at tiny
horizons. A method cannot claim a new risk-constrained POMDP or risk-probability game. The remaining
G1/G2 burden is a scalable algorithm and a nontrivial theorem (or strict lower/upper frontier
separation) exploiting the joint conditional-null, pending-query, pathwise-budget and repeated
economic-switch structure, with the 2025 game as a mandatory comparison in its common-information
subcase and the causal LP as the stronger small-instance oracle.

## Provenance and decision

The PDF and extracted text are cached under ignored `outputs/switching_source_audit_v1/`. Their
byte counts and SHA256 hashes are recorded in `switching_source_manifest_v12.json`. Continue G1;
no efficacy experiment follows from this audit. The 2024 Wen–Guo–Xia decision paper remains
abstract-only in manifest v12 and must not be described as a proof-level read.
