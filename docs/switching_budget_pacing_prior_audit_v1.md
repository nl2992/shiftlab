# Budget-pacing online-learning prior audit

**Checked:** 2026-10-29. **Status:** primary-source boundary, not a method claim.

## Source and verified theorem scope

Braverman, Liu, Mao, Schneider and Xue, [*Optimally Pacing Budget Spending and Learning*](https://arxiv.org/abs/2610.11074), arXiv v1 submitted 2026-10-08. The full 38-page primary PDF was inspected. Theorem 4.6 gives near-optimal regret against a class of D-pacing experts under hard resource constraints; the rate is `O((sqrt(T)+D)*sqrt(log F))` in the online-learning-with-resource-constraints regime and `O(D*sqrt(log F))` in the online-resource-allocation regime, under their stated bounded reward-to-cost ratio and feedback assumptions. Theorem 5.8 / Corollary 5.9 extend the sampled full-information version to pathwise budget feasibility and high-probability regret, with an explicit sampling-concentration penalty. Their algorithms jointly control reward regret and cumulative spending deviation with a potential argument.

The formal OLRC model has resource-consuming actions, bounded reward and cost vectors, experts with advice distributions, a hard resource budget, and a null action after a conservative hard stop. In the full-information variant the complete reward/cost vectors are observed; in bandit feedback only the selected action's reward/cost is observed. No delayed-label process or anytime false-promotion event appears in the source's protocol/theorem statements. The guarantees target pacing experts; they do not target a recurrent switching comparator with query-dependent information.

## Relation to the ShiftLab contract

This result closes any proposed novelty based solely on a hard budget, an adaptive spending/pacing rule, a resource shadow price, or online learning against spending-pattern experts. It is also a useful comparator-design reference: a baseline must specify how its pacing class and spending deviation relate to query opportunity.

It does not directly solve ShiftLab's information-acquisition problem. Here a query is a resource-consuming observation whose unknown label arrives after a fixed delay; the learner cannot observe the current reward vector before choosing whether to query. The hard cap counts both resolved and pending labels at request time. The learner must also control the probability of any false promotion under a history-adaptive conditional null, while measuring recurrent deployment loss and switching cost. These distinctions are a source-level reduction obligation, not evidence that the combined problem is novel.

Most relevant existing overlaps remain stronger on the component problems: Cheng et al. characterize observation-budget regret with switching costs for a fixed comparator, and established delayed online-learning reductions handle feedback delay under their own regret/feedback models. The remaining methodological target, if pursued, must prove a substantive joint result in which selective delayed labels change the safe switching frontier under the declared conditional-null event. Merely adding a pacing potential, an e-process, a delay buffer, and a switching penalty is not a novelty claim.

## Decision

Do not prototype a budget-pacing wrapper from this source. Keep it in the mandatory baseline/prior boundary. G1 remains unresolved: seek a theorem-level result about the interaction of delayed information acquisition and an anytime conditional-null switching constraint, or revise the hypothesis if the strongest such rule reduces to standard controlled sensing plus risk-constrained planning. G2–G5 stay held.
