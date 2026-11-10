# 00 Repo inventory (Phase 0)

Captured 2026-11-09 ~23:46 UTC (commands run in worktree `ICML/shiftlab-paper3-2026-11-09`).

## Environment
- OS: Windows 11 Home 10.0.26200; shells: Git Bash + PowerShell 5.1.
- CPU: Intel i7-13700HX, 16 cores / 24 threads. RAM: 15.7 GB.
- GPU: NVIDIA GeForce RTX 4060 Laptop, 8188 MiB, driver 592.82; torch CUDA available (True).
- Python (`../shift-research-starter/.venv/Scripts/python.exe`): 3.13.1; torch 2.9.1+cu130 (CUDA 13.0); numpy 2.5.4; scipy 1.18.1; scikit-learn 1.9.1; pytest 9.1.1. `pytest-timeout` NOT installed (`--timeout` unusable). venv has no pip module (`-m pip list` empty).
- Tools on PATH: uv, ruff, pytest (all under `C:\Users\nigel\AppData\Local\Programs\Python\Python313\Scripts`), git (Git for Windows). `codex` and `gemini` CLIs: not found by `where` (NOT available). mypy: UNVERIFIED (CI runs it).
- PaperBanana: not found (no `*banana*` file under shift-research-starter excluding .venv, nothing in venv site-packages, no `~/.claude/skills/paperbanana`). Treat as UNAVAILABLE; per mandate log it and keep numeric tables.
- ARIS: `.aris/` exists in worktree and contains only `traces/` (empty listing). `~/.claude/skills`: arxiv, benchmark-paper-template, citation-audit, deep-research, drawio-reconstruction, experiment-audit, experiment-plan, figure-designer, idea-evaluator, intro-drafter, kill-argument, novelty-check, openalex, paper-claim-audit, paper-polish, paper-writer, ponytail*, pre-submission-reviewer, proof-checker, rebuttal-guidance, research-lit, research-refine(-pipeline), research-review, result-to-claim, semantic-scholar, shared-references, tech-paper-template, vibe-research-workflow. Reviewer backend (Codex MCP) is absent, so cross-model skills can only run as MANUAL_FALLBACK. `~/.claude/vendor`: ponytail, Supervisor-Skills.

## Git
- Worktree HEAD = origin/main = `8af33afe934c3c5dba03caa55257125941f6df4f` (clean tracked tree; untracked files are other Paper-3 agents' work: configs/paper3, scripts/paper3, src/shiftlab/paper3, tests/paper3, ledger/, 02/03D docs).
- 77 branch refs (local+remote). Per-branch detail for the 14 requested: `00_BRANCH_PROVENANCE.json`. Summary: gave-r, hg-decision-aware-betting-v2, promising-directions, failure-atlas-v2-sota (origin only) are 0 ahead (merged). p2-null-aware-deployment is local only (`6f71b51e`, 35 ahead). Active Paper-1/QSG/BCR/D2A/methods-recovery branches are 15-62 ahead of main, mostly docs/ and scripts/.
- `shiftlab-risk-approx-2026-10-29` worktree exists as a sibling dir; the A1 scripts hard-code it as `DEFAULT_SOLVER_ROOT` (see risk register).

## Data (NOT in worktree; gitignored; live in `../shift-research-starter/data/`)
All of these were used by Papers 1/2 -> classify as exploratory/dev-exposed (no confirmatory use).
| dir | files | size | content |
|---|---|---|---|
| c4_sealed | 27 npz | 8.5 MB | real paired-loss streams (311/permits/crashes/etc.); keys `l0,l1` int8 (100,2000), `starts` (100,), `delay` scalar |
| saes_dev | 11 npz | 5.4 MB | keys `l0,l1` int8 (E,2000), `s0,s1,drift` float32 (E,2000) (scores/drift), `starts`, `delay` |
| atlas_v2_losses | 10 files (9 npz + README) | 112 KB | cached loss streams, sha256 in README |
| sprint_fresh_losses | 7 | 276 KB | README + stats.json; array hash on `l0,l1,starts` |
| sprint_twin_losses | 7 | 4.8 MB | exchangeable twins, known-null |
Other dirs under data/: gpu_auto_verification, interim, manifests, processed, raw, reports, synthetic. Worktrees need the path `../shift-research-starter/data` (or symlink/copy); scripts use `ROOT/"data/..."` so they fail in this worktree unless data is linked.

## CI
`.github/workflows/ci.yml` (push+PR, ubuntu): `uv sync --extra dev --extra data-sources --extra neural --extra drift --locked`; `ruff check .`; `ruff format --check .`; `mypy` (files=src/shiftlab/core); `pytest -q`; `scripts/validate_environment.py`. pytest config: testpaths `tests`, pythonpath `[".","src"]`.

## Baseline tests
Command: `PYTHONPATH=src OPENBLAS_NUM_THREADS=1 python -m pytest -q --continue-on-collection-errors -p no:cacheprovider tests` (230 test entries under tests/).
First attempt with `-x` stopped at a collection error in 111 s. Full run: **52 failed, 3178 passed, 28 skipped, 8 errors in 5913 s (98.6 min)** on main `8af33afe`.
Failure breakdown:
- 49 failed `tests/sprint2/test_fam_h.py` + 8 collection errors (`tests/sota_sprint/test_fam_b|c|m.py`, `tests/sprint2/test_fam_p|late_real|wp1_clock_ablation|wp1_giacomini_rossi|wp2.py`): `ImportError: cannot import name 'ALL_REGIMES' from 'regimes'` - module-name collision: `scripts/failure_atlas_v2/regimes.py` shadows `scripts/failure_atlas_v2_flq/regimes.py` on sys.path in a whole-suite run. Order-dependent; likely passes if the files are run separately (UNVERIFIED).
- 1 `tests/test_reference_implementations_manifest.py`: SHA-256 mismatch for `src/shiftlab/dive/eprocess.py` (probable CRLF/autocrlf checkout effect on Windows; UNVERIFIED).
- 1 `tests/test_atlas_mechanism_check.py`: needs `outputs/failure_atlas_v1_cycle3/family1/state.json` (gitignored outputs absent in worktree).
- 1 `tests/test_delayed_evidence_ppi_start_mixture_confirmation.py::..._smoke_requires_passing_calibration` (cause not inspected; UNVERIFIED).
No Paper-3 code touched by these. Log: scratchpad `pytest_full2.log`.
