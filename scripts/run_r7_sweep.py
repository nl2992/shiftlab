"""Run the R7 adaptation-strength sweep (docs/r7_adaptation_strength_sweep_protocol.md)."""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

import pandas as pd

from shiftlab.dive.gated_monitor_comparison import comparison_seed

ROOT = Path(__file__).resolve().parents[1]
STRENGTHS = (0.10, 0.25, 0.50, 0.75, 1.00)
BUDGETS = (0.02, 0.05, 0.10, 0.20)
SEEDS = range(61000000, 61000100)


def one_task(task: tuple) -> list[dict]:
    return comparison_seed("harmful_adaptation", *task)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    out = ROOT / ("outputs/r7_sweep_smoke" if args.smoke else "outputs/r7_sweep")
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"refusing to overwrite {out}")
    seeds = list(SEEDS)[:2] if args.smoke else list(SEEDS)
    tasks = [(seed, b, "cpu", s) for s in STRENGTHS for b in BUDGETS for seed in seeds]
    out.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with ProcessPoolExecutor(args.workers, mp_context=get_context("spawn")) as pool:
        rows = [row for block in pool.map(one_task, tasks, chunksize=4) for row in block]
    pd.DataFrame(rows).to_parquet(out / "streams.parquet", index=False)
    (out / "manifest.json").write_text(
        json.dumps(
            {
                "tasks": len(tasks),
                "strengths": STRENGTHS,
                "budgets": BUDGETS,
                "seeds": [seeds[0], seeds[-1]],
                "runtime_seconds": time.perf_counter() - start,
                "device": "cpu",
            },
            indent=2,
        )
        + "\n"
    )
    print(f"{len(tasks)} tasks, {time.perf_counter() - start:.0f}s")


if __name__ == "__main__":
    main()
