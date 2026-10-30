"""E2 runner: per-stream rows for every cell, arm and engine (CPU).

Blocks:
- ``dev``: the smoke and power block (registry id e2_dev_smoke_and_power);
- ``grid``: the grid-selection block (e2_dev_grid), development only;
- ``confirmation``: the registered confirmation. It calls ``require_freeze`` on the P1 freeze
  record before any confirmation seed is generated, and takes its cells, order and n from the
  locked design file only (CLI sample sizes are rejected).

Seeds are used directly as per-stream seeds; each cell owns a disjoint sub-block.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from shiftlab.dive import e2_acquisition_pacing as e2  # noqa: E402 -- local script path bootstrap
from shiftlab.freeze import require_freeze  # noqa: E402 -- local script path bootstrap

STAGE1 = Path("docs/research_refinement_v1/stage1")
FREEZE_RECORD = ROOT / STAGE1 / "P1_E2_freeze.json"
LOCKED_DESIGN = ROOT / STAGE1 / "P1_E2_locked_design.json"


def _job(args: tuple[str, int]) -> list[dict]:
    cell, seed = args
    return e2.run_stream(cell, seed)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def build_jobs(args, freeze: dict | None) -> tuple[list[tuple[str, int]], dict]:
    """Return (cell, seed) jobs and the cell -> [lo, hi, n] mapping."""
    if args.block == "confirmation":
        if args.n_per_cell is not None or args.n_mech is not None or args.cells:
            raise SystemExit("confirmation takes cells and n from the locked design only")
        locked = json.loads(LOCKED_DESIGN.read_text(encoding="utf-8"))
        order, sizes = locked["order"], locked["n"]
        if set(order) != set(sizes) or len(order) != len(set(order)):
            raise SystemExit("locked design order and n disagree")
        plan = {name: (sizes[name], order) for name in order}
    elif args.block == "grid":
        names = args.cells or [c.name for c in e2.GRID_CELLS]
        plan = {name: (args.n_per_cell or e2.GRID_WIDTH, None) for name in names}
    else:
        if args.n_per_cell is None:
            raise SystemExit("--n-per-cell is required for dev")
        names = args.cells or [c.name for c in e2.ALL_CELLS]
        plan = {
            name: (args.n_per_cell if e2.CELLS[name].kind != "mech" else args.n_mech, None)
            for name in names
        }
    jobs: list[tuple[str, int]] = []
    ranges = {}
    for name, (n, order) in plan.items():
        if n is None:
            lo, hi = e2.cell_seed_range(args.block, name, order)
            n = hi - lo + 1
        seeds = e2.cell_seeds(args.block, name, n, order)
        jobs += [(name, s) for s in seeds]
        ranges[name] = [seeds[0], seeds[-1], n]
    return jobs, ranges


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", choices=sorted(e2.SEED_BLOCKS), required=True)
    parser.add_argument("--n-per-cell", type=int, default=None)
    parser.add_argument("--n-mech", type=int, default=None, help="mechanism cells (dev only)")
    parser.add_argument("--cells", nargs="*", default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    freeze = None
    if args.block == "confirmation":
        # Before any confirmation seed exists: the checkout must match the freeze record.
        freeze = require_freeze(FREEZE_RECORD)
    jobs, seeds = build_jobs(args, freeze)
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if args.workers > 1:
        with ProcessPoolExecutor(args.workers) as pool:
            results = list(pool.map(_job, jobs, chunksize=4))
    else:
        results = [_job(j) for j in jobs]
    frame = pd.DataFrame([r for batch in results for r in batch])
    frame.to_parquet(args.out / "rows.parquet", index=False)
    elapsed = time.perf_counter() - started
    manifest = {
        "experiment": "E2 acquisition and pacing",
        "block": args.block,
        "registry_id": e2.SEED_BLOCKS[args.block]["id"],
        "seed_block": [e2.SEED_BLOCKS[args.block]["start"], e2.SEED_BLOCKS[args.block]["end"]],
        "cell_seed_ranges_and_n": seeds,
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "config_sha256": e2.config_digest(),
        "freeze_record_git_head": freeze["git_head"] if freeze else None,
        "locked_design_sha256": (
            hashlib.sha256(LOCKED_DESIGN.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            if args.block == "confirmation"
            else None
        ),
        "streams": len(jobs),
        "rows": len(frame),
        "runtime_seconds": elapsed,
        "workers": args.workers,
        "python": platform.python_version(),
        "created_utc": datetime.now(UTC).isoformat(),
        "command": " ".join(sys.argv),
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{len(jobs)} streams, {len(frame)} rows, {elapsed:.0f}s -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
