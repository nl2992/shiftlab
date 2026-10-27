# Publication scope decision v1

**Decision date:** 2026-10-26  
**Status:** project-level research decision; manuscript execution remains in progress.

## Decision

**NO-GO** for the proposed unified-method paper claiming a novel decision-harm/adaptation algorithm, a generally superior integrated system, or real-world end-to-end deployment benefit. **PIVOT** to a claim-bounded retrospective benchmark and failure-analysis manuscript across the three tracks. Do not start RIVE, ASC, or another algorithm branch under the current evidence.

This decision does not assert that a benchmark manuscript is already publication-ready or that its novelty is established. It selects the only scope currently consistent with the evidence. Publication viability remains conditional on the completion criteria below.

## Why this is the defensible scope

- **The integrated method has no general advantage.** In the frozen 100-seed-per-profile synthetic confirmation, the full pipeline helped over continue on two monitor-aligned harm profiles but lost to simpler two-gate/fixed-candidate methods in those profiles; it missed late-onset harm, performed poorly under reversal, and controller ablations made the same decisions. See [`integrated efficacy results`](integrated_efficacy_confirmation_results_v1.md).
- **Standalone components have established comparators and conditional gains.** The direct paired-cost monitor showed no adjusted advantage over Timans in its registered full-feedback design; PPE and Target-Scout improved only in their registered synthetic settings; MOPE already supplies a logged-bandit candidate gate under its assumptions. Do not infer an integrated gain by adding component wins. See [`claim-to-evidence map`](claim_evidence_map_v1.md) and [`comparator scope`](comparator_scope_decision_v1.md).
- **Real-data evidence is component-specific.** EIA tests forecasting/refit schedules under assumed delays, Upworthy tests package choice on a public project-relative holdout, and OBD supplies retrospective logged-bandit diagnostics whose MOPE confidence set became empty. None evaluates all monitor, candidate-certification, feedback-cost, and intervention stages under one validated information contract.
- **The closest work narrows generic novelty.** Published methods and preprints already cover sequential risk monitoring, policy-value gates, cost-aware retraining/switching, cost–reliability-volatility intervention, and a closely aligned retrospective temporal-shift audit of label-free monitoring/adaptation failures. Ahmed et al. (2026) use a natural cybersecurity shift pair and predictive/abstention endpoints; this overlaps the failure-analysis framing even though ShiftLab studies separate synthetic estimands and task-specific finance/online-advertising panels. Neither a domain difference nor a distinct estimand alone proves a publication-level contribution. See [`novelty audit`](novelty_audit.md), [`temporal-reliability source audit`](temporal_reliability_cost_control_audit.md), and [`label-free temporal audit`](label_free_temporal_audit_prior_work.md).

## Permitted manuscript claims

1. The three quantities—distributional change, predictive risk, and policy-relative decision harm—are distinct estimands; the registered generators demonstrate examples where they diverge. This is an estimand distinction and controlled empirical observation, not a new general theorem.
2. Under the registered immediate-feedback simulator, DIVE did not demonstrate an adjusted detection advantage over the chosen established bounded-risk/paired-score comparators. Under the registered sparse-label design, PPE showed a query-rate-dependent synthetic gain over its fixed-mixture comparator. These are separate tasks and guarantees.
3. The integrated system has profile-specific benefits and material failures; the frozen evidence does not support general superiority over simpler intervention rules.
4. The real-data studies offer separate external component checks with different outcomes, timing assumptions, and units. They do not validate prospective monitoring or the complete intervention pipeline.
5. The OBD replay is exploratory. The empty MOPE confidence set is a method diagnostic, not a false-alarm estimate, harm finding, or real-data validity result.

## Claims to exclude

- A novel unified ShiftGuard/RIVE/ASC algorithm or a new general transition from evidence to costed intervention.
- A single pooled Q1–Q3 score, common utility frontier, or cross-dataset ranking without defensible common units and information budgets.
- A general deployment, real-time, causal policy-value, future-profit, or anytime-valid real-data guarantee.
- Broad superiority of the integrated system or of a component beyond its registered task.
- A novelty claim based only on separating endpoints, using e-processes, querying labels, or charging retraining/switching costs.

## Finite completion gate for the benchmark manuscript

Before calling the manuscript complete, the project must: (1) finish a source-by-source literature and citation audit, including task-compatible versus scope-only comparator decisions; (2) reconcile the primary manuscript claims and every displayed number against the claim map and verified artifacts; (3) keep each track in a separate estimand/information panel, report the cross-track synthesis only qualitatively where units differ, and include negative results; (4) verify figure/table source data, PaperBanana-style visual consistency, captions, accessibility, and exact artifact links; (5) document dataset versions, permissions/licenses, feature/label timing, and exclusions; (6) rerun the full test suite and all selected artifact verifiers after final edits; and (7) freeze the manuscript, source, protocols, and output hashes together in a reviewed Git revision.

If the final comparator and literature audit cannot identify a differentiated, reproducible empirical contribution after these steps, the decision is **STOP/PIVOT** rather than submit the current manuscript under a novelty claim.

## Evidence links

- [`Decision gate report`](decision_gate_report_2026-10-26.md)
- [`Programme completion audit`](programme_completion_audit.md)
- [`Claim-to-evidence map`](claim_evidence_map_v1.md)
- [`SOTA fidelity matrix`](sota_fidelity_matrix.md)
- [`Comparator scope decision`](comparator_scope_decision_v1.md)
- [`Current manuscript draft`](manuscript_draft_v0.md)
