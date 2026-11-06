# CI recovery checkpoint

**Date:** 2026-11-06  
**Branch:** `codex/scoped-method-research-results-2026-11-06`  
**Starting revision:** `e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b`  
**Repair commits:** `82e1c48e` (`Fix Ruff lint and formatting checks`), `4dddf965` (disambiguate the FLQ regime import), and `f9b8db02` (support pinned baseline imports in shallow checkouts).  
**Status:** Ruff, format, typing and focused tests pass. Full pytest is running in GitHub Actions run `42188683332` and locally; no merge to `main`.

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

## Test collection diagnostics and repairs

The first repeatable collection error is a top-level module-name collision. `tests/sota_sprint/test_fam_b.py:16` imports `bench`; `scripts/sota_sprint/bench.py:23` requests `ALL_REGIMES` from the top-level name `regimes`. Pytest had already resolved that name to the other module `scripts/failure_atlas_v2/regimes.py`, which does not export `ALL_REGIMES`:

```text
ImportError: cannot import name 'ALL_REGIMES' from 'regimes'
(/.../scripts/failure_atlas_v2/regimes.py)
```

The same collision blocked collection of `tests/sota_sprint/test_fam_c.py`, `test_fam_m.py`, and other suites. `scripts/sota_sprint/bench.py` now loads the FLQ regimes under a namespaced module and `screen.py` imports those exports through `bench.py`. Focused tests pass: `uv run pytest -q tests/sota_sprint/test_fam_b.py tests/sota_sprint/test_fam_c.py` — 57 passed.

The next CI attempt then exposed a second collection issue: shallow `actions/checkout` did not contain pinned commit `041bc26`, so the B3 loaders could neither compare against nor extract that historical object. The checked-in baseline file is byte-identical to the pinned file (SHA-256 `7565a647f3bb3f940d4fbd2a948597b9ffe42ef0485550a771d137e7930baebd`). Both loaders now accept the file by this pinned digest and otherwise require a successful `git show`. Targeted verification: `uv run pytest -q tests/promising_directions/test_b3_plus_policy.py tests/promising_directions/test_b3_real_data.py` — 25 passed.

## Change scope and next action

The repair commit contains Ruff-reported fixes and formatter output only: 137 source/test files changed (including 20 executable-bit corrections for shebang scripts). `src/shiftlab.egg-info/SOURCES.txt` and local Graphify cache/hook files were not included. No dependency lock, research result, or prior registered experiment record was changed.

At revision `c699b4b4`, CI run [42192207364](https://github.com/nl2992/shiftlab/actions/runs/42192207364) passed locked dependency setup, `ruff check`, `ruff format --check`, and `mypy`; full pytest is still in progress. Run [42189641802](https://github.com/nl2992/shiftlab/actions/runs/42189641802) at prior revision `469ee3c0` also remained in progress at the last check. A later workflow on unrelated revision `0970dbc2` failed Ruff; it is not this branch head and does not invalidate the successful Ruff result on `c699b4b4`. The local full suite was stopped after remaining CPU-bound for over an hour without a result; focused suites passed, so CI remains authoritative. No test failure was observed in the stopped local run. The economic headroom checkpoint and bounded composition pilot are recorded separately in `research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md`.

Phase 0 remains open until full pytest finishes and `validate_environment.py` completes on the current branch revision. The local `validate_environment.py` command passed, but the workflow step on the current revision has not yet run. Local exact locked sync is not possible on macOS arm64 because the lock pins CUDA-only `torch==2.9.1+cu130`; CI is the authoritative environment for that exact workflow. Any code push after this checkpoint triggers a fresh workflow on the updated revision.
