# Local test environment (W1, 2026-11-06)

**Result:** with the project's own optional dependencies installed, the full suite passes on macOS
arm64: **3,337 passed, 46 skipped, 0 failed** (pytest 9.1.1, Python 3.12.2, about 70 minutes,
commit `f69382fa`).

## Why the suite failed before

All 34 failures and 85 collection errors in the earlier local run came from missing optional
packages, not from code defects:

- `torch` (`neural` extra). `uv.lock` pins `torch==2.9.1+cu130`, which has no macOS wheel, so
  `uv sync --locked` cannot install it on this machine. That accounted for 33 failures and 73 errors.
- `river` (`drift` extra). 12 collection errors.
- One failure was a defect in the new `tests/p2_benchmark` test, fixed in `f69382fa`.

## Setup on macOS

```bash
uv sync --extra dev --locked
uv pip install --python .venv/bin/python "torch==2.9.1" "river==0.26.1" "folktables>=0.0.12"
uv run pytest -q
```

The second command installs the CPU build of the locked torch version and the locked `river`
outside the lock, because the lock's CUDA build cannot be installed on macOS. CI on Linux uses the
locked extras unchanged. The `wilds` extra (torchvision) was not needed by any test.

Experiment runners need the simulator on the path:
`PYTHONPATH=scripts/promising_directions/sota`.
