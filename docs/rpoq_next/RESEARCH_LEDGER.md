# RPOQ-next research ledger (append-only)

Branch `research/rpoq-s1-fatal-flaw-audit`. Historical RPOQ protocols, results and outputs are not modified by this programme. Working style: Ponytail "full" (smallest complete change, reuse repo components, one small test per new piece of logic, `shortcut:` comments for known limits).

## 2026-10-30, Cycle 0: Git/CI audit

- Starting commit: `ba0298ef` (working tree clean, in sync with `origin/research/rpoq-s1-fatal-flaw-audit`). The pre-repair source snapshot is that commit; every historical result was produced by code at or before it.
- CI run on `ba0298e` ("CPU checks") failed at its first failing step, `ruff check .`. The job log was not retrievable through the API, so the failures were reproduced locally with the repo's Ruff configuration: exactly the two reported findings, `RUF046` (`int(round(...))` in `rpoq_crsp_replay.py`) and `C408` (`dict(...)` in `tests/test_rpoq_exact.py`).
- Repair: both fixed as one-line behavior-neutral edits; `ruff format` applied to the five RPOQ files it flagged (`rpoq_exact.py`, `rpoq_crsp_replay{,_b,_c}.py`, `tests/test_rpoq_exact.py`). No result file was regenerated or edited.
- Verification: `ruff check .` clean; `ruff format --check .` clean (1173 files); `mypy` (configured for `src/shiftlab/core` only) clean; `tests/test_rpoq_exact.py` 6 passed; exact B=3 power still 0.0330 (matches the registered S3 value).
- Not yet verified: the rest of the CI sequence (`pytest -q` over the whole repo, `scripts/validate_environment.py`) never ran remotely because CI stopped at Ruff. A local full-suite run follows.

## 2026-10-30, Cycle 1–3 checkpoint

- **Source access.** Primary-paper reads failed: `arxiv.org`, `proceedings.mlr.press`, `proceedings.neurips.cc`, `people.bath.ac.uk`, `doi.org`, `openreview.net` unreachable. Read this session: authors' released code for ASI and Robust ASI (GitHub). Pro-Active Inference (2610.34681) and Active MPPI (2605.08429) are `UNREAD` and absent from all repo audits. SOTA gate **not fully met**; all novelty statements provisional.
- **Cycle 1.** `SOTA_GAP_AND_OPPORTUNITY_MATRIX.md`, `CANDIDATE_RANKING.md`: primary A (growth/signal-aware allocation with per-context bets), fallback C, deferred B.
- **Cycle 2.** `growth_alloc.py` + tests: second-moment algebra verified by simulation; bang-bang split of marginal events fixed (budget now met exactly).
- **Cycle 3 (A1).** Registered verdict NOT PASSED (tie condition violated). Large oracle effect from concentrating labels on one context; calibration clean. Diagnosis in `SYNTHETIC_RESULTS.md`. Prediction P1-tie was wrong (SNR, not signal, must be constant).
- **CI.** Ruff/format/mypy repaired and verified; full-suite triage pending (task #4).
- **Next.** Register A2 (estimation, equally equipped comparators), run, then decide A vs fallback.

## 2026-10-30, CI triage result

Local full suite (base dependencies only, no `neural`/`drift` extras): 1639 passed, 23 skipped, 33 failed, 82 collection errors. Every failure and error traces to a missing optional dependency: `torch` (collection and runtime `import torch` in `budgeted_promotion.py`) and `river` (8 collection errors). The same tests fail identically on `main` at `ec42a2d`, before this branch. **No code defect found.** CI installs `--extra neural --extra drift`; torch could not be installed here (the pinned `pytorch-cu130` index is outside the network allowlist), so the full suite has *not* been verified end to end in this environment. Remaining CI step `scripts/validate_environment.py` not run.

## 2026-10-30, Cycle 3 closed (A1–A3)

- A1 NOT PASSED (oracle subgroup effect; tie prediction was wrong: SNR must be constant). A2 NOT PASSED (tie control; `growth_online` worse than uniform). A2b INCONCLUSIVE (placebo). A3: **SUPPORTED WITH RESTRICTION** (fair baselines, calibrated; `het` Δ ≈ +0.215; `het_flip` Δ = −0.120).
- Decision: Candidate A survives only as a restricted, stationary heterogeneous-SNR mechanism. The failure condition is the burn-in favourite losing its signal. Cycle 4 allows at most two substantive revisions; revision 1 targets exactly that failure (see `METHOD_DESIGN.md` addendum, to be written before running).
- Real data: not yet. The synthetic gate is only partially passed, so only a *development-split heterogeneity/stability check* (no test split) is permitted next.
