# Candidate B: policy-column generation pricing audit

**Date:** 2026-10-29. **Status:** exact reformulation PROVED; useful pricing
complexity and novelty UNRESOLVED. No implementation or efficacy claim.

## Exact restricted-master formulation

Let `P` be the finite set of deterministic, nonanticipating, hard-budget learner
policies over the original observation histories. Randomized policies are mixtures
of these policies using a private root lottery. For each policy `p`, let `c_p` be
its alternative-HMM economic cost and `r_{ip}` its first-promotion probability
against causal-null pure endpoint response `i`. The full problem is the finite LP

    min sum_p c_p z_p
    s.t. sum_p z_p = 1,
         sum_p r_{ip} z_p <= alpha for every null pure response i,
         z_p >= 0.

This is equivalent to the behavioral sequence-form program: perfect recall makes
behavioral randomization realization-equivalent to a root mixture over pure
contingent policies, and linear expected cost/risk depend only on that mixture.
The policy set and null-response set can both be exponentially large.

Given an active subset `I` of null responses, a restricted master has a valid
lower bound on the full optimum because it drops constraints. Its dual pricing
problem is to find a deterministic learner policy minimizing

    c_p + sum_{i in I} lambda_i r_{ip},

where `lambda_i >= 0` are the active risk-constraint multipliers, and compare that
minimum against the master normalization dual. If no policy has negative reduced
cost, the restricted master is optimal for the restricted constraint set; it is
globally optimal only after an exact full causal-null separation oracle also
certifies risk feasibility. Root mixing with a never-promote policy remains a
valid feasible upper-bound repair for any exactly evaluated candidate.

## Why this differs from the existing null-cut screen

`CAUSAL_CUTS_PROTOCOL_V1.md` uses a restricted null-response set but still
materializes every learner realization variable and information set before
solving each master. Policy-column generation would instead avoid the learner
sequence-form variable set, provided the reduced-cost pricing problem can be
solved without reconstructing an equivalent full history tree. The existing
diagnostic does not do this. Its T=5/6 runs needed 26/51 cuts, and at T=7 the
64-cut limit left a verified gap below 0.0725661; it remains a baseline.

## Pricing reduction and unresolved cost

For fixed dual weights, the pricing objective is an additive mixture of one
alternative-HMM cost and promotion-risk payoffs under the active null responses.
It can be represented as a partially observed finite-horizon control problem with
a hidden root mode selecting the alternative model or one active null response.
The learner receives only its original released labels. Under each null mode,
the transition law may depend on the null's full generated history, including
labels still pending for the learner. Thus the pricing belief must retain the
mode and enough latent null/alternative history and pending-label state to update
the learner's posterior and future rewards. A direct history-based dynamic program
has the same exponential policy-tree growth as the original learner polytope; a
belief-state implementation may merge states, but no bound shows that it does so
uniformly or compactly as the number of active cuts grows.

The critical missing lemma is a pricing algorithm with a provable state bound in
`T,B,d,|I|` that is smaller than the learner sequence form, while still evaluating
each active response under its correct hidden-history information. Without it,
column generation merely moves the hard search into the pricing oracle. An
approximate pricing oracle would additionally need a certified reduced-cost
error and a corresponding global lower-bound correction.

## Prior-art comparison

| Method | Relevant established result | What it does not yet give here | Status |
| --- | --- | --- | --- |
| Constrained-POMDP column generation | Walraven & Spaan generate policy columns via unconstrained POMDP subproblems and provide quality bounds for finite-horizon constrained POMDPs. | Their source model has a single-agent finite set of expected constraints; it does not supply a compact pricing state for a learner facing delayed labels and multiple history-adaptive hidden null responses. | Generic reduction relevant; exact adaptation unresolved. |
| Sequence-form double oracle | Bošanský et al. add sequences using best-response search without initially constructing the full extensive-form LP. | Their result concerns finite extensive-form games and best responses in the explicit sequence representation. Here the principal opportunity would be avoiding learner sequences through an implicit partially observed pricing DP; no such efficient oracle is supplied by the generic result. | Generic approach established; pricing complexity unresolved. |
| Robust finite-state controller synthesis | Cubuktepe et al. optimize robust controllers for uncertain POMDP specifications with exact verification and a finite LP after relaxations. | It does not prove an approximation gap against the unrestricted original policy class for a compact controller, nor a better pricing oracle for this causal-null game. | Strong comparator; source-matched adaptation required. |

Primary sources: [Walraven & Spaan, JAIR 2018](https://www.erwinwalraven.nl/publications/column-generation-algorithms-for-constrained-pomdps.pdf),
[Bošanský et al., JAIR 2014](https://doi.org/10.1613/jair.4477),
and [Cubuktepe et al., AAAI 2021](https://ojs.aaai.org/index.php/AAAI/article/view/17401).
The source-level comparison is scoped to the stated formulations and is not a
claim that no further related algorithm exists.

## Decision and next test

Do not implement a policy-column solver until the pricing DP is specified and its
state-growth advantage is justified. The next theoretical test, if pursued, is to
derive the exact latent state and Bellman recursion for a fixed set of active null
responses, then count reachable belief states versus learner realization
sequences on the registered T=5/6 cells. Continue only if this yields a genuine
compression and an exact or certified approximate pricing oracle. Otherwise,
retain this as a useful reformulation and proceed to Candidate C. No real-data,
synthetic-efficacy, novelty or speed claim follows from the LP equivalence alone.
