# Scoped methods research assessment (2026-11-06)

## Decision

**`BENCHMARK_OR_CASE_STUDY_ONLY`** for this execution. The repository supports useful, scoped failure and cost diagnostics, but does not establish a new method contribution or independent real-world transfer. This is an evidence decision, not a claim that a future method is impossible.

## Four contribution gates

| Contribution | Status | Exact evidence | Limitation / next smallest action |
|---|---|---|---|
| C1 Diagnosis | **PARTIAL** | `docs/sprint2/wp1/RESULTS.md`: 10 late-improvement episodes / 5 source clusters and 16 reversals / 7 clusters among 348 retrospective episodes / 14 sources. Corrected 100-seed Sprint 2 replay confirms ordinary Gated is much costlier than Gated+front on several synthetic improving regimes. Across 14 previously exposed real source clusters, front−Gated is −24.55 J [−42.81,−6.29]. | The real cohorts were repeatedly exposed to development and the simple front-vs-tuned contrast is unresolved: −0.30 [−1.05,+0.45]. Classifier strata are retrospective, not causal change labels. The registered WP1 late contrast remains NOT_SUPPORTED (0/4 host intervals exclude zero). |
| C2 Explanation | **PARTIAL** | Corrected replay shows front-loaded acquisition reduces cost on several improving synthetic regimes. Existing C2/C6 are cheaper than Gated+front on two late synthetic cells by 7.4–7.8 J (100 seeds/cell), but promotion remains rare. Corrected real source-level contrasts do not show a clear C2/C6 advantage over front or tuned pacing. The 20-block E_rb replay is ΔJ −6.86 [−8.69,−5.03] versus RMM; horizon gate remains non-binding and alpha/start-grid are material. | No new mechanism is isolated. The never-switch control was cheaper than every switching policy in the reversal replay; a matched restart-grid/two-sided SR/CUSUM falsification remains incomplete. |
| C3 Targeted repair | **FAIL** | No new repair was frozen, implemented and demonstrated against the strongest matched baselines. RMM is not superior to matched SRR on the real late stratum; E_rb has a post-development synthetic signal. | E_rb's observed gain is consistent with conventional alpha/start-grid tuning. A candidate must first survive this matched ablation and the corrected Gated/DISCERN comparisons; do not make a novelty claim now. |
| C4 Independent real confirmation | **FAIL** | Corrected real replays cover 9- and 5-source exposed cohorts; they do not establish independent transfer. Wild-Time feasibility found no verified label-release logs. OPSD/Binance task code offers a better clocked future lead, but no untouched method evaluation was run. | No frozen repair or untouched independent cohort. OPSD costs are imposed and its locked holdout was not accessed. |

## Baseline fidelity and interpretation

The baseline registry and source review are in [BASELINE_FIDELITY.md](BASELINE_FIDELITY.md). Xu is an acquisition-only adapter paired with a ShiftLab certificate, not Xu et al.'s published certificate. Gated and DISCERN variants are common-contract ports; they must not be described as author-native reproductions. The corrected DISCERN scaling and adaptive-range predictability defect are recorded in `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md`. The defect affects 130 runs / 411 policy entries; corrected Atlas validation and Sprint 2 replay/null suites are available, with correction-replay interpretation in `CORRECTED_REPLAY_AUDIT.md`.

Keep null targets distinct: an iid conditional null, a marginal/exchangeable twin null, and expected economic cost are different estimands. E_srr's ARL behavior is not a per-horizon false-alarm probability. Empirical null rates do not establish a theorem.

## Candidate method specification (not advanced)

The only bounded next candidate worth a falsification screen is a post-promotion rollback reserve: set a label reserve before deployment; use only released labels and pre-decision state to update a mirrored rollback process; issue rollback only under a stated conditional null test and a prespecified cost-to-go rule; account for repeated cycles by alpha spending. Its statistical claim would be conditional on predictable queries, valid release-time filtration, and the stated conditional mean null. The cost-to-go rule is empirical unless independently justified. It must be compared with E_rb as-is, matched higher alpha, two-sided SR/CUSUM, and no rollback at identical horizon, pathwise budget, delay, query cost and switch cost. This specification is a falsifiable follow-up, not an implemented result or a novelty claim.

## Real-data construction audit

`docs/scoped_method_research_2026-11-06/REAL_DATA_AUDIT.md` records why current streams do not satisfy fresh confirmation. In particular, the Failure Atlas FLQ suite creates balanced evaluator labels and derives paired predictions by XOR with losses; this is a replay adapter, not authentic model-pair prediction chronology. Imposed delays are not dataset label-release records. Episode resampling does not replace source-level uncertainty.

## Independent review

The read-only internal critical review is preserved in `docs/scoped_method_research_2026-11-06/INDEPENDENT_REVIEW.md`. It agrees with the decision above. It is an internal LLM subagent review, not external scientific review or theorem verification.

## Manuscript-ready four-contribution outline

1. **Diagnosis:** characterize when fixed-budget online deployment misses late challenger improvements and when post-promotion monitoring fails to reverse after a reversal; make the operating region and retrospective status explicit.
2. **Explanation:** decompose label timing, restart/acquisition, alpha, start grid, delay and switching costs using matched ablations; separate predictive loss, label expenditure and switch expenditure.
3. **Repair:** currently unsubstantiated. Only include after a frozen rule beats strongest matched published methods in a specified target region and the benefit is not explained by conventional front-loading or restart calibration.
4. **Validation:** currently unsubstantiated for independent real transfer. Report fresh synthetic seeds and untouched chronological source clusters only after authentic chronology and source-level uncertainty are audited.

This outline describes the evidence needed for a paper, not a claim that all four contributions are complete. Use corrected Sprint 2 outputs in the benchmark report while preserving original artifacts as historical provenance. For this execution, present the findings as a benchmark/case study and retain the negative and inconclusive outcomes.


## Bounded direct-composition follow-up (2026-11-06)

The omitted direct front-loading-plus-E_rb composition was screened on 20 paired seeds in each of four reused simulator regimes. It failed the stated economic gate: its F0_better saving over the front-loaded host was −3.86 (95% paired t interval [−12.35, 4.64]); its V_late_600 difference from paced E_rb was −9.65 [−19.89, 0.59]; and under F3_reversal_800 it cost +60.65 versus never-switch [42.52, 78.78]. It spent all 200 labels in every cell; null promotion was 1/20 (Wilson interval [0.009, 0.236]). The independent audit recomputed the 400 raw rows and net-cost identity. This closes the specific missing-composition question as a development falsification, but does not exhaust the design space or upgrade C3/C4. The protocol was not committed/checksummed before execution and source hashes were truncated in the dirty-run manifest. See [`DIRECT_FRONTLOAD_ERB_CRITICAL_REVIEW.md`](DIRECT_FRONTLOAD_ERB_CRITICAL_REVIEW.md) and [`ECONOMIC_HEADROOM_DECISION_20261106.md`](../../research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md). The decision remains **`BENCHMARK_OR_CASE_STUDY_ONLY`**.
