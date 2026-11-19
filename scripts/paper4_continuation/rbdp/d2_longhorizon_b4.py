"""Delay-2 long-horizon study, B = 4 extension (T = 24..100). Appends to d2_longhorizon_cells.jsonl.

Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/d2_longhorizon_b4.py [minutes] [workers] [timeout_min]
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import d2_longhorizon_run as run  # noqa: E402

if __name__ == "__main__":
    minutes = float(sys.argv[1]) if len(sys.argv) > 1 else 300.0
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    timeout_min = float(sys.argv[3]) if len(sys.argv) > 3 else 90.0
    cells = [run.cell(t, 4, T, 401, "uniform") for T in (24, 32, 48, 64, 100) for t in run.TS]
    run.pool_run(cells, run.CELLS, minutes, workers, timeout=timeout_min * 60)
