# Working on the three papers

Use this single repository for the shared infrastructure and all three papers. `main` is the
integration branch and should remain runnable. Paper source, protocols and research logs live
in the existing `papers/paper1_decision_drift`, `papers/paper2_adaptive_conformal` and
`papers/paper3_cost_aware_adaptation` directories. Shared components stay under `src/shiftlab`.

Create short-lived branches when starting real work, for example:

```bash
git switch main
git switch -c paper1/decision-loss-study
# Other examples: paper2/delayed-calibration, paper3/retrain-budget, shared/data-validation
```

Separate infrastructure changes from paper-specific experiments when that makes review clearer.
Avoid permanent independent paper branches: they would duplicate and diverge shared methods.
Merge reviewed work back into `main`; record negative findings in the relevant research log.

## Install local checks

```bash
uv sync --extra dev
uv run python -X utf8 -m pre_commit install
uv run pre-commit run --all-files
uv run pytest -q
uv run mypy
```

The UTF-8 installation command also supports Windows repository paths containing non-ASCII characters.
The local hooks run pinned Ruff checks/formatting. CI also runs the CPU test suite and scoped
mypy checks. Each fresh clone must install its hooks; `.git/hooks` is intentionally not versioned.
CUDA and acquisition dependencies remain optional. Use the data documentation for those extras.

Commit code, tests, configs, protocols, literature records and selected aggregate reports.
Keep raw/proprietary data, credentials, environment files, local dataset indexes, model weights
and large generated experiment outputs outside Git. Reports must avoid record-level proprietary
observations. Dataset manifests/checksums and experiment metadata connect results to code and
inputs; Git does not replace data licensing, immutable storage or acquisition receipts.

Use meaningful commits such as `feat(data): add recurring variance stream` or
`paper2: record delayed-label calibration experiment`. Describe the actual scientific result;
do not imply novelty or success before validation. Use the existing Git author identity.

For a reproducibility snapshot, commit the implementation and configuration before running
experiments, then commit selected aggregate reports in a follow-up commit. Their saved code
revision identifies the implementation used. Add an annotated tag for a reviewed milestone:

```bash
git tag -a paper1-baseline-2026-10-19 -m "Reviewed Paper 1 baseline snapshot"
```

That is an example naming convention; it does not declare the paper complete. The existing tag
`data-foundation-2026-10-19` points to the executed data-foundation report snapshot. Never move
an already shared result tag; use a new tag after corrections and record invalidated results.

## Remote collaboration

No remote is assumed or created automatically. After a repository URL is supplied:

```bash
git remote add origin <repository-url>
git push -u origin main
git push origin data-foundation-2026-10-19
```

The remote owner's permissions are required to configure protected branches. Once hosted,
require pull requests and the `CPU checks / test` status check on `main`, and disable force pushes
and deletion. These are recommended hosting settings, not protections enforced by local Git.
Make repository visibility and collaborator access explicit before publishing research data.
