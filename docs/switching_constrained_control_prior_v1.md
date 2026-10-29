# Constrained partially observed control and probability-risk prior audit

2026-10-28. **Status:** source-level scope audit; generic constrained planning is occupied.
No novel algorithm or unoccupied gap is claimed.

## Sources and verified scope

Helmeczi, Kavaklioglu and Cevik, “Linear programming-based solution methods for constrained
partially observable Markov decision processes,” [arXiv:2206.14081v2](https://arxiv.org/abs/2206.14081).
The full 42-page v2 source was downloaded and extracted. I inspected its problem description,
Sections 3.3 and 3.2.2 and the finite-horizon formulation. Its objective maximizes expected
finite-horizon reward subject to an expected cumulative resource-cost budget. It presents
belief-state/occupancy LP formulations and approximate grid-based methods; the source expressly
describes the exact model as intractable. This is a source-text scope audit, not independent
verification of the approximation analysis. The main source equations use expected cumulative
cost, so they do not establish pathwise hard-budget feasibility.

Wen, Guo and Xia, “Finite horizon partially observable semi-Markov decision processes under risk
probability criteria,” Operations Research Letters 57, 107187 (2024), [publisher record and
abstract](https://www.sciencedirect.com/science/article/pii/S0167637724001238). The publisher
abstract and model/result summary were accessible, but the full paper was not. They optimize a
finite-terminal probability criterion for accumulated rewards relative to a profit target, augment
the state with the joint conditional distribution of the hidden state and remaining goal, and
establish an optimality equation and existence of an epsilon-optimal Markov policy. This supports
the existence of probability-risk control for partially observed finite-horizon systems; exact
overlap with our global-null false-promotion event is unverified, and this is not a proof-level
audit of their paper.

## Consequence for ShiftLab

The following cannot be presented as the methodological contribution by themselves: casting
querying, deployment and rollback as a belief-state POMDP; including a finite query/resource
budget; solving a small instance by dynamic programming or sequence-form LP; randomizing among
policies to meet one scalar risk constraint; or adding a terminal probability-risk objective.
These are established control/optimization patterns. Our finite causal-game reference is a tiny
exact benchmark under a known alternative and an adversarial conditional-null opponent, not a new
planning method.

The formal contract still has material differences that require precise treatment rather than
being declared a gap. The CPOMDP source constrains expected resource use, whereas ShiftLab counts
every requested label immediately against a pathwise cap. The risk-probability paper's accessible
summary describes terminal accumulated-profit risk under a specified model; ShiftLab's proposed
statistical constraint is a worst-case probability of any promotion over a conditional-null family,
at every time, and is separate from alternative-regime economic utility. Delayed paired outcomes,
pending requests, repeated reversible deployment, and a dynamic switching comparator must all be
represented in the same causal filtration.

Thus a generic constrained-belief planner has no novelty claim. G1 now requires a theorem-level
separation from (i) ordinary constrained POMDP / terminal risk planning where its model applies,
(ii) an anytime-valid test composed with the strongest delayed hard-budget switching method, and
(iii) the exact small causal-game reference. A viable contribution must give a scalable acquisition
and switching rule with a finite-sample, worst-case anytime risk guarantee and a strictly better
utility/regret guarantee in a nontrivial declared regime. If no such separation exists, revise the
research hypothesis. No new efficacy experiment is justified by this audit.

## Provenance

The CPOMDP PDF and extracted text are cached in ignored
`outputs/switching_source_audit_v1/cpomdp_budget_lp_2022.{pdf,txt}`. Their byte counts and hashes,
plus the publisher URL/status for the risk-probability paper, are recorded in
`switching_source_manifest_v11.json`. The latter full text remains an explicit source-access gap.
