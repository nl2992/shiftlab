"""A3 repeated timing campaign: every (method, cell, rep) in its own fresh process.

    uv run --no-sync python scripts/paper4_continuation/ablation_campaign.py --reps 5 --out PATH

Round-robin interleaved: for rep in range(reps): for cell: for method.  Per-child peak RSS
comes from ``os.wait4`` (rusage of that pid only).  1200 s cap per child.  Refuses to overwrite
PATH.  Run only on a quiet CPU (protocol A3_A4_ABLATION_PROTOCOL_V1).
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

sys.set_int_max_str_digits(0)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.paper4_continuation.runner import run_child, sha256_file  # noqa: E402

METHODS = ("R0", "R1", "R2", "I0", "F0")
CELLS = ("C6", "S1", "T10D1")
CAP_SECONDS = 1200
PROTOCOL = ROOT / "docs/paper4_continuation/protocols/A3_A4_ABLATION_PROTOCOL_V1.md"
RUNNER = Path(__file__).resolve()
ONE = RUNNER.parent / "ablation_one.py"
MODULE = ROOT / "src/shiftlab/paper4_continuation/ablation.py"
RUNNER_MODULE = ROOT / "src/shiftlab/paper4_continuation/runner.py"


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reps", type=int, required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--cells", default=",".join(CELLS))
    parser.add_argument("--methods", default=",".join(METHODS))
    parser.add_argument("--max-nodes", type=int, default=200_000)
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    cells, methods = args.cells.split(","), args.methods.split(",")
    runs = []
    for rep in range(args.reps):
        for cell in cells:
            for method in methods:
                command = [
                    sys.executable, str(ONE), "--method", method, "--cell", cell,
                    "--max-nodes", str(args.max_nodes),
                ]  # fmt: skip
                child = run_child(command, CAP_SECONDS)
                line = child.pop("stdout_last_line")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    payload = None
                runs.append(
                    dict(rep=rep, cell=cell, method=method, cap_seconds=CAP_SECONDS, **child,
                         result=payload)
                )  # fmt: skip
                total = (payload or {}).get("phases", {}).get("total")
                print(rep, cell, method, child["returncode"], child["wall_seconds_parent"], total,
                      child["peak_rss_mib"], flush=True)  # fmt: skip
    record = {
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": sha256_file(PROTOCOL),
        "runner_sha256": sha256_file(RUNNER),
        "ablation_one_sha256": sha256_file(ONE),
        "module_sha256": sha256_file(MODULE),
        "runner_module_sha256": sha256_file(RUNNER_MODULE),
        "git_head": git_head(),
        "platform": platform.platform(),
        "python": sys.version,
        "created_unix": time.time(),
        "reps": args.reps,
        "cells": cells,
        "methods": methods,
        "runs": runs,
    }
    with open(out, "x") as handle:  # 'x' also refuses overwrite atomically
        json.dump(record, handle, indent=1)


if __name__ == "__main__":
    main()
