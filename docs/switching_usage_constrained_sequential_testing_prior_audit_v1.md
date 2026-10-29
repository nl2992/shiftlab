# Usage-constrained sequential testing with online sensing: prior-art boundary

**Date:** 2026-10-28. **Status:** primary source inspected; generic finite-horizon adaptive sensing plus stopping is closed as a novelty claim.

## Source and inspected result

Shang Li, Xiaoou Li, Xiaodong Wang and Jingchen Liu, “Sequential Hypothesis Test with Online Usage-Constrained Sensor Selection,” arXiv:1601.06447. The [primary arXiv source](https://arxiv.org/abs/1601.06447) and PDF are cached in `outputs/switching_source_audit_v1/`; PDF SHA256 is `DF578972670ACF21937914266B873670B1A823D7D1F6E16110AFCF57FBF9038D`.

Inspected the model and constrained problem in Section II, finite-horizon Bellman recursion and stopping/selection structure in Section III-A (Lemma 1, Lemma 2, Lemma 4, Theorem 1), Lagrange reduction and usage-constrained optimum in Section III-C (Theorem 3 and its proof), and the appendix arguments establishing the posterior sufficient statistic and concavity/threshold structure. The source assumes two known simple hypotheses and heterogeneous sensors whose observations are independent over time and across sensors. It jointly selects a sensor as a function of the current posterior, stops by a finite maximum sample count N, and makes a terminal decision. The objective minimizes expected sample size subject to type-I/type-II error bounds and expected per-sensor usage constraints. The finite-horizon solution is a time-varying posterior/LLR sensor-selection rule with curved stopping boundaries; the usage constraints are handled through Lagrange multipliers. The paper's usage limits are in expectation, not a pathwise total-label budget.

## Consequence for ShiftLab

This source directly defeats generic novelty claims for adaptive evidence acquisition, finite-horizon stopping, posterior-dependent sensing, and error-constrained resource use in a known testing model. Its N-round horizon also enforces a per-realization maximum number of samples, although it does not provide a global hard query budget across a longer deployment horizon with skips and pending labels.

It does not solve the proposed ShiftLab problem: its null and alternative are known stationary simple hypotheses; it has no arbitrary causal conditional-null family, fixed delayed release with pending-query reservation, recurrent hidden regime, repeatedly reversible policy deployment, economic switching charge, or dynamic regret comparator. These mismatches are comparison obligations. They do not create novelty by themselves. A candidate limited to one-shot fixed-regime certification must compare directly with this posterior-sensing/stopping DP after matching its max-sample and error semantics. A repeated-switching claim must prove the additional result comes from the interaction of causal-null safety, delayed pathwise acquisition, and economic deployment switches—not merely from augmenting the state of a finite-horizon planner.

## Decision

Reject “jointly adapt queries and stop when evidence suffices under a finite sample cap” as a contribution. Add Li et al. as a mandatory comparator for any one-shot or stationary certification subproblem. G1 remains open for the repeated delayed causal-null contract; no algorithm or efficacy experiment passes on the strength of this source distinction.
