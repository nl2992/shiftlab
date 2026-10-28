# Research evidence inventory

**Recorded 2026-10-27, loop tick 2. Read-only.** No experiment was rerun and no raw or licensed
data was opened.

Four Sonnet subagents surveyed the repository by area and wrote Parts I–IV below. The lead
(Opus) read the 2026-10-26 decision gate, the publication-scope decision and the claim map
directly. The lead also re-checked every finding that this synthesis relies on against source
files or frozen outputs; Section 3 lists those checks and the corrections they produced. Where a
part disagrees with Section 3, Section 3 governs.

## 1. Implementation completeness versus research completeness

| Track | Implementation | Research status | Decisive record |
|---|---|---|---|
| Q1 detection (DIVE, paired-cost monitors, PPE, gating, betting engines, horizon detectors) | High: code, tests, frozen protocols, verifiers | **Checkpoint B, evidenced NO-GO** on a new monitoring algorithm. The S3 gating gain is credited to DISCERN. DIVE showed no adjusted advantage over Timans in a matched full-feedback test. PPE's gain is synthetic and depends on query rate. | `docs/phase_report_stratified_monitor.md`, `docs/algorithm_search_exit_ledger.md`, claim map C2, C3, C12 |
| Q2 certification (Target-Scout, MOPE, OPI, Certification Exponent) | High for registered synthetic runs | Target-Scout is confirmed only in its IID synthetic workflow. Logged-bandit certification is covered by existing methods, and OBD is exploratory. | Claim map C4, C5, C11 |
| Q3 intervention (budgeted promotion, rollback, retraining schedules, integrated controller) | Moderate: there is a pipeline, but no certified action rule | NO-GO on RIVE, ASC or any unified algorithm. The integrated result is profile-specific and the controller is inert. | `papers/shiftguard_unified/decision_gate_report_2026-10-26.md`, `integrated_efficacy_confirmation_results_v1.md` |
| Real data (EIA, Upworthy, CRSP, OBD, Criteo, Hillstrom, WILDS, Gas Sensor) | Loaders, receipts and replays exist; CRSP is script-only | Results are component-level, retrospective, and often on exposed windows. Nothing tests the complete system or gives prospective validity. | Claim map C7, C8, C10; `docs/eia_real_data_validity_results.md` |

## 2. Cross-cutting findings that matter for direction choice

1. **A trivial fallback dominates the integrated system on three profiles.** In the frozen
   100-seed integrated confirmation, `q1_fallback` (revert to the reference policy at the first
   monitor alarm) has mean expected gain:
   - +664.6 on `boundary_local_harm`, against +118.0 for `full_pipeline`, +186.5 for `two_gate`
     and +285.9 for `fixed_candidate_certification`;
   - +685.9 on `harmful_adaptation_at_monitor`;
   - +448.0 on `recurring_regimes`, where every certification arm gets 0.

   It loses heavily on `post_promotion_reversal` (−1,148.5, against −143.8 for `full_pipeline`),
   and gets 0 on `harmful_adaptation_native` and `residual_variance`. Source:
   `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/integrated_pipeline_summary.csv`
   (lead-verified). **Neither the integrated results report nor the manuscript discusses this
   arm.** When a safe reference exists, monitor-then-revert is the strongest simple baseline, and
   certification-based promotion adds value only where reverting is unavailable or harmful. This
   bears directly on Q3 and on any claim about promotion.
2. **Monitoring evidence:** the strongest positive evidence is the published-mechanism benchmark
   result. Gated sampling grew evidence 7.2× faster than correctly bounded uniform sampling, and
   G1's analytic prediction held within a factor of two at every budget. Under bursty
   disagreement, fixed gating beat past-paced gating (S3 R7 and EIA injected harm). No new
   mechanism survived its screen.
3. **The conditional-null assumption is load-bearing.** The persistent-sign stresses and the
   contextual-stratified null audit (`docs/residual_variance_context_null_audit.md`) show that
   pointwise-null validity does not carry over to mixed nulls. Promotion (Q2) and composition
   (Q3) are not calibrated under mixed nulls, adaptive queries, delayed feedback, or actions that
   change outcomes.
4. **Identification:** every paired policy comparison identifies both action losses from a
   common label, which holds only in the non-performative synthetic generators and in the EIA
   reserve task (where the costs are imposed). There is no randomized or off-policy design for a
   real Q2 or Q3 comparison except the OBD and Hillstrom logged data, and both are exposed or
   exploratory.
5. **Exposed real-data windows:**
   - CRSP's 2020–2025 test window is reused across at least five analyses.
   - The Upworthy holdout has been public since 2021.
   - EIA 2026 is called a "final-period confirmation" in one place
     (`eia_2026_out_of_time_confirmation_results.md`) and a "previously examined development
     window" in WP4. The later description is correct for any new use.
   - **No untouched real-data holdout exists for a new confirmatory claim**, apart from
     post-freeze EIA data that has not yet been pulled.
6. **No central seed registry.** There are 82 registered seed ranges, and several overlaps are
   undisclosed (Section 3). None is known to have caused tuning on evaluation seeds, but the
   disjointness claims in some protocols are false as written.
7. **Documentation lags the evidence.** The manuscript draft, the claim map (it has C12 but not
   S3 or WP4), `docs/closest_prior_work.md`, `docs/methods_and_assumptions.md`,
   `docs/implementation_status.md` and the Paper 1 README predate the 2026-10-27 phase. Test
   counts are stale (1,486, 1,563, 1,566 and 1,575 in various docs; 1,869 passed on 2026-10-27).

## 3. Lead verification log

| Claim (source part) | Check | Result |
|---|---|---|
| `q1_fallback` dominance (IV) | Read `integrated_pipeline_summary.csv` | **Confirmed**, numbers as in Section 2.1 |
| S2 null-calibration seed block (I) | `streams.parquet` seed column | Run used the registered `58500000–58501999`. `docs/gated_monitor_null_calibration_results.md:8` misstates `58300000–58301999`. **This is a documentation error; the run is valid.** |
| WP3 temporal incumbent "switches at 1200 and 1800" (I) | `docs/data_efficient_edetector_prescreen_protocol.md` | **Corrected:** one switch, at monitor index 1200, which is the 50% secondary onset and before the 75% primary onset (monitor index 1800). The baseline was openly registered as onset-informed ("late-prior"). The WP3 negative is against a favourably timed incumbent, which is a fair-comparison caveat. |
| `budgeted_promotion.py` hash drift (II) | `sha256sum` against manifests | **Confirmed:** current `681a4e13…` against `8eada2f9…` recorded in earlier manifests. Changed in `32c5cfd`; no equivalence re-run is recorded. |
| "Rollback not implemented" stale (II) | `docs/methods_and_assumptions.md:126` | **Confirmed stale:** the integrated pipeline implements rollback |
| Seed overlap `54000000–54000029` in `54000000–54000499` (III) | `docs/harm_power_grid_protocol.md:11` against `docs/policy_bound_null_calibration_protocol.md:15` | **Confirmed.** Both documents claim disjointness. |
| Seed overlap at `20290000` (III) | `docs/delayed_evidence_ppi_markov_calibration_protocol.md` against `docs/start_prior_robust_mix_protocol.md:35` | **Confirmed.** The start-prior protocol claims no overlap. |

Findings in Parts I–IV that are not listed above have **not** been lead-verified. Line-number
citations in those parts may be approximate.

## 4. Open items carried forward to Phases B–D

- Is there a differentiated contribution after Ahmed et al. (2026), Digalakis et al. (2025/26),
  Regol et al. (ICML 2025), DISCERN, MOPE and Wang (2026)? Phase B must check this from primary
  sources.
- Is "monitor-then-revert versus certify-then-promote" (Section 2.1) a real research question
  with a defensible estimand, or a benchmark observation? This is a Phase C candidate.
- Small documentation fixes: the S2 seed typo, the stale rollback sentence, test counts and the
  duplicate Wang reference. They are not part of the refinement; offer them to the user
  separately.

---

# Part I. Paper 1 / decision-harm monitoring (subagent survey, not lead-verified except as listed in Section 3)

## A2 evidence inventory: Paper 1 / decision-harm monitoring

Scope: read-only. No tests or experiments were run. Raw/licensed data were not opened. All paths are relative to the repo root. Under `docs/` the repo holds roughly 200 protocol/result pairs for this area, so the 2026-10-27 phase is covered in detail. The 2026-10-24/25 delayed-feedback line is covered at family level.

**Bottom line.** Implementation is essentially complete for what was registered. Research completeness is low. There is no confirmatory, non-synthetic, non-gating result. The phase ended at "checkpoint B", an evidenced NO-GO for a new monitoring algorithm (`docs/phase_report_stratified_monitor.md` L3-10; `docs/algorithm_search_exit_ledger.md` L3-4).

### 1. Methods (verified to exist)

| Method | Location |
|---|---|
| Disagreement-gated HT/PPI replay (G1, G1f, G2, G3 arms) | `src/shiftlab/dive/gated_monitor_comparison.py::replay_gated` (L136), `gated_increment` (L62) |
| Past-only 200-event pacer (floor 0.10) | same file, `DisagreementPacer` (L86) |
| Shared path generation and evaluator split | `gated_monitor_comparison.py::comparison_seed` (L239) |
| Feature ADWIN sentinel (not a harm test) | same file, `feature_adwin_alarm` (L37) |
| Bounded-mean mixture; predictable-bound; started mixture; variance-adaptive Kelly; PM-EB; hedged positive; PPI block CS/mixture | `src/shiftlab/dive/eprocess.py`: `BoundedMeanEProcess`, `PredictableBoundMeanEProcess`, `PredictableStartedMixtureEProcess`, `PredictableVarianceAdaptiveEProcess`, `PredictablePlugInEmpiricalBernsteinEProcess`, `PredictableHedgedPositiveEProcess`, `PPIBlockConfidenceSequence`, `PPIBlockMixtureEProcess` |
| Timans (approx.) GRAPA, fixed08/fixed1/plugin/pm_eb engine parity | `comparison_betting_engines.py::replay_engine` (L25). It imports `_timans_logs` from `scripts/reproduce_timans_risk_monitor_paired_cost.py` (L69) |
| PPE factor (Csillag) | `prediction_powered_evalues.py::prediction_powered_factor`, `PredictionPoweredEProcess` |
| Xu active betting (formula level) | `xu_active_betting.py::xu_paired_betting_factor`, `XuActivePairedEProcess`, `xu_variance_query_policy` |
| Horizon SR/CUSUM e-detector | `horizon_edetectors.py::HorizonCalibratedEDetector` |
| WP3 optional-observation replay | `data_efficient_prescreen.py::optional_policy_replay` (L23), `evidence_replays` (L191); `data_efficient_source_panel.py::build_path`, `source_panel` |
| WP2 stratified e-process, allocation, growth screen | `stratified_harm_eprocess.py::StratifiedEProcess`; `stratified_eprocess.py::ContextStratifiedEProcess`; `stratified_harm_allocation.py::minimax_support_allocation`; `stratified_growth_prescreen.py::evaluate_slice` |
| ADG anchor analytic screen | `adg_growth_prescreen.py::prescreen_stream`, `expected_log_growth`, `solve_tilt` |
| WP4 EIA paired reserve, orientation null, injected harm | `eia_paired_reserve.py::build_respondent_streams`; `orientation_replay.py`; `eia_injected_harm.py::inject_under_procurement`; `eia_validity_analysis.py::null_analysis`, `injected_analysis` |
| Delayed event-prefix buffer | `delayed_feedback.py::EventOrderBuffer` (ordering primitive only; its docstring says it is not a validity result) |
| Evidence-directed query (earlier line) | `query.py::EvidenceDirectedQueryPolicy` (L244); driver `delayed_evidence_directed_ppi.py::_simulate_method` |
| Other query policies | `query.py`: `AdaptiveQueryPolicy`, `EvidenceGrowthQueryPolicy`, `ExactMixtureGrowthQueryPolicy`, `RobustMixtureGrowthQueryPolicy` |
| Complete-feedback Hoeffding e-process | `src/shiftlab/monitoring.py::HoeffdingExcessEProcess`; also `conformal_upper_threshold`, `one_sided_cusum` |

- `src/shiftlab/core/` holds only `config.py` (run config). It has no monitor logic.
- The Paper 1 folder `papers/paper1_decision_drift/` has no code.
- Out of area (Paper 2 / promotion): the `budgeted_promotion*`, `promotion*`, `persistence_promotion`, `scout_*` and `contextual_*` families. They are not inventoried here.

### 2. Assumptions: intended versus implemented

| Item | Intended (docs) | Implemented (code) | Match? |
|---|---|---|---|
| Null | `E[H_t \| F_{t-1}] <= 0`, `H_t = Z_t - eps` (`docs/research_charter.md` L36-46; `docs/methods_and_assumptions.md` Target and filtration) | Same, via `PredictableBoundMeanEProcess` etc. Validity is not checked in code. `eprocess.py` and `horizon_edetectors.py` docstrings say so | Yes, by design |
| Filtration with current stratum/disagreement | Stratum or disagreement is known pre-outcome but is not `F_{t-1}`-measurable. Proof is by the optional-subsequence factor (`methods_and_assumptions.md` "Validity: standard subgroup betting composition"; `theory_notes.md` WP3 section) | `replay_gated` uses `active[i]` (current-feature policy disagreement) to gate. Pacing uses only past actions/tariffs (`DisagreementPacer.observe` is called after the update). Tests: `test_pacing_ignores_outcomes`, `test_current_actions_enter_only_next_propensity` | Yes |
| Predictable bound | `B_t = 5/q_t + eps` (HT) or `(5+eps)(2/q_t - 1)` (PPI), where `q_t` is a function of the past only | `gated_monitor_comparison.py` L180-181 | Yes |
| Covariate-dependent bounds | A bound chosen from the current covariate needs a pointwise null. A marginal null is insufficient (`docs/marginal_null_predictable_bound_audit.md`) | WP1 avoids current-covariate bounds. The older `bound_mode="decision_local"` in `hard_budget.py` requires the stronger null (`methods_and_assumptions.md` "Predictable decision-local betting bounds") | Yes. Old runs carry this caveat |
| Subgroup null | The stratified (WP2) null is the intersection null. It is stronger than the pooled null | `docs/residual_variance_context_null_audit.md`: the earlier contextual-stratified e-process tests a null that is false in the registered controls. Its alarm rates are not interpretable as pooled-null calibration | Documented mismatch. Earlier `contextual_stratified_*` results must not be read as pooled-null results |
| Boundedness | Costs are in [-5,5]. Proxy clipped at 5.1. Increment `|v| <= B_t` | `replay_gated` raises if the bound is exceeded. The S3 numerical amendment snaps rounding up to 1e-9 relative (L~172-176) | Yes, with the amendment (`docs/gated_monitor_s3_numerical_amendment.md`) |
| Independence | The synthetic control events are independent. The control-null clarification in the WP1 protocol (Section 2) rests on this generator, these actions and this cost matrix | The generator is iid within regime | Holds only for this generator. `docs/delayed_ppi_persistent_sign_stress_results.md` shows alarms of 7.25% / 72% / 98% at sign persistence rho = 0.5 / 0.9 / 0.98. That is a violated-null diagnostic, not a monitor failure |
| Label delay | Delay-12 prefix argument: alarm only on the contiguous resolved prefix. This holds for arbitrary finite delays if delays are not used as signal (`docs/delayed_event_prefix_validity.md`) | `EventOrderBuffer`. `delayed_evidence_directed_ppi.py::_simulate_method` feeds the query rule from `query_process.log_e_value` on the resolved prefix | Yes for delayed-line runs. WP1, WP2, WP3 and WP4 are immediate feedback only (protocol L"Immediate feedback only"; WP4 protocol L153 "Monitor labels are assumed to arrive at once") |
| Query-coin independence | `Q_t ~ Bernoulli(q_t)`, independent of the current outcome given the past | Shared uniforms: `np.random.default_rng(seed + 9_173).random(3200)` | Yes |
| Policy predictability | The deployed policy is frozen or predictably selected | Synthetic: the deployed policy is a fixed function. `harmful_adaptation` switches to "always 1" at event 1600 by hand (`comparison_seed`). The EIA frozen Ridge versus a weekly-refit Ridge reference | Fixed switch only. No learned or adaptive policy-selection filtration is tested |
| Reference counterfactual loss | Both action losses are identifiable from the same outcome | Synthetic binary cost, so yes. EIA costs are imposed (shortfall 5 / idle 1) | Real-world identifiability is not tested |
| Oracle isolation | Evaluator truth stays out of the learner | `comparison_seed` computes `expected`/`probability` evaluator-side. `replay_gated` receives none of these. Test: `test_runner_matches_existing_ungated_and_oracle_perturbation_is_learner_invariant` | Yes |
| Paced HT and the pooled null | Pooled gating retains the known agreement factors | `gated_increment` returns `-eps` on agreement | Yes. The caveat that a naive K=2 subgroup process is not identical is in `theory_notes.md` ("Gating special case") |

**Real-data null.** The EIA check is a random-orientation null (S_t swaps the policy roles). At eps = 0.1 it is trivially conservative, because the centered mean is -eps. It is informative only on CISO-2026 (150 disagreements) at eps = 0 (`docs/eia_real_data_validity_results.md` section (a)). See the phase report L128-136 for the same caveat.

### 3. Experiments (2026-10-27 phase; every stage registered before it ran)

All stages are synthetic except WP4. The comparators in all cells are the WP1 panel: Timans approximate/grid GRAPA, PPE, Xu, gated HT/PPI/EB, uniform PPI, variance PPI, full feedback, no-action and feature ADWIN. Each one runs on the shared engine panel.

| Stage | Protocol (frozen at) | Seeds / data | Headline result | Artifact | Frozen before run? |
|---|---|---|---|---|---|
| WP1 S0 implementation | `docs/gated_vs_ungated_monitor_comparison_protocol.md`, freeze commit `50c4314f` (2026-10-27T08:40:32Z) | n/a | Tests passed | `docs/gated_monitor_implementation_results.md` | Yes |
| S1 fidelity replay | same | historic 20373024-083 | Exact: 6/60 at B=96.9 and 47/60 at B=45.9; log-wealth matches to 1e-10 | `outputs/gated_monitor_fidelity/`; `docs/gated_monitor_fidelity_results.md` | Yes |
| Smoke | same | 58600000-04, budget 0.2 | 205 rows, no cap violations. Excluded from inference | `outputs/gated_monitor_smoke/` | Yes |
| S2 null calibration | same | **58500000-58501999 per cell** (code `scripts/run_gated_monitor_comparison.py` L168 and the protocol). The results doc says "58300000-58301999" (see Section 7) | 16,000 streams. Primary arm 0-6 alarms per 2,000; max simultaneous upper bound 0.764% (primary), 1.953% (PPE alias, worst) | `outputs/gated_monitor_null/{manifest,launch}.json`; `docs/gated_monitor_null_calibration_results.md` | Yes |
| S3 comparison | same + numerical amendment | 58400000-58400099, 100 per scenario x budget, budgets 0.02/0.05/0.10/0.20 | P1 growth ratio 7.20 (lower bound 6.88; rule >= 2). P2 100 wins / 0 losses, McNemar p = 7.9e-31. Prediction vs measured: 17.5/20.6/14.7/7.2 against 18/18/15/7.5. R7 prediction falsified: fixed gating >= paced gating under `harmful_adaptation` | `outputs/gated_monitor_compare/analysis/decision.json`; `docs/gated_monitor_comparison_results.md` | Protocol yes. Source partly uncommitted at launch (Section 5) |
| WP2 G1 (stratified) | `docs/stratified_harm_monitor_development_protocol.md`, freeze `7dd8d94a` | 58700000-019, learner slices only, no monitor window | 19,440 rows. Candidate equals the subgroup composition to 4.44e-16; ratio <= 1.000 (rule 1.5). Stopped before the 588/589 blocks | `outputs/stratified_growth_prescreen_20/`; `docs/stratified_growth_prescreen_results.md` | Yes |
| ADG G1 (anchor) | `docs/anchored_gated_harm_monitor_development_protocol.md` | 58000000-019; 18 of 20 seeds feasible | Ratio 1.000 at r=0.20 (q_D = 1, so the anchor has no effect). At most 1.23x at r=0.02. Stopped | `outputs/adg_growth_prescreen_20/`; `docs/adg_growth_prescreen_results.md` | Yes (prediction written before output) |
| WP3 data-efficient e-detector | `docs/data_efficient_edetector_prescreen_protocol.md`, freeze `d0a350a0` (2026-10-27T14:30:35Z) | 59000000-019, 2 onsets x 4 budgets | 39,200 rows. Primary cell: candidate 11/20 (55%, Wilson 34-74%) against 20/20 for the temporal fixed1/started incumbent. Delay ratio 0.353. Failed all 7 secondary cells. Stopped | `outputs/data_efficient_prescreen_20/`; `docs/data_efficient_edetector_prescreen_results.md` | Yes |
| WP4 EIA validity | `docs/eia_real_data_validity_protocol.md`; hash freeze `docs/eia_real_data_validity_freeze.json` (protocol SHA `c40620ba...`, streams SHA `bcb3bcbe...`, 2026-10-27T20:58:55Z) | 4 retrospective paths (CISO/ERCO 2025/2026), 68 null cells x 1,000 coin replicates | 68/68 pass, 0/1000 each (upper 0.0030). Descriptive: eps = 0 peak 28/1000 (0.0382). Injected under-procurement: fixed gating matches the full-feedback median delay from r = 0.05 in 10/10 detectable cells. Paced gating degrades | `outputs/eia_real_data_validity/`; `docs/eia_real_data_validity_results.md`; `docs/phase_tables_stratified_monitor/wp4_*.csv` | Yes. Sources uncommitted at the S3 launch; frozen by hash |
| Exit ledger | `docs/algorithm_search_exit_ledger.md` | n/a | M1-M4 and M7 failed. M5 and M6 are credited to DISCERN and the published engines. M8 is moved to Paper 3 | same | Written before S3 results existed (stated L8) |

Older Paper 1 lines, family level (all synthetic CUDA; each has a protocol/results pair in `docs/`):

- **Delayed-feedback line (2026-10-24/25).** The evidence-directed delay-12 PPI monitor passed null calibration (0.4%; simultaneous upper 1.12%). On the disjoint confirmation it detected 92/1,000 versus 36/1,000 for uniform (`delayed_evidence_directed_ppi_*_results.md`). An independent fixed-12 confirmation gave 82/1,000 versus 41/1,000 (`delayed_ppi_adaptive_fixed12_harm_confirmation_results.md`). Absolute power is below 10%.
- **History-predictable bound (2026-10-24).** The 4,000-stream confirmation gave +3.95 pp over a fixed bound. Calibration upper limits are at most 2.25%. The Markov variant gave +5.66 pp (`history_predictable_bound_confirmation_results.md`; `markov_predictable_bound_validation_results.md`).
- **Start-time mixtures.** Matched shadow confirmation: 24.2% versus 18.8% (`delayed_evidence_ppi_start_mixture_confirmation_results.md`).
- **Hard-budget, 20% operating point and diagnostics.** `evidence_budget20_comparison_results.md` found that the evidence-directed candidate does not advance. Uniform detected 6/60 at B = 96.9. The B = 45.9 replay shows 47/60 (`propensity_floor_diagnostic_results.md`).
- **Early development lines.** `monitor_power_diagnostic_results.md`: 0/30 detections for all monitors. Also `risk_proxy_monitor_*_results.md`, `regime_warning_grid_results.md` and `horizon_hedge_sweep_results.md` (no promotion).
- **CRSP replays (retrospective).** `crsp_monitor_comparison_results.md` and `crsp_eprocess_candidate_replay_results.md`: no strong decision-harm monitor was identified. No candidate crossed (max log-e 0.062).

### 4. Findings

**Positive (with scope limits)**

- WP1 S3: gating raises growth 7.2x at r=0.20 and detection from 0.00-0.01 to 0.82-1.00 at r <= 0.05. This is the DISCERN mechanism, so it is not novel. The analytic G1 growth prediction held within about 15% (S3 results; `adg_growth_prescreen_results.md`).
- WP1 S1: the correction 6/60 -> 47/60 on identical increments (a bound artifact, not a power difference).
- WP1 S2 and the S3 null cells: at most 2/100 false alarms. These are synthetic iid nulls. The largest S2 upper bound is 1.953%.
- WP4: fixed gating matches full-feedback delay from r = 0.05 on injected EIA harm, using 338-701 labels. This is retrospective, with imposed costs.
- Delayed-line confirmations passed their registered gates on the single registered DGP. Effect sizes are 4-6 pp over uniform, from low absolute power.

**Inconclusive**

- WP4 random-orientation null at eps = 0.1: 0/1000 everywhere is expected from conservativeness. Three of four paths have 1-7 disagreements.
- WP4 unmodified streams: no harm found, with no ground truth.
- The `ungated_ht` r = 0.20 alarm on CISO-2026 (2/200) has no interpretation.
- ADG at r >= 0.10: q_D = 1, so the anchor is untestable.
- WP3 and WP2 stopped before any null calibration or simulated detection. Nothing is known about stratified detection power.
- The WP3 negative is against an incumbent whose schedule aligns with the registered onset (Sections 5 and 7).
- Delayed ppi `informative_delay` calibration: 11/12 cells pass. The fixed12/evidence-directed/full-stream cell failed its simultaneous gate (5/250, upper 5.66%). A 2,000-stream replication passed (9/2,000), but the two blocks are not pooled (`delayed_ppi_adaptive_informative_delay_results.md`, `delayed_ppi_adaptive_fixed12_replication_results.md`).

**Negative**

- WP2 (stratified), WP3 (adaptive observation controller) and ADG (anchor) all failed their registered screens. Net result: no new Paper 1 algorithm.
- The R7 prediction is falsified (S3 results, finding 4). Past-paced gating is beaten by fixed gating under bursty disagreement. Both are DISCERN-style.
- Low budgets under `harmful_adaptation`: every selective arm detects at most 0.33 at r <= 0.05.
- Under `harmful_adaptation`, PPI hurts detection: 0.36-0.39 versus 0.50-0.59 for gated HT.
- The persistent-sign stress shows the conditional-mean-null assumption is load-bearing.
- No DIVE monitor advantage over Timans in matched full feedback (`papers/shiftguard_unified/claim_evidence_map_v1.md` C2, R1).
- The earlier contextual-stratified null is false in the controls (`residual_variance_context_null_audit.md`).
- Early diagnostics: 0/30 detections for all monitors (`monitor_power_diagnostic_results.md`).
- CRSP: no strong monitor.

### 5. Reproduction, freezes, leakage risks

**Hashes and freeze records**

- WP4: protocol SHA, six code SHAs and streams SHA in `docs/eia_real_data_validity_freeze.json`.
- The S2 receipt table lists six SHA-256 values (`docs/gated_monitor_null_calibration_results.md`).
- WP1 S1 and the smoke run have manifest hashes.
- Every stage records `launch.json` and `manifest.json` with source hashes, `git_head`, dirty paths and hardware.
- The data-efficient and stratified results docs carry SHA tables.
- CRLF caveat: Git stores LF. A CRLF checkout gives different hashes from the WP4 freeze record (phase report L198-199).

**Seed separation**

- 58M blocks: 580 ADG, 581/582/583 ADG reserved and unused, 584 S3, 585 S2, 586 smoke, 587 WP2, 588/589 reserved for WP2 and unused, 590 WP3, 591 reserved for confirmation.
- Disjointness is asserted in the protocol (L"58M sub-blocks ... do not appear elsewhere"). I did not verify it by grep beyond `scripts/run_gated_monitor_comparison.py`.
- S1 deliberately reuses historic seeds 20373024-083, as a fidelity replay.
- `monitor_signal_diagnostic` and `propensity_floor` reuse seeds and are labelled descriptive.
- Older lines use separate blocks (for example 20280000-999 calibration, 20282000-999 confirmation, 27104027-27108026).

**Provenance risks**

- The S3 launch had HEAD `d0d49f6` with `gated_monitor_comparison.py` and its test modified but uncommitted (`outputs/gated_monitor_compare/launch.json` `dirty_paths`). The amendment was committed afterwards in `a4c3800`. Source hashes are recorded.
- The S2 run started at `fcbc54e2` with two uncommitted WP2 files. It ended at `1e2cba73`, with a different HEAD.
- Two earlier S3 launches crashed, with no outputs written. They are retained as `outputs/gated_monitor_compare_aborted_*` and `_crashed_*`.
- The 42 phase commits are unpublished to GitHub (`docs/research_refinement_v1/REPOSITORY_STATE_AUDIT.md`).

**Leakage / tuning risks**

- WP3 incumbent is onset-aligned. The "temporal" policy raises intensity at monitor index 1200, and the started mixture opens a start at 1800. In the protocol, absolute onset 2600 = monitor index 1800 (primary) and 2000 = index 1200 (secondary). A learner could not know these. Inferred from the protocol text; not otherwise checked.
- The WP4 injected-harm band uses the 2024 rehearsal median margin. This is an evaluator-side design choice. All four EIA paths are previously examined development windows (WP4 results, header).
- The "harm onset" in synthetic data is a scheduled change (`change_fraction`) or a path-based material-harm onset (`_material_harm_onset`). Neither is a causal real-world time (AGENTS.md).
- Oracle isolation is test-verified for WP1. I did not audit the WP3 `evidence_replays` code for it.
- No tuning on S3 seeds is evident: the protocol says "no arm, budget, stake, or threshold may be changed after Stage 3 outputs exist". The harmful-adaptation stress is descriptive.

### 6. Unsupported claims, missing comparisons, open questions

- **Not claimable.** A new monitoring algorithm, superiority over the composed panel, real-world harm detection, prospective validity, or a general anytime-valid guarantee. The conditional excess-cost null remains a target, not an established guarantee (AGENTS.md).
- **Prospective EIA data.** None pulled. Earliest useful check is about 2026-12-08, pending API key or bulk snapshot (phase report L173-182).
- **The only real-data evidence is the EIA retrospective path.** Costs are imposed, delay is 0, disagreements are rare.
- **No delayed-feedback validity or power test inside the WP1 gated design.** Delays appear only in the earlier delayed line, which uses a different generator and a zero-proxy PPI.
- **Missing or excluded comparators.**
  - DISCERN official code: not reproduced. G3 and the EB arm are adaptations (phase report L143).
  - Comparecast, PPRM, MOPE/OPI/Wang: excluded for target mismatch. The reason is stated.
  - Podkopaev-Ramdas confidence-sequence risk monitor: named as a direct comparator in `docs/delayed_event_prefix_validity.md`. I did not find it run in the 2026-10-27 panel (`not found`).
  - DE-CuSum: cited, not implemented.
- **Open.**
  - Whether M8 (burst-robust allocation) beats fixed gating. Out of Paper 1 scope.
  - Whether a late-onset advantage exists against a non-oracle-aligned start set.
  - Stratified detection power. WP2 stopped before it was measured.
  - Gated `eb` arm under harmful adaptation.
- **Claim-to-evidence map not updated for WP1/WP4.** The WP1 protocol (Section 6) says to update it after rules 1-4. `papers/shiftguard_unified/claim_evidence_map_v1.md` has C12 for WP2/WP3 only. Its grep for "gating/WP1/WP4" gave no match beyond C5/C6/C9/C10. `manuscript_draft_v0.md` has no gating finding.

### 7. Conflicts between older docs and newer code/results

1. **S2 seed block.** `docs/gated_monitor_null_calibration_results.md` L8 says `58300000-58301999`. The frozen protocol (`docs/gated_vs_ungated_monitor_comparison_protocol.md` L194) and the runner (`scripts/run_gated_monitor_comparison.py` L168; `scripts/analyze_gated_monitor_comparison.py` L75) use `58500000-58501999`. The analysis script requires exactly 585. The results doc is wrong. It is also the ADG-reserved 583 block, which the protocol says will not be used. I did not open the manifest's seed list.
2. **Paper 1 folder docs are stale.**
   - `papers/paper1_decision_drift/experimental_protocol.md` (seeds 11/22/33, n=1200, delay 3) and `hypotheses.md` (KS versus CUSUM) describe the original baseline study.
   - `papers/paper1_decision_drift/README.md` says "baseline study ... not novel algorithms".
   - `docs/implementation_status.md` says "Novel methods: intentionally not started" and "No theorem or novelty has been established".
   - The code and `docs/phase_report_stratified_monitor.md` now carry about 100 DIVE modules and a closed phase.
3. **Charter versus phase report on method status.** `docs/research_charter.md` L132-134 describes the Paper 1 folder as "not yet the proposed anytime-valid decision-harm method". The phase report ends the search with "no new algorithm". These are consistent. But the README predates the delayed-line "confirmation" language (`docs/methods_and_assumptions.md` mentions confirmations that "passed"). Those confirmations are on one DGP and are not novelty claims.
4. **Pacing finding framing.** `docs/eia_real_data_validity_results.md` L~95 calls the pacing result "new and practically relevant". `docs/phase_report_stratified_monitor.md` L109-124 and the exit ledger R7 call the same effect a benchmark finding that is "not a method (both DISCERN-style)".
5. **Uniform PPI baseline.** `docs/evidence_budget20_comparison_results.md` (6/60, bound 96.9) is superseded by `docs/propensity_floor_diagnostic_results.md` and S1 (47/60 at 45.9). The correction note is in the older doc. `docs/methods_and_assumptions.md` also still describes "fixed worst-case bound M(2/q_min-1)" for uniform PPI. The manuscript and claim map do not yet cite the correction.
6. **Exit ledger commit count.** `algorithm_search_exit_ledger.md` L48 says "41 were used". The audit counts 42 unpublished commits (`REPOSITORY_STATE_AUDIT.md`). This is a minor timing difference.
7. **Test counts.** The phase report says 52 tests for `tests/test_gated_monitor_comparison.py`. The file has 12 test functions. The difference is parametrization. Not verified by running.

### Implementation versus research completeness

- **Implementation complete** for the registered phase: S0-S3, WP2/WP3/ADG prescreens, WP4, with test files for each (`tests/test_gated_monitor_comparison.py`, `test_stratified_growth_prescreen.py`, `test_data_efficient_prescreen.py`, `test_adg_growth_prescreen.py`, `test_eia_*`, `test_orientation_replay.py`). The `outputs/` directories are present but I did not re-run them.
- **Research incomplete.** There is no confirmatory study for the benchmark manuscript claims. The 591 confirmation block is unused. There is no prospective real data, no delayed-feedback gated design, and no real-data evidence of actual harm. Per the exit ledger, the next productive step is the benchmark manuscript (continue) or a user-approved Paper 3 / Paper 2 pivot. This is not a method paper.

# Part II. Q2 certification and Q3 intervention (subagent survey, not lead-verified except as listed in Section 3)

## A2: Q2 certification and Q3 intervention evidence inventory

Snapshot: branch `research/phase-progress-2026-10-27`, HEAD `caff0ed`, read-only. Paths are repo-relative. SD = `papers/shiftguard_unified/`. No tests, runs or raw data touched. Hashes below were computed with sha256sum on the working tree.

**Headline.** Implementation completeness for Q2/Q3: high (code, tests, verifiers, hash manifests exist for every registered synthetic run). Research completeness: low to moderate. Q2 has a calibrated, independently confirmed synthetic result for Target-Scout. Q3 is mostly heuristic controllers plus retrospective EIA baselines. There is no real-data end-to-end Q2/Q3 evidence, no certified Q3 action rule, and the programme itself records a NO-GO on RIVE/ASC (`SD/decision_gate_report_2026-10-26.md`, `SD/gap_analysis.md:78`). RIVE and ASC have no code; grep of `src/`, `scripts/` and `tests/` found no matches. They appear only as "do not develop" notes in docs.

### 1. Methods (file:function, verified present)

| Method | Location | Notes |
|---|---|---|
| Bounded-mean betting e-process (shared engine) | `src/shiftlab/dive/eprocess.py::BoundedMeanEProcess` (l.38; `alarm` = log E >= -log alpha) | Fixed 5-stake mixture; validity only under stated conditional-mean null (docstring l.38-45). |
| Shadow candidate certificate | `src/shiftlab/dive/promotion.py::CandidatePromotionTest` | Full-feedback paired costs; alpha_i = alpha_total/[i(i+1)] (union over unbounded candidate sequence); switching cost in the increment; certificate absorbing (`tests/test_dive_promotion.py::test_candidate_certificate_is_absorbing_after_first_threshold_crossing`). |
| Promote then rollback state machine | `src/shiftlab/dive/controller.py::CertifiedPromotionRollback` (`observe_shadow`, `observe_deployment`) | Two independent e-processes; alpha split 50/50 by default; costs amortised over a fixed deployment horizon. |
| One-step cost-aware controller | `controller.py::InterventionController.choose` | Heuristic argmax of supplied forecasts; promote needs certificate, fallback needs authorisation. No guarantee (docstring). |
| Repeated-candidate sparse-label certification | `budgeted_promotion.py::_fit_candidate_family` (l.254), `_monitor_family` (l.382), `_monitor_validation_context_policy` (l.801); alpha allocation `promotion_grid._candidate_alpha_allocations` | Rank / equal / validation-power alpha spend; direct-IPW or PPI increments; pathwise label cap. |
| Target-Scout | `budgeted_promotion.py::_monitor_scout_context_policy` (l.1011) | First half of target monitor: IPW per-context argmax among 13 candidates (selected only if net gain > 0). Second half: one e-process on the frozen composite policy. Scout labels charged to the same cap. Modes `minimum_propensity` / `eventwise_propensity` (`SCOUT_BOUND_MODES`, l.50). |
| Fixed-split / pooled-rank comparators | same file (`_monitor_validation_context_policy`, `_monitor_family`); drivers `scripts/compare_target_scout_fixed_split.py`, `scripts/calibrate_target_scout_fixed_split.py`, `scripts/confirm_target_scout_fixed_split.py` | Source-validation selection, then a full independent target-monitor certificate. |
| Two-gate closed loop | `closed_loop_intervention.py::_simulate_gate` (l.72), `_evaluate_methods` | continue / unconditional promote / promote-only / promote+rollback. |
| Context-stratified gate | `contextual_stratified_intervention.py::_stratified_gate` (l.138) | Bonferroni over fixed learner-visible contexts. |
| Persistence gate | `persistence_promotion.py::_two_phase_decisions` | Discovery plus disjoint persistence phase. |
| Integrated Q1-Q3 | `integrated_pipeline.py::run_seed` (l.547), `_controller_decision` (l.211), `_fixed_candidate_certification` (l.270) | alpha .02/.015/.015 (protocol `SD/integrated_efficacy_confirmation_protocol_v1.md`); learner and evaluator event schemas separate (`LEARNER_EVENT_SCHEMA` / `EVALUATOR_EVENT_SCHEMA`, l.~66-100). |
| Adaptation baselines (Q3, EIA) | `rccda.py::RCCDAState.decide`, `cara_retraining.py::{tune_threshold,tune_periodic,threshold_schedule,periodic_schedule}`, `upf_retraining.py::upf_retraining_schedule`, `drift_retraining.py::replay_drift_schedule`, `eia_paired_reserve.py`, `reserve_costs.py` | Task-specific adaptations of published rules; not paper reproductions (`SD/evidence_inventory.md`). |
| Comparators for certification | `certification_exponent_one_step.py::ProjectedKellyOneStep`, `open_bandit_mope.py`, `anytime_policy_identification.py::{bounded_dr_pseudo_outcomes,lil_value_bounds,optimal_policy_stopping_time}`, `scripts/reproduce_anyrank_shiftguard.py::_anyrank_select` | MOPE/OPI/AnyRank adaptations; AnyRank v1 invalid (cost reversal bug), v2 exploratory. |
| Query/acquisition (Q3 info allocation) | `src/shiftlab/dive/query.py` (`AdaptiveQueryPolicy`, `EvidenceDirectedQueryPolicy`, `ExactMixtureGrowthQueryPolicy`, `RobustMixtureGrowthQueryPolicy`), `hard_budget.py::run_hard_budget`, `active_inference.py`, `robust_asi_fixed_horizon.py` | Budget-allocation heuristics; ASI is fixed-horizon, no sequential guarantee. |
| Conformal baselines | `src/shiftlab/methods.py::{weighted_conformal_quantile,exponentially_weighted_conformal_quantile,rolling_quantile}`, `learner.py`, `monitoring.py::conformal_upper_threshold` | Supporting baselines only (`papers/paper2_adaptive_conformal/README.md`). |
| RIVE / ASC | not found | Explicit NO-GO. |

### 2. Assumptions: intended vs implemented

| Issue | Intended (doc) | Implemented / observed | Flag |
|---|---|---|---|
| Counterfactual action losses | Paired losses identified from the common label, else randomised/OPE design (`SD/mathematical_problem.md` s.4; `docs/methods_and_assumptions.md:126`; `docs/research_charter.md` Paper 2) | Synthetic: cost = f(action, y) with outcomes non-performative, so both policy costs are identified from y; under sparse labels the increment uses known predictable propensity IPW (`budgeted_promotion.py` l.1040-1075, `z1/z0` indexed by observed y). Real: EIA/WILDS/Gas Sensor are common-label (imposed costs); Upworthy and Hillstrom are randomised arms; OBD needs MOPE/OPE; Criteo Uplift and Project GATE judged ineligible (`SD/decision_gate_report_2026-10-26.md` item 3). | Consistent in synthetic runs. All synthetic evidence is non-performative, so "action changes outcome" is untested for Q2/Q3. Real Q2/Q3 evidence with performative actions: not found. |
| Selection/multiplicity | Candidate selection on scout/dev data, certification on fresh data; FWER for many candidates/contexts (`mathematical_problem.md` s.6) | (a) `CandidatePromotionTest`: alpha_i = alpha/(i(i+1)). (b) Pooled-rank: validation-frozen alpha weights, union bound conditional on pilot (`methods_and_assumptions.md:142`). (c) Target-Scout: data split, full alpha on one frozen composite. Per-context argmax over 13 candidates is absorbed by the split, not by alpha. (d) Integrated: alpha .02/.015/.015. | Valid in principle only if scout/certification data are exchangeable-enough that selection does not change the conditional null. Calibrations cover: zero-signal global null (`SD/target_scout_fixed_split_null_calibration_protocol.md`: every candidate has exactly zero gross gain), abrupt context-prevalence, Markov and temporal schedules (older `docs/scout_context_policy_*_null_*`). Not calibrated: mixed nulls (some candidates truly positive, composite selected from both), adaptive query probabilities beyond the registered uniform/variance policies, delayed feedback, performative effects. Rollback validity after data-dependent promotion needs an independent forward slice (`controller.py` docstring); only the registered generators supply one. |
| Optional stopping | Anytime-valid via Ville | e-process `alarm` checked every event; certificate absorbing (`promotion.py`). Hard cap stops the stream via query flags and uniforms, not outcomes. | OK for e-process arms. Comparator gates (fixed-N Hoeffding, empirical-Bernstein, McNemar) are fixed-horizon, so "power" comparisons mix anytime and fixed-N rules. Scout half-split is fixed at length/2 rather than data-adaptive. |
| Estimand mismatch | Certificate controls the shadow-period null, not future utility (`mathematical_problem.md` s.6) | Confirmed empirically: 62 of 1,018 temporal-confirmation promotions had nonpositive realised future net utility; 11 harmful of 3,570 in Markov confirmation (`docs/next_phase_plan.md` ~l.225, 231). `late_benefit` and reversal scenarios show gain after the shadow period is not learnable (`docs/closed_loop_intervention_results.md`). | Documented, but "harmful promotions = 0" in the fixed-split confirmation (below) is an in-distribution statement. |
| Subgroup versus population null | Decision-local / context-wise tests target a different null than aggregate benefit (`methods_and_assumptions.md:154-158`) | Mixed-sign calibration: local scaling crossed 2.5-5.8% when aggregate mean was exactly zero. Stratified gate is Bonferroni over fixed contexts with directly observable balanced contexts. | Estimand mismatch is documented. Context discovery and rare contexts untested. |
| Learner/evaluator separation | Separate learner and evaluator objects, with tests (`mathematical_problem.md` s.3) | `family` dict passed to selectors carries evaluator `h_truth`; only code-path review plus one metamorphic test guarantee noninterference (`SD/target_scout_information_flow_audit.md`; `tests/test_target_scout_fixed_split_calibration.py::test_oracle_truth_cannot_change_selection_or_certification`). Integrated pipeline has schema-level separation in event logs. | Partial mismatch with contract: no architectural separation in the Target-Scout path. |
| Controller ablation | Controller adds value over gates | `_controller_decision` only offers {CONTINUE, PROMOTE}, and PROMOTE is available only if already certified. Gross-gain forecast is on the same certification block, so it almost always exceeds the 0.05 switch cost. | Inference (not tested): the identical-outcome ablation (`SD/integrated_efficacy_confirmation_results_v1.md`) is probably structural, not an empirical finding about controllers. The controller is never asked to choose retrain/query/recalibrate/fallback in the integrated runs. |
| Q3 as certified action rule | Q3 seeks falsifiable algorithmic/theoretical improvement (`docs/research_charter.md`) | Only heuristics and baselines; no regret or safety theorem; `InterventionController` docstring disclaims guarantees. | Q3 method contribution not present. |

### 3. Experiments (registered Q2/Q3)

Frozen-before-run evidence is by protocol text plus protocol hash recorded in manifests. **Git cannot prove ordering:** protocols, runners, results and manifests for the whole `SD/` Q2 package were added in one commit `32c5cfd` (2026-10-27 02:43, "Record phase progress and verified comparators"). Older `docs/` protocols were committed earlier (e.g. `8745401` 2026-10-25 for the scout calibration/confirmation).

| Experiment | Protocol | Seeds | Data and comparators | Metric and headline | Artifact | Frozen? |
|---|---|---|---|---|---|---|
| Target-Scout vs fixed split dev (Q2) | `SD/target_scout_fixed_split_protocol.md` | 20,265,000-059 (60 seeds x 27 cells) | Synthetic; pooled rank, fixed split, scout | Expected post-promotion net gain; exploratory | `outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_dev_v1/` | Yes (hash in manifest); **seed overlap** with Markov null calibration 20,265,000-999 (`SD/target_scout_fixed_split_seed_overlap_correction.md`) |
| Exact-rule null calibration | `SD/target_scout_fixed_split_null_calibration_protocol.md` | 99,000,000-999 (1,000 x 9 cells, zero signal) | Same 3 methods | False promotion 5/27,000; max simultaneous exact upper 0.85%; 0 positive-net-gain promotions; caps held | `.../target_scout_fixed_split_null_calibration_v1/` (manifest `status: passed`; protocol sha `aa2b2671...`; runner sha `a470e637...`) | Yes |
| Q2 paired confirmation | `SD/target_scout_fixed_split_confirmation_protocol.md` (frozen conditionally on calibration pass; runner checks calibration hash) | 99,010,000-299 (300 x 18 positive-signal cells) | Same 3 methods, matched streams and query uniforms | Scout minus fixed split +8.7607 [7.2301, 10.3668]; minus pooled rank +6.6660 [5.2745, 8.0539]; margin +1; bootstrap seed 2026102699 | `.../target_scout_fixed_split_confirmation_v1/` (protocol sha `bcbcb73a...`; verifier passed, 16,200 rows) | Yes |
| Older Target-Scout line (about 15 stages: dev, replication, null, confirmation; eventwise, Markov, temporal, variance-query) | `docs/scout_*_protocol.md`; seed roots 20261130-20261200-20261300-20264000 (IID confirm), 20271000 (eventwise), 20910000 (Markov), 20920000 (temporal), 21440000 (variance query) | 600 per cell in confirmations | Pooled rank, nested-volume, min-bound scout | IID: +5.284 [4.301, 6.292] vs rank, +4.182 vs nested. Eventwise: +0.599. Markov: +10.567. Temporal: +4.727 | `docs/scout_*_results.md`, `outputs/` | Protocol-first per docs; first commits e.g. `8745401`, `4e69a83` |
| Validation-selected selector (negative) | `docs/validation_selected_context_policy_protocol.md` | 20,261,026-055; replication 20,261,100 | pooled rank, nested volume | -4.123 and -4.137 vs references; retired | `outputs/validation_selected_context_policy_30/` | Dev; 29/30 seeds overlap `docs/contextual_budgeted_promotion_grid_protocol.md` block 20,261,025-054 (stated at protocol l.3-6) |
| Repeated-candidate familywise null | `docs/repeated_candidate_null_calibration_protocol.md` | 2,000 streams | 6 betting monitors, 1/5/13 candidates | Max crossing 35/2,000 (1.75%) | `outputs/repeated_candidate_null_calibration_2000/` | Locked protocol |
| Closed-loop promote/rollback | `docs/closed_loop_intervention_protocol.md` | 2,000 seeds x 6 scenarios | continue, unconditional promote, promote-only, promote+rollback | no_benefit promotion 20/2,000; early reversal: rollback +3.07 vs promote-only but -81.50 vs continue | `outputs/closed_loop_intervention/` | Dev run |
| Intervention confirmation + calibration replication | `docs/intervention_confirmation_protocol.md` (seed offset 52,102,626); `docs/intervention_calibration_replication_protocol.md` | 2,000 and 10,000 | 4 policies | +5.51 [5.32, 5.69] over promote-only (macro over reversal profiles). 2,000-stream rollback null 35/2,000, upper bound 2.64% **missed** the 2.5% criterion; 10,000-stream replication max upper 1.64% | `outputs/intervention_confirmation/`, `outputs/intervention_calibration_replication/` | Yes; miss kept separate |
| Context-stratified gate | `docs/contextual_stratified_intervention_protocol.md` | 80102024 dev / 90102024 cal / 91102024 conf | global vs stratified gate | +30.53 vs global, +13.00 vs continue (balanced observable contexts) | `outputs/contextual_stratified_*` | Yes |
| Integrated null calibration | `SD/integrated_null_calibration_protocol_v1.md` | 1,000 per endpoint | continue etc. | 0/1,000 in each of 4 endpoints, upper 0.4372% (Q2/Q3 conditional on eligibility) | `outputs/shiftguard_unified/integrated_development/integrated_null_calibration_v1/` (re-run v2 passed after source change) | Yes |
| Integrated efficacy confirmation | `SD/integrated_efficacy_confirmation_protocol_v1.md` | 2026104000-099 (100 x 8 profiles x 9 methods) | continue, scheduled, two-gate, fixed-candidate, controller variants | Full vs continue +118.01 (boundary), +161.16 (monitor-onset), -143.76 (reversal), 0 elsewhere; vs two-gate -68.53, -40.10; vs fixed candidate -129.51, -82.32; controller identical | `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/` (7,200 rows, verifier passed) | Yes; 22 Holm-corrected tests |
| Fixed-candidate certification null | `SD/fixed_candidate_null_protocol_v1.md` | 1,000 | no-scout arm | 0/1,000, upper 0.2991% | `outputs/shiftguard_unified/integrated_development/fixed_candidate_null_calibration_v1/` | Yes |
| Comparator replays | `SD/mope_gated_calibration_protocol_v1.md`, `SD/opi_mope_matched_protocol_v1.md`, `SD/certification_exponent_one_step_protocol_v1.md`, `SD/anyrank_adaptation_protocol_v{1,2}.md` | various | MOPE, OPI, Kelly one-step, AnyRank | MOPE null 6/1,000, power 991/1,000 vs 717 Hoeffding; Kelly 270/300 vs MOPE 279/300 (McNemar p=0.0636); AnyRank 0 promotions, inconclusive | `outputs/shiftguard_unified/sota_reproductions/*` | Yes; AnyRank v2 reused v1 seeds |
| Real-data Q2 (dev) | `SD/wilds_candidate_selection_protocol.md`, `SD/wilds_pace_gate_protocol_v1.md`, `SD/upworthy_policy_selection_protocol_v1.md` | splits | WILDS CivilComments, Gas Sensor, Upworthy | WILDS gain +0.01250 / +0.05038 / +0.00467; PACE did not cross (log E -10.97) while fixed-N McNemar promoted (p=0.020); Upworthy +0.1002 pp CTR [0.0850, 0.1170] on 3,808 tests | `outputs/shiftguard_unified/real_data_development/*`, `.../independent_real_data/` | WILDS test exposed; Upworthy protocol pinned before holdout acquisition |
| Real-data Q3 (EIA) | `SD/eia_retraining_protocol.md`, `SD/eia_2026_out_of_time_confirmation_protocol_v1.md`, `SD/upf_eia_development_protocol_v2.md`, `SD/rccda_eia_development_protocol_v2.md`, `SD/cara_eia_development_protocol_v1.md`, `SD/eia_adwin_ddm_development_protocol_v1.md` | chronological | frozen, weekly, monthly, error-trigger, UPF, RCCDA, CARA, ADWIN, DDM | 2026 replay: all adaptive policies below frozen RMSE (CISO 2235.80 vs ~1650-1705; ERCO 2013.63 vs ~2005); CARA best beat prior best in 16/40 cells, lost 19; ADWIN/DDM best won 3/40, lost 31 | `outputs/shiftguard_unified/independent_real_data/eia_2026_v1/`, `.../real_data_development/*` | 2026 replay frozen; others development |
| Paper 2/3 conformal and cost baselines | `papers/paper2_adaptive_conformal/experimental_protocol.md`, `docs/initial_results.md` | seeds 11,22,33 | split vs rolling conformal, frozen, periodic, triggered | Coverage 0.4937 frozen, 0.8871 rolling, 0.8424 triggered; exploratory 3 seeds | `docs/initial_results.md` | Exploratory |

### 4. Findings

**Positive (all conditional on registered synthetic DGP, IID or registered schedules, immediate labels, non-performative actions):**
- Target-Scout beats fixed split and pooled rank by more than the +1 margin after a passed null calibration (above). Older line replicates with other generators.
- Two-gate promote+rollback is calibrated and beats promote-only on average over reversal profiles (+5.51), with the 2,000-stream calibration miss recorded and then resolved by a 10,000-stream replication.
- Context-stratified gate beats a global gate in a designed heterogeneous reversal.
- Integrated null calibration: 0/1,000 errors at each endpoint.

**Inconclusive:**
- AnyRank pilot (0 promotions for all methods); Hillstrom, CRSP and Criteo as candidate-selection evidence (exposed splits, imposed costs); WILDS (exposed test, imposed costs); Upworthy (CTR only, project-relative holdout); EIA (predictive RMSE and update counts only, release times unknown).
- Certification-exponent Kelly versus MOPE: no rate difference detected.

**Negative:**
- Integrated pipeline: no general advantage. Fixed-candidate certification (+247.51 / +243.48) beats scout-based full pipeline (+118.01 / +161.16) in the aligned profiles. Q1 misses post-window onset (0% trigger). Rollback leaves negative utility under reversal (-143.76). Controller adds nothing.
- Validation-selected selector, PVA/context-volume variants, decision-local bound (power concentrated in estimand-mismatch regimes) and several acquisition tunings were retired.
- Budget frontier: 0/60 harm detections for every acquisition rule (`docs/budget_frontier_results.md`).
- Strongest simple finding: promotion rates are low. In the fixed-split confirmation Target-Scout promoted 296/5,400 (5.5%), fixed split 48, pooled rank 101 (`.../target_scout_fixed_split_confirmation_v1/method_summary.csv`). The +8.76 mean gain is an average dominated by non-promoted zeros, and the gain per promoted stream is not reported in the headline.

### 5. Reproduction, seeds, leakage

- **Hash records.** Manifests record protocol, runner and source sha256, CUDA environment and artifact hashes. Verifiers: `scripts/verify_target_scout_fixed_split_calibration.py`, `scripts/verify_target_scout_fixed_split_confirmation.py`, `scripts/verify_integrated_pipeline_calibration.py`, `scripts/analyze_integrated_efficacy_confirmation.py`.
- **Source drift (verified).** `src/shiftlab/dive/budgeted_promotion.py` is now `681a4e13...`, whereas all fixed-split manifests and `SD/target_scout_information_flow_audit.md` record `8eada2f9...` (commit `16313bb`). The change landed in `32c5cfd`: additive logging (`certification_log_e_path`, `promotion_event`) inside `_monitor_scout_context_policy`. No equivalence re-run is recorded. `SD/evidence_inventory.md` still labels `8eada2f9...` as "Current HEAD source SHA-256".
- `scripts/calibrate_target_scout_fixed_split.py` also differs from its manifest hash (`a470e637...` in manifest, working-tree LF-normalised `11303043...`); the execution-start copy is archived as `outputs/shiftguard_unified/sota_reproductions/target_scout_fixed_split_null_calibration_v1_runner_at_execution_start.py` (hash matches the manifest). The raw working-tree copy has CRLF line endings (`30162c22...`), so use that archived copy for reproduction.
- **Seed separation.** Fixed-split calibration 99,000,000-999, confirmation 99,010,000-299, with a pre-freeze repo-wide scan claimed in the protocol. Known overlaps: dev v1 vs Markov-null block at 20,265,000, and validation-selected vs contextual grid (29/30). I did not run a full overlap check across all ~30 scout blocks. I only compared the roots listed in section 3.
- **Not in Git.** `outputs/**/streams.*` and per-stream files are `.gitignore`d (`git check-ignore` confirms for the confirmation dir). Only manifest and verification JSON are tracked, so a clone cannot recompute the paired contrasts without regenerating on CUDA.
- **Leakage risks.** (i) Evaluator `h_truth` lives in the shared `family` dict (audited, not structurally removed). (ii) Fixed-split and pooled-rank baselines select on source-validation data that precede the target change, so the DGP is designed to mis-aim them; the comparison measures that handicap. (iii) Real-data test splits for WILDS, Hillstrom and CRSP are exposed. (iv) Threshold and design selection on development seeds (e.g. q=0.80, 40% cap) before confirmation is documented, not hidden.

### 6. Unsupported claims, missing comparisons, open questions

- **Unsupported:** unified-system superiority; real-world benefit; "statistically justified evidence-to-costed-intervention" as novelty (`SD/decision_gate_report_2026-10-26.md` novelty update citing Digalakis et al. and Löfström); guaranteed future utility after promotion; any claim that Q3 allocates labels/compute/interventions optimally; anything about performative actions.
- **Missing comparators:** a fixed-N sample-split test with target-only selection and exact McNemar/t gate at matched labels (WILDS showed fixed-N promoted where PACE did not, so the e-process may be conservative); Digalakis switching framework, Löfström conformal repair/refit, Regol cost-aware retraining (cited as covering the space, not implemented as comparators; `SD/novelty_audit.md`); CPC/CPS/CABAI/HCPI deemed inapplicable on common-label tasks (`SD/comparator_applicability_audit_v1.md`); OPE-based Q2 on performative data.
- **Open:** (1) Is Target-Scout's gain mostly from selection or from the weak baseline? (2) Mixed-null and adaptive-query calibration for Target-Scout. (3) Per-promoted-stream gain and promotion-rate reporting. (4) A Q3 controller that actually chooses among retrain/query/recalibrate with a certified rule, plus a vacuity check on the ablation. (5) Re-run equivalence check after the 32c5cfd source change.

### 7. Conflicts between older and newer docs/code/results

| Older | Newer | Conflict |
|---|---|---|
| `SD/evidence_inventory.md` l.23 and l.71 (budgeted_promotion hash `8eada2f9...` as "current") | working tree `src/shiftlab/dive/budgeted_promotion.py` = `681a4e13...`; `git log` shows change in `32c5cfd` | Stale hash. |
| `SD/decision_gate_report_2026-10-26.md` and `SD/evidence_inventory.md`: HEAD `525c79e3...`, 1,566 passing tests, "uncommitted" worktree | `docs/research_refinement_v1/REPOSITORY_STATE_AUDIT.md` l.58: 1,869 passed, 1 skipped at `c0f84af`; current HEAD `caff0ed`, tree clean | Test count and snapshot differ; commit 525c79e exists in local history (verified with git cat-file), so those docs describe an earlier snapshot. |
| `docs/research_charter.md` and `docs/next_phase_plan.md` ("Phase D: connect monitoring to intervention", Q3 development) | `SD/decision_gate_report_2026-10-26.md`, `SD/claims_and_limitations.md`: NO-GO on RIVE/ASC and new algorithm; scope = retrospective benchmark/failure analysis | Direction changed; older plan text still lists next milestones. |
| `docs/validation_selected_context_policy_protocol.md` l.72 "fresh seed root 20261026" | same file l.3-6 admits 29/30 seed overlap | Internal contradiction, correction acknowledged in the header only. |
| `SD/target_scout_fixed_split_protocol.md` ("not seed-disjoint" claims in early notes) | `SD/target_scout_fixed_split_seed_overlap_correction.md` | Correction appended; original protocol text unchanged. |
| `docs/methods_and_assumptions.md:126` ("Model-version persistence and operational rollback are not implemented") | `controller.py::CertifiedPromotionRollback`, `closed_loop_intervention.py` | Stale sentence; rollback exists in simulation form (no real operational rollback). |
| `docs/intervention_confirmation_results.md` (2.64% upper bound exceeded the 2.5% criterion) | `SD/evidence_inventory.md` l.26 / l.53 summary ("calibrated synthetic behavior", `no_benefit` 20/2,000) | Summary omits the 2,000-stream miss; replication (1.64%) resolves it. |
| `papers/paper2_adaptive_conformal/README.md`, `papers/paper3_cost_aware_adaptation/README.md` (conformal and cost baselines are the Paper 2/3 content) | `SD/` (Target-Scout, closed-loop; not under paper2/paper3 directories) | Certification and intervention evidence lives in `SD/` and `docs/`, not in the paper folders; paper2/3 research logs do not mention Target-Scout. |

# Part III. Datasets and evaluation substrates (subagent survey, not lead-verified except as listed in Section 3)

## A2: Datasets and evaluation substrates (read-only inventory)

Scope read: AGENTS.md, docs/, papers/*, data/reports/, outputs summaries, src/shiftlab/data, scripts. No raw/licensed file was opened; no experiment or test was run. A seed-range scan of docs/papers text (scratchpad `seeds.py`) was used for the overlap check. "Not found" = could not locate.

### 1. Datasets

| Dataset | Loader / builder | Licence / access | Provenance / checksum | Splits | Label availability | Used by |
|---|---|---|---|---|---|---|
| Synthetic suite (46 versions) | `src/shiftlab/data/synthetic/generators.py`, `scripts/generate_synthetic.py`, `src/shiftlab/synthetic.py` (45 lines), `src/shiftlab/decision_harm_experiment.py` (774 lines), `src/shiftlab/dive/*` (hard_budget etc.) | Own code | `dataset_manifest.json` per version with per-file SHA-256 (`src/shiftlab/data/validation.py:validate_dataset`); evaluator-only `evaluator_only/dgp.json` (`storage.py` L149) | Known change times; `assign_splits` time-boundary (`chronological_splits.py`) | Explicit delay / MCAR missingness / feedback_change (`docs/synthetic_catalogue.md`) | All Paper 1 confirmatory work; `docs/dgp.md`, `docs/synthetic_oracle_spec.md` |
| CRSP CIZ 2000-2025 | No `src/` loader (grep "crsp" in src: none). `scripts/extract_crsp_ciz_wrds_cloud.py` then `scripts/build_crsp_study_panel.py` | Licensed WRDS; raw excluded from Git; Columbia confirmed private-repo use (`docs/cross_device_data_access.md`) | 26 annual manifests, 147 part SHA-256, 32,803,597 raw rows; panel `5211412140dcb86f08f9`, 32,774,131 rows (`data/reports/crsp_study_panel_validation.json`); release archive digests in `docs/cross_device_data_access.md` | Prediction-year: train 2000-14, val 2015-17, cal 2018-19, test 2020-25; rows whose target date crosses a split are `unassigned` (`build_crsp_study_panel.py` L213-295) | `feature_available_time`=event, `prediction_time`=event+1, `label_available_time`=target-date close (L330-333): a retrospective convention, no publication lag (`docs/crsp_study_execution.md`) | Smoke (`crsp_study_smoke.json`), policy pilot, monitor comparison, e-process replay, exchange replay |
| EIA EBA bulk (CISO, ERCO) | `src/shiftlab/data/real/eia.py:_acquire_bulk` | US gov public domain (`catalogue.py`) | SHA-256 `3a6143c4...936f`, 697,661,852 B, retrieved 2026-10-20 (`data/reports/eia_2026_holdout_readiness.json`) | Train 2019-24, cal 2025, test 2026-01-01..10-19 (`papers/shiftguard_unified/eia_2026_out_of_time_confirmation_results.md`) | Event time only; 0/24/168 h delay is an assumed sensitivity | EIA 2026 replay; WP4 validity (`docs/eia_real_data_validity_*.md`); retraining frontier |
| Upworthy Research Archive | `scripts/acquire_upworthy_holdout.py`, `src/shiftlab/dive/upworthy_policy_selection.py:filter_eligible_tests`/`tune_and_fit` | CC BY 4.0 | Exploratory SHA `8368313b...`; holdout `93832660...` (`data/reports/upworthy_holdout_acquisition_manifest.json`) with protocol/runner/impl hashes | Official exploratory (train), holdout (eval); confirmatory (22,743 tests) unopened | None: package-level aggregates, no timing or feedback stream | Q2 headline selection only |
| Criteo Attribution | `src/shiftlab/data/real/criteo_attribution.py:acquire` | CC BY-NC-SA 4.0 | Pinned HF snapshot, receipts under `data/raw/criteo_attribution/` | Relative-second clock | 30-day window assumed (`impression+30d`), only 3.31% mature in-stream | Maturity audit, then marked unsuitable (`real_data_inventory.md`) |
| CriteoPrivateAds | `scripts/acquire_criteo_private_ad.py`, no processed copy | CC BY-SA 4.0 (card) | Pinned rev `3436458...`, 288 files hashed (`data/reports/criteo_privatead_snapshot_audit.json`) | Publisher days 1-25/26-30 | 2-day block maturity is a research convention | One-seed cost-sensitive click development |
| Criteo sponsored-search (`criteo`) | `real/criteo.py` | CC BY-NC-SA | **Zero acquired versions** | n/a | n/a | None |
| Gas Sensor, WILDS, Folktables, OPSD, NOAA, Monash, Binance, FRED | `src/shiftlab/data/real/{wilds,folktables,opsd,...}.py` | Per `catalogue.py` | Per-version manifest SHA-256; `scripts/audit_raw_provenance.py` | Batch/official/domain partitions | Coarse or unknown | Offline candidate-selection (`gas_sensor_candidate_protocol.md`, `wilds_candidate_selection_protocol.md`), exploratory only |
| Hillstrom, Open Bandit, ELEC2, Criteo uplift/BLBF, CUVET | `scripts/evaluate_hillstrom_policy_development.py`, `prepare_open_bandit_full.py`, `audit_elec2_candidate.py`, etc. | Mixed; Hillstrom no explicit licence | Local SHA-256 (Hillstrom `0e589...`; Uplift stream `2716e1bf...`) | Mostly exposed or unsplit | Not sequential | Component audits in `papers/shiftguard_unified/real_data_inventory.md` |

Registry gap: neither CRSP nor Upworthy appears in `src/shiftlab/data/catalogue.py` SOURCES; CRSP is also absent from `dataset_manifest.json`/`data_inventory.csv` and `dataset_paper_suitability.md` (`real_data_inventory.md` states this explicitly). Two CRSP pointers exist (`data/manifests/crsp_ciz_next_day-404c...`, `...-5211...`); replays use `5211...`.

### 2. Assumptions: intended vs implemented

| Item | Intended (AGENTS.md / charter) | Implemented | Status |
|---|---|---|---|
| CRSP change dates | Not causal labels | Docs say no known causal changepoints (`crsp_study_execution.md`). Monitor comparison builds evaluator-only "next-20-date positive mean paired cost" labels from the same test path (`docs/crsp_monitor_comparison_results.md`) | Labelled hindsight/descriptive. This is not a causal change label, but AUROC against data-derived windows can be misread. Overlapping labels (prevalence 0.414; 628 of 1,487 in e-process replay, 2,318 pooled in exchange replay: different definitions) |
| CRSP utility | Not inferred from data | Imposed: returns clipped to +/-10%, long/flat, 0/5/10/25 bps turnover (`crsp_decision_policy_replay_protocol.md`) | Disclosed as imposed. The 5-bps primary is a choice, not sourced |
| CRSP point-in-time | Not verified | `prediction_time=event+1`, `label_available_time=target close`; same-date `vwretd` reference | Disclosed. Not replay evidence |
| EIA utility | Not inferred | Shortfall 5 / idle reserve 1 imposed; `tau` = 90th percentile of 2019-24 demand (`eia_real_data_validity_protocol.md`) | Disclosed. WP4 pairing assumes procurement does not alter demand (full-information assumption) |
| EIA label delay | Explicit | 0/24/168 h assumed; publisher release times unknown | Disclosed |
| Upworthy utility | CTR only | CTR only, no revenue (`upworthy_real_data_eligibility_audit.md`) | Matches |
| Upworthy causal reading | Needs randomisation | Excludes 2013-06-24..2014-01-11 (date proxy for suspected assignment problem; no `Problem` flag in 2020 CSV) | Proxy rule, flagged |
| Synthetic oracle visibility | Evaluator-only | `dgp.json` under `evaluator_only/`; `tests/data/test_oracle_spec.py` checks formulas. `docs/synthetic_oracle_spec.md` says all oracle columns stay in evaluator-only Parquet | No test found that asserts monitors cannot read oracle columns (see Sec 5) |
| Shift times | Known only in synthetic | `true_change_time` in oracle frame (`decision_harm_experiment.py` L157) | Evaluator-side. OK |

No code or doc found that infers causal shift times from CRSP alarms or sets costs from data. The nearest risks are the hindsight labels above and the 5-bps/clip choices.

### 3. Experiments on these substrates

| Experiment | Protocol | Seed / RNG | Comparators | Metrics | Headline | Artifact | Class |
|---|---|---|---|---|---|---|---|
| CRSP smoke | `docs/crsp_study_execution.md` | 20261022 | Train-mean vs Ridge, split conformal | RMSE, coverage | RMSE 0.041351 vs 0.041419; coverage 86.3% | `data/reports/crsp_study_smoke.json` | Smoke. Cohort chosen from PERMNOs present in all four splits (survivor selection) |
| CRSP policy pilot (100 PERMNOs) | `docs/crsp_decision_policy_replay_protocol.md` (frozen) | 20261025 | Ridge long/flat vs `vwretd>0` | Paired cost, 20-date block bootstrap | 5 bps: -0.000558 [-0.000912,-0.000202]; RMSE 0.039943 vs 0.039786 (no predictive gain); only 30/100 names in test | `outputs/crsp_policy_replay_pilot_100/`; `outputs/shiftguard_unified/real_data_development/crsp_decision_policy_pilot_100_v1/` | Descriptive/exploratory. Test 2020-25 already exposed |
| CRSP full monitor comparison | `docs/crsp_monitor_comparison_protocol.md` | 20261025 | Paired-cost CUSUM, bounded e-process, loss CUSUM, MMD | AUROC/AP vs next-20-date label | 7.62M events; cost -0.0003357 [-0.000655,-0.0000415]; AUROCs 0.422 / 0.413 / 0.505 / 0.551; e-process never crossed | `outputs/crsp_monitor_comparison_full/` | Descriptive; negative for decision-harm monitors |
| CRSP e-process replay / exchange replay | `crsp_eprocess_candidate_replay_protocol.md`, `crsp_exchange_stratified_replay_protocol.md` | none (deterministic) | 4 bounded-mean processes; fixed vs 8-start mixture per exchange | Max log-e, AUROC | No crossing; AUROC 0.41-0.49; exchange mixture 0.504/0.508 | `outputs/crsp_eprocess_candidate_replay/`, `outputs/crsp_exchange_stratified_replay/` | Descriptive; negative |
| EIA 2026 out-of-time | `eia_2026_out_of_time_confirmation_protocol_v1.md` | none stated | Frozen / weekly / monthly / error-trigger Ridge x 3 delays | RMSE, MAE, updates, 168-h block intervals (42 blocks) | CISO frozen 2235.8 vs weekly 1651-1672; ERCO 2013.6 vs 2004-2005 | `outputs/shiftguard_unified/independent_real_data/eia_2026_v1/` | Frozen retrospective; independent CUDA re-run reproduced 24 rows (`scripts/verify_eia_2026_reproducibility.py`) |
| EIA WP4 validity | `docs/eia_real_data_validity_protocol.md`, freeze `docs/eia_real_data_validity_freeze.json` (2026-10-27T20:58:55Z) | Blocks `59200000-03`, `59210000-32`, `59220000-03` (protocol L189) | WP1 monitor panel | Random-orientation null alarm rate | 68/68 cells, 0/1,000 alarms at eps 0.1; eps 0 up to 28/1,000, bound 0.038 | `docs/eia_real_data_validity_results.md` | Null control (registered pass) plus descriptive injected harm; only CISO-2026 informative (150 disagreements) |
| Upworthy Q2 | `papers/shiftguard_unified/upworthy_policy_selection_protocol_v1.md` | bootstrap 20261026, 10,000 reps, 90 week clusters | Text TF-IDF logistic vs uniform | Equal-test CTR delta | +0.001002 [0.000850, 0.001170]; 3,808 tests | `outputs/shiftguard_unified/real_data_development/upworthy_policy_v1/` (+ `independent_verification.json`) | Frozen single-shot evaluation, reproduced by `verify_upworthy_policy.py` |
| Synthetic WP1 gated monitor (S0-S3) | `docs/gated_vs_ungated_monitor_comparison_protocol.md` | Fidelity 20373024-83; S2 58500000-501999 per cell; S3 58400000-99; smoke 58600000-04 | Gated HT vs correctly bounded uniform, DISCERN-style, Xu, SR/CUSUM | Growth ratio, detection | S2 pass (all <5%); S3 growth ratio 7.20 [6.88,7.55], 100 wins/0 losses | `outputs/gated_monitor_*`; `docs/gated_monitor_comparison_results.md` | Confirmatory-style on synthetic after a numerical-tolerance amendment (two earlier launches crashed, `outputs/gated_monitor_compare_aborted_*`, `..._crashed_*`) |
| Synthetic WP2/WP3/ADG screens | `stratified_growth_prescreen_results.md`, `data_efficient_edetector_prescreen_results.md`, `adg_growth_prescreen_results.md` | 58700000-19, 59000000-19, 58000000-19 | Strongest incumbents | Analytic / 20-seed prescreen | All failed gates; stopped | `docs/phase_report_stratified_monitor.md` | Negative; checkpoint B NO-GO |
| Delayed-PPI calibration/confirmation chains | e.g. `delayed_evidence_directed_ppi_*_protocol.md` | 20280000-999 (cal), 20282000-999 (conf), many others | Uniform PPI, fixed mixture | Null alarm bound, paired detection | Several gates PASS (`delayed_evidence_directed_ppi_confirmation_results.md`); FAIL: `delayed_ppi_adaptive_informative_delay_results.md` (5/250 escalations), `delayed_ppi_fixed12_dose_onset_grid_results.md` (-0.17 pp macro), `predictable_stake_portfolio_results.md` (stopped at calibration) | `outputs/delayed_*` | Mix of calibration, confirmation and failed gates, all synthetic |
| Phase-2 decision-harm benchmark | `configs/experiments/decision_harm_phase2.yaml` | offset 20261022, 30 seeds, 60 calibration seeds | Six scenarios | Alarm rates | not summarised here | `data/reports/decision_harm_phase2/` | Not read |

### 4. Findings

- **Positive (narrow):** synthetic null calibrations repeatedly stay under 5% (gated S2 largest bound 1.953%, `gated_monitor_null_calibration_results.md`); WP1 S3 gating gain (7.20x). EIA adaptive refits beat frozen Ridge in both authorities in 2026. Upworthy selector +0.10 CTR pp over uniform.
- **Inconclusive:** WP4 EIA validity: three of four paths have 1-7 disagreements, so the pass carries little information (`eia_real_data_validity_results.md`). Hillstrom neural T-learner minus random: -$0.0258 [-0.165, 0.114] (`real_data_inventory.md`). CRSP policy pilot lower imposed cost with no RMSE gain: only 30 names, descriptive.
- **Negative:** CRSP decision-cost monitors never alarmed and ranked hindsight windows below chance (AUROC 0.41-0.42); predictive-loss CUSUM alarmed 96.4% of dates without decision harm (consistent with the shift/degradation/harm separation). Uniform-start mixture gain did not transfer to CRSP. WP2/WP3/ADG prescreens failed. Criteo Attribution unsuitable for in-stream delayed monitoring (3.31% matured).

### 5. Reproduction

**Hash verification:** raw/processed SHA-256 verified for CRSP (147 parts), EIA, Upworthy, Criteo PrivateAds (288 files), per the audits above; `validate_dataset` recomputes manifest file hashes. In `live_data_inventory_stratified_phase.md`, 273 of 332 local payloads were not rehashed (size only). I did not re-hash anything.

**Seed blocks (from doc scan; 82 distinct ranges):** 20261025-54 and 20261026-55 (validation-selected context policy); 20261300-20262299 (scout null) and 20262000-29 (start-prior sweep); 20264000-599; 20265000-999 (Markov null) and 20265000-59 (fixed-split dev); 20271000-599; 20272000-29 (PPI calibration); 20273000-59; 20274000-20275999 (start-prior null); 20275000-999 (temporal null); 20276000-7999; 20280000-999; 20282000-999; 20290000-499 / 20291000 (robust-mix dev) and 20290000-999 / 20292000-999 (Markov PPI); 20310000-05 and 20310000-59; 20320000-59; 20321000-499; 20322000-299; 20373000-199 and 20373024-83; 20374000-20375999; 20410000-249; 20420000-20421999; 20440000-199; 20450000-99; 20910000-599; 20920000-599; 21210000-999; 27104027-27112026; 27504027, 27604027; 31302026-85; 31303026-85; 54000000-29 and 54000000-499; 58000000-19; 58100000-59 / 58200000-20 / 58300000-999 (anchored draft); 58400000-99; 58500000-501999; 58600000-04; 58700000-19; 58800000-59; 58900000-901999; 59000000-19; 59100000-999 (reserved); 59200000-3, 59210000-32, 59220000-3; 99010000-299; 2026102700-09. Real-data integers: 20261022 (CRSP smoke), 20261025 (CRSP pilot and monitor), 20261026 (Upworthy).

**Overlaps found (text scan; whether DGPs differ was checked only where noted):**
1. 20265000-59 (fixed-split dev) inside 20265000-999 (Markov null). Already disclosed and annotated (`papers/shiftguard_unified/target_scout_fixed_split_seed_overlap_correction.md`, `scripts/annotate_target_scout_seed_overlap.py`).
2. **54000000-29 (`harm_power_grid_protocol.md`) inside 54000000-499 (`policy_bound_null_calibration_protocol.md`).** The grid protocol says its block is "disjoint from the calibration, confirmation, and smoke blocks". The calibration protocol's text puts the same start. Not annotated anywhere I found. Different scenario generators not verified.
3. **20274000-20275999 (start_prior_validation null) contains 20275000-999 (scout_context_policy_eventwise_temporal_null)** and 20274000-59 (temporal development). Different DGPs, but both are nulls on the same integers; no correction found.
4. 20290000-499 (robust-mix development alternative offset) inside 20290000-999 (Markov PPI null calibration). No correction found.
5. 20261300-20262299 (scout null) inside 20262000-29 (start-prior development sweep). Minor; not annotated.
6. 20272000-01 within 20272000-29; 20310000-05 within 20310000-59 (nested/identical reuse across protocol families).
7. 20373024-83 within 20373000-199: intentional historic fidelity reproduction (`agent_goal_stratified_monitor_phase.md` Sec 7), listed as historic.
8. 2026102700-01 within 2026102700-09 (integrated pipeline reports).
No central machine-checked seed registry found; the only one is a prose table (`agent_goal_stratified_monitor_phase.md` Sec 7) and per-runner "disjoint seed" checks in `src/shiftlab/dive/*` (e.g. `allocation_grid.py`), which cover declared pairs only. The anchored-monitor draft once collided with an existing 57M block and was moved (`anchored_gated_harm_monitor_development_protocol.md` L287); good practice, manual.

**Leakage and reuse:**
- Oracle truth: stored evaluator-only; I found no test that fails if a monitor reads oracle columns. `tests/data/test_oracle_spec.py` checks formula correctness only.
- Train-only preprocessing: enforced for CRSP in panel builder invariants (`build_crsp_study_panel.py` L396-447) and `fit_training_scaler`; the smoke cohort rule uses presence in all splits.
- CRSP test window 2020-2025 reused by smoke, pilot, monitor, e-process, exchange replay, and (per inventory) is "not a clean-room holdout". Prior outputs from failed or adjusted runs are retained: `outputs/crsp_monitor_comparison_full_attempt_before_cohort_label_fix`, `..._before_source_typecheck`, `..._cleanup_attempt`, `..._pre_cleanup`. Why they were re-run (cohort label fix) is not documented in the results doc I read (grep found nothing).
- WILDS v1 interleaved test scoring with selection; superseded by v2 (`decision_log.md` L18).
- EIA 2026 was scored once in the "confirmation" replay and then reused as a WP4 "development" path.
- Upworthy: exploratory/holdout experiment IDs disjoint (0 overlap in `summary.json`). I found no check for headline text reuse across tests. Selected C=0.01 is at the grid edge.

### 6. Unsupported claims, missing comparisons, open questions

- "Two real-data task families, meaningfully frozen" (`real_data_confirmation_gate_audit.md`) rests on EIA (not independent, release time unknown, utility unknown) and Upworthy (holdout public since 2021). The audit itself calls them component checks.
- CRSP policy pilot sign (-0.000558) coexists with no predictive gain and 30/100 names, so a "decision-aware advantage" is not supported; the doc says so.
- No real-data false-alarm validity claim exists for CRSP (conditional-mean null, filtration, dependence unestablished). Documents state this.
- WP4 EIA validity uses a random-orientation null, which is not a real harm-null; zero alarms at eps 0.1 on 3 of 4 paths is near-vacuous.
- Missing: dependence-aware / PERMNO-cluster uncertainty for the pilot; a pre-registered CRSP monitor comparison with independent calibration; Upworthy against a non-uniform baseline such as the publisher `winner` (evaluator-only comparator is described but not reported in what I read); no CRSP row in the suitability matrix.
- Paper 3 budget allocation and Paper 2 evaluation of a frozen candidate: no real-data substrate with delayed labels (Criteo Attribution only 3.31% matured; PrivateAds is a convention).
- Open: which Phase-2 decision-harm benchmark numbers (`data/reports/decision_harm_phase2/`) are headline; not read.

### 7. Conflicts between older docs and newer code/results

- `docs/implementation_status.md` ("novel methods intentionally not started", 3-seed runs, dependence deferred) is superseded by dozens of later protocols and `papers/paper1_decision_drift/research_log.md`; it has no date or supersession note.
- `docs/crsp_study_execution.md` says Paper 1 CRSP alarms are "descriptive only", and later replays comply, but its smoke numbers (133,505 test rows, RMSE 0.041351) differ from the pilot (40,557 rows, 0.039786); different cohorts, easy to conflate.
- `data/reports/dataset_paper_suitability.md` and `src/shiftlab/data/catalogue.py` omit CRSP; `real_data_inventory.md` and `docs/crsp_*` treat it as available.
- EIA 2026: labelled "final-period / frozen confirmation" in `real_data_confirmation_gate_audit.md` and "previously examined development windows" in `eia_real_data_validity_results.md`; `live_data_inventory_stratified_phase.md` says the snapshot "remains development data".
- Upworthy output path is `real_data_development/upworthy_policy_v1`, yet the result is treated as a final evaluation in the gate audit.
- Seed text "disjoint from all prior experiments" (fixed-split dev protocol) was wrong (item 1 above); `harm_power_grid_protocol.md` disjointness claim conflicts with `policy_bound_null_calibration_protocol.md` (item 2).
- Criteo licence: catalogue/audit say CC BY-NC-SA 4.0 for Attribution and PrivateAds as CC BY-SA 4.0; `real_data_inventory.md` flags the uplift/datasheet licence conflict and applies the stricter terms.
- AGENTS.md describes Papers 1-3 as separate contributions; `papers/shiftguard_unified/` builds a single integrated "ShiftGuard" evidence track (not independently checked here).

# Part IV. ShiftGuard integrated benchmark and claim layer (subagent survey, not lead-verified except as listed in Section 3)

## A2: ShiftGuard integrated benchmark, decision gates, manuscript, claim layer

Repo root: `C:\Users\nigel\OneDrive\桌面\ICML\shift-research-starter`. Read-only audit. All paths below are relative to the root. Git dates are from `git log`; nearly all `papers/shiftguard_unified/*` files first enter history in commit `32c5cfd` (2026-10-27 02:43), even though their text is dated 2026-10-26, so file dates in headers are not commit dates. Branch is `research/phase-progress-2026-10-27`. The decision gate report names HEAD `525c79e` (a pre-`32c5cfd` commit), so it describes a worktree snapshot, not a release.

### 1. ShiftGuard integrated benchmark

**What it is.** A synthetic, evaluator-oracle benchmark that chains Q1 (monitor incumbent harm), Q2 (Target-Scout candidate selection and certification) and rollback on a 3,200-event stream: fit to 800, monitor to 1,600, scout/certify to 2,400, deploy to 3,200. Hard label cap 640 (monitor 320, scout/cert 320, rollback 160). Query rates 0.40 in the monitor stage and 0.20 later. Switch and rollback cost 0.05. Alphas .02/.015/.015. Source: `src/shiftlab/dive/integrated_pipeline.py` (constants at lines ~35-55, verified); design in `papers/shiftguard_unified/integrated_benchmark_protocol.md`, which itself says it is a "design draft", not the frozen efficacy protocol. Tests: `tests/test_integrated_pipeline.py`. Analysis: `scripts/analyze_integrated_efficacy_confirmation.py`. Figure source: `papers/shiftguard_unified/figures/` (`integrated_efficacy_forest.png`/`.pdf`, `render_integrated_efficacy_plot.py`). I did not inspect the PNG against the CSV.

**Arms (9).** `continue`, `scheduled_promote`, `two_gate`, `two_gate_controller`, `q1_fallback`, `full_pipeline`, `full_pipeline_controller`, `fixed_candidate_certification`, `full_pipeline_fixed_certification` (`integrated_efficacy_confirmation_protocol_v1.md`). Per `integrated_pipeline.py` ~line 877, `q1_fallback` = switch to the reference policy after the first Q1 alarm, no promotion.

**Profiles (8).** stationary, benign_nuisance, boundary_local_harm, post_promotion_reversal, recurring_regimes, residual_variance, harmful_adaptation_at_monitor, harmful_adaptation_native (same protocol file).

**Comparators in the integrated test are internal ablations only.** There are no external published methods inside the integrated pipeline. Published comparators (Timans, Comparecast, PPE, MOPE and others) are tested in separate component studies (see section 3).

**Metrics.** Primary: evaluator-expected cumulative paired-cost reduction net of switching/rollback charges (`expected_incremental_utility`). Secondary: realized utility, rates, labels. Inference unit is the stream seed. 22 one-sided paired t-tests (6 full-vs-continue, 8 full-vs-two_gate, 8 full-vs-fixed-certification), Holm-adjusted, simultaneous Bonferroni lower bounds. The protocol also requires a "system-level claim" to show no materially negative full-vs-`continue` contrast in stationary/benign, but those two contrasts are not in the 22.

**Confirmation result** (`papers/shiftguard_unified/integrated_efficacy_confirmation_results_v1.md`; I re-checked it against `outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1/analysis_v3/primary_contrasts.csv` and `integrated_pipeline_summary.csv`; numbers match; `verification.json` status "passed").
- Design: seeds 2026104000-099, 100 per profile, 7,200 seed-method rows, 23,040,000 rows in each of the learner and evaluator event logs, max labels exactly 640, CUDA.
- Full vs continue: boundary-local harm +118.006 (Holm p 2.09e-11); harm-begins-at-monitor +161.161 (p 3.15e-19); post-promotion reversal -143.758; recurring, residual-variance and native-late-onset are exactly 0.
- Full vs two_gate: negative in boundary (-68.53), monitor-aligned (-40.10), residual variance (-8.92) and native (-201.26); positive only under reversal (+37.26, Holm p 0.00248).
- Full vs full_pipeline_fixed_certification: negative in boundary (-129.51) and monitor-aligned (-82.32); positive only under reversal (+73.23, p 3.3e-6). Both of those reversal wins are over arms that are themselves negative against `continue`.
- Q1 triggers in 92-93% of streams when its window overlaps harm and 0% in native late onset. `two_gate` promotes in 72% of native streams and gains +201.26.
- Reversal: rollback fires in 58% (full), 86% (fixed-cert) and 72% (two_gate) of streams, yet all three lose against `continue` (-143.76, -216.99, -181.02).
- `*_controller` arms match the non-controller arms exactly in all 8 profiles.
- Null controls: 0/100 promotions and 0/100 Q1 triggers in stationary and benign for the gated arms (efficacy-block observation only; calibration claim rests on a separate 1,000-stream null study, `integrated_null_calibration_protocol_v1.md`).

**Decision gate NO-GO reasoning** (`decision_gate_report_2026-10-26.md`, committed 2026-10-27). Paraphrase: NO-GO on any new algorithm (RIVE, ASC) for four reasons.
1. The frozen integrated result is profile-specific, simpler two-gate and fixed-candidate arms did better in the same profiles, it missed native late onset and reversed badly, and the controller ablation was inert.
2. The strongest component results (Comparecast, PPE/PPRM, Target-Scout, fixed-start mixtures) are conditional on their own nulls and DGPs; Target-Scout's gain is confined to its IID synthetic workflow.
3. Real data (EIA 2026, Upworthy) gives two task-specific evaluations, but none exercises the whole monitor-certify-intervene system. CRSP, WILDS and Gas Sensor are offline or exposed; Criteo feedback is too immature; Hillstrom's split is exposed; Project GATE has differential follow-up.
4. Comparator closure is scope-dependent. AnyRank is inconclusive, OCS/HCPI/CPC/CPS/CABAI are inapplicable to common-label tasks, and UPF/RCCDA/CARA/ADWIN/DDM are task-specific adaptations.

It adds a novelty update: Digalakis et al., Löfström and Regol et al. cover the "evidence to costed switching/intervention" transition, so that phrase is "not a defensible novelty claim". It ranks four remaining gaps (real-data unified evidence, no general integrated advantage, incomplete Q1-Q3 baseline frontier, manuscript and contribution). `publication_scope_decision_v1.md` converts this to NO-GO on a unified-method paper and PIVOT to a retrospective benchmark/failure-analysis manuscript, with STOP/PIVOT if differentiation is not shown.

### 2. Claims in manuscript_draft_v0.md and claim_evidence_map_v1.md vs evidence

Manuscript: `papers/shiftguard_unified/manuscript_draft_v0.md` (last commit `32c5cfd`, 2026-10-27 02:43). Claim map: `claim_evidence_map_v1.md` (last commit `d0d49f6`, 2026-10-27 16:18). The status line of every claim below is mine; the claim map's own "permitted strength" column is mostly conservative.

| ID / manuscript claim | Cited evidence | Exists? Supports? |
|---|---|---|
| C1 / Sec 4.1: shift, predictive degradation and decision harm are distinct estimands | `synthetic_benchmark_protocol.md`, integrated results, Timans protocol | **Supported** for registered generators only; manuscript and claim map both bound it correctly. |
| C2 / Sec 4.2: no Holm-adjusted DIVE advantage over Timans; Comparecast counts descriptive | `timans_unknown_shift_paired_cost_protocol_v1.md`, `outputs/.../sota_reproductions/timans_unknown_shift_paired_cost_v1/report.md`, verifier script | **Supported** as a negative or tie result. Not re-opened by me. Newer WP1 phase restates R1 as "Tie / no method claim" (`docs/phase_report_stratified_monitor.md`). |
| C3 / Sec 4.3: PPE 67.71% vs 55.21%, +12.50 pp [11.17, 13.83], gain concentrated at q=0.20; null 0/1000 in 16 cells | `ppe_paired_cost_confirmation_results_v1.md` (numbers confirmed by grep) | **Supported** for the registered synthetic design. **Partially superseded in framing**: WP1 S3 (`docs/gated_monitor_comparison_results.md`) shows gated arms dominate ungated ones and the PPE gated alias is among the best selective arms, tied with the gated HT composition. So the ungated "fixed-mixture" PPE comparator is a weak baseline (~91% of labels go to zero-cost events per `docs/phase_report_stratified_monitor.md`). |
| C4 / Sec 4.3: Target-Scout beats fixed split (+8.7607) and pooled rank (+6.6660), above +1 margin | `target_scout_fixed_split_confirmation_protocol.md`, confirmed output dir | **Supported** for the frozen IID synthetic family. Not re-checked numerically. |
| C5 / Sec 4.3: MOPE 991/1000 vs Hoeffding 717/1000; MOPE/OPI +0.15 matched; empty sets retained | `opi_mope_matched_results_v1.md`, protocol | **Supported** for IID synthetic only; no ShiftLab advantage claimed. Wang's Certification Exponent is not fully evaluated (see C11). |
| C6 / Sec 4.4: integrated pipeline has profile-specific gains and failures, no general advantage | efficacy results v1 | **Supported** (re-verified against CSV). **Omission**: the manuscript and claim map never discuss `q1_fallback` or the ungated `fixed_candidate_certification` arm (see section 4). |
| C7 / Sec 4.6: EIA 2026, all adaptive refits beat frozen Ridge; CISO frozen RMSE 2,235.80, weekly 1,651.21-1,672.10, ERCO 2,013.63 | `eia_2026_out_of_time_confirmation_results.md` (numbers confirmed by grep) | **Supported** as retrospective prediction/update-count result under assumed delays. |
| C8 / Sec 4.6: Upworthy +0.1002 CTR pp on 3,808 tests, CI 0.0850-0.1170 | `upworthy_real_data_eligibility_audit.md`, `real_data_confirmation_gate_audit.md` | **Supported** per repo text; I did not open the output bundle. |
| C9: no novel unified algorithm or deployment advantage | gate report, `challenger_switching_fidelity_audit.md`, `label_free_temporal_audit_prior_work.md` | **Supported**, and reinforced by newer docs. |
| C10 / Sec 4.6 table: CRSP, Gas Sensor, WILDS, CriteoPrivateAds, Criteo Attribution, Hillstrom exploratory | `crsp_decision_policy_pilot_results.md`, `real_data_development_results.md`, `real_data_inventory.md`, `docs/crsp_monitor_comparison_results.md` | **Supported** as exploratory; not individually re-verified. |
| C11 / Sec 4.3: one-step Certification Exponent 16/1000 vs MOPE 11/1000 null; 270/300 vs 279/300; McNemar p=0.0636 | `certification_exponent_one_step_results.md` | **Supported** (bounded). Reference list has Wang as "Wang, R." and again as "Wang, J." with the same arXiv ID: duplicate and inconsistent entry, lines 190 and 202. |
| C12 (claim map only): WP2/WP3 candidate screens negative | `docs/stratified_growth_prescreen_results.md`, `docs/data_efficient_edetector_prescreen_results.md` | **Supported** (confirmed against `docs/phase_report_stratified_monitor.md`). **Not in the manuscript draft.** |
| Sec 4.5: ASI 30-seed result; Robust ASI lower RMSE at 9/10 budgets | `asi_paired_cost_development_results.md`, `robust_asi_acs_reproduction_results.md` | Exists per `sota_fidelity_matrix.md`; I did not open the result files. Manuscript labels it as development or single-sample. |
| Sec 4.6 OBD: IPW +0.001809, MOPE empty at event 866, 274,737 events | `open_bandit_mope_development_execution_note_2026-10-26.md` (confirmed by grep) | **Supported** as exploratory only. |
| Abstract: "EIA replay found lower forecast error for adaptive refitting" | same as C7 | Supported; note the abstract also says the gate "evaluates separate components". |

No claim I found cites evidence that is missing. The draft's own header says it is not submission-ready.

### 3. Prior-art and SOTA fidelity status per comparator (as the repo records it)

Sources: `papers/shiftguard_unified/sota_fidelity_matrix.md` (last commit `32c5cfd`), `comparator_scope_decision_v1.md`, `comparator_applicability_audit_v1.md`, `novelty_audit.md`. No new literature search done.

- **Timans (UAI 2025):** source-pinned replay, official `approx_grapa` and `grapa`; log-wealth max abs error 0 and 1.86e-7. Included, tie with DIVE. `novelty_audit.md` says its null maps exactly to the paired-cost null after an affine transform, so "generic Q1 monitor is not a novelty claim."
- **Comparecast (Choe and Ramdas):** official `eprocess_expm` called from pinned checkout; weak running-average null differs from DIVE's conditional null; counts descriptive only. The matrix flags NumPy masked-log warnings and a pending verification of upstream warning behavior.
- **PPE (Csillag):** project-specific paired-cost transfer, calibrated and confirmed; "not a reproduction of the paper's applications."
- **PPRM (Zhang):** implemented for predictive risk; 7/300 detections vs SRM 19/300, i.e. no PPRM advantage. Excluded from harm ranking.
- **WATCH:** no reproduction; "Not comparable as-is" until a score/null bridge exists.
- **Schirmer TTA monitor:** code inspected at commit `f200f00d`, no reproduction; scope comparator only (`tta_monitor_fidelity_audit.md`).
- **MOPE (Karampatziakis):** pinned, independently verified on IID synthetic; OBD validity unresolved (unit, slate dependence, feedback timing).
- **OPI (Molitor 2026):** independent formula-level calibration (0/1000 false eliminations, 80.0% unique separation); the repo flags author-code fidelity problems (full-stream OLS fit, clipping, `alpha/m` on both tails). Preprint-only.
- **Wang Certification Exponent (arXiv 2610.24345, 17 Oct 2026):** one-step specialization only, not the full multi-step algorithm; the repo notes no public code or supplement in the arXiv source archive. Matrix line 39 still says the frontier is "incomplete until task fit is resolved"; `claim_evidence_map_v1.md` C11 was added later.
- **AnyRank, PACE:** AnyRank pilot is star-shaped and inconclusive; PACE is a limited WILDS adaptation only.
- **HCPI, CPS, CPC, RCPS, OCS, CABAI, CUVET, R-IDeA:** scope-only or inapplicable to current common-label tasks (`comparator_scope_decision_v1.md`).
- **UPF (Regol), CARA, RCCDA, ADWIN, DDM:** task-specific EIA adaptations; published-task fidelity "open." DDM threshold is imposed and River is not byte-identical to the official implementation.
- **Digalakis (Challenger), Löfström, Rahman and Tabassum, Ahmed et al. (2026), Ren et al., Wei:** primary-source audited, not reproduced. They are arXiv or recent proceedings, and `novelty_audit.md` calls the search "targeted, not exhaustive."
- **ASI and Robust ASI:** ASI is a fixed-horizon adaptation, authors' source not run; Robust ASI has one original-task reproduction on a single 20,000-record sample.
- **Newest panel not in the matrix:** DISCERN, Xu et al. (NeurIPS 2024), Chugg-style group betting, horizon SR/CUSUM, Zhou et al. G0 audits are recorded only in `novelty_audit.md` (appended 2026-10-27) and `docs/phase_report_stratified_monitor.md`. DISCERN, Chugg and Xu have 0 grep hits in `sota_fidelity_matrix.md`, `comparator_scope_decision_v1.md`, `claim_evidence_map_v1.md`, `manuscript_draft_v0.md`, `docs/closest_prior_work.md` and `docs/next_phase_plan.md`. DISCERN has "no official code reproduction here."
- **Unverified references flagged by the repo:** the draft's reference list header says core metadata was checked on 2026-10-26 but the full systematic search for competing work is still open. Several cited items are 2026 preprints (arXiv 2512.18390, 2604.02351, 2606.17515, 2610.24345, 2610.22930, 2609.17560).

### 4. Positive / inconclusive / negative findings at the integrated level

**Positive (all synthetic, bounded):**
- Full pipeline beats `continue` when harm overlaps the Q1 window: +118.0 and +161.2, both Holm-significant.
- Full pipeline beats `two_gate` and fixed-cert under reversal (+37.3, +73.2), though all remain worse than `continue`.
- Gated arms had 0/100 promotions and 0/100 Q1 triggers in stationary and benign.
- Separate calibration passed for the integrated null (0/1,000 Q1 false escalations per `next_phase_plan.md` line ~334).

**Inconclusive:**
- Recurring regimes and residual variance: exactly 0 effect for the full pipeline, because Q1 triggers but nothing is promoted (recurring), or nothing triggers (residual variance).
- No real-data integrated test exists.

**Negative:**
- No general advantage over the simpler arms. Q1 gate adds no utility on the two aligned profiles (-68.5, -40.1).
- Native late onset is missed entirely (0% Q1 trigger), while `two_gate` earns +201.3.
- Reversal losses are not recovered by rollback.
- Controller adds nothing (identical decisions in 8/8 profiles).
- Newer 2026-10-27 phase: WP2 stratified monitor equals the standard subgroup composition (4.44e-16); WP3 adaptive controller 55% vs 100% for the fixed temporal baseline; ADG anchor at most 1.23x vs required 1.5x; S3 co-primary endpoints pass but credited to DISCERN gating and published engines (`docs/phase_report_stratified_monitor.md`, `docs/algorithm_search_exit_ledger.md`). WP4 real-data validity: 68/68 EIA null cells with 0/1,000 alarms (largest exact bound 0.0030), descriptive only.

**Under-reported in the integrated documents (from the summary CSV, my own reading, not stated in any repo doc I read):**
- `q1_fallback` (switch to the reference on first alarm, no promotion) had mean expected gain +664.64 in boundary harm and +685.91 in monitor-aligned harm, versus +118 for `full_pipeline` and +247 for the full-with-fixed-cert arm. It also had +447.96 in recurring regimes, the only arm that gains there besides `scheduled_promote`. I found no discussion of it in `integrated_efficacy_confirmation_results_v1.md`, the decision gate, claim map or manuscript. It is outside the 22 registered contrasts, but it directly bears on "does Q2/Q3 add value over the Q1 gate alone." Whether the reference policy is a strong oracle-like fallback in the DGP is not documented in the files I read.
- Ungated `fixed_candidate_certification` promoted in 93% of native-late-onset streams (+263) and +285.9 in boundary harm, but is not discussed. The results prose uses `full_pipeline_fixed_certification` (+247.5, +243.5) as "the fixed-candidate pipeline."
- `scheduled_promote` (always promote) beats `full_pipeline` on every aligned-harm profile (+289.9 vs +118.0) and on stationary (+44.1) and benign (+15.95); the results file notes the stable-profile gains but not the comparison with the full pipeline. Under reversal it is -1,581.7.
- On the registered stationary/benign contrasts: `full_pipeline` vs `continue` is not in the family, though the protocol's system-level claim rule asks for it. The summary CSV shows 0.00 for both, so the rule passes, but the results file does not report this explicitly.

### 5. Conflicts and staleness

1. **Manuscript draft not updated for the 2026-10-27 phase.** `manuscript_draft_v0.md` (commit `32c5cfd`) contains no WP1-WP4 content (no DISCERN, gating correction, stratified or WP3 screens, EIA validity table). Superseding: `docs/phase_report_stratified_monitor.md`, `docs/algorithm_search_exit_ledger.md`, `claim_evidence_map_v1.md` C12 (commit `d0d49f6`). The phase report (Sec "Continue / pivot / stop") says the benchmark manuscript should absorb these findings; the manuscript does not yet.
2. **Manuscript Sec 4.3 PPE vs fixed-mixture.** The 12.50 pp gain is measured against an ungated fixed-mixture comparator. Superseded in interpretive weight by `docs/gated_monitor_comparison_results.md`: gating alone gives 0.82-1.00 vs 0.00-0.01 detection at r <= 0.05, and the PPE gated alias ties gated HT. The manuscript sentence "PPE showed a query-rate-dependent synthetic gain over its fixed-mixture comparator" is correct but now misleading about strength against the best equally equipped baseline.
3. **Manuscript status header "2026-10-26"** and the decision gate "Provenance" paragraph (HEAD `525c79e`, "Results in the worktree remain uncommitted") are stale: the content was committed on `32c5cfd` (2026-10-27 02:43) and later commits exist; the gate report also predates WP1-WP4.
4. **Test counts disagree across docs.** `decision_gate_report_2026-10-26.md` and `docs/next_phase_plan.md` line 16: 1,566 pass, 629.95 s. `papers/shiftguard_unified/programme_completion_audit.md` line 32: 1,575 pass, 796.38 s. `docs/next_phase_plan.md` lines ~350, ~376 give 1,486 and 1,563. Latest commit `c2f280d` records a newer full-suite status (outside my area). Verify before citing any single figure.
5. **`docs/research_charter.md` (2026-10-22)** frames Paper 1 as a candidate for a "new method only when a reproducible limitation" exists and Papers 1-3 as independent contributions. Newer evidence (exit ledger, checkpoint B) says Paper 1 algorithm search stops, Paper 2 and 3 are unaffected pivots needing approval. The charter does not mention the benchmark/failure-analysis pivot at all, and still names `next_phase_plan.md` as the next sequence. Treat the charter as direction and `docs/phase_report_stratified_monitor.md` as status.
6. **`docs/next_phase_plan.md`** opening paragraphs (lines 1-14) describe the 60-seed 20% diagnostic as "latest" and "Decision from the latest study" (lines 22-24) about interval-robust mixture-growth; "Current programme status (2026-10-26...)" at line 16 supersedes older lines but not the stratified/WP phase. Also line 84, the "Exit criteria," are generic. No mention of WP1-WP4 or checkpoint B.
7. **`docs/closest_prior_work.md`** (last commit 2026-10-27, first 2026-10-22) calls itself "an initial primary-source comparison"; its table lacks Digalakis, Löfström, Rahman and Tabassum, Wang, Molitor, CPS, DISCERN, Xu, Chugg, Zhou. It still says "This benchmark is deliberately baseline work" and that the Phase 2 benchmark does not yet compare WATCH, PPRM or delayed paired feedback, which is stale given the PPE, PPRM, Timans, MOPE comparisons. Superseded by `novelty_audit.md` and `sota_fidelity_matrix.md`.
8. **`sota_fidelity_matrix.md`** row 66 (existing controller) is current; row 39 (Wang) still says "frontier incomplete" while `claim_evidence_map_v1.md` C11 reports a run. The matrix's own audit-status line says "updated 2026-10-26."
9. **`publication_scope_decision_v1.md` Permitted claim 2** ("DIVE did not demonstrate an adjusted detection advantage...PPE showed query-rate-dependent gain") predates the gated-monitor result and is silent on gating; Claim 3's "profile-specific benefits" does not mention `q1_fallback`.
10. **Duplicate Wang reference** with different first-author initials (`manuscript_draft_v0.md` lines 190 and 202).
11. `claim_evidence_map_v1.md` C6 and manuscript Sec 4.4 say simpler arms performed better "in those same profiles". True for `two_gate` and fixed-cert, but the same results file shows the full pipeline beats both under reversal, and the manuscript omits that.

### 6. Open questions and missing comparisons the repo itself lists

From `decision_gate_report_2026-10-26.md` ranked gaps, `publication_scope_decision_v1.md` finite completion gate, `claim_evidence_map_v1.md` readiness paragraph, `novelty_audit.md`:
- A falsifiable use case where the integrated policy should beat the best simpler baseline, tested on a new registered design with independent data; no new method is the remedy by itself.
- A common claim map and a real-data source supplying the information/outcome contract for a matched end-to-end replay; otherwise state integrated efficacy is synthetic-only.
- Remaining eligible Q1-Q3 comparators run at matched information; Wang's task fit and matched one-step head-to-head (partly done in C11, contextual/OBD fit not); a task-matched logged-bandit head-to-head; WATCH score/null bridge; Challenger and Rahman and Tabassum quantitative comparison (needs matching tasks); UPF official on supported classification timeline.
- Source-by-source literature and citation audit; the repo says the refresh was "targeted, not exhaustive" and that publication-level differentiation, especially after Ahmed et al. (2026), is unverified.
- Manuscript completion: reconcile all numbers and claims against artifacts; PaperBanana-style figure review; dataset versions, licences, timing documentation; rerun full test suite and all verifiers; freeze code, protocols and output hashes in a reviewed revision. `docs/phase_report_stratified_monitor.md` states "No research figure was generated" for the new phase and PaperBanana is not configured in the pinned environment; the Figure 1 caption in the manuscript says it used the PaperBanana style guide rendered deterministically, not the agent pipeline (AGENTS.md requires PaperBanana for research visuals, so this is a possible compliance gap, flagged by the repo's own wording).
- Unresolved real-data items: EIA release times and operational utility, Upworthy lacks a chronological future holdout and the 2024 problem flag, OBD unit and slate dependence and feedback timing, CRSP exposed test period.
- Newer-phase open items: M8 burst-robust label allocation (Paper 3) and Paper 2 promotion need user approval and protocols; prospective EIA smoke check needs data access (earliest about 2026-12-08, about 700 MB bulk or API key); WP3 had only 20 alternative seeds and no null calibration; WP1 S3 is a development comparison, not confirmation (`docs/phase_report_stratified_monitor.md`).
- Not stated anywhere I found: any follow-up on the `q1_fallback` result, or on why the integrated benchmark has no Chugg/DISCERN-style gated arm in its Q1 stage.
