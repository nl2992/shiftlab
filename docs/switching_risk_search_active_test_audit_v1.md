# Risk-aware search and cost-aware active testing: source audit

**Date:** 2026-10-28. **Status:** primary-source scope checked; no novelty conclusion.

## RAO*: chance-constrained POMDP search

Santana, Thiébaux and Williams, *RAO*: An Algorithm for Chance-Constrained POMDPs*, AAAI
2016, [official paper](https://ojs.aaai.org/index.php/AAAI/article/view/10423). The full seven-page
primary paper was inspected. Section 2 defines finite-horizon partially observed control and a
whole-execution path-violation probability constraint. Equations (6)–(12) give an exact backward
execution-risk recursion; Section 2.2 derives forward risk-budget bounds; Section 4 presents
heuristic belief-space search with reward and admissible risk heuristics that prune infeasible
branches. The paper explicitly targets optimal deterministic finite-horizon policies satisfying
the chance constraint.

This closes novelty from generic “finite-horizon risk-constrained policy search,” explicit risk
propagation, or risk-based tree pruning. Its environment is a known stochastic POMDP; the audited
formulation does not provide ShiftLab's worst case over causal conditional-null kernels with
pending outcomes hidden from the learner, a pathwise total query cap including pending labels, or
delayed label release. Those are exact reduction and comparator questions, not novelty by
themselves. The registered causal-game LP already supplies a stronger small-instance oracle;
using RAO*-style search as its scalable shell would still need a new guarantee and a demonstrated
advantage over robust constrained planning.

## Active sequential testing with heterogeneous acquisition costs

Vershinin, Cohen and Gurewitz, *Active Sequential Hypothesis Testing with Non-Homogeneous Costs*,
arXiv:2509.11632 (2025), [primary preprint](https://arxiv.org/abs/2509.11632). The source's system
model, cost-aware design derivation, main theorem and appendix argument for its objective bound
were inspected. It considers a finite hypothesis set and actions with heterogeneous positive
sampling costs. Under an average decision-error constraint, its cost-aware Chernoff scheme selects
experiments using a ratio of expected discrimination to expected cost and retains logarithmic
error dependence in its stated asymptotic regime. The paper explicitly shows that simply
maximizing per-action information-per-cost can be suboptimal.

This closes novelty from generic cost-aware active evidence acquisition or an information-per-cost
heuristic. It does not treat a pathwise hard total label cap, delayed feedback, a causal conditional
null and anytime promotion event, or repeated costed deployment/rollback. Again, the mismatches
create comparison obligations, not an unoccupied method claim. The reported guarantee is for its
sequential hypothesis-testing problem; it is not transferred to model switching.

## Partial feedback with deployment switching costs

Rangi and Franceschetti, *Online Learning with Feedback Graphs and Switching Costs*, AISTATS
2019, [PMLR paper](https://proceedings.mlr.press/v89/rangi19a/rangi19a.pdf). The full ten-page
primary paper was inspected, including its feedback-graph protocol, Algorithms 2–3 and Theorems
5–6. It gives expected-regret and switch-count bounds for threshold-based EXP3 under partial
feedback graphs, as well as an alternative EXP3.SC method. The selected action determines which
losses are observed through the graph; the feedback graph may vary over time and may be revealed
only after the action.

This is direct prior art for adapting action distributions to partial feedback while controlling
deployment switches. Its labels are free side observations induced by the played action, and its
comparator is the best fixed action in expected regret. It does not impose paid label requests, a
hard pathwise query cap, delayed feedback, or a false-promotion probability constraint. These exact
mismatches must be handled in any reduction; simply adding a query price and an e-process to a
switching-cost learner would not itself establish novelty.

## Gate impact

Alongside the previously audited robust and chance-constrained POMDP methods, these sources leave
no credible generic algorithmic delta in combining risk-aware search, cost-aware sampling and
deployment switching.
The monotone-event utility counterexample in
[`switching_monotone_class_separation_v1.md`](switching_monotone_class_separation_v1.md) rules out
the current easy risk-compression route over signed reversal-predictive alternatives. The broad
G1 problem therefore remains unresolved. A next candidate must identify a restricted but
scientifically defensible dynamic alternative class and a theorem beyond these methods, or the
research hypothesis should be revised before implementation or efficacy studies.
