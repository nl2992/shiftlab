# Reward–detection control prior: two-threshold switching is established

**Date:** 2026-10-28. **Status:** primary-source mechanism audit; no novelty or equivalence claim.

## Source and inspected scope

Banerjee, Liu and How, [*Quickest Change Detection Approach to Optimal Control in Markov Decision Processes with Model Changes*](https://arxiv.org/pdf/1609.06757v2), arXiv:1609.06757v2 (2017; ACC 2017). I inspected the primary seven-page PDF's formal model, POMDP reduction, Shiryaev/SR/CUSUM statistics, Section V two-threshold controller, multiple-change discussion and numerical-comparison description. This was a source-level mechanism and contract read, not a full proof audit; the paper does not state a theorem for its two-threshold controller in the inspected version.

## Exact overlap

The paper considers nonstationary MDPs whose transition or reward model changes. In its Bayesian formulation, the change point has a prior and the controller maximizes discounted reward. Its two-threshold rule uses the reward-optimal policy while the change statistic is below a lower threshold, an information-maximizing policy between thresholds, and the post-change reward-optimal policy above the upper threshold. It explicitly returns to the reward-optimal policy if the statistic falls below the lower threshold. The paper also describes repeating a change-detection procedure across multiple changes when changes are sufficiently separated.

This directly occupies the broad mechanism “trade reward for information in an intermediate regime-belief band, then switch policies when evidence crosses a threshold.” Replacing its information-maximizing action with a query policy, adding a reserve variable, or adding rollback is not by itself a novelty delta. Standard posterior control with reward/detection thresholds and repeated changes must be included in any close comparison.

## Contract boundary

The audited model observes the state-action process each step and optimizes a Bayesian discounted-reward or a separate regime-performance criterion. The source does not give a pathwise total cap on paid common-outcome labels, delayed label-release queue, per-query fee, deployment switch fee, or a finite-horizon probability bound on any false promotion under a history-adaptive conditional-mean null. Its repeated-change passage assumes enough separation between changes and is not a hard-budget finite-sample guarantee. These are unresolved reduction obligations, not evidence that their conjunction is unoccupied.

For ShiftLab, one common queried outcome scores both candidate policies and its law is action-independent. Thus there is no choice among action-dependent observation channels of the type used by the paper's information-maximizing control. The relevant acquisition decision is when to spend a pathwise query right, accounting for pending releases, useful remaining horizon and possible future reversals. Any candidate must state an information structure where this decision yields a proved gain over the two-threshold reward/detection rule, budgeted sequential design and the exact causal-risk planner on small instances.

## Research decision

Reject generic reward-versus-detection thresholding as the proposed contribution. Retain the two-threshold policy as a mandatory conceptual baseline for future current-regime monitoring and switching work. A viable continuation needs a source-audited theorem for the delayed, costed, pathwise-budget and robust-null interaction; if a standard constrained-POMDP wrapper supplies it, revise the method hypothesis instead of adding another controller layer. Promotion validity under the causal null remains separate from evidence that the deployed model is beneficial in the current regime after a reversal.
