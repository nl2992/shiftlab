# Graph Report - scoped-method-research-current  (2026-11-06)

## Corpus Check
- Large corpus: 3506 files · ~4,129,588 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder.

## Summary
- 5828 nodes · 15768 edges · 249 communities (197 shown, 52 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 952 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c66185c0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 12
- Community 13
- Community 14
- Community 15
- Community 16
- Community 17
- Community 18
- Community 19
- Community 20
- Community 21
- Community 22
- Community 23
- Community 24
- Community 25
- Community 26
- Community 27
- Community 28
- Community 29
- Community 30
- Community 31
- Community 32
- Community 33
- Community 34
- Community 35
- Community 36
- Community 37
- Community 38
- Community 39
- Community 40
- Community 41
- Community 42
- Community 43
- Community 44
- Community 45
- Community 46
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59
- Community 60
- Community 61
- Community 62
- Community 63
- Community 64
- Community 65
- Community 66
- Community 67
- Community 68
- Community 69
- Community 70
- Community 71
- Community 72
- Community 73
- Community 74
- Community 75
- Community 76
- Community 77
- Community 78
- Community 79
- Community 80
- Community 81
- Community 82
- Community 83
- Community 84
- Community 85
- Community 86
- Community 87
- Community 88
- Community 89
- Community 90
- Community 91
- Community 92
- Community 93
- Community 94
- Community 95
- Community 96
- Community 97
- Community 98
- Community 99
- Community 100
- Community 101
- Community 102
- Community 103
- Community 104
- Community 105
- Community 106
- Community 107
- Community 108
- Community 109
- Community 110
- Community 111
- Community 112
- Community 113
- Community 114
- Community 115
- Community 116
- Community 117
- Community 118
- Community 119
- Community 120
- Community 121
- Community 122
- Community 123
- Community 124
- Community 125
- Community 126
- Community 127
- Community 128
- Community 129
- Community 130
- Community 131
- Community 132
- Community 133
- Community 134
- Community 135
- Community 136
- Community 137
- Community 138
- Community 139
- Community 140
- Community 141
- Community 142
- Community 143
- Community 144
- Community 145
- Community 146
- Community 147
- Community 148
- Community 149
- Community 150
- Community 151
- Community 152
- Community 153
- Community 154
- Community 155
- Community 156
- Community 157
- Community 158
- Community 159
- Community 160
- Community 161
- Community 162
- Community 163
- Community 164
- Community 165
- Community 166
- Community 167
- Community 168
- Community 169
- Community 170
- Community 171
- Community 172
- Community 173
- Community 174
- Community 175
- Community 176
- Community 177
- Community 178
- Community 179
- Community 180
- Community 181
- Community 182
- Community 183
- Community 184
- Community 185
- Community 186
- Community 187
- Community 188
- Community 189
- Community 190
- Community 191
- Community 192
- Community 193
- Community 194
- Community 195
- Community 196
- Community 197
- Community 198
- Community 199
- Community 200
- Community 201
- Community 202
- Community 203
- Community 204
- Community 205
- Community 206
- Community 207
- Community 208
- Community 209
- Community 210
- Community 211
- Community 212
- Community 213
- Community 214
- Community 215
- Community 216
- Community 217
- Community 218
- Community 219
- Community 220
- Community 221
- Community 222
- Community 223
- Community 224
- Community 225
- Community 226
- Community 227
- Community 228
- Community 229
- Community 230
- Community 231
- Community 232
- Community 233
- Community 234
- Community 235
- Community 236
- Community 242
- Community 243
- Community 244
- Community 245

## God Nodes (most connected - your core abstractions)
1. `environment()` - 166 edges
2. `Event` - 104 edges
3. `QueryRequest` - 98 edges
4. `ReleasedFeedback` - 63 edges
5. `BudgetedPromotionConfig` - 60 edges
6. `finalize_manifest()` - 53 edges
7. `resolve_device()` - 52 edges
8. `PublicEvent` - 49 edges
9. `Method` - 47 edges
10. `BoundedMeanEProcess` - 46 edges

## Surprising Connections (you probably didn't know these)
- `_alarm_rate()` --uses--> `MixtureSRDetector`  [INFERRED]
  tests/failure_atlas_v2/test_restart_monitor.py → scripts/failure_atlas_v2/restart_monitor.py
- `test_detects_late_change()` --uses--> `MixtureSRDetector`  [INFERRED]
  tests/failure_atlas_v2/test_restart_monitor.py → scripts/failure_atlas_v2/restart_monitor.py
- `AlwaysAsk` --uses--> `Event`  [INFERRED]
  tests/promising_directions/test_sota_simulator.py → scripts/promising_directions/sota/simulator.py
- `AlwaysAsk` --uses--> `QueryRequest`  [INFERRED]
  tests/promising_directions/test_sota_simulator.py → scripts/promising_directions/sota/simulator.py
- `Flipper` --uses--> `Event`  [INFERRED]
  tests/promising_directions/test_sota_simulator.py → scripts/promising_directions/sota/simulator.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Failure Atlas v2 protocol, selected mechanism, validation and report** — docs_failure_atlas_v2_flq_protocol, docs_failure_atlas_v2_flq_results_selected_mechanism, docs_failure_atlas_v2_flq_results_validation_synthetic, docs_failure_atlas_v2_flq_results_validation_real, docs_failure_atlas_v2_flq_results_report [EXTRACTED 1.00]
- **WP1 RMM and rollback results reviewed with prior-art audit** — docs_sprint2_wp1_results, docs_sprint2_wp1_results_rmm, docs_sprint2_wp1_results_e_rb, docs_sprint2_novelty_novelty_rmm, docs_sprint2_novelty_novelty_e_rb [EXTRACTED 1.00]

## Communities (249 total, 52 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.04
Nodes (85): environment(), resolve_device(), _append_paired_report(), BudgetedPromotionConfig, _cp_upper(), main(), _profile_name(), run_calibration() (+77 more)

### Community 1 - "Community 1"
Cohesion: 0.03
Nodes (61): _job(), main(), digest(), main(), paired_ci(), wilson(), main(), main() (+53 more)

### Community 2 - "Community 2"
Cohesion: 0.04
Nodes (58): DelayedBenchmarkConfig, _device(), _generate_stream(), main(), run_benchmark(), summarize(), _write_report(), calibration_alarm_indices() (+50 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (46): main(), sha256(), exact_upper(), main(), run(), Config, _bootstrap_interval(), main() (+38 more)

### Community 4 - "Community 4"
Cohesion: 0.05
Nodes (41): benefit_schedule(), _calibration(), _evaluate_methods(), main(), _paired_contrasts(), run_grid(), _simulate_gate(), _update_mixture() (+33 more)

### Community 5 - "Community 5"
Cohesion: 0.04
Nodes (12): _Base, DelayedFTRLCapacity, GongZhangPaidObs, QiuMovementOCO, _View, CAMSNative, EconomicReplacement, FixedModel (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.04
Nodes (17): _QCECertMixin, GongZhangPaidObsPolicy, _Paced, QiuDelayedMovementPolicy, RyabchenkoCapacityPolicy, _sigmoid(), QueryRequest, DeployGate (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.04
Nodes (37): replay_engine(), evidence_replays(), _first_crossing(), _fixed_stake_detector(), _log_factors_to_detector(), optional_policy_replay(), _alarm(), build_stream() (+29 more)

### Community 8 - "Community 8"
Cohesion: 0.05
Nodes (34): StartedMixtureEProcess, AdaptiveReliance, pprm_adaptive_reliance(), pprm_block_design_variance(), pprm_block_estimate(), prediction_powered_bound(), prediction_powered_estimate(), prediction_powered_randomization_variance() (+26 more)

### Community 9 - "Community 9"
Cohesion: 0.05
Nodes (63): build_method(), NoSwitch, run(), _boundary_null_rate(), _boundary_null_rate_v2(), small(), small2(), small3() (+55 more)

### Community 10 - "Community 10"
Cohesion: 0.04
Nodes (39): boot(), load(), main(), summarize_panel(), cluster_ci(), binary_action(), binary_risk(), bounded_position() (+31 more)

### Community 11 - "Community 11"
Cohesion: 0.06
Nodes (13): _HorvitzThompsonMonitor, _PacedBase, UniformHT, V1MonitorShim, HarnessResult, run_monitor(), Feedback, Monitor (+5 more)

### Community 12 - "Community 12"
Cohesion: 0.06
Nodes (29): generate(), main(), _main(), _chunk_plan(), random_chunks(), DatasetTaskSpec, SyntheticConfig, oblivious_change_times() (+21 more)

### Community 13 - "Community 13"
Cohesion: 0.05
Nodes (30): assign_splits(), fit_training_scaler(), retrospective_event_splits(), acquire(), _licensed_timestamp_seconds(), standardize(), prepare(), acquire() (+22 more)

### Community 14 - "Community 14"
Cohesion: 0.06
Nodes (26): calendar(), Bars, build_binance_task(), calendar_features(), costs_for_fee(), load_binance_bars(), loss_from_pnl(), momentum_position() (+18 more)

### Community 15 - "Community 15"
Cohesion: 0.06
Nodes (46): bbsd(), _boundary_q(), boundary_weight(), c2st(), _cal_scores(), cusum(), _ewm_cumsum(), _family() (+38 more)

### Community 16 - "Community 16"
Cohesion: 0.05
Nodes (24): run_metrics(), stream_from_losses(), run_metrics(), stream_from_losses(), run_episode(), AlwaysAsk, Flipper, test_delay_one_is_immediate_feedback_and_does_deliver() (+16 more)

### Community 17 - "Community 17"
Cohesion: 0.07
Nodes (28): _assemble(), decision_cost(), paired_cost(), reserve_actions(), guard_timestamps(), build_opsd_tasks(), embargoed(), _build_window() (+20 more)

### Community 18 - "Community 18"
Cohesion: 0.05
Nodes (38): all_cells(), all_method_names(), baseline_registry(), build_ref_family(), build_ref_family_for(), build_ref_valid2(), calibrate_family_kappa(), classify_cell() (+30 more)

### Community 19 - "Community 19"
Cohesion: 0.07
Nodes (23): mean_difference_interval(), purge_unavailable_labels(), benchmark(), _GpuSampler, read_samples(), _parse_sample(), commit(), source_hash() (+15 more)

### Community 20 - "Community 20"
Cohesion: 0.05
Nodes (10): DiscernQCE, DiscernFrontLoad, DiscernLCE, _FrontLoadMixin, GatedFrontLoad, _LabelClockMixin, _CertificateStop, DiscernStyleStop (+2 more)

### Community 21 - "Community 21"
Cohesion: 0.08
Nodes (27): _calibrate(), ExperimentConfig, _generate(), _git_revision(), main(), _observed_run(), _plot(), run_experiment() (+19 more)

### Community 22 - "Community 22"
Cohesion: 0.08
Nodes (20): make_family2_stream(), make_family3_stream(), make_family4_stream(), make_markov_stream(), make_stream(), markov_transitions(), BankSpec, bernoulli_grid_spec() (+12 more)

### Community 23 - "Community 23"
Cohesion: 0.09
Nodes (24): build_stream(), build_timeline(), candidate_actions(), CertResult, _cost(), deployed_actions(), deterioration_start(), evaluate_timeline() (+16 more)

### Community 24 - "Community 24"
Cohesion: 0.08
Nodes (23): main(), _persistence_rows(), PersistencePromotionConfig, _plot(), run_persistence_grid(), _two_phase_decisions(), _fixed_horizon_empirical_bernstein_gate(), _fixed_horizon_gate() (+15 more)

### Community 25 - "Community 25"
Cohesion: 0.08
Nodes (23): _aggregate_contrasts(), main(), _paired_contrasts(), run_grid(), main(), run_grid(), main(), _paired_contrasts() (+15 more)

### Community 26 - "Community 26"
Cohesion: 0.09
Nodes (13): _candidate_outcome_contrasts(), ActionEstimate, CertifiedPromotionRollback, Intervention, InterventionController, InterventionStep, _build_event_logs(), _candidate_active_mask() (+5 more)

### Community 27 - "Community 27"
Cohesion: 0.07
Nodes (7): BoundedMeanEProcess, HorizonHedgedStartedMixtureEProcess, PredictableVarianceAdaptiveEProcess, main(), run_grid(), _process(), ContextStratifiedEProcess

### Community 28 - "Community 28"
Cohesion: 0.08
Nodes (20): DeadlinePacer, diagnose(), _gated(), GridMixtureDetector, host_detector(), _make(), f(), multiscale_detector() (+12 more)

### Community 29 - "Community 29"
Cohesion: 0.07
Nodes (22): build_stream(), build_suite(), r(), load_losses(), main(), make_p7s(), paired_ci(), run_dataset() (+14 more)

### Community 30 - "Community 30"
Cohesion: 0.10
Nodes (13): learner_slice(), AllocationGridConfig, main(), _one_stream(), _plot_allocation_summary(), _plot_rate_stabilized_summary(), robust_main(), run_allocation_grid() (+5 more)

### Community 31 - "Community 31"
Cohesion: 0.09
Nodes (11): CalibratedPosterior, derivation4_weight(), _features(), introspective_delta(), propensity(), sampling_distribution(), _Sawade, SawadeActiveNeq (+3 more)

### Community 32 - "Community 32"
Cohesion: 0.09
Nodes (18): GatedHTFixed, GatedHTPaced, HarnessResultV2, public_stream_audit(), RealTask, run_length_summary(), opsd_informative(), _delays() (+10 more)

### Community 33 - "Community 33"
Cohesion: 0.07
Nodes (14): DataEfficientSourcePath, _record(), _source_factor_logs(), source_panel(), feature_adwin_alarm(), minimum_query_probability(), PPEUpdate, prediction_powered_factor() (+6 more)

### Community 34 - "Community 34"
Cohesion: 0.10
Nodes (25): decision_cost(), _delta_terms(), g5_effects(), _g5_p(), _g5_stream(), nonlinear_term(), population_effects(), _rbf_mmd2() (+17 more)

### Community 35 - "Community 35"
Cohesion: 0.07
Nodes (10): HardBudgetPacing, put(), _final_log_e(), RValidFamily2, AllOnsetEDetector, C2ReversalBudgetSplit, DALRestart, Method (+2 more)

### Community 36 - "Community 36"
Cohesion: 0.07
Nodes (12): _CAMSCore, constant_policy_advice(), KNNCorrectnessPolicy, learning_rate(), loss_increment(), normalise_advice(), policy_posterior(), query_probability() (+4 more)

### Community 37 - "Community 37"
Cohesion: 0.11
Nodes (17): sha256(), reject_secrets(), required_key(), scrub(), snapshot_pages(), metadata_json(), numeric_rows(), save_source() (+9 more)

### Community 38 - "Community 38"
Cohesion: 0.08
Nodes (16): CapMixture, _chain_queries(), _cond_ll(), FamP1, fisher_efficiency(), ll_grad(), _h(), _k_job() (+8 more)

### Community 39 - "Community 39"
Cohesion: 0.15
Nodes (20): _bins(), build_cohort_b(), main(), _propensity_from_root(), _sqrt_r(), _bootstrap(), build_cohort(), main() (+12 more)

### Community 40 - "Community 40"
Cohesion: 0.08
Nodes (18): DiscernDesignFloor, _f(), r(), _cmean(), _cmean_s(), CondMeanEB, _dd(), _DepMixin (+10 more)

### Community 41 - "Community 41"
Cohesion: 0.09
Nodes (13): _BlockOracle, epsilon_grid(), expected_entropy_is_instance_blind(), final_model_by_labeled_accuracy(), gamma_from_epsilon(), hypothetical_entropies(), ModelSelectorNative, _Offset (+5 more)

### Community 42 - "Community 42"
Cohesion: 0.12
Nodes (5): _fit_allocation(), AdaptiveQueryPolicy, EvidenceGrowthQueryPolicy, ExactMixtureGrowthQueryPolicy, RobustActiveInferenceQueryPolicy

### Community 43 - "Community 43"
Cohesion: 0.09
Nodes (8): arithmetic_mean_evalue(), closure_adjust(), confidence_set_step(), PacedDisagreementAcquisition, run_native(), SMCSDeploymentPolicy, SMCSInference, weighted_pair_inputs()

### Community 44 - "Community 44"
Cohesion: 0.08
Nodes (10): binary_zero_one_score_is_disagreement(), fit_class_prior(), lure(), pair_score(), query_weights(), sample_from_p_numpy(), VarianceMinCausalAdapter, VarianceMinNative (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.12
Nodes (19): _fit_candidate_family(), _binary_cost(), CandidatePromotionTest, CandidateVersion, _evaluate_stream(), main(), _plot_promotion_summary(), PromotionExperimentConfig (+11 more)

### Community 46 - "Community 46"
Cohesion: 0.14
Nodes (15): LearnerSlice, _allocation_vectors(), _as_jsonable_per_stratum(), calendar_to_list(), evaluate_slice(), _exact_stake_growth(), fixed_tariff_strata(), _pooled_growth() (+7 more)

### Community 47 - "Community 47"
Cohesion: 0.09
Nodes (13): outcome_delay(), ReorderBuffer, run_informative(), run_for(), set_stake_mixture(), valid_gate(), BudgetExceeded, Config (+5 more)

### Community 48 - "Community 48"
Cohesion: 0.09
Nodes (5): AlarmThenSwitch, run_monitor_v2(), MonitorV2, SwitchContext, Switcher

### Community 49 - "Community 49"
Cohesion: 0.09
Nodes (8): _Evidence, wide_stakes_gate(), with_stakes(), MultiTimescaleStartedKellyEProcess, VectorizedStartedMixtureEProcess, ValidKellyMixtureEProcess, _with_stakes(), started_gate()

### Community 50 - "Community 50"
Cohesion: 0.09
Nodes (8): _alt_grid(), build_dep(), _FrontGated, _loglik(), MarkovLREProcess, MarkovLRGate, null_sup_loglik(), ThinnedHedgedGate

### Community 51 - "Community 51"
Cohesion: 0.11
Nodes (18): structured_rows(), acquire(), load_input(), _make_frames(), _parquet_file(), _read_chunks(), _row_group(), validate_config() (+10 more)

### Community 52 - "Community 52"
Cohesion: 0.13
Nodes (17): _alpha_weights(), generate_proxy_streams(), main(), _posterior_harm_probability(), _render_report(), run_grid(), _score_gate(), _score_stratified() (+9 more)

### Community 53 - "Community 53"
Cohesion: 0.14
Nodes (16): candidate_rank_weights(), _cp_upper(), _draw_contexts(), _draw_gains(), _first_ranked(), _hierarchical_paired_bootstrap(), _log_e(), main() (+8 more)

### Community 54 - "Community 54"
Cohesion: 0.10
Nodes (8): references(), RefMonitor, ReleasedObservation, _RT, run_reference(), SequentialMonitor, StreamEvent, TrackSpec

### Community 55 - "Community 55"
Cohesion: 0.11
Nodes (5): GameConfig, SequenceFlow, DelayedRegimeInformation, RegimeFeedback, RegimeModel

### Community 56 - "Community 56"
Cohesion: 0.11
Nodes (5): GatedQCE, GatedLCE, GatedDeploymentStop, MopeCS, EconomicStop

### Community 57 - "Community 57"
Cohesion: 0.09
Nodes (7): _factories(), lrmd(), HorizonWeightedPacer, MixtureSRDetector, RestartMixtureMonitor, r(), PacedDisagreementAcquisition

### Community 58 - "Community 58"
Cohesion: 0.12
Nodes (13): arm_specifications(), conditional_support(), expected_increment_mean(), expected_log_growth(), _increments(), _joint_weights(), mixture_rows(), prescreen_stream() (+5 more)

### Community 59 - "Community 59"
Cohesion: 0.09
Nodes (4): CAMSDeploymentAdapter, ModelPickerDeploymentAdapter, k_policies(), KGate

### Community 60 - "Community 60"
Cohesion: 0.09
Nodes (6): bet_cap(), PairedDiffPredictor, rate_from_score(), residual_score(), solve_normaliser(), XuAcquisitionPolicy

### Community 61 - "Community 61"
Cohesion: 0.11
Nodes (7): build_r6(), GongZhangPaidObs, OnlineFWERSpending, _PacedIW, QiuDelayedMovement, RyabchenkoCapacity, _sigmoid()

### Community 62 - "Community 62"
Cohesion: 0.11
Nodes (7): EnvelopeMixture, _Fixed, StartedMixture, _a1_or_standin(), _Cert, _EnvCert, envelope()

### Community 63 - "Community 63"
Cohesion: 0.15
Nodes (21): build_dataset(), classify(), classify_all(), _classify_stream(), cluster_boot(), contrasts(), _cusum_stat(), _delay_native() (+13 more)

### Community 64 - "Community 64"
Cohesion: 0.13
Nodes (10): analytic_label_requirement(), build_ref_law(), CellSpec, diagnose_cell(), _end_round(), law_hypotheses(), make_family1_stream(), _onset_round() (+2 more)

### Community 65 - "Community 65"
Cohesion: 0.10
Nodes (4): BernoulliPairedModel, PairedCUSUM, _SequentialControl, ShiryaevRoberts

### Community 66 - "Community 66"
Cohesion: 0.10
Nodes (9): Controller, DiscernC, _dz(), _g(), _point(), _q(), QSGTwoStage, report() (+1 more)

### Community 67 - "Community 67"
Cohesion: 0.15
Nodes (13): neyman(), confirm(), diagnostic(), main(), _rasi(), _realloc(), run_arm(), simulate() (+5 more)

### Community 68 - "Community 68"
Cohesion: 0.14
Nodes (15): _ci(), _f(), main(), matrix_rows(), paired(), pooled(), reanalyse_sprint1(), tables() (+7 more)

### Community 69 - "Community 69"
Cohesion: 0.13
Nodes (8): allocate_marginal_cost_equalization(), cost_at(), multipliers_at(), Allocation, CuvetQuantileTree, fit_power_law_bucket(), PowerLawBucket, _TreeNode

### Community 70 - "Community 70"
Cohesion: 0.16
Nodes (15): Config, _device(), _fit_source_proxy(), _generate(), main(), _method_parameters(), _name(), _paired_contrasts() (+7 more)

### Community 71 - "Community 71"
Cohesion: 0.16
Nodes (13): parse_regime(), _delay(), _git_rev(), _h(), _job(), _loss_file(), main(), metrics() (+5 more)

### Community 72 - "Community 72"
Cohesion: 0.16
Nodes (5): CausalSwitchingGame, visit(), visit(), visit(), policy()

### Community 73 - "Community 73"
Cohesion: 0.11
Nodes (8): DecisionFeedback, DecisionRequest, Label, OracleDecisionRecord, PolicyDecision, replay(), replay_decision_stream(), Request

### Community 74 - "Community 74"
Cohesion: 0.11
Nodes (9): build_suite(), p7s(), r(), build_suite(), p7s(), _dec(), _enc(), p7s_plus_params() (+1 more)

### Community 75 - "Community 75"
Cohesion: 0.10
Nodes (4): GatedAdaptiveRange, _Ctl, GatedC, _b()

### Community 76 - "Community 76"
Cohesion: 0.14
Nodes (13): rho_mle(), prep(), f(), build(), main(), _seed(), build_splits(), build_v2() (+5 more)

### Community 77 - "Community 77"
Cohesion: 0.10
Nodes (11): JointContextualONS, f(), _solve3(), xu_query(), f(), compile(), compile_batch(), query() (+3 more)

### Community 78 - "Community 78"
Cohesion: 0.08
Nodes (6): GatedFrontOnly, _smcs_front(), SMCSQCE, _xu_front(), XuQCE, _gate()

### Community 79 - "Community 79"
Cohesion: 0.14
Nodes (9): equal_test_contrasts(), filter_eligible_tests(), _fit_model(), _fit_vectorizer(), FittedCTRPolicy, package_text(), select_package_indices(), tune_and_fit() (+1 more)

### Community 80 - "Community 80"
Cohesion: 0.17
Nodes (13): fixed_mix(), h2c(), hg(), indep_hg_h2c(), kelly(), ons(), tenzer(), xu() (+5 more)

### Community 81 - "Community 81"
Cohesion: 0.12
Nodes (12): chunked(), _clipped_hook(), freeze_m3(), generate_indep(), measure_shift_addon(), mix_control(), replace_source(), salted_streams() (+4 more)

### Community 82 - "Community 82"
Cohesion: 0.15
Nodes (9): atomic_json(), main(), run(), Config, load_config(), LearnerSettings, plot(), EvaluatorStream (+1 more)

### Community 83 - "Community 83"
Cohesion: 0.11
Nodes (12): _A1Cert, started_mixture(), _diag_job(), diagnose(), _episode(), _replay(), sui_cert(), summarize() (+4 more)

### Community 84 - "Community 84"
Cohesion: 0.20
Nodes (6): constant_table(), Evaluator, run_budget(), certify(), main(), SnappedEvaluator

### Community 85 - "Community 85"
Cohesion: 0.11
Nodes (5): setv(), step(), _p(), Result, Ring

### Community 86 - "Community 86"
Cohesion: 0.12
Nodes (12): bottleneck_combinations(), effective_config_key(), PacedCombination, Combination, combinations(), config_dicts(), make_world(), screen() (+4 more)

### Community 87 - "Community 87"
Cohesion: 0.16
Nodes (13): PostZeroMixture, exact_ll(), markov_stream(), queried(), run_e(), test_budget_never_exceeded_and_no_future_access(), test_eprocess_nonnegative_and_finite(), test_null_upper_bound_dominates_every_null_member() (+5 more)

### Community 88 - "Community 88"
Cohesion: 0.17
Nodes (5): _run_arm(), simulate_cell(), simulate_pair(), EventOrderBuffer, ResolvedEvidence

### Community 89 - "Community 89"
Cohesion: 0.14
Nodes (3): _risk_bound_alarm(), PPIBlockConfidenceSequence, PPRMRiskMonitor

### Community 90 - "Community 90"
Cohesion: 0.12
Nodes (5): all_cells3(), all_cells4(), Family3CellSpec, Family4CellSpec, _RegimeCell

### Community 91 - "Community 91"
Cohesion: 0.13
Nodes (13): _at(), audit_cells(), ensure_cs(), equivalence_suite(), fn(), fit_selector(), per_seed(), power_n() (+5 more)

### Community 92 - "Community 92"
Cohesion: 0.16
Nodes (12): calibrate(), cat_tapes(), dev_grid(), generate(), _h30(), _noise(), _paths(), _phi() (+4 more)

### Community 93 - "Community 93"
Cohesion: 0.14
Nodes (5): Cocob, fixed_question_features(), FixedRiskPredictor, QueryNormalizer, learned_paired_rcps()

### Community 94 - "Community 94"
Cohesion: 0.13
Nodes (9): paired_cusum(), paired_edetectors(), finish_paired_result(), paired_fixed_mixture(), paired_paper_reference(), active_rcps_cost(), ppi_batch_estimate(), pprm_batch_cost() (+1 more)

### Community 95 - "Community 95"
Cohesion: 0.16
Nodes (13): _active(), audit_equivalence(), _block_size(), canonicalise(), _decode(), enumerate_space(), _groups(), Op (+5 more)

### Community 96 - "Community 96"
Cohesion: 0.14
Nodes (4): CamsDecision, HardBudgetDelayedCams, _PendingLabel, RandomSource

### Community 97 - "Community 97"
Cohesion: 0.14
Nodes (6): build_ref_valid(), DiagOracleGate, family1_start_design(), RValid2Family1, RValidFamily1, EpisodeComposition

### Community 98 - "Community 98"
Cohesion: 0.16
Nodes (8): _epoch(), _frame(), _git(), load_series(), PairedReserveStream, read_streams(), _sha256(), write_streams()

### Community 99 - "Community 99"
Cohesion: 0.15
Nodes (7): build_packet(), _guard_form(), _guard_root(), guard_source(), packet_manifest(), SandboxError, _stripped_env()

### Community 100 - "Community 100"
Cohesion: 0.15
Nodes (5): feasible_leaf_factors(), _leaf_arrays(), OneStepUpdate, _projected_mle_bet(), ProjectedKellyOneStep

### Community 101 - "Community 101"
Cohesion: 0.13
Nodes (6): compute_u_t(), eta_t(), eta_zero(), ModelPickerNative, posterior(), query_probability()

### Community 102 - "Community 102"
Cohesion: 0.14
Nodes (3): _entropy(), OnlineLLMPicker, pseudo_loss_matrix()

### Community 103 - "Community 103"
Cohesion: 0.14
Nodes (4): DepTwin, DMHACMonitor, newey_west_var(), _regs()

### Community 104 - "Community 104"
Cohesion: 0.15
Nodes (4): FilterReference, HMMFilterReference, _tables(), _Tables

### Community 105 - "Community 105"
Cohesion: 0.15
Nodes (4): HardBudgetDelayedOnlinePicker, _PendingLabel, PickerDecision, RandomSource

### Community 106 - "Community 106"
Cohesion: 0.16
Nodes (9): Instance, levels_instance(), main(), min_changes(), monotone_in_wealth(), neyman_table(), _nonincreasing(), _selection_exists() (+1 more)

### Community 107 - "Community 107"
Cohesion: 0.24
Nodes (12): build(), calendar(), load_appliances(), load_beijing_pm25(), load_bike_hour(), load_household_power(), load_metro(), main() (+4 more)

### Community 108 - "Community 108"
Cohesion: 0.16
Nodes (6): LPRiskVerification, verify_controller_lp(), DeterministicController, RiskVerification, verify_causal_null_risk(), value()

### Community 109 - "Community 109"
Cohesion: 0.12
Nodes (13): _a5b_host(), _Det, kbuild(), _make_p6(), __init__(), _new_detector(), request_labels(), _p6() (+5 more)

### Community 110 - "Community 110"
Cohesion: 0.15
Nodes (7): ablation_of(), CandidateSpec, differing_slots(), dss_ablations(), dss_spec(), propose_candidates(), add()

### Community 111 - "Community 111"
Cohesion: 0.16
Nodes (8): main(), run_direct_ipw_query_calibration(), summarize_direct_ipw_query_calibration(), DirectIPWQueryGridConfig, main(), _paired_summary(), run_direct_ipw_query_grid(), run_hard_budget()

### Community 112 - "Community 112"
Cohesion: 0.16
Nodes (7): _bounded_vector(), PPRMBatchEstimate, PredictableReliance, prediction_powered_batch_risk(), source_prediction_powered_values(), source_risk_upper_bound_betting(), source_risk_upper_bound_cm_eb()

### Community 114 - "Community 114"
Cohesion: 0.19
Nodes (11): boot_ci(), load(), main(), paired(), summary(), units(), main(), cell() (+3 more)

### Community 115 - "Community 115"
Cohesion: 0.14
Nodes (6): DetectorSwapMonitor, GLRDetector, _kl(), SRRDetector, _sw(), _swap()

### Community 116 - "Community 116"
Cohesion: 0.18
Nodes (5): CUSUM, ks_test(), decision_losses(), Learner, exponentially_weighted_conformal_quantile()

### Community 117 - "Community 117"
Cohesion: 0.16
Nodes (6): BetaPerformanceForecaster, build_upf_features(), fit_available_performance_forecaster(), fit_beta_performance_forecaster(), PerformanceObservation, upf_retraining_schedule()

### Community 118 - "Community 118"
Cohesion: 0.19
Nodes (6): _collect_horizons(), main(), _lse(), MarkovSUI, _p_edges(), _rho_edges()

### Community 119 - "Community 119"
Cohesion: 0.13
Nodes (6): allocate_update_budget(), ComputeBudget, gaussian_interval_score_expectation(), interval_recalibration_reference(), intervention_reference(), pareto_frontier_mask()

### Community 121 - "Community 121"
Cohesion: 0.17
Nodes (7): bin_estimates(), bin_propensities(), main(), normalize(), run_monitor_ctx(), allocate(), growth()

### Community 123 - "Community 123"
Cohesion: 0.18
Nodes (11): _mk(), _axis_specs(), build_candidate(), _c(), ComponentInfo, default_spec(), _duration_onset_specs(), _evidence_specs() (+3 more)

### Community 124 - "Community 124"
Cohesion: 0.27
Nodes (8): choose_two_slot_channel(), _distribution(), expected_switches(), _fraction(), _probability(), query_strata(), QueryStratum, TwoSlotChannel

### Community 125 - "Community 125"
Cohesion: 0.17
Nodes (7): inject_under_procurement(), injected_paired_cost(), onset_index(), select_band(), classify_alarms(), injected_analysis(), injection_coins()

### Community 126 - "Community 126"
Cohesion: 0.23
Nodes (8): _baseline_rows(), _build_paired_query_path(), GridConfig, main(), pva_grid(), PVAConfig, run_grid(), _vectorized_pva()

### Community 129 - "Community 129"
Cohesion: 0.21
Nodes (7): frame(), main(), summarize(), t_summary(), wilson(), main(), summarize()

### Community 130 - "Community 130"
Cohesion: 0.18
Nodes (4): FamA, IIDMixture, _a5b(), f()

### Community 132 - "Community 132"
Cohesion: 0.18
Nodes (4): bounded_dr_pseudo_outcomes(), lil_value_bounds(), optimal_policy_set(), optimal_policy_stopping_time()

### Community 133 - "Community 133"
Cohesion: 0.24
Nodes (8): _init_worker(), main(), smoke_check(), _sources(), _h(), _job(), main(), _summarize()

### Community 134 - "Community 134"
Cohesion: 0.22
Nodes (8): clopper_pearson_upper(), null_analysis(), _null_row(), orientation_coins(), registered_cells(), rerun_coins(), replay_batch(), ReplayBatch

### Community 135 - "Community 135"
Cohesion: 0.25
Nodes (6): collect_paths(), _hours(), PathData, _replay(), unmodified_analysis(), unmodified_coins()

### Community 137 - "Community 137"
Cohesion: 0.18
Nodes (3): Candidate, sample_raw(), source_channels()

### Community 138 - "Community 138"
Cohesion: 0.18
Nodes (8): calib_score(), eval_cands(), fn(), finalist_tables(), kmax_auto(), run_cands(), sig(), tapes_for()

### Community 139 - "Community 139"
Cohesion: 0.18
Nodes (7): clopper_pearson(), _flag(), frontier(), intersection_union(), paired_cluster_bootstrap(), _registry(), summarise()

### Community 140 - "Community 140"
Cohesion: 0.22
Nodes (6): main(), _one(), sha256(), timestamp_ns(), TimestampIndexedRMM, wallclock_factory()

### Community 141 - "Community 141"
Cohesion: 0.17
Nodes (3): DiscernFrontOnly, build_extra(), _rmm()

### Community 142 - "Community 142"
Cohesion: 0.26
Nodes (5): _offline_objective(), periodic_schedule(), threshold_schedule(), tune_periodic(), tune_threshold()

### Community 143 - "Community 143"
Cohesion: 0.24
Nodes (4): expected_oracle_path(), hindsight_oracle_cost(), _r(), Regime

### Community 144 - "Community 144"
Cohesion: 0.24
Nodes (4): expected_oracle_path(), hindsight_oracle_cost(), _r(), Regime

### Community 145 - "Community 145"
Cohesion: 0.22
Nodes (5): load_losses(), main(), make_policies(), paired_ci(), run_dataset()

### Community 146 - "Community 146"
Cohesion: 0.21
Nodes (4): _a5b(), _gar(), RMMSUI, SUIDetector

### Community 147 - "Community 147"
Cohesion: 0.24
Nodes (5): p2p3(), _paths_eval(), _paths_job(), PRegime, _twin_job()

### Community 149 - "Community 149"
Cohesion: 0.28
Nodes (5): budgeted_probabilities(), choose_robust_geometric_path(), geometric_budget_path(), robust_variance_objective(), _validated_scale()

### Community 150 - "Community 150"
Cohesion: 0.26
Nodes (6): allocate(), find_overlaps(), load_registry(), Registry, SeedBlock, undisclosed_overlaps()

### Community 151 - "Community 151"
Cohesion: 0.23
Nodes (4): main(), boot(), main(), wilson_hi()

### Community 152 - "Community 152"
Cohesion: 0.26
Nodes (7): compare_json(), vv_list(), walk(), dirs(), main(), add(), run()

### Community 153 - "Community 153"
Cohesion: 0.20
Nodes (3): main(), markdown_table(), report_check()

### Community 155 - "Community 155"
Cohesion: 0.21
Nodes (6): _consume_feedback(), _new_detector(), predict(), request_labels(), _switch(), TimestampStartMixture

### Community 157 - "Community 157"
Cohesion: 0.29
Nodes (6): _cp_upper(), main_calibration(), main_confirmation(), run_calibration(), run_confirmation(), _source_hash()

### Community 158 - "Community 158"
Cohesion: 0.24
Nodes (3): all_cells2(), Family2CellSpec, law2_hypotheses()

### Community 159 - "Community 159"
Cohesion: 0.24
Nodes (8): main(), run(), _sha256(), confirm_seeds_allowed(), freeze(), read_freeze(), require_frozen(), sha256_file()

### Community 160 - "Community 160"
Cohesion: 0.24
Nodes (4): build_mope_stream(), choose_best_item(), fixed_horizon_hoeffding_lower(), validate_mope_path()

### Community 161 - "Community 161"
Cohesion: 0.32
Nodes (7): _inputs(), _minimax_bisection(), allocation(), spend(), minimax_support_allocation(), minimax_uncapped_allocation(), _vector()

### Community 162 - "Community 162"
Cohesion: 0.30
Nodes (5): check_freeze(), file_sha256(), _git(), require_freeze(), write_freeze()

### Community 164 - "Community 164"
Cohesion: 0.33
Nodes (6): amend5(), _ci(), gate(), main(), null_table(), rmm()

### Community 167 - "Community 167"
Cohesion: 0.18
Nodes (6): _econ_stop(), _g(), f(), _norm_ppf(), r6_joint(), _xu()

### Community 169 - "Community 169"
Cohesion: 0.38
Nodes (6): Config, _device(), main(), run(), simulate(), _stream()

### Community 170 - "Community 170"
Cohesion: 0.24
Nodes (4): log_factors(), restart_mixture(), sr_statistic(), start_weights()

### Community 171 - "Community 171"
Cohesion: 0.29
Nodes (4): check_imports(), check_source(), _module_violation(), _top_level()

### Community 172 - "Community 172"
Cohesion: 0.24
Nodes (3): DelayedBudgetHedge, PairedFeedback, SwitchingDecision

### Community 173 - "Community 173"
Cohesion: 0.33
Nodes (7): _ci(), diff(), holm(), _load(), main(), wilson(), write_md()

### Community 174 - "Community 174"
Cohesion: 0.31
Nodes (5): calibrate(), evaluate(), _load(), main(), wilson()

### Community 176 - "Community 176"
Cohesion: 0.20
Nodes (3): classification_group_evidence(), fit_offline_classifier(), group_summaries()

### Community 177 - "Community 177"
Cohesion: 0.27
Nodes (3): labels_available_before(), labels_available_by(), purge_unavailable_labels()

### Community 178 - "Community 178"
Cohesion: 0.29
Nodes (5): _generate(), _log_paths(), main(), run(), _upper()

### Community 179 - "Community 179"
Cohesion: 0.24
Nodes (3): _excess(), run(), score()

### Community 180 - "Community 180"
Cohesion: 0.39
Nodes (6): batch(), block_values(), main(), mean_ci(), one(), risk_ci()

### Community 181 - "Community 181"
Cohesion: 0.28
Nodes (4): DeterministicFSC, FSCRiskResult, worst_case_promotion_risk(), visit()

### Community 182 - "Community 182"
Cohesion: 0.31
Nodes (5): boot(), main(), fam_vec(), vec(), wilson_ub()

### Community 183 - "Community 183"
Cohesion: 0.39
Nodes (5): load(), main(), paired(), summarise(), to_markdown()

### Community 184 - "Community 184"
Cohesion: 0.33
Nodes (4): cluster_boot(), cluster_id(), main(), read_runs()

### Community 185 - "Community 185"
Cohesion: 0.33
Nodes (7): make_host(), _h(), f(), _hg(), f(), _tg(), f()

### Community 187 - "Community 187"
Cohesion: 0.28
Nodes (4): build_respondent_streams(), _complete_arrays(), _simulate_pair(), StreamWindows

### Community 189 - "Community 189"
Cohesion: 0.31
Nodes (4): _append_paired_comparisons(), _paired_effects(), _plot_hard_budget(), _summarize()

### Community 190 - "Community 190"
Cohesion: 0.25
Nodes (3): baseline_table(), Frontier, pick_cells()

### Community 191 - "Community 191"
Cohesion: 0.36
Nodes (4): _h(), _job(), jobs_for(), main()

### Community 192 - "Community 192"
Cohesion: 0.29
Nodes (8): Sprint 2 novelty and prior-art audit, A5b gap-indexed Markov sequential universal inference, Conditional and marginal null distinction, E_rb certified rollback gate, RMM restart monitoring module, WP1 RMM late-improvement real-world evaluation, E_rb reversal-cost reduction, RMM and continued post-verdict acquisition

### Community 194 - "Community 194"
Cohesion: 0.36
Nodes (4): analyze(), _bootstrap_mean_ci(), main(), to_markdown()

### Community 195 - "Community 195"
Cohesion: 0.46
Nodes (4): audit(), family_entries(), load_json(), main()

### Community 196 - "Community 196"
Cohesion: 0.46
Nodes (5): _affected_policy(), _available_output(), _command(), main(), _replace_option()

### Community 197 - "Community 197"
Cohesion: 0.36
Nodes (4): evaluate_regression(), Feedback, Observation, simulate()

### Community 199 - "Community 199"
Cohesion: 0.43
Nodes (4): analyse(), contrast(), main(), md()

### Community 206 - "Community 206"
Cohesion: 0.33
Nodes (4): Failure Atlas v2 report, Real-data validation, Fresh-seed synthetic validation, Strict certification: promotion <= 0.0936 on every validation null

### Community 207 - "Community 207"
Cohesion: 0.53
Nodes (4): boot_ci(), load(), main(), table()

### Community 208 - "Community 208"
Cohesion: 0.47
Nodes (3): main(), table_after(), within_rounded()

### Community 209 - "Community 209"
Cohesion: 0.60
Nodes (3): file_record(), main(), sha256()

### Community 210 - "Community 210"
Cohesion: 0.47
Nodes (3): analyze(), gr_one_time_reversal(), main()

### Community 216 - "Community 216"
Cohesion: 0.40
Nodes (5): Comparator validity audit 2026-11-05, GatedAdaptiveRange predictability defect and fix, SOTA benchmark fidelity audit, Same-sample comparator-selection uncertainty, Xu acquisition-only is not Xu published certificate

### Community 217 - "Community 217"
Cohesion: 0.50
Nodes (5): Failure Atlas v2 selected mechanism, M1: certification latency under binding budget, Query-conditional evidence (QCE), QSG standalone candidate, Budget-feasible uniform pacing

### Community 218 - "Community 218"
Cohesion: 0.40
Nodes (5): ShiftLab research charter, Proposed conditional excess-cost null, Decision harm under distribution shift, Feedback regime and filtration, Monitoring, certified adaptation, budgeted adaptation

### Community 227 - "Community 227"
Cohesion: 0.40
Nodes (3): cp_lower(), min_member_gain(), summarise()

### Community 228 - "Community 228"
Cohesion: 0.40
Nodes (3): pareto_rank(), select_pareto(), select_rung0()

### Community 229 - "Community 229"
Cohesion: 0.50
Nodes (3): epoch_configurations(), epoch_screen(), EpochConfig

### Community 230 - "Community 230"
Cohesion: 0.50
Nodes (4): M4: serial dependence and dense sampling, SOTA sprint novelty audit, Choe–Ramdas conditional-mean paired e-process comparator, Prior art for sequential tests, active sampling, restart detectors, and budgeted acquisition

### Community 231 - "Community 231"
Cohesion: 0.67
Nodes (3): decode_fields(), numeric(), part()

### Community 233 - "Community 233"
Cohesion: 0.67
Nodes (3): Atlas v2 cached loss streams README, Nine cached 2000-event paired model-loss streams, Previously exposed cached datasets; episode-level inference

### Community 234 - "Community 234"
Cohesion: 0.67
Nodes (3): Failure Atlas v2 protocol, V2 contract: T=2000, B=200, label price 0.05, switch cost 5, FLQ: front-loaded acquisition plus QCE

### Community 235 - "Community 235"
Cohesion: 1.00
Nodes (3): WP2 benchmark: model deployment under temporal dependence, Exchangeable twins as known marginal-null streams, WP2 V1 conditional, V2 marginal, and V3 economic outcomes

## Knowledge Gaps
- **30 isolated node(s):** `TaskSpec`, `ParamSpec`, `Op`, `Decision harm under distribution shift`, `Proposed conditional excess-cost null` (+25 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2113 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **52 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_simulate_method()` connect `Community 3` to `Community 225`, `Community 88`, `Community 27`, `Community 188`, `Community 223`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **What connects `TaskSpec`, `ParamSpec`, `Op` to the rest of the system?**
  _30 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.03673031209263093 - nodes in this community are weakly interconnected._
- **Why does `kbuild()` connect `Community 109` to `Community 10`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.02588009759498083 - nodes in this community are weakly interconnected._
- **Why does `run_start_prior_robust_mix()` connect `Community 2` to `Community 0`, `Community 1`, `Community 3`, `Community 4`, `Community 10`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.03923853923853924 - nodes in this community are weakly interconnected._