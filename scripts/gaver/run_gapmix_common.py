"""Shared resumable runner for the GAVE-R WP1 Gap-Mix studies (null calibration and power).

One task = (cell, chunk of paired seeds); every method sees the same stream per seed. Records are
appended to ``records.jsonl`` as they finish, so a killed run resumes where it stopped.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_k, "1")
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver import gapmix as gm

T, D_DELAY = 1000, 10
RHOS = (0.0, 0.5, 0.8, 0.95)
BUDGET_FRACS = (0.1, 0.25)  # B = 100 (gap ~10), B = 250 (gap ~4)
# (label, onset, duration, effect)
ALT_TYPES = (
    ("early", 0.3, 1.0, "strong"),
    ("late", 0.6, 1.0, "strong"),
    ("transient", 0.3, 0.3, "strong"),
    ("early_med", 0.3, 1.0, "medium"),
)
WP1_NULL_BASE, WP1_ALT_BASE = 101000000, 101040000  # registered sub-ranges (01_HARNESS_MAP.md)
WP1_NULL_END, WP1_ALT_END = 101039999, 101079999
SMOKE_BASE = 7000000  # throwaway prototype seeds


def null_cells() -> list[dict]:
    out = []
    for rho in RHOS:
        for bt in BUDGET_FRACS:
            cell = fa.Family3CellSpec(
                rho, 0.3, 0.6, "strong", "harmful", D_DELAY, bt, T=T
            ).null_twin()
            out.append({"id": f"null_rho{rho:g}_bt{bt:g}", "kind": "null", "cell": cell})
    return out


def alt_cells() -> list[dict]:
    out = []
    for typ, onset, dur, eff in ALT_TYPES:
        for rho in (0.0, 0.5, 0.8):
            for bt in BUDGET_FRACS:
                cell = fa.Family3CellSpec(rho, onset, dur, eff, "harmful", D_DELAY, bt, T=T)
                out.append({"id": f"alt_{typ}_rho{rho:g}_bt{bt:g}", "kind": "alt", "cell": cell})
    return out


def seeds_for(kind: str, idx: int, n: int, smoke: bool) -> list[int]:
    if smoke:
        return [SMOKE_BASE + (0 if kind == "null" else 500000) + idx * 1000 + i for i in range(n)]
    base, end = (WP1_NULL_BASE, WP1_NULL_END) if kind == "null" else (WP1_ALT_BASE, WP1_ALT_END)
    s = [base + idx * 1000 + i for i in range(n)]
    if s[-1] > end:
        raise ValueError("seed block overflow")
    return s


def task(args):
    cid, cell, seeds, methods = args
    out = {m: [] for m in methods}
    for seed in seeds:
        stream = fa.make_stream(cell, seed)
        for name in methods:
            cfg = cell.config(seed)
            m = gm.build_gate(name)
            r = fa.run_for(cell, stream, m, cfg)
            path = stream.truth.regime
            onset = int(np.argmax(path)) + 1 if path.any() else None
            hit = np.nonzero((r.actions == 1) & (path == 1))[0]
            out[name].append(
                {
                    "fp": int((r.fp_regime or 0) > 0),
                    "promoted": int(r.promotions > 0),
                    "on_promo_t": int(hit[0]) + 1 if len(hit) else None,
                    "onset": onset,
                    "alarm_ev": m.first_alarm_ev,
                    "n_used": m.n_used,
                    "queries": int(r.queries),
                    "cost": float(r.cost) / cell.T,
                }
            )
    return {"cell": cid, "seeds": list(seeds), "values": out}


def run_study(cells, n_seeds, chunk, out_dir: Path, smoke: bool, workers: int, methods=None):
    methods = tuple(methods or gm.METHOD_NAMES)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "records.jsonl"
    done = set()
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            r = json.loads(line)
            done.add((r["cell"], r["seeds"][0]))
    jobs = []
    for idx, c in enumerate(cells):
        sd = seeds_for(c["kind"], idx, n_seeds, smoke)
        for i in range(0, n_seeds, chunk):
            part = sd[i : i + chunk]
            if (c["id"], part[0]) not in done:
                jobs.append((c["id"], c["cell"], part, methods))
    print(f"{len(jobs)} chunks to run, {len(done)} done", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool, path.open("a", encoding="utf-8") as fh:
        for k, rec in enumerate(pool.map(task, jobs)):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[{k + 1}/{len(jobs)}] {rec['cell']} seeds {rec['seeds'][0]}", flush=True)
