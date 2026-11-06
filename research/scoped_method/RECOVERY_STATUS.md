# Recovery and headroom checkpoint (2026-11-06)

## Phase 0 — CI recovery

The reported GitHub Actions run was `42179919497` at commit
`e7f4dca60c3a39c5a97ceb21efb4b311d2d96e8b`. Its `uv run ruff check .` step failed with 506
findings (332 automatically fixable), primarily import ordering/formatting, unused `noqa`
directives, and redundant casts. Retrieved with:

```sh
gh run view 42179919497 --log-failed
```

The repair is already present in ancestor commit `82e1c48e` (`Fix Ruff lint and formatting checks`);
it changes Ruff formatting/lint findings across 137 files. This checkpoint does not redo that
repair or overwrite any experiment artifacts. Current branch: `codex/scoped-method-research-results-2026-11-06`,
starting commit `28e21f2c`.

Commands run on the current checkout:

```sh
uv run ruff check .
```

Result: **passed** (`All checks passed!`). Current GitHub Actions run `42307382928` also reports
success for locked dependency setup, Ruff lint, Ruff format check, and mypy. At checkpoint time its
full `uv run pytest -q` step was still in progress; environment validation was pending. Do not
interpret the full suite as passed until that run completes. No experiment or test output was
modified by this recovery note.

## Phase 1 — Reconciliation of prior evidence

| Observation to verify | Reconciled evidence |
|---|---|
| E_rb and B2 matched exactly on 90 pilot episodes | `research/scoped_method/pilots/rollback_acquisition_30seed_20261106/summary.json` records exact equality on the common-seed regime; the prior pilot covers three 30-seed environments (90 paired episodes). This is a specific implementation/pilot result, not general equivalence. |
| Never-switch beat E_rb in all three pilot environments | Same summary: E_rb minus never-switch is positive in `F3_reversal_800` (+46.20, 95% CI [+38.46,+53.94]), `F4_recurrent` (+34.53 [+26.04,+43.03]), and `S_reversal_400` (+26.93 [+17.48,+36.38]). |
| Conventional SR/CUSUM guarantees are incomparable absent calibration | `docs/scoped_method_research_2026-11-06/BASELINE_FIDELITY.md` distinguishes E_srr's ARL target from per-horizon/any-false-promotion probability. The economic matrix's E_srr port promoted on all 30 null streams; it cannot support an equal-safety advantage without separately calibrated null control. |
| Direct front-loaded acquisition + E_rb was not evaluated | This was true at the first headroom decision, but has since been evaluated in `research/scoped_method/pilots/direct_frontload_erb_20261106/`. The exploratory 20-seed/cell composition did not clear its economic gate and was worse than never-switch under reversal; protocol timing was not independently verifiable. |
| Adaptive-range correction changes historical provenance | Confirmed in `docs/failure_atlas_v2_flq/results/comparator_validity_audit_20261105.md` and `docs/scoped_method_research_2026-11-06/CORRECTED_REPLAY_AUDIT.md`. Pre-fix comparison tables are historical and must not be pooled with corrected results. |
| No independent real-data confirmation has been performed | No repair has independent real-data confirmation. A single-source chronological HuffPost replay was opened and was adverse to canonical PFA-SR; this is a negative transfer case study with simulated 24-hour label release, not positive confirmation of a repair. |

## Phase 2 — Economic opportunity decision

The precommitted five-cell, 30-paired-seed development matrix is in
`research/scoped_method/pilots/economic_headroom_matrix_20261106/`. It covers persistent gain,
economically worthwhile and unfavorable reversals, null, and delayed/scarce feedback under shared
horizon, budget, delay, query cost and switch cost. The feasible reference is never-switch; the
truth-aware oracle is evaluator-only. Main results and full cost decomposition are in
`run/RESULTS.md` and `run/summary.json`.

No certified/applicable policy passed the frozen gate of at least five net-cost units saved with a
paired 95% interval below zero in a worthwhile cell, while limiting harm in the unfavorable and
null cells. On the worthwhile reversal, E_rb was +25.63 cost units vs never-switch (95% CI
[+16.91,+34.36]) and E_swcert was +23.51 ([+14.34,+32.68]). On persistent and delayed/scarce gain,
E_rb's incremental savings against the frozen Xu-acquisition-only adapter were unresolved and
below the five-unit practical gate. The economic replacement reference is uncertified and does not
meet the null safety gate. Conventional E_srrSR reduced cost by 18.83 in the worthwhile reversal
cell (95% CI [-30.96,-6.71]) but promoted in 30/30 null streams; its ARL claim does not qualify it
for the same safety comparison.

**Decision:** tested environments do not identify safety-qualified economic headroom for a new
joint method. This rejects the tested candidates and compositions, not the whole research question
or all possible environments. Phase 3/4 novelty and candidate development gates are therefore not
entered. The smallest next step already specified in the matrix assessment is a prospective
any-false-promotion calibration of the conventional two-sided restart detector, then rerun only the
two reversal cells and null. No real-data confirmation should open before that gate.

## Reproduction

```sh
git status --short --branch
gh run view 42179919497 --log-failed
uv run ruff check .
gh run view 42307382928 --json status,conclusion,jobs
```

The research matrix reproduction command and frozen policy contract are preserved in
`research/scoped_method/pilots/economic_headroom_matrix_20261106/protocol.md`; this recovery
checkpoint does not rerun its prior experiment.
