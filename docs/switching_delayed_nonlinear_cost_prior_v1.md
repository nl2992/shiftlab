# Delayed feedback with switching costs: additional prior-art boundary

**Date:** 2026-10-28. This source read closes novelty claims about delay plus switching costs in general; it does not directly solve the ShiftGuard contract.

## Primary source inspected

Weici Pan, Guanya Shi, Yiheng Lin and Adam Wierman, “Online Optimization with Feedback Delay and Nonlinear Switching Cost,” arXiv:2111.00095v1. The [primary arXiv record](https://arxiv.org/abs/2111.00095) identifies the 2021 preprint. The cached PDF and extracted text are in `outputs/switching_source_audit_v1/online_delay_nonlinear_switch_cost.*`; provenance and SHA256 are in `switching_source_manifest_v9.json`.

## Theorem scope

The paper studies online convex optimization with a `k`-round delay in feedback about hitting-cost minimizers and a nonlinear switching cost that may depend on multiple previous actions. Under strongly convex/smooth hitting costs and a Lipschitz condition on the nonlinear switching map, Theorem 1 proves an `iROBD` competitive ratio bounded by an expression of order `O(L^2 k)` (with additional convexity, memory, and tuning factors displayed in the theorem). The paper also proves delay-dependence lower bounds. This is a competitive-ratio result for continuous control, not a pathwise-query-budget regret result.

## Mismatch and consequence

The source has delayed information and switching costs, but no selective paid-query decision, no hard cumulative observation cap, no paired counterfactual label, and no anytime false-promotion constraint. It measures performance against an offline control optimum under a structured smooth hitting-cost model. Thus it does not subsume our information structure. It does make clear that “delayed feedback + switching cost” is not itself a gap. A valid novelty delta must depend on the observation acquisition and finite-sample statistical-risk contract, and must beat a suitable adaptation of both delayed online learning and dynamic indicator-switching methods.
