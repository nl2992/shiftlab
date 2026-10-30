# Non-partitioned PFA detector: formula execution and target mapping

2026-10-30. Previous goal turn: progress (SR/CUSUM panel committed). This continuation reads the stronger PFA construction and executes a bounded numerical formula pilot. Goal remains active; neither full baseline coverage nor a new mechanism is established.

## Primary construction

[Saha and Ramdas, Non-partitioned e-detectors for nonparametric sequential change detection](https://arxiv.org/html/2607.28322v1), Section2.2 Eq3–5 and Theorem2.3, Section3 Eq6, plus Section1 null/metrics inspected. Web retrieval initially timed out; official versioned HTML was retrieved directly, retained in ignored source cache and hashed. Standard-library HTML parsing was used; no new dependency was installed. Cached HTML and parsed text are source material, not published experiment artifacts.

Eq3 forms D_t=inf_R sum_{s<=t} pi_s M^R_{s:t}, where deterministic start weights sum to at most1, and thresholds at1/alpha. Theorem2.3 gives global PFA control for the exact construction with its restartable point-null e-process assumptions. Eq4's canonical infinite-horizon weighting has a logarithmic late-start penalty. This is not restricted to ARL. The earlier conservativeH/alpha experiment is only one finite-horizon choice, not exhaustive coverage of PFA methods.

For any true no-change R, D_t is dominated by the weighted process corresponding to that R. Validity does not follow by treating the pointwise infimum as a generic supermartingale; domination of the appropriate e-process supplies the argument. The family tests constancy of an unknown law, not membership in our one-sided conditional gain null.

## Registered formula pilot

Script check_nonpartitioned_pfa.py implements displayed Eq6 for sigma²=rho²=1 and Eq3's finite-support specialization pi_s=1/120 on the120 starts, zero afterward. This omits the infinite-horizon Eq4 schedule and is explicitly a finite-horizon example. Scalar logsumexp minimization uses the hull of the segment sample means; outside that hull every quadratic term points inward, so an optimizer lies inside. The objective is convex. Direct-sum arithmetic and1001-point grids at times30/60/120 independently check the numerical calculation. Constant-sequence results also match a closed form exactly.

Registration and output: nonpartitioned_pfa_registration.json and nonpartitioned_pfa_results.json. Source/script hashes recorded before computation. No author code has been located/verified for this paper in this continuation; this is a formula implementation, not a native-code reproduction or published-experiment replication.

| Path (120 observations) | Composite unknown-mean numerical crossing | Known-zero-mean crossing |
|---|---:|---:|
| Constant0 | none | none |
| Constant2 | none | 6 |
| One standard-normal null path | none | none |
| One normal path changing mean0 to2 after60 | 67 | 65 |

All crossings use threshold20. These four paths are smoke/target checks, not estimates of false alarms, power or detection delay. Constant0 and constant2 have the same final composite log statistic−1.812724, consistent with translation invariance. One may use a constant centered variable as sub-Gaussian with variance proxy1; it is not an invalid test case merely because its actual variance is0.

Numerical optimization is a crucial limitation: evaluating the objective at an approximate minimizer gives an **upper bound** on the mathematical infimum. Rejection based only on that numerical value can be anti-conservative. Dense-grid agreement and convexity do not provide a certified lower enclosure. Accordingly these numerical crossings are diagnostics only; no deployed PFA-valid implementation or theoretical certificate is claimed. A full implementation needs rigorously controlled minimization or a conservative lower-bound decision rule, stable mixture integration and the actual delay/query reduction.

## Applicability and boundary

A candidate can be beneficial at every event with no distributional change; the non-partitioned no-change null then holds while the operational benefit alternative is true. The constant2 example exposes that target distinction directly. Conversely a change in a nuisance covariate or in loss variance need not make the candidate useful. Therefore an unchanged no-change detector cannot be interpreted as a candidate-promotion certificate.

Disposition: **EXCLUDED_UNCHANGED_TARGET_FOR_PROMOTION**, while retained as a relevant change sentinel and mandatory prior art for aggregation/PFA claims. This does not exclude a sentinel-plus-paired-certification operational comparison, provided all uncertainty/budget/delay costs are charged. It does not show that a new composition is novel. Such a baseline must include always-beneficial streams, nuisance changes, harmful challengers and reversals, rather than evaluating only favorable post-change cases.

Main-text IID no-change laws differ from selective delayed-label event histories. AppendixA explicitly treats a Markov setting, so no blanket statement that the framework requires independence is justified. Full appendix proof mapping to our query/feedback contract has not been completed; arbitrary dependence is not inherited from that example. The nuisance target mismatch suffices to reject unchanged use as a benefit certificate without alleging a flaw in the published theorem.

## Research consequence

The fourth-round tradeoff remains: resets can help late onset but consume evidence/capital and do not certify future duration. This paper already supplies principled summable start weights and point-null aggregation. Novelty cannot rest on adding a restart mixture or replacingH/alpha with a time-varying start allocation.

Next finite obligations: certified operational implementation if this sentinel is compared numerically; source-level robust-FSC/CPOMDP synthesis mapping; truthful distinction between complete native reproduction and scoped adaptations. A new candidate must address action value or the information/cost coupling beyond these existing tools. No final real windows were read, no new≥500 count assigned to four formula paths, no paid/remote jobs or subagents.
