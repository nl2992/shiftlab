# ShiftLab /goal — executable audit checklist

**Use with:** `SHIFT_LAB_FULL_RESEARCH_AUDIT_GOAL.md`. This file is a *work queue*, not a claim that tasks have been performed. Every checkbox starts unchecked. Do not mark complete from narrative review alone.

## State and validation rules

- States: `TODO`, `IN_PROGRESS`, `DONE_VERIFIED`, `BLOCKED`, `INCONCLUSIVE`, `REOPENED`. A checkbox becomes checked only when `DONE_VERIFIED`.
- Each task's execution record must contain exact source paths/versions, operations performed, output paths, command/test, exit code, hash, reviewer, and conclusion.
- Historical registered outcome and corrected current interpretation must be stored separately; never backdate a gate.
- Any `BLOCKED` or `INCONCLUSIVE` required task prevents the overall `/goal` from claiming `SUCCESS`. Record blocker category and attempted resolution; keep progressing elsewhere.
- Verify all 18 phase gates and independent reviews. Record every new experiment's frozen registration and seed/data exposure before running.

## Primary task queue

### W00 — Snapshot, isolation, resources, permissions [G00]

- [ ] **W00.01** Record current `git status`, `git rev-parse HEAD`, remote URLs, remote branch tips, active worktrees, staged/unstaged/untracked files, ignored outputs, local environment, runner/test commands and available CPU/GPU.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W00.02** Read `AGENTS.md`, research charter, current goals, data permissions, and any branch-specific instructions. Identify conflicts between old and new directives; the newer explicit user goal governs the task, while old experiments remain immutable.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W00.03** Create separate audit branch/worktree without overwriting user changes. Install nothing unusual and download no large datasets without permission.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W00.04** Discover exact main/branch/local source paths and create the source catalog.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G00 (phase sign-off)** A clean, isolated audit worktree exists; current source commit recorded; all known source groups listed with resolution statuses; no existing user file or frozen result altered.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W01 — Exhaustive programme and verdict census [G01]

- [ ] **W01.01** Traverse every `docs/`, `papers/`, `configs/`, `scripts/`, `src/`, `tests/`, and `outputs/` subtree; capture historical `PASS`, `KILL`, `NO-GO`, `STOP`, `MIXED`, `INCONCLUSIVE`, `conditional go`, `novel`, `invalid`, `uncertified`, and `not worth` decisions (case-insensitive, plus synonyms).  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W01.02** Group duplicate phrasing into distinct scientific claims, but keep all source references and dated versions.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W01.03** Reconstruct decision chronology: original proposal, preregistration, execution, critique, amendment, supersession, newer empirical result; include branch-only and PR-only records.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W01.04** Detect contradictory current statements, e.g., `FINAL_RESEARCH_REPORT.md` historical negative heading versus `14_FAIR_REEVALUATION.md` and new B3 outcomes; label a correction as `SUPERSEDED`, not falsified if the historical gate was correctly applied.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W01.05** Ensure findings from Paper 1, Paper 2, Paper 3, integrated ShiftGuard, E2/E3/E4, RPOQ, Failure Atlas, HG/H2c, HG×H2c, A1–A3c, P3b/B3, and CRSP/EIA are represented.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G01 (phase sign-off)** A complete master claim ledger plus source-count and branch-by-branch coverage summary; an automated search confirms no unresolved matching historical decision documents; reviewers inspect omissions. No broad `NO-GO` without explicit scope.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W02 — Gate, effect-size, and early-termination audit [G02]

- [ ] **W02.01** Enumerate every artificial/administrative numeric rule: 10% average net-cost, 50% gap closure, 1.5× evidence growth, +10 detection points, three-point slope/trend rule, zero-loss across all regimes, all-frontier dominance, tight alpha grid, and any hidden stop condition.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W02.02** Classify each gate as statistical validity requirement, preregistered confirmatory criterion, research-priority screen, resource ceiling, practical utility threshold, or publication aspiration. Only the first two can govern the original confirmatory outcome, and none should be silently discarded.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W02.03** Check power of short screens and near misses; compute continuous effect and interval even if gate fails; separate `passed registration` from `meaningful effect`, `novel` and `worth following up`.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W02.04** Explicitly re-audit A1b's positive gap at T=11 (4.641% under alpha=0.20) that missed 5% continuation; the 48% versus 50% Failure Atlas closure case; WP2 1.5× threshold; WP3 small 20-seed screen; and P3/P3b B1/B2 10% classification.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W02.05** For any post hoc reclassification, state it is a *new interpretation*, not a retroactive protocol pass. If proposing an alternative threshold for future runs, justify by loss/utility/precision or preregistered science and freeze new seeds.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G02 (phase sign-off)** Exhaustive gate register; all near misses evaluated continuously; no unchanged historical test is called newly confirmatory; documented decision on whether each early-stopped branch requires another study.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W03 — Comparator, information-set, and fairness audit [G03]

- [ ] **W03.01** For every prominent result, construct a matrix of candidate and competitor: target null, statistical class, free information, labeled information, release timing, budget, cost, model pair, fallback action, intervention latency, tuning effort, reference selection, calibration, stopping opportunities, and guarantee.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W03.02** Reproduce missing strong comparators where viable, with author-code checks: CAMS-style disagreement queries, Xu-style active anytime-valid procedures, fixed-batch paired tests with *valid* predeclared sampling/stopping assumptions, SR/CUSUM/Page–Hinkley calibrated alarms, economic retraining policies, constrained switching/value-of-information control, separate HG/H2c, joint contextual ONS/Kelly, multivariate gambling, and appropriate delayed-feedback R6 methods.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W03.03** Do not compare different-null methods as equal validity baselines; if testing a joint intersection null, show how it differs from individual cost and Brier nulls. Do not grant an oracle knowledge as deployable baseline; display oracle headroom separately.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W03.04** Check WP3's 55% versus 100% detection at 5%-budget/late-onset setting: retain a valid negative result for this specific controller even if advancement gate is relaxed; report resource savings and Pareto frontier separately.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W03.05** Check B2 `BEST` excluded a fair strong paired test and that in-sample baseline tuning is not mistaken for out-of-sample dominance. Check B3 P6's assumptions; do not say P3b wins all comparators when P6 wins on five streams.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W03.06** Check selection of best comparator on evaluation seeds for winner's curse and adjust with train/dev/frozen independent selection or nested resampling.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G03 (phase sign-off)** Comparator parity cards for every headline result; every benchmark marked `FAITHFUL`, `TASK_ADAPTED`, `FORMULA_VERIFIED`, `INSPIRED`, `DIFFERENT_NULL`, `INVALID`, or `MISSING`; stronger baseline implemented/tested or logged as an explicit unresolved limitation; valid match-by-match confidence intervals available.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W04 — Statistical validity, estimands, and certification [G04]

- [ ] **W04.01** Recheck all theorems and implementations for history-predictable stakes, query decisions, issued propensities, release-time conditioning, unresolved-prefix versus out-of-order outcomes, selection on available labels, endogenous policy transitions, resetting after intervention, anytime validity and repeated comparisons.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W04.02** Distinguish eventwise conditional mean null from marginal/stationary null; demonstrate the 20.8% false promotion under the persistent marginal-null stress does *not* contradict conditional-null results and forbids any broad unconditional safety claim.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W04.03** Test nominal risk on genuine **boundary** null streams, not only strict/safe nulls. Separate analytical e-process guarantee from Monte Carlo calibration and from research-level `SAFE` cost definitions.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W04.04** Revisit Q2 integrated net-benefit claim: actual increment `E[I_t(g_t-s)|F_{t-1}]<=0` does not certify the whole switching-cost utility. Decide whether to revise the estimand or implement and prove the correctly costed increment. If unproved, withdraw full-net-benefit certification.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W04.05** Audit Q1→Q2→Q3 composition: verify conditional validity under adaptive handoffs, alpha spending, multiple candidate rounds, model versions, delayed feedback and rollback. No blanket union-bound claim without conditions. Audit HG×H2c J combiners: fixed mixtures/Bonferroni valid under stated assumptions; unguarded products of e-processes **not** generally valid. Never bypass an invalidity finding by rebranding it as conservatism.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W04.06** Build explicit validity table by scenario: iid, Markov/autocorrelated, outcome-dependent delays, selective labels, adaptive querying, repeated switches, multiple candidates, unknown nominal risk, information leakage, policy-responsive stream, and real data.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W04.07** Check proof/simulation correspondence with regression tests including adversarial counterexamples. If a proof is incomplete, mark `ARGUED`/`UNPROVED` and forbid `CERTIFIED` in dependent text.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G04 (phase sign-off)** Exact null and filtration written for every certification claim; boundary-null tests and counterexamples executed or blocked with evidence; every unresolved invalid guarantee withdrawn/downgraded or actually repaired; proof/claim correspondence independently checked.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W05 — Seed reuse, leakage, chronology, provenance [G05]

- [ ] **W05.01** Read the Stage 0 seed registry finding: **103 overlapping pairs, 101 previously undisclosed, including 51 cross-study reuses**; independently regenerate overlap detection over *all* main/branch/local output manifests and test sets.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W05.02** Classify overlap severity: identical seeds + identical generator/config, prefix sharing, shared data tape, reused development after viewing, leakage into confirmation, harmless reproducibility reuse, or not ascertainable. A reused integer seed is not alone proof of data reuse; track stream generation hierarchy.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W05.03** Check all frozen protocol dates against actual first read of labels/holdouts; distinguish previously exposed Gas/elec2/criteo from truly locked windows; check the `B3` declared locked windows and pair selection.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W05.04** Validate `event_time`, `request_time`, `release_time`, `prediction_time`, `action_time`; train-only transforms and ordering; source-clock plausibility for spam, bank, airlines, rialto and weather. Do not claim prospective timing when a release contract is imposed.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W05.05** Rehash key output/manifests, verify snapshot code parity and identify uncommitted-run cases. If raw unavailable, classify metadata-only check and identify required copy.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W05.06** Restrict any seed-tainted results to development/descriptive use; create fresh allocations only after preregistration for new confirmation.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G05 (phase sign-off)** Seed-collision graph and leakage/exposure matrix, per-claim impact verdict, independent reproducibility checks, no exposed evidence relabelled as independent confirmation.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W06 — Historical code/claim errata and defect repair [G06]

- [ ] **W06.01** Reassess all 10 Stage 0 errata and check whether downstream reports still repeat the wrong claims (e.g., inaccurate seed range, stale rollback status, miscited prior work, error in E3 counts, propensity interpretation).  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W06.02** Revisit documented P4 pilot reward/cost-matrix direction error, HG finite-support cap, HG×H2c frontier cross-track and DIFFERENT_NULL leakage, Atlas R_law reference defect, R_valid2 reference-classification artifact, and A1d vacuous/upper-bound mistake.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W06.03** For each confirmed code defect: add a failing minimal regression test against a pinned old commit or fixture, implement minimal fix on audit branch, run direct and whole relevant test suites, compare before/after, regenerate only **development** outputs by default, and append an erratum with invalidated downstream artifacts.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W06.04** Maintain `bug_id`, `severity`, `affected_versions`, `source_line`, `old_behavior`, `correct_behavior`, `test`, `fix_commit`, `output_re-run_status`, `claims_changed`.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W06.05** Do not silently change model estimand, budget, cost units, alpha, data construction, or experiment clocks while calling it a bug fix. This requires a new protocol/version.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G06 (phase sign-off)** Every high-severity defect has a regression test, code fix or explicit ruled-out finding, and claim impact; no missing errata propagation into current publication drafts.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W07 — P3b certified switching / B1-B3 audit and upgrade [G07]

- [ ] **W07.01** Independently recompute B1/B2 world means, confidence intervals, exact boundary-null FAR, W1–W4 breakdown, P3 cap `p_min/2` versus P3b propensity-matched cap, and all published caveats. Track selected four-world weights and weaker-signal generator.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W07.02** Recompute B3 from `results/b3/summary.json` and per-episode JSONL if accessible, including all seven streams, P0/P1/P2/P3b/P6, WIN, SAFE, episode counts, promotion/rollback, label spend, 95% uncertainty, sensitivity B=400 and switching cost 20; confirm P6 wins five of seven.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W07.03** Challenge pseudo-replication: one spam episode, three weather episodes; query-randomisation seeds do not constitute independent source episodes. Report within-episode uncertainty separately from across-episode generalisation; do not use seed-level bootstrap to imply population-level precision.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W07.04** Check the `SAFE` criterion exactly: `P3b <= P0 + P3b query spend + 0.02*P0`; distinguish this from non-inferiority under independently justified costs or validity under the conditional null.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W07.05** Implement faithful, applicable published and strong simple alternatives (CAMS/Xu/task-adapted, risk-valid sequential batch alternative, paired SR/CUSUM, disagreement-aware P2, budget-matched economic switch/retrain) with identical observation opportunities and versioning.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W07.06** Identify realistic challenger headroom *before* opening new test sets. Freeze two structurally different synthetic generators, one independent real-data or quasi-real stream with sufficient independent episodes, and sensitivity across signal size, disagreement rate, delay, fees and budget. If no new adequate stream exists, report limited transfer; do not invent one.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W07.07** Run fresh confirmation only after a protocol, comparator software, seed registry, and power/design analysis are locked. Report cost, economic regret, false promotion, timing, net utility and Pareto trade-offs, not a forced 10% cutoff.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G07 (phase sign-off)** B3 aggregate and episode accounting reconciles; factual current narrative includes three WIN/seven SAFE plus five P6 losses, imposed costs/delays, episode limitations; any newly claimed superiority is independently confirmed against valid strong baselines.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W08 — A1/A1b/A1c/A1d/A2/A3/A3b/A3c theory reassessment [G08]

- [ ] **W08.01** Recover exact game, full/joint policy information set, slot-set-restricted calendars with adaptive skipping, strict forced open-loop schedules, public coin randomisation and calendar mixtures. Distinguish all three. No mislabeled comparator.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.02** Recompute representative exact rational/LP cells; confirm J ≤ C_mix ≤ C*; audit feasibility, numerical solver status, timeout/node cap and equality tolerance; no extrapolation from unsolved T=12.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.03** Retain historical A1 `KILL` for its grid but withdraw global `no adaptive value` reading. Revisit A1b T=11 4.641% with alpha=0.2, risk-specific alpha dependence, A1d lower-convex-envelope correction, exact lower/upper bounds in A3c.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.04** Verify per-instance certificate (Proposition 6), chain reduction (Theorem 7), and assumptions in `13_A2_BRANCH_CONFLICT_THEORY.md`; in particular explain why the Lemma 2 bound is zero/vacuous, and distinguish original upper-only from later proven two-sided gap.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.05** Check known 108 B=3 tight cells, 54 B=4 alpha=.05 cells, 54 B=4 alpha=.10 noncertified cells, and six A3c positive mixture-gap intervals [.71%,1.21%]. Do not generalize to all HMMs or larger budgets.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.06** Recheck claimed F5 intermediate-alpha lower bounds (5.07%, 4.68%) against actual source `results/a1d/LOWER_BOUNDS.md`, source audit and arithmetic. Calculate independently where feasible.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.07** Audit literature on constrained POMDPs, adaptive sensor scheduling, chance-constrained acquisition, stopping, sequential trials, risk-ledger dependent observation, model-level thresholds; identify what is already known and which theorem would be genuinely new.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W08.08** Explore `Conjecture 8` only via a properly stated model-level sufficient condition and proof/counterexample; if not solvable, remain `OPEN` with precise obstacles, not `PROVED`.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G08 (phase sign-off)** Corrected theorem ledger, exact instance certificates reproduced or independently inspected, valid comparator hierarchy, no vacuous bound cited as proof, novelty status determined as far as accessible primary sources permit.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W09 — Failure Atlas cycles 1–5: recover avoidable improvement and real cost of validity [G09]

- [ ] **W09.01** Re-run only minimal checks needed to replicate the documented R_law reference defect and cycle-2/3/4 classification transitions. Preserve the original `shared_failure` counts and the fact **116 of 123** moved to `cost_of_validity` under R_valid, without interpreting that as mathematical necessity.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.02** Audit R_family's empirical-only calibration and oracle family knowledge. Audit R_valid/R_valid2 boundary-null rates, unused alpha, R_best within-sample best-of-two winner's curse, cost of comparator selection, null-twin distribution and reference-tape equivalence.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.03** Independently reproduce cycle-3 fresh-seed straddle repair (cost candidate 0.2781, ablation 0.3933, best_safe 0.3733, R_family 0.1838, R_valid 0.3541; closure 0.503; one cell) and relevant neighbours, but keep it as *development mechanism finding*. Show gain sign versus delays 1, 10, 50; distinguish labels saved from acquisition latency.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.04** Preserve negative straddle mean across full grid and triggered-Kelly late-onset harm; a conditional effect cannot be promoted to a universal win.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.05** Execute/locate registered Amendment 6 cycle-5 exact finite-horizon cost-of-validity study if feasible: HMM analogues T in {6,7,8}, B in {2,3,4}, delay {1,2}, risk alpha=.1, onsets and magnitudes per frozen protocol. Calculate V_free (unconstrained), V_valid (risk-constrained), CoV=V_valid−V_free, RC=cost(R_valid)−V_valid, gap=cost(best_safe)−V_valid; verify solver duals/primal residuals, simulation match and monotonicity. Record unsolved cells and why.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.06** Do not extrapolate T≤8 exact results to T=1000. If RC>CoV in a majority of solved registered cells, report the registered finding, but also sensitivity to distributions, prior, and validity-matched reference. If not, maintain conditional/narrow verdict.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.07** Audit Amendment 6 dependent-outcome family 3 and informative-release family 4, including null classes; label marginal-null violations as misspecification, not contradiction. Use original frozen protocol if running it; no post-result tuning on confirm pool.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.08** Reclassify the 48%-closure and all 1%/3%/near-threshold improvements as `PARTIAL_IMPROVEMENT` when warranted; do not call them `REPAIR` under the old ≥50% rule or infer efficacy from a selected best cell.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W09.09** Benchmark strongest applicable R6 wrappers and hard-budget pacing where implemented; mark adaptation vs source fidelity, and distinguish uncertified ungated utility from certified comparisons.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G09 (phase sign-off)** Real cost-of-validity attribution explicitly separated from conservative-reference artifacts; cycle-5 status resolved or blocked with exact resource reasons; straddle and triggered-Kelly conclusions scoped by delay/onset, all past registered outcomes intact.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W10 — HG and H2c independent audit [G10]

- [ ] **W10.01** Trace HG, H2c, parent PPRM, discounted Kelly, cost/Brier ONS, true-cost thresholds, Brier guidance and the published PPI betting family through main and research branches.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W10.02** Recompute H2c G5 from per-seed data (reported +0.086 [0.059,0.113] power @10% labels; +0.094 [0.063,0.125] @20%) and compare per-cell local winners with a frozen selection rule. Preserve significant within-class improvements without claiming novel engine.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W10.03** Verify H2c cost-null proof and implementation test, clipping, unknown-nominal calibration, signal alignment/misalignment, AR dependence, delayed outcomes, Gas negative transfer, and lag before alarm. State the equivalent substituted-moment discounted-Kelly representation.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W10.04** Recompute HG parent gains (reported +0.029 / +0.052) and harm-world reduction, confirm finite-support cap, correct erroneous raw ~21/24 interpretation, and retain lack of strong superiority over Page–Hinkley/CUSUM and dependence FAR up to .23.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W10.05** Repeat only necessary synthetic confirmation using new independently registered seeds if claims exceed old development results. Test cost-null and Brier-null *separately*.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G10 (phase sign-off)** HG/H2c factual results independently reconciled or marked analysis-only; power, utility, validity, novelty, dependence and calibration-size limitations explicitly distinct.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W11 — HG × H2c bidirectional grammar and completion audit [G11]

- [ ] **W11.01** Locate stage 1–4 outputs in main, all branches, ignored local worktrees and remote artifacts; do not infer failure from missing `outputs/hgxh2c/stage4/confirmation.json` on main.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W11.02** Verify stage-1 baseline source fidelity and missing author-code reproductions in `02_NATIVE_REPRODUCTION.md`; check `03_BASELINE_REGISTRY.md` fidelity classification and different-null exclusions.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W11.03** Verify A3 invalid product combiner excluded; A4 wrong-track and DIFFERENT_NULL frontier contamination fixed and the old frontier archived; A5 primary validity-compatible versus secondary empirical alarm comparator separation. Re-run unit tests on frontier composition.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W11.04** Audit grammar equivalences, cross-track stake/query/restart hook predictability and joint-filtration assumptions; exact equivalence to contextual ONS/multivariate/PP constructions where appropriate. The raw grammar is huge: evaluate actual canonicalisation, resource budgets, successive halving bias and whether good Q/R candidates were prematurely filtered.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W11.05** If final confirmation does not exist and resources/permissions allow, execute the registered staged protocol from a corrected clean frontier with frozen finalists, complete independent null risk calibration and disjoint seeds; if frozen conditions were compromised, establish a new registered protocol and fresh seeds, not reuse the former confirm block.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W11.06** Produce per-regime J-cost, power, delay, labels, negative-transfer, sensitivity, ablations, cross-risk alignment shuffled controls, parity with independent HG+H2c and contextual ONS, strong guaranteed baselines, and secondary CUSUM/PH comparators.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W11.07** Classify separately: meaningful composition, narrow method novelty, monitoring-only advantage, economic decision advantage, null-class guarantee, publication readiness. Lack of broad dominance is not evidence of no conditional benefit.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G11 (phase sign-off)** A complete branch-inclusive stage-status record and exact missing/deployed artifacts; all frontier errors repaired; stage-4 confirmational claim only when actually run and integrity verified.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W12 — Original Paper 1, E2/E3/E4, integrated action loop [G12]

- [ ] **W12.01** Revalidate Paper 1 WP1: S3 gated-versus-uniform effect and interpretation credited to published DISCERN-style gating; do not invent novelty. Revisit WP2 analytic equality with subgroup composition and WP3 20-seed negative screen, while retaining any resource-efficiency trade-off.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W12.02** Reconcile E2: 20,000-stream burst experiments; fixed better in harmful post-onset bursts, pacing better when harmless early bursts deplete budget; monitor without knowing burst harmfulness. Factor out correct budgets, latency, fixed/pace caps, monitoring null and published comparable burst-aware allocation.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W12.03** Reconcile E3: confirm estimated revert/promote crossover between doses .45 and .60, but verify full economic estimand and distinguish abstention, revert, promote, and certification delay. Build a fair matched-opportunity factorial, not confounded arms.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W12.04** Reconcile E4: no eligible q<1 detectable cells in locked EIA analysis means no sparse-query transfer claim; distinguish structural non-identifiability from a failed method.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W12.05** Audit integrated Q1→Q2→Q3 and rollback: different policy latencies, versioning, rollout and exposure; correct old “full net benefit certified” interpretations, evidence selection/reuse and expected-versus-realized utility errors.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W12.06** If recommending new methods for burst-aware acquisition and state-dependent intervention, write two separate hypotheses, limitations of closest published methods, fixed primary endpoints and new independent test/validation designs. Do not call study design itself a new result.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G12 (phase sign-off)** E2/E3/E4 and Paper 1 findings retained or narrowed correctly; no broad premature programme exit inferred from their scoped negatives; exact matched economic action/estimand documented.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W13 — Real-world eligibility and transfer [G13]

- [ ] **W13.01** Census EIA, CRSP, Gas, Spam, Rialto, Weather, Airlines, Bank, Elec2, Criteo, Folktables, WILDS, Open Bandit, Upworthy and other accessed streams. Record provenance, licences, target, action/outcome observability, independent episodes, timestamp validity, source availability, train/dev/test splits, exposed status and imposed parameters.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W13.02** Determine which streams permit paired fixed-policy losses, which require off-policy estimators, which are retrospective only, and which lack point-in-time release clocks. Never use market returns as verifiable executability or causal shift timing without evidence.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W13.03** Treat B3 five initially unexposed streams and two partly exposed streams according to recorded provenance; because B3 has now been executed, those B3 locked windows are exposed for any *subsequent* hypothesis motivated by outcomes.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W13.04** For research that needs larger independent episodes, find suitable permitted data or label limitation as `NO_ELIGIBLE_SOURCE`; do not silently duplicate one stream into pseudo-independent samples.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W13.05** Run leakage and counterfactual identifiability audit of each proposed new real-data test, including temporal dependence and event clocks; freeze task and metric before opening labels.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G13 (phase sign-off)** Complete real-data eligibility matrix; honest conditions on transfer; new validation sources meet independence/clock/licence constraints or are explicitly unavailable.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W14 — Formal review of literature, theory, and novelty [G14]

- [ ] **W14.01** Collect primary texts, versions, author implementations, theorems and actual algorithm definitions for comparisons already referenced: DISCERN/CAMS, Xu active RCPS, Csillag prediction-powered e-values, Ryu–Wornell vector gambling, PPRM, Timans, DE-CuSum, delayed testing methods, constrained sensing/POMDP, fixed/sample certification, policy switching, adaptive e-processes and family-wise online control.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W14.02** Record citation details, exact assumption, theorem number, comparator behavior, and what the published method already achieves. Remove conclusions from abstract-only searches or vague “prior work covers it” statements.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W14.03** Specifically audit novelty of Prop. 6, Thm. 7, F5 risk-specific branch conflict, A3c gap, straddle delay decision boundary, P3b conditional certification, E2 burst allocation, E3 crossover and HG×H2c cross-channel techniques.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W14.04** Use a sceptical independent theorem reviewer and a separate experimental/statistical reviewer. Each must try to falsify, not merely approve. If external reviewers unavailable, mark review `INTERNAL_ONLY` without fabricating independence.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G14 (phase sign-off)** Source-level novelty matrix for each positive method/theorem candidate, with unresolved source access disclosed; theorem corrections and reductions propagated into claims.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W15 — Re-grade ALL findings without lowering scientific validity [G15]

- [ ] **W15.01** For every row in the master claim ledger give **four separate fields**: effect magnitude/uncertainty, guarantee status, novelty status, and practical value. Add generalisability and data-exposure separately.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W15.02** Preserve null, small, negative and contrary-world effects. Use exact descriptive continuous effects rather than turning an arbitrary 10% cutoff into “no effect”. Report absolute and relative improvement with denominator, paired uncertainty, effect heterogeneity, label counts, delay and net economic benefit.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W15.03** Apply verdicts: `UPHOLD`, `NARROW`, `SUPERSEDE`, `WITHDRAW`, `REOPEN FOR EXPLORATION`, `REPAIR VALIDITY`, or `OPEN BLOCKER`. A near miss is not an automatically positive result.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W15.04** Reassess at minimum F1–F10 in `14_FAIR_REEVALUATION.md`, all A/B/C/D/E/F/G lanes, the original Paper 1 decision and programme-level `NO-GO`, the Atlas classification and HG/H2c/HG×H2c status; update conclusions after any new evidence, retaining old registered verdicts.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W15.05** Produce a contradiction checker linking each current summary line to the latest applicable evidence and its historical predecessor; identify stale statements in README, manuscript drafts, decision logs, summaries, prompts and public-facing tables.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G15 (phase sign-off)** Every major finding has exactly one latest audit interpretation with visible history, direct source anchors and independent grade axes; no known contradictory unsuperseded headline remains.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W16 — Manuscript decomposition and honest publication assessment [G16]

- [ ] **W16.01** Prepare separate claim-constrained candidate paper outlines: (A) budgeted certified model switching / P3b and real-data comparisons; (B) risk-constrained acquisition calendar-optimality, branch conflict, exact adaptivity gaps; (C) monitoring/burst/decision failure benchmark with E2/E3 mechanistic experiments; (D) HG/H2c cross-risk information-transfer only if reproducible results justify it.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W16.02** For each outline define central claim, strongest contrary baseline, empirical evidence, theorem, dependence/null contract, real-data eligibility, nearest literature, remaining decisive experiment, disqualifying outcome, alternative venue/format, and non-claims. Do not rate acceptance probability as fact.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W16.03** Score evidence readiness separately from originality; conference-target aspiration never dictates truth of scientific results.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W16.04** Prefer separate focused manuscripts to a stitched-together claim unless a unifying theorem or meaningful shared method is actually demonstrated.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G16 (phase sign-off)** A portfolio of appropriately scoped manuscripts (including viable benchmark/negative manuscripts), with explicit go/narrow/pivot decisions and evidence-gated remaining experiments; no unsupported ICML readiness claim.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

### W17 — End-to-end verification, independent criticism, final sign-off [G17]

- [ ] **W17.01** Run project and new audit tests (targeted then full feasible suite), static checks, seed collision detection, CSV schema checks, provenance hash checks, consistency checks, synthetic leak tests, and confirmation separation checks. Capture commands, exit codes and output hashes.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W17.02** Independently recompute samples of all headline figures from underlying per-event/per-seed/episode artifacts. Use exactly the estimator and clustering justified by the unit of independent replication; inspect published figures/tables against numeric source outputs.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W17.03** Assign at least two adversarial reviews: statistical validity/theorem review and experimental design/comparator/data review. Have each produce `FATAL`, `MAJOR`, `MINOR` issues with evidence; correct fatal errors and rerun tests before closing.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W17.04** Verify that all W00–W17 outputs exist with meaningful content, G00–G17 tests pass, source catalog covers all relevant artifacts, every active item in TASKS.md is `DONE` or a genuinely external blocker is recorded, and every changed interpretation points back to preserved history.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **W17.05** Produce final summary with: what changed, what held, what was withdrawn, what was newly confirmed, what remains descriptive, real-world relevance, negative outcomes, exact reproduction commands, commits, outstanding blockers, and recommended next scientific actions.  
  *Evidence:* source anchors + file/commit + check output + reviewer; record in `TASKS.md` and `EXECUTION_LOG.jsonl`.
- [ ] **G17 (phase sign-off)** A reviewer can reproduce every asserted correction from source/command, no unaddressed validity-critical issue or mislabeled confirmation remains, all independently feasible remediation steps completed, and success is asserted only when no required blocker remains.  
  *Evidence:* phase-gate review + verified artifacts + test exit codes + source references.

## Final conjunctive completion review

- [ ] Each of the 18 workstreams has a verified phase acceptance artifact; phase owners and independent reviewers recorded.
- [ ] Every claim from the complete source/branch census has a current evidence-supported interpretation, or a precise unresolved blocker.
- [ ] Historical experiment files are preserved; every correction appears in a separately dated erratum/supersession.
- [ ] No unproved validity or unverified novelty claim appears in current README, paper drafts, executive summary or graphical abstracts.
- [ ] All corrected programmatic defects have reproducible before/after tests, with fresh data where genuinely necessary.
- [ ] The seed/holdout exposure graph and comparator information-matching checks are complete.
- [ ] Paired effects, appropriate uncertainty, denominators, dependence and negative cases accompany every headline result.
- [ ] The strongest source-compatible baselines are reproduced or specifically documented as blocked; missing baseline does not count as method dominance.
- [ ] Independent statistics/theory and experimental/comparator reviewers have signed off, with fatal/major issues closed.
- [ ] All files in the output contract exist and are linked in ARTIFACT_MANIFEST.json with SHA-256; all runnable tests pass; no unresolved high-severity integrity issue.
- [ ] Final report lists exact `DONE_VERIFIED` / `BLOCKED` totals, changes, commands, open risks, and next action. Only mark `SUCCESS` if no required blocker remains.

**Generated from the master goal:** 103 actionable tasks + 18 phase-gate checks + 11 final sign-off checks. Numbered tasks above are deliberately detailed in the master goal; retain all their criteria and do not silently simplify them.
