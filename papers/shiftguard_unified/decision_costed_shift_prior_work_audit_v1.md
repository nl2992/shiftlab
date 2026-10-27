# Decision-costed shift and selective-label prior-work audit v1

**Audit date:** 2026-10-26  
**Status:** targeted primary-source addition; not a systematic literature review and not a paper-faithful reproduction.

## 1. Decision-Making Under Selective Labels

Dennis Wei, “Decision-Making Under Selective Labels: Optimal Finite-Domain Policies and Beyond,” ICML 2021, PMLR 139, 11035–11046. [Publisher record and paper](https://proceedings.mlr.press/v139/wei21a.html).

The paper models individuals arriving online with IID feature/outcome pairs. The decision policy chooses whether to accept; a binary outcome is observed only after acceptance. The accepted outcome determines utility, and the formulation maximizes discounted total reward while accounting for the costs incurred during learning. The paper derives an optimal threshold policy in the homogeneous case, parallel policies for finite feature domains, and a classifier-and-bootstrap extension for general domains. Its experiments include synthetic and real data. These details make it a close precedent for utility-aware decisions when actions govern which labels become observable.

**What it already covers:** online decision-making under endogenous selective labels, explicit immediate decision rewards/costs, and the value of collecting outcome-bearing observations as part of a policy. Thus, a broad claim that ShiftLab first joins information acquisition and decision utility is untenable.

**What it does not establish for ShiftLab's registered tasks:** a sequential test for a paired deployed-minus-reference harm null; adaptation to a changing population or drift; time-uniform false-escalation control; delayed feedback; explicit retraining/switching/fallback budgets; or a gate that certifies a separately trained challenger. Its IID assumption and action-dependent observation mechanism differ from ShiftLab's randomized post-decision label queries. The paper is therefore a scope comparator and a candidate baseline only for a matched selective-label policy task—not a drop-in baseline for the current query-and-certify protocols.

**Required disposition:** cite it in the related work and keep the Q3 baseline question open. Include a task-matched implementation only if a registered task reproduces the accept/reject observation contract, the IID assumptions, and the same discounted-utility objective. Otherwise document the mismatch and do not compare its utility numerically with ShiftLab's query-cost or expected-regret metrics.

## 2. Decision-Focused Evaluation of Worst-Case Distribution Shift

Kevin Ren, Yewon Byun, and Bryan Wilder, “Decision-Focused Evaluation of Worst-Case Distribution Shift,” UAI 2024, PMLR 244, 3076–3093. [Publisher record](https://proceedings.mlr.press/v244/ren24a.html).

The paper studies predictive resource-allocation settings with combinatorial interactions. It introduces a hierarchical model for finding worst-case distribution shifts aligned to a downstream optimization task and formulates the resulting search as a submodular optimization problem. The paper's central empirical point is that shifts identified by conventional average predictive losses can differ from those that are worst for downstream decisions.

**What it already covers:** decision-aligned shift evaluation and the possibility that prediction-oriented shift/risk criteria do not identify decision-harmful changes. This is directly relevant to ShiftLab's separation of distributional change, predictive degradation, and decision harm.

**What it does not establish for ShiftLab's sequential tasks:** online monitoring, anytime-valid inference, delayed/selective label handling, comparison with a reference policy over time, intervention-cost allocation, or statistical certification of a replacement. Its setting is worst-case shift search for a structured allocation problem, not an eventwise decision-harm gate.

**Required disposition:** cite as a decision-focused shift comparator and sharpen the paper's distinction: ShiftLab's supported claim is about empirical sequential monitoring and adaptation behavior under explicit feedback contracts, not the first recognition that distribution shift should be evaluated through downstream decisions. A numerical baseline is warranted only if a ShiftLab task matches the paper's hierarchical resource-allocation and within/across-instance shift structure; the current scalar-policy synthetic profiles do not establish that match.

## 3. Effect on the contribution decision

These sources reinforce the existing **NO-GO for a new unified algorithm**. They do not supply the missing end-to-end combination of a valid decision-harm alarm, candidate certification, and constrained intervention, but they narrow each component's novelty space. At present, there is no publication-level gap demonstrated by simply combining policy-relative costs, selective labels, and shift evaluation. A benchmark/failure-analysis paper remains possible only if its contribution is differentiated by the controlled cross-method evidence and is supported by a sufficiently complete, task-valid comparator frontier. This audit does not close that frontier or justify a new experiment on its own.

## Primary-source facts checked

- Wei's publisher PDF states the IID arrival assumption, action-dependent outcome observation, and reward `a_i (y_i - c)` in the problem formulation (PMLR 139 PDF, pp. 1–2); its introduction explicitly describes the discounted-total-reward objective (p. 1).
- Ren et al.'s PMLR record states the downstream resource-allocation setting, divergence between predictive and decision-aligned worst-case shifts, hierarchical model, and submodular formulation.

