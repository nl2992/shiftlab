# Claim-bounded benchmark / case-study manuscript outline

**Disposition:** `BENCHMARK_OR_CASE_STUDY_ONLY` (same as the active research lane's
`BENCHMARK_ONLY` checkpoints). No distinct repair survived the frozen economic and novelty
gates. This outline is a synthesis of existing evidence, not a new experiment or confirmation.

## Proposed title and claim

**Title:** *Economic Headroom in Delayed-Feedback Model Switching: When Sequential Certificates,
Restart Detectors, and Label Budgets Disagree*

**Defensible claim:** Under the registered synthetic costs, label budgets, and feedback regimes,
promotion speed, anytime false-promotion control, and deployment cost trade off sharply. Some
published or conventional restart methods improve a narrow late/strong-persistence cell against
certificate adapters, while they fail against other cost-aware comparators or on reversals. Existing
evidence does not support a new method, a universal ranking, or independent real-world transfer.

## Four-contribution status

| Contribution | Status | Evidence and limit |
|---|---|---|
| Diagnosis | **PASS, scoped** | Failure Atlas and the frozen economic matrix identify specific late-promotion and reversal-cost patterns under stated synthetic contracts. Wild-Time HuffPost adds one chronological late-improvement stress case, where tested PFA-SR is costly. It is one source cluster with simulated 24-hour label delay. |
| Explanation | **PARTIAL** | Matched hosts, ablations, and paired cost decomposition separate acquisition, detector, and switching effects in selected settings. They do not establish a single mechanism that generalizes across regimes; some older pilot timing/provenance is weaker and remains labeled exploratory. |
| Repair | **FAIL** | No candidate cleared the economic, null-safety, adverse-regime, and novelty gates. PFA-SR, E-SR pacing, front-loaded E_rb, contextual switching, and altered start-prior variants either invoke established methods or fail their frozen gates. |
| Validation | **PARTIAL** | Synthetic runs are reproducible and include fresh development streams. Real chronological evidence is exposed/stress-test evidence, not an untouched multi-source confirmation of a repair. No repair exists to validate. |

## Manuscript structure

1. **Problem and estimand.** Define net deployment cost as predictive loss plus label expenditure
   plus switching expenditure. Separate statistical promotion guarantees from economic value; state
   the complete feedback filtration and the exact null whenever a false-promotion rate is discussed.
2. **Benchmark design.** Document the fixed horizon, pathwise label budget, delays, cost contract,
   synthetic regime definitions, shared seeds, and evaluator-only oracle. Present the Failure Atlas
   as a map of conditional failure patterns, not as an inferred real-world causal taxonomy.
3. **Baseline fidelity.** Report corrected DISCERN scaling and adaptive-range ordering, distinguish
   Xu acquisition-only from Xu's published certificate, and list author-native versus inspired
   ports. Explain why SR/CUSUM ARL control is not interchangeable with probability of any false
   promotion.
4. **Economic headroom matrix.** Lead with the frozen 30-stream-per-cell matrix, including the
   persistent, favorable/unfavorable reversal, null, and delayed/scarce cells. Show cost
   decomposition, paired intervals, and null outcomes. The conventional E-SR result is a
   safety-incomparable diagnostic unless its specific error contract is met.
5. **Targeted falsifications.** Summarize the direct front-loading + E_rb screen, calibrated SR
   late-improvement screen, altered PFA prior, slower E-SR pacing, and context-stratified replay.
   Keep every negative and protocol deviation visible. No post-hoc favorable-cell selection.
6. **Chronological real-data stress cases.** Use Wild-Time HuffPost and the MN-DS Q4 replay only
   with their limitations prominent: simulated release delay, retrospective replay, single-source
   clustering, and (for MN-DS) opening before the synthetic/novelty gates passed. Do not call either
   an independent confirmation of a method.
7. **Discussion and stopping decision.** State that the evidence supports a benchmark/case-study
   paper about economic and guarantee trade-offs, not a new method contribution. Identify data
   chronology, source-level replication, and author-native baseline reproduction as limitations.

## Anchor artifacts and reproducibility

- Recovery, fidelity, and reconciled headroom: [`RECOVERY_STATUS.md`](RECOVERY_STATUS.md),
  [`ECONOMIC_HEADROOM_DECISION_20261106.md`](ECONOMIC_HEADROOM_DECISION_20261106.md), and
  [`docs/scoped_method_research_2026-11-06/FAILURE_ATLAS_UPDATE.md`](../../docs/scoped_method_research_2026-11-06/FAILURE_ATLAS_UPDATE.md).
- Frozen matrix protocol/results/raw records: [`pilots/economic_headroom_matrix_20261106/`](pilots/economic_headroom_matrix_20261106/).
- Restart calibration and late screen: [`pilots/srr_any_false_calibration_20261106/CALIBRATION_RESULTS.md`](pilots/srr_any_false_calibration_20261106/CALIBRATION_RESULTS.md) and [`pilots/srr_late_improvement_20261106/EVALUATION_RESULTS.md`](pilots/srr_late_improvement_20261106/EVALUATION_RESULTS.md).
- One-source chronological stress test: [`PFA_SRR_TRANSFER_DECISION_20261106.md`](PFA_SRR_TRANSFER_DECISION_20261106.md) and its linked run artifacts.
- P7s published-baseline loss replay and explicit no-go: [`pilots/p7s_vs_sota_loss_replay_20261106/RESULTS.md`](pilots/p7s_vs_sota_loss_replay_20261106/RESULTS.md); it finds one narrow exposed advantage over Gated on OpenML-LDPA but loses to Model Picker and Model Selector, so it does not meet the all-comparator rule.
- Context replay and explicit deviation: [`pilots/context_stratified_mnds_20261106/DECISION.md`](pilots/context_stratified_mnds_20261106/DECISION.md).
- ALFRED remains source feasibility only: [`ALFRED_SOURCE_FEASIBILITY_20261106.md`](ALFRED_SOURCE_FEASIBILITY_20261106.md); do not describe it as a performance result.

Before external submission, produce a table of baseline provenance and author-code fidelity from
the existing audit, recalculate manuscript tables directly from validated summaries, and obtain a
fresh independent review of all claims. Any next empirical claim requires a new protocol and fresh
untouched sources; the present evidence does not justify opening a confirmation holdout.

## Evidence amendment (2026-11-07)

The Failure Atlas update's F8 positive control is now accompanied by an Elexon BMRS profile screen.
The frozen 2024-train/2025-development pair did not reproduce the F8 profile: H1 disagreement was
17.021% with 52.856% challenger accuracy on disagreements (7,714 eligible events; 3 complete
2,000-event blocks); H2 disagreement was 8.745% with 48.725% conditional challenger accuracy
(8,073 eligible events; 4 blocks). This is a model-pair profile failure, not a policy-cost test;
no 2026 outcomes were opened. Source query hashes, label missingness, timestamps, and correction
history are recorded in `pilots/elexon_f8_profile_20261107/`.

This result strengthens the limit on the F8 transfer claim: EIA's 11 balancing authorities give
within-provider consistency for the fixed challenger control, but do not constitute independent
source replication, and the Elexon pair failed the prespecified applicability screen. The frozen
Wild-Time arXiv protocol remains unopened because the recovery brief's development and novelty
gates for a distinct candidate did not pass. Do not present either the EIA control or the synthetic
F8 advantage as a repaired algorithm or independent cross-source confirmation.

Updated contribution ledger: diagnosis **PASS, scoped** for the documented simulator regimes;
explanation **PARTIAL** because the controlled ablations identify component trade-offs but not a
cross-regime mechanism; repair **FAIL** because no distinct candidate passes the frozen economic,
safety, adverse-regime, and novelty gates; validation **PARTIAL** because the EIA replay is one
provider with simulated feedback/costs and the attempted Elexon transfer screen fails. Reproduction
and negative outcomes are summarized in `RECOVERY_STATUS.md` Phase 10–11, the Failure Atlas update,
and the linked run manifests. This amendment adds no new experiment or result.
