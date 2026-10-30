# Report A - experimental coverage
Mandate requirements by status (rows: at the start of this task; columns: now). Statuses use the allowed vocabulary only; COMPLETE requires code + test or validity experiment + protocol + executed results.

| initial | BLOCKED | COMPLETE | PARTIAL | REPRODUCTION_REQUIRED |
|---|---|---|---|---|
| BLOCKED | 1 | 0 | 0 | 0 |
| COMPLETE | 0 | 5 | 0 | 0 |
| INVALID | 0 | 1 | 0 | 0 |
| NOT_STARTED | 0 | 13 | 6 | 0 |
| PARTIAL | 0 | 2 | 2 | 0 |
| REPRODUCTION_REQUIRED | 0 | 0 | 0 | 2 |

| id | requirement | initial | final | limitation |
|---|---|---|---|---|
| Q1-BASE | Q1 baselines A1-A8 (MMD, C2ST, BBSD, CUSUM, PH, two-window, P-R CS, WATCH, PPRM, PP-E) | PARTIAL | PARTIAL | source-inspired only; BOCPD absent |
| X1 | Tight one-sided bet cap (extra candidate) | COMPLETE | COMPLETE | mild empirical effect at Kelly bets |
| S01 | Decision-harm-aware PPRM | COMPLETE | COMPLETE | - |
| S02 | Multi-start (SR) e-detector | COMPLETE | COMPLETE | no anytime validity claim |
| DK-HG-BD | Novelty fixes DK, HG, BD on dev pool | COMPLETE | COMPLETE | dev pool only |
| G1-HELD | G1 held-out confirmation of frozen finalists | COMPLETE | COMPLETE | G1 only, same family |
| G2-HELD | G2 held-out confirmation of frozen finalists | REPRODUCTION_REQUIRED | REPRODUCTION_REQUIRED | not recoverable here; not re-run (would not be an independent confirmation) |
| CRSP | CRSP replay (provenance audit only) | REPRODUCTION_REQUIRED | REPRODUCTION_REQUIRED | mark provenance incomplete |
| S03 | Proxy-reliability-adaptive monitoring | NOT_STARTED | PARTIAL | structured subset only |
| S04 | Growth-aware active querying | NOT_STARTED | PARTIAL | exact RPOQ gaps on the toy instance only |
| S05 | Robust growth/variance hybrid | NOT_STARTED | COMPLETE | published Robust-ASI guarantees not claimed |
| S06 | Budget-paced delayed query allocation | NOT_STARTED | PARTIAL | no DP at scale; v1 confounded (disclosed), v2 corrected |
| S07 | Robust pro-active inference (pool-based) | NOT_STARTED | PARTIAL | PAI baseline is source-inspired, not a verified reproduction; no tests |
| S08 | Balanced growth-aware sampling | NOT_STARTED | PARTIAL | monitoring only; estimation-quality arm not run; BAI not faithful |
| S09 | Q2 model certification + extensions S09a-e | NOT_STARTED | COMPLETE | structured subset; baselines source-inspired |
| S10 | Q3 cost-aware switching | NOT_STARTED | COMPLETE | idealised recalibration / retrain; 12 of 108 cost cells; exact reference toy only |
| S11 | Amortised approximation of exact acquisition | NOT_STARTED | PARTIAL | toy instance only; exact-oracle cost counted |
| S12 | Efficient multi-scale distribution testing | NOT_STARTED | COMPLETE | Gaussian two-sample worlds; classifiers: logistic / LDA only |
| G3 | Markov-switching generator | NOT_STARTED | COMPLETE | - |
| G4 | Synthetic finance-oriented generator | NOT_STARTED | COMPLETE | synthetic only |
| G5 | Strong proxy misspecification generator | NOT_STARTED | COMPLETE | - |
| G6 | Feedback and dependence stress generator | NOT_STARTED | COMPLETE | - |
| P1-STORE | Per-seed experiment storage | NOT_STARTED | COMPLETE | runtime / RSS are batch-level |
| P1-PAIR | Paired design / common random numbers | PARTIAL | COMPLETE | - |
| P1-BUDGET | Hard pathwise query budget + charge at issue | NOT_STARTED | COMPLETE | - |
| P1-VALID | Statistical-validity audit (conditional null, covariate-dependent wagers, label timing) | INVALID | COMPLETE | no proof under dependence |
| STRESS | 14 statistical stress experiments | NOT_STARTED | COMPLETE | empirical, not a proof |
| SEARCH | 500-1,500 distinct configurations | PARTIAL | PARTIAL | no full S03 grid; no DP at scale |
| PERF | Runtime / memory profile | NOT_STARTED | COMPLETE | single machine |
| SYNTH | Cross-experiment synthesis and second-round fixes (<= 3) | PARTIAL | COMPLETE | fixes selected on dev seeds |
| CONFIRM | Independent synthetic confirmation on new G3-G6 pools | NOT_STARTED | COMPLETE | single run of a frozen protocol |
| LIT | Literature novelty check / faithful published reproductions | BLOCKED | BLOCKED | - |

**Finally completed:** per-seed storage, paired design, hard budgets, validity audit and repair, the 14-experiment stress matrix, generators G3-G6, S05, Q2 (S09), Q3 (S10), S12, runtime / memory benchmarks, second-round fixes (none accepted), two frozen confirmation rounds.
**Executed but reduced (PARTIAL):** S03 (108 of 432 grid points per parent, plus a sensitivity run), S04 (exact oracle gaps toy-only; v1 floor confound, v2 development gain not confirmed), S06 (no DP at scale; v1 confounded, v2 development gain not confirmed), S07 (PAI baseline is source-inspired, not verified), S08 (monitoring only, development gain not confirmed), S11 (single toy instance; negative), the configuration search (count in range by hash, few genuinely different algorithms).
**Blocked or unreproducible:** verified reproductions of published methods and the literature novelty check (sources unreachable); G2 held-out and CRSP replay artifacts (never committed -> REPRODUCTION_REQUIRED, not re-run, no real data touched).
**Process errors disclosed and handled:** S06 v1 floor confound (reran as v2); S12 v1 saturated shifts with a negative-harm "harmful" direction (kept as `e12_s12_dist_v1_saturated_wrong_harm_sign.csv`, rerun); confirmation round-1 classical-arm names mixed two fractions (rerun with identical seeds, the mixed file kept); runtime benchmark first draft timed under `tracemalloc` (rewritten, clean timings); the earlier phase's `.gitignore` lost its G2/CRSP artifacts (whitelisted now); a stray `.venv` was created in the main checkout by an `uv run` started from the wrong directory (gitignored; deletion was denied by the sandbox, left in place).
