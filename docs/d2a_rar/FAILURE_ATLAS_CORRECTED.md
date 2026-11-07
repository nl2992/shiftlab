# Failure Atlas, corrected for null mismatch (WP0 draft)

Branch `research/drift2act-rar-autoresearch-2026-11-07`, written 2026-11-07. Status: **development
knowledge only**; nothing here is confirmatory except the two rows marked CONFIRMED (scoped).
Machine-readable companions: [registry/failure_ledger.jsonl](registry/failure_ledger.jsonl) (55 rows,
every number a verbatim quote re-checked against `git show`), [registry/null_assumptions.yaml](registry/null_assumptions.yaml)
(29 entries), validator `scripts/d2a_rar/validate_registry.py --verify-quotes`.

Source refs (all read with `git show`, nothing checked out): **MAIN** = `main@7354480a`;
**GV** = `origin/research/gave-r-2026-11-06@03289d1d`; **SL** = `origin/claude/sweet-lovelace-pznpjq@c53f6459`;
**CO** = `research/continuation-2026-11-04@10a8e808`; **SC** = `origin/codex/scoped-method-research-results-2026-11-06@a9d5c3cd`.
Row ids `FL-nnn` are ledger ids.

## 1. The correction in one paragraph

Several Atlas, Sprint-1 and GAVE-R measurements scored a **conditional-null** method (`E[d_t | F_{t-1}] <= 0`,
`d_t = l(I(X_t),Y_t) - l(C(X_t),Y_t)`) by its **marginal-null** false-promotion rate (stationary or
exchangeable null with serial dependence or a per-split fixed effect). The repository itself documents this:
Atlas cycle 6 ("the cycle-6 null is therefore outside the gates' conditional-null contract whenever rho > 0",
FL-006), the GAVE-R harness map ("'gated' in the code means 'has an e-process shell', not 'valid under
dependence'", FL-028), Sprint-2 `bench2.py` ("each method is scored only against the null it actually tests",
FL-032), the P2 adversarial review ("Null-class mismatch (central)", FL-034) and the P2 controls, where under
the exact per-event conditional null (ESWAP) **0 of 10** certified ports exceed the .0936 bound (FL-035).
The honest reading is therefore: those rows are **out-of-contract stress maps**, not refutations of any
published guarantee. What survives the correction is listed in section 4.

Null classes used throughout (`d_t` as above):

| code | requirement | ShiftLab label | typical owner |
|---|---|---|---|
| cond | `E[d_t | F_{t-1}] <= 0` on a stated filtration | V1 | e-process gates (episode_*, DSS evidence, certified ports, RMM, H2c, QSG, E_rb) |
| marg | `E[d_t] <= 0`, or a parametric process null (stationary Markov, exchangeable twin) | V2 | Markov-LR, Gap-Mix, A5b/A1b/D5, Sethi et al., ASI (estimand) |
| absolute_risk | `R_t <= tau` for one model | - | Drift2Act certificate, PPRM |
| economic | expected deployment value after all costs | V3 | Challenger GSE/OSE/LSE, economic_replacement, RAR objective |
| none | no validity claim | none | Page-CUSUM, PAVE, uncertified selectors, controls |

## 2. Counts

55 ledger rows (49 from WP0 + 6 from WP0b, section 3E). WP0 breakdown: 32 negative, 11 correction, 2 narrow positive, 2 theory-closed, 2 applicability; WP0b adds 4 negative, 1 correction, 1 theory-closed. Status: 52 development, 3 confirmed (scoped; FL-036, FL-047, FL-052). Null-mismatch flag: **13** (WP0) + 1 (WP0b, FL-054) measurements where a marginal-null rate was charged
against a conditional-null method (`yes`, original measurement), **4** (WP0) + 1 (FL-055) partial (valid-vs-invalid pairs or
mixed-null comparisons), **4** `yes`-flagged rows that are the corrections themselves (FL-028, FL-035,
FL-036, FL-037), 14 `no`, 13 not applicable, 1 unclear (secondary source).

## 3. Corrected failure table

Columns: **Measured under** = the null the number was computed against; **Own null** = what the method's
guarantee concerns (registry); **Flag** = mismatch. Evidence level: DEV = development/exploratory
(registered or not, but seeds exposed or tuned), CONF = frozen-protocol confirmation (scoped).

### 3A. Rows where a marginal-null false-promotion rate was charged against a conditional-null method (the P2 error)

| Ledger | Failure mode | Number copied (source) | Measured under | Own null | Corrected reading | Level |
|---|---|---|---|---|---|---|
| FL-004 | Straddle unsafe at d=1 under dependence | 0.130 (rho .5, B/T .05) and 0.475 (rho .8, B/T .05) vs 0.005 / 0.000 uniform ablation (MAIN `docs/failure_atlas_v1_ledger.md` cycle 6) | marg (Markov boundary twin) | cond | Contract violation; straddle valid only when outcomes are conditionally independent given regime. Keep as dependence-stress map; not "unsafe method". | DEV |
| FL-006 | Dense correlated labels inflate e-process gates | episode_front 382/400 = 0.955 [0.930,0.971]; episode_equal 162/400 = 0.405 [0.358,0.454] at rho .8, B/T .5 (MAIN ledger cycle 6) | marg | cond | Atlas verdict: "a diagnostic, not a discovery"; gates run outside their contract. | DEV |
| FL-007 | c1_hmm_cs fails under dependence | 0.960 (rho .5, B/T .25, d=1); 0.172 (rho .8) (MAIN ledger cycles 5-6) | marg | cond given regime (iid emissions assumed) | Assumption violation of the emission model, same error family. | DEV |
| FL-008 | Cycle 5 families 3/4 | Every e-process baseline <= 0.085 despite rho>0; I1 failed (MAIN ledger cycle 5) | marg | cond | The non-failure is explained by sparse sampling, not conditional validity; V3 (release order) later FAILED. | DEV |
| FL-009 | DSS cycle-7 A3 safety | DSS null freq .065 to .39 at rho=.8, .44 to .975 at rho=.95 for B/T<=.25 (MAIN `failure_atlas_cycle7_decision_v1.md`) | marg | cond | A3 charged a conditional gate with a dependent marginal null; the registered cost result A1 is unaffected. Safety at rho>0 is a gap-4 mitigation, not validity. | DEV |
| FL-011 | Fallback gap-4 repair | 11/40 DSS vs 12/40 with fallback gap at rho .8, B/T .25, d 10 (MAIN `failure_atlas_cycle7_followup_results_v1.md`) | marg | cond | Same mismatch; repair also confounds spacing with sample count (500 -> 245 requests). | DEV |
| FL-020 | iid/DSS evidence miscalibrated | DSS evidence UCB 0.269 (rho .8, B/T .1, d 1), 0.395 (rho .8, B/T .25, d 10), 0.983 (rho .95); iid gate .542 / .997 (GV `90_SUMMARY.md`) | marg | cond | Out-of-contract stress; the GAVE-R authors call it descriptive, not a new method. | DEV |
| FL-023 | PAVE "null UCB" | <= 0.0283 (reserve on) / <= 0.0586 (reserve off) at rho<=.8; DSS up to 0.269 (GV `90_SUMMARY.md`) | marg | cond (inherited) | An empirical stress rate for conditional evidence; "safer than DSS" is mainly fewer promotions. | DEV |
| FL-024 | Delay-gated PAVE null | raw PAVE worst UCB 0.039 (DSS 0.196) at rho<=.8; .468 at rho .95 (GV `90_SUMMARY.md`) | marg | cond (inherited) | Same; the 4.4% cost gain is a cost result, not a null measurement. | DEV |
| FL-032 | Sprint-1 P2 headline | "9/9 powered ports break the bound"; A5b below it (SL `m3_RESULT_TO_CLAIM.md`); `bench2.NULL_TESTED`: gated_*, discern, SMCS, Choe-Ramdas, QSG, D2, RMM = V1; A5b, A1b, D5 = V2 | marg (V2 stationary Markov, bound .0936) | cond (V1) for all but A5b/A1b/D5 | **The P2 error.** The A5b "robustness" headline compares a V2-targeting method with V1 methods on the V2 null. | DEV |
| FL-034 | P2 twin known-null streams | SMCS 0.428 [0.339,0.511], Xu 0.375, Choe-Ramdas 0.336 on appliances (SL `candidate_registry_v2.md`) | marg (twin, per-split effect + dependence) | cond | Review finding 1: twin null holds only over split/role coins, so promoting a realised-better twin is not a false promotion under the conditional guarantee. | DEV |
| FL-038 | QSG / front-loaded hosts | rho=.8 Markov null .13-.32 vs .094 bound (QSG .32); SMCS .13, P7s .12 (SL `failure_atlas_v2_flq/results/REPORT.md`) | marg | cond ("valid under the pointwise conditional null via Ville") | Atlas-v2 instance of the P2 error; Amendment-2 "strict certification" failure is a V2 reading. | DEV |
| FL-042 | RMM twin/dependence nulls | rho=.8 null .12-.18, rho=.95 ~.71 "as declared"; twin-null elevated up to .62 (SL `sota_sprint/REPORT.md`, `m3_RESULT_TO_CLAIM.md`) | marg | cond (V1) | Declared out-of-contract by the authors in advance; the twin figure is a V2 reading of a V1 method. | DEV |

### 3B. Partial mismatches (valid-conservative vs invalid-aggressive pairs, mixed nulls)

| Ledger | Failure mode | Number copied (source) | Issue |
|---|---|---|---|
| FL-012 | Amendment-9 pilot | DSS null FP "reached 1.00 under strong dependence"; Markov LR "no promotions in 10/11 alternative cells" (MAIN `failure_atlas_review_2026_11_01.md`) | Markov-LR is scored on its own marg null, DSS on one it does not target; mandate Phase 7 forbids ranking invalid-aggressive vs valid-conservative as equal. |
| FL-013 | Paper-1 stratified evidence | candidate equals Chugg-style subgroup composition to 4.4e-16; ratio <= 1.000 vs required 1.5 (MAIN `algorithm_search_exit_ledger.md`) | Stratified "wins" change the null to the intersection null. |
| FL-030 | Integrated GAVE-R | Gap-Mix worst UCB 0.051 / 0.055 (rho<=.8) vs frozen DSS evidence 0.395 (GV `90_SUMMARY.md`) | Gap-Mix arms scored on their own marg null; the DSS arm is the mismatched one. Cost results unaffected. |
| FL-046 | Sprint-1 validation | H0 FAIL (1/6); H1 part 3 FAIL (1/5); HR 3/5 (SL `sota_sprint/REPORT.md`) | H1 parts 1-2 safety claims use the V2 null and inherit FL-032. |

### 3C. Corrected measurements (use these, not 3A)

| Ledger | What it measures | Numbers copied (source) | Level |
|---|---|---|---|
| FL-035 | P2 attribution controls on 5 UCI streams x 10 certified ports | ORIG breaks 9/10 (25 cells, promote .121/.428, harmful .0098/.072); PERM 9/10 (promote .082/.292, harmful .0001/.0017); BSWAP 7/10 (promote .068/.242, harmful .0084/.069); **ESWAP (exact conditional null) 0/10**, promote .003/.040, harmful .0003/.008 (SL `DISCOVERY_DECISION.md`) | DEV (exposed streams; MOPE code-fix replay pending) |
| FL-036 | Frozen harm-split confirmation on 3 new UCI streams | HC1 Delta = 0.00536 [0.00234, 0.00896]; H_PERM = 0 (0 harmful promotions in 19,200 runs); P_BSWAP = 0.0776 [0.0646, 0.0916]; pooled promote/harmful ORIG .189/.0021, BSWAP .078/.0054 (SL `P2_HARM_CONFIRMATION_RESULTS.md`) | **CONF (scoped to the twin construction, block length 100, common-contract ports)** |
| FL-037 | Sprint-2 P2: V2 vs V1 error on p<=.5 null episodes (columns V2 / V1) | A5b 0/0; gated_adaptive_range+front .175/.067; RMM (gated) .308/.125; D2 .308/.142; QSG .358/.183; P3_follow 1.0/.60 (SL `sprint2/family_p/P2P3_objectives_harm.md`) | DEV (12 seeds/setting) |
| FL-033 | Rule | "A V1 rate is never compared with a V2 rate as if the two tested the same hypothesis." (SL `sprint2/wp2/BENCHMARK.md`) | rule |

### 3D. Failures whose measurement is not null-mismatched (cost, power, latency, closed theory)

| Ledger | Failure mode | Numbers copied (source) | Null at issue | Level |
|---|---|---|---|---|
| FL-001 | Family-1 gap is mostly cost of validity | 116 of 123 cycle-2 shared failures reclassified `cost_of_validity`; best composition closed 48% (MAIN ledger cycle 2-3) | cond | DEV |
| FL-002 | Exact cost of validity | RC > CoV in 0 of 144 solved cells (T<=8); T=1000 open (MAIN ledger cycle 5) | cond | DEV |
| FL-003 | Straddle gain is delay-governed | family 1 +0.0024 [-0.0012,+0.0061], family 2 +0.0047 [-0.0000,+0.0095]; helps when d < d* (MAIN ledger cycle 4) | - | DEV |
| FL-005 | triggered_kelly | onset-0.1 gain +0.0411; known start-multiplicity trade-off (MAIN ledger cycle 4) | - | DEV |
| FL-009 (cost part) | DSS cost regressions | long-delay family-1 +.01283 per round; rho=0 earlier-onset B/T .1 cell +.06451; neighbourhoods +.01539 and +.03867 (MAIN cycle-7 decision) | - | DEV |
| FL-010 | DSS additions not isolated | uniform acquisition removes 155.5% of gain; delay switch removes 2.58% (MAIN cycle-7 decision) | - | DEV |
| FL-014 | Deadline-aligned acquisition = belief-state control approximation | killed before implementation (CO `g1_deadline_aligned_acquisition_kill_v1.md`) | economic | theory |
| FL-015 | Lane B D2 split clock | triggered burst worse than two-phase in 8/9 cells by 3.9-7.5 units (CO `D2_split_clock_mechanism.md`) | cond | DEV |
| FL-016 | Exact-gap Markov SUI (dense and sparse start) | cost vs Markov LR +0.0102 [+0.0041,+0.0162] / +0.0059 [+0.0004,+0.0114]; adverse cell vs episode_front +0.2406 / +0.2459 (CO `failure_atlas_gap_markov_sui_*_results_v1.md`) | marg (matched) | DEV |
| FL-017 | Joint acquisition+switching DP | 0 gap in 108 + 54 cells; gap <= 1.1% on 192 exact toy instances (SL `candidate_registry_v2.md`, `novelty_validation 11`; secondary) | economic | theory |
| FL-018 | H2c on a real reversal stream; MAG repair | alarms 242-824 events later than cost-only Kelly/ONS; MAG >= H2c in 13/30 harmful cells; MAG - H2c -0.0030 to -0.0095 in 9/20 cells (SL `novelty_validation 11`, `X3_MAG_RESULTS.md`) | cond | DEV (MAG gas arm in-sample) |
| FL-021 | Gap-Mix (narrow positive) | valid UCB <= 0.078 at declared rho_bar .8; fails at rho .95 (FP .87-1.00); detection +0.367 [.342,.394] vs Markov LR; 5.1% worse than invalid iid DSS (GV `90_SUMMARY.md`) | marg (matched) | DEV |
| FL-022 | Gap-Mix rho-robust extensions | best valid detection -0.059 [-.076,-.042] vs Markov LR; gain fraction -0.16 vs required >= 0.5; ELIMINATED (GV `90_SUMMARY.md`) | marg | DEV |
| FL-023 (cost part) | PAVE as a general governor | d<=10: 13 of 22 cells worse than DSS, 0 better; f3_rho0 d1 cell 16-19% worse (GV `90_SUMMARY.md`) | - | DEV |
| FL-024 (cost part) | Delay-gated PAVE niche | gate-on -0.0186 [-.0237,-.0137] (4.4% better); regression cell .4095 -> .3584; pooled 1.4% (GV `90_SUMMARY.md`) | - | DEV, post-hoc scope |
| FL-025 | FreshCheck | reversal harm 0.0527 vs Page-CUSUM 0.0094; mean J/T CUSUM .488, E_rb .489, FreshCheck .496, two-phase .518 (GV `90_SUMMARY.md`) | cond (matched) | DEV |
| FL-026 | Two-phase persistence | harm 0.0027 only because it almost never promotes (58/775 keep-null streams promoted) (GV `90_SUMMARY.md`) | cond | DEV |
| FL-027 | Heuristic rollbacks lack level control | Page-CUSUM / hysteresis / cost-threshold roll back in 772/773, 713/722, 706/775 vs FreshCheck 2/584, E_rb 1/775 (GV `90_SUMMARY.md`) | none (not a failed guarantee) | DEV |
| FL-029 | No object called E_rb in Atlas code; rollback is heuristic Page-CUSUM | (GV `01_HARNESS_MAP.md`) | none | code audit |
| FL-030 (cost part) | Integrated GAVE-R sub-additive | joint +0.0161 [+.0138,+.0186] vs DSS (4.2% worse); interaction -0.0064 [-.0106,-.0026] (GV `90_SUMMARY.md`) | - | DEV |
| FL-031 | Unrepaired regression cells | f3_rho0 d1: PAVE 16-19% worse, Gap-Mix 3.5% worse (.4101), episode_front better (.3415) (GV `90_SUMMARY.md`) | - | DEV |
| FL-039 | Atlas-v2 M1 certification latency; M2 uncertified churn | gated/DISCERN cost 426, 429 vs 419 never-switch on F0_better; uncertified promote 64-100% of nulls, +12 to +64 (SL `failure_atlas_v2_flq/results/REPORT.md`) | economic | DEV |
| FL-040 | Comparator-pool and implementation defects | adaptive-range ordering defect: 130 runs / 411 policy entries; H1 +68..+189, H2 +60..+203 ranges withdrawn; DISCERN dropped `/4` (SC `FAILURE_ATLAS_UPDATE.md`, SL `CLAIM_RECONCILIATION.md`) | n/a | corrections |
| FL-041 | H2 and R5 | H2 +67 to +84 vs D2 on persistent alternatives, +81.2 vs D2 on 14 real sources; R5 promotions 15/100, 26/100, 24/100 on three nulls (SL `sprint2/LEADERBOARD.md`) | marg for H2; empirical risk for R5 | DEV |
| FL-043 | Reversal headroom unclosed | vs never-switch on F3_reversal_1200: E_swcert +12.59 [8.69,16.49], E_rb +28.73 [19.92,37.54], RMM +33.70 [24.62,42.78], PFA-SR +40.73 [30.58,50.89], E-SR +18.87 [9.16,28.58]; evaluator-only oracle 84.13 below never-switch (SC `PHASE2_HEADROOM_RESULTS.md`) | cond + economic | DEV; decision BENCHMARK_OR_CASE_STUDY_ONLY |
| FL-044 | Aggressive switching; T-family hosts | delay=100 loss margins +14.0 to +669.5; T1 +43.4 vs Model Picker (SL `family_p/P2P3_objectives_harm.md`, `CLAIM_RECONCILIATION.md`) | economic | DEV |
| FL-045 | A5b power loss on real streams | cost +61 to +257 on real time series; K2 fails on bike_hour 0.058 [0.017,0.100]; HMM stress 176/1,000 (SL `sota_sprint/REPORT.md`, `DISCOVERY_DECISION.md`, `CLAIM_RECONCILIATION.md`) | marg (matched) | DEV |
| FL-047 | Uncertified selectors on the twin protocol | Model Picker .695-.931, CAMS .788-.962 promote rates; harmful in 24-46% of runs under every condition incl. ESWAP (SL `DISCOVERY_DECISION.md`, `P2_HARM_CONFIRMATION_RESULTS.md`) | none | CONF (scoped) / DEV |
| FL-019 | Decision-value track CF-S1 failed; PFA-SR HuffPost miss +289.91 [+193.64,+391.18] per 1000 events vs RMM | secondary citation only (SL `candidate_registry_v2.md`) | UNVERIFIED | primary docs not read |
| FL-048, FL-049 | Drift2Act and RAR: **no repo-measured failure**; never reproduced; abstract/secondary level only | (SL `SOTA_APPLICABILITY_REPORTS.md`; CO `versioned_dual_monitor_protocol.md`) | absolute_risk / none | n/a |

### 3E. WP0b additions (sources skipped in the first pass)

Source kinds: **MD2V** = `research/monitoring-to-decision-value-2026-10-30@a155ed6c`; **PD** =
`research/shiftlab-promising-directions-2026-10-30@673a2b79`; **HGXH** = `main-checkout-untracked:docs/hgxh2c/FINAL_REPORT.md`
(untracked file in the main checkout, generated from a dirty tree at 7354480a; verifier reads it from disk).

| Ledger | Failure mode | Numbers copied (source) | Null measured / own null | Flag | Level |
|---|---|---|---|---|---|
| FL-050 | HGxH2c search and Stage-4: scoped win only inside the anytime-valid family, loses to CUSUM/PH; A7 mechanism not run | registry rows 2055203; secondary family (CUSUM/PH) Holm p = 1.0, status = lost; primary Holm p = 0.0012496875781054738; negative control and E7-E9 marked DEFECTIVE_A7 (HGXH) | cond / cond (families kept separate, the corrected practice) | no | DEV |
| FL-051 | PPRM independent reproduction (synthetic only) | paired PPRM - SRM -313.7 steps vs paper about -40 / -30; adaptive - fixed -0.8 vs -11 to -21; PPE NOT_AVAILABLE (HGXH) | absolute_risk / absolute_risk | no | DEV, fidelity caveat |
| FL-052 | Monitoring-to-decision-value: better monitoring is small and conditional once controllers are tuned | four target cells +6.58 (LB 6.07) < MME 6.79 so CF-S1 FAILED; CF-S2 +1.87 (LB 1.35) passed, driven by 2 of 6 pairs; untuned reversals 16/1620, 0 matched in 23/24 tuned cells; real OPSD Part R: no alarm (value 0 vs MME 7.3) (MD2V `09`, `13`) | economic / economic | no | CONF (frozen one-shot; negative on CF-S1, uninformative on real) |
| FL-053 | Lane A primary: joint acquisition+switching vs best calendar | max relative gap 0.003645 (144 cells), 0.008741 (288 cells), 0 J<=C* violations; A1b alpha=1/5 0.500 to 4.641 % for T=6..11, INCONCLUSIVE; zero at alpha=1/10 (PD `FINAL_RESEARCH_REPORT.md`) | cond / cond | no | DEV (exact, known model) |
| FL-054 | **P3b paired certificate under a persistent-regime marginal null** | promoted in 20.8% of 6,000 paths, all in the positive regime; "Any certificate claim must be written as conditional-null only"; fixed-sample batch test ties P3b (P6 - P3b +3.0, +3.0, -0.2, +1.3) (PD) | marg / cond | **yes (new)** | DEV |
| FL-055 | HG vs PH/CUSUM; P4 persistence-aware promotion | HG -0.066 / -0.110 n.s. vs PH / CUSUM, FAR up to .23 under dependence; P4 worse by 10.45, 22.33, 9.50, 23.93 % in W1 (PD) | marg stress / cond (HG null UNVERIFIED) | partial (new) | DEV |

Net effect of WP0b: one additional `yes` mismatch (FL-054, now 14 original mismatches) and one additional
`partial` (FL-055, now 5). It also confirms the registry-level Lane A numbers (FL-017) from the primary report,
and adds one more frozen-protocol result (FL-052), a scoped negative.

## 4. What survives the correction

1. **Certified V1 gates are not "invalid under dependence".** Under the exact per-event conditional null
   (ESWAP) 0/10 ports exceed .0936, largest promote rate .040 [0.013, 0.079] (FL-035). Do not claim
   Drift2Act/RAR/other-host failures from marginal-null rates.
2. **Marginal-bound exceedance splits into a benign and a harmful part** (CONFIRMED, scoped): per-split fixed
   effect promotions carried zero harm (H_PERM = 0 in 19,200 runs); dependence-driven promotions carried small
   but nonzero harm (Delta 0.00536 [0.00234, 0.00896], concentrated in SMCS and tetouan) (FL-036).
3. **Validity-matched (V2) methods are valid but costly**: Markov-LR makes no promotions in 10/11 alternative
   cells; Gap-Mix is valid only at a declared rho_bar and loses its edge beyond it; A5b loses +61 to +257 on real
   streams (FL-012, FL-021, FL-022, FL-045). The pair "valid-conservative vs invalid-aggressive" must be
   reported on a Pareto plot, never as equals.
4. **Economic failures that do not depend on the null:** certification latency under a binding budget (M1,
   FL-039); unrepaired reversal headroom (FL-043); two cost-regression cells where episode_front still wins
   (FL-009, FL-031); sub-additive evidence x acquisition interaction (FL-030).
5. **Closed constructions to avoid repeating** (see `do_not_repeat_without` in the ledger): exact-gap SUI
   full-sup denominators (FL-016), rho-robust Gap-Mix (FL-022), FreshCheck as a value component (FL-025),
   split-clock bursts (FL-015), deadline-aligned acquisition as a heuristic (FL-014), triggered_kelly (FL-005).

## 5. Consequences for this programme (WP1 and later)

* **Drift2Act certificate** targets `absolute_risk` (`U_t(delta) <= tau`). Its validity metric is
  "gate passes while true window risk exceeds tau under the sampling it assumes", **not** conditional or
  marginal false promotion. Its exact conditions (uniform sampling from window, bounded losses, whether the target
  tracks drift) are UNVERIFIED until the d2a agent reads Secs 3-5 and App D.
* **RAR gates and canary** appear to be operational screens (target none/economic, UNVERIFIED against the
  paper); score them on J, rollback latency and unnecessary retrains, and compare with the paper's cost-aware
  binary baseline.
* Any proposed gap-aware evidence (Q1) must declare **which** null it targets (cond or marg), be compared with
  Markov-LR/thinning under the marg null and with e-process gates under the cond null, and report both
  plus ESWAP-style exact-null checks. A power win over an out-of-contract comparator is not a win.
* Q2 (decision-valued labels) overlaps the killed deadline-aligned acquisition (FL-014) and the PAVE negative
  (FL-023); it must beat a simple pending cap or fixed schedule (episode_front-style) and the belief-state
  planner on small instances.
* Q3 factorial precedent: GAVE-R already found a **negative interaction** (FL-030); a pre-registered
  J00/J10/J01/J11 design must treat it as the prior.

## 6. Evidence labelling and limits

* DEV rows use exposed or tuned seeds; some were registered before running, none are independent confirmations.
  Only FL-036 (and the control-group portion of FL-047) is a frozen-protocol confirmation, scoped to its twin
  construction and common-contract ports (no author-native code; five gated ports ran without fixes
  c66185c0 and 81dc4d34).
* Every comparator is `COMMON_CONTRACT_PORT` unless stated; Xu appears only as an acquisition adapter plus
  ShiftLab's certificate.
* Secondary-source rows (FL-017, FL-019, FL-048, FL-049) carry registry-level numbers; their primary documents
  were not re-read by WP0.
* The untracked `docs/hgxh2c/FINAL_REPORT.md` in the main checkout (Stage 3/4 results of the HGxH2c programme)
  and the branches `research/monitoring-to-decision-value-2026-10-30`, `research/shiftlab-promising-directions-2026-10-30`
  (Lane A primary docs) were **not mined**; see open items in the registry notes.
* No figures were produced (PaperBanana not used in WP0).
