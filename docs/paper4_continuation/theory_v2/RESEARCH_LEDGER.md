# theory_v2 research ledger (append-only)

## 2026-11-10 — start
- Fetched origin; Paper 4 branch HEAD `b1215242` (not `76b9f744`). Created and pushed
  `research/paper4-causal-premium-theory-2026-11-10` from it, in worktree `shiftlab-methods-strategy-dba13e`.
  The worktree `failure-atlas-v2-sota-195428` (session "Risk-preserving approximate optimization", idle) still holds
  the old branch and a running A3 campaign; it is left untouched.
- ARIS: skills present under `.agents/skills/` (research-pipeline, novelty-check, proof-checker, proof-orchestrator,
  experiment-plan, research-review, result-to-claim). No `.aris/reviewer.json`; no Codex/Grok/Antigravity/claude-review
  tools loaded ⇒ BL-1 persists; all reviews same-family / provisional.

## 2026-11-10 (afternoon)
- 03:48 EST: launched WP-A (Opus auditor), WP-B, WP-C (Opus theory), WP-F (Sonnet retrieval), WP-E (Sonnet auditor).
  All five stopped on the account's 5-hour usage limit before writing any file (HTTP 429). Resumed at 12:50 EST
  from their saved transcripts; no partial outputs existed. The A3 campaign process had ended by then, so the
  quiet-CPU restriction was lifted.

## 2026-11-10 — WP B (multi-label zero premium), agent report
- PROVED Theorem S0: static alternative, c = 0, any B, d, k, prior, alpha => Gamma = 0. The proof uses the calendar
  reduction plus an induction on the closed G/D recursions. Audit: 254 cells, 0 violations.
- FALSIFIED Z2 / U-M / "TP2 + multi-label W". Counterexample CE-B1: T=5, B=4, d=1, t=1/10, e=(1/100,99/100), prior 1/2,
  c=k=0, alpha=25/32, Gamma in [0.00209251952, 13078247/6250000000]. Certified two ways: by gamma_cell, and
  independently by the wpB_dual_check lower bound.
- OPEN: static with c > 0 (Lemma S+). 0 failures in 29,297 cells.
- Details: `MULTILABEL_ZERO_PREMIUM.md`. Nothing committed.
