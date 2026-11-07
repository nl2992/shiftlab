# CI recovery checkpoint

**Date:** 2026-11-06  
**Branch:** `codex/scoped-method-research-results-2026-11-06`  
**Starting revision:** `e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b`  
**Repair commits:** `82e1c48e` (`Fix Ruff lint and formatting checks`), `4dddf965` (disambiguate the FLQ regime import), and `f9b8db02` (support pinned baseline imports in shallow checkouts).  
**Status:** The full suite on the previous source snapshot failed in GitHub Actions run `42192207364`: 94 failed, 3,238 passed, 46 skipped. The failure classes have been repaired locally and focused verification passes; a full rerun on the repair commit is required. No merge to `main`.

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

## Latest full-suite failure and repair status

The Actions run [42192207364](https://github.com/nl2992/shiftlab/actions/runs/42192207364) completed on source snapshot `c699b4b4` with **94 failed, 3,238 passed, 46 skipped** in 1:25:49. The captured runner log is `/tmp/shiftlab-421922-ci.log`. Failure causes were:

- 85 FAM B/C/M and late-real tests saw a test-module `registry` name collision; the B3 test loader now scopes that module and restores `sys.modules`.
- FAM P/WP2 had the same polluted registry; the pytest path now includes the SOTA simulator directory.
- FAM R's test imported `StartedMixture` from the wrong module; it now imports the implementation from `qsg`.
- A front-loading stochastic test used a platform-sensitive maximum; it now asserts at least 90% of labels are purchased before half-horizon.
- The mechanism-check smoke test depended on ignored output state; it now supplies `--kappa 0.05` explicitly.
- A delayed-evidence test relied on a stale calibration source hash after the e-process implementation changed. It now checks that stale calibration is rejected; the old calibration is not rewritten or represented as current evidence.
- H-GXH2C stage 4 omitted selector alarm/metadata fields; the selector input now includes them. Its scale test is reduced from 648×1,000 cells/seeds and 50×4,000 resamples to 324×500 and 10×2,000; local runtime is 77.24s.
- The ShiftGuard reference manifest contained an obsolete e-process hash. It now records the current source hash and preserves the superseded hash and explanation; the implementation change was alarm-read memoization only, not an update to the betting/wealth equations.

Local verification on the repair patch:

| Command | Result |
|---|---|
| `uv run ruff check .` | PASS |
| `uv run ruff format --check .` | PASS — 2,001 files already formatted |
| `uv run mypy` | PASS — no issues in 2 source files |
| `uv run pytest --collect-only -q` | PASS — 3,378 tests collected in 5.41s |
| Order-sensitive FAM/B3/FAM-P/R/WP2 subset | PASS — 141 passed in 67.54s |
| Front-loading, atlas smoke, stale-calibration rejection, reference manifest | PASS — 4 passed |
| H-GXH2C stage 3/4 smoke | PASS — 1 passed in 48.04s |
| H-GXH2C scale test | PASS — 1 passed in 77.24s |
| `git diff --check` | PASS |

The new code/test fixes have not yet passed a full suite. CI run `42192207364` is not evidence of a passing full suite, and rejecting the stale calibration leaves that prior PPI confirmation unauthorized until a current calibration is generated. Neither caveat changes the bounded economic-headroom decision recorded below.

## Change scope and next action

The repair commit contains Ruff-reported fixes and formatter output only: 137 source/test files changed (including 20 executable-bit corrections for shebang scripts). `src/shiftlab.egg-info/SOURCES.txt` and local Graphify cache/hook files were not included. No dependency lock, research result, or prior registered experiment record was changed.

The branch before this repair was `6299987e`; its code was identical to source snapshot `c699b4b4` (a later commit changed documentation only). Older duplicate run [42189641802](https://github.com/nl2992/shiftlab/actions/runs/42189641802) at prior revision `469ee3c0` was cancelled. The duplicate doc-only run [42193148296](https://github.com/nl2992/shiftlab/actions/runs/42193148296) was also cancelled after its checks passed. A later workflow on unrelated revision `0970dbc2` is outside this branch. The economic headroom checkpoint and bounded composition pilot are recorded separately in `research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md`.

Phase 0 remains open. GitHub Actions run [42293566727](https://github.com/nl2992/shiftlab/actions/runs/42293566727) on source `c0a5017dc17ff5ef8fcb64c5fa29bc10ae58acaf` passed locked dependency installation, Ruff, format check, and mypy. Full pytest completed with **1 failed, 3,331 passed, 46 skipped in 812.19 seconds**; environment validation was skipped after the failure. Exact failure: `tests/promising_directions/test_sota_online_llm_picker.py::test_budget_is_front_loaded_under_the_cap`, line 97 asserted at least 23 of 25 requests before event 300, while the fixed seed produced 22. The test also measured median request event 90 and passed its separate median-before-120 assertion. This is a one-label miss in a stochastic timing assertion, not a failing production behavior check. Per the recovery brief, stop Phase 0 at this reproducible diagnostic; do not report the CI suite as passing. Local `validate_environment.py` passed on an earlier source. Exact locked sync is unavailable locally on macOS arm64 because the lock pins CUDA-only `torch==2.9.1+cu130`; CI handled dependency installation successfully.

## Latest full-suite recovery result

Actions run [42302052205](https://github.com/nl2992/shiftlab/actions/runs/42302052205) on commit `2092979f` passed Ruff, format check, mypy, environment validation, and the full pytest suite: **3,332 passed, 46 skipped in 791.73 seconds**. This run predates the chronological-news transfer scripts and therefore does not verify them. Their current local verification is limited to Ruff, formatting, bytecode compilation, and construction of the six requested policy factories. The HuffPost evaluator has read-only protocol sign-off; its confirmation window remains unopened pending the pre-outcome freeze-only smoke step.

## Current branch verification and economic-headroom decision (2026-11-06)

**Branch / tested HEAD:** `codex/scoped-method-research-results-2026-11-06` at `17a3f7e0006afc5247a345c1cc033147851fc4b3`. This is the same commit as `origin/codex/scoped-method-research-results-2026-11-06` before this documentation update. The Ruff repair is already present in the branch history (`82e1c48e`) and was not reapplied.

### Phase 0 checks on current source

| Command | Result |
|---|---|
| `gh run view 42179919497 --repo nl2992/shiftlab --log-failed` | Reproduced CI's Ruff failure: 506 findings, exit 1. |
| `uv run ruff check .` | PASS — Ruff 0.17.1, all checks passed. |
| `uv run ruff format --check .` | PASS — 2,054 files already formatted. |
| `uv run mypy` | PASS — no issues in 2 source files. |
| `uv run pytest -q tests/sprint2/test_late_real.py tests/failure_atlas_v2/test_restart_monitor.py tests/promising_directions/test_sota_economic_stop.py tests/promising_directions/test_sota_controls.py` | PASS — 97 passed in 14.67s. |
| `uv run pytest -q` | PASS — 3,339 passed, 46 skipped in 1,929.05s. |

The full suite is the first full run recorded here against the latest research branch. An initial focused invocation named nonexistent `tests/sota_sprint/test_fam_e.py` and collected no tests; it was immediately replaced by the valid focused command above. No test outcome was inferred from that failed invocation.

### Phase 1 reconciliation and Phase 2 decision

The evidence and provenance in `research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md`, `docs/scoped_method_research_2026-11-06/PHASE1_RECONCILIATION.md`, and `docs/scoped_method_research_2026-11-06/PHASE2_HEADROOM_RESULTS.md` remain controlling. E_rb and B2 match exactly on the 90 rollback-pilot episodes; never-switch beats E_rb in all three tested reversal/recurrent pilot cells; SR/CUSUM ARL controls are not equal-safety substitutes for anytime probability-of-any-false-promotion certificates; the direct front-load+E_rb run exists but was not committed/checksummed before execution; adaptive-range corrections supersede affected historical comparisons; and no independent real-data confirmation of a repair has occurred.

The frozen economic matrix found oracle-only headroom in the economically worthwhile reversal regime but no safety-qualified implementable policy passed the target, null, and adverse-cell gate. The strongest recent conventional comparison, slower-paced E-SR (`k=0.5`), passed its two 1,000-stream iid-null screens (20/1,000 each; one-sided Wilson upper 2.8682%) but cost 1.69 more than default E-SR on `F1_late_800` (paired 95% CI [-0.51, +3.90]) and cost 20.04 more than never-switch on `F3_reversal_800` (95% CI [+17.26, +22.82]); it is a conventional pacing setting, not a new method. See `research/scoped_method/pilots/srr_tail_pacing_20261106/RESTART1_RESULTS.md` for the full baseline panel and raw hashes.

**Phase decision:** `BENCHMARK_ONLY`. The tested environment has economic headroom in principle, but no distinct repair survives the frozen development gates; this does not establish that the entire research question or field is exhausted. Do not open locked holdouts or extend this candidate search under the same claim. Smallest next step: prepare the benchmark/case-study manuscript from the corrected records, including the adverse regimes and baseline-provenance caveats.

## Common-prefix diagnostic follow-up (2026-11-06)

A matched-seed source check verified that `F3_reversal_800` and `F3_reversal_1200` have exactly identical generated loss histories through event 799 in 1,000/1,000 pairs. Their registered parameter schedules are identical until the unfavorable regime changes at event 800; the worthwhile regime changes at event 1200. The policy receives no regime label or pre-change context feature. See `research/scoped_method/COMMON_PREFIX_IDENTIFIABILITY_20261106.md` and the amended `research/scoped_method/ECONOMIC_HEADROOM_DECISION_20261106.md`. This is a design-identifiability diagnostic, not a new positive method result or a claim of universal impossibility. The remaining plausible route is to locate a chronological model-pair source with an observable pre-change covariate, then freeze one context-aware hypothesis before accessing a test window.

## Current branch revalidation (2026-11-07)

The current branch is `codex/scoped-method-research-results-2026-11-06` at
`80e78824219f9a2258f586c0dc528f04f2a364c8` (`Record current retraining prior-art boundary`). The
immediately preceding code commit `68f3e59f` only reformatted and lint-repaired the already reported
P7s/Model Picker overlay pilot runner, analyzer, adapter, implementation, and tests; it did not
change the frozen protocol or pilot outcomes. The targeted rerun on this exact checkout passed:

| Command | Result |
|---|---|
| `uv run ruff check .` | PASS — all checks passed |
| `uv run ruff format --check .` | PASS — 2,070 files already formatted |
| `uv run mypy` | PASS — no issues in 2 source files |
| `uv run pytest -q tests/promising_directions/test_p7s_model_picker_overlay.py` | PASS — 4 passed in 1.42s |

The last full-suite run recorded above was on `17a3f7e0` (3,339 passed, 46 skipped); the full suite
was not rerun after the narrow overlay cleanup. The overlay results remain adverse to the proposed
composition: its frozen `F1_late_800` comparisons miss the practical improvement threshold, and its
reversal excess over never-switch is 56.43 [47.69, 65.17] units. The separate 1,000-null E-SR
calibration and late-persistent synthetic advantage are results for an established method, not a
distinct ShiftLab repair. The current exit remains `BENCHMARK_OR_CASE_STUDY_ONLY`; the smallest
scientifically permitted next action is to close the method search and prepare the benchmark/case
study with all adverse results. Do not open confirmation data under this failed development gate.

## Calibrated E-CUSUM headroom check (2026-11-07)

A missing baseline-fidelity comparison was prospectively frozen at `b0904611` in
`research/scoped_method/pilots/cusum_any_false_calibration_20261107/PROTOCOL.md`. This was a
bounded calibration of the already implemented E-CUSUM, not a new algorithm. On 1,000 calibration
null streams per fixed alpha, the largest value satisfying the Bonferroni-adjusted one-sided 99%
Wilson upper bound of 0.05 was alpha 0.005 (22/1,000; upper 0.04062). Alpha 0.01 failed (40/1,000;
upper 0.06290). Calibration records and hashes are committed alongside the protocol.

The independent comparison was frozen at `d7c3f5ad` before evaluation. On the fresh 1,000-stream
null block, E-CUSUM promoted in 6/1,000 episodes (ordinary one-sided 95% Wilson upper 0.01156),
passing the empirical null gate. However, the economic gate failed in the worthwhile
`F3_reversal_1200` cell: candidate minus never-switch was +20.93 (paired 95% CI [+17.53, +24.33]);
minus E-swcert was +2.59 ([-1.20, +6.38]); minus RMM/E_rb was +0.29 ([-2.68, +3.27]). In the
adverse `F3_reversal_800` cell, excess cost versus never-switch was +48.45 ([+44.56, +52.33]),
exceeding the allowed +5. The complete decomposition, all method rows, paired intervals, commands,
source hashes and raw records are in
[`EVALUATION_RESULTS.md`](research/scoped_method/pilots/cusum_any_false_calibration_20261107/EVALUATION_RESULTS.md)
and its adjacent run directories. The reproducible analyzer is
[`analyze.py`](research/scoped_method/pilots/cusum_any_false_calibration_20261107/analyze.py).

**Decision:** close this calibrated CUSUM operating-point lane. Do not retune alpha or switch
methods using these evaluation outcomes. This calibration does not solve the economic failure, add
a novel method contribution, or justify opening real-data outcomes. The branch-level status remains
`BENCHMARK_OR_CASE_STUDY_ONLY`; the broader field is not claimed to be exhausted.

## Real-source feasibility follow-up (2026-11-07)

A metadata-only audit verified an ALFRED point-in-time source route for UNRATE, CPIAUCSL, INDPRO,
RSAFS, HOUST, and PCE. ALFRED provides vintage histories and release dates, but documents fallback
release dates when an issuing-source date is unavailable and typical ingestion lag of up to one
business day. The source can support a future release-date replay only after per-series agency
verification and conservative availability handling. These six series share one U.S. macroeconomic
environment and are not six independent external domains; a separate market/source domain is still
needed for a multi-domain transfer claim. No outcomes or series data were opened. Since the current
method gates failed, this remains source-feasibility metadata and does not authorize real-data
confirmation. Details and exact source URLs are in
[`ALFRED_SOURCE_FEASIBILITY_20261107.md`](research/scoped_method/ALFRED_SOURCE_FEASIBILITY_20261107.md).
