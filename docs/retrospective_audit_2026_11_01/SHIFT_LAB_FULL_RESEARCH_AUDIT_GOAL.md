# /goal — ShiftLab comprehensive retrospective scientific audit, rectification, and evidence recovery

**Version:** 2026-11-01 | **Target repository:** https://github.com/nl2992/shiftlab | **Starting main tip observed during planning:** `e74fdc33108d8e367094e57a46241a2b2e651caa` (re-resolve at execution; do not assume tip is unchanged).

> **Use:** Paste everything after this introductory sentence into an agent's `/goal` command, if that orchestration command exists, or supply it as the primary autonomous task. The command name is not assumed to be a universal built-in. The entire text is the task specification. An unattended scheduler or autonomous multi-session facility must actually exist before claiming persistence across sessions.

/goal

## 0. Mandate and strict definition of success

You are the lead research auditor, implementation engineer, sequential-inference statistician, and research project manager for the entire ShiftLab programme. Your job is **NOT** to produce another attractive narrative audit. You must reconstruct the historical research evidence, locate premature rejections, prove or refute the asserted validity and novelty claims at their correct scope, implement necessary rectifications, execute justified tests, rewrite affected conclusions **without modifying immutable historical records**, and create a fully traceable audit trail.

**Research objective:** Determine which conclusions in ShiftLab were prematurely discarded through artificial thresholds, incorrectly selected benchmarks, overly conservative or incompatible references, incompletely explored parameter regimes, unsupported interpretations, failed certification logic, inadequate uncertainty analysis, or incomplete real-data testing. Salvage legitimate empirical/theoretical results at their actual scope without relaxing real statistical or scientific obligations. Distinguish (1) discovery, (2) correctness, (3) novelty, and (4) publication readiness.

**Success is conjunctive, not a score:** Every required workstream W00–W17 and acceptance test G00–G17 must be *completed and evidenced*. A workstream is not complete because a report says so. It needs a tracked artifact, the source/result links, verified computations or a documented proof/test where applicable, and review. `BLOCKED` and `INCONCLUSIVE` are valid scientific statuses, but **they are not task-completion substitutes** when the work can be done. If a genuinely external dependency cannot be resolved after the specified attempts, create a detailed blocker and complete all independent work; overall state remains `BLOCKED`, never `SUCCESS`. The goal does not require inventing a new method or manufacturing positive results. It requires honest completion of the audit and all feasible corrective actions.

Do not stop at the first weak/negative finding; do not repeatedly search indefinitely for a positive effect. Continue through a finite, precommitted task ledger. Do not make arbitrary ≥10% relative gain, ≥50% oracle-gap closure, ≥1.5× growth, +10-point power, or ICML-worthy novelty a universal gate on *scientific discovery*. Such thresholds can remain historical registered outcomes or justified application-specific decision thresholds, but never be retroactively redefined as proof that an effect does not exist. Equally, do not loosen a nominal Type-I error constraint, change a null, omit multiplicity corrections, or re-use exposed confirmation data to turn a failure into a success.

### Hard invariants

1. **Preserve original evidence.** Never edit, delete, rename, or overwrite frozen protocols, source output manifests, seed partitions, historical verdicts, original reports, or provenance files to conceal or reverse a finding. Place corrections in additive, dated, linked errata / supersession documents. A code fix must have an explicit before/after difference and an independent test. If an original document requires an attention banner, change only an expressly permitted explanatory header, never the original results; otherwise use new index documents to point to supersessions.
2. **Reproducibility.** At every stage log commit SHA, branch/worktree, clean/dirty status, source file hashes, protocol hash, config, package lock, Python/device versions, seed IDs, raw-data IDs/checksums where legally permitted, wall-time, result file paths, code command, and reviewer. Never cite the parent programme's reported number as if independently re-run.
3. **Valid inference.** Define estimand, null, sigma-field/filtration, observed/free inputs at each decision time, action predictability, issue/release clocks, missingness, query propensity and its lower bound, candidate/reference version, costs, available counterfactual losses, dependence assumptions, stopping rule, and exact coverage/false-alarm claim. Different-null methods may be qualitative references only.
4. **Separation of data uses.** Historic development / exposed data may be reanalysed for explanatory or descriptive purposes only. Any fresh hypothesis motivated by it must be labelled post hoc, then frozen before unexposed validation. A new dataset may not be called unexposed merely because its seed is fresh if its generator, hyperparameters, design, or selection rule was chosen using earlier outcomes.
5. **Respect third-party material.** Read actual primary papers and published implementations where obtainable. Record inaccessible sources as unverified, do not infer absence of novelty from search snippets. Observe licence/access restrictions; do not commit CRSP, licensed logs, raw sensitive data, credentials, or huge binary archives. Do not exfiltrate proprietary material through reviewers.
6. **Research code over rhetoric.** Every programmatic defect needs a regression test; every claim-correction needs a claim-to-evidence trace; every unverified paper theorem needs a proof/audit or explicit downgrade; every proposed new confirmation needs a separately frozen protocol and registered fresh seeds.
7. **Git safety.** First inspect repo guidance, user permissions, Git state, open worktrees, and remote. Work in `audit/shiftlab-retrospective-rectification-2026-11-01` (or a conflict-free equivalent) forked from fresh `origin/main`. Commit logical slices. Never force-push, rewrite history, modify the user's dirty worktree, merge into `main`, open destructive PRs, or start high-cost GPU sweeps / bulk downloads without actual authorization and available resources. A remote branch may be pushed only if permitted by the hosting workflow; otherwise keep local commits and report them. Do not assert that a push/merge happened without evidence.
8. **No invented autonomy.** If the agent runtime cannot persist or resume, save an atomic checkpoint and exact restart instructions. Do not claim a future notification will arrive unless a scheduler is actually configured. End only with `SUCCESS`, `BLOCKED`, or `INCOMPLETE`; never `SUCCESS` on documentation-only work that leaves required analysis unperformed.

## 1. Initial source map (verify dynamically, do not hardcode existence)

### Project-level guide and history

- `AGENTS.md`: scientific scope, clocks, handling of raw/licensed data, tests, visual generation rules.
- `README.md`, `docs/research_charter.md`, `docs/budgeted_switching_research_goals.md`, `docs/next_phase_plan.md`, `docs/methods_and_assumptions.md`.
- `docs/algorithm_search_exit_ledger.md`, `docs/phase_report_stratified_monitor.md`, `docs/data_efficient_edetector_prescreen_{protocol,results}.md`, `docs/gated_monitor_comparison_results.md`, `docs/gated_monitor_null_calibration_results.md`.
- `papers/shiftguard_unified/{decision_gate_report_2026-10-26.md,method_decision.md,programme_completion_audit.md,integrated_results.md,claims_and_limitations.md,claim_evidence_map_v1.md,evidence_inventory.md,novelty_audit.md,real_data_inventory.md}`. Paths may differ: discover by recursive filename/content search if not present.
- `docs/research_refinement_v1/{BRIEF.md,LOOP_CONTROL.md,FINAL_RESEARCH_PROPOSAL.md,CLAIM_TO_EVIDENCE_MATRIX.md,RESEARCH_EVIDENCE_INVENTORY.md,PRIOR_ART_AND_NOVELTY_MATRIX.md,ADVERSARIAL_REVIEW_1.md,REFINEMENT_ROUND_1.md,REFINEMENT_ROUND_2.md}`.
- `docs/research_refinement_v1/stage0/{STAGE0_SUMMARY.md,ERRATA.md}` and `docs/research_refinement_v1/stage1/{STAGE2_RESULTS.md,P1_E2_protocol.md,P2_E3_protocol.md,P3_E4_protocol.md}`.
- `configs/seed_registry.yaml`, `src/shiftlab/seed_registry.py`, `tests/test_seed_registry.py`, `docs/research_refinement_v1/stage0/T0.2_e1_verification.md`; inspect all relevant seed manifests, including branch-only ones.

### Main promising-directions / certified-switching package

- `docs/promising_directions/{00_REPOSITORY_AUDIT.md,02_LITERATURE_AND_NOVELTY_AUDIT.md,04_EXACT_ORACLE_SEPARATION.md,05_PAIRED_CERTIFICATION_THEORY.md,06_H2C_AND_HG_REPRODUCTION.md,07_MATCHED_BASELINE_COMPARISONS.md,08_SYNTHETIC_DEVELOPMENT.md,09_FROZEN_CONFIRMATION.md,10_REAL_DATA_RESULTS.md,11_ADVERSARIAL_REVIEW.md,12_NOVELTY_DECISION.md,13_A2_BRANCH_CONFLICT_THEORY.md,14_FAIR_REEVALUATION.md,15_REAL_DATA_ADMISSIBILITY.md,15b_FETCHED_DATA_ADMISSIBILITY.md,16_REAL_DATA_RESULTS.md,16_REAL_DATA_RESULTS_APPENDIX.md,FINAL_RESEARCH_REPORT.md,RESEARCH_LEDGER.md,RESEARCH_STATE.json}`.
- `docs/promising_directions/protocols/` including B2 and B3 registered protocols; `docs/promising_directions/results/{b1,b2,b3,a1b,a1d,a2,a3c,adversarial_review}/` where available.
- `scripts/promising_directions/{b1_certified_switching.py,b3_real_data.py,a1_exact_separation.py,a1b_growing_family.py,a1c_alpha_mechanism.py,a1d_mixture_comparator.py,a2_binding_alpha_screen.py,a3_calendar_certificates.py,a3b_prelabel_mixture.py,a3c_b4_mixture_bounds.py,research_loop.py}`.
- `tests/promising_directions/`, and registered protocol SHA/code pin records for B3 (`19f1090` registration; `041bc26` P3b implementation; `475bf47` run; current main merge `e74fdc3` observed during planning).

### Failure Atlas and constrained switching

- `docs/failure_atlas_v1_{protocol,ledger}.md`, `docs/failure_atlas_onset_multiplicity_bound_v1.md`, `docs/failure_atlas_straddle_theory_v1.md`, `docs/switching_*` (theory, novelty, eligibility, two-law game, LP, risk frontiers, reversal, economic benefit).
- `src/shiftlab/dive/{failure_atlas.py,atlas_components.py,atlas_r6_baselines.py,causal_switching_game.py,switching_explore.py,eprocess.py}`; `scripts/{run_failure_atlas_loop.py,run_atlas_mechanism_check_v1.py,run_atlas_cycle4_map_v1.py,run_atlas_rvalid2_reclassify_v1.py}`; `tests/{test_failure_atlas.py,test_atlas_cycle4_map.py}`.
- `outputs/failure_atlas_v1*/` for cycle 1–5 if present. The absence of a cycle-5 output in main is not proof it never ran in a branch/worktree or Git-ignored local path.
- `docs/lane_b_burst_allocation/` and `docs/research_refinement_v1/stage1/STAGE2_RESULTS.md` for burst and intervention decision mechanisms.

### HG, H2c, combinations, SOTA benchmarking, data

- `docs/hgxh2c/{00_ANCHOR_SPEC.md,01_BASELINE_AUDIT.md,02_NATIVE_REPRODUCTION.md,03_BASELINE_REGISTRY.md,PROTOCOL.md,THEORY_AUDIT.md,NOVELTY_AUDIT.md,FINAL_REPORT.md}` where present.
- `src/shiftlab/hgxh2c/{contract.py,engines.py,baselines.py,grammar.py,registry.py,search.py,stats.py,evaluate.py,freeze.py}` and `scripts/hgxh2c/{pipeline.py,stage2_benchmark.py,stage3_search.py,stage4_confirm.py,refreeze_frontier.py,make_report.py}`; `outputs/hgxh2c/` may be untracked, ignored, local, or held on another branch.
- `docs/{hg_validation,hg_v2,h2c_next,h2c_restart,icml_sprint,sota_synthetic_search,rpoq_next}/` (discover complete case/branch-sensitive paths); `src/shiftlab/sota_search/`, `outputs/{sota_search,gap_closure}/`.
- `DATA_DICTIONARY.md`, `docs/cross_device_data_access.md`, `data/reports/{data_inventory.csv,experiment_readiness.md,data_quality_report.md}`, `src/shiftlab/data/{streaming.py,label_availability.py,tasks.py,real/,synthetic/}`.
- `papers/shiftguard_unified/` real-data and SOTA fidelity / logged bandit / EIA / CRSP / MOPE material; distinguish retrospective from point-in-time and causal eligibility.

### Branch census (verify branch existence and tip; not all findings are necessarily on `main`)

Search all remote/local branches, specifically:
- `research/shiftlab-promising-directions-2026-10-30`
- `research/shiftlab-icml-method-sprint-2026-10-30`
- `research/shiftlab-sota-synthetic-search-2026-10-29`
- `research/shiftlab-sota-local-checkpoint-2026-10-30`
- `research/hg-validation-and-novelty-2026-10-30`
- `research/hg-decision-aware-betting-v2`
- `research/h2c-strong-baselines-and-generalization-2026-10-30`
- `research/h2c-restart-risk-certified-2026-10-30`
- `research/rpoq-s1-fatal-flaw-audit`
- Any other related branch discoverable from `git branch -a`, `git log --all`, PR history, and `docs/icml_sprint/HANDOFF_AGENT_PROMPT.md`; prior local unpushed worktrees must be checked if accessible, without modifying them.

Before relying on a URL or a filename above, confirm the content/branch. Use `git ls-files`, `git grep`, `find`, `git log --all -- <path>`, and checksum tools. Maintain a `source_catalog.csv` with status `FOUND_MAIN`, `FOUND_BRANCH`, `FOUND_LOCAL`, `GITIGNORED`, `MISSING`, `ACCESS_DENIED`, or `OUTDATED_POINTER`. A path not found is a locator problem first, not proof a result does not exist.

## 2. Required workspace and output contract

Create `docs/retrospective_audit_2026_11_01/` on the audit branch with at least:

```
00_GOAL_AND_GATES.md
01_SOURCE_CATALOG.csv
02_RESEARCH_LINEAGE.md
03_CLAIM_MASTER_LEDGER.csv
04_GATE_AND_THRESHOLD_AUDIT.csv
05_BENCHMARK_INFORMATION_AUDIT.csv
06_SEED_DATA_EXPOSURE_AUDIT.csv
07_VALIDITY_AND_ESTIMAND_AUDIT.md
08_REPRODUCIBILITY_AND_CODE_DEFECTS.md
09_FRESH_VALIDATION_PLAN.md
10_REVISED_FINDINGS.md
11_RETRACTION_AND_SUPERSESSION_INDEX.md
12_LITERATURE_THEOREM_MATRIX.csv
13_PAPER_PORTFOLIO.md
14_INDEPENDENT_REVIEW.md
15_FINAL_DECISION.md
16_RUNBOOK.md
TASKS.md
STATE.json
EXECUTION_LOG.jsonl
ARTIFACT_MANIFEST.json
```

Add auditable tests and scripts under `tests/retrospective_audit/` and `scripts/retrospective_audit/`; put non-sensitive lightweight results under `outputs/retrospective_audit_2026_11_01/` only if repository policy permits. Do not add fake placeholders: if a named file is not relevant, explicitly mark it N/A with justification and use a real artifact where necessary.

Required `03_CLAIM_MASTER_LEDGER.csv` fields: `claim_id,topic,verbatim_historical_claim,claim_type,source_path,branch,source_commit,source_lines,original_gate,original_verdict,estimand,null_class,filtration,feedback_regime,comparison_set,metric,point_estimate,ci_or_bound,replication_status,seed_exposure,data_exposure,validity_status,novelty_status,practical_value,corrected_scope,proposed_verdict,correction_reason,corrective_action,new_experiment_id,reviewer,artifact_links,status`.

Statuses must be controlled vocabularies, not prose-only: `HISTORICAL_REGISTERED_FAIL`, `HISTORICAL_REGISTERED_PASS`, `UPHELD`, `NARROWED`, `SUPERSEDED`, `WITHDRAWN`, `REOPEN_FOR_EXPLORATION`, `REQUIRES_VALIDITY_REPAIR`, `INCONCLUSIVE`, `NOT_YET_AUDITED`, `BLOCKED`. Preserve BOTH the historical gate outcome and the present interpretation.

Required `04_GATE_AND_THRESHOLD_AUDIT.csv` fields: `gate_id,source,original_rule,gate_role,registration_time,why_this_cutoff,metric_and_units,statistical_basis,decision_cost_basis,selection_or_power_issue,result_near_boundary,counterfactual_descriptive_grade,corrected_interpretation,requires_new_test,approval_and_freeze_state`.

Use `TASKS.md` as the authoritative live checklist. Every item must include: unique ID, dependency, owner, evidence source(s), exact action, prescribed outputs, validation command/check, expected acceptance criteria, state, observed results, blocker category, next action, and related commit SHA. Maintain resumable `STATE.json` with last completed stage, unfinished IDs, manifest hashes, last test commands, ready-to-run next task, and unresolved blocking questions. Every decision transition gets an append-only execution log line.

## 3. Workstreams, exact steps, and acceptance tests

### W00 — Snapshot, isolation, resources, permissions [G00]

- [ ] Record current `git status`, `git rev-parse HEAD`, remote URLs, remote branch tips, active worktrees, staged/unstaged/untracked files, ignored outputs, local environment, runner/test commands and available CPU/GPU.
- [ ] Read `AGENTS.md`, research charter, current goals, data permissions, and any branch-specific instructions. Identify conflicts between old and new directives; the newer explicit user goal governs the task, while old experiments remain immutable.
- [ ] Create separate audit branch/worktree without overwriting user changes. Install nothing unusual and download no large datasets without permission.
- [ ] Discover exact main/branch/local source paths and create the source catalog.
**G00:** A clean, isolated audit worktree exists; current source commit recorded; all known source groups listed with resolution statuses; no existing user file or frozen result altered.

### W01 — Exhaustive programme and verdict census [G01]

- [ ] Traverse every `docs/`, `papers/`, `configs/`, `scripts/`, `src/`, `tests/`, and `outputs/` subtree; capture historical `PASS`, `KILL`, `NO-GO`, `STOP`, `MIXED`, `INCONCLUSIVE`, `conditional go`, `novel`, `invalid`, `uncertified`, and `not worth` decisions (case-insensitive, plus synonyms).
- [ ] Group duplicate phrasing into distinct scientific claims, but keep all source references and dated versions.
- [ ] Reconstruct decision chronology: original proposal, preregistration, execution, critique, amendment, supersession, newer empirical result; include branch-only and PR-only records.
- [ ] Detect contradictory current statements, e.g., `FINAL_RESEARCH_REPORT.md` historical negative heading versus `14_FAIR_REEVALUATION.md` and new B3 outcomes; label a correction as `SUPERSEDED`, not falsified if the historical gate was correctly applied.
- [ ] Ensure findings from Paper 1, Paper 2, Paper 3, integrated ShiftGuard, E2/E3/E4, RPOQ, Failure Atlas, HG/H2c, HG×H2c, A1–A3c, P3b/B3, and CRSP/EIA are represented.
**G01:** A complete master claim ledger plus source-count and branch-by-branch coverage summary; an automated search confirms no unresolved matching historical decision documents; reviewers inspect omissions. No broad `NO-GO` without explicit scope.

### W02 — Gate, effect-size, and early-termination audit [G02]

- [ ] Enumerate every artificial/administrative numeric rule: 10% average net-cost, 50% gap closure, 1.5× evidence growth, +10 detection points, three-point slope/trend rule, zero-loss across all regimes, all-frontier dominance, tight alpha grid, and any hidden stop condition.
- [ ] Classify each gate as statistical validity requirement, preregistered confirmatory criterion, research-priority screen, resource ceiling, practical utility threshold, or publication aspiration. Only the first two can govern the original confirmatory outcome, and none should be silently discarded.
- [ ] Check power of short screens and near misses; compute continuous effect and interval even if gate fails; separate `passed registration` from `meaningful effect`, `novel` and `worth following up`.
- [ ] Explicitly re-audit A1b's positive gap at T=11 (4.641% under alpha=0.20) that missed 5% continuation; the 48% versus 50% Failure Atlas closure case; WP2 1.5× threshold; WP3 small 20-seed screen; and P3/P3b B1/B2 10% classification.
- [ ] For any post hoc reclassification, state it is a *new interpretation*, not a retroactive protocol pass. If proposing an alternative threshold for future runs, justify by loss/utility/precision or preregistered science and freeze new seeds.
**G02:** Exhaustive gate register; all near misses evaluated continuously; no unchanged historical test is called newly confirmatory; documented decision on whether each early-stopped branch requires another study.

### W03 — Comparator, information-set, and fairness audit [G03]

- [ ] For every prominent result, construct a matrix of candidate and competitor: target null, statistical class, free information, labeled information, release timing, budget, cost, model pair, fallback action, intervention latency, tuning effort, reference selection, calibration, stopping opportunities, and guarantee.
- [ ] Reproduce missing strong comparators where viable, with author-code checks: CAMS-style disagreement queries, Xu-style active anytime-valid procedures, fixed-batch paired tests with *valid* predeclared sampling/stopping assumptions, SR/CUSUM/Page–Hinkley calibrated alarms, economic retraining policies, constrained switching/value-of-information control, separate HG/H2c, joint contextual ONS/Kelly, multivariate gambling, and appropriate delayed-feedback R6 methods.
- [ ] Do not compare different-null methods as equal validity baselines; if testing a joint intersection null, show how it differs from individual cost and Brier nulls. Do not grant an oracle knowledge as deployable baseline; display oracle headroom separately.
- [ ] Check WP3's 55% versus 100% detection at 5%-budget/late-onset setting: retain a valid negative result for this specific controller even if advancement gate is relaxed; report resource savings and Pareto frontier separately.
- [ ] Check B2 `BEST` excluded a fair strong paired test and that in-sample baseline tuning is not mistaken for out-of-sample dominance. Check B3 P6's assumptions; do not say P3b wins all comparators when P6 wins on five streams.
- [ ] Check selection of best comparator on evaluation seeds for winner's curse and adjust with train/dev/frozen independent selection or nested resampling.
**G03:** Comparator parity cards for every headline result; every benchmark marked `FAITHFUL`, `TASK_ADAPTED`, `FORMULA_VERIFIED`, `INSPIRED`, `DIFFERENT_NULL`, `INVALID`, or `MISSING`; stronger baseline implemented/tested or logged as an explicit unresolved limitation; valid match-by-match confidence intervals available.

### W04 — Statistical validity, estimands, and certification [G04]

- [ ] Recheck all theorems and implementations for history-predictable stakes, query decisions, issued propensities, release-time conditioning, unresolved-prefix versus out-of-order outcomes, selection on available labels, endogenous policy transitions, resetting after intervention, anytime validity and repeated comparisons.
- [ ] Distinguish eventwise conditional mean null from marginal/stationary null; demonstrate the 20.8% false promotion under the persistent marginal-null stress does *not* contradict conditional-null results and forbids any broad unconditional safety claim.
- [ ] Test nominal risk on genuine **boundary** null streams, not only strict/safe nulls. Separate analytical e-process guarantee from Monte Carlo calibration and from research-level `SAFE` cost definitions.
- [ ] Revisit Q2 integrated net-benefit claim: actual increment `E[I_t(g_t-s)|F_{t-1}]<=0` does not certify the whole switching-cost utility. Decide whether to revise the estimand or implement and prove the correctly costed increment. If unproved, withdraw full-net-benefit certification.
- [ ] Audit Q1→Q2→Q3 composition: verify conditional validity under adaptive handoffs, alpha spending, multiple candidate rounds, model versions, delayed feedback and rollback. No blanket union-bound claim without conditions. Audit HG×H2c J combiners: fixed mixtures/Bonferroni valid under stated assumptions; unguarded products of e-processes **not** generally valid. Never bypass an invalidity finding by rebranding it as conservatism.
- [ ] Build explicit validity table by scenario: iid, Markov/autocorrelated, outcome-dependent delays, selective labels, adaptive querying, repeated switches, multiple candidates, unknown nominal risk, information leakage, policy-responsive stream, and real data.
- [ ] Check proof/simulation correspondence with regression tests including adversarial counterexamples. If a proof is incomplete, mark `ARGUED`/`UNPROVED` and forbid `CERTIFIED` in dependent text.
**G04:** Exact null and filtration written for every certification claim; boundary-null tests and counterexamples executed or blocked with evidence; every unresolved invalid guarantee withdrawn/downgraded or actually repaired; proof/claim correspondence independently checked.

### W05 — Seed reuse, leakage, chronology, provenance [G05]

- [ ] Read the Stage 0 seed registry finding: **103 overlapping pairs, 101 previously undisclosed, including 51 cross-study reuses**; independently regenerate overlap detection over *all* main/branch/local output manifests and test sets.
- [ ] Classify overlap severity: identical seeds + identical generator/config, prefix sharing, shared data tape, reused development after viewing, leakage into confirmation, harmless reproducibility reuse, or not ascertainable. A reused integer seed is not alone proof of data reuse; track stream generation hierarchy.
- [ ] Check all frozen protocol dates against actual first read of labels/holdouts; distinguish previously exposed Gas/elec2/criteo from truly locked windows; check the `B3` declared locked windows and pair selection.
- [ ] Validate `event_time`, `request_time`, `release_time`, `prediction_time`, `action_time`; train-only transforms and ordering; source-clock plausibility for spam, bank, airlines, rialto and weather. Do not claim prospective timing when a release contract is imposed.
- [ ] Rehash key output/manifests, verify snapshot code parity and identify uncommitted-run cases. If raw unavailable, classify metadata-only check and identify required copy.
- [ ] Restrict any seed-tainted results to development/descriptive use; create fresh allocations only after preregistration for new confirmation.
**G05:** Seed-collision graph and leakage/exposure matrix, per-claim impact verdict, independent reproducibility checks, no exposed evidence relabelled as independent confirmation.

### W06 — Historical code/claim errata and defect repair [G06]

- [ ] Reassess all 10 Stage 0 errata and check whether downstream reports still repeat the wrong claims (e.g., inaccurate seed range, stale rollback status, miscited prior work, error in E3 counts, propensity interpretation).
- [ ] Revisit documented P4 pilot reward/cost-matrix direction error, HG finite-support cap, HG×H2c frontier cross-track and DIFFERENT_NULL leakage, Atlas R_law reference defect, R_valid2 reference-classification artifact, and A1d vacuous/upper-bound mistake.
- [ ] For each confirmed code defect: add a failing minimal regression test against a pinned old commit or fixture, implement minimal fix on audit branch, run direct and whole relevant test suites, compare before/after, regenerate only **development** outputs by default, and append an erratum with invalidated downstream artifacts.
- [ ] Maintain `bug_id`, `severity`, `affected_versions`, `source_line`, `old_behavior`, `correct_behavior`, `test`, `fix_commit`, `output_re-run_status`, `claims_changed`.
- [ ] Do not silently change model estimand, budget, cost units, alpha, data construction, or experiment clocks while calling it a bug fix. This requires a new protocol/version.
**G06:** Every high-severity defect has a regression test, code fix or explicit ruled-out finding, and claim impact; no missing errata propagation into current publication drafts.

### W07 — P3b certified switching / B1-B3 audit and upgrade [G07]

- [ ] Independently recompute B1/B2 world means, confidence intervals, exact boundary-null FAR, W1–W4 breakdown, P3 cap `p_min/2` versus P3b propensity-matched cap, and all published caveats. Track selected four-world weights and weaker-signal generator.
- [ ] Recompute B3 from `results/b3/summary.json` and per-episode JSONL if accessible, including all seven streams, P0/P1/P2/P3b/P6, WIN, SAFE, episode counts, promotion/rollback, label spend, 95% uncertainty, sensitivity B=400 and switching cost 20; confirm P6 wins five of seven.
- [ ] Challenge pseudo-replication: one spam episode, three weather episodes; query-randomisation seeds do not constitute independent source episodes. Report within-episode uncertainty separately from across-episode generalisation; do not use seed-level bootstrap to imply population-level precision.
- [ ] Check the `SAFE` criterion exactly: `P3b <= P0 + P3b query spend + 0.02*P0`; distinguish this from non-inferiority under independently justified costs or validity under the conditional null.
- [ ] Implement faithful, applicable published and strong simple alternatives (CAMS/Xu/task-adapted, risk-valid sequential batch alternative, paired SR/CUSUM, disagreement-aware P2, budget-matched economic switch/retrain) with identical observation opportunities and versioning.
- [ ] Identify realistic challenger headroom *before* opening new test sets. Freeze two structurally different synthetic generators, one independent real-data or quasi-real stream with sufficient independent episodes, and sensitivity across signal size, disagreement rate, delay, fees and budget. If no new adequate stream exists, report limited transfer; do not invent one.
- [ ] Run fresh confirmation only after a protocol, comparator software, seed registry, and power/design analysis are locked. Report cost, economic regret, false promotion, timing, net utility and Pareto trade-offs, not a forced 10% cutoff.
**G07:** B3 aggregate and episode accounting reconciles; factual current narrative includes three WIN/seven SAFE plus five P6 losses, imposed costs/delays, episode limitations; any newly claimed superiority is independently confirmed against valid strong baselines.

### W08 — A1/A1b/A1c/A1d/A2/A3/A3b/A3c theory reassessment [G08]

- [ ] Recover exact game, full/joint policy information set, slot-set-restricted calendars with adaptive skipping, strict forced open-loop schedules, public coin randomisation and calendar mixtures. Distinguish all three. No mislabeled comparator.
- [ ] Recompute representative exact rational/LP cells; confirm J ≤ C_mix ≤ C*; audit feasibility, numerical solver status, timeout/node cap and equality tolerance; no extrapolation from unsolved T=12.
- [ ] Retain historical A1 `KILL` for its grid but withdraw global `no adaptive value` reading. Revisit A1b T=11 4.641% with alpha=0.2, risk-specific alpha dependence, A1d lower-convex-envelope correction, exact lower/upper bounds in A3c.
- [ ] Verify per-instance certificate (Proposition 6), chain reduction (Theorem 7), and assumptions in `13_A2_BRANCH_CONFLICT_THEORY.md`; in particular explain why the Lemma 2 bound is zero/vacuous, and distinguish original upper-only from later proven two-sided gap.
- [ ] Check known 108 B=3 tight cells, 54 B=4 alpha=.05 cells, 54 B=4 alpha=.10 noncertified cells, and six A3c positive mixture-gap intervals [.71%,1.21%]. Do not generalize to all HMMs or larger budgets.
- [ ] Recheck claimed F5 intermediate-alpha lower bounds (5.07%, 4.68%) against actual source `results/a1d/LOWER_BOUNDS.md`, source audit and arithmetic. Calculate independently where feasible.
- [ ] Audit literature on constrained POMDPs, adaptive sensor scheduling, chance-constrained acquisition, stopping, sequential trials, risk-ledger dependent observation, model-level thresholds; identify what is already known and which theorem would be genuinely new.
- [ ] Explore `Conjecture 8` only via a properly stated model-level sufficient condition and proof/counterexample; if not solvable, remain `OPEN` with precise obstacles, not `PROVED`.
**G08:** Corrected theorem ledger, exact instance certificates reproduced or independently inspected, valid comparator hierarchy, no vacuous bound cited as proof, novelty status determined as far as accessible primary sources permit.

### W09 — Failure Atlas cycles 1–5: recover avoidable improvement and real cost of validity [G09]

- [ ] Re-run only minimal checks needed to replicate the documented R_law reference defect and cycle-2/3/4 classification transitions. Preserve the original `shared_failure` counts and the fact **116 of 123** moved to `cost_of_validity` under R_valid, without interpreting that as mathematical necessity.
- [ ] Audit R_family's empirical-only calibration and oracle family knowledge. Audit R_valid/R_valid2 boundary-null rates, unused alpha, R_best within-sample best-of-two winner's curse, cost of comparator selection, null-twin distribution and reference-tape equivalence.
- [ ] Independently reproduce cycle-3 fresh-seed straddle repair (cost candidate 0.2781, ablation 0.3933, best_safe 0.3733, R_family 0.1838, R_valid 0.3541; closure 0.503; one cell) and relevant neighbours, but keep it as *development mechanism finding*. Show gain sign versus delays 1, 10, 50; distinguish labels saved from acquisition latency.
- [ ] Preserve negative straddle mean across full grid and triggered-Kelly late-onset harm; a conditional effect cannot be promoted to a universal win.
- [ ] Execute/locate registered Amendment 6 cycle-5 exact finite-horizon cost-of-validity study if feasible: HMM analogues T in {6,7,8}, B in {2,3,4}, delay {1,2}, risk alpha=.1, onsets and magnitudes per frozen protocol. Calculate V_free (unconstrained), V_valid (risk-constrained), CoV=V_valid−V_free, RC=cost(R_valid)−V_valid, gap=cost(best_safe)−V_valid; verify solver duals/primal residuals, simulation match and monotonicity. Record unsolved cells and why.
- [ ] Do not extrapolate T≤8 exact results to T=1000. If RC>CoV in a majority of solved registered cells, report the registered finding, but also sensitivity to distributions, prior, and validity-matched reference. If not, maintain conditional/narrow verdict.
- [ ] Audit Amendment 6 dependent-outcome family 3 and informative-release family 4, including null classes; label marginal-null violations as misspecification, not contradiction. Use original frozen protocol if running it; no post-result tuning on confirm pool.
- [ ] Reclassify the 48%-closure and all 1%/3%/near-threshold improvements as `PARTIAL_IMPROVEMENT` when warranted; do not call them `REPAIR` under the old ≥50% rule or infer efficacy from a selected best cell.
- [ ] Benchmark strongest applicable R6 wrappers and hard-budget pacing where implemented; mark adaptation vs source fidelity, and distinguish uncertified ungated utility from certified comparisons.
**G09:** Real cost-of-validity attribution explicitly separated from conservative-reference artifacts; cycle-5 status resolved or blocked with exact resource reasons; straddle and triggered-Kelly conclusions scoped by delay/onset, all past registered outcomes intact.

### W10 — HG and H2c independent audit [G10]

- [ ] Trace HG, H2c, parent PPRM, discounted Kelly, cost/Brier ONS, true-cost thresholds, Brier guidance and the published PPI betting family through main and research branches.
- [ ] Recompute H2c G5 from per-seed data (reported +0.086 [0.059,0.113] power @10% labels; +0.094 [0.063,0.125] @20%) and compare per-cell local winners with a frozen selection rule. Preserve significant within-class improvements without claiming novel engine.
- [ ] Verify H2c cost-null proof and implementation test, clipping, unknown-nominal calibration, signal alignment/misalignment, AR dependence, delayed outcomes, Gas negative transfer, and lag before alarm. State the equivalent substituted-moment discounted-Kelly representation.
- [ ] Recompute HG parent gains (reported +0.029 / +0.052) and harm-world reduction, confirm finite-support cap, correct erroneous raw ~21/24 interpretation, and retain lack of strong superiority over Page–Hinkley/CUSUM and dependence FAR up to .23.
- [ ] Repeat only necessary synthetic confirmation using new independently registered seeds if claims exceed old development results. Test cost-null and Brier-null *separately*.
**G10:** HG/H2c factual results independently reconciled or marked analysis-only; power, utility, validity, novelty, dependence and calibration-size limitations explicitly distinct.

### W11 — HG × H2c bidirectional grammar and completion audit [G11]

- [ ] Locate stage 1–4 outputs in main, all branches, ignored local worktrees and remote artifacts; do not infer failure from missing `outputs/hgxh2c/stage4/confirmation.json` on main.
- [ ] Verify stage-1 baseline source fidelity and missing author-code reproductions in `02_NATIVE_REPRODUCTION.md`; check `03_BASELINE_REGISTRY.md` fidelity classification and different-null exclusions.
- [ ] Verify A3 invalid product combiner excluded; A4 wrong-track and DIFFERENT_NULL frontier contamination fixed and the old frontier archived; A5 primary validity-compatible versus secondary empirical alarm comparator separation. Re-run unit tests on frontier composition.
- [ ] Audit grammar equivalences, cross-track stake/query/restart hook predictability and joint-filtration assumptions; exact equivalence to contextual ONS/multivariate/PP constructions where appropriate. The raw grammar is huge: evaluate actual canonicalisation, resource budgets, successive halving bias and whether good Q/R candidates were prematurely filtered.
- [ ] If final confirmation does not exist and resources/permissions allow, execute the registered staged protocol from a corrected clean frontier with frozen finalists, complete independent null risk calibration and disjoint seeds; if frozen conditions were compromised, establish a new registered protocol and fresh seeds, not reuse the former confirm block.
- [ ] Produce per-regime J-cost, power, delay, labels, negative-transfer, sensitivity, ablations, cross-risk alignment shuffled controls, parity with independent HG+H2c and contextual ONS, strong guaranteed baselines, and secondary CUSUM/PH comparators.
- [ ] Classify separately: meaningful composition, narrow method novelty, monitoring-only advantage, economic decision advantage, null-class guarantee, publication readiness. Lack of broad dominance is not evidence of no conditional benefit.
**G11:** A complete branch-inclusive stage-status record and exact missing/deployed artifacts; all frontier errors repaired; stage-4 confirmational claim only when actually run and integrity verified.

### W12 — Original Paper 1, E2/E3/E4, integrated action loop [G12]

- [ ] Revalidate Paper 1 WP1: S3 gated-versus-uniform effect and interpretation credited to published DISCERN-style gating; do not invent novelty. Revisit WP2 analytic equality with subgroup composition and WP3 20-seed negative screen, while retaining any resource-efficiency trade-off.
- [ ] Reconcile E2: 20,000-stream burst experiments; fixed better in harmful post-onset bursts, pacing better when harmless early bursts deplete budget; monitor without knowing burst harmfulness. Factor out correct budgets, latency, fixed/pace caps, monitoring null and published comparable burst-aware allocation.
- [ ] Reconcile E3: confirm estimated revert/promote crossover between doses .45 and .60, but verify full economic estimand and distinguish abstention, revert, promote, and certification delay. Build a fair matched-opportunity factorial, not confounded arms.
- [ ] Reconcile E4: no eligible q<1 detectable cells in locked EIA analysis means no sparse-query transfer claim; distinguish structural non-identifiability from a failed method.
- [ ] Audit integrated Q1→Q2→Q3 and rollback: different policy latencies, versioning, rollout and exposure; correct old “full net benefit certified” interpretations, evidence selection/reuse and expected-versus-realized utility errors.
- [ ] If recommending new methods for burst-aware acquisition and state-dependent intervention, write two separate hypotheses, limitations of closest published methods, fixed primary endpoints and new independent test/validation designs. Do not call study design itself a new result.
**G12:** E2/E3/E4 and Paper 1 findings retained or narrowed correctly; no broad premature programme exit inferred from their scoped negatives; exact matched economic action/estimand documented.

### W13 — Real-world eligibility and transfer [G13]

- [ ] Census EIA, CRSP, Gas, Spam, Rialto, Weather, Airlines, Bank, Elec2, Criteo, Folktables, WILDS, Open Bandit, Upworthy and other accessed streams. Record provenance, licences, target, action/outcome observability, independent episodes, timestamp validity, source availability, train/dev/test splits, exposed status and imposed parameters.
- [ ] Determine which streams permit paired fixed-policy losses, which require off-policy estimators, which are retrospective only, and which lack point-in-time release clocks. Never use market returns as verifiable executability or causal shift timing without evidence.
- [ ] Treat B3 five initially unexposed streams and two partly exposed streams according to recorded provenance; because B3 has now been executed, those B3 locked windows are exposed for any *subsequent* hypothesis motivated by outcomes.
- [ ] For research that needs larger independent episodes, find suitable permitted data or label limitation as `NO_ELIGIBLE_SOURCE`; do not silently duplicate one stream into pseudo-independent samples.
- [ ] Run leakage and counterfactual identifiability audit of each proposed new real-data test, including temporal dependence and event clocks; freeze task and metric before opening labels.
**G13:** Complete real-data eligibility matrix; honest conditions on transfer; new validation sources meet independence/clock/licence constraints or are explicitly unavailable.

### W14 — Formal review of literature, theory, and novelty [G14]

- [ ] Collect primary texts, versions, author implementations, theorems and actual algorithm definitions for comparisons already referenced: DISCERN/CAMS, Xu active RCPS, Csillag prediction-powered e-values, Ryu–Wornell vector gambling, PPRM, Timans, DE-CuSum, delayed testing methods, constrained sensing/POMDP, fixed/sample certification, policy switching, adaptive e-processes and family-wise online control.
- [ ] Record citation details, exact assumption, theorem number, comparator behavior, and what the published method already achieves. Remove conclusions from abstract-only searches or vague “prior work covers it” statements.
- [ ] Specifically audit novelty of Prop. 6, Thm. 7, F5 risk-specific branch conflict, A3c gap, straddle delay decision boundary, P3b conditional certification, E2 burst allocation, E3 crossover and HG×H2c cross-channel techniques.
- [ ] Use a sceptical independent theorem reviewer and a separate experimental/statistical reviewer. Each must try to falsify, not merely approve. If external reviewers unavailable, mark review `INTERNAL_ONLY` without fabricating independence.
**G14:** Source-level novelty matrix for each positive method/theorem candidate, with unresolved source access disclosed; theorem corrections and reductions propagated into claims.

### W15 — Re-grade ALL findings without lowering scientific validity [G15]

- [ ] For every row in the master claim ledger give **four separate fields**: effect magnitude/uncertainty, guarantee status, novelty status, and practical value. Add generalisability and data-exposure separately.
- [ ] Preserve null, small, negative and contrary-world effects. Use exact descriptive continuous effects rather than turning an arbitrary 10% cutoff into “no effect”. Report absolute and relative improvement with denominator, paired uncertainty, effect heterogeneity, label counts, delay and net economic benefit.
- [ ] Apply verdicts: `UPHOLD`, `NARROW`, `SUPERSEDE`, `WITHDRAW`, `REOPEN FOR EXPLORATION`, `REPAIR VALIDITY`, or `OPEN BLOCKER`. A near miss is not an automatically positive result.
- [ ] Reassess at minimum F1–F10 in `14_FAIR_REEVALUATION.md`, all A/B/C/D/E/F/G lanes, the original Paper 1 decision and programme-level `NO-GO`, the Atlas classification and HG/H2c/HG×H2c status; update conclusions after any new evidence, retaining old registered verdicts.
- [ ] Produce a contradiction checker linking each current summary line to the latest applicable evidence and its historical predecessor; identify stale statements in README, manuscript drafts, decision logs, summaries, prompts and public-facing tables.
**G15:** Every major finding has exactly one latest audit interpretation with visible history, direct source anchors and independent grade axes; no known contradictory unsuperseded headline remains.

### W16 — Manuscript decomposition and honest publication assessment [G16]

- [ ] Prepare separate claim-constrained candidate paper outlines: (A) budgeted certified model switching / P3b and real-data comparisons; (B) risk-constrained acquisition calendar-optimality, branch conflict, exact adaptivity gaps; (C) monitoring/burst/decision failure benchmark with E2/E3 mechanistic experiments; (D) HG/H2c cross-risk information-transfer only if reproducible results justify it.
- [ ] For each outline define central claim, strongest contrary baseline, empirical evidence, theorem, dependence/null contract, real-data eligibility, nearest literature, remaining decisive experiment, disqualifying outcome, alternative venue/format, and non-claims. Do not rate acceptance probability as fact.
- [ ] Score evidence readiness separately from originality; conference-target aspiration never dictates truth of scientific results.
- [ ] Prefer separate focused manuscripts to a stitched-together claim unless a unifying theorem or meaningful shared method is actually demonstrated.
**G16:** A portfolio of appropriately scoped manuscripts (including viable benchmark/negative manuscripts), with explicit go/narrow/pivot decisions and evidence-gated remaining experiments; no unsupported ICML readiness claim.

### W17 — End-to-end verification, independent criticism, final sign-off [G17]

- [ ] Run project and new audit tests (targeted then full feasible suite), static checks, seed collision detection, CSV schema checks, provenance hash checks, consistency checks, synthetic leak tests, and confirmation separation checks. Capture commands, exit codes and output hashes.
- [ ] Independently recompute samples of all headline figures from underlying per-event/per-seed/episode artifacts. Use exactly the estimator and clustering justified by the unit of independent replication; inspect published figures/tables against numeric source outputs.
- [ ] Assign at least two adversarial reviews: statistical validity/theorem review and experimental design/comparator/data review. Have each produce `FATAL`, `MAJOR`, `MINOR` issues with evidence; correct fatal errors and rerun tests before closing.
- [ ] Verify that all W00–W17 outputs exist with meaningful content, G00–G17 tests pass, source catalog covers all relevant artifacts, every active item in TASKS.md is `DONE` or a genuinely external blocker is recorded, and every changed interpretation points back to preserved history.
- [ ] Produce final summary with: what changed, what held, what was withdrawn, what was newly confirmed, what remains descriptive, real-world relevance, negative outcomes, exact reproduction commands, commits, outstanding blockers, and recommended next scientific actions.
**G17:** A reviewer can reproduce every asserted correction from source/command, no unaddressed validity-critical issue or mislabeled confirmation remains, all independently feasible remediation steps completed, and success is asserted only when no required blocker remains.

## 4. Definition of a CORRECT alteration (accept/reject rule)

An alteration is **ACCEPTABLE** if and only if ALL applicable conditions hold:

1. **Locatable:** Names exact existing source, branch, commit, path/line or artifacts and first observed erroneous interpretation.
2. **Typed:** Specifies whether it is `CODE_BUG`, `CALIBRATION_BUG`, `INVALID_INFERENCE`, `ESTIMAND_CHANGE`, `COMPARATOR_FIX`, `THRESHOLD_INTERPRETATION`, `DATA_EXPOSURE`, `NOVELTY_CORRECTION`, `RESULT_RECOMPUTATION`, or `EDITORIAL_SCOPE`.
3. **Semantically exact:** For scientific claims, states previous and corrected hypothesis, null, metric, unit, population, information set, comparator, delay, budget, outcome variable and intended guarantee; proves why old broad claim does not follow.
4. **Evidence-backed:** Supplies actual proof/check, matched rerun or calculation with executable command, test output and checksum; an opinion, source snippet, or author assertion alone cannot certify a theorem or outcome.
5. **Reproducibly fixed:** If implementation changed, includes failing test before fix, passing test after, compatibility and leakage tests, minimal diff and pinning; new behavior must be versioned.
6. **History-preserving:** Historical protocol result remains unchanged; dated erratum/supersession says exactly what is revised and whether result status is registered or descriptive/post hoc.
7. **Uncertainty-honest:** Confidence level, replicate unit, multiplicity/selection, estimator, effect direction and dependence handled; non-random dataset selections and one-episode results are not assigned across-world confidence.
8. **Comparable:** Baseline has the same estimand, clock, information and feasible budget (or mismatch is transparently a non-like-for-like reference).
9. **Exposure-safe:** Fresh confirmation uses frozen independent data; no recycled looked-at test labels or seeds; past data allowed for diagnosis with appropriate label.
10. **Reviewer-tested:** Competing methodological explanation and strongest counterexample considered; any residual uncertainty explicitly retained.
11. **Propagated:** Latest project overview, claim matrix, scientific report, manuscript outline and relevant implementation notes link to the correction, while old findings are not erased.
12. **No overstatement:** Does not convert marginal-null failures into conditional-null validity, a theoretical sufficient condition into universal optimality, a selected best cell into deployment guarantee, or a meaningful known-method combination into method novelty.

Reject these specific anti-patterns:
- Change `10%` to `3%` in an already-run protocol and declare the original gate passed.
- Retest exposed holdouts and call them new confirmation.
- Drop strong or inconvenient baselines from a Pareto frontier; include different-null tests to inflate difficulty.
- Declare “unavoidable cost of validity” using only a grossly conservative reference.
- Treat all negative or near-zero averages as no value in identifiable positive subgroups.
- Treat a selected lucky subgroup as independently significant without selective-inference correction or a new holdout.
- Declare e-process validity from a few zero-alarm simulations or validate under the wrong null.
- Use hindsight model-selection oracle as if it is a deployable switching policy.
- Replace original experiment output or registered decision instead of recording a supersession.
- Conclude a method is novel because no arXiv keyword result appeared or stop because “DP already exists” without matching hypotheses and algorithm.
- Pretend missing filesystem artifacts were never produced without checking relevant branches/worktrees/ignored datasets.

## 5. Decision logic, work queue and persistence rules

Execute this deterministic loop, not a one-off prompt-response:

```
INITIALIZE:
    verify sources, permissions, Git isolation, and resource limits
    create append-only source/claim/gate/defect task registries
    insert W00..W17 with dependency graph

WHILE any required task is NOT DONE:
    select highest-priority unblocked task whose prerequisites are done
    if task requires unavailable permissions/data/compute:
        do allowed metadata, design, test and small-scope work first
        record exact blocker, attempts, expected input and next restart command
        mark BLOCKED (not DONE); continue independent tasks
    else:
        perform task, save artifacts, run its acceptance tests
        obtain a skeptical reviewer for validity-critical/high-impact claims
        if a test fails:
            create defect + reproduction, implement repair, rerun tests
        if result is negative:
            record it; continue remaining tasks, do not fabricate a win
        if near miss:
            grade continuously and scope; optional NEW protocol only
        if new experiments needed:
            first freeze outcome/units/comparators/seeds, then execute if authorized
        commit one auditable vertical slice; update TASKS.md, STATE.json, LOG
    repeat until no feasible pending work and no defects can be resolved

IF all W00..W17 complete AND G00..G17 pass AND no unresolved critical
validity/claim contradiction exists AND independent reviews signed:
    mark SUCCESS with reproducibility manifest
ELSE IF any external/technical blocker remains:
    mark BLOCKED, list blocker IDs and exact restart instructions
ELSE:
    mark INCOMPLETE with outstanding tasks
```

Run automated checkpoint validation at least after each workstream, after any failure, and before final completion. Do not equate iteration count, elapsed wall-time, or number of tests with success. If a workstream is large, split into subtasks and apply the same gate; use resumable subagents. Use the cheapest competent independent research agents for inventory/primary-paper extraction, senior statistical reviewer for proof/estimand, implementation reviewer for code defects, data reviewer for time ordering and licences, and lead integrator for synthesis. Parallel workers may read independently, but commits to shared paths must be coordinated, and confirmation seeds/heldouts must remain locked from every development agent. Each subagent must submit claims with evidence and tests, not a verdict-only prose summary.

### Delegation and escalation

- **Source librarian:** branch/file census, checksum/provenance, prior results, historical protocol registry; cannot certify novelty.
- **Statistics reviewer:** nulls, e-process proofs, delayed filtration, risk boundaries, CI/selection; cannot alter data or score a paper without evidence.
- **Comparators reviewer:** author-code reproduction, parity, published baselines, null compatibility, budgets.
- **Theory reviewer:** LP exact solver, calendar mixtures, proof gap, literature reducibility.
- **Real-data reviewer:** clocks, leakage, licences, episode counts, B3 reanalysis, independent validation sources.
- **Research engineer:** minimal code repairs, smoke and integration tests, deterministic runbook.
- **Lead:** dispute resolution; source and result integrity, evidence thresholds, decisions, final audit sign-off.

Disagreements go to an `adjudication_id` with both arguments, source evidence, and an explicit resolution or unresolved status. Do not silently pick the most rejection-prone voice, or the most optimistic one.

## 6. Core evidentiary examples that must be checked, not copied as independently verified facts

These are waypoints from the current main-branch audit, not guaranteed truth in an updated checkout:

- B2 P3b **7.67%–10.20%** average reduction against simple preselected policies (the registered 10% gate yielded `MIXED`), conditional null only, and a strong fixed-batch rival.
- B3 registered outcome **WIN 3 / 7, SAFE 7 / 7** (weather, spam, rialto wins); spam 1 episode, weather 3, rialto 16; P3b beats P6 on spam/rialto but P6 is cheaper on remaining five. Imposed costs/delays, not operational guarantees.
- Lane A **A1 original KILL**; A1b at T=11 alpha=.20 **4.641%** below a 5% continuation threshold; later proven per-instance calendar optima for tight risk and **0.71%–1.21%** B4 alpha=.10 gaps in six selected families. Verify F5 lower-bound arguments, correct vacuous lemma.
- Failure Atlas early 116/123 shared-failure reclassification is not a mathematical bound; R_valid may leave much of alpha unused; one straddle mechanism passed a fresh-seed narrow repair check (closure **0.503** vs historical 0.50), but mean effects are small/heterogeneous and novelty questionable. Registered cycle-5 Amendment 6 remains to locate/execute.
- H2c +.086/.094 power against local parents, HG +.029/.052 against its parent, dependence/nominal-risk caveats, exact equivalent betting formulation, negative-transfer cases.
- WP3 at late onset/5% budget **11/20 vs 20/20** for strong simple comparator: genuine scoped underperformance, not a finding to reverse merely because gate was stiff.
- E2 20,000-stream burst trade-off; E3 1,000-seed revert/promote crossover in **(0.45,0.60]**; E4 q<1 transfer inconclusive.
- Stage 0 seed audit **103 overlapping block pairs**, 101 newly disclosed, 51 cross-study. Determine actual severity per pair.
- HG×H2c original stage-2 frontier accidentally admitted cross-track and DIFFERENT_NULL methods; A4/A5 repairs must be checked. Do not claim stage 4 has finished without its outputs.

## 7. Final deliverable template

The final answer delivered to the PI must include all of:

1. **Executive audit verdict**: exact counts of claims `UPHELD/NARROWED/SUPERSEDED/WITHDRAWN/REOPEN/UNRESOLVED` and count of repaired implementation defects, verified outputs, reruns and blockers.
2. **Changed conclusions**: old text, new wording, evidence links, why the change is justified, original registered gate, whether new confirmation exists.
3. **Real recoveries**: scientifically meaningful partial improvements, subgroup and regime effects, per-unit costs, intervals, conditional-null status, independent validation status.
4. **Genuine failures**: any adverse/unfavorable evidence retained, plus strongest baselines and contradictions.
5. **Validity audit**: proof/assumptions/counterexamples for every intended certification; unresolved guarantees withdrawn from abstracts and submissions.
6. **Exact experimental ledger**: dataset, seed block, exposure, simulator family, clock, code commit, comparator source fidelity, result hash.
7. **Theory ledger**: proved / per-instance certified / conjectured / vacuous or corrected / known result / novelty open.
8. **Revised publication plan**: modular paper candidates and evidence-conditioned readiness, not acceptance promises.
9. **Commit and test inventory**: before/after fixes, test commands, full status and branch/PR links if legitimately pushed.
10. **Verified completion matrix**: W00–W17 each with G00–G17, underlying files and independent review signoff; explicit blockers with next commands.

### Last rule

**A successful audit may conclude that no new method was found. It may not conclude that no scientifically useful discovery exists merely because an arbitrary gate was missed.** It may not conclude that a method is valid because the effect is large, or that it is novel because it is useful. Do not mark the `/goal` complete until every feasible step has actually been completed, every critical claim has been appropriately repaired or withdrawn, and every remaining external dependency is transparently recorded without a false success claim.
