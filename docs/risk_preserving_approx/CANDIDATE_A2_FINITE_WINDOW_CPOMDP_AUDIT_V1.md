# Candidate A2: finite-window CPOMDP approximation source audit

**Date:** 2026-10-30. **Status:** related approximation theorem verified;
no direct transfer to the full causal-null risk objective. **Decision:** do not
implement the finite-window method as a lead without a separate risk-transfer
lemma and a demonstrated end-to-end size advantage.

## Source result

Zaccaria, Jordan, Ni, Susto and Kamgarpour, *Finite-Time Guarantees for
Constrained Reinforcement Learning under Partial Observability*, arXiv
preprint v1, submitted 2026-10-15, study an infinite-horizon discounted,
single-controller CPOMDP. The controller maximizes expected discounted reward
subject to an expected discounted cost bound. Their method replaces full
history by a length-`l` observation-action window, assumes uniform filter
stability, and derives policy-transfer and constrained-value bounds; its
tabular superstate count is
`O(|O|^(l+1) |A|^l)`. Their primal-dual result bounds average optimality gap
and average constraint violation across iterates.

Primary source: [arXiv:2610.21548](https://arxiv.org/abs/2610.21548), especially
Assumptions 1–2, Propositions 1–2, Theorem 1 and the complexity statement in
Section 4.

## Exact comparison with ShiftLab

| Component | Source result | ShiftLab target | Transfer status |
|---|---|---|---|
| Horizon and law | Infinite-horizon discounted single CPOMDP under one transition/observation model | Finite horizon; known alternative HMM for cost plus a separate full-history causal-null family | Not the same model |
| Constraint | Expected discounted cumulative cost under the controlled CPOMDP | Supremum, over causal nulls that see unreleased outcomes and public choices, of the probability of any first promotion | No direct risk or feasibility bound |
| Approximation state | Recent observed action-observation suffix; uniform filter stability controls current-state belief error | Any useful pre-promotion abstraction must also preserve how a null chooses future label probabilities from full generated history | Alternative-HMM filter stability does not control null-response memory |
| Guarantee | Approximate value/constraint bounds; primal-dual guarantee is on averages across iterates | One returned policy must meet a hard pathwise query cap and exact (or explicitly bounded) worst-case first-promotion risk, with value gap to the unrestricted optimum | Required output and comparator differ |
| Complexity | Tabular superstate memory/time is exponential in window length `l` | Must beat the exact extensive-form baseline in a declared regime while retaining the full null family | No advantage follows without a favorable `l` bound and risk-transfer theorem |

The model-specific alternative HMM may satisfy a useful filter-stability
condition under additional positivity/mixing assumptions. That only controls
alternative expected cost. It does not imply that histories with the same
recent learner-visible suffix induce the same null continuation: the null is
allowed to remember the full generated transcript and pending labels. The
branch's response-quotient lower bound constructs many such continuation-
distinguishable public transcripts. Thus applying the CPOMDP window result to
the alternative law and then calling the resulting controller safe would be an
invalid reduction.

An exact full-null verifier could check a particular finite-window policy, and
root mixing could make it feasible if a certified risk upper bound is available.
Those steps alone do not bound its cost relative to the unrestricted feasible
optimum. The missing quantity is a uniform value/risk transfer bound for
truncating learner policies while the null retains full-history adaptation.
The existing history-alias and response-quotient examples show why alternative
filter stability alone cannot supply it.

## Decision and next test

Classify the source as **relevant established finite-memory CPOMDP approximation**,
not a direct equivalent theorem for ShiftLab. No novelty claim is supported by
reusing its finite-window CMDP or primal-dual updates. Keep finite-window
planning only as an economic candidate generator if a later method proves a
uniform full-null risk/value repair bound and includes exact verification and
repair overhead. Otherwise leave Candidate A closed. No code, seeds, outcomes,
real data or holdouts were accessed in this audit.

The next candidate must address the implicit robust pre-promotion optimization
directly; a single-law alternative-model state approximation does not resolve
that bottleneck.
