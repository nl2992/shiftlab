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
