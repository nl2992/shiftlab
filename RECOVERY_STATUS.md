# CI recovery checkpoint

**Date:** 2026-11-06  
**Branch:** `codex/scoped-method-research-results-2026-11-06`  
**Starting revision:** `e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b`  
**Repair commit:** `82e1c48e` (`Fix Ruff lint and formatting checks`)  
**Status:** CI lint and formatting repaired; full test phase stopped at collection failure. No merge to `main`.

## Reproduction of Actions run 42179919497

GitHub Actions run [42179919497](https://github.com/nl2992/shiftlab/actions/runs/42179919497) on the starting revision failed at `uv run ruff check .`. `ruff format --check .`, `mypy`, `pytest`, and environment validation were skipped by the workflow. The failed Ruff step reported 506 lint findings across 110 files, including unused `noqa`s, import ordering, unsafe/int casts, closures over loop variables, file handling, and scripts with shebangs but no executable bit.

Exact workflow setup:

```sh
uv sync --extra dev --extra data-sources --extra neural --extra drift --locked
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run pytest -q
```

## Local execution and results

This machine is macOS arm64. The exact locked sync above cannot install `torch==2.9.1+cu130`, which has only Linux and Windows wheels in the lock resolution:

```text
uv sync --extra dev --extra data-sources --extra neural --extra drift --locked
error: Distribution `torch==2.9.1+cu130` can't be installed ...
You're on macOS (`macosx_15_0_arm64`), but `torch` ... only has wheels for manylinux and win_amd64.
```

The dev-only tools were installed successfully with:

```sh
uv sync --extra dev --locked
```

Local verification on Ruff 0.17.1:

| Command | Result |
|---|---|
| `uv run ruff check --output-format json .` before repair | 506 findings; detailed diagnostic saved during execution at `/tmp/shiftlab-ruff-42179919497.json` (local ephemeral file) |
| `uv run ruff check --fix --unsafe-fixes .` | Applied direct lint fixes; the remaining executable-bit findings were corrected on the affected shebang scripts. Manual findings were fixed in the exact reported sites. |
| `uv run ruff check .` | PASS — `All checks passed!` |
| `uv run ruff format --check .` before format | FAIL — 133 files would be reformatted |
| `uv run ruff format .` | Reformatted the 133 files reported by Ruff |
| `uv run ruff format --check .` after format | PASS — 1,996 files already formatted |
| `uv run mypy` | PASS — no issues in 2 source files |
| `uv run pytest -q` | STOPPED at collection: 93 collection errors in 42.04 seconds; no test cases ran |

## Test collection diagnostic

The first repeatable collection error is a top-level module-name collision. `tests/sota_sprint/test_fam_b.py:16` imports `bench`; `scripts/sota_sprint/bench.py:23` requests `ALL_REGIMES` from the top-level name `regimes`. Pytest had already resolved that name to the other module `scripts/failure_atlas_v2/regimes.py`, which does not export `ALL_REGIMES`:

```text
ImportError: cannot import name 'ALL_REGIMES' from 'regimes'
(/.../scripts/failure_atlas_v2/regimes.py)
```

The same collision blocks collection of `tests/sota_sprint/test_fam_c.py`, `test_fam_m.py`, and other suites. The full pytest run was stopped here as required; focused tests were not attempted after the collection failure. This is a reproducible test-harness/import-path failure, not evidence about the behavior of the lint changes.

## Change scope and next action

The repair commit contains Ruff-reported fixes and formatter output only: 137 source/test files changed (including 20 executable-bit corrections for shebang scripts). `src/shiftlab.egg-info/SOURCES.txt` and local Graphify cache/hook files were not included. No dependency lock, research result, or prior registered experiment record was changed.

**Phase 0 is incomplete at the test gate.** The smallest next action is to make the test import paths unambiguous (prefer package-qualified imports or scoped `sys.path` handling instead of the shared top-level `regimes` name), then rerun pytest collection and the full suite in CI's Linux environment with the locked extras. Do not proceed to economic-headroom experiments until this checkpoint passes or a bounded, reproducible platform limitation is accepted.
