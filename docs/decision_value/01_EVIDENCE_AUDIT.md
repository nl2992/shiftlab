# 01 Evidence audit of six historical findings (Agent A, 2026-10-30)

Scope. Six findings (F1-F6) inherited from sibling research branches were traced to documents, scripts, configs and stored artifacts, and every statistic that has a stored per-seed or batch-level artifact was recomputed. Nothing here is confirmatory evidence for the new programme.

Vocabulary used throughout.
- **Analysis recomputation**: a statistic recomputed from a stored per-seed / batch-level file. It is NOT a simulation reproduction.
- **Bit-identical rerun**: the original script rerun with the original seed gave identical output.
- **Fresh-seed rerun**: the original generator rerun with a new seed block (900000+). Non-confirmatory, development only.
- Status classes: VERIFIED, PARTIALLY_VERIFIED, DOC_ONLY, CONTRADICTED, UNAVAILABLE.

Code and outputs of this audit (not committed): `WT/outputs/decision_value/development/audit/` (WT = `branch-research-monitoring-to-decision-value-2026-10-30`):
`audit_recompute.py` / `audit_recompute.json` (all analysis recomputations), `rerun_fresh_seed.py` (F3 and F4 reruns), `f3_fresh_rerun_seed900001.json`, `f4_seed{31,900031,900032,900033}.json`, `bl_copy.py`, `estimand_switching_copy.py` (verbatim copies of the originals with only seed/output-path/ROOT edits), `gas_rerun_root/` (patched-root rerun of the Gas headroom script). Inputs were read-only; Python was run with bytecode writing disabled; `git status` in the sibling worktrees showed no new files from this audit.

Evaluation status of ALL inherited results: exploratory or development, except F1 which is a *frozen synthetic confirmation of one single run of a pre-registered protocol* (e164d63 before running, 44119c6 results). Even F1 is confirmatory only for its own synthetic generator family; it is not confirmatory for the new programme (the new programme's question differs). All real-data items (F5, Gas D2) are exposed holdouts.

---------------------------------------------------------------------------------------------------

## Summary table

| id | claim (short) | status | headline recomputed number | main caveat |
|---|---|---|---|---|
| F1 | H2c beats better of cost-only C1/C2 on frozen G5 | VERIFIED (analysis recomputation; simulation not rerun) | +0.0858 [0.0586, 0.1133] @10%; +0.0938 [0.0634, 0.1251] @20%; H2c power 0.3819 / 0.6405 | 14 harm cells (not 32) carry the estimate; known nominal; one generator; reverses on exposed Gas; benign cell with FA 0.31 |
| F1b | Gas replay reverses H2c gain | PARTIALLY_VERIFIED (stored JSON read, not rerun) | H2c later by 241.7 to 824.1 events | exposed holdout, different task/costs, branch not a worktree |
| F1c | H2c = discounted Kelly with substituted moment | DOC_ONLY | not rerun | max abs dlogW 8.9e-16 reported in sweet-lovelace |
| F2a | HG > local PPRM-inspired parent | VERIFIED (analysis recomputation) | +0.0288 [0.012, 0.046] @10%; +0.0518 [0.019, 0.090] @20% | "pprm" is a local SOURCE_INSPIRED arm |
| F2b | HG does not beat PH/CUSUM | VERIFIED (analysis recomputation) | HG-PH -0.0657 [-0.240, 0.083] @10%, -0.1102 [-0.258, 0.004] @20% | n.s. but point estimates favour PH |
| F2c | HG-triggered switching worse than PH-triggered in persistent harm | VERIFIED (analysis recomputation, 120 paired seeds, dev) | perm_beneficial +19.2 [6.2, 32.2]; harmful_incumbent_delay50 +26.5 [14.6, 39.2] net regret | doc's switch-rate sentence CONTRADICTED (see below); PH threshold empirically calibrated, HG at 1/alpha |
| F2d | ranking changes under transient/reversal/near-tied harm | VERIFIED (same artifact) | temp -9.4 [-17.1, -2.7]; reversal -12.7 [-23.8, -2.5]; near_tied -6.2 [-10.1, -2.7] | in those worlds both HG and PH lose to never switching |
| F2e | nominal validity fails under dependence | PARTIALLY_VERIFIED (stored JSON read) | HG FAR .2725 (ctx cap) / .295 (unif cap) at rho .98, 20% labels | gap-branch doc quotes "up to .23"; sources differ |
| F2f | context-dependent cap breaks supermartingale; uniform cap repairs | VERIFIED (analytic recomputation of exact drift) | drift +0.04474 (ctx cap) vs 0 (uniform cap) | toy two-context example; MC crossing 0.0675 / 0.035 stored, not rerun |
| F2g | HG_unifcap beats parent but not ONS / disc_only on G3 | VERIFIED (analysis recomputation) | +0.0500 [0.028, 0.073] @10%; +0.1313 [0.106, 0.157] @20%; vs ONS -0.098 / -0.011 | post-hoc repair arm; single generator |
| F3 | P3b certified switching 7.67%-10.20% cheaper than best simple | VERIFIED (analysis recomputation + fresh-seed rerun) | 10.20 / 9.65 / 7.88 / 7.67 %; fresh seeds 10.02 / 9.59 / 7.60 / 7.54 % | world-averaged, gain concentrated in W1; W3/W4 worse than BEST at B400_cs20 |
| F3b | fixed-sample batch test captures much of it | VERIFIED (fresh-seed rerun) | batch P6 8.99 / 8.51 / 7.68 / 7.21 % vs P3b 10.02 / 9.59 / 7.60 / 7.54 % | report text says no saved artifact; it is archived at 1a717bc |
| F4 | stylised dependent-regime switching | VERIFIED (bit-identical rerun at seed 31; fresh-seed rerun qualitatively replicates) | A, cluster 333: 601.5 / 298.0 / 213.4; fresh mean of 3 runs 587.9 / 291.4 / 208.6 | absolute levels move +-10-20 between 600-path runs; ratios stable (-50.5% vs -50.4%) |
| F5 | Gas incumbent 3,403 vs challenger 2,983 errors (12.34%); hindsight headroom 0.97% | PARTIALLY_VERIFIED | stored artifact recomputes exactly (12.342%; 2955 vs 2984 = 0.972%); code rerun in this environment gives 3416 / 2974 (12.94%), headroom 1.08% | exposed; selection on batch 6; switch cost 1, no label cost; not bit-reproducible across library versions |
| F6a | persistence bound P_alt(reject) <= alpha + eps(1+(T-1)delta) | VERIFIED (proof re-derived, exact n=16 enumeration reproduces doc) | exact NP power .0667 / .0678 / .0804 / .2131 vs bound .1507 / .165 / .30 / 1.65 | bounds one specific alternative class for a test valid under one specific chain |
| F6b | oracle ceiling table at T=2000 | DOC_ONLY / stored JSON matches doc | e.g. T*delta=5, eps .10: .0985 | MC not rerun; bound is loose, the table (not the bound) shows the low power |
| F6c | "false alarms" under stationary-marginal null are valid detections of the conditional-risk estimand | VERIFIED logically; usefulness conditional (F4 variant A vs B) | n/a | validity of the conditional e-process under dependence itself is not proven here |

---------------------------------------------------------------------------------------------------

## F1. H2c versus stronger cost-only comparators on frozen G5

**Original branch / commits.** `research/h2c-strong-baselines-and-generalization-2026-10-30` (worktree `branch-research-h2c-strong-baselines-and-generalization-2026-10-30`, HEAD `60930a4`).
- Protocol (written before running): `docs/h2c_next/FROZEN_CONFIRMATION_PROTOCOL.md`, commit `44119c612a0068e21348893fd94a44c20c297b01` (protocol first committed at `e164d63310cbec7fed4efc16dbf726b20abf0a17`).
- Results: `docs/h2c_next/FROZEN_CONFIRMATION_RESULTS.md` `44119c61...`.
- Ablations: `docs/h2c_next/H2C_MECHANISM_ABLATIONS.md` `803bc8a824d56e3aed9af0b7a786e6561cced6fa`.
- Decision: `docs/h2c_next/FINAL_SPRINT_DECISION.md` `60930a417952b3059b6309fa519a1abb4af893fb`.
- Runner: `scripts/sota_search/g5_confirmation.py` (`44119c61`); analysis `scripts/sota_search/g5_confirmation_analysis.py` (`44119c61`; written after the runner crashed in its analysis block on a name clash, per the results doc; the simulation was not rerun).
- Detectors: `src/shiftlab/sota_search/detectors.py` (`2aa6a8b8`), generator `generators.py` (`e164d63`).

**Protocol.** G5 synthetic generator, seed block 90000+, 8 deployed-model conditions x 4 shifts {none, prior1, concept2, concept1.5} = 32 cells, 600 seeds per cell, T = 2000, t0 = 700, fixed delay 5, label rates 10% and 20%, threshold 1/alpha (alpha .05). Roles (harm / benign / null) from ground-truth decision harm >= 0.10 computed by population simulation. Finalists frozen from the development summary. Hypotheses D1-D4 stated before running.

**Cells and seeds.** 32 cells (14 harm, 10 benign, 8 null) x 600 seeds (verified from the parquet: 345,600 rows = 32 x 600 x 9 arms x 2 label rates). The paired power estimate uses only the 14 harm cells.

**Metric.** Harm power = fraction of seeds with an alarm at or after t0 in harm cells; benign/null false alarm; D1 estimate = mean over harm cells of (H2c detect - detect of the per-cell better of C1/C2, chosen from realised cell means), two-level bootstrap (cells then seeds, 4000 resamples, rng seed 17).

**Reported:** +0.086 [0.059, 0.113] (10%), +0.094 [0.063, 0.125] (20%); H2c power .382 / .640.
**Recomputed** (`audit_recompute.py`, section F1, from `outputs/h2c_next/g5_confirmation_per_seed.parquet`, sha256 `ed5923e9...66ba7`; same formulas and seed as the original analysis script):
- 10%: +0.08583 [0.05857, 0.11334]; H2c power 0.38190; C1 0.26464; C2 0.29607; H2c beats the per-cell better comparator in 13 of 14 harm cells.
- 20%: +0.09381 [0.06345, 0.12512]; H2c power 0.64048; C1 0.54512; C2 0.49095; 14 of 14 cells.
- Benign FA (mean over 10 cells) 0.0357 / 0.0670; null FA mean 0.0117 / 0.0179, null max 0.0233 / 0.0267.
- Sensitivity to the comparator definition: H2c - C1 alone = +0.117 / +0.095; H2c - C2 alone = +0.086 / +0.150; H2c - C7a (cost SR e-detector, empirically thresholded) = -0.190 / -0.132.

**Status: VERIFIED (analysis recomputation).** Simulation not rerun in full. A single-cell rerun on other seeds (subgroup_failure/concept2) was reported by a previous audit (`shiftlab-promising-directions-2026-10-30/docs/promising_directions/01_EVIDENCE_MATRIX.md`: H2c .330/.617 vs frozen .342/.627); I did not repeat it because the G5 runner needs the full `shiftlab.sota_search` harness and the 10-minute single-process budget is better spent elsewhere.

**Caveats and findings from the audit.**
1. The headline "32 cells x 600 seeds" overstates the support: the D1 estimate rests on 14 harm cells built from 8 conditions of one linear-boundary generator; cells share conditions and shifts, so they are neither independent nor a random sample of anything. The cell-level bootstrap is descriptive of this design only.
2. One benign-role cell has positive true harm below the 0.10 threshold (`biased` / `concept1.5`, harm .076). H2c alarms in 30.7% of its seeds at 20% labels (C2: 17.7%, C1: 16.5%); `underconfident/concept2` (harm .038) 13.8%; `subgroup_failure/prior1` (harm .082) 10.2%. Frozen criterion D3 only constrained the pooled benign mean (0.067 vs limit 0.07), which hides these cells. In these cells the cost null is in fact false, so the alarms are not null-violations, but "benign false alarm profile kept" is not a statement about per-cell behaviour.
3. D1's comparator is the per-cell better of C1/C2 chosen from the same realised means. This makes the comparison harder for H2c (conservative), but it is a data-dependent oracle choice, not a deployable comparator.
4. Not a win over every method: C7a is more powerful by .19 / .13 with 2-3x false alarms; Brier-null methods (HG, Brier ONS) are more powerful but alarm in 16-33% of benign cells.
5. Nominal risk is effectively known (`docs/h2c_restart/NOMINAL_RISK_UNCERTAINTY.md`, h2c-restart `d4673d9`: unknown nominal gives power near 0 for n_cal <= 1000; empirical-Bernstein with n_cal = 50,000 recovers .535/.850 vs .603/.902).
6. Mechanism: the ablation (dev seeds 70000+, exploratory) attributes the advantage to Brier-guided bet selection (+0.17 over pooled parent) and discounting (additive). Separate sweet-lovelace work reports that H2c reduces exactly to discounted Kelly with a substituted moment ratio (max abs dlogW 8.9e-16) and that guidance helps only when Brier co-shifts (+.03 to +.14) and loses up to .59 otherwise (`origin/claude/sweet-lovelace-pznpjq`, `research/novelty_validation_2026-10-30/outputs/x1_guidance_mechanism_q{0.1,0.2,1.0}.json`). Status DOC_ONLY; not recomputed here.
7. Cost-null validity of H2c: `docs/h2c_next/COST_NULL_VALIDITY.md` is a written argument; no unit test of the supermartingale property exists (DOC_ONLY).
8. Real data was `BLOCKED_EXTERNAL_ACCESS` in that sprint.

### F1b. Gas replay reversal (sweet-lovelace D2)
Source (not a worktree; read via `git show origin/claude/sweet-lovelace-pznpjq:...`, HEAD `e9e68574a474ce347e78e4a7d856674bfbdcf3d2`): `research/novelty_validation_2026-10-30/{scripts/d2_gas_sensor_replay.py, scripts/d2_followup_paired_and_diagnostic.py, outputs/d2_gas_sensor_replay.json, outputs/d2_followup_paired_and_diagnostic.json, outputs/d2_gas_sensor_per_seed_alarm_idx.npz}`; last change to the replay JSON `34c7c8f0cdddedfe53f8e62c09651a91bcb53486`. Protocol 06 was committed (`89dba6a`) before the run; labelled EXPLORATORY, batches previously exposed. Stored paired result: mean alarm-index difference (H2c minus reference) of 241.69 [231.6, 256.8] (vs C1, 20% labels) up to 824.1 [681.1, 976.5] (vs better of C1/C2, 5% labels), with H2c later in 99.3-100% of seeds. Archive sha256 `91e8f466...351fe4` equals the local `shift-research-starter/data/raw/gas_sensor/uci-224.zip`. **PARTIALLY_VERIFIED**: stored JSON read; the 2-4x pre-alarm excess-cost figure and the per-seed `.npz` were not recomputed; script not rerun. Note the D2 task (binary class-6-style decision, tolerance .1, T_drift 12,221) differs from the F5 headroom task.

---------------------------------------------------------------------------------------------------

## F2. HG (decision-aware betting): parent, PH/CUSUM, switching, dependence, cap repair

Sources and commits.
- `research/shiftlab-mandate-gap-closure-2026-10-30` (worktree `branch-research-shiftlab-mandate-gap-closure-2026-10-30`), HEAD `85529116eb9fd16e533ddce9f545f79d695e87d7`.
- `research/hg-validation-and-novelty-2026-10-30` (worktree `branch-research-hg-validation-and-novelty-2026-10-30`), HEAD `1299c1c285ca5cb1387f4805c60767c214fe1106`.
- `research/shiftlab-dependence-gates-2026-10-31` (worktree `branch-research-shiftlab-dependence-gates-2026-10-31`), HEAD `026500db9dac67da8b9dc239870356a85c571811`.

### F2a / F2b. Frozen confirmation e15 (HG vs PPRM-inspired parent, PH, CUSUM)
- Docs: `docs/sota_gap_closure/FINAL_STATISTICAL_COMPARISONS.md` and `REPORT_D_RESEARCH_DECISION.md`; commits `08cee3df1e57725f39bde7a525305ae71359379f` and `85529116...`.
- Script: `scripts/gap/e15_confirm.py` (`85529116`), analysis `scripts/gap/analyze_confirmation.py`; config `configs/gap_closure/frozen_confirmation_v1.json`. Per-seed: `outputs/gap_closure/e15_confirm/perseed.parquet` (168,000 rows), `comparisons.csv`.
- Protocol: 15 harm worlds + 6 null worlds from G3-G6 pools; 400 seeds per harm world, 1000 per null world; seeds 900000+; T = 2000, labels 10% / 20%, delay 5 unless the world sets a delay model; Holm over 10 comparisons; cluster bootstrap over worlds then seeds. Status: frozen synthetic confirmation (single run; round 2 reran corrected-floor HG variants on seeds 1,100,000+ separately).
- Metric: power = detection among seeds with a harmful step, worlds equally weighted.
- Reported: HG - PPRM +0.029 [0.012, 0.046] (Holm p .004), +0.052 [0.020, 0.090] (p .003); HG - PH -0.066 [-0.240, 0.079] and -0.110 [-0.247, 0.005]; both n.s. after Holm.
- Recomputed (`audit_recompute.py` F2b, own bootstrap, 2000 resamples, rng 2026): HG-PPRM +0.0288 [0.0117, 0.0460] and +0.0518 [0.0188, 0.0900]; HG-PH -0.0657 [-0.2395, 0.0828] and -0.1102 [-0.2575, 0.0040]; HG-CUSUM +0.018 [-0.155, 0.166] and -0.039 [-0.186, 0.088]. Mean powers: HG .701/.808, PH .767/.918, CUSUM .683/.847, PPRM .672/.756.
- **Status: VERIFIED (analysis recomputation).**
- Caveats: the PPRM arm is a local SOURCE_INSPIRED parent, not the published confidence sequence (`02_LITERATURE_AND_NOVELTY_AUDIT.md` in promising-directions; "FORMULA_ADAPTATION / SOURCE_INSPIRED"); PH/CUSUM thresholds are empirically null-calibrated, HG uses 1/alpha; the first confirmation run mixed two label fractions in the classical-arm names, was rerun with identical seeds, and the mixed file is retained as `perseed_run1_classical_names_mixed.parquet` (disclosed in `REPORT_A_EXPERIMENTAL_COVERAGE.md`). HG "reduces harm" figure of "21/24" is a MISMATCH noted by the earlier audit (raw cumulative-harm units averaged over all 21 worlds incl. null; harm-world-only about 15% / 25% relative).

### F2c / F2d. HG- vs PH-triggered switching (Q3) -- key lead for "monitoring ranking reversal"
- Doc: `docs/sota_gap_closure/Q3_HG_TRANSFER_RESULTS.md` (`08cee3df`; earlier `0b02596`); environment `Q3_ENVIRONMENT.md`; baselines `Q3_BASELINE_RESULTS.md`.
- Code: `src/shiftlab/gap/q3.py` (`290b0560116e41aebb427bef16d484d9fcb594c7`; `OnlineHG` class lines ~112-153, `run_policy`, `total_cost`), `scripts/gap/e8_q3.py` (`290b0560`). Per-seed: `outputs/gap_closure/e8_q3/perseed.parquet` (77,760 rows = 6 scenarios x 9 policies x 12 cost settings x 120 seeds; sha-verifiable; gitignored in worktree but present on disk).
- Protocol: fully synthetic logistic-label world; two pre-trained models; T = 1000, onset 300, 120 seeds per scenario (seed bases 8000 + scenario index), delay 5 (50 in `harmful_incumbent_delay50`); 10% labels; actions continue/query/recalibrate/retrain/promote/rollback; costs multiplied by KQ = 10 and KC = 100 (a design choice to make costs comparable to the harm); base cost row used for the headline; post-hoc cost grid (12 settings, not the 108-cell Cartesian product). PH threshold = 95% quantile of the null horizon maximum on 300 null paths. Status: development / exploratory (single draw, no preregistered hypothesis).
- Metric: net regret = realised loss + action costs - loss of the instantly adapted Bayes model (a lower bound ignoring costs); paired differences by seed; bootstrap 95% CI.
- Reported and recomputed (`audit_recompute.py` F2a_q3, bootstrap 4000): all point estimates match the doc to the printed precision; CIs agree within about +-0.7.

| scenario | HG - PH net regret (reported) | recomputed | reading |
|---|---|---|---|
| perm_beneficial | +19.2 [6.2, 32.2] | +19.2 [6.2, 32.2] | HG worse |
| harmful_incumbent_delay50 | +26.5 [14.5, 39.1] | +26.5 [14.6, 39.2] | HG worse |
| temp_beneficial | -9.4 [-16.9, -2.9] | -9.4 [-17.1, -2.7] | HG better |
| reversal | -12.7 [-23.2, -2.5] | -12.7 [-23.8, -2.5] | HG better |
| near_tied_flip | -6.2 [-10.0, -2.8] | -6.2 [-10.1, -2.7] | HG better |
| no_worthwhile | -1.7 [-3.9, 0.0] | -1.7 [-4.0, 0.0] | n.s. |

- **Status: VERIFIED (analysis recomputation) for the paired differences.** The sign pattern (HG worse under persistent harm, better under transient / reversal / near-tied) is real in this artifact.
- Discrepancies found:
  1. The doc says HG "switches in 20% of seeds vs 30% for PH" under permanent harm "at 10% labels". The per-seed `n_sw > 0` rates are 56.7% (HG) vs 67.5% (PH) in `perm_beneficial` and 47.5% vs 63.3% in `harmful_incumbent_delay50`. The direction (HG switches less) is right; the quoted magnitudes do not match any definition I tried. Mark that sentence **CONTRADICTED** (numbers), mechanism otherwise supported.
  2. The `verdict` column labels `cert_switch - ph_switch` rows "n.s." although their listed intervals exclude zero (reversal -16.8 [-28.4, -5.9], near_tied -7.3 [-11.6, -3.6], temp -10.8 [-18.0, -4.6]); the test behind "n.s." is not stated. Treat those labels as unreliable.
  3. In the four scenarios where HG beats PH, both lose to never switching: HG - frozen = +11.7 (temp), +23.8 (reversal), +11.1 (near_tied), +10.1 (no_worthwhile), so PH - frozen is larger still. The monitoring ranking reversal therefore sits in worlds where the best decision is to not act at all. The decision-relevant statement is about *which false-switch profile costs less*, not about a beneficial switching policy.
  4. Not size-matched: PH threshold is a 95% empirical null-max quantile, HG uses ln(1/alpha) with a restart mechanism and gamma .99 / gate window 100 (hard-coded in `OnlineHG`); the HG implementation in q3.py is a separate online reimplementation, not `engine.run`. The ranking may therefore reflect conservativeness (switch propensity), not monitor quality.
  5. Costs scaled (KQ 10, KC 100) by a design choice; only the base cost row appears in the doc.

### F2e. HG under dependence
- Docs: `docs/hg_validation/06_DEPENDENCE_STRESS.md` (`3d16a88bdc022fef9f89c143108cbbe2f4a1c5cf`), data `outputs/hg_validation/06_DEPENDENCE_NULL.json`; AR(1) covariates, no shift, 400 seeds, T = 2000, alpha .05, delay 5. At rho .98, 20% labels: parent .17, HG ctx cap .2725, HG unif cap .295, ONS .36 (stored JSON read, matches the doc table). Gap-branch round-2 dependence nulls: HG@0.2 up to .141 (HG_hardcap .140; HGu@0.3 .222) in `FINAL_CONFIRMATION_ROUND2_RESULTS.md`; `01_EVIDENCE_MATRIX` (promising-directions) quotes "up to .23". The value depends on the source and the dependence model; use ".14 to .30, empirical".
- **Status: PARTIALLY_VERIFIED** (stored artifacts read; simulation not rerun). Discounting plus gating is worse than the parent (.27-.30 vs .17); the uniform cap does not fix dependence because the repaired argument requires E[R_t | F_{t-1}] <= r0.

### F2f. Context-dependent betting cap
- Doc `docs/hg_validation/02_VALIDITY_COUNTEREXAMPLES.md` (`79e14272f0f20ade251cdcbbbb8c2b3f2eb15091`); data `outputs/hg_validation/02_EXACT_NULL_TESTS.json`; repair verified by `tests/gap/test_engine.py::test_exact_finite_support_cap` (`07826329`, 18 tests per the earlier audit; I did not rerun pytest) and `Cfg.cap_mode = "sup"` in `src/shiftlab/gap/engine.py`.
- Analytic recomputation: two equiprobable contexts with risks (0.6, 0.2), r0 = 0.4, so E[X | context] = risk - r0 = (+0.2, -0.2) (the PP-IPW increment is unbiased for the risk). With the stored context-cap bets lambda = (0.5882, 0.1408) the exact drift per step is 0.5*(0.5882*0.2 - 0.1408*0.2) = 0.044739, matching the stored 0.044739; with the uniform bet 0.1887 in both contexts the drift is 0. **VERIFIED.** Stored Monte Carlo crossing probabilities (0.0675 > 0.05 vs 0.035) were not rerun.
- Caveat: toy counterexample with idealised bet ceiling lambda0 = 1; the calibrated-proxy case is conservative; the practical inflation is small. The guarantee, not the practical false-alarm rate, is what fails.

### F2g. G3 confirmation (HG_unifcap vs parent, ONS, disc_only)
- Doc `docs/hg_validation/05_G3_RESULTS.md` (`edf4a95226528baea3f7f173715f18d33cd57b50`); per-seed `outputs/hg_validation/05_G3_PER_SEED.parquet` (10,000 rows: 2 label rates x 5 arms x 1000 seeds, 960 reach the harmful regime). Frozen protocol `05_G3_FROZEN_PROTOCOL.md`; HG_unifcap is a post-hoc repair (see `03_PAIRED_INFERENCE_RESULTS.md`, `3630375781351bcdc01e8efd3fd1d75e23d8a61b`).
- Recomputed: HG_unifcap - parent +0.0500 [0.0281, 0.0729] (10%), +0.1313 [0.1063, 0.1573] (20%); HG_unifcap - ONS -0.0979 [-0.121, -0.074] and -0.0115 [-0.033, 0.009]; HG_unifcap - disc_only -0.0573 and -0.0344 (CI excludes 0 at both). **VERIFIED.** The 10% gain sits exactly on the +0.05 threshold. HG does not beat plain discounting or ONS.

---------------------------------------------------------------------------------------------------

## F3. P3b certified switching

- Branch `research/shiftlab-promising-directions-2026-10-30` (worktree `shiftlab-promising-directions-2026-10-30`), HEAD at audit start per ledger `041bc26`; report `docs/promising_directions/FINAL_RESEARCH_REPORT.md` (`3d5d9a1f53665eb2fbda8e16aad0f86f96a203b8`).
- Protocol `protocols/B2-propensity-cap.md` (commit `af14d5a`, sha256 `533a529d...`); code `scripts/promising_directions/b1_certified_switching.py` (`041bc26fafeed1132f17ed762ddbfdcff02e34f2`, run with `--b2 --seed-base 20261101 --seeds 500`); tests `tests/promising_directions/test_b1_certified_switching.py`; per-seed `docs/promising_directions/results/b2/per_seed.npz` (+`summary.json`, `SHA256SUMS.txt`).
- Design: 4 worlds (W1-W4) x budget B in {200, 400} x switch cost c_s in {5, 20} = 4 settings, 500 seeds per cell, T = 2000 synthetic disagreement-regime streams (W1 useful-persistent challenger, W2 useless challenger, W3 reversing, W4 benign; protocol `B1-certified-switching.md`), fixed delay 5, c_q = 0.05, nominal alpha .05. "BEST" = the best of {P0 never, P1 always, P2 incumbent-alarm} chosen on the world-averaged cost within each setting (in-sample). Status: development round 2, explicitly "not confirmatory"; B2's single change (P3b propensity-matched cap) was motivated by a B1 post-hoc diagnostic.
- Metric: cost = deployment loss + c_q queries + c_s switches, averaged over the four worlds with equal weights; reduction = 1 - cost(P3b)/cost(BEST).
- Reported: 10.20, 9.65, 7.88, 7.67 %; P3b - BEST -35.04 [-36.81, -33.40], -33.52, -26.91, -26.66 [-27.36, -25.96]. Only B200_cs5 meets all 3 pre-registered criteria (10% bar).
- Recomputed (`audit_recompute.py` F3, from `per_seed.npz`): 10.202, 9.645, 7.877, 7.673 %; diff -35.042 [-36.75, -33.31], -33.517 [-34.25, -32.77], -26.906 [-28.54, -25.33], -26.663 [-27.32, -25.99]. BEST = P2, P0, P2, P0. **Per-world relative cost of P3b vs BEST:** W1 -28.3 / -36.7 / -16.0 / -37.4 %; W2 -5.1 / +2.1 / -7.5 / +4.2 %; W3 0.0 / +9.6 / -4.9 / +14.3 %; W4 +0.1 / +5.0 / +0.2 / +10.0 %. The headline reduction is carried by W1; in B400_cs20 P3b is 14.3% worse than BEST in W3 and 10.0% worse in W4 (matches the doc).
- **Fresh-seed rerun** (seed base 900001, 500 seeds per cell, using the archived critic code `docs/promising_directions/results/adversarial_review/bl.py.txt` (`1a717bcd04a0fdc9b9908e430d8e27b3f39962d5`) and `b1_certified_switching.py` imported read-only; `f3_fresh_rerun_seed900001.json`): P3b reduction 10.02 / 9.59 / 7.60 / 7.54 %; untuned fixed-sample paired batch test P6 (nv 25, thr 0.3): 8.99 / 8.51 / 7.68 / 7.21 %. Compare reported 10.20 / 9.65 / 7.88 / 7.67 % and 9.3 / 8.8 / 7.9 / 7.3 %. Label: **fresh-seed rerun (development, non-confirmatory)**. The batch test is within 0.1 to 1.1 percentage points of P3b, reproducing the "ties" finding.
- **Status: VERIFIED** (analysis recomputation plus fresh-seed rerun). "Did not meet the superiority threshold": VERIFIED (3 of 4 settings miss the 10% bar, one passes).
- Corrections: (i) the report states the critic's P6 numbers "have no saved artifact in this repo"; the scratch scripts and raw outputs were archived at `1a717bc` (`results/adversarial_review/`, with SHA256SUMS) after that text was written, so the statement is stale. (ii) The 7.67-10.20% range is a world-average dominated by W1 and uses an in-sample-selected BEST; per-world it is -37% to +14%. (iii) The conditional-null only: persistent-regime marginal null gives 20.8% false promotion (6,000 paths; reported, not rerun here; DOC_ONLY). (iv) Boundary null 3.05% / 2.67% (20,000 paths) DOC_ONLY. (v) The gain is generator specific (3.0 to 5.4% under a weaker paired signal; DOC_ONLY, from the critic's runs).

---------------------------------------------------------------------------------------------------

## F4. Stylised dependent-regime switching study

- Branch `research/shiftlab-dependence-gates-2026-10-31`; doc `docs/dependence_sprint/11_SAFE_SWITCHING_INTEGRATION.md` (`026500db9dac67da8b9dc239870356a85c571811`); script `scripts/dep_sprint/estimand_switching.py` (`026500db`, hard-coded rng seed 31, global generator, 600 paths, T = 2000, writes `outputs/dep_sprint/estimand_switching.json`); depends on `src/shiftlab/dep/sethi.py` (`026500db`; Sethi Algorithm 1 reproduction on the binary chain).
- World: hidden bad/good regime (lazy-resample chain, P(bad) = 0.3 = r0; cluster length 20 / 100 / 333 i.e. delta .05 / .01 / .003); incumbent loss = regime indicator (marginal mean r0 = nominal, i.e. there is no marginal shift); fallback loss 0.35 (variant A: regime-local benefit) or incumbent + 0.05 (variant B: none); switch cost 1.0 each way; both monitors see every loss (q = 1); holds 20 or 100 after an alarm, then restart; no label cost; deterministic losses.
- Metric: net cost = summed loss + switching, mean over 600 paths. No per-path outputs were stored (only means), so no CI can be recomputed from stored output.
- Reported: A, cluster 333: incumbent 601.5, conditional alarm hold 100 = 298.0, oracle 213.4; B, cluster 333: incumbent 600.1, conditional hold 100 = 639.9.
- **Bit-identical rerun at the original seed (31)** reproduced all 42 stored net-cost values exactly (max absolute difference 0.0 against `outputs/dep_sprint/estimand_switching.json`; e.g., A333 601.5 / 375.6 / 298.0 / 213.4; B333 600.1 / 664.0 / 639.9 / 633.0), taking 24 s. Marginal (Sethi) alarm equals incumbent-only (never fires) in all six variants.
- **Fresh-seed reruns** (seeds 900031-900033, three independent 600-path runs; label: fresh-seed rerun, development): A333 incumbent 587.9 (runs 584.2 / 588.2 / 591.4), conditional hold100 291.4, oracle 208.6; B333 incumbent 610.3, conditional hold100 650.9, oracle 643.7. Relative effects: A333 -50.5% (original) vs -50.4% (fresh); B333 +6.6% vs +6.7%. A, cluster 100: 606.0 / 383.9 / 220.8; A, cluster 20: 598.1 / (hold100) 556.9 / 251.6. Absolute levels between 600-path runs differ by up to 10-20 cost units (cluster 333 has only about six regime draws per path), so quote ratios or intervals, not three-digit levels.
- **Status: VERIFIED.** Direction and magnitude replicate; the original is one draw.
- Caveats: the world is constructed so the conditional monitor's alarm coincides with the bad regime and the fallback is hand-built with regime-local benefit; the conditional e-process uses the exactly known r0; nothing about label cost, delay, or rollback tests; holds not optimised; "+6 to +10% worse" in variant B is +6.3% to +10.6% over the six B rows (hold 20 and hold 100). It shows how the answer depends on the action set, not a method.

---------------------------------------------------------------------------------------------------

## F5. UCI Gas replay (headroom)

- Branch `research/exhaustive-candidate-evaluation-2026-10-30` (worktree `shiftlab-exhaustive-evaluation-2026-10-30`; the earlier audit cites it as `ad6cedf`). Doc `docs/exhaustive_evaluation/PROMISING_OPTIONS_EXPLORATION.md` and artifacts `gas_headroom_registration.json`, `gas_headroom_results.json` at `ad6cedf41c182ee8b0fcbda71fe09a73659959af`; script `scripts/exhaustive_evaluation/explore_gas_headroom.py` (`ad6cedf4`). The promising-directions doc (`10_REAL_DATA_RESULTS.md`, `939d5bf6beac0c06a39eef7b217893b0e9c7ecb2`) only inherits the numbers; no new real-data run was made there.
- Protocol: UCI-224 gas sensor drift, ten official batches, 13,910 rows; incumbent = logistic regression (C = 1) trained on batches 1-3; candidates trained on batches 1-5 with C in {.01, .1, 1}; selection on batch 6 including the incumbent; evaluation on batches 7-10 (7,977 observations); symmetric 0/1 decision cost primary. Source archive sha256 `91e8f466f202e7a093d657673ce47311c3e90416f7df3057966058961c351fe4` (equals the local `data/raw/gas_sensor/uci-224.zip`).
- **Exposure status: exploratory; all batches had prior repository exposure** (registration says so explicitly). It is an exposed holdout and cannot support confirmatory claims. The earlier PyTorch-softmax protocol is not reproduced; this is a new model family.
- Metric: errors; clairvoyant batch-boundary two-state DP with switch cost 1, initial incumbent deployment, no label cost; always-challenger cost includes its initial switch (2983 + 1).
- Reported: 3,403 vs 2,983 errors = 12.342%; clairvoyant 2,955 vs always-challenger 2,984 = 0.972%.
- Recomputed from the stored batch-level costs (`audit_recompute.py` F5): incumbent 3403, challenger 2983 (n 7977), reduction 12.342%; DP optimum 2955 with sequence challenger / incumbent / challenger / challenger; always-challenger 2984; headroom 0.9718%. Per batch (errors incumbent / challenger): b7 1306 / 1027, b8 106 / 137, b9 179 / 176, b10 1812 / 1643.
- **Code rerun in this environment** (Python 3.13.1, scikit-learn 1.6.1, numpy 2.4.2, scipy 1.17.1; patched ROOT so nothing was written into the sibling worktree; `gas_rerun_root/`): same selection (C = .1) but 3,416 vs 2,974 errors (12.939%), clairvoyant 2,943 vs always 2,975 (1.076% headroom); same optimal sequence. So the exact 3403 / 2983 is not reproducible across solver or library versions (deltas of 9 to 13 errors), though the qualitative picture (about 12-13% predictive gain, about 1% headroom) holds.
- **Status: PARTIALLY_VERIFIED** (stored artifact exactly; fresh code rerun within about 1 percentage point).
- Interpretation notes: 12.34% is predictive headroom of a challenger; 0.97% is the switching headroom relevant to a rollback policy; they must not be conflated. The 0.97% is a post-hoc hindsight DP over 4 batches (not an expected value or online regret), at switch cost 1 and zero label cost, so label cost can only reduce it. Batch 8 (n = 294) is the only batch where the challenger is clearly worse (137 vs 106 errors), which is what produces any headroom. Timestamps within batches are unverified (no natural delay).

---------------------------------------------------------------------------------------------------

## F6. Persistence obstruction and the estimand claim

- Branch `research/shiftlab-dependence-gates-2026-10-31`; doc `docs/dependence_sprint/03_IMPOSSIBILITY_AND_FEASIBILITY.md` (`001e878de519afa3acf012deca0982527486cd34`); scripts `scripts/dep_sprint/gate_ab.py` and `gate_b_oracle.py` (`001e878d`), outputs `outputs/dep_sprint/gate_ab.json`, `gate_b_oracle.json` (T = 2000, 6000 paths per cell, rng seed 11); estimand discussion in `11_SAFE_SWITCHING_INTEGRATION.md`.
- **What is bounded (exactly).** Let L_t follow the lazy-resample chain C(delta, pi): x_1 ~ Bern(pi); at each step with probability delta redraw Bern(pi), else keep. Then for any (possibly randomized, adaptive-query, delayed, budget-limited) test phi with P_{r0}(reject) <= alpha,
  P_{r0+eps}(reject) <= alpha + eps (1 + (T-1) delta).
  It bounds the power, against the specific alternative "same chain with marginal r0+eps", of any test that is level-alpha under the specific null chain with the same delta. It does not bound power against other alternatives, does not say a stationary-marginal-null test must be that conservative in general, and it is only an upper bound.
- **Derivation check.** Couple the two chains with the same switch uniforms and a maximal coupling of Bern(r0) and Bern(r0+eps) at each redraw (use one uniform U, compare U < r0 and U < r0+eps; mismatch probability exactly eps). Paths coincide unless some redraw mismatches; the number of redraws is 1 + Bin(T-1, delta) and is the same under both measures because switch events are shared, so P(paths differ) <= eps * E[#redraws] = eps(1 + (T-1)delta) by a union bound. Any observation scheme is a (randomized) function of the path, so data processing gives TV(observations) <= TV(paths) and power <= level + TV. Correct. The doc's consequence ((T-1)delta >= 6.5 for power .8 at eps .1, alpha .05) follows: 0.8 <= 0.05 + 0.1(1+x) gives x >= 6.5. **VERIFIED (proof re-derived).**
- **Exact numerical check (n = 16, r0 = 0.3, eps = 0.1, alpha = .05, full enumeration of 2^16 paths with a randomized Neyman-Pearson test; `audit_recompute.py` F6).** delta 5e-4: TV .10022, NP power .0667, bound .1507; delta .01: .1042, .0678, .165; delta .1: .1250, .0804, .30; delta 1: .3309, .2131, 1.65. Doc reports .067, .068, .080, .213 and TV .1002 vs coupling bound .1008: all match. (The doc does not state r0 and pi; r0 = 0.3 reproduces it.)
- **Oracle table at T = 2000** (`gate_b_oracle.json`; the stored values match the doc table; Monte Carlo not rerun): eps = .10, T*delta = 5: oracle power .0985, coupling ceiling .65; T*delta = 20: .184; 100: .476; 500: .976. The table, not the bound, is what shows the practical power loss: the coupling ceiling is loose (0.35 to 1.0) at the same points. **Status: DOC_ONLY for the Monte Carlo, with the stored JSON consistent.**
- **The estimand claim.** The sentence "false alarms under a stationary-marginal null are valid detections of the conditional-risk estimand" is logically correct: in a persistent chain the conditional mean E[L_t | F_{t-1}] equals the last value for most steps, so H0-cond (conditional excess <= 0) is false on every path with a bad stretch, and a valid H0-cond e-process rejecting there is a true rejection of H0-cond (a "false alarm" only relative to H0-marg). The caveats: (a) validity of the specific e-process under H0-cond with delayed, selectively sampled feedback was not independently proven in this sprint; (b) economic usefulness of such an alarm is *not* implied by its validity; F4 shows it depends on whether an action with regime-local benefit exists (variant A -50% net cost, variant B +6 to +10%); (c) Gate-A numbers (marginal null with persistence: pprm .35, HG_f0.2 .1385 at delta .5) support only that marginal-null FAR is inflated by persistence.

---------------------------------------------------------------------------------------------------

## Corrections and overstatements found

1. F1: "32 cells x 600 seeds" supports only a 14-cell paired estimate from 8 conditions of one generator. Pooled benign FA hides per-cell values up to .307 (H2c, `biased/concept1.5`, true harm .076 < .10 threshold). H2c is outperformed by C7a (-.19 / -.13) and reverses on exposed Gas. D1's comparator is chosen from the same realised cell means.
2. F2c: the "20% vs 30%" switch-rate sentence is not reproduced (57% vs 68%, 47.5% vs 63%); "n.s." labels on `cert_switch - ph_switch` contradict their own CIs; HG and PH both lose to never switching in exactly the scenarios where HG beats PH.
3. F2a: the "PPRM" arm is a local source-inspired parent, not the published method; HG vs PPRM gain is therefore a gain over a local variant.
4. F2e: HG dependence false alarm "up to .23" is not what the hg-validation artifact shows (up to .295 for the uniform-cap arm at rho .98, 20% labels).
5. F3: "no saved artifact" for the critic's baseline is stale (archived at `1a717bc`); the range 7.67-10.20% is a world-average over four worlds with in-sample BEST selection and is concentrated in W1 (per-world -37% to +14%).
6. F4: three-digit absolute costs are single-draw values (seed 31) with +-10-20 run-to-run variability; quote ratios.
7. F5: 3403 / 2983 is not reproducible across library versions (rerun: 3416 / 2974); exposed data; 0.972% is hindsight, zero label cost.
8. F6: the persistence bound alone does not establish "no useful power"; the oracle Monte Carlo does. The bound is attached to a particular alternative class.
9. Process: earlier audits' branch SHAs partially lag current HEADs (e.g., exhaustive branch HEAD `93a3ecf3...` vs the cited `ad6cedf`; sweet-lovelace head `e9e68574` vs cited `d1b173b`); the artifact commit SHAs above are per-file last-change commits and are the ones to cite.

---------------------------------------------------------------------------------------------------

## Reuse inventory for the engineering team

All paths are relative to the named worktree under `C:\Users\nigel\OneDrive\桌面\ICML\`. SHAs are `git log -1 --format=%H -- <file>`. Worktrees are read-only; copy or import, never write there.

### Monitors and e-processes
| component | file | commit | notes |
|---|---|---|---|
| Page-Hinkley, CUSUM (`page_hinkley`, `cusum`), PR-CS, two-window | `branch-research-h2c-strong-baselines-and-generalization-2026-10-30/src/shiftlab/sota_search/detectors.py` | `2aa6a8b849bf3cb502b9991b7962155f34de4b53` | per-stream functions on a `sim` dict; `first_cross` helper |
| H2c = `pp_cost_guided(mode="guided_disc", gamma=.995)`; discounted Kelly `fix_cost`/`pp_fix`; cost ONS `pp_ons`; multi-horizon `pp_cost_multi`; SR e-detector `sr_cost_tight`; PPRM-inspired `pprm`/`pprm_tight`; Brier ONS | same file | same | `uniform_cap` option in `_pp_parts`; no supermartingale unit test |
| HG with uniform (predictable) cap: `Cfg(cap_mode="sup", gamma, gate_w, release="prefix")` through `engine.run` | `branch-research-shiftlab-mandate-gap-closure-2026-10-30/src/shiftlab/gap/engine.py` | `0b025969c515a83f12cfabf25579b3117beb30c6` | hard budget, delayed-release, pacing, allocation options; PH/CUSUM/PPRM reference arms live in the confirmation scripts |
| Predictable-cap tests (exact finite-support) | `.../tests/gap/test_engine.py` | `07826329dfd631f66cf540e2edf062f0b9336707` | the only supermartingale-level unit test found |
| HG uniform-cap development variant | `branch-research-h2c-strong-baselines-and-generalization-2026-10-30/scripts/sota_search/uniform_cap_cost.py` | `79e14272f0f20ade251cdcbbbb8c2b3f2eb15091` | |
| Exact-drift counterexample (cap) | `branch-research-hg-validation-and-novelty-2026-10-30/outputs/hg_validation/02_EXACT_NULL_TESTS.json` | `79e14272...` | |
| Sethi Algorithm 1 (marginal-null Markov test) | `branch-research-shiftlab-dependence-gates-2026-10-31/src/shiftlab/dep/sethi.py` | `026500db9dac67da8b9dc239870356a85c571811` | `statistic`, `threshold` |

### Batch / fixed-sample paired test and certified switching
| component | file | commit |
|---|---|---|
| Fixed-sample paired batch test `Batch` (nv, thr), disagreement-gated alarm `AlarmG`, runner `run` | `shiftlab-promising-directions-2026-10-30/docs/promising_directions/results/adversarial_review/bl.py.txt` (rename to .py; hard-coded repo path) | `1a717bcd04a0fdc9b9908e430d8e27b3f39962d5` |
| `Cert` (P3/P3b), `Alarm`, `make_stream`, simulators, `analyse_b2` | `shiftlab-promising-directions-2026-10-30/scripts/promising_directions/b1_certified_switching.py` | `041bc26fafeed1132f17ed762ddbfdcff02e34f2` |
| Tests | `.../tests/promising_directions/test_b1_certified_switching.py` | `041bc26f...` |
| Online switching controllers (frozen, periodic retrain, rolling recal, PH-triggered, HG-triggered `OnlineHG`, certified `cert_*`, hysteresis, cost-gated), `total_cost` | `branch-research-shiftlab-mandate-gap-closure-2026-10-30/src/shiftlab/gap/q3.py` | `290b0560116e41aebb427bef16d484d9fcb594c7` |
| Q3 driver and cost grid | `.../scripts/gap/e8_q3.py` | `290b0560...` |
| Dependent-regime switching world (cond / marginal triggered, hold, oracle) | `branch-research-shiftlab-dependence-gates-2026-10-31/scripts/dep_sprint/estimand_switching.py` | `026500db...` |

### Generators and analysis
| component | file | commit |
|---|---|---|
| G5 proxy-defect generator (8 conditions x 4 shifts), harness, G6 delay/budget | `branch-research-h2c-strong-baselines-and-generalization-2026-10-30/src/shiftlab/sota_search/{generators,harness,g6}.py` | `e164d63310cbec7fed4efc16dbf726b20abf0a17` / `b00e567b80119fa1d86a7259ffc8d95bb124eb5e` / `bdcd1b51f76ff981871a1488ce3a836bcc0df151` |
| G3-G6 world pools (15 harm + 6 null) | `.../branch-research-shiftlab-mandate-gap-closure-2026-10-30/src/shiftlab/gap/worlds.py` | `290b0560...` |
| Two-level (cells then seeds) paired bootstrap, Holm | `.../scripts/gap/analyze_confirmation.py` (`85529116...`); `.../h2c.../scripts/sota_search/g5_confirmation_analysis.py` (`44119c61...`) | |
| Run store / Wilson / CP intervals | `.../src/shiftlab/gap/store.py` | `290b0560...` |

### Per-seed artifacts (all on disk, gitignored in their worktrees; re-verify checksums before use)
| artifact | path | sha256 / commit | rows |
|---|---|---|---|
| G5 frozen confirmation | `branch-research-h2c-strong-baselines-and-generalization-2026-10-30/outputs/h2c_next/g5_confirmation_per_seed.parquet` | sha256 `ed5923e9486c6bc9c8a0d1497f68c74563a4221f5644721f508dfd7fbbf66ba7` | 345,600 |
| e15 frozen confirmation (HG, PH, CUSUM, PPRM, cost, HG variants) | `branch-research-shiftlab-mandate-gap-closure-2026-10-30/outputs/gap_closure/e15_confirm/perseed.parquet`; round 2 `e15b_confirm_round2/perseed.parquet` | `85529116...` | 168,000 |
| Q3 switching benchmark | `.../outputs/gap_closure/e8_q3/perseed.parquet` | `290b0560...` | 77,760 |
| HG G3 confirmation | `branch-research-hg-validation-and-novelty-2026-10-30/outputs/hg_validation/05_G3_PER_SEED.parquet` | `edf4a952...` | 10,000 |
| B2 certified switching | `shiftlab-promising-directions-2026-10-30/docs/promising_directions/results/b2/per_seed.npz` | `041bc26f...` | 500 per world x setting x policy |
| Gas batch-level costs | `shiftlab-exhaustive-evaluation-2026-10-30/docs/exhaustive_evaluation/gas_headroom_results.json` | `ad6cedf4...` | 10 batches x 4 models x 3 multipliers |

### Gas replay adapter and data
- Local data: `shift-research-starter/data/raw/gas_sensor/uci-224.zip` (sha256 `91e8f466f202e7a093d657673ce47311c3e90416f7df3057966058961c351fe4`) plus receipt.
- Batch-level logistic bank and DP: `shiftlab-exhaustive-evaluation-2026-10-30/scripts/exhaustive_evaluation/explore_gas_headroom.py` (`ad6cedf41c182ee8b0fcbda71fe09a73659959af`; it refuses to rerun if its registration file exists, and writes into its own repo root; use a patched ROOT as in `WT/outputs/decision_value/development/audit/gas_rerun_root/`).
- Event-level counterfactual replay of H2c / Kelly / ONS on gas (D2): `origin/claude/sweet-lovelace-pznpjq:research/novelty_validation_2026-10-30/scripts/d2_gas_sensor_replay.py` and `d2_followup_paired_and_diagnostic.py` (head `e9e68574a474ce347e78e4a7d856674bfbdcf3d2`; read with `git show`).
- Earlier candidate evaluation script: `shiftlab-exhaustive-evaluation-2026-10-30/scripts/exhaustive_evaluation/evaluate_gas_sensor_candidates.py` (no per-file commit recorded at audit time).

### Caution for reuse
- None of the e-process implementations has a unit test of the supermartingale property except the finite-support cap test in `tests/gap/test_engine.py`.
- No comparator is a faithful reproduction of the published method (PPRM, Active RCPS, CAMS not implemented); label them "inspired".
- G5 / e15 / Q3 / B2 have fixed delay 5 (Q3: 5 or 50), known nominal risk, and one or few generator families.
