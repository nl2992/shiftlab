# 00 Risk register (Paper 3)

| # | risk | type | sev | mitigation |
|---|---|---|---|---|
| 1 | Overlap with Paper 1: late-label cutoff compositor and EQSDp already do budgeted acquisition plus economic switching; joint-acquisition claims can collapse into P1 | scientific | high | run EQSDp+cutoff and Wald+cutoff as mandatory comparators; claim only mechanisms absent from P1; never edit P1 files |
| 2 | Information-limited headroom: free labels worth <=5.3 units to tuned Wald; calendar exactly optimal at tight risk; 12 mechanisms and BCR tie tuned Wald/K-Wald | scientific | high | pre-register an oracle-information headroom screen before building controllers; stop/pivot if gap is negligible (<1%); keep negative results |
| 3 | All local real data (c4_sealed 27, saes_dev, atlas_v2, sprint_*) already exposed to Papers 1/2; no fresh confirmation set | scientific | high | label dev-exposed/exploratory; confirm only on registered synthetic seeds or newly fetched, checksummed streams; leave-family-out for Workstream D |
| 4 | Comparator fidelity: Gong-Zhang, Qiu, DISCERN, Gated are in-house adapters; DISCERN psi_E /4 bug in Atlas v2 numbers; author-code parity unverified | scientific | high | label NATIVE_SOURCE_FIDELITY / DOCUMENTED_ADAPTER / IN_HOUSE_HEURISTIC; rerun DISCERN post-fix; equal dev-only tuning budgets; do not reuse Atlas v2 headline numbers |
| 5 | Dependence validity: Markov/phi envelopes are assumptions; real streams serially dependent; e-process names do not imply validity | scientific | high | state filtration, predictability, dependence class per guarantee; twin-null and Markov-null stress tests; no guarantee claimed without proof or exact check |
| 6 | Contract mismatch: npz streams hold only paired losses; predictions are synthesised; feedback only on queried disagreements; paired comparison needs both losses identifiable | scientific | med | document per component; keep evaluator-only truth (change points, regimes, hindsight oracle) out of learner inputs; follow `contract/isolation.py` |
| 7 | Exact DP only scales to tiny T with known HMM; planner gap 0.7-1.2% at alpha .10, B=4 | scientific | med | DP as benchmark/certificate only; test approximate controllers on exact grid then large simulation |
| 8 | Tuning leakage / multiple looks across reused configs; seed ranges overlapping P1/P2 | scientific | med | disjoint registered seed ranges (`seed_registry.py`); confirmation opened once after freeze; ledger every attempt |
| 9 | Transfer leakage via shared source family (about 20 city-311 streams are one family) | scientific | med | group by family, leave-family-out; record holdout composition |
| 10 | Baseline suite not green on main: 52 failed + 8 errors (regimes module collision, eprocess.py SHA manifest, missing gitignored outputs, 1 start-mixture smoke) | engineering | med | run Paper-3 tests separately; avoid bare `import regimes` in Paper-3 code (importlib with unique names); record as known baseline failures |
| 11 | Full suite takes 98 min | engineering | low | targeted tests; full suite detached |
| 12 | Data absent from worktree; scripts hard-code `ROOT/data` and a sibling solver worktree path | engineering | med | single data-root env var in Paper-3 code; sha256 verification before use |
| 13 | Windows: non-ASCII path (桌面), OneDrive locking/sync, CRLF hash mismatch (UNVERIFIED), subprocess/tasklist hangs, 120 s tool timeout | engineering | med | pathlib + utf-8 everywhere; run long jobs detached with logs; check `.gitattributes`; keep large outputs untracked |
| 14 | OpenBLAS crashes / thread oversubscription with multiprocessing (24 logical CPUs) | engineering | med | `OPENBLAS_NUM_THREADS=1`; <=12 workers; resumable jsonl; watchdog |
| 15 | 8 GB laptop GPU: throttling, nondeterminism | engineering | low | GPU only for Workstream D; fixed seeds; CPU fallback tests |
| 16 | Tooling gaps: PaperBanana, codex/gemini CLIs, pytest-timeout absent; ARIS traces empty | process | med | log PaperBanana as unavailable (numeric tables only); audits labelled MANUAL_FALLBACK; subprocess timeouts |
| 17 | Porting from branches (sys.path hacks, D2A 300 behind main, P2 local-only) | engineering | med | port with source SHA into `src/shiftlab/paper3/` plus smoke tests; P2 read-only |
| 18 | Lint scope: repo-wide `ruff --fix` forbidden; CI lints everything | engineering | low | lint only Paper-3 paths |
| 19 | Hindsight oracle misused as a target or for selection | scientific | med | evaluator-side only, labelled unattainable |
| 20 | Prior art: costed query+act (Atan & van der Schaar 2016; Chick et al.; Cheng et al. ICML 2023; Drift2Act); deadline alignment is POMDP control | scientific | high | consult `01_PRIOR_ART_MATRIX.md`; mechanism-level claim per workstream; no novelty claim before audit |
