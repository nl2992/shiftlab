# Online active model selection: comparator audit

**Date:** 2026-10-29. **Status:** primary-source scope checked; no novelty conclusion.

## Source and verified scope

Turrin, Okanovic, Hoefler and Gürel, “Which LLM to pick? Online Active Model Selection for
Large Language Models,” arXiv:2610.01592v1, submitted 2026-10-01
([primary arXiv record](https://arxiv.org/abs/2610.01592),
[full text](https://arxiv.org/html/2610.01592v1)). Sections 1, 3.1–3.2 and 4.3 were inspected.
The paper considers an incoming prompt stream, multiple candidate LLMs, a limited annotation
budget and selective oracle labels. Its Online LLM Picker maintains a posterior over the best
model, uses importance-weighted observed losses with exponential weights, and chooses query
probabilities using hypothetical committee-loss variance and posterior entropy. Its objective is
cumulative regret to the best single model over the full stream, and it reports annotation
efficiency and best-model identification. The evaluation draws IID prompts uniformly from each
test set for each realization. Although the problem statement calls `b` a maximum annotation
budget, Section 4.3 says hyperparameters are tuned so methods query the same number of annotations
**on average**; the tested protocol therefore does not verify pathwise budget feasibility.

## Relation to ShiftLab

This is a close comparator for online active model selection under limited labels. It rules out
claims that online streams, selective annotations, uncertainty-guided acquisition, or identifying
a best model under a label budget are new by themselves. The inspected formulation does not state
fixed delayed label releases, a pathwise hard cap that counts pending requests, repeated reversible
deployment with switching charges, or a global anytime causal-null false-promotion constraint.
These are contract differences and obligations for a theorem-level reduction, not evidence of an
unoccupied gap. The empirical baseline should be adapted to reserve a pathwise query budget and
update only on released labels before it can serve as a matched ShiftLab comparator. The paper also
does not provide a current-value certificate after a regime reversal.

## Decision

Retain Online LLM Picker as a required active-model-selection comparator where its prompt/loss
feedback can be adapted fairly. Do not nominate horizon-aware VOI, committee uncertainty, posterior
entropy, or active online model selection itself as the contribution. G1 remains unresolved. For
empirical comparison, use a hard-budget, delay-aware adaptation, and label it as an adaptation rather
than a faithful reproduction of the paper's average-budget, immediate-feedback protocol. Any future
rule must state a strict mathematical advantage over this family and the closer delayed POMDP,
controlled-sensing, robust sequential-testing and two-law constrained-game baselines.

Historical test-epoch evidence does not certify current challenger benefit after reversal; current
economic value needs contemporaneous evidence or an explicit persistence model.
