# Out-of-order release filtration audit

**Date:** 2026-11-04. **Status:** scope clarification and counterexample; no new method or novelty claim.

## Decision

The current paired-certification result is not invalidated. The repository's B3/P3b statement specifies a fixed common delay and release-order process, and its proof uses a release-time conditional null. The existing theorem explicitly warns that the event-time-prefix argument does not cover reordered, informative releases. See [`05_PAIRED_CERTIFICATION_THEORY.md`](../promising_directions/05_PAIRED_CERTIFICATION_THEORY.md), [`switching_safe_test_baseline_v1.md`](../switching_safe_test_baseline_v1.md), and [`switching_safe_composition_boundary_v1.md`](../switching_safe_composition_boundary_v1.md).

This audit closes only a possible extension: issue-time martingale differences do not, by themselves, license updating a product in arbitrary label-arrival order. The counterexample below makes that scope boundary explicit. It does not establish a useful new certificate; a valid and target-relevant release-filtration null remains an open modeling obligation.

## Operational filtration condition

Index queried paired outcomes by their release order. Let `G_(j-1)` contain everything the deployed monitor knows immediately before release `j`: contexts, query and deployment actions, pending requests and their issue times, prior released labels (including labels with later issue indices), and the release metadata. A sufficient condition for release-time betting factors is

```text
E_j >= 0,   E[E_j | G_(j-1)] <= 1.
```

For `E_j = 1 + lambda_j Z_j`, it suffices that `lambda_j >= 0` is `G_(j-1)`-measurable, `E_j >= 0`, and `E[Z_j | G_(j-1)] <= 0`. Then the product in release order is a nonnegative test supermartingale and Ville controls its maximum. A pathwise budget is compatible if each request is charged when issued, pending requests count toward the cap, and querying stops at the cap. Budget accounting does not repair a failure of the conditional-mean assumption.

Under a deterministic common delay, release order preserves issue order; the existing event-time-prefix proof can instead control the release-visible crossing as a crossing of the event-time process. This is why the existing fixed-delay result need not assert that wealth is a supermartingale in every larger arrival-time filtration. Arbitrary reordering removes that prefix containment argument.

## Two-outcome counterexample

Issue two outcomes and reveal `D_2` before `D_1`. Let `D_1` be a fair sign. Conditional on `D_1=+1`, set `D_2=+1/3` with probability `3/4` and `D_2=-1` otherwise. Conditional on `D_1=-1`, let `D_2` be a fair sign. Then

```text
E[D_1] = 0,       E[D_2 | D_1] = 0.
```

So the issue-order factors `E_1=1+0.5 D_1` and `E_2=1+D_2` form a nonnegative martingale in issue order. But after `D_2=+1/3` is released, `E[E_1 | D_2=+1/3] = 1.5 > 1`: the first issue-time factor is not valid conditional on the information available at its later release.

If the monitor multiplies factors as they arrive and alarms at wealth `2` (`alpha=1/2`), it crosses on the first release when `(D_2,D_1)=(+1,-1)`, probability `1/4`. It also crosses after the second release when `(D_2,D_1)=(+1/3,+1)`, probability `3/8`. These events are disjoint, so the release-order crossing probability is `5/8 > 1/2`. Thus issue-order martingale validity alone does not imply release-order Ville validity under this out-of-order Markov construction.

The example does not satisfy the stronger release-filtration null for `D_1`; it is not a counterexample to P3b. Rather, it shows why the filtration in that null cannot be silently weakened when release order changes.

## Literature boundary and remaining gate

Lindon and Kallus, [*Design-Based Anytime-Valid Inference for Randomized Experiments with Delayed Outcomes and Staggered Entry* (ICML 2026)](https://proceedings.mlr.press/v306/lindon26a.html), show that their treatment-effect IPW error is not a martingale under any filtration and construct arm-specific event-time martingales. That is relevant evidence that delayed-outcome estimands can have nontrivial filtration structure, but their randomized-arm setting does not directly supply a paired, selectively queried, reversible-promotion certificate with a pathwise query cap.

Waudby-Smith et al., [*Anytime-valid off-policy inference for contextual bandits*](https://arxiv.org/abs/2210.10768), allow adaptive logging and dependent time-series contexts in their contextual-bandit contract. This does not automatically cover arbitrary out-of-order release of paired outcomes; those assumptions must be matched to the deployed observation filtration.

Before any extension is implemented, specify (i) the estimand, (ii) the operational release filtration and delay/order mechanism, (iii) a null that implies the required conditional expectation in that filtration or another valid design-based construction, and (iv) whether that null is scientifically defensible when delay depends on outcome or event history. If no such null preserves the intended paired-gain target, stop this extension. A theorem under a stronger or changed null alone is not a research contribution; it needs a quantitative advantage against matched delayed-inference and acquisition baselines.
