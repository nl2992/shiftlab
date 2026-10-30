# Mandate completion matrix: state at the START of this task (Phase 0 audit)

Branch `research/shiftlab-mandate-gap-closure-2026-10-30` cut from `origin/research/shiftlab-sota-synthetic-search-2026-10-29` at `bb74057`. Statuses are derived from source code, registries (`outputs/sota_search/registry_*.sqlite`, 5,999 rows, 281 distinct configurations) and tracked files, not from Markdown claims. Provenance finding: `outputs/*` is git-ignored, so the G2 held-out summary / registry and the CRSP replay outputs were **never committed** and are absent from every checkout; their numbers survive only as prose in docs 11 and 16. They are marked REPRODUCTION_REQUIRED and are not re-run here (a reconstruction would not be an independent confirmation; CRSP is barred in this task). No real-data file was opened.

| id | requirement | prior protocol | existing implementation | evidence of execution / result files | configs | worlds | seeds | validity status | missing components | next action | status |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q1-BASE | Q1 baselines A1-A8 (MMD, C2ST, BBSD, CUSUM, PH, two-window, P-R CS, WATCH, PPRM, PP-E) | doc 01, 03 | src/shiftlab/sota_search/detectors.py | registry_q1_{cheap,window,cand}.sqlite; 4,275 runs | 225 | 19 dev worlds | 200 seeds, block 1000 | none VERIFIED_REPRODUCTION; 23/225 empirical thresholds exceed 0.07 on fresh nulls | BOCPD; exact ADWIN; verified reproductions (sources inaccessible) | keep as baselines; no re-run | PARTIAL |
| X1 | Tight one-sided bet cap (extra candidate) | doc 03b | detectors.pp_eprocess(tight=True) | doc 06 | 108 | 19 | 200 | tight cap fixes loose baseline; later found to depend on the current covariate | - | repair in Phase 1 | COMPLETE |
| S01 | Decision-harm-aware PPRM | doc 03b | pp_cost_tight | doc 06 | 36 | 19 | 200 | valid under iid | - | none | COMPLETE |
| S02 | Multi-start (SR) e-detector | doc 03b | sr_cost_tight, sr_brier_tight | doc 06 | 72 | 19 | 200 | empirical thresholds, Brier version 0.12 null FA | - | none | COMPLETE |
| DK-HG-BD | Novelty fixes DK, HG, BD on dev pool | doc 09, 10 | detectors.pp_fix | q1_baselines_summary_fix.csv | 48 | 19 | 200 | covariate-dependent cap (defect found this phase) | - | re-run under repaired cap | COMPLETE |
| G1-HELD | G1 held-out confirmation of frozen finalists | doc 11 part 1 | run_heldout.py | registry_heldout_g1.sqlite (tracked) | 7 arms x 2 fracs | 8 | 400 | single run, frozen config | - | none | COMPLETE |
| G2-HELD | G2 held-out confirmation of frozen finalists | doc 11 part 2 | run_heldout.py G2 | numbers only in doc 11; heldout_g2_summary.csv and registry_heldout_g2.sqlite are git-ignored and absent from every checkout | 7 arms x 2 fracs | 9 | 400 | PROVENANCE INCOMPLETE: not independently verifiable | tracked summary CSV and registry | reproduce only as a clearly labelled reconstruction; not a new confirmation | REPRODUCTION_REQUIRED |
| CRSP | CRSP replay (provenance audit only) | doc 15, 16 | run_crsp_replay.py | outputs/sota_search/crsp_replay absent; numbers only in doc 16 | - | 10 cohorts | 20 query seeds | PROVENANCE INCOMPLETE; real data not touched here | tracked outputs | none (barred from rerun) | REPRODUCTION_REQUIRED |
| S03 | Proxy-reliability-adaptive monitoring | mandate Phase 2 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S04 | Growth-aware active querying | mandate Phase 2 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S05 | Robust growth/variance hybrid | mandate Phase 2 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S06 | Budget-paced delayed query allocation | mandate Phase 2 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S07 | Robust pro-active inference (pool-based) | mandate Phase 3 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S08 | Balanced growth-aware sampling | mandate Phase 3 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S09 | Q2 model certification + extensions S09a-e | mandate Phase 4 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S10 | Q3 cost-aware switching | mandate Phase 5 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S11 | Amortised approximation of exact acquisition | mandate Phase 6 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| S12 | Efficient multi-scale distribution testing | mandate Phase 6 | - | - | 0 | 0 | 0 | - | everything | implement + run | NOT_STARTED |
| G3 | Markov-switching generator | mandate Phase 7 | - | - | - | - | - | - | everything | implement + test | NOT_STARTED |
| G4 | Synthetic finance-oriented generator | mandate Phase 7 | - | - | - | - | - | - | everything | implement + test | NOT_STARTED |
| G5 | Strong proxy misspecification generator | mandate Phase 7 | - | - | - | - | - | - | everything | implement + test | NOT_STARTED |
| G6 | Feedback and dependence stress generator | mandate Phase 7 | - | - | - | - | - | - | everything | implement + test | NOT_STARTED |
| P1-STORE | Per-seed experiment storage | mandate Phase 1.1 | aggregates only (secondary_metrics) | - | - | - | - | cannot recover per-seed outcomes | per-seed table | implement | NOT_STARTED |
| P1-PAIR | Paired design / common random numbers | mandate Phase 1.2 | label mask by lseed per world | - | - | - | - | partial | per-seed paired outputs | implement | PARTIAL |
| P1-BUDGET | Hard pathwise query budget + charge at issue | mandate Phase 1.3 | expected (Bernoulli) budget only | - | - | - | - | hard caps not implemented | implement + test | implement | NOT_STARTED |
| P1-VALID | Statistical-validity audit (conditional null, covariate-dependent wagers, label timing) | mandate Phase 1.4 | doc 12 (claims T1-T7) | doc 12 | - | - | - | INVALID as implemented: cap depends on the current covariate | audit + repair | audit | INVALID |
| STRESS | 14 statistical stress experiments | mandate Phase 8 | none (doc 12: not run) | - | - | - | - | - | everything | run | NOT_STARTED |
| SEARCH | 500-1,500 distinct configurations | mandate Phase 9 | 281 distinct (5,999 rows) | registries | 281 | - | - | - | coverage matrix, dedup | audit + extend | PARTIAL |
| PERF | Runtime / memory profile | mandate Phase 10 | none (doc 07) | - | - | - | - | - | everything | run | NOT_STARTED |
| SYNTH | Cross-experiment synthesis and second-round fixes (<= 3) | mandate Phase 11 | doc 08 (one round, 225 configs) | doc 08 | - | - | - | - | updated matrix, 3 fixes on new dev worlds | run | PARTIAL |
| CONFIRM | Independent synthetic confirmation on new G3-G6 pools | mandate Phase 12 | none | - | - | - | - | - | everything | run | NOT_STARTED |
| LIT | Literature novelty check / faithful published reproductions | mandate Phase 13 | blocked (sources unreachable) | doc 01 | - | - | - | - | primary sources | none possible offline | BLOCKED |
