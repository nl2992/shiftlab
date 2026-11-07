"""Shared resumable runner for the GAVE-R WP1b rho-robust Gap-Mix studies.

Reuses the WP1 cell definitions and record format (``run_gapmix_common``); only the method builder,
the rho grid (adds 0.99) and the seed block (``gaver_wp1b_rho_mixture``) differ.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from run_gapmix_common import ALT_TYPES, BUDGET_FRACS, D_DELAY, ROOT, T

from shiftlab.dive import failure_atlas as fa
from shiftlab.gaver import gapmix_rho as gr

RHOS_NULL = (0.0, 0.5, 0.8, 0.95, 0.99)
NULL_BASE, ALT_BASE = 101200000, 101220000
NULL_END, ALT_END = 101209999, 101243999
SMOKE_BASE = 7100000  # throwaway prototype seeds (outside the registered block)
NEG_CONTROLS = ("mixnaive_eq_s4", "mixnaive_w_s4")
NULL_METHODS = gr.METHOD_NAMES
POWER_METHODS = tuple(m for m in gr.METHOD_NAMES if m not in NEG_CONTROLS)
OUT = ROOT / "outputs/gaver/wp1b"


def null_cells() -> list[dict]:
    out = []
    for rho in RHOS_NULL:
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
    base, end = (NULL_BASE, NULL_END) if kind == "null" else (ALT_BASE, ALT_END)
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
            m = gr.build_gate(name)
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
                    "ub_final": float(m.ep.ub) if hasattr(m.ep, "ub") and m.ep.cs else None,
                }
            )
    return {"cell": cid, "seeds": list(seeds), "values": out}


def run_study(cells, n_seeds, chunk, out_dir: Path, smoke: bool, workers: int, methods):
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
                jobs.append((c["id"], c["cell"], part, tuple(methods)))
    print(f"{len(jobs)} chunks to run, {len(done)} done", flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool, path.open("a", encoding="utf-8") as fh:
        for k, rec in enumerate(pool.map(task, jobs)):
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
            print(f"[{k + 1}/{len(jobs)}] {rec['cell']} seeds {rec['seeds'][0]}", flush=True)
