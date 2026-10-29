# Costly observations with correlated arms: two-phase prior audit

**Date:** 2026-10-29. **Status:** primary-source audit; generic cost-aware acquisition and
explore-then-commit structure are occupied. This does not resolve the full ShiftLab objective.

## Source and verified result

Schur, Lago and Fiez, [*The Price of Knowledge: Optimal Algorithms for Costly Bandits*](https://proceedings.mlr.press/v337/schur26a.html), UAI 2026, PMLR 337:6064–6090. The official PMLR PDF was downloaded and text-extracted; byte count and SHA256 are in `switching_source_manifest_v25.json`. I inspected the round protocol, Lemma 1, its Appendix B.1 proof, the cost-adjusted information-gain definitions, Algorithms 1–2, Theorems 4–7, and the discussion contrasting hard-budget bandits.

The model has a stationary unknown reward function `f(x)` with independent mean-zero sub-Gaussian noise. Each round the learner picks `x_t`, then either pays its known action-dependent observation price `c(x_t)` to see the reward or skips it. Cost-aware regret includes both opportunity loss and paid observations. Lemma 1 proves a uniform reduction: every possibly randomized history-dependent policy is dominated, on every instance, by a two-phase policy that requests observations in an initial prefix and then repeatedly plays one action without further observation. Its proof compresses all virtual labeled rounds first and replaces unlabeled play by a uniformly sampled action from the virtual unlabeled actions; stationarity, independence, and zero information on unlabeled rounds preserve the labeled-history law and expected suffix regret.

For correlated action rewards modeled by a GP, Theorem 4 gives the C3-GP cost-aware regret guarantee under its confidence event, bounded kernel/reward assumptions, and a positive minimum observation cost (with a stated residual-uncertainty alternative). Theorem 5 gives a minimax lower bound for finite independent arms, and Theorems 6–7 give instance-dependent bounds and a lower bound. These establish cost-aware query allocation and a substantial explore-then-commit baseline; they are not paired common-outcome switching results.

## Exact boundary for ShiftLab

The two-phase reduction depends on stationary rewards and the fact that an unobserved round carries no information. It does not preserve the ShiftLab process when regime states reverse, labels are released after a nonzero delay, a hard total query cap must reserve pending requests, deployment can repeatedly switch and roll back, or the objective includes a causal-null probability of any promotion. Its comparator is a best action under the stationary reward function with observation costs in regret. It has neither an anytime false-promotion event nor switching charges.

Accordingly, this source closes generic claims of a novel cost-aware acquisition score, adaptive observation allocation, or an exploration-then-commit rule. Its two-phase theorem is not a reduction of the nonstationary delayed switching contract. The residual is only an obligation: prove a strict finite-horizon acquisition/switching result that fails under the stationary two-phase assumptions and survives equal-budget delayed, reversible, alpha-safe baselines. The difference in assumptions alone is not novelty.

The current `p_j`-by-query-stratum coupling remains only a mechanism hypothesis. A genuine result must derive its realized action-conditioned continuation value, include the incumbent-dependent movement cost, preserve the causal-null information pattern, and beat a state-aware costed-sensing comparator. A local score separation with supplied values is not sufficient. Do not run a development efficacy grid until that theorem-level comparison is specified.

## Decision

Continue G1 only for a result that uses the interaction of recurrent regimes, delayed paired labels, pathwise budget reservation, reversible switching economics, and the explicit null-risk event. Reject another generic costly-observation wrapper. G2–G5 remain held. Promotion validity remains distinct from evidence of present benefit after a reversal; historical likelihood-ratio wealth cannot certify post-reversal value.

## Primary source

- Schur, Lago and Fiez (2026), [PMLR paper record and abstract](https://proceedings.mlr.press/v337/schur26a.html). The primary PDF is cached in the ignored output directory named in `switching_source_manifest_v25.json`; the B.1 reduction proof and selected theorem sections were inspected, not independently reproved.
