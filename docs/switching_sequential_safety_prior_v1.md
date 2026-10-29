# Controlled sequential testing with sensing-switch costs: prior-art audit

**Date:** 2026-10-28. **Status:** primary source and targeted theorem/proof passages inspected; close prior, no novelty conclusion.

## Source and inspected scope

Prabhu, Bhashyam, Gopalan and Sundaresan, “Sequential Multi-hypothesis Testing in Multi-armed Bandit Problems: An Approach for Asymptotic Optimality,” IEEE Transactions on Information Theory 68(7), 4790–4817 (2022), [author arXiv version](https://arxiv.org/abs/2007.12961). I inspected the complete 53-page v2 source and read the model/policy statements, composite parameter hypotheses, error constraint, cost, Proposition 1 converse, and Theorem 4. I traced Proposition 6's Appendix D proof through its change-of-measure/modified-GLR bound to the `(M-1)L` union bound, and Proposition 7's Appendix E proof route through forced exploration, information-rate convergence and the expected-stopping-time argument. This is a fidelity audit of selected proof passages, not an independent proof verification. The cached PDF is `outputs/switching_source_audit_v1/prabhu22_sequential_multihypothesis.pdf`, SHA256 `ff99a61a70d3f956d3f2099ae9fab21801a1737c238f09a92d0ae933ccf5be8f`; provenance is recorded in source manifest v10.

## What is already established

The decision maker adaptively chooses one sensing arm per round from a finite set. Arm observations follow a stationary vector-exponential-family model with unknown parameters lying in one of several disjoint hypotheses. The controller may continue sampling or stop and declare one hypothesis. Admissibility requires the probability of a wrong terminal declaration to be at most `alpha` for every parameter in every hypothesis. The objective is expected stopping time plus switching costs between sensing arms:

`C(pi) = tau(pi) + sum_{l < tau(pi)} g(a_l, a_{l+1})`.

Proposition 1 gives the information-theoretic lower bound
`E[C | eta] >= d_B(alpha || 1-alpha) / D*(eta)`, where `D*` is the max-min relative-entropy information rate over sensing-arm allocations and nearest alternative hypotheses. Their sluggish, modified-GLR policy has a fixed threshold depending on `alpha` and the hypothesis count, and randomizes whether to keep the current sensing arm or change it. Proposition 6 establishes false-detection admissibility by a change-of-measure argument. Proposition 7 and Theorem 4 show that, under Assumption A and a continuous-selection condition, expected total cost divided by `log(1/alpha)` approaches `1/D*(eta)` as `alpha` tends to zero and the sluggishness parameter tends to zero. This is a strong prior result for generic active evidence acquisition, a sequential error constraint, and switching-cost-aware sensing.

## Contract comparison and novelty consequence

| Dimension | Prabhu et al. | ShiftLab target |
|---|---|---|
| Object being switched | Sensing arm used to obtain the next observation | Deployed prediction/model policy; acquisition is a separate query choice |
| Feedback | One selected arm's observation arrives in the sampling round | One query yields a paired common-outcome loss; fixed known release delay and pending-query queue |
| Environment | Stationary unknown parameter in a known exponential-family hypothesis class | Repeated or drifting regimes; current target includes arbitrary conditional-null safety and dynamic economic regret |
| Error event | One terminal hypothesis declaration, uniformly bounded by alpha over parameter points | Any promotion/re-promotion under a composite event-time conditional no-benefit null |
| Resource constraint | Expected stopping time plus sensing-switch cost; no hard total query cap | Pathwise total query cap counting pending requests, query price, and repeated deployment switching costs |
| Guarantee | Finite-alpha terminal error control; asymptotic expected-cost optimality as alpha vanishes | Target is finite-horizon utility/regret with anytime false-promotion control and useful reversal behavior |

The general premise “adaptively buy evidence, control a sequential error probability, and account for switching costs” is therefore occupied. A paper cannot nominate an e-process-plus-value-of-information-plus-switching controller as novel on that basis. Remaining possible deltas are substantially narrower: a finite-sample risk-regret frontier for *paired delayed* feedback under a *pathwise query cap*, while the costed switch is the deployment action, and with a repeated-switch comparator. Even that list is a specification gap, not proof of novelty. The theorem must beat a fair adaptation of this sequential-testing result where its stationary, terminal-decision assumptions apply, and the budgeted/delayed switching compositions already audited.

This source does not directly resolve the target. Its observations are not queued after a known delay, no pending labels or finite hard sample budget are modeled, the underlying parameter is stationary, and switches are among sensing arms rather than deployment policies. Its asymptotic criterion is not a finite-horizon dynamic-regret bound. These are concrete comparison dimensions; they do not on their own establish a contribution.

## Decision

Add this paper as a mandatory baseline in G1. Treat one-shot stationary known-family cells as a required reduction test: the proposed rule should recover or improve on the modified-GLR sensing allocation after matching observation and switch-cost semantics. Do not launch efficacy experiments or claim novelty until that comparison and the joint delayed-budget-risk frontier are derived. G1 remains open; G2–G5 remain unmet.
