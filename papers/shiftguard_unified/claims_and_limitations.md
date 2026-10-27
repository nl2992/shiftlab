# Current claims and limits

**Evidence snapshot:** 2026-10-27 working tree. This document records what
the current evidence supports and blocks stronger manuscript language until
the corresponding gates pass. The claim-level artifact map is
[`claim_evidence_map_v1.md`](claim_evidence_map_v1.md).

## Supported claims

1. **Distribution shift, predictive degradation, and downstream decision
   harm are distinct outcomes.** The synthetic benchmark contains controls
   with large nuisance change and alternatives where the declared cost
   endpoint changes; alarm rates are always attributed to the tested null and
   endpoint.
2. **The PPE proxy correction can be applied to a bounded paired-cost
   e-factor under its required query and filtration conditions.** The code
   implements the published correction and propensity floor. Its paired-cost
   use is an endpoint adaptation, not a reproduction of the paper's full
   application suite.
3. **At one frozen synthetic operating point, PPE improved matched detection
   over fixed-mixture at query rate 0.20.** Across the registered alternative
   grid and both rates, the paired difference was +12.50 percentage points
   (95% stream-seed bootstrap interval [+11.17,+13.83]). The effect was
   concentrated at q=0.20: PPE averaged 64.17% versus 37.25% at that rate;
   at q=0.40 it averaged 71.25% versus 73.17%. This is a result for the
   registered synthetic generator, score, stake, proxy, horizon, and query
   policy only.
4. **The frozen PPE synthetic null calibration passed its registered
   simulation gate.** There were zero false alarms in each of 16 cells with
   1,000 streams per cell; the maximum Bonferroni-adjusted one-sided exact
   upper bound was 0.5752%. The independent replay matched all 6,400 PPE
   stream outputs, and all four methods shared the same query path and stayed
   within the hard spend cap. The simulation is evidence about the registered
   generator, not a proof beyond the e-process assumptions.
5. **The independent integrated synthetic confirmation exposes material
   limitations.** Q1 gating misses shifts that start outside its
   monitoring window; late rollback can still leave promoted policies below
   the continue baseline; and the full pipeline does not generally beat
   simpler two-gate or fixed-candidate arms. The controller did not change
   outcomes in this simulator. These findings are scoped to the registered
   design and costs.
6. **Two distinct real-data task families now have frozen, independently
   checked component evaluations.** EIA 2026 tests retrospective forecasting
   error and retraining-resource schedules under assumed label delays; the
   separate CUDA replay reproduced its aggregate results. Upworthy tests a
   fixed-horizon text-based package selector and found +0.1002 CTR percentage
   points over uniform choice on 3,808 eligible project-relative holdout tests
   (week-cluster 95% interval [+0.0850,+0.1170] points). These tasks have
   different units and protocols and must not be pooled. Neither evaluates
   the complete monitor–certify–intervene system or establishes prospective
   real-world validity. CRSP, WILDS, Gas Sensor, Open Bandit and other sources
   remain task-specific development/retrospective evidence with their own
   data-contract limitations.
7. **The matched Timans synthetic Q1 comparison did not establish a DIVE
   advantage over an established bounded-risk monitor.** No Holm-adjusted
   paired detection difference was significant in that registered
   immediate-feedback design. A separate Comparecast comparison has
   descriptive detection results, but its tested running-average null differs
   from DIVE's conditional-mean null and is not treated as a valid superiority
   test. These are not equivalence claims and do not cover sparse-label
   settings.
8. **The integrated Q1–Q3 synthetic system has mixed, profile-specific
   outcomes.** It helped relative to continuing in two monitor-aligned harm
   profiles, but simpler arms did better there, other onset/reversal profiles
   exposed failures, and the controller ablation did not change decisions.
   This does not support a general integrated-system advantage.

## Claims not currently supported

- A universal or real-world advantage of PPE, DIVE, Target-Scout, or the
  integrated controller.
- A guarantee for PPE under outcome-dependent queries, unverified propensity,
  delayed feedback, arbitrary temporal dependence, performative actions, or
  costs not identified by the observed outcome.
- A claim that covariate shift or predictive degradation necessarily causes
  downstream decision harm, or that its absence rules harm out.
- A guaranteed future utility improvement from a positive shadow certificate.
- A claim that separately validated components combine into a statistically
  valid or economically superior end-to-end system.
- Actual investment profitability, executable trading value, or a validated
  point-in-time trading policy from CRSP retrospective replay; costs remain
  imposed and release-time assumptions are unverified.
- A novelty claim for betting/e-processes, prediction-powered residual
  correction, fixed-start mixtures, label budgeting, or candidate gates in
  isolation. Do not claim to be the first temporal-shift audit of monitoring
  and adaptation failures: Ahmed et al. (2026) provide a close published
  precedent on label-free prediction monitoring and test-time adaptation.
  The possible cross-estimand empirical contribution beyond that work and the
  WATCH, Comparecast, PPE, PPRM, policy-selection, and safe-adaptation
  literature remains unverified. See
  [`label-free temporal audit`](label_free_temporal_audit_prior_work.md).

## Remaining evidence gates

The comparator scope triage and reference-method selection are now recorded,
but the comparable Q1–Q3 numerical frontier is still incomplete. The research
scope decision is made: NO-GO for a new algorithm and PIVOT to a retrospective
benchmark/failure-analysis manuscript. Publication-level differentiation
remains open, especially after Ahmed et al. (2026). Other blockers are a
defensible real-data information/cost contract for the complete system and the
manuscript. The independently calibrated synthetic end-to-end comparison is
complete for its frozen design and does not support general superiority. See
[`gap_analysis.md`](gap_analysis.md), [`sota_fidelity_matrix.md`](sota_fidelity_matrix.md),
[`real_data_inventory.md`](real_data_inventory.md), and
[`method_decision.md`](method_decision.md), and the
[`claim-to-evidence map`](claim_evidence_map_v1.md) and
[`manuscript draft v0`](manuscript_draft_v0.md). The current decision remains
**NO-GO for speculative RIVE/ASC development** and **GO for the finite closure
pass**. A publication-scope decision should follow the remaining ranked gap
audit, not the size of the existing codebase or dataset archive.
