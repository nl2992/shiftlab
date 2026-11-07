"""Stage 2: run every registered baseline on the dev partition over the dev grid (PROTOCOL sections 3-5).

Resumable: one parquet shard per cell in <out>/shards/. Cells are processed in cell-batches (one tape per
batch) and the shard of each cell is written as soon as its batch finishes. Afterwards the per-seed
parquet, summary.parquet and frontier.json are written and, for a full run, the frontier hash is
registered with freeze.py. ``--smoke`` uses a few cells into <out>_smoke and never freezes.

  PYTHONPATH=src .venv/Scripts/python.exe scripts/hgxh2c/stage2_benchmark.py [--seeds 256] [--smoke]
"""

import argparse
import hashlib
import json
import re
import time
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import torch

from shiftlab.hgxh2c import baselines as BL
from shiftlab.hgxh2c import tapes as TP
from shiftlab.hgxh2c.evaluate import run

ROOT = Path(__file__).resolve().parents[2]


def shard_path(shards, cell):
    return shards / (re.sub(r"[^A-Za-z0-9_.-]", "_", cell.cell_id) + ".parquet")


def smoke_cells(T):
    mk = lambda f, m, d, r, p: TP.ScenarioCell(f, m, d, r, p, T)
    return [mk("coshift", 0.08, 5, "b20", "good"), mk("null_stationary", 0.0, 5, "b20", "good"),
            mk("opposed", 0.08, 20, "b05", "biased"), mk("cost_only", 0.16, 0, "full", "noisy")]  # fmt: skip


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=256)
    ap.add_argument("--T", type=int, default=2000)
    ap.add_argument("--out", default="outputs/hgxh2c/stage2")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--batch", type=int, default=108, help="cells per tape batch")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--methods", default="", help="comma list, default: all registered")
    a = ap.parse_args()
    out = ROOT / (a.out + ("_smoke" if a.smoke else ""))
    shards = out / "shards"
    shards.mkdir(parents=True, exist_ok=True)
    cells = smoke_cells(a.T) if a.smoke else TP.dev_grid(a.T)
    methods = [m for m in a.methods.split(",") if m] or list(BL.REGISTRY)
    todo = [c for c in cells if not shard_path(shards, c).exists()]
    print(
        f"{len(cells)} cells, {len(todo)} to do, {len(methods)} methods, {a.seeds} seeds, device {a.device}",
        flush=True,
    )
    timings = []
    for i in range(0, len(todo), a.batch):
        chunk = todo[i : i + a.batch]
        t0 = time.perf_counter()
        df = run(methods, chunk, "dev", a.seeds, a.device)
        if a.device.startswith("cuda"):
            torch.cuda.synchronize()
        dt = time.perf_counter() - t0
        for (
            c
        ) in chunk:  # write after the batch is complete: a shard exists only if its cell is done
            part = df[df.cell_id == c.cell_id]
            tmp = shard_path(shards, c).with_suffix(".tmp")
            part.to_parquet(tmp, index=False)
            tmp.replace(shard_path(shards, c))
        timings.append({"cells": len(chunk), "seconds": dt, "sec_per_cell": dt / len(chunk)})
        print(
            f"batch {i // a.batch}: {len(chunk)} cells in {dt:.1f}s ({dt / len(chunk):.2f} s/cell)",
            flush=True,
        )
    if timings:
        (out / "timings.json").write_text(json.dumps(timings, indent=1))
    finalize(out, cells, a)


def finalize(out, cells, a):
    from shiftlab.hgxh2c import stats

    files = [shard_path(out / "shards", c) for c in cells]
    missing = [f.name for f in files if not f.exists()]
    if missing:
        raise SystemExit(f"{len(missing)} shards missing, not finalizing")
    writer, sums = None, []
    for f in files:
        d = pd.read_parquet(f)
        sums.append(stats.summarise(d, a.T))
        tab = pa.Table.from_pandas(d, preserve_index=False)
        writer = writer or pq.ParquetWriter(out / "per_seed.parquet", tab.schema)
        writer.write_table(tab)
    writer.close()
    summary = pd.concat(sums, ignore_index=True)
    summary.to_parquet(out / "summary.parquet", index=False)
    fr = stats.frontier(summary)
    fr["methods"] = {
        k: {"track": v[1], "fidelity": v[2], "notes": v[3]} for k, v in BL.REGISTRY.items()
    }
    fr["config"] = {
        "seeds": a.seeds,
        "T": a.T,
        "partition": "dev",
        "n_cells": len(cells),
        "smoke": bool(a.smoke),
    }
    fp = out / "frontier.json"
    fp.write_text(json.dumps(fr, indent=1, sort_keys=True))
    print("frontier sha256", hashlib.sha256(fp.read_bytes()).hexdigest(), flush=True)
    if not a.smoke:
        try:
            from shiftlab.hgxh2c import freeze

            print("registered", freeze.freeze("frontier", fp), flush=True)
        except Exception as e:  # freeze must be explicit about failure, never silent
            print("FREEZE FAILED:", repr(e), flush=True)
            raise


if __name__ == "__main__":
    main()
