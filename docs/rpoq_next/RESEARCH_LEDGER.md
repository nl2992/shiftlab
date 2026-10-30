# RPOQ-next research ledger (append-only)

Branch `research/rpoq-s1-fatal-flaw-audit`. Historical RPOQ protocols, results and outputs are not modified by this programme. Working style: Ponytail "full" (smallest complete change, reuse repo components, one small test per new piece of logic, `shortcut:` comments for known limits).

## 2026-10-30, Cycle 0: Git/CI audit

- Starting commit: `ba0298ef` (working tree clean, in sync with `origin/research/rpoq-s1-fatal-flaw-audit`). The pre-repair source snapshot is that commit; every historical result was produced by code at or before it.
- CI run on `ba0298e` ("CPU checks") failed at its first failing step, `ruff check .`. The job log was not retrievable through the API, so the failures were reproduced locally with the repo's Ruff configuration: exactly the two reported findings, `RUF046` (`int(round(...))` in `rpoq_crsp_replay.py`) and `C408` (`dict(...)` in `tests/test_rpoq_exact.py`).
- Repair: both fixed as one-line behavior-neutral edits; `ruff format` applied to the five RPOQ files it flagged (`rpoq_exact.py`, `rpoq_crsp_replay{,_b,_c}.py`, `tests/test_rpoq_exact.py`). No result file was regenerated or edited.
- Verification: `ruff check .` clean; `ruff format --check .` clean (1173 files); `mypy` (configured for `src/shiftlab/core` only) clean; `tests/test_rpoq_exact.py` 6 passed; exact B=3 power still 0.0330 (matches the registered S3 value).
- Not yet verified: the rest of the CI sequence (`pytest -q` over the whole repo, `scripts/validate_environment.py`) never ran remotely because CI stopped at Ruff. A local full-suite run follows.
