# Hidden-Markov optimal switching: source-level boundary

**Date:** 2026-10-28. **Status:** primary source inspected; rollback alone rejected as a novelty claim.

## Primary source and scope

Erhan Bayraktar and Michael Ludkovski, “Sequential Tracking of a Hidden Markov Chain Using Point Process Observations,” arXiv:0712.0413 (2008), later *Stochastic Processes and their Applications* 119(6), 1792–1822 (2009). The [arXiv source](https://arxiv.org/abs/0712.0413) was downloaded and inspected locally. Sections 1–4 formulate finite-horizon switching among a finite set of policies while a hidden finite-state Markov chain drives observed point-process characteristics. The controller filters the state by Bayesian updates, accrues state-dependent running benefits, pays state-dependent switching costs, and optimizes over observation-adapted stopping times. The authors characterize an optimal strategy by dynamic programming in posterior belief and policy state, and give a numerical scheme. The paper also discusses recurrent hidden states; this is not limited to one irreversible change.

This source covers the core economic primitive in our screen: recurrent latent regimes, Bayesian current-state beliefs, deployment-like policy choice, running value, and paid reversible switches. Thus “use a hidden Markov posterior to decide when to switch or roll back at a cost” is established optimal switching, not our contribution.

## What remains different

The source assumes a correctly specified hidden Markov observation model and continuous-time point-process observations. It does not formulate a hard pathwise budget for acquiring paired labels, a release delay with pending queries consuming budget, or a worst-case conditional-null false-promotion guarantee. Its posterior belief is used to forecast economic value and optimize control. It does not certify that a current intervention remains beneficial after a latent regime reversal under a robust null.

These distinctions are candidate comparison obligations, not an established gap. A candidate must show a theorem or strict finite instance separating it from this posterior-state dynamic program combined with standard risk-constrained testing and budgeted sensing. Adding a likelihood-ratio gate to model-posterior control alone does not pass: accumulated evidence may justify an initial promotion, while only fresh current-regime evidence can support benefit after reversal.

## Registered rollback-value diagnostic

Protocol: [`switching_rollback_value_pair_protocol_v1.md`](switching_rollback_value_pair_protocol_v1.md). Exact rational results: `outputs/switching_rollback_value_pair_v1/results.json`.

With T=6, B=3, delay 2 and alpha=0.1, the optimized test promotes with probability 2/5 only after the two early labels are both 1. Its worst-case promotion risk is exactly 1/10 across the eight endpoint causal-null kernels. In the recurrent symmetric HMM cell, enabling a one-time rollback at event 6 lowers expected cost by exactly 27114503/1953125000 (about 0.0138826); redesigning the promotion test recovers no further value. In the one-way no-reversal control, rollback changes cost by zero. Explicit hidden-world enumeration independently matches both posterior-recursion costs (8,192 worlds per controller/model cell). The randomized-test LP was solved numerically and the recovered policy was rationalized and rechecked; there is no dual certificate, so this is not a global-optimality certificate.

The result supports the intuition that reversals create some rollback value in this tiny setup, but it is a standard finite-horizon control effect under the assumed HMM. It neither establishes a useful algorithmic gain nor a novel guarantee. In particular, the HMM posterior used to predict action value is kept distinct from the null-risk calculation. A promotion-risk guarantee does not guarantee benefit after reversal, and evidence from an earlier regime cannot be reused as current-regime certification.

## Decision

Reject “reversible switching under hidden regimes” or “rollback adds value” as the novelty claim. Retain this result as a mechanism diagnostic and use Bayraktar–Ludkovski as a required comparator in future source-level novelty audits. G1 remains open; no broad efficacy or real-data evaluation is authorized by this screen.
