# Active Sequential Two-Sample Testing: source-level comparison

**Date:** 2026-10-28. **Status:** primary source, model, Theorems 5.1 and 5.4, and the
Theorem 5.1 proof inspected. This closes one source-level audit item; it does not pass G1 or
establish novelty.

## Primary source and theorem

Weizhi Li, Prad Kadambi, Pouria Saidi, Karthikeyan Natesan Ramamurthy, Gautam Dasarathy, and
Visar Berisha, [“Active Sequential Two-Sample Testing,” TMLR 2024](https://wayne0908.github.io/Publications/TMLR2024.pdf).
The primary PDF is cached (ignored) at
`outputs/switching_source_audit_v1/active_sequential_two_sample_testing_tmlr2024.pdf`;
SHA256 is `1bd1579868fac17a9f405b8da45c776636d0a5ab93a0a6d8b271edad5a1adbe2` (802,742 bytes).

The paper considers an unlabeled feature pool whose feature-label pairs are IID. The null is
independence of feature and label; labels are costly and the analyst has a finite label-query
budget. Query features can be selected adaptively using a classifier updated from previous
queried labels. The sequential statistic is

`W_n = product_(i<=n) P_hat(Z_i) / Q_i(Z_i | S_i)`,

and the null is rejected when `W_n <= alpha`. Theorem 5.1 proves
`P_0(exists n<=N_q: W_n<=alpha)<=alpha`. Appendix A.2 first argues that adaptive feature
selection preserves feature-label independence under the null; it then upper-bounds the
empirical-prior likelihood ratio by the version using the true class prior, whose reciprocal is a
nonnegative martingale, and applies Ville's inequality. Theorem 5.4 provides an asymptotic
mutual-information characterization for a consistent bimodal query scheme. The finite label cap,
active selection, adaptive updates, anytime Type-I control, and power analysis are therefore
already combined in a published method.

## Exact relation to the ShiftLab contract

This is a serious prior against a generic “active queries + anytime-valid test” novelty claim.
The sample is a fixed IID unlabeled pool; labels arrive immediately; the null is feature-label
independence; and the action is a terminal reject/retain decision. It has no paired counterfactual
policy losses, online regime onset, fixed release delay, pathwise budget over pending requests,
query price, deployment switching cost, repeated promotion/rollback, dynamic regret comparator,
or future-value certificate. Its theorem cannot be relabeled as the target switching theorem, and
those model differences do not establish an open gap by themselves.

The nulls also do not reduce directly. If the feature is constant, feature-label independence
holds for every Bernoulli label mean, so the test cannot detect the ShiftLab alternative
`E[Y_t|history]>1/2`. If time or regime indicators are used as features to encode an onset, the
chronological onset stream is no longer the paper's IID sequence of feature-label pairs. A new
validity argument would be needed for this predictable non-IID stream and its delayed release
filtration.

Any proposed acquisition contribution must therefore do more than adaptively select queries while
preserving an anytime test. The residual technical claim must explicitly couple delayed query
timing and pending labels to costed deployment actions under the global conditional-null risk
event, then prove a performance advantage over active sequential testing composed with a standard
economic switching rule, under the same pathwise budget. Whether such an exact composition exists
remains unresolved; the source model mismatch is not itself a novelty result. A guarantee about
evidence against a fixed null still does not promise that benefit persists after an unobserved
reversal.

## Verification and consequence

The theorem statement and proof passages were inspected in the cached primary PDF: Section 3.2,
Section 4, Algorithm 1, Sections 5.1–5.3, Theorems 5.1/5.4, and Appendix A.2. The paper is not
being treated as an implementation baseline for the common-outcome switching task; an exact
reduction would be needed before numerical comparability. This source read closes the broad audit
question of whether active label selection and anytime Type-I testing have already been combined.
It narrows, but does not clear, G1. No new algorithm or experiment is authorized by this source
comparison alone.
