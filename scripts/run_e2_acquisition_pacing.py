"""E2 runner: per-stream rows for every cell, arm and engine (CPU).

The ``confirmation`` block is only run after the P1 protocol is frozen. Seeds are used directly
as per-stream seeds; each cell owns a disjoint sub-block of the registered block.
"""

from __future__ import annotations

import argparse
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

from shiftlab.dive import e2_acquisition_pacing as e2


def _job(args: tuple[str, int]) -> list[dict]:
    cell, seed = args
    return e2.run_stream(cell, seed)


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--block", choices=sorted(e2.SEED_BLOCKS), required=True)
    parser.add_argument("--n-per-cell", type=int, required=True, help="primary cells")
    parser.add_argument("--n-mech", type=int, default=None, help="mechanism cells (default: all)")
    parser.add_argument("--cells", nargs="*", default=None)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    names = args.cells or [c.name for c in e2.ALL_CELLS]
    jobs = []
    for name in names:
        n = args.n_per_cell if e2.CELLS[name].kind != "mech" else args.n_mech
        if n is None:
            n = (
                e2.cell_seed_range(args.block, name)[1]
                - e2.cell_seed_range(args.block, name)[0]
                + 1
            )
        jobs += [(name, s) for s in e2.cell_seeds(args.block, name, n)]
    args.out.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    if args.workers > 1:
        with ProcessPoolExecutor(args.workers) as pool:
            results = list(pool.map(_job, jobs, chunksize=4))
    else:
        results = [_job(j) for j in jobs]
    rows = [r for batch in results for r in batch]
    frame = pd.DataFrame(rows)
    frame.to_parquet(args.out / "rows.parquet", index=False)
    elapsed = time.perf_counter() - started
    seeds = {
        n: [*e2.cell_seed_range(args.block, n), sum(1 for c, _ in jobs if c == n)] for n in names
    }
    manifest = {
        "experiment": "E2 acquisition and pacing",
        "block": args.block,
        "registry_id": e2.SEED_BLOCKS[args.block]["id"],
        "seed_block": [e2.SEED_BLOCKS[args.block]["start"], e2.SEED_BLOCKS[args.block]["end"]],
        "cell_seed_ranges_and_n": seeds,
        "git_head": _git("rev-parse", "HEAD"),
        "git_dirty": bool(_git("status", "--porcelain")),
        "config_sha256": e2.config_digest(),
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
