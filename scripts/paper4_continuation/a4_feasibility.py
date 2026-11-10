"""A4 exploratory feasibility: R0 and F0 once each on one cell, fresh processes.

uv run --no-sync python scripts/paper4_continuation/a4_feasibility.py --cell T10D1 --out PATH
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

sys.set_int_max_str_digits(0)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.paper4_continuation.runner import run_child, sha256_file  # noqa: E402

ONE = Path(__file__).resolve().parent / "ablation_one.py"
CAP_SECONDS = 1200


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--methods", default="R0,F0")
    args = parser.parse_args()
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    runs = []
    for method in args.methods.split(","):
        child = run_child(
            [sys.executable, str(ONE), "--method", method, "--cell", args.cell], CAP_SECONDS
        )
        line = child.pop("stdout_last_line")
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            payload = None
        runs.append(dict(method=method, cell=args.cell, cap_seconds=CAP_SECONDS, **child,
                         result=payload))  # fmt: skip
        print(method, child["returncode"], child["wall_seconds_parent"], child["peak_rss_mib"])
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    record = {
        "purpose": "A4 exploratory feasibility (not the campaign)",
        "git_head": head.stdout.strip(),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "module_sha256": sha256_file(ROOT / "src/shiftlab/paper4_continuation/ablation.py"),
        "runner_module_sha256": sha256_file(ROOT / "src/shiftlab/paper4_continuation/runner.py"),
        "platform": platform.platform(),
        "runs": runs,
    }
    with open(out, "x") as handle:
        json.dump(record, handle, indent=1)


if __name__ == "__main__":
    main()
