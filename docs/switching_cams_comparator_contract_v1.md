# CAMS under ShiftLab's delayed switching contract

**Date:** 2026-10-29. **Status:** comparator adaptation implemented and unit-tested; no efficacy result or theorem.

## Published method and target mismatch

CAMS (Liu et al., arXiv:2207.06030v4) receives each context and predictions, maintains exponential
weights over a finite contextual policy set (including constant classifiers), and queries with a
probability based on contextual classifier disagreement. A queried label reveals the current full
classifier loss vector and updates policy losses immediately. Its stochastic theorems assume IID
labeled contexts and gap/margin regularity; its adversarial theorems bound regret/query count with
immediate feedback.

ShiftLab instead selects a deployed action under the same stream but charges query and switching
costs, releases queried paired losses only after fixed delay `d`, and must reserve budget for labels
still pending. It also evaluates a separate worst-case causal-null event of any promotion. CAMS's
Algorithm 1 already has a budget gate, and its experiments report maximum query counts; hard query
limits alone are therefore not a gap. The gate does not specify a delayed pending-label queue.
CAMS's regret and query-complexity results do not cover delayed updates, costed deployment, or the
separate risk event. Its query-complexity theorem bounds expected query count, which differs from
the pathwise request-accounting contract.

## Fair comparator adaptation

Use a binary predictive classification development task for a direct CAMS comparison: each event
reveals the current context and both frozen candidate predictions; a query returns both 0–1 losses
on the common label. Run CAMS's contextual policy weights and disagreement-based query score, but:

1. Preserve the paper's query-probability gate and enforce an exact cap of `B` requests, reserving
   each right at request time so a pending label continues to consume budget.
2. Release queried loss vectors at exactly `t+d` and update weights only at release, retaining the
   original request propensity for inverse-propensity weighting.
3. Deploy the model recommended by the CAMS weighted vote at each event, charge the same fee `k`
   whenever it differs from the incumbent, and charge the same query fee at request time.
4. Log recommendation regret, realized predictive loss, query fees, switching fees, query count,
   and pending count separately. If a common safety layer is applied, report risk separately and
   apply the same layer to each method being compared.

This is a transparent delayed/hard-cap CAMS adaptation, not the published algorithm. It is
cost-oblivious in choosing its recommendation: switching fees are charged in evaluation but are
not fed back as a switching-aware optimization objective. A cost-aware extension would need to
define its stateful policy class and feedback vector explicitly, and is a further adaptation.

## Guarantee boundary

No CAMS regret, query-complexity, or safety theorem is claimed for this adaptation. Delaying the
importance-weighted updates changes the update filtration and estimator dependence. A cost-aware
extension that feeds the deployed model into the context would also create an endogenous context;
that is not part of the initial cost-oblivious adaptation. A theorem transfer would need to handle
the changed update timing and objective under the declared data assumptions. The causal-null
promotion event is a separate constraint and is not implied by regret bounds.

The binary classification restriction makes queried loss vectors and the published disagreement
score well-defined. CAMS is not directly applicable to arbitrary continuous paired-loss or finance
tasks without a separately justified response-space and acquisition-score adaptation.

## Comparator decision

Retain CAMS as an active-selection baseline for compatible binary synthetic tasks. Pair it with
the exact two-law oracle on small horizons and a risk-aware scalable baseline for safety comparisons.
Do not use the immediate-feedback theorem as evidence for the delayed/costed switching contract.
The implementation in `src/shiftlab/dive/hard_budget_delayed_cams.py` preserves the
cost-oblivious policy weights, weighted-vote recommendation and disagreement query score, while
queuing queried binary labels for fixed-delay updates and reserving requests at query time under a
pathwise cap. Four unit tests cover the delay, reservation, contextual experts, and submission
lifecycle. This is comparator plumbing only: it has no efficacy result, cost-aware rule, false-switch
guarantee, or inherited CAMS theorem. Because its update timing changes CAMS's estimator history,
even the uncosted published delayed-feedback claims are not asserted.
