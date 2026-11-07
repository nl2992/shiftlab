# Scoped methods research assessment (2026-11-06)

## Decision

**`BENCHMARK_OR_CASE_STUDY_ONLY`** for this execution. The repository supports useful, scoped failure and cost diagnostics, but does not establish a new method contribution or independent real-world transfer. This is an evidence decision, not a claim that a future method is impossible.

## Four contribution gates

| Contribution | Status | Exact evidence | Limitation / next smallest action |
|---|---|---|---|
| C1 Diagnosis | **PARTIAL** | A new untouched chronological HuffPost test shows canonical PFA-SR misses a validation-strong challenger under scarce labels: 0 promotions after using all 200 labels; net cost 3,163 versus 2,039 for same-host RMM and 1,454 for Xu. PFA-SR is +289.91/1,000 vs RMM `[+193.64,+391.18]`, and +440.80 vs Xu `[+394.19,+486.84]`. This supplements the 10 late-improvement / 5-cluster and 16 reversal / 7-cluster retrospective evidence and corrected synthetic replay. | One dataset/source cluster, date-only event timestamps and simulated 24-hour label delivery; no observed annotation-release clock. This is a reproducible scoped chronological replay, not a multi-domain deployment claim. |
| C2 Explanation | **PARTIAL** | Corrected synthetic ablations and the news replay are consistent with slow evidence accumulation under a small label budget: PFA-SR spends all 200 labels and never promotes; RMM and Xu promote at events 1,498 and 254. Existing front-loading and restart ablations provide synthetic mechanism evidence. | Promotion timing alone does not isolate which detector/acquisition component caused the real failure. Matched synthetic ablations remain the mechanism evidence; real source has one cluster and simulated feedback. |
| C3 Targeted repair | **FAIL** | No new repair was frozen, implemented and demonstrated against the strongest matched baselines. RMM is not superior to matched SRR on the real late stratum; E_rb has a post-development synthetic signal. | E_rb's observed gain is consistent with conventional alpha/start-grid tuning. A candidate must first survive this matched ablation and the corrected Gated/DISCERN comparisons; do not make a novelty claim now. |
| C4 Independent real confirmation | **FAIL** | One untouched chronological HuffPost test source was evaluated with a frozen one-opening runner and time-block uncertainty. It gives clear negative evidence for PFA-SR under the simulated-feedback contract. UCI and MN-DS were screened before test access and remained locked because they failed validation eligibility. | No frozen repair was validated; only one independent source cluster; label release is simulated, not authentic. The run does not confirm a new method on independent real-world domains. |

## Baseline fidelity and interpretation

The baseline registry and source review are in [BASELINE_FIDELITY.md](BASELINE_FIDELITY.md). Xu is an acquisition-only adapter paired with a ShiftLab certificate, not Xu et al.'s published certificate. Gated and DISCERN variants are common-contract ports; they must not be described as author-native reproductions. The corrected DISCERN scaling and adaptive-range predictability defect are recorded in `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md`. The defect affects 130 runs / 411 policy entries; corrected Atlas validation and Sprint 2 replay/null suites are available, with correction-replay interpretation in `CORRECTED_REPLAY_AUDIT.md`.

Keep null targets distinct: an iid conditional null, a marginal/exchangeable twin null, and expected economic cost are different estimands. E_srr's ARL behavior is not a per-horizon false-alarm probability. Empirical null rates do not establish a theorem.

## Candidate method specification (not advanced)

The only bounded next candidate worth a falsification screen is a post-promotion rollback reserve: set a label reserve before deployment; use only released labels and pre-decision state to update a mirrored rollback process; issue rollback only under a stated conditional null test and a prespecified cost-to-go rule; account for repeated cycles by alpha spending. Its statistical claim would be conditional on predictable queries, valid release-time filtration, and the stated conditional mean null. The cost-to-go rule is empirical unless independently justified. It must be compared with E_rb as-is, matched higher alpha, two-sided SR/CUSUM, and no rollback at identical horizon, pathwise budget, delay, query cost and switch cost. This specification is a falsifiable follow-up, not an implemented result or a novelty claim.

## Real-data construction audit

`docs/scoped_method_research_2026-11-06/REAL_DATA_AUDIT.md` records both the new HuffPost replay and its limits. HuffPost uses a chronological dataset, frozen historical model pair and actual per-row predictions. Its 24-hour label delay is simulated, the date-only clock uses an explicit batch convention, and only one dataset/source cluster qualified. The Failure Atlas FLQ suite's balanced XOR streams remain replay adapters; episode resampling does not replace source-level uncertainty.

## Independent review

The read-only internal critical review is preserved in `docs/scoped_method_research_2026-11-06/INDEPENDENT_REVIEW.md`. It agrees with the decision above. It is an internal LLM subagent review, not external scientific review or theorem verification.

## Manuscript-ready four-contribution outline

1. **Diagnosis:** characterize when fixed-budget online deployment misses late challenger improvements and when post-promotion monitoring fails to reverse after a reversal; make the operating region and retrospective status explicit.
2. **Explanation:** decompose label timing, restart/acquisition, alpha, start grid, delay and switching costs using matched ablations; separate predictive loss, label expenditure and switch expenditure.
3. **Repair:** currently unsubstantiated. Only include after a frozen rule beats strongest matched published methods in a specified target region and the benefit is not explained by conventional front-loading or restart calibration.
4. **Validation:** a single-source negative transfer case study is available; independent multi-domain positive repair validation remains unsubstantiated.

This outline describes the evidence needed for a paper, not a claim that all four contributions are complete. Use corrected Sprint 2 outputs in the benchmark report while preserving original artifacts as historical provenance. For this execution, present the findings as a benchmark/case study and retain the negative and inconclusive outcomes.

## MN-DS context-screen amendment (2026-11-06)

After this assessment was drafted, a Q3-selected publisher-static rule and a standard context-wise
promotion/rollback composition were replayed on MN-DS Q4. This screen **did not pass** the prior
synthetic headroom and novelty gates, so the Q4 run is retained as exposed descriptive evidence,
not confirmation. The error is documented in
[`context_stratified_mnds_20261106/DECISION.md`](../../research/scoped_method/pilots/context_stratified_mnds_20261106/DECISION.md);
do not reuse this Q4 window as untouched evidence.

The context-wise rule made no promotion, had the same 1,033 errors as never-switch, and cost 1.64
more per 1,000 events than never-switch. It saved 2.29 per 1,000 versus the validation-selected
static rule, below the registered 5-unit practical threshold, with a simultaneous 99% interval
`[-5.75,+3.62]`. These results do not change any contribution gate: C1 and C2 remain **PARTIAL**,
C3 and C4 remain **FAIL**. The current disposition stays
**`BENCHMARK_OR_CASE_STUDY_ONLY`**.

## Chronological-news transfer update

The final HuffPost result strengthens the late-improvement diagnosis but does not advance a new
method claim. The PFA-SR transfer gate failed decisively against both frozen comparators. The
appropriate disposition remains **`BENCHMARK_OR_CASE_STUDY_ONLY`**; do not extend this candidate
search on the same source or reinterpret its unfavorable result as repair evidence.

The replay runner retained only hashes of per-event prediction/policy traces, not the traces or
date-level paired cost/count sufficient statistics. The aggregate point estimates and block-bootstrap
intervals are recorded, but an independent analyst cannot recompute the bootstrap endpoints from
the committed aggregates alone. Treat this as a reproducibility limitation; do not reopen the same
single-opening test window to repair the artifact.


## Bounded direct-composition follow-up (2026-11-06)

The omitted direct front-loading-plus-E_rb composition was screened on 20 paired seeds in each of four reused simulator regimes. It failed the stated economic gate: its F0_better saving over the front-loaded host was −3.86 (95% paired t interval [−12.35, 4.64]); its V_late_600 difference from paced E_rb was −9.65 [−19.89, 0.59]; and under F3_reversal_800 it cost +60.65 versus never-switch [42.52, 78.78]. It spent all 200 labels in every cell; null promotion was 1/20 (Wilson interval [0.009, 0.236]). The independent audit recomputed the 400 raw rows and net-cost identity. This closes the specific missing-composition question as a development falsification, but does not exhaust the design space or upgrade C3/C4. The protocol was not committed/checksummed before execution and source hashes were truncated in the dirty-run manifest. See [`DIRECT_FRONTLOAD_ERB_CRITICAL_REVIEW.md`](DIRECT_FRONTLOAD_ERB_CRITICAL_REVIEW.md) and [`ECONOMIC_HEADROOM_DECISION_20261106.md`](../../research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md). The decision remains **`BENCHMARK_OR_CASE_STUDY_ONLY`**.

## E-SR empirical operating-point follow-up (2026-11-06)

The existing conventional `E_srrSR:gated_deployment` detector was calibrated on 1,000 iid
`F0_null` streams per predeclared alpha and independently evaluated at the selected alpha 0.0005.
The independent null result was 20/1,000 promotions (one-sided 95% Wilson upper 0.0287), passing
the frozen empirical ≤0.05 gate. It did not improve deployment economics in the registered
reversal target: on `F3_reversal_1200`, candidate-minus-never cost was +22.75 [19.70,25.79] and
candidate-minus-E_swcert was +3.84 [0.12,7.57] over 200 paired seeds. On `F3_reversal_800`, its
harm versus never-switch was +45.76 [42.46,49.05]. This is an operating-point calibration of
published prior art, not a new mechanism; the track is closed after failing its prespecified
economic gate. Exact protocols, raw records, hashes, and analysis are in
`research/scoped_method/pilots/srr_any_false_calibration_20261106/` and
`research/scoped_method/analyze_srr_calibrated_evaluation.py`. The overall decision remains
**`BENCHMARK_OR_CASE_STUDY_ONLY`**; this additional result does not satisfy the active positive
repair objective.

## Calibrated E-SR late-improvement screen (2026-11-06)

On 100 fresh paired `F1_late_800` streams, calibrated E-SR alpha 0.0005 cost 365.60, saving
23.63 [19.40,27.86] versus PFA-SR:Gated adaptive range and 31.34 [26.98,35.69] versus Gated+front.
It also cost 6.20 less than matched RMM [1.44,10.96]. It was 21.01 [16.64,25.39] costlier than
Qiu-inspired and 14.39 [8.89,19.89] costlier than Gong-inspired ports; the latter two are not
author-native published implementations and promoted on 100/100 and 99/100 null streams. On the
fresh 100-stream null screen, E-SR promoted 2 times and its one-sided 95% Wilson upper bound was
5.86%, just above the frozen 5% gate (the earlier independent 1,000-stream evaluation at the same
alpha was 20/1,000, upper 2.87%). In the adverse reversal cell, it cost 45.07 [40.13,50.01] more
than never-switch. These results show a scoped comparison advantage over certificate-style and
PFA-SR policies, but fail the frozen all-comparator and null-precision development gates. Since
E-SR is prior art, this does not establish a new method; no real data was opened. The exact protocol,
outputs, hashes, and analysis are in `research/scoped_method/pilots/srr_late_improvement_20261106/`
and `research/scoped_method/analyze_srr_late_improvement.py`. The overall research objective
remains unresolved.

## 2026-11-06 scoped recovery and reversal follow-up

The latest execution recovered CI (the Ruff repair was already present at `82e1c48e`), recorded a candidate-specific test correction, and completed the economic-headroom follow-up. The full-suite run passed 3,336 tests, skipped 46, and exposed one short-null failure in the rejected split-90 configuration; that variant was quarantined from generic safety assertions and given a dedicated deterministic failure test. The focused file now passes 68 tests.

The new risk-separated E-SR setting (`alpha=0.0005`, rollback `alpha_rb=0.05`) passed its independent iid-null calibration (17/1,000; one-sided Wilson 95% upper 2.51%) and improved `F3_reversal_1200` by 10.16 net units vs never-switch (95% paired CI [−16.71,−3.61]). It failed its frozen adverse `F3_reversal_800` gate (+12.22 [8.48,15.96] vs never-switch) and lost to default E-SR on the persistent control (+34.48 [25.50,43.46]). The setting is explained by existing rollback alpha separation and is not advanced as novel or independently validated. Exact records, hashes, cost decomposition and reproduction commands are in [`EVALUATION_RESULTS.md`](../../research/scoped_method/pilots/srr_risk_separated_rollback_20261106/EVALUATION_RESULTS.md).

**Current decision: `BENCHMARK_OR_CASE_STUDY_ONLY` / `BENCHMARK_ONLY`.** Diagnosis is supported for the registered synthetic reversal generator; the acquisition/evidence/rollback/switch-cost interaction is the most consistent explanation, but the full causal decomposition remains partial. No novel repair passed its frozen gate and no real-world validation of a repair was performed. Do not open the locked Wild-Time arXiv or other holdouts under this failed development gate. Smallest next action: preserve this as a benchmark/case-study result, or define a new research objective before reopening any candidate search; do not retune the failed configuration.
