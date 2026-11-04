# Prior-art audit and next research target — 2026-11-04

## Decision

Do not claim novelty for combining an active selector with a sequential confidence set. The
repository already studies selector-plus-certificate policies, and sequential confidence sets are
established. The nearest current source is especially relevant: CC-SMCS (Li & Zhu, 2026) gives
time-uniform simultaneous confidence sets for cost-minimal pipelines subject to coverage constraints,
allows data-dependent stopping, and treats delayed multi-horizon feedback. The broad composition is
therefore not a defensible contribution by itself.

The P7s screen also removes the empirical reason to continue tuning this parameterization: it loses
on net cost to Model Picker on four streams and Model Selector on one, even though it beats Gated
Deployment on all five. Close this candidate. The only follow-on worth a small, development-only
study is a **budget-and-reversal contract**, not a wrapper: with one shared stream of selectively
queried labels, delayed release, a pathwise cap that counts pending queries, and nonzero switching
cost, can one policy jointly (i) spend labels preferentially where they are informative, (ii) retain
time-uniform false-promotion control, and (iii) detect a post-promotion reversal and roll back with
a separately stated error guarantee? Compare the joint objective to the best of Gated, SMCS,
Model Picker/Selector, and P7s under exactly the same information, delay, safety event and cost.

The repository has already implemented and screened this follow-on family. The version-indexed
challenger and its dual promotion/rollback monitor lose to the version-aware Model Picker on all
five exposed streams. A fresh four-scenario stress screen found that the unreserved monitor used
nearly the full label cap but rolled back in only 4/100 degradation episodes; reserving labels for
rollback cut late-improvement promotions from 64/100 to 29/100 and produced no rollbacks in the
screen. The paired P7s restart-mixture pilot also failed its frozen cost gate against Cao controls.
These results close the proposed generic budget-and-reversal wrapper as a current algorithm lead.
See [`versioned_challenger_candidate.md`](../../sota_sprint/versioned_challenger_candidate.md),
[`versioned_stress_screen_2026-11-04.md`](../../sota_sprint/versioned_stress_screen_2026-11-04.md),
and [`B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_FINDINGS_2026-11-04.md`](../B3_PLUS_RESTART_MIXTURE_DEVELOPMENT_FINDINGS_2026-11-04.md).

The active research direction is therefore **evidence and claim closure**, not another algorithm
screen: determine whether any current claim survives primary-source review and source-to-row
provenance. The authoritative project checkpoint says no algorithmic lead currently survives;
method work should reopen only for a documented structural gap or an admissible stream with
observed release times and an aligned decision contract. This does not complete the broader
research objective, and it does not establish publication-level novelty.

## Source comparison

| Work | Established result relevant here | Remaining contract difference to audit |
|---|---|---|
| Arnold et al., [Sequential Model Confidence Sets](https://arxiv.org/abs/2404.18678) | Sequential model confidence sets with time-uniform, nonasymptotic coverage for best-model selection. | Whether its theorem covers this adaptive queried-label filtration, pending delayed outcomes, a hard pathwise label cap, and switch/rollback actions. Repository audit classifies our use as an inference-component adapter. |
| Li & Zhu, [CC-SMCS](https://arxiv.org/abs/2609.28522), 2026 preprint | Simultaneous martingale confidence sequences for cost-minimal pipelines under multiple conditional miscoverage constraints; time-uniform oracle coverage, data-dependent stopping, and a delayed multi-horizon extension. | The abstract/paper target is constrained conformal pipeline selection. Audit whether the theorem directly covers binary paired frozen-model benefit, selective queries shared across candidates, pathwise pending-label caps, switching cost, and reversal/rollback control. Do not infer that it does not from the application difference alone. |
| Gu et al., [SERPANT](https://proceedings.mlr.press/v306/gu26l.html), ICML 2026 | Pairwise e-process tests provide familywise error control at any monitoring time for adaptive online LLM ranking; a tournament sampling rule adapts comparison allocation to past outcomes and extends to top-k identification. | This closes generic novelty claims for anytime pairwise ranking with adaptive annotation. Its target is pairwise human preference ranking; it does not, by itself, establish the same guarantee for paired predictive-loss streams, deployment switching costs, or post-switch rollback. Any claimed gap requires a theorem-level contract comparison. |
| Repo C1 theory target, [`switching_theory_targets_c1_c2_v1.md`](../../switching_theory_targets_c1_c2_v1.md) | A model-conditional anytime false-promotion gate under an explicit finite delayed-HMM model; separates this claim from distribution-free safety. | It is a different model-based contract and its confidence-set core may be a direct corollary of sequential likelihood-ratio methods; the delay/budget upper-bound proof remains partly a sketch. |
| Repo failure atlas / rollback and query-scheduling work | Already explores rollback, dependence, query scheduling and composition with Gated/SMCS. | Novelty must be stated at theorem level; a new adapter label or bundled engineering features do not suffice. |

## Evidence and limits

The theorem-level source check confirms CC-SMCS's candidates may adapt arbitrarily to the past so
long as their state, prediction set, exposure, and objective are predictable; its main theorem
gives time-uniform inclusion of the constrained oracle set and explicitly allows outcome-dependent
efficiency losses. Appendix G.1 treats delayed multi-horizon feedback. This makes generic adaptive
selection and delay poor novelty claims. The source setup evaluates outcomes on a common stream and
does not directly specify our policy's selective query cap, pending-label accounting, deployment
switching cost, or reversal error event. Those are *candidate* contract differences only; before
claiming a gap, construct a valid mapping and determine whether the existing martingale CS theorem
already covers them.

The repo C1 target is a finite-model likelihood confidence set over delayed selectively observed
labels and a model-conditional false promotion event, with a pathwise query budget. It may fit within
the general predictable martingale framework, but its likelihood-ratio and HMM filtering target is
not identical to CC-SMCS's prefix-average constrained-argmin target. Its delay/budget upper-bound
result is still a proof sketch. Relevant primary sources: [CC-SMCS, arXiv:2609.28522](https://arxiv.org/abs/2609.28522)
and [SMCS, arXiv:2404.18678](https://arxiv.org/abs/2404.18678).

SERPANT further narrows the broad sequential selection/ranking space: anytime pairwise error control,
adaptive comparison allocation, and top-k identification are already combined in a 2026 ICML paper.
The application differs from ShiftLab's paired predictive-loss and promotion decisions, but an
application difference alone is not a novelty argument.

The follow-on is not ready for a confirmatory run. The five UCI streams were already exposed to
other sprint methods; the delay and monetary costs in the P7s replay are imposed; several feature-
dependent comparators remain unimplemented for this contract. Any next screen must use development
data only, register the safety event and all costs before looking at outcomes, and reserve a new
stream or simulation seed family for confirmation.

## Go/no-go questions before any future algorithm work

1. Read CC-SMCS theorem statements and delayed-feedback appendix; write a mapping from each
   assumption to our query, feedback, cap and switching filtration.
2. Map the existing `P7s`, `QSG`, rollback-mixture and `budgeted_promotion` results to the same
   contract. Identify a concrete guarantee not already present.
3. If a gap remains, state the exact null, estimand, filtration and resource contract, prove a
   separation from the closest method, and screen against matched baselines on fresh development
   data. The already-screened generic selector/certificate/rollback composition is not an open
   lead.

## Current project-level stop/go

| Question | Current evidence | Decision |
|---|---|---|
| P7s beats its implemented published suite on the exposed streams? | No: best active selection is cheaper on 5/5 streams. | Close this P7s parameterization. |
| A sequential selector-plus-safety wrapper is novel? | No support: SMCS and CC-SMCS cover sequential confidence-set selection, with adaptive candidates and delayed multi-horizon feedback; SERPANT covers anytime-valid adaptive pairwise ranking; repository wrapper and rollback variants are also screened. | Do not claim novelty for composition or generic adaptive online ranking. |
| A budgeted promotion/rollback wrapper has a practical gain? | No: the versioned stress screen shows weak rollback sensitivity or a promotion-power cost under reserved labels. | Close this generic wrapper. |
| Any algorithmic SOTA lead currently survives? | The broader research checkpoint and local decision ledger record none. | No-go on new algorithm tuning until a new structural gap or aligned data contract is documented. |
| What remains useful now? | Complete the source-to-claim and result-to-row audit; keep each Q1/Q2/Q3 estimand and external-data limitation separate. | Continue evidence closure; do not report it as a novel method result. |

## Related outcome report

The empirical screen and its limitations are recorded in
[`P7S_FRESH_REAL_SUITE_RESULTS_2026-11-04.md`](P7S_FRESH_REAL_SUITE_RESULTS_2026-11-04.md).
