# WP6 Stage B tranche 2 status (Amendment A1; auto-generated)

Updated: 2026-11-07T23:43:24+00:00  
Ledger head: `0abeb6810b1655d1112762cf72daa2a22c03ba69716a19171c1a7342b1896824` (149 records; suite-v2: 41 scope i-ii, 48 scope iii)  
Branch commit: `9a5cafd8c8604e2ac9dfff720c53252186d0c482`

Scope (i-ii) file `results/d2a_rar/stage_b/tranche2_scope.json`: 41 selected (cap 140); counts {"ii": 14, "i": 33}.
Scope (iii) file `results/d2a_rar/stage_b/tranche2_scope_iii.json`: 42 Q1 evidence identities; cells Q1_0, Q1_1, Q1_2, Q1_3, S1a, S1b, S1c, S2d, S2e, S2f, S3a, S3b, S3c, S4a, S4b, S4c.
* [scope i-ii] phase: finished; experiments done this launch: 41 / 41; elapsed 72.1 min; in flight: none; last: replacement_economic_thresholds.switch_cost_amortisation@cost_aware_binary -> DISCARD (28.552s); not run this launch: {}
* [scope iii] phase: finished; experiments done this launch: 5 / 5; elapsed 11.9 min; in flight: none; last: restart_mixture_allocation.e_cusum_markov_base[marg] -> CRASH (305.697s); not run this launch: {"already_in_ledger": 37}

# Scope (i)-(ii): DUPLICATE-of-host-identical and family-gap identities (Q2) on DEV_SUITE_v2

## Decision counts

DISCARD=19, DUPLICATE=19, UNVERIFIED=3

## KEEP and near-KEEP

KEEP = section 4 satisfied under A1. near-KEEP = DISCARD only through the control-cell / host-ablation / complexity / simple-control criteria: valid under its claimed null, not invalid-aggressive, and an effect label other than 'none' on its best target cell against the per-cell strongest applicable comparator. dJ = J(candidate) - J(comparator), negative = candidate better, 95% paired bootstrap CI.

| decision | candidate | method | best target cell (comparator) | dJ [95% CI] | effect | validity (claimed null) | failed checks |
|---|---|---|---|---|---|---|---|
| DISCARD | CAND-2c23131fbaf36f3a | deadline_aware_querying.certificate_deadline_priority@drift2act[d2a.request_size] | S1a:td_shift_lognormal_T400 (never_switch) | -20.76 [-23.99, -17.59] | meaningful (rel +0.077) | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | worse/overspend on neighbouring or negative-control cell |
| DUPLICATE | CAND-38cac870ac6f602b | deadline_aware_querying.certificate_deadline_priority@drift2act[d2a.request_size] | S1a:td_shift_lognormal_T400 (never_switch) | -20.76 [-23.99, -17.59] | meaningful (rel +0.077) | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | worse/overspend on neighbouring or negative-control cell |

## Mandate Q2 stop rule (candidates vs pending_cap / fixed_schedule on target cells)

* Records with a v2 result: 22; candidates whose paired CI is entirely below 0 against BOTH pending_cap and fixed_schedule simultaneously on at least one (the same) target cell: **0**.
* No candidate beats both controls on the same target cell with a paired CI excluding 0.

## All records

| candidate | method | decision | effect | best target cell (comparator) dJ [95% CI] | beats VALID-applicable simple controls (vacuously True if none valid) | validity | v1-regression |
|---|---|---|---|---|---|---|---|
| CAND-2c23131fbaf36f3a | deadline_aware_querying.certificate_deadline_priority@drift2act[d2a.request_size] | DISCARD | meaningful | S1a (never_switch) -20.76 [-23.99, -17.59] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-15f6685377881007 | pending_aware_budgets.release_weighted_inventory_cap@drift2act[d2a.request_size] | DISCARD | none | S1a (never_switch) +14.70 [+7.91, +20.24] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-321b11662ffe1afa | deadline_aware_querying.window_close_probability_value@drift2act[d2a.request_size] | DISCARD | none | S1a (never_switch) +16.31 [+12.87, +19.60] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-38cac870ac6f602b | deadline_aware_querying.certificate_deadline_priority@drift2act[d2a.request_size] | DUPLICATE/CAND-2c23131fbaf36f3a | meaningful | S1a (never_switch) -20.76 [-23.99, -17.59] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-4ba3141109da56cb | pending_aware_budgets.release_feasible_requests@drift2act[d2a.request_size] | DISCARD | none | S1a (never_switch) +16.31 [+12.87, +19.60] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-002d282e5f717866 | pending_aware_budgets.release_feasible_requests@drift2act[d2a.request_size] | DUPLICATE/CAND-4ba3141109da56cb | none | S4a (never_switch) +187.70 [+170.94, +203.10] | False | no validity claim (null=economic) | 0 |
| CAND-307d2109d144f48e | deadline_aware_querying.certificate_deadline_priority@rar[rar.label_request] | DISCARD | none | S4a (never_switch) +2.63 [+2.59, +2.67] | True | no validity claim (null=economic) | 0 |
| CAND-01e20f32110dc0a6 | deadline_aware_querying.window_close_probability_value@drift2act[d2a.request_size] | DISCARD | none | S1a (never_switch) +7.90 [+0.64, +14.81] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-aad82c8e13cf558e | canary_exposure_verification.adaptive_ramp@rar[rar.config] | UNVERIFIED | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-bb9fc589f3333f08 | reversal_aware_rollback.reversal_hazard_rollback@contract_native[contract.switch_policy] | DISCARD | substantial | S1a (never_switch) -115.70 [-132.75, -100.05] | True | false_rollback_rate_given_promotion_under_keep_null 114/157 (0.726), CP95 upper 0.784, screen-level | 2 |
| CAND-bf53e234adc8f886 | deadline_aware_querying.window_close_probability_value@drift2act[d2a.request_size] | DUPLICATE/CAND-321b11662ffe1afa | none | S4a (never_switch) +187.70 [+170.94, +203.10] | False | no validity claim (null=economic) | 0 |
| CAND-cb208e8b3bc4c959 | canary_exposure_verification.economic_exposure_design@rar[rar.config] | UNVERIFIED | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-27378bf06ba653c8 | canary_exposure_verification.economic_exposure_design@rar[rar.config] | UNVERIFIED | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-1fa436fa27dda0f3 | canary_exposure_verification.adaptive_ramp@rar[rar.config] | DUPLICATE/CAND-aad82c8e13cf558e | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=none) | 0 |
| CAND-c4b41d56cbfd3509 | canary_exposure_verification.economic_exposure_design@rar[rar.config] | DUPLICATE/CAND-cb208e8b3bc4c959 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=none) | 0 |
| CAND-c4d268f87c7835d6 | cost_aware_rar_gate.gate2_deadline_label_fraction@rar[rar.gate2] | DISCARD | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-4097033724f480af | cost_aware_rar_gate.gate2_deadline_label_fraction@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-7751b253e8760047 | cost_aware_rar_gate.gate2_recovery_aware@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-e93614e68cb1d430 | cost_aware_rar_gate.gate2_value_of_waiting@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-fa27612e847feb79 | cost_aware_rar_gate.gate2_deadline_label_fraction@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=none) | 0 |
| CAND-ea7b2fe887f6420a | cost_aware_rar_gate.gate2_value_of_waiting@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-4052a46c11559798 | cost_aware_rar_gate.gate2_value_of_waiting@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=none) | 0 |
| CAND-a0cbd8d902074554 | cost_aware_rar_gate.gate3_recovery_gain@rar[rar.gate3] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=none) | 0 |
| CAND-dc0eebf34c7be4e9 | cost_aware_rar_gate.gate2_recovery_aware@rar[rar.gate2] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=none) | 0 |
| CAND-473b6d18fb6287a7 | cooldown_hold_release.cost_scaled_cooldown@rar[rar.config] | DUPLICATE/CAND-c4d268f87c7835d6 | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-5d3af34101a25c54 | cooldown_hold_release.cost_scaled_cooldown@drift2act[d2a.config] | DISCARD | none | S4a (never_switch) +187.75 [+170.99, +203.15] | False | no validity claim (null=economic) | 0 |
| CAND-a76d0be6041edef2 | fresh_post_switch_evidence.paired_pre_post_evidence@contract_native[contract.switch_policy] | DISCARD | substantial | S1a (never_switch) -115.70 [-132.75, -100.05] | True | false_rollback_rate_given_promotion_under_keep_null 116/157 (0.739), CP95 upper 0.796, screen-level | 2 |
| CAND-3b3a6cf5cdc45188 | voi_acquisition.voq_certificate_state@drift2act[d2a.request_size] | DISCARD | none | S1a (never_switch) +17.99 [+14.79, +21.20] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-d1cc903e40ec4cdb | voi_acquisition.voq_release_survival@drift2act[d2a.request_size] | DUPLICATE/CAND-3b3a6cf5cdc45188 | none | S1a (never_switch) +17.99 [+14.79, +21.20] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-0b0837b7f4f60e31 | voi_acquisition.voq_certificate_state@drift2act[d2a.request_size] | DUPLICATE/CAND-3b3a6cf5cdc45188 | none | S1a (never_switch) +17.99 [+14.79, +21.20] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-0b53e5d559e9bb8f | voi_acquisition.voq_release_survival@drift2act[d2a.request_size] | DISCARD | none | S1a (never_switch) +17.79 [+14.59, +21.03] | True | abs_risk_certificate_violation_rate 0/300 (0.000), CP95 upper 0.010, screen-level | 0 |
| CAND-3296f01d0fb7b330 | hazard_regime_duration.regime_age_dependent_query_rate@rar[rar.label_request] | DISCARD | none | S4a (never_switch) +2.68 [+2.65, +2.70] | True | no validity claim (null=economic) | 0 |
| CAND-af27e802d5bbf9c1 | voi_acquisition.voq_release_survival@rar[rar.label_request] | DISCARD | none | S4a (never_switch) +2.64 [+2.60, +2.68] | True | no validity claim (null=economic) | 0 |
| CAND-3b3896e00eafef30 | hazard_regime_duration.hazard_survival_for_voq@rar[rar.label_request] | DUPLICATE/CAND-af27e802d5bbf9c1 | none | S4a (never_switch) +2.64 [+2.60, +2.68] | True | no validity claim (null=economic) | 0 |
| CAND-6cab5c6ebb407add | hazard_regime_duration.regime_age_dependent_query_rate@rar[rar.label_request] | DISCARD | none | S4a (never_switch) +2.68 [+2.65, +2.70] | True | no validity claim (null=economic) | 0 |
| CAND-dd7417133d1352a8 | hazard_regime_duration.hazard_survival_for_voq@drift2act[d2a.request_size] | DISCARD | none | S4a (never_switch) +187.70 [+170.94, +203.10] | False | no validity claim (null=economic) | 0 |
| CAND-fc8eb8f5495e9a46 | hazard_regime_duration.regime_age_dependent_query_rate@rar[rar.label_request] | DUPLICATE/CAND-3296f01d0fb7b330 | none | S4a (never_switch) +2.68 [+2.65, +2.70] | True | no validity claim (null=none) | 0 |
| CAND-464eddb00dd3f45f | hazard_regime_duration.hazard_survival_for_voq@rar[rar.label_request] | DUPLICATE/CAND-af27e802d5bbf9c1 | none | S4a (never_switch) +2.64 [+2.60, +2.68] | True | no validity claim (null=economic) | 0 |
| CAND-a6635384e674f5bd | risk_cost_aware_promotion.label_cost_net_promotion@cost_aware_binary[cab.gate] | DISCARD | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-ccc5b64f4f3f25c7 | replacement_economic_thresholds.switch_cost_amortisation@cost_aware_binary[cab.gate] | DISCARD | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |
| CAND-3223e705cdbe3c4e | replacement_economic_thresholds.switch_cost_amortisation@cost_aware_binary[cab.gate] | DISCARD | none | S4a (never_switch) +2.50 [+2.50, +2.50] | True | no validity claim (null=economic) | 0 |

# Scope (iii): Q1 evidence identities in the evidence promoter shell (v1 Q1 row + compatible v2 cells)

## Decision counts

CRASH=10, DISCARD=27, DUPLICATE=11

## KEEP and near-KEEP

KEEP = section 4 satisfied under A1. near-KEEP = DISCARD only through the control-cell / host-ablation / complexity / simple-control criteria: valid under its claimed null, not invalid-aggressive, and an effect label other than 'none' on its best target cell against the per-cell strongest applicable comparator. dJ = J(candidate) - J(comparator), negative = candidate better, 95% paired bootstrap CI.

| decision | candidate | method | best target cell (comparator) | dJ [95% CI] | effect | validity (claimed null) | failed checks |
|---|---|---|---|---|---|---|---|
| DISCARD | CAND-554673b35895b8a4 | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -50.15 [-97.65, -2.75] | meaningful (rel +0.095) | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | worse/overspend on neighbouring or negative-control cell |
| DISCARD | CAND-7862c5cfe5aa62f3 | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -48.45 [-95.50, -1.15] | meaningful (rel +0.092) | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | worse/overspend on neighbouring or negative-control cell |
| DISCARD | CAND-0c6c168c019f555d | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -69.85 [-127.77, -11.60] | substantial (rel +0.132) | false_promotion_rate 7/160 (0.044), CP95 upper 0.081, screen-level | worse/overspend on neighbouring or negative-control cell |
| DUPLICATE | CAND-0de97ac96627107d | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -48.45 [-95.50, -1.15] | meaningful (rel +0.092) | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | worse/overspend on neighbouring or negative-control cell |
| DUPLICATE | CAND-af5957d8eafd33a0 | hazard_regime_duration.semi_markov_duration_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -48.45 [-95.50, -1.15] | meaningful (rel +0.092) | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | worse/overspend on neighbouring or negative-control cell |
| DUPLICATE | CAND-b8629b81b7df50ff | hazard_regime_duration.semi_markov_duration_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -50.15 [-97.65, -2.75] | meaningful (rel +0.095) | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | worse/overspend on neighbouring or negative-control cell |
| DUPLICATE | CAND-0369028b27c4e9c6 | hazard_regime_duration.semi_markov_duration_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -50.15 [-97.65, -2.75] | meaningful (rel +0.095) | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | worse/overspend on neighbouring or negative-control cell |
| DISCARD | CAND-535bb9e297b2660b | restart_mixture_allocation.e_cusum_markov_base@drift2act[d2a.evidence_log_lik] via evidence promoter shell | Q1_2:markov05_shift_d10 (thinned_hedged_gate) | -48.35 [-93.95, -1.74] | meaningful (rel +0.091) | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | worse/overspend on neighbouring or negative-control cell |

## Q1 simple-control reading (section 4 item 4: vs Markov-LR and the gap-10 thinned gate, target cells)

* Records with a v2 result: 27; candidates whose paired CI is entirely below 0 against BOTH markov_lr_gate and thinned_hedged_gate simultaneously on at least one (the same) target cell: **16**.

| candidate | method | decision | winning target cell vs markov_lr_gate (dJ [95% CI]) | vs thinned_hedged_gate |
|---|---|---|---|---|
| CAND-554673b35895b8a4 | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -103.20 [-125.40, -82.60] | S2d -128.60 [-163.96, -97.95] |
| CAND-7862c5cfe5aa62f3 | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | Q1_2 -156.30 [-197.45, -115.15] | Q1_2 -48.45 [-95.50, -1.15] |
| CAND-394c3ded5229b4e4 | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -68.85 [-96.30, -42.39] | S2d -94.25 [-134.50, -58.25] |
| CAND-6c9be3173d82efd6 | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S1a -10.00 [-21.35, -0.15] | S1a -10.00 [-21.35, -0.15] |
| CAND-0c6c168c019f555d | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | Q1_2 -177.70 [-221.40, -133.90] | Q1_2 -69.85 [-127.77, -11.60] |
| CAND-37c1100fe1a7d17e | conditional_marginal_objective_selection.dependence_test_router@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -68.20 [-96.70, -40.05] | S2d -93.60 [-133.65, -57.95] |
| CAND-51f2e4dad5e15ef5 | conditional_marginal_objective_selection.dependence_test_router@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -54.80 [-89.70, -18.45] | S2d -80.20 [-128.11, -34.95] |
| CAND-52260c4efc649d06 | actual_gap_evidence.gap_tempered_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -41.10 [-65.90, -18.55] | S2d -66.50 [-107.80, -30.85] |
| CAND-fb712b6b1deb6149 | markov_transition_envelopes.plugin_slack_inflation@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -67.35 [-93.32, -41.95] | S2d -92.75 [-132.65, -56.59] |
| CAND-47d3c4e3c12c9d0d | actual_gap_evidence.gap_bucketed_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -71.60 [-98.75, -45.65] | S2d -97.00 [-136.21, -61.64] |
| CAND-510767b8188904ea | markov_transition_envelopes.interval_uncertainty_set@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -27.70 [-57.16, -0.10] | S2d -53.10 [-94.61, -16.00] |
| CAND-550994fbd7bade22 | actual_gap_evidence.exact_Pg_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -57.55 [-87.75, -28.65] | S2d -82.95 [-125.50, -44.25] |
| CAND-9df9bf5c228629d1 | markov_transition_envelopes.dirichlet_mixture_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -71.55 [-98.70, -45.65] | S2d -96.95 [-136.21, -61.59] |
| CAND-fc1224a62c726920 | markov_transition_envelopes.lfd_envelope@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -71.55 [-98.70, -45.65] | S2d -96.95 [-136.21, -61.59] |
| CAND-57be9b676b8d010b | restart_mixture_allocation.truncated_restart_window@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -65.95 [-97.65, -33.30] | S2d -91.35 [-139.55, -47.60] |
| CAND-535bb9e297b2660b | restart_mixture_allocation.e_cusum_markov_base@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | S2d -102.35 [-125.05, -81.60] | S2d -127.75 [-164.35, -96.50] |

## All records

| candidate | method | decision | effect | best target cell (comparator) dJ [95% CI] | beats VALID-applicable simple controls (vacuously True if none valid) | validity | v1-regression |
|---|---|---|---|---|---|---|---|
| CAND-394c3ded5229b4e4 | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s wall-clock hard limit (process killed) | - | - | - |
| CAND-6c9be3173d82efd6 | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s wall-clock hard limit (process killed) | - | - | - |
| CAND-0293464ca33d03a7 | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s wall-clock hard limit (process killed) | - | - | - |
| CAND-554673b35895b8a4 | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | meaningful | Q1_2 (thinned_hedged_gate) -50.15 [-97.65, -2.75] | True | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | 0 |
| CAND-7862c5cfe5aa62f3 | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | meaningful | Q1_2 (thinned_hedged_gate) -48.45 [-95.50, -1.15] | True | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | 0 |
| CAND-da01042591756ac5 | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s wall-clock hard limit (process killed) | - | - | - |
| CAND-db08bb3b67d2379b | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s wall-clock hard limit (process killed) | - | - | - |
| CAND-0c6c168c019f555d | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s wall-clock hard limit (process killed) | - | - | - |
| CAND-394c3ded5229b4e4 | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -41.65 [-97.91, +11.96] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-6c9be3173d82efd6 | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -33.05 [-85.87, +19.30] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-0293464ca33d03a7 | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -0.15 [-57.47, +55.40] | True | false_promotion_rate 0/180 (0.000), CP95 upper 0.017, screen-level | 0 |
| CAND-da01042591756ac5 | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-0293464ca33d03a7 | none | Q1_2 (thinned_hedged_gate) -0.15 [-57.47, +55.40] | True | false_promotion_rate 0/160 (0.000), CP95 upper 0.019, screen-level | 0 |
| CAND-db08bb3b67d2379b | conditional_marginal_objective_selection.dual_null_reporting@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-6c9be3173d82efd6 | none | Q1_2 (thinned_hedged_gate) -33.05 [-85.87, +19.30] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-0c6c168c019f555d | conditional_marginal_objective_selection.min_of_both_certificate@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | substantial | Q1_2 (thinned_hedged_gate) -69.85 [-127.77, -11.60] | True | false_promotion_rate 7/160 (0.044), CP95 upper 0.081, screen-level | 0 |
| CAND-0de97ac96627107d | hazard_regime_duration.geometric_hazard_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-7862c5cfe5aa62f3 | meaningful | Q1_2 (thinned_hedged_gate) -48.45 [-95.50, -1.15] | True | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | 0 |
| CAND-37c1100fe1a7d17e | conditional_marginal_objective_selection.dependence_test_router@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -47.25 [-105.70, +8.20] | True | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | 0 |
| CAND-af5957d8eafd33a0 | hazard_regime_duration.semi_markov_duration_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-7862c5cfe5aa62f3 | meaningful | Q1_2 (thinned_hedged_gate) -48.45 [-95.50, -1.15] | True | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | 0 |
| CAND-b8629b81b7df50ff | hazard_regime_duration.semi_markov_duration_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-554673b35895b8a4 | meaningful | Q1_2 (thinned_hedged_gate) -50.15 [-97.65, -2.75] | True | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | 0 |
| CAND-e71abfeebc0f3ec6 | conditional_marginal_objective_selection.dependence_test_router@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-37c1100fe1a7d17e | none | Q1_2 (thinned_hedged_gate) -47.25 [-105.70, +8.20] | True | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | 0 |
| CAND-0369028b27c4e9c6 | hazard_regime_duration.semi_markov_duration_prior@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-554673b35895b8a4 | meaningful | Q1_2 (thinned_hedged_gate) -50.15 [-97.65, -2.75] | True | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | 0 |
| CAND-51f2e4dad5e15ef5 | conditional_marginal_objective_selection.dependence_test_router@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -47.25 [-105.70, +8.20] | True | false_promotion_rate 2/180 (0.011), CP95 upper 0.035, screen-level | 0 |
| CAND-52260c4efc649d06 | actual_gap_evidence.gap_tempered_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -37.95 [-95.91, +18.01] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-56925e1ab06b5edd | actual_gap_evidence.gap_tempered_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | S1a (rmm_detector) -7.90 [-19.90, +3.20] | True | false_promotion_rate 0/180 (0.000), CP95 upper 0.017, screen-level | 0 |
| CAND-f1836f8276a847d2 | markov_transition_envelopes.plugin_slack_inflation@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | S4a (markov_lr_gate) +0.00 [+0.00, +0.00] | False | false_promotion_rate 0/180 (0.000), CP95 upper 0.017, screen-level | 0 |
| CAND-fb712b6b1deb6149 | markov_transition_envelopes.plugin_slack_inflation@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -38.25 [-86.97, +11.55] | True | false_promotion_rate 1/160 (0.006), CP95 upper 0.029, screen-level | 0 |
| CAND-1b19e808fa8d2318 | markov_transition_envelopes.plugin_slack_inflation@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-fb712b6b1deb6149 | none | Q1_2 (thinned_hedged_gate) -38.25 [-86.97, +11.55] | True | false_promotion_rate 1/160 (0.006), CP95 upper 0.029, screen-level | 0 |
| CAND-279a24b1c07a36f4 | actual_gap_evidence.gap_tempered_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | S1a (rmm_detector) -7.90 [-19.90, +3.20] | True | false_promotion_rate 0/180 (0.000), CP95 upper 0.017, screen-level | 0 |
| CAND-43c6c4c6277059ff | markov_transition_envelopes.interval_uncertainty_set@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | S4a (markov_lr_gate) +0.00 [+0.00, +0.00] | False | false_promotion_rate 0/180 (0.000), CP95 upper 0.017, screen-level | 0 |
| CAND-47d3c4e3c12c9d0d | actual_gap_evidence.gap_bucketed_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -48.25 [-97.85, +3.40] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-510767b8188904ea | markov_transition_envelopes.interval_uncertainty_set@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | S4a (markov_lr_gate) +0.00 [+0.00, +0.00] | True | false_promotion_rate 0/160 (0.000), CP95 upper 0.019, screen-level | 0 |
| CAND-8c574923fa678300 | actual_gap_evidence.gap_bucketed_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -10.95 [-67.56, +46.91] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-0cd8fe5f70a6fbe5 | actual_gap_evidence.gap_bucketed_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -12.95 [-69.21, +44.66] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-0e9e0ffe6180231b | markov_transition_envelopes.interval_uncertainty_set@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | S4a (markov_lr_gate) +0.00 [+0.00, +0.00] | False | false_promotion_rate 0/160 (0.000), CP95 upper 0.019, screen-level | 0 |
| CAND-1141ad25465c0c09 | actual_gap_evidence.exact_Pg_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-394c3ded5229b4e4 | none | Q1_2 (thinned_hedged_gate) -41.65 [-97.91, +11.96] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-1680d66857549adb | markov_transition_envelopes.dirichlet_mixture_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -10.45 [-67.25, +48.06] | True | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | 0 |
| CAND-550994fbd7bade22 | actual_gap_evidence.exact_Pg_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -33.85 [-87.11, +18.15] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-9df9bf5c228629d1 | markov_transition_envelopes.dirichlet_mixture_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -48.25 [-97.85, +3.40] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-c8f369d6bb29f8d9 | markov_transition_envelopes.lfd_envelope@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -32.15 [-83.30, +21.56] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-fc1224a62c726920 | markov_transition_envelopes.lfd_envelope@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -52.25 [-104.10, +0.65] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-0fca2006edfeb4d6 | actual_gap_evidence.exact_Pg_kernel@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-550994fbd7bade22 | none | Q1_2 (thinned_hedged_gate) -33.85 [-87.11, +18.15] | True | false_promotion_rate 1/180 (0.006), CP95 upper 0.026, screen-level | 0 |
| CAND-27c41ba751d6ca57 | markov_transition_envelopes.lfd_envelope@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DUPLICATE/CAND-fc1224a62c726920 | none | Q1_2 (thinned_hedged_gate) -52.25 [-104.10, +0.65] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-7581504c54f5e3a1 | markov_transition_envelopes.dirichlet_mixture_evidence@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -10.95 [-67.56, +46.91] | True | false_promotion_rate 3/180 (0.017), CP95 upper 0.043, screen-level | 0 |
| CAND-57be9b676b8d010b | restart_mixture_allocation.truncated_restart_window@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | none | Q1_2 (thinned_hedged_gate) -23.05 [-75.91, +31.25] | True | false_promotion_rate 3/160 (0.019), CP95 upper 0.048, screen-level | 0 |
| CAND-ba2574e0f9346865 | restart_mixture_allocation.truncated_restart_window@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s active compute (cpu_cap; cpu_s=300.2); process killed | - | - | - |
| CAND-513a2ac3c5be3dc3 | restart_mixture_allocation.truncated_restart_window@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s active compute (cpu_cap; cpu_s=300.7); process killed | - | - | - |
| CAND-535bb9e297b2660b | restart_mixture_allocation.e_cusum_markov_base@drift2act[d2a.evidence_log_lik] via evidence promoter shell | DISCARD | meaningful | Q1_2 (thinned_hedged_gate) -48.35 [-93.95, -1.74] | True | false_promotion_rate 2/160 (0.013), CP95 upper 0.039, screen-level | 0 |
| CAND-b8dab053ecb90cc0 | restart_mixture_allocation.e_cusum_markov_base@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s active compute (cpu_cap; cpu_s=301.0); process killed | - | - | - |
| CAND-11bf475bee8d9d13 | restart_mixture_allocation.e_cusum_markov_base@drift2act[d2a.evidence_log_lik] | CRASH | - | timeout: exceeded 300s active compute (cpu_cap; cpu_s=300.9); process killed | - | - | - |

## Run notes and A1 interpretation choices (read before using the numbers)

* Strongest applicable comparator = per cell, lowest mean J among comparators whose promotion rate on the candidate's validity cells (cells where its claimed null holds) is <= 0.10; the host is subject to the same filter. Candidates claiming no null (economic/none) face all comparators. `never_switch` is a comparator, so on null cells and on several alternative cells it is the strongest and every label-spending candidate is compared with it.
* The registered Gap-Mix `exact0.8_s4` adapter declares claimed null `marg` (A1 text says conditional-null); on all v2 cells cond and marg truths coincide, so no comparator validity decision depends on this.
* Control-cell regression (section 4 item 2) is evaluated against the same per-cell strongest comparator, as registered; this is a strict test (never_switch is cheapest on null cells).
* Suite-v2 hosts are `calibrated_v1`; one `native_v0` host run per cell is stored in each record (`results.native_v0_reference`), never used as a comparator. A candidate worse than its host on a v1 cell it ran on (paired CI above 0) is not KEEP; the tranche-1 records are the source.
* Scope (i-ii) 33+14 flags overlap on 6 identities (`scope: [i, ii]`). Canary identities need the family 'RAR-native persistent drift' that v2 does not provide: they stay UNVERIFIED by construction.
* Reference runs were sharded into seed chunks of 2 (paired runs are independent per seed, so concatenation equals one run). Gap-Mix `exact0.8_s4` took up to ~11 CPU-minutes per seed on S2c (cap = T, lognormal delay) and emits numerical RuntimeWarnings (divide by zero / overflow in `sota/inrepo/gapmix.py`) on some cells; the adapter is frozen and was not changed.
* Cache keys use a code hash pinned at launch (`SHIFTLAB_STAGE_B_CODE_HASH`). Another agent added the opt-in Q1 evidence seam to `adapters_drift2act.py` in the same worktree during the run; the default path is unchanged (its golden test passes), and the hash at launch covers the pre-seam sources.
* Scope (iii) cap: after a first launch measured the 300 s limit on wall-clock under 12-way contention, 6 early CRASH records (wall-clock timeouts, identities `dual_null_reporting` and `min_of_both_certificate`) were appended; the experiment cap was then measured as 300 CPU seconds of the worker process tree (a 16-cell experiment needs 40-270 CPU-s alone) and those identities were re-run and decided (CRASH records stay in the ledger). Four `restart_mixture_allocation` identities exceed 300 CPU-s and are CRASH (cpu_cap) - retryable only with a larger cap or fewer cells, which A1 does not allow.
* Scope (iii) cells: the v1 section-3 Q1 row (4 cells) plus the 12 v2 cells with label_cap < T and no informative delay/missingness (S2a-c have cap = T, i.e. a degenerate gap schedule). Shell = `adapters_evidence.promoter_adapter`, calendar schedule, alpha 0.1. The Drift2Act-host run with the identity's evidence is reported only for two v1 cells (`results.descriptive_drift2act_host_runs`) and is OUT_OF_CONTRACT for validity. Scope (iii) fully reports every `required_baselines` entry outside the registered Q1 comparator set in `required_baselines_outside_scope_iii_set`.

Ledger: `docs/d2a_rar/registry/EXPERIMENT_LEDGER.jsonl`; logs: `results/d2a_rar/stage_b/stage_b_t2_run.log`, `stage_b_t2_iii_run.log`.
