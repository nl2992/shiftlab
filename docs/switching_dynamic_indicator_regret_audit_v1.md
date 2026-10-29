# Dynamic regret with indicator deployment costs: prior-art audit

**Date:** 2026-10-28. This source-level audit closes novelty claims about dynamic regret plus switching cost alone. It does not establish whether the remaining feedback/safety interaction is novel.

## Primary source inspected

“Dynamic Regret in Online Convex Optimization with Indicator Switching Costs,” arXiv:2609.30556 (September 2026 preprint). The [primary arXiv record](https://arxiv.org/abs/2609.30556) links the cached full text `outputs/switching_source_audit_v1/indicator_switching_dynamic_regret_2026.pdf`; exact PDF provenance is in `switching_source_manifest_v8.json`. I inspected the formal assumptions, Algorithm 1/2 descriptions, Theorems 5, 7, 12 and 14, and Corollary 13.

## Theorem scope

The paper studies online convex optimization on a bounded convex set with convex, smooth, Lipschitz losses revealed after the action each round. The learner pays a fixed indicator charge whenever its consecutive decisions differ. Its Algorithm 2 aggregates restarted lazy randomized FTRL learners across dyadic scales, with maximal coupling of successive proposal distributions. Theorem 12 gives strongly adaptive regret; Corollary 13 gives expected dynamic regret plus learner switching cost of order `O~(sqrt((S_T+1)T))` against piecewise-constant comparator paths; Theorem 14 also adapts to comparator path length. The algorithm does not need to know the comparator complexity in advance. It explicitly motivates model deployment and startup overhead.

Affine losses over the convex hull of two fixed policies satisfy the convex/smooth loss conditions (with zero Hessian), so this source directly covers dynamic economic tracking with model-switching overhead when complete loss functions arrive each round. That subcase is not a novel direction.

## Mismatch to the ShiftGuard contract

The source assumes a loss function is revealed every round, enabling full-information learner updates. It has no hard total query cap, no delayed paired-label queue, no query cost, no conditional-null/anytime false-promotion event, and no statistical restriction on when the learner can deploy policy 1. Therefore its theorem does not directly solve the current contract. Conversely, adding a sparse-sampling estimator, a delay buffer and a separate e-process to Algorithm 2 is only an ingredient composition until a new joint theorem or separation proves a nontrivial advantage.

This is a sharper baseline than static switching-cost regret: it already controls the same dynamic comparator and indicator deployment cost in a full-feedback special case. Any novelty statement must isolate what pathwise observation limitation and false-promotion control change jointly in the attainable utility/regret frontier, and compare against algorithms adapted from this full-information method as well as budgeted paid-observation methods.

## Research consequence

Close as occupied: (a) switching cost plus dynamic regret, (b) dynamic model selection with unlimited full feedback, and (c) generic budgeted observation plus switching-cost regret. Keep open only a theorem about the interaction of selective delayed paired feedback, pathwise query budget, repeated reversible model deployment and finite-sample global risk. Before coding a new controller, derive a minimax lower bound and a matching or meaningfully improved upper bound in one explicit regime; compare the candidate's rate and constants to standard sampling/delay reductions. If existing reductions attain the same frontier, revise the hypothesis.
