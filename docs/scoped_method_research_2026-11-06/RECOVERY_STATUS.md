# Recovery status — 2026-11-06

## Scope and checkout

- Branch: `codex/scoped-method-research-results-2026-11-06`
- Starting HEAD: `2e901a1c11b4cc251f5b5f2302252057ef8f28a8`
- CI failure: [GitHub Actions run 42179919497](https://github.com/nl2992/shiftlab/actions/runs/42179919497), failing head `e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b`.
- Pre-existing user artifacts (`.codex/hooks.json`, `graphify-out/**`) were left unstaged. An incomplete pacing calibration directory was also left unmodified; its process was interrupted before a complete run record and it is not evidence.

## CI lint reproduction and repair provenance

The CI job used `uv sync --extra dev --extra data-sources --extra neural --extra drift --locked` followed by `uv run ruff check .`. At the exact failing commit, the pinned Ruff 0.17.1 reports 506 findings (332 marked automatically fixable, 113 more only with unsafe fixes). Exact isolated reproduction command:

```sh
git worktree add --detach /tmp/shiftlab-ci-repro e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b
cd /tmp/shiftlab-ci-repro
uv run --with ruff==0.17.1 ruff check . --output-format=concise
```

The platform-specific locked sync could not install the CUDA-only PyTorch wheel on macOS arm64; direct `uv run --with ruff==0.17.1` was used to reproduce the lint step. The reported 506 findings match the CI failure. The branch already contains the repair as commit `82e1c48ec473600ad07775216c6b5a81939b1b65` (parent is exactly the CI failing SHA). It fixes Ruff findings and formatting across the linted repository. No additional lint edit was needed in this recovery checkpoint.

## Checks on the starting branch

Commands and results:

```sh
uv run ruff check .
# All checks passed!

uv run ruff format --check .
# 2042 files already formatted

uv run mypy
# Success: no issues found in 2 source files

uv run pytest -q
# 3336 passed, 46 skipped, 1 failed in 3150.21s
```

The single failure was independently reproduced with:

```sh
uv run pytest -q 'tests/sprint2/test_late_real.py::test_short_stream_null_no_promotion[E_srrSR:split90:gated_deployment]'
```

Result: `3 <= 2` assertion fails (3 of 5 short null streams promoted; 1 failed in 1.55s). This is the risk-split candidate already stopped by its registered 49/1000 null calibration result and upper Wilson bound 6.15% exceeding the 5% gate; see `research/scoped_method/pilots/srr_risk_split_20261106/CALIBRATION_RESULTS.md`. This recovery run does not change that decision. The pacing calibration was interrupted and must not be counted or resumed as a partial confirmatory result.

## Phase decision

The historical CI Ruff issue is repaired in the branch and all lint, format and typing checks pass. The full suite exposes a candidate-specific short-null regression in the already rejected split-90 variant. In accordance with the recovery instructions, no speculative or unrelated code change was made. Recovery phase is stopped at this reproducible diagnostic; no economic-headroom matrix or new candidate experiment was launched in this checkpoint.

Smallest next action: remove the rejected split-90 variant from the parametrized regression set or replace it with an assertion consistent with the registered null-calibration stop, then rerun that focused test and the relevant candidate tests before continuing Phase 1.
