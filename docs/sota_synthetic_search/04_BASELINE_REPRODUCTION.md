# Reuse verification and infrastructure smoke — checkpoint 1

## Scope and verdict

Continue. Existing local numerical components are usable, and the new run archive
works on a small synthetic diagnostic. Baseline source reproduction and substantive
algorithm discovery are not completed by this checkpoint.

The baseline-focused command passed 25 tests:

```powershell
python -m pytest -q tests/test_prediction_powered_evalues.py tests/test_pprm_risk_monitor.py tests/test_robust_asi_fixed_horizon.py tests/test_rpoq_exact.py
```

The new registry/supervisor tests passed four tests, covering append-only start and
terminal events, failed jobs, resource timeout, snapshot overwrite refusal, and
matched PPE/IPW diagnostics. These checks establish implementation properties,
not reproduction of every published source.

## First registered batch

Reproduction command from the isolated worktree root:

```powershell
$env:PYTHONPATH = 'src'
python scripts/sota_search/run_smoke.py --output outputs/sota_search/infrastructure_smoke_reproduction_UNIQUE
```

Use a new output name; existing snapshots are refused.

The executed snapshot is `outputs/sota_search/infrastructure_smoke_v1/`.
It contains a pre-execution manifest, 24 SQLite events for 12 attempted jobs,
per-run logs and result JSON, and `verification.json`. All 12 jobs completed;
all six paired worlds had identical alarm status, first-alarm time, and label use
under matched effective coefficients. Each method alarmed on three of its six
worlds. These counts are diagnostics, not a calibrated false-alarm or power estimate.

Summed worker wall time was 37.0945 seconds; maximum sampled process-tree resident
memory was 160,538,624 bytes. Sampling is not an exact peak measurement.

The initial commit attempt was rejected by the pre-commit lint hook, but the shell
continued to the already-preregistered smoke command. The manifest therefore
correctly records base commit `18878af0ff9fcdeae261c4c8fed86e53d82db61d` plus source
SHA256 `2d3ff4b26505f271f74e586f6801ff7f825a39028b912404a04fd2f04be0f751` for the
then-uncommitted worker/driver/module/budget source set. The source implementation
was subsequently committed in `8ca4dfd`. Do not describe the batch as having run
from a clean committed checkout. The current source set was rehashed to verify
an exact match, then archived as `executed_source.zip` beside the run manifest.
Future substantive manifests must refuse dirty
research source or archive the exact patch as well as its content hash.

## CI corrections and limits

The initial installed Ruff 0.15.18 check found 48 errors: 46 import-order errors
from direct-script path bootstrapping and two lambda assignments. Added narrowly
scoped bootstrap import annotations and rewrote the two lambdas as equivalent
functions. No real-data task was executed. Existing result artifacts and protocols
were not changed.

Pre-commit uses Ruff 0.17.1, whose default rule policy differed from the installed
version. `pyproject.toml` now explicitly selects the established E4/E7/E9/F policy
so both versions use the same checks. Both lint versions and the pre-commit checks
passed. Installed Ruff format checked all 637 Python files successfully.

The system Python lacks mypy. Running the existing repository environment's mypy
passed its configured two-file `src/shiftlab/core` scope. That narrow result does
not establish type checking of the new research modules. The full CI workflow and
full pytest suite have not been asserted green: data-dependent tests may access
real or protected data, which this programme forbids.

## Next checkpoint

Implement global budget accounting, exact clean-source manifests, the G1–G4
learner/evaluator generator boundary, and generator contract tests. Then audit and
adapt the remaining baseline families, freeze the substantive staged-screen
protocol, and run the requested 500–1,500 valid development configurations. Keep
Q1/Q2/Q3, source fidelity, scientific validity, and the mandatory later full-archive
synthesis separate from this integration smoke.
