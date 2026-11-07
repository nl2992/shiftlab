# 07 Matched baseline comparisons (2026-10-30)

Scope: every matched comparison executed or verified in this programme. All paths are relative to `docs/promising_directions/` in this worktree. Nothing here is confirmatory. Status vocabulary follows `00_REPOSITORY_AUDIT.md` (VERIFIED / DOC-ONLY) and `02_LITERATURE_AND_NOVELTY_AUDIT.md` (VERIFIED_REPRODUCTION / FORMULA_ADAPTATION / SOURCE_INSPIRED / INAPPLICABLE_INFORMATION_CONTRACT / UNVERIFIED).

Important qualifier on the label "SOURCE_INSPIRED vs VERIFIED_REPRODUCTION". `02` assigns reproduction status only to published-source comparators. Programme-internal comparators (P0, P1, calendar C*) are not published algorithms and receive no `02` status. Where a comparator has no `02` entry, this file says so rather than assigning one. No H2c comparator is a verified published reproduction (`01_EVIDENCE_MATRIX.md` section 1 Lane B caveats; `06_H2C_AND_HG_REPRODUCTION.md` section 2).

## 1. Matched comparisons executed or verified

| ID | Candidate vs comparators | Matching (same information / budget / delay / costs) | Strongest matched baseline | Result (source) | Decision | Evidence level |
|---|---|---|---|---|---|---|
| A1 | J (exact joint planner, `FirstPromotionDecomposedGame`) vs C* (best fixed calendar of <= B slots with exactly optimised risk-constrained switching, `CalendarOpportunityGame`) | Same exact two-law game: causal-null false-promotion risk <= alpha with root-mixture calibration, pathwise budget B, release delay d, reversible promotion (`04_EXACT_ORACLE_SEPARATION.md`; `protocols/A1-exact-separation.md`) | C* itself. Under public randomness, history-adaptive acquisition + optimal switching equals J (Proposition A0 in `03_FORMAL_PROBLEM_AND_INFORMATION_CONTRACT.md`), so C* is the only information-matched separable comparator | Primary (d=2, 144 cells): max relative gap 0.3645% (10787546091/2959163041129), 8 cells with gap > 0. Primary+secondary (288 cells): max 0.8741% (22608701046/2586568221299), 23 cells with gap > 0. 0 J <= C* violations. Adversarial (200 instances, T=6, B=3, d=2): max gap 0 (`results/a1/summary.json`) | KILL (`results/a1/summary.json`: `decision_primary_only`, `decision_grid_primary_plus_secondary`) | Development, known-model synthetic, exact rationals; verified by orchestrator recomputation (`RESEARCH_LEDGER.md`) |
| B1-a | P3 (certified switch, cap p_min/2) vs P0 never-switch, P1 always-challenger, P2 incumbent-alarm switch | Same T=2000, delay 5, c_q=0.05, B in {200,400}, c_s in {5,20}, alpha 0.05, 500 seeds paired across policies (`protocols/B1-certified-switching.md`; `results/b1/summary.json` `meta`) | BEST = lowest world-averaged cost among P0-P2 per (B,c_s): P2, P0, P2, P0 for B200_cs5, B200_cs20, B400_cs5, B400_cs20 (`results/b1/summary.json` `q1_settings.*.best`) | P3 reduces world-averaged cost vs BEST by 3.35%, 3.50%, 0.14%, 1.07% (relative reductions recomputed from `q1_settings`); CI excludes 0 in 3 of 4; B400_cs5 CI [-2.16, 1.08] includes 0 | Q1 MIXED (max 3.5% vs the 10% bar) (`results/b1/summary.json` `decisions`) | Development, synthetic, 4 worlds, one generator |
| B1-b | P4 (persistence-aware, hazard 1/150 declared) vs P3 | Same as B1-a | P3 | P4 minus P3 in W3: relative gain 0.24%, 0.39%, 0.62%, 0.82%; W1 P4 worse by 10.5%, 22.3%, 9.5%, 23.9% (`results/b1/summary.json` `q2_settings`) | Q2 NOT SUPPORTED | Development; P4 uses a known hazard, so it would be a plug-in result in any case (`protocols/B1-certified-switching.md`) |
| B2 | P3b (P3 with propensity-matched bet cap q_t/2) vs P0, P1, P2 (P3 and P5 reported for reference) | Same worlds, B, c_s, c_q, delay, alpha, p_min as B1; fresh seeds 20261101, 500 per cell (`protocols/B2-propensity-cap.md`; `results/b2/NOTES.md`) | BEST = P2, P0, P2, P0 per setting (same ordering as B1) (`results/b2/summary.json` `q1_settings.*.best`). P2's Kelly cap is 3.0 vs matched rate/2 of 0.05 (B=200) or 0.10 (B=400), so it is not under-capped and P2b was not added (`results/b2/NOTES.md`) | P3b reduces world-averaged cost vs BEST by 10.20%, 9.65%, 7.88%, 7.67%. Passes all three criteria only in B200_cs5. W3 +14.29% and W4 +10.02% worse than BEST in B400_cs20 (`results/b2/summary.json`) | Q1 MIXED (`results/b2/summary.json` `decisions`) | Development round 2, selected after seeing B1 diagnostics; NOT confirmation (`protocols/B2-propensity-cap.md`) |
| H2c-G5 | H2c (`pp_cost_guided`, `guided_disc`, gamma=0.995) vs C1 fix_cost (discounted Kelly), C2 cost_ons, C7a sr_cost_tight | 14 harm / 10 benign / 8 null cells, 600 seeds, one generator family (`06_H2C_AND_HG_REPRODUCTION.md` section 2) | Per-cell better of C1/C2, chosen from realised means. C7a is empirically calibrated and more powerful (H2c -0.19 / -0.13) but has no guarantee | Advantage vs better comparator +0.086 [0.059, 0.113] at 10% and +0.094 [0.063, 0.125] at 20%; power 0.382 / 0.640; benign FAR 0.067 at 20%; null FAR max <= 0.027; harm cells won 13/14 and 14/14 | Inherited; analysis VERIFIED by rerun, simulation partial | Frozen confirmation (synthetic, known nominal cost, fixed delay 5); interpretation limited: H2c reduces exactly to discounted Kelly with a substituted moment ratio (max abs dlogW 8.9e-16) (`01_EVIDENCE_MATRIX.md` Lane B) |
| HG-parent | HG vs PPRM parent (hg-validation G3) | Per hg-validation (`01_EVIDENCE_MATRIX.md` Lane C) | PPRM parent; ONS and plain discounting were NOT beaten | +0.050 / +0.131 vs parent | Inherited, DOC-ONLY | Limits novelty claim |
| HG-PH/CUSUM | HG vs Page-Hinkley / CUSUM | Per gap-closure docs | Page-Hinkley / CUSUM | Power -0.066 / -0.110 (not significant) | Not a win (DOC-ONLY) | Inherited |
| HG-e15 | HG within e15 confirmation, 21 worlds | 400 seeds harm / 1000 null; Holm family 10 | e15 internal comparator | +0.029 [0.012, 0.046] (Holm p 0.004; recompute 0.0288) and +0.052 [0.020, 0.090] (Holm p 0.003; recompute 0.0518) | Inherited; analysis VERIFIED | Synthetic; HG invalid under dependent outcomes (FAR up to .23) (`01_EVIDENCE_MATRIX.md` Lane C) |

## 2. Comparator status per `02_LITERATURE_AND_NOVELTY_AUDIT.md`

| Comparator in this programme | Nearest source (02 id) | 02 reproduction status | Classification for this file |
|---|---|---|---|
| A1 C* calendar + optimal switching | C9 RAO* (AAAI 2016), C10 recursively constrained POMDPs / robust FSC | C9 UNVERIFIED; C10 FORMULA_ADAPTATION for the fixed-controller product LP (agrees with exact J on six cells), synthesis UNVERIFIED | In-repo exact solver at `2bd2e8e` (file sha256 in `results/a1/summary.json` `provenance`); not a published-paper reproduction |
| B1/B2 P0, P1 | none (trivial policies) | not assigned | Programme-internal |
| B1/B2 P2 (cost-null discounted-Kelly incumbent alarm, IPW increment, nominal 0.15) | A1 Podkopaev-Ramdas, A2 PPRM, A3 Xu et al. active RCPS | A1 FORMULA_ADAPTATION; A2 FORMULA_ADAPTATION (local `pprm` parent SOURCE_INSPIRED); A3 VERIFIED_REPRODUCTION at component level only (FTL parity <= 1.3e-15 at delay 1; COCOB port parity 2.2e-16), full learned-query reproduction incomplete | Not assigned in 02. Nearest classification: FORMULA_ADAPTATION of component sources, i.e. NOT a VERIFIED_REPRODUCTION of any published monitor |
| B1/B2 P3 / P3b paired certification | A3 (IPW, predictable q), A8 CAMS, A9 sequential MCS, C11 | A3 as above; A8 UNVERIFIED (not implemented; audit file missing); A9 UNVERIFIED; C11 UNVERIFIED | Candidate, not comparator. Its parts are established (`05_PAIRED_CERTIFICATION_THEORY.md`) |
| B1 P4 persistence-aware | none | n/a | Plug-in decision rule with declared hazard |
| H2c comparators C1, C2, C7a | A1/A2/A3 plus e-detectors B1 | No comparator is a verified published reproduction (`01_EVIDENCE_MATRIX.md` Lane B caveats) | FORMULA_ADAPTATION / SOURCE_INSPIRED level at best |
| HG comparator PH/CUSUM | B3 Page; Lorden | FORMULA_ADAPTATION (repo: PH cumulative-minimum is algebraically CUSUM) | FORMULA_ADAPTATION |
| SR / CUSUM e-detector adapter | B1 Shin-Ramdas-Rinaldo | FORMULA_ADAPTATION (fixed-stake paired adapter, 16 settings); matrix author did not read the body | FORMULA_ADAPTATION; not run in this programme |
| DQ pacing (B1/B2 P3 rate) | B5/B6 DE-Shiryaev / DE-CuSum; C6 Ryabchenko | SOURCE_INSPIRED (`DisagreementPacer` pacing idea); B1 in this programme used its own pacer (`results/b1/IMPLEMENTATION_NOTES.md`) | SOURCE_INSPIRED |

VERIFIED_REPRODUCTION appears for exactly one comparator family in `02`: component-level A3 (Xu et al.). Every other comparator used here is FORMULA_ADAPTATION, SOURCE_INSPIRED, in-repo, or unassigned.

## 3. Missing comparators (not run; outcome of any comparison with them is unknown)

From `01_EVIDENCE_MATRIX.md` section 3 and `00_REPOSITORY_AUDIT.md` section 4 (BASELINE_COVERAGE obligations, eleven open):

1. Robust finite-state controller (FSC) synthesis and controller synthesis certificates.
2. Finite-window CPOMDP.
3. Active RCPS full reproduction (A3 is component-level only).
4. PR monitoring.
5. PPRM faithful confidence sequence (the local parent is SOURCE_INSPIRED).
6. Hsu-Shekhar native (INAPPLICABLE_INFORMATION_CONTRACT via measurability obstruction; arXiv 2607.17409 is abstract-level scanned only).
7. Betting on Predictions native (A4, INAPPLICABLE_INFORMATION_CONTRACT).
8. PH / CUSUM / SR e-detector mapping to the paired certificate setting.
9. Nonpartitioned PFA (B2 in `02`; four-path numerical pilot only).
10. Sethi Markov (A12, reduced 2-state native pilot only).
11. Additional gaps recorded in `01`: state-independent adaptive acquisition; standalone always-query and immediate-deploy rows under the risk contract (NOT FOUND); CAMS (A8) not implemented; sequential model confidence sets (A9); economic retraining policies CARA (C1) and Regol et al. (C2), both UNVERIFIED and not implemented.

Consequence for B1/B2: BEST is the strongest among {P0, P1, P2} only. The set does not include CAMS-style disagreement acquisition with a plain (non-certifying) switching rule, an e-detector (SR/CUSUM) paired trigger, or an economic retraining rule. A P3b margin over BEST therefore cannot be read as a margin over the strongest published alternative.

## 4. Provenance pointers

- A1: protocol commit `0d03912`; solver commit `2bd2e8e41639073c8d22ffb17ef0bcc68111e321`; summary sha256 `5e121765c7550b9aff813bbc8c339e0cecda5b546ad6a85465126d3fe237a2b5` (`RESEARCH_LEDGER.md`).
- B1: protocol commit `1a742dc`; protocol sha256 `98f85250a95ae6e31857760ca33f2ebe1dc0c042762469b7d8f84cd557a82757`; summary sha256 `0062aec5eeba38caf93cdc69d307c9b957928ba0450b9911447566fc010a562e`.
- B2: protocol commit `af14d5a`; protocol sha256 `533a529ddda537ce8b925fdaf6b0b503cce46797ade2c7ca0d5a9b95202b6844`; summary sha256 `4af87b4fad2d9ca2ac5cfe32616728ba1fea0f0a3d98db06d38cbede2441b488`.
- H2c: results `44119c6`, preregistration `e164d63`, code `60930a4`; per-seed parquet sha256 `ed5923e9486c6bc9c8a0d1497f68c74563a4221f5644721f508dfd7fbbf66ba7` (`06_H2C_AND_HG_REPRODUCTION.md`).
