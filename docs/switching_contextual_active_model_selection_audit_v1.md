# Contextual active model selection: source audit

**Date:** 2026-10-29. **Status:** primary-source theorem scope inspected; comparator required; no novelty conclusion.

## Source and theorem scope

Liu, Xia, Stevens and Chen, “Contextual Active Model Selection,” arXiv:2207.06030v4
([primary record](https://arxiv.org/abs/2207.06030),
[full text](https://arxiv.org/html/2207.06030v4)). I inspected the problem definition, Algorithm 1,
Theorems 1–4 and the experimental protocol.

The learner observes each current context and candidate classifier predictions. A finite set of
contextual model-selection policies, augmented by constant single-classifier policies, is evaluated
with queried full loss vectors. CAMS aggregates these policies by exponential weights and uses a
contextual disagreement score to set the label-query probability. Feedback is immediate in the
algorithm; the queried loss vector updates policy losses for the next event.

The stochastic results assume IID labeled contexts, a finite policy set, a unique best policy with
positive gap, a nonzero recommendation margin, and a regularized positive minimum policy probability.
Theorem 1 gives a high-probability constant pseudo-regret bound in those parameters; Theorem 2 gives
a high-probability bound on expected query count. The adversarial results allow an adversarial stream
and give a sublinear expected regret bound (Theorem 3) and expected query-complexity bound
(Theorem 4). The algorithm's query decisions are budget-gated, while the query-complexity theorem is
stated in expectation; it does not give delayed-feedback regret or a switching-cost result.

## Relation to ShiftLab

CAMS is direct prior art for active online selection among contextual predictors with queried labels,
including regret/query-complexity guarantees under stochastic and adversarial streams. This closes
generic “context-aware model selection plus active acquisition” as a novelty claim. Its setting
reveals all candidate losses for a queried event immediately, and its objective compares against the
best contextual selection policy or single model. Algorithm 1 already includes a query-budget gate,
and its experiments report maximum query counts. The inspected formulation does not include fixed
delayed label releases with pending-request reservation, repeated deployment charges, or anytime
causal-null false-promotion risk. Those differences are obligations to test reductions, not proof
of a gap.

For any later empirical study, adapt CAMS to request-time pathwise budget reservation and delayed
updates, then specify how its per-event recommendation is converted to a deployed switching action
with the same switching fee as the candidate. That adaptation must be labeled as such. The existing
Online LLM Picker adaptation is not a substitute for CAMS where contextual policies are available.
Neither CAMS nor its regret theorem certifies current challenger value after a regime reversal.

The explicit comparator protocol and theorem-transfer boundary are specified in
[`switching_cams_comparator_contract_v1.md`](switching_cams_comparator_contract_v1.md). Its first
adaptation is cost-oblivious when recommending actions; a cost-aware extension would require a
separate stateful policy and feedback definition.

## Decision

Retain CAMS as a required scalable active-selection comparator for compatible synthetic tasks.
Keep the exact two-law oracle and robust sequential-testing methods as separate risk-aware
comparators. Do not describe delayed feedback, switching charges, hard pathwise accounting, or a
causal-null wrapper alone as novelty. G1 remains unresolved; no new algorithm or theorem follows
from this audit.
