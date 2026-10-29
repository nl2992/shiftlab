# Headroom screen for the uniform safe baseline

**Date:** 2026-10-28. **Status:** analytic comparison of existing artifacts; no method claim.

This combines two existing results for the registered cell `T=120, nu=61, B=20, epsilon=.10,
alpha=.05`: the all-onset uniform-calendar baseline is pathwise unable to promote, and the noisy
information lower bound applies to every adaptive risk-valid learner. It is a headroom calculation,
not a matched empirical comparison.

The baseline has gross regret exactly `12` for `d in {1,5,20}`. The general lower bound gives
gross regret at least `8.4289`, `8.6579`, and `9.5164`, respectively. Thus even an ideal learner
attaining that lower bound could improve on the inert baseline by at most `3.5711`, `3.3421`, and
`2.4836` gross units. These comparisons use the same one-switch comparator; its switch charge
cancels from the net-cost difference. The baseline itself spends `20c` on queries, so its net
excess is `12+20c-k`; however, the cited lower bound does not impose a positive query-spend floor
on every learner. It cannot be used to claim that high query cost makes improvement impossible.

The lower bound is not known to be attainable, so these values only upper-bound gross decision-
loss headroom. The fixed baseline's failure does not establish that an adaptive method can close
the gap, and it is especially weak evidence for novelty. This cell should not be used as a
showcase for the proposed method; a viable empirical cell needs enough information and economic
headroom under the universal lower bound before method comparisons.

The source values are in `switching_uniform_safe_baseline_v1.md` and
`switching_noisy_information_lower_bound_v1.md`. No new simulation or source claim was used.
