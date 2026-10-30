# 01 Evidence Matrix (2026-10-30)

Status vocabulary: VERIFIED (re-derived from raw artifact this session), DOC-ONLY (stated in a repo doc, not re-derived), MISMATCH, NOT FOUND.
Branch abbreviations: sweet-lovelace = `origin/claude/sweet-lovelace-pznpjq` (`d1b173b`); risk-approx = `research/risk-preserving-switching-approx-2026-10-29` (`2bd2e8e`); exhaustive = `research/exhaustive-candidate-evaluation-2026-10-30` (`9cb4a1d`); h2c = `research/h2c-strong-baselines-and-generalization-2026-10-30` (`60930a4`; prereg `e164d63`; results `44119c6`); restart = `research/h2c-restart-risk-certified-2026-10-30` (`d4673d9`); gap = `research/shiftlab-mandate-gap-closure-2026-10-30` (`8552911`); depgate = `research/shiftlab-dependence-gates-2026-10-31` (`026500d`); rpoq = `research/rpoq-s1-fatal-flaw-audit` (`0b1ce99`).

## 1. Claim-to-evidence matrix

### Lane A: joint vs separable acquisition/deployment

| Claim | Source (branch@commit : path) | Status | Caveat | Contradiction / supersession |
|---|---|---|---|---|
| Toy DP, T=8, no risk constraint, 192 instances: joint J <= every separate arm 192/192; strictly better in 27/192, by >0.01 in 16; max relative gap 1.1%, mean 0.04%; zero for B=1; best separate arm is the open-loop schedule in 188 | sweet-lovelace@d1b173b : `research/novelty_validation_2026-10-30/outputs/x2_joint_vs_separate_dp.json` | DOC-ONLY | No risk constraint; toy | Different setting from risk-approx rows below |
| Risk-approx T=8, B=4, d=2, alpha=1/10, cq=1/100, cs=1/10: gap vs best calendar 6744087/781250000 ~ 0.00863 (transition 1/10, emissions 1/10, 9/10) and 11126044659/976562500000 ~ 0.01139 (emissions 1/50, 49/50; 3.4123 vs 3.4237); 4 other cells gap 0 | risk-approx@2bd2e8e : `docs/risk_preserving_approx/T8_B4_CALENDAR_RESULTS_V1.md` | DOC-ONLY | 2 of 6 cells nonzero; exact rationals | |
| T=6, B=3, d=2: all 6 cells gap 0 | risk-approx@2bd2e8e : `docs/risk_preserving_approx/CAP_CALENDAR_RESULTS_V1.md` | DOC-ONLY | | |
| T=6, B=3, d=2: joint 22083523/7812500 = best calendar (1,2,3); runtimes 0.31 s / 0.59 s | reproduced this session from risk-approx code | VERIFIED | Single cell | Consistent with the zero-gap row |
| T=7 and T=8 with d=1: gap 0; T8 d=1 reference 24735833/6400000 certified within 4.8e-12 | risk-approx@2bd2e8e : `docs/risk_preserving_approx/FULL_T8_DECOMPOSED_CERT_RESULTS_V1.md` | DOC-ONLY | | |
| Streak controller class is worse than the sequence-form reference by 0.7248% (H/B/d = 4/3/1) and 1.6114% (5/4/1); adding abandonment controllers closes both exactly and matches 5 prospective H=6 cells; the 1.6% was an incomplete-baseline artifact, not a joint-vs-separable gap | exhaustive@9cb4a1d (commits `405bb79`, `6047afd`, `9cb4a1d`) | DOC-ONLY | Gap came from an incomplete baseline class | Do not cite 0.72% / 1.61% as a joint-vs-separable gain |
| Under risk, missing baselines: state-independent adaptive acquisition; always-query and immediate-deploy as standalone rows | audit finding across risk-approx / exhaustive | VERIFIED (absence) | | Open obligation |
| Real-data headroom: Gas 3403 -> 2983 errors over 7977 = 12.342%; clairvoyant batch switching 2955 vs always-challenger 2984 = 0.972% | exhaustive@ad6cedf : `docs/exhaustive_evaluation/PROMISING_OPTIONS_EXPLORATION.md` | 12.342% VERIFIED (recomputed); 0.972% DOC-ONLY | Switch cost 1, no label cost; Gas exposed; Bike/Beijing no headroom and raw data absent | |

### Lane B: H2c (cost-guided discounted betting)

| Claim | Source | Status | Caveat | Contradiction / supersession |
|---|---|---|---|---|
| G5 confirmation: 14 harm / 10 benign / 8 null cells, 600 seeds; advantage over better comparator +0.086 [0.059, 0.113] @10% and +0.094 [0.063, 0.125] @20% | h2c@60930a4 : `outputs/h2c_next/g5_confirmation_per_seed.parquet` (sha256 `ed5923e9486c6bc9c8a0d1497f68c74563a4221f5644721f508dfd7fbbf66ba7`); `outputs/h2c_next/g5_confirmation_cells.csv` (sha256 `81c8e39d6afc29ce88a62a28d42395d11cc3661af2ff538e0978c0e04c1877b6`); `scripts/sota_search/g5_confirmation_analysis.py` | VERIFIED (analysis rerun) | Cluster bootstrap, 4000 resamples over cells then seeds; per-cell better comparator chosen from realised means; no manifest in repo; simulation not re-run in full | Interpretation limited by sweet-lovelace X1 (reduces to Kelly) |
| Power 0.382 / 0.640; benign FAR 0.067 @20%; null FAR max <= 0.027; harm cells won 13/14 and 14/14 | same | VERIFIED (analysis rerun) | | |
| Single-cell rerun subgroup_failure/concept2, N=600, different seeds: H2c 0.330 / 0.617 vs frozen 0.342 / 0.627 | this session, h2c@60930a4 scripts | VERIFIED (MC-consistent; 3.1 s) | One cell | |
| Statistic `pp_cost_guided(mode="guided_disc", gamma=0.995)`, threshold ln(1/alpha); comparators C1 fix_cost (discounted Kelly), C2 cost_ons, C7a sr_cost_tight | h2c@60930a4 : `src/shiftlab/sota_search/detectors.py` ~570-610 | VERIFIED (read) | C7a empirically calibrated and more powerful (H2c -0.19 / -0.13) but no guarantee | |
| Cost-null validity | h2c@60930a4 : `docs/h2c_next/COST_NULL_VALIDITY.md` | DOC-ONLY | No unit test of the supermartingale property | |
| Caveats: G5 nominal cost effectively known; fixed delay 5; static proxy defects; one generator family; no comparator is a verified published reproduction; outcome-dependent delay not covered; dependence not re-run for cost-null | h2c docs | DOC-ONLY | | |
| Under AR rho = .98, Brier-null e-processes exceed alpha (up to .36) | h2c docs | DOC-ONLY | Brier null, not cost null | See section 2 |
| Restart: valid restart mixtures +.003 / +.009 / +.023 (noise); SR-recursion empirical thresholds do not transfer (FAR .03-.13; .19-.30 at rho = .98); unknown nominal gives power ~ 0 for n_cal <= 1000; EB n_cal = 50,000 gives .535 / .850 vs .603 / .902 known | restart@d4673d9 : `docs/h2c_restart/` | DOC-ONLY | | Weakens G5 known-nominal setting |
| H2c reduces exactly to discounted Kelly with substituted moment ratio (max abs dlogW 8.9e-16); guidance helps +.03 to +.14 only when Brier co-shifts; loses up to .59 when flat/opposed | sweet-lovelace@d1b173b : `research/novelty_validation_2026-10-30/outputs/x1_guidance_mechanism_q{0.1,0.2,1.0}.json` | DOC-ONLY | | Undercuts a novel-method reading of G5 |
| D2 Gas replay (exposed): H2c 242-824 events later than cost-only Kelly/ONS; 2-4x excess cost before alarm | sweet-lovelace@d1b173b : `outputs/d2_gas_sensor_replay.json`, `outputs/d2_followup_paired_and_diagnostic.json` | DOC-ONLY | Exposed holdout | Reverses the synthetic gain |

### Lane C: HG (decision-aware betting)

| Claim | Source | Status | Caveat | Contradiction / supersession |
|---|---|---|---|---|
| e15 confirmation, 21 worlds, 400 seeds harm / 1000 null: +0.029 [0.012, 0.046], Holm p 0.004 (recompute 0.0288; raw p 0.0005) and +0.052 [0.020, 0.090], Holm p 0.003 (recompute 0.0518); Holm family 10 | gap@8552911 : `outputs/gap_closure/e15_confirm/perseed.parquet`; `scripts/gap/e15_confirm.py` | VERIFIED | Synthetic | |
| "Harm reduction ~21/24" | gap docs | MISMATCH | Raw cumulative-harm units (-20.6 / -24.2) averaged over all 21 worlds including null; harm worlds only -28.9 / -33.9, about 15% / 25% relative | Use the relative harm-world figures |
| Predictable uniform cap repair | gap@8552911 : `tests/gap/test_engine.py::test_exact_finite_support_cap` | VERIFIED (18 tests pass) | | |
| HG vs Page-Hinkley/CUSUM power -0.066 / -0.110 (n.s.) | gap docs | DOC-ONLY | Not a win | |
| HG invalid under dependent outcomes (FAR up to .23) | gap docs | DOC-ONLY | | |
| hg-validation G3: beats parent +.050 / +.131, not ONS or plain discounting | hg-validation@1299c1c : `docs/hg_validation/05_G3_RESULTS.md`; `outputs/hg_validation/05_G3_PER_SEED.parquet` | DOC-ONLY | | Limits novelty claim |

### Lane D: paired/CAMS promotion, dependence, RPOQ

| Claim | Source | Status | Caveat | Contradiction / supersession |
|---|---|---|---|---|
| Paired/CAMS simulated FWER max 0.023 (paired_e, K=10), cams 0.0029; wrong promotion after reversal 0.012-0.038 | gap@8552911 : `src/shiftlab/gap/q2.py` | DOC-ONLY | No tests for q2.py | |
| Dependence bound alpha + eps(1 + (T-1) delta) | depgate@026500d (docs `001e878`, `026500d`) | VERIFIED (proof read; maximal coupling) | Necessary condition on power; not independently reviewed | |
| Oracle power at T=2000 (eps .05 / .10): T*delta = 5: .069 / .099; 20: .092 / .184; 100: .193 / .476; 500: .606 / .976 | depgate : `outputs/dep_sprint/gate_b_oracle.json` | DOC-ONLY | Oracle | |
| Fallback (600 paths, stylised, no label cost). Variant A cluster 333: incumbent 601.5, conditional alarm hold100 298.0, oracle 213.4, marginal monitor never fires; cluster 20: 595.9 / 527.5 / 250.9. Variant B: no fallback benefit; conditional alarm +6 to +10% worse | depgate : `outputs/dep_sprint/estimand_switching.json` | DOC-ONLY | Stylised | |
| RPOQ: +0.215 [0.177, 0.253] het rho=0; -0.120 [-0.157, -0.082] het_flip rho=.6; CRSP growth vs uniform -1.15 [-1.56, -0.76] @5%, -3.21 [-5.16, -0.87] @20% log-wealth (exposed) | rpoq@0b1ce99 : `docs/rpoq_next/` (`FINAL_DECISION.md`, `CANDIDATE_RANKING.md`) | DOC-ONLY | CRSP is exposed retrospective stress data | Sign flips with design; Hsu-Shekhar 2607.17409 is prior art (abstract-level scan) |
| Sweet-lovelace overall: H2c = composition of PP-IPW increment, discounted Kelly/ONS, side-information bet, alpha-split; verdict BENCHMARK_OR_NEGATIVE_RESULT_ONLY | sweet-lovelace@d1b173b : `research/novelty_validation_2026-10-30/12_FINAL_PUBLICATION_DECISION.md` | DOC-ONLY | Kill standard predates R1-R6 | See section 2 |

## 2. Contradictions and mismatched nulls

| Issue | Detail | Handling |
|---|---|---|
| Sweet-lovelace kill standard vs R2 | Sweet-lovelace concludes composition-only / negative. The revised main criteria (R2) permit a prior-art kill only if a source theorem states or implies the result under the same contract; R3 and R4 allow partial contracts and exploratory prototypes. The sweet-lovelace verdict is a composition judgment, not shown here to be a theorem-based kill | Treat as evidence of weak novelty, not a kill; re-screen under R1-R6 |
| X2 no-risk vs risk-approx | X2 (no risk constraint, T=8) finds a small, mostly zero joint gap (max 1.1%). Risk-approx (risk constraint, B=4, d=2) finds gaps 0.0086 and 0.0114 in 2 of 6 cells, zero elsewhere. Different problems | Report separately; do not extrapolate either |
| Incomplete-baseline artifact | Exhaustive streak-class gaps (0.7248%, 1.6114%) vanish with abandonment controllers | Exclude from separation evidence |
| Brier-null vs cost-null | The AR rho=.98 exceedance (up to .36) is for Brier-null e-processes; cost-null validity rests on a written, unit-untested argument; dependence not re-run for the cost null | Do not transfer either statement to the other null |
| Empirical vs anytime validity | C7a / SR empirically calibrated thresholds (restart FAR .03-.13; .19-.30 at rho=.98) versus the ln(1/alpha) e-process threshold with an argued but unit-untested guarantee; G5 FAR is empirical | Label every FAR as empirical unless a proof is cited |
| Known vs unknown nominal | G5 nominal cost effectively known; restart shows power ~ 0 for n_cal <= 1000 when unknown | G5 gains are for the known-nominal setting |
| Synthetic gain vs exposed Gas replay | G5 +0.086 / +0.094 versus D2 Gas where H2c is 242-824 events later than cost-only Kelly/ONS. Gas is an exposed holdout | No confirmatory real-data claim |
| Exposed CRSP | RPOQ CRSP results are negative (-1.15, -3.21 log-wealth); CRSP dates are not causal change labels | Stress-test only |
| HG interpretation | "21/24" is a raw-units average including null worlds | Use about 15% / 25% relative (harm worlds) |
| Dependence | HG invalid under dependence (FAR to .23); H2c dependence not re-run; depgate bound is a necessary condition on power only | Keep dependence gate open |

## 3. Missing primary sources

- Faithful reproductions listed in `docs/exhaustive_evaluation/BASELINE_COVERAGE.md` @ `9cb4a1d`: robust FSC; finite-window CPOMDP; Active RCPS (full); PR monitoring; PPRM faithful confidence sequence; Hsu-Shekhar native (obstruction); Betting on Predictions native; PH/CUSUM/SR e-detector mapping; nonpartitioned PFA; Sethi Markov; controller synthesis certificates.
- Hsu-Shekhar arXiv 2607.17409: only an abstract-level scan; full text not verified.
- No published-paper reproduction of any H2c comparator (h2c caveat).
- H2c supermartingale unit test: NOT FOUND.
- G5 simulation manifest: NOT FOUND in repo.
- Tests for `src/shiftlab/gap/q2.py`: NOT FOUND.
- Bike and Beijing raw data: NOT FOUND locally (URLs only).
- State-independent adaptive acquisition baseline and standalone always-query / immediate-deploy rows under risk: NOT FOUND.
