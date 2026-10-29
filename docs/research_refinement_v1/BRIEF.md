# Brief (user-supplied, 2026-10-27, verbatim)

SHIFT LAB — RESEARCH RED-TEAM AND SECOND-PASS REFINEMENT
You are acting as a principal research scientist, statistical learning theorist, causal inference researcher, and adversarial ICML/NeurIPS/ICLR reviewer.
Your task is to audit, challenge, and refine an existing research programme into the strongest scientifically defensible publication strategy. You are not starting a new project.
Repositories
Primary research repository:
https://github.com/nl2992/shiftlab
Research automation framework:
https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep
Work inside the existing ShiftLab checkout. Inspect `git remote -v`, including any GitLab remote, the active branch, working-tree status, latest commit, and available unpublished changes. Do not assume GitHub and GitLab are synchronized.
Read `AGENTS.md` and `docs/research_charter.md` before making decisions. Preserve all existing code, protocols, evidence, and negative results.
Use ARIS's available research, literature, novelty, reviewer, and refinement skills. Configure an independent cross-model reviewer when available. Never claim an independent review took place if it did not.
1. Scientific objective
Our research concerns detecting and mitigating downstream decision harm under distribution shift.
We want to answer three questions:
Q1: Detection
When has an incumbent model or policy become materially worse in terms of actual downstream decision loss, rather than merely showing statistical drift or predictive degradation?
Q2: Certification
How can we establish that a replacement policy is genuinely better, accounting for feedback limitations, multiple candidates, adaptive selection, deployment costs, and the possibility that improvements do not persist?
Q3: Intervention
Given limited information, compute, labels, and intervention resources, when should a system continue, query for additional evidence, promote a replacement, retrain, or fall back to a safer policy?
Our preferred unifying scientific question is:
Can a deployed learning system identify, certify, and execute a beneficial intervention under distribution shift using limited information, while controlling statistically unjustified decisions and accounting for operational costs?
This question is a hypothesis, not an established novel contribution.
Do not force all three questions into one algorithm or paper. Determine whether they can support a compelling unified contribution, whether a benchmark/failure-analysis paper is stronger, or whether they should remain separate.
2. Current repository status
The repository has progressed substantially beyond a starter implementation.
Investigate, rather than blindly accept, its existing:

* DIVE and decision-harm monitoring.
* Prediction-powered evidence, adaptive querying, delayed feedback, and sequential testing.
* Target-Scout and context-sensitive candidate selection.
* Shadow candidate evaluation, promotion, rollback, and budgeted intervention.
* Synthetic calibrations, confirmations, null controls, and negative experiments.
* CRSP retrospective evaluation.
* EIA electricity forecasting and Upworthy headline selection.
* Integrated ShiftGuard benchmark and manuscript drafts.

Prioritize reading:

* `docs/research_charter.md`
* `docs/next_phase_plan.md`
* `docs/closest_prior_work.md`
* `docs/methods_and_assumptions.md`
* `papers/shiftguard_unified/decision_gate_report_2026-10-26.md`
* `papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md`
* `papers/shiftguard_unified/novelty_audit.md`
* `papers/shiftguard_unified/sota_fidelity_matrix.md`
* `papers/shiftguard_unified/claim_evidence_map_v1.md`
* `papers/shiftguard_unified/publication_scope_decision_v1.md`
* `papers/shiftguard_unified/manuscript_draft_v0.md`

Resolve file availability and changes against the actual checkout.
The existing decision gate says NO-GO on a new RIVE/ASC/unified algorithm because the integrated benchmark has not shown a general improvement over simpler policies. The benchmark/failure-analysis manuscript is presently the defensible path.
Treat this as a serious prior decision. Do not reverse it merely because a new algorithm sounds promising.
3. Phase A — Repository reconstruction and scientific audit
Perform a comprehensive read-only investigation first.
Produce an evidence inventory containing:

1. Every significant implemented method and its exact code location.
2. The intended and actually implemented mathematical assumptions.
3. Every registered experiment, dataset, comparator, metric, result, and associated artifact.
4. Positive, inconclusive, and negative findings.
5. Reproduction status, verified hashes, seed separation, and known leakage risks.
6. Unsupported claims, missing comparisons, and open questions.
7. Conflicts between older documentation and newer code or results.

Distinguish implementation completeness from research completeness.
Do not rerun completed frozen evaluations unless a separately stated verification need justifies doing so. Avoid exposing held-out data while exploring ideas.
4. Phase B — Aggressive literature and novelty audit
Search primary literature through 27 October 2026, including NeurIPS, ICML, ICLR, AISTATS, UAI, JMLR, PMLR, OpenReview, and relevant recent preprints.
Begin with the existing bibliography and novelty audit, including work on:

* Anytime-valid risk monitoring, prediction-powered monitoring, WATCH, and RADAR.
* Off-policy confidence sequences and high-confidence policy improvement.
* Conformal policy control and safe reference policies.
* Change-point detection and selective feedback.
* Cost-aware retraining and resource-constrained adaptation.
* Candidate selection under repeated testing.
* Statistical/economic incumbent–challenger switching.
* Delayed or informative feedback and distribution-dependent policy evaluation.

For every closely related paper, verify the bibliographic identity, read the actual method and theorem assumptions, and identify precisely what is already established.
Create a comparison matrix with columns:
Paper | Year/Venue | Exact Problem | Assumptions | Guarantees | Feedback Contract | Intervention Costs | Implemented Comparator | Remaining Gap
Do not use an abstract alone to justify a novelty claim.
If an essential reference cannot be accessed, mark it as unverified.
Challenge each proposed contribution with the question:
"Could a knowledgeable reviewer obtain essentially the same result by combining two existing algorithms without a substantive new insight?"
If yes, reject or narrow the novelty claim.
5. Phase C — Reconsider the research direction
Evaluate at least four paths:
A. A rigorous benchmark/failure-analysis paper explaining where decision-aware monitoring and intervention systems succeed or fail.
B. A targeted method for statistically controlled policy promotion with adaptive information acquisition and explicit switching costs.
C. A narrower result concerning limited/delayed feedback, selective labels, optional stopping, or time-varying policy benefit.
D. A separate, more promising causal-inference, tail-risk, or partially identified decision-making problem that uses existing ShiftLab infrastructure.
For each path, assess:

* Exact problem definition and estimand.
* Closest prior work and defensible novelty delta.
* Whether new theory is actually possible under reasonable assumptions.
* Strongest existing competing baseline.
* Empirical signal already present in the repository.
* Missing data and identification requirements.
* Computational feasibility.
* Main anticipated reviewer objections.
* A minimal falsification experiment.
* Whether the contribution is strong enough to motivate a paper.

Rank directions on intellectual importance, novelty, theoretical tractability, empirical feasibility, and evidence already available.
Do not manufacture a winner. "No compelling new method identified" is an acceptable conclusion.
6. Phase D — First research refinement
Choose the strongest surviving direction.
Write a concrete research proposal containing:

* One dominant scientific claim.
* At most one supporting claim.
* Formal problem setup and filtration.
* A clearly specified feedback model.
* The estimand and appropriate null hypothesis.
* Proposed algorithm, if justified.
* Assumptions required for identifiability and statistical validity.
* A potential theorem, with proof obligations clearly marked.
* Minimal sufficient baselines.
* Three core experiment blocks.
* Primary and secondary metrics.
* Expected failure modes.
* Falsifiable success criteria.

Any proposed statistical guarantee must explain how candidate selection, adaptive sampling, delayed labels, repeated testing, and optional stopping are handled.
Explicitly distinguish:

* An established theorem.
* A plausible but unproved theorem.
* An engineering heuristic.
* An empirical hypothesis.

Do not describe conjectures as demonstrated results.
7. Phase E — Adversarial review and second-pass refinement
Run a structured research review, ideally using ARIS `/research-refine` and an independently configured reviewer.
Review from the perspectives of:

1. A statistical theorist who searches for invalid assumptions and hidden optional-stopping errors.
2. A specialist who knows the closest prior literature.
3. An empirical ML reviewer who challenges the baselines, fairness, data access, and statistical comparisons.
4. A skeptical programme committee member who asks whether this is genuinely a sufficiently important contribution.

Require each reviewer to identify fatal weaknesses, major weaknesses, possible remedies, and the exact evidence required.
Produce a revised proposal that responds to these objections.
Then conduct a second full adversarial review of the revised version, not a superficial wording polish.
Repeat substantive refinement up to five rounds if necessary, but stop if further rounds introduce no new evidence or resolve no significant objections.
An attractive reviewer score is not sufficient for approval. Critical validity and novelty objections must be resolved with reasoning, primary sources, proofs, or experiments.
Maintain a claim-by-claim revision log.
8. Phase F — Final scientific selection
Issue one of four explicit decisions:

* BENCHMARK_PAPER: strongest contribution is a rigorous comparative or failure-analysis study.
* NEW_METHOD: a precise, sufficiently distinct method has survived novelty and feasibility review.
* PIVOT: a different problem has materially stronger support.
* NO_GO: there is insufficient evidence for a defensible publication contribution.

Do not select NEW_METHOD without identifying the concrete published-method limitation and a falsifiable mechanism that could overcome it.
For the selected path, specify what result would cause us to abandon it.
9. Required outputs
Create a new versioned research-refinement directory without overwriting historical audit files.
Deliver:

1. `REPOSITORY_STATE_AUDIT.md`
2. `RESEARCH_EVIDENCE_INVENTORY.md`
3. `PRIOR_ART_AND_NOVELTY_MATRIX.md`
4. `COMPETING_RESEARCH_DIRECTIONS.md`
5. `REFINEMENT_ROUND_1.md`
6. `ADVERSARIAL_REVIEW_1.md`
7. `REFINEMENT_ROUND_2.md`
8. `ADVERSARIAL_REVIEW_2.md`
9. `FINAL_RESEARCH_PROPOSAL.md`
10. `IMPLEMENTATION_READINESS_GATE.md`
11. `CLAIM_TO_EVIDENCE_MATRIX.md`

The final proposal must identify the selected manuscript or research contribution, exact falsifiable hypotheses, required baselines, experimental design, theory obligations, and decision rules.
Also supply a compact machine-readable handoff for the implementation agent identifying approved tasks, rejected approaches, and unresolved blockers.
10. Non-negotiable constraints

* Do not delete or replace functioning research code.
* Do not discard, relabel, or hide negative results.
* Do not modify the frozen holdout protocols retrospectively.
* Do not fit hyperparameters using final test data.
* Do not claim that nominal confidence intervals are anytime-valid without proof.
* Do not assume common-label feedback identifies counterfactual action outcomes.
* Do not claim that research novelty follows from a new application domain.
* Do not conduct expensive sweeps merely to improve a reviewer score.
* Do not develop RIVE or another new algorithm unless the renewed evidence explicitly reverses the existing NO-GO decision.
* Do not push changes or modify the default branch without authorisation.
* Use the repository's scientific-figure policy, including PaperBanana when figures are required.

Final instruction
Your responsibility is not to defend the existing proposal. It is to find the strongest scientifically defensible contribution, even if that means disproving our favorite idea.
Start with repository inspection. Complete the research refinement and independent review before recommending implementation. Return the final decision, unresolved objections, and exact next-stage handoff.
