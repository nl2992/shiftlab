# Drift2Act / RAR SOTA-first autoresearch programme — plan and TODO

Branch `research/drift2act-rar-autoresearch-2026-11-07`, worktree `ICML/shiftlab-d2a-rar-2026-11-07`,
cut from `main@7354480a` on 2026-11-07. Full brief: the user's "SOTA-First Autonomous Methods
Research" mandate (copied verbatim to `docs/d2a_rar/MANDATE.md`).

Central question: can a justified modification to Drift2Act, RAR or another strong existing controller
achieve better statistically valid deployment decisions by exploiting actual observation gaps, the
economic value of delayed labels, or interactions between evidence and acquisition?

Exit states: `METHODS_CANDIDATE` / `BENCHMARK_ONLY` / `NEGATIVE_RESULT`. Prior ShiftLab (GAVE-R,
Atlas) findings are development knowledge, not confirmation.

## Operating rules

- Routing: Sonnet subagents do coding, reproduction, experiment running and write-ups; Haiku for
  lookups/greps; the Opus main session plans, verifies and decides. Opus re-checks every subagent
  claim against code and result files before ticking a box.
- HKUSTDial Supervisor-Skills guide doubtful decisions: `idea-evaluator` (candidate triage),
  `deep-research` (prior art), `benchmark-paper-template` / `tech-paper-template` (deciding methods
  vs benchmark framing), `paper-writer` (write-ups). Also `novelty-check`, `experiment-audit`,
  `result-to-claim` before any claim.
- Subagents do not commit; the coordinator commits after verification. No pushes without the user.
- Python: main checkout `.venv/Scripts/python.exe` with `PYTHONPATH=<this worktree>/src`.
- Long compute (> ~10 min) runs detached (Start-Process) with checkpoints on disk; status files in
  `docs/d2a_rar/status/`.
- Missing comparator? `git grep` all refs (incl. `origin/codex/*`, `research/continuation-2026-11-04`
  which has a Drift2Act reproduction audit) and port with a source-commit citation.
- Null discipline: every method has an entry in `registry/null_assumptions.yaml`; never score a
  conditional-null method on marginal-null false promotions.
- Grading: fair-evaluation standard (substantial >= 10%, meaningful 3-10% CI excl. 0, small 1-3%).
  Acceptance: mild novelty + beats strongest applicable SOTA on a shared failure, valid, ablated,
  not worse nearby, independently confirmed.

## Work packages

- [x] WP0 Failure ledger + null-assumption registry + `FAILURE_ATLAS_CORRECTED.md` (agent: ledger)
- [ ] WP1a Drift2Act paper_reconstruction + native-task reproduction subset (agent: d2a)
- [ ] WP1b RAR paper_reconstruction + native-stream reproduction subset (agent: rar)
- [x] WP1c SOTA registry for C-F + WATCH/PPRM; implement Challenger GSE/OSE/LSE (agent: sota)
- [x] WP2 `BENCHMARK_CONTRACT.md` + common event-driven simulator with leakage/budget/cost tests (agent: sim)
- [ ] WP1d Gong-Zhang paid-observation, ASI, Sethi Markov test comparators (after WP1c)
- [x] WP4 Prior-art ledger (first pass; verified structure; gaps: no GitHub code search, no OpenReview, Drift2Act App D.7 unread)
- [ ] WP5 Candidate grammar + `CANDIDATE_REGISTRY` (<= 100k identities, dedup by mechanism) + `AUTORESEARCH_PROGRAM.md`
- [ ] WP6 Stage A preflight + Stage B 300 s screens (initial 200) -> checkpoint review
- [ ] WP6c Stage C medium validation (<= 20) -> Pareto/ablation report
- [ ] WP7 Confirmation protocol registered BEFORE holdout -> <= 3 finalists -> confirmation results
- [ ] WP8 `METHODS_PAPER_DECISION.md`

Dependencies: WP5 after WP0+WP1a/b+WP2; WP6 after WP5; Q3 factorial only after a Q1 and a Q2 winner.

## Progress log

- 2026-11-07: branch + worktree created; WP0, WP1a, WP1b, WP1c, WP2 launched as Sonnet subagents.
- 2026-11-07: WP4 first pass landed (10 families; most room: pending/deadline-aware querying, RAR Gate-2, canary exposure). WP2 verified (33 tests); WP2b sent (retrospective queries, canary split, retrain-window loss, seed registry).
- 2026-11-07: WP1c committed 6f0e6d88 (Challenger 12 tests; Lending Club not reproduced). WP2+WP2b committed 7a9743c4 (55 tests). WP1d relaunched paper-only (auto-mode blocked cloning/executing author repos); WP1e in-repo ports launched.
- 2026-11-07: WP0 committed (49 ledger rows, 29 null entries, 13 P2 null-mismatched measurements; 57 UNVERIFIED fields to be filled by baseline agents; HGxH2c FINAL_REPORT and Lane A docs not yet mined).
- 2026-11-07: WP1e committed a7fcc291 (33 in-repo adapters, 22 regression tests incl. bit-for-bit). Open: H2c/HG/PPRM need proxy predictions + source calibration in ObservableState (WP2c, do with Drift2Act sensing port); original E_rb + RMM restart wrapper not ported.
