# MOPE / off-policy confidence sequence applicability audit

**Audit date:** 2026-10-26  
**Status:** official 2021 reference code passed a registered IID calibration and power comparison; OBD fixed-horizon DM/IPS/SNIPS/DR point-estimation development and one exploratory fixed-candidate MOPE path replay are complete; no claim of real-data sequential validity.

## What the methods already solve

Karampatziakis, Mineiro, and Ramdas (ICML 2021) construct nonparametric, nonasymptotic confidence sequences for contextual-bandit policy values from logged actions, rewards, and propensities. Their gated-deployment construction directly forms a confidence sequence for the value difference between a staged policy and the incumbent. The sequence is valid at arbitrary stopping times under the paper's contextual-bandit sampling contract. Thus, sequential candidate certification in an action-dependent reward setting is already established; it cannot be claimed as a new ShiftGuard contribution by itself.

Waudby-Smith et al. (arXiv 2022, ACM/IMS Journal of Data Science 2024) extend anytime-valid off-policy inference to predictable, changing logging policies and exogenously time-varying context and reward distributions. The contexts may be a dependent time series: conditional on prior contexts, the next context and reward law may not depend on past actions or rewards. The target policy must be predictable and absolutely continuous with respect to the logging policy at each event; the bounded-reward results use rewards in [0,1]. Section 3 gives separate confidence sequences for the running average of time-varying conditional policy values, with no restriction on how those values change. That estimand is an average over the observed sequence, not an alarm for an instantaneous regime change. These conditions make the paper a closer reference for a chronological OBD analysis than the 2021 IID-only method, but they do not remove the need to verify the OBD decision unit, conditional propensities, feature timing, or feedback availability. See the [primary paper](https://arxiv.org/abs/2210.10768), especially its data-generation assumptions and Section 3.

These methods answer a contextual-bandit policy-value question. They do not, by themselves, solve ShiftLab's label-query allocation, retraining-cost optimization, or generic paired-cost monitoring under full-feedback classification. Their presence substantially narrows any proposed Q2 contribution: ShiftGuard would need to show a valid, useful extension beyond their staged-versus-incumbent gate, with explicit costs and resource limits, and compare against the applicable OPE confidence sequence.

## OBD task compatibility

The official OBD release describes logged actions as recommended item IDs, position as one of three slots, the click as a binary outcome, and `propensity_score` as the probability of recommending the item at that position. The full Random/all archive has 1,374,327 records; its recorded Random propensity is uniformly 1/80. For a candidate policy fixed before an evaluation segment and supported on the 80 items, this gives a practical action-dependent reward contract and a known finite importance-ratio bound of at most 80 against the Random logger, subject to the exact per-position estimand and source propensity semantics.

The 2021 MOPE method is only eligible if the chosen sequence satisfies its IID contextual-bandit assumptions. The later time-varying OPE framework allows dependent contexts but not arbitrary action/reward-driven context or reward dynamics; it still needs the observed propensity to be the conditional action probability for the declared decision unit and the exogeneity/predictability assumptions above. Its time-varying target is the running average of conditional policy values, not pointwise harm. OBD has no exposed user/session or complete-slate request key, so dependence among positions or repeated users cannot currently be clustered or checked. The 80 `user-item_affinity_*` columns have unverified as-of construction and must stay out of the candidate learner. The seven-day archive and explicit UTC impression times do not provide click-release or feature-delivery times; a retrospective sequence cannot be reported as a prospective live gate.

The BTS archive count also remains discrepant: the full archive streams to 12,357,200 rows, while the 2020 paper reports 12,168,084 for the corresponding count. Do not use the BTS on-policy value as a published benchmark reference until this is reconciled. The Random logger is sufficient for an OPE development task if its unit, candidate policy, and evaluation period are frozen; it does not remove the exposure and source-availability limitations above.

**OBD estimator development result:** full-archive IPS/SNIPS plus a two-fold cross-fitted item-position DM/DR adaptation now compares the Random target policy with concurrent Random/all observations. The equal-position errors are 0.14% for DM, 1.03% for IPS, 4.75% for SNIPS, and 3.90% for DR; DM is closest in this run and DR does not improve on IPS. This uses the paper's item-position reward assumption and avoids user-affinity features with unverified timing. The exact DR formula matches the official Open Bandit Pipeline implementation on a deterministic test at source commit `8cbd5fa4558b7ad2ba4781546d6604e4cc3e07c4` (absolute difference 1.11e-16). The result has no confidence interval, does not reproduce the paper's full repeated-split benchmark, and does not test candidate selection. Position-specific errors and importance-weight ESS remain uneven. Full method and artifacts: [`open_bandit_ope_development_results.md`](open_bandit_ope_development_results.md), [`DM/DR manifest`](../../outputs/shiftguard_unified/real_data_development/open_bandit_dr_ope_v1/manifest.json).

## Executable source check

The authors' MIT-licensed repository `https://github.com/n17s/mope` was cloned at commit `a4b8584b622f3a8296932568c520c1bb3e1957f0`. The unmodified `opebetrp.wealth_lb_gd` routine first passed a 30-stream zero-difference execution smoke test; that earlier run was not a calibration. A subsequent frozen comparison used 1,000 independent 200-event streams in each of a zero-mean cell, a +0.12 policy-gain cell, and a −0.12 strict-control cell. CUDA generated inputs; the pinned confidence-sequence calculation ran unchanged on CPU. MOPE promoted in 6/1,000 zero-mean streams and 1/1,000 negative-gain streams; their Bonferroni-adjusted one-sided upper bounds were 1.50% and 0.70%. The fixed-N Hoeffding comparator promoted in 0/1,000 streams in each nonpositive cell. The maximum over four nonpositive promotion endpoints and three empty-confidence-set endpoints was 1.50%, below the registered 5% gate. Empty confidence sets occurred in 0.1%, 0.2%, and 0.1% of MOPE paths in the zero, positive, and negative cells.

In the +0.12 cell, MOPE promoted in 991/1,000 streams (99.1%; exact 95% CI [98.30%, 99.59%]), versus 717/1,000 (71.7%; [68.80%, 74.47%]) for Hoeffding. The paired power difference was +27.4 percentage points (95% seed-bootstrap interval [+24.7, +30.2]); MOPE used 105.685 labels on average versus 200, a paired reduction of 94.315 labels (95% interval [92.454, 96.198]). These results establish a useful comparison only for the frozen bounded IID DGP, fixed target policy, reward model, and horizon. They do not reproduce the paper's full applications, validate MOPE on OBD, establish delayed/selective-feedback validity, or support a ShiftGuard novelty claim. The independent verifier checked all 6,000 stream-method rows, six source hashes, four run-artifact hashes, recomputed exact intervals and bootstrap summaries, and regenerated the CUDA input fingerprints. See [`protocol`](mope_gated_calibration_protocol_v1.md), [`run report`](../../outputs/shiftguard_unified/sota_reproductions/mope_gated_calibration_v1/report.md), [`manifest`](../../outputs/shiftguard_unified/sota_reproductions/mope_gated_calibration_v1/manifest.json), and [`independent verification`](../../outputs/shiftguard_unified/sota_reproductions/mope_gated_calibration_v1/independent_verification.json).

## Decision

**GO, completed for the registered scope:** the 2021 MOPE gated-deployment implementation is now calibrated and compared with a fixed-N bound on one synthetic IID contextual-bandit design. The 2022/2024 time-varying OPE paper has a source-level applicability audit; its dependent-context results would fit a chronological OBD replay only if OBD's decision unit, conditional propensities, context-history exogeneity, and outcome availability were established.  
**NO-GO:** do not label OBD an anytime-valid real-data confirmation until decision-unit propensities, action-induced dependence, feature availability, and label arrival are addressed. Do not claim novelty for sequential off-policy policy certification alone.

## Primary sources

- Karampatziakis, Mineiro, and Ramdas, [*Off-Policy Confidence Sequences*, ICML 2021](https://proceedings.mlr.press/v139/karampatziakis21a.html); [official author code](https://github.com/n17s/mope).
- Waudby-Smith et al., [*Anytime-valid off-policy inference for contextual bandits*, arXiv:2210.10768](https://arxiv.org/abs/2210.10768); [published journal article](https://doi.org/10.1145/3643693).
- ZOZO Research, [Open Bandit Dataset release and field definitions](https://research.zozo.com/data.html).

## OBD fixed-candidate replay follow-up

The frozen position-1 MOPE replay is now complete using an exact 2-D
optimizer for the reference algorithm's per-event concave QP. The full run
processed 274,737 held-forward events after selecting item 41 on the three
training dates. The logged-data IPW value difference was +0.001809, but the
MOPE confidence set first became empty at event 866, before its lower bound
crossed zero; the fixed-horizon Hoeffding lower bound also did not promote.
The original pinned CVXPY implementation reproduced the lower and upper paths
exactly through 1,000 actual OBD events, including the empty-set event. An
independent full-data verifier reconstructed the candidate, event scores,
daily summaries, full accelerated path and output hashes. The numerical
acceleration is documented in
[`MOPE optimizer validation`](mope_fast_optimizer_validation.md).

This is one exploratory retrospective sequence whose evaluation dates were
already present in ShiftLab OPE diagnostics. The empty set is retained as a
method diagnostic; it is neither evidence of candidate harm nor an estimate
of the method's false-alarm rate. Missing user/slate units, click-release and
feature-availability clocks, and possible dependence mean the MOPE guarantee
is not asserted on OBD. See the
[`protocol`](open_bandit_mope_development_protocol_v1.md),
[`execution note`](open_bandit_mope_development_execution_note_2026-10-26.md),
and verified aggregate folder
[`open_bandit_mope_v1`](../../outputs/shiftguard_unified/real_data_development/open_bandit_mope_v1/).
