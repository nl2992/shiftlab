# Paper 3 execution checklist (user-supplied 2026-11-09; status updated by the PI session)

Legend: [x] done and verified, [~] partial, [ ] not done. Updated at each commit milestone.

## Isolation and repo audit
- [~] Record repo status, main SHA, branch SHAs, hardware, dataset inventory (00_REPO_INVENTORY.md, 00_BRANCH_PROVENANCE.json)
- [x] Create `research/paper3-safe-budgeted-intervention-2026-11-09` in isolated worktree `ICML/shiftlab-paper3-2026-11-09` from origin/main 8af33afe
- [x] Read AGENTS, charter, streaming contract, paper3 baselines, failed novelty attempts (MANDATE.md records settled findings)
- [~] Reuse map and file-ownership plan (00_REUSE_MAP.md; ownership below)

File ownership (concurrent workers): core = src/shiftlab/paper3/*.py, tests/paper3/*.py, scripts/paper3/core;
atlas = src/shiftlab/paper3/atlas/, scripts/paper3/atlas; transfer = src/shiftlab/paper3/transfer/,
scripts/paper3/transfer; literature = 01_* and references.bib. Only the PI session commits.

## Skill-driven novelty gates
- [ ] HKUSTDial/ARIS versions and paths; preserve `.aris` traces
- [ ] deep-research + idea-evaluator per A/B/C/D
- [ ] Full closest-work reading (WISE-ATTA, Drift2Act, RAR, Regol, Atan, Chick, meta-CUSUM)
- [ ] Prior-art matrix and adversarial rejection memos
- [ ] Each novelty claim labelled covered / conditional / unverified / supported

## Core implementation and validity
- [ ] Event-time queue, action/query logging, request-time budgets, full cost accounting
- [ ] Leak-prevention, positivity, delayed-release, stochastic budget property tests
- [ ] Exact small-horizon controller + robust-null risk oracle where feasible
- [ ] Separate false-promotion gate, future-payback certificate, dynamic regret
- [ ] iid / Markov / informative-delay claims only where assumptions apply

## A, B, C, D, data, paper — see 07_NEXT_ACTIONS.md and the final verdict for status.

## Status at 2026-11-10 (PI session)
- [x] Inventory, provenance, reuse map, risk register (50e1c3cb)
- [~] Novelty: matrix + memos + idea-evaluator scores (c01766c1); MANUAL_FALLBACK, single family; 5 sources abstract-only, Liu TPAMI unretrieved
- [x] Core contract, queue, budget ledger, 24-regime tapes, exact DP oracle vs brute force, 65 tests (06ac8597); 114 paper3 tests pass in total
- [x] A implemented (A0-A5), tuned, ablated, exact-gap checked: NEGATIVE (dfda60a6)
- [x] B theory + certificates + pilot (f8f5d470); proof audit (1b8be025); T6-T8 open
- [x] C fidelity fix, atlas grid, inversions, repairs (d3f8a4de); real-stream inversion not reproduced
- [x] D baselines, recommenders, GRU controller, OOD fallback (f3525867): NEGATIVE
- [x] E dual-use kill test: STOP (8d62545d)
- [x] Confirmation registered (2190f95f), opened once, H1-H5 SUPPORTED (480a669b)
- [ ] ~25 eligible new real streams (only exposed c4/saes + 4 sealed)
- [ ] Figures (PaperBanana unavailable)
- [ ] Cross-model ARIS audits (no external reviewer backend)
- [ ] Manuscript (not supported by evidence yet; see 07_FINAL_PUBLICATION_VERDICT.md)
