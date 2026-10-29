# Paid observation and switching: source-level novelty audit

**Date:** 2026-10-28. **Decision:** generic budgeted acquisition plus switching costs is already covered by a close ICML 2026 comparator. No new method, theorem, or gap claim is validated here.

## Primary source inspected

Xueping Gong and Jiheng Zhang, “The Cost of Information: Phase Transitions in Contextual Bandits with Paid Observations,” ICML 2026, PMLR 306. The [PMLR paper page](https://proceedings.mlr.press/v306/gong26i.html) links the accepted paper. The cached PDF and extracted text are `outputs/switching_source_audit_v1/gong26_paid_observation.pdf` and `.txt`; URL, size, and SHA256 are in `docs/switching_source_manifest_v6.json`.

## Results and overlap

The paper's round protocol reveals context and per-action observation costs, then lets the learner choose an action and an additional set of actions whose losses it pays to observe. It analyzes adversarial contextual losses, importance-weighted updates, and total regret including observation expenditure. Theorem 2.1 gives a near-optimal paid-observation regret bound. Section 3 adds a hard cumulative *free-observation* budget, proves lower bounds with a budget threshold, and gives a meta-controller matching the stated rates across budget regimes (Theorems 3.1–3.2). Section 4 gives an oracle-efficient result under a realizable conditional-mean model.

The paper explicitly reduces ordinary action switching costs to paid observation: assign cost `c` to observing any action other than the previous action and zero to the previous action. It says the resulting modified algorithm obtains the familiar order `O((c |A| ln |A|)^(1/3) T^(2/3))`. This directly rules out novelty for “choose observations by value/cost while paying for switches,” and substantially overlaps the proposed generic hard-budget regret objective.

The information timing is different from our target. Their loss vector for round `t` is fixed from history through `t-1`; the learner then selects an action and an observation set and receives observed losses in the round. The inspected protocol does not model an outcome released after a random or fixed delay, multiple pending requests, or a time-uniform false-promotion constraint for interventions. Also, the “free observation budget” is an allowance for observations outside the paid set in a regret construction; it is not our exact hard cap on costly paired outcome queries. Those are contract differences, not by themselves a novelty claim. Adding a delay queue and an e-process to their rule would still be an unsubstantiated combination absent a result showing a new guarantee or separation.

## Research consequence

Close G1 for the broad premise: paid acquisition with switching costs and a hard observation allowance is not an unoccupied algorithmic gap. Keep the delayed feedback and causal anytime safety contracts explicit. Before proposing another controller, state a narrower theorem question that is not a direct corollary or routine wrapper of the paper—for example, whether delayed, selectively released paired comparisons permit a strictly better safe decision-regret frontier at fixed total query cap than every immediate-feedback paid-observation reduction plus a separately valid safety test. This is only a candidate question, not a claimed gap. First derive either a lower bound/counterexample or a matching construction and test the reduction carefully, including the two papers' different budget semantics and adversary timing.

The current causal-game LP remains a classical finite reference and one small solved cell; the post-solve cohort equivalence means it demonstrates no adaptive acquisition advantage. Do not expand that cell or present it as efficacy evidence. G2–G5 remain open. Proceed only when the exact contract and a nontrivial theorem-level delta survive source comparison; otherwise revise the hypothesis.
