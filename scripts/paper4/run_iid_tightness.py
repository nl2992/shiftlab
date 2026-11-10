"""Run the IID-tightness check (protocol IID_TIGHTNESS_CHECK_V1) on C1-C6 and S1-S3.

    uv run --no-sync python scripts/paper4/run_iid_tightness.py            # all cells
    uv run --no-sync python scripts/paper4/run_iid_tightness.py --cell C2  # child mode: one JSON line

Each cell runs in its own subprocess (1200 s cap). Refuses to overwrite the results file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
import traceback
from fractions import Fraction as F
from pathlib import Path

sys.set_int_max_str_digits(0)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

CELLS = ("C1", "C2", "C3", "C4", "C5", "C6", "S1", "S2", "S3")
CAP_SECONDS = 1200
PROTOCOL = ROOT / "docs/paper4/experiments/protocols/IID_TIGHTNESS_CHECK_V1.md"
MODULE = ROOT / "src/shiftlab/paper4/iid_tightness.py"
OUT = ROOT / "docs/paper4/experiments/results/iid_tightness_v1.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonable(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def child(cell: str) -> None:
    started = time.perf_counter()
    try:
        from shiftlab.paper4.iid_tightness import check_cell, make_cell

        result = {"status": "ok", **check_cell(*make_cell(cell))}
    except Exception as exc:  # recorded verbatim, never skipped
        result = {
            "status": "failed",
            "error": repr(exc),
            "trace": traceback.format_exc(),
            "seconds": time.perf_counter() - started,
        }
    result["cell"] = cell
    print(json.dumps(jsonable(result)), flush=True)


def parent() -> None:
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    cells = {}
    for cell in CELLS:
        started = time.perf_counter()
        try:
            proc = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), "--cell", cell],
                capture_output=True,
                text=True,
                timeout=CAP_SECONDS,
                check=False,
            )
            lines = [ln for ln in proc.stdout.splitlines() if ln.startswith("{")]
            if lines:
                cells[cell] = json.loads(lines[-1])
            else:
                cells[cell] = {
                    "status": "failed",
                    "error": f"no JSON output, returncode {proc.returncode}",
                    "stderr_tail": proc.stderr[-2000:],
                }
        except subprocess.TimeoutExpired:
            cells[cell] = {"status": "timeout", "cap_seconds": CAP_SECONDS}
        cells[cell]["wall_seconds"] = time.perf_counter() - started
        print(
            cell,
            cells[cell].get("status"),
            cells[cell].get("classification"),
            cells[cell].get("contrast_check"),
            f"{cells[cell]['wall_seconds']:.1f}s",
            flush=True,
        )
    payload = {
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": sha256(PROTOCOL),
        "runner_sha256": sha256(Path(__file__).resolve()),
        "module_sha256": sha256(MODULE),
        "cap_seconds": CAP_SECONDS,
        "cells": cells,
    }
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print("wrote", OUT)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", choices=CELLS)
    args = ap.parse_args()
    child(args.cell) if args.cell else parent()
