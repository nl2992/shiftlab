"""Failure Atlas v1, Amendment 8 (cycle 7): locked development tuning of the DSS gap g.

Protocol: docs/failure_atlas_v1_protocol.md, Amendment 8 ("Candidate"). Development seeds
[160000, 170000) only (null screen: [160000, 160200); cost: [161000, 161040)). Locked rule:
  1. keep g in {1,4,8,16} (delay_switch on) whose null false promotion is <= alpha (0.1) at
     rho = 0.5, B/T in {0.05, 0.1, 0.25}, d = 1 (boundary family-3 null twins, 200 seeds each);
  2. among survivors take the lowest mean development cost over the 16 failure cells
     (5 family-1 cycle-3 + 11 family-3 cycle-5 reproduced shared failures, 40 seeds each);
  3. freeze it in <out>/tuning/frozen.json with the spec ids of the DSS and its ablations.
Costs are also computed for non-survivors (informative only; they cannot be selected).

    .venv/Scripts/python scripts/run_atlas_dss_tuning_v1.py --workers 8          # resumable
    .venv/Scripts/python scripts/run_atlas_dss_tuning_v1.py --smoke --out <dir>

Checkpoints: ``<out>/tuning/nulls.jsonl`` and ``costs.jsonl`` (one line per finished config).
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.dive import atlas_components as comp
from shiftlab.dive import failure_atlas as fa

ALPHA = 0.1
GAPS = (1, 4, 8, 16)
BTS = (0.05, 0.1, 0.25)
RHO = 0.5
D_NULL = 1
N_NULL = 200
NULL_OFFSET = 60000  # development [160000, 160200)
N_COST = 40
COST_OFFSET = 61000  # development [161000, 161040)
CHUNK = 10
T = fa.T_DEFAULT
F1_CELLS = (
    "on0.3_L0.6_strong_harmful_d10_b0.05_s0.1",
    "on0.6_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.6_L1_strong_harmful_d50_b0.05_s0.1",
    "on0.1_L0.6_strong_harmful_d1_b0.05_s0.1",
    "on0.1_L0.6_strong_harmful_d10_b0.05_s0.5",
)
F3_SUMMARY = ROOT / "outputs/failure_atlas_v1_cycle5/family3/summary.md"
F3_RE = re.compile(
    r"^f3_rho(?P<rho>[\d.]+)_on(?P<on>[\d.]+)_L(?P<L>[\d.]+)_(?P<ef>\w+?)_(?P<off>harmful|neutral)"
    r"_d(?P<d>\d+)_b(?P<b>[\d.]+)_s(?P<s>[\d.]+)$"
)


def f3_failure_ids() -> list[str]:
    ids = []
    txt = F3_SUMMARY.read_text("utf-8")
    sec = txt.split("## Reproduced failures", 1)[1].split("###", 1)[0]
    for line in sec.splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) > 2 and cols[0].startswith("f3_") and cols[1] == "shared_failure":
            ids.append(cols[0])
    return ids


def build_cell(cid: str):
    if cid.startswith("f3_"):
        m = F3_RE.match(cid)
        assert m, cid
        c = fa.Family3CellSpec(
            float(m["rho"]),
            float(m["on"]),
            float(m["L"]),
            m["ef"],
            m["off"],
            int(m["d"]),
            float(m["b"]),
            s=float(m["s"]),
        )
        assert c.cell_id == cid, (c.cell_id, cid)
        return c
    by_id = {c.cell_id: c for c in fa.all_cells(T)}
    return by_id[cid]


def null_cell(bt: float):
    return fa.Family3CellSpec(RHO, 0.3, 0.6, "strong", "harmful", D_NULL, bt).null_twin()


# ------------------------------------------------------------------ worker


def task(args: tuple) -> dict:
    kind, key, cell_id, gap, seed_list = args
    spec = comp.dss_spec(gap, True)
    cell = null_cell(float(cell_id)) if kind == "null" else build_cell(cell_id)
    out = []
    for sd in seed_list:
        stream = fa.make_stream(cell, sd)
        cfg = cell.config(sd)
        r = fa.run_for(cell, stream, comp.build_candidate(spec), cfg)
        out.append(int((r.fp_regime or 0) > 0) if kind == "null" else float(r.cost) / cell.T)
    return {"key": key, "seeds": [int(s) for s in seed_list], "vals": out}


def load_done(path: Path) -> dict[str, dict]:
    done = {}
    if path.exists():
        for line in path.read_text("utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue  # truncated last line from a killed process
            done[r["key"]] = r
    return done


def run_phase(path: Path, items: list[tuple], seed_list, workers: int) -> dict[str, dict]:
    """items: (kind, key, cell_id, gap). Appends one line per finished item; skips finished ones."""
    done = load_done(path)
    todo = [it for it in items if it[1] not in done or done[it[1]]["seeds"] != list(seed_list)]
    print(f"{path.name}: {len(done)} done, {len(todo)} to run", flush=True)
    work = [
        (*it, tuple(seed_list[i : i + CHUNK]))
        for it in todo
        for i in range(0, len(seed_list), CHUNK)
    ]
    nchunk = -(-len(seed_list) // CHUNK)
    parts: dict[str, list] = {it[1]: [] for it in todo}
    meta = {it[1]: it for it in todo}
    t0, fin = time.time(), 0
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for f in as_completed([pool.submit(task, w) for w in work]):
            r = f.result()
            parts[r["key"]].append(r)
            if len(parts[r["key"]]) == nchunk:
                ps = sorted(parts[r["key"]], key=lambda p: p["seeds"][0])
                it = meta[r["key"]]
                rec = {
                    "key": r["key"],
                    "kind": it[0],
                    "cell": it[2],
                    "gap": it[3],
                    "seeds": [s for p in ps for s in p["seeds"]],
                    "vals": [v for p in ps for v in p["vals"]],
                }
                with path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec) + "\n")
                done[r["key"]] = rec
                fin += 1
                el = time.time() - t0
                print(
                    f"[{el:.0f}s] {r['key']} ({fin}/{len(todo)}) "
                    f"ETA {el / fin * (len(todo) - fin):.0f}s",
                    flush=True,
                )
    return done


def git_head() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=str(ROOT / "outputs" / "failure_atlas_v1_cycle7"))
    ap.add_argument("--smoke", action="store_true", help="tiny seeds; writes frozen_smoke.json")
    a = ap.parse_args()
    workers = min(a.workers, 8)
    n_null, n_cost = (10, 10) if a.smoke else (N_NULL, N_COST)
    out = Path(a.out) / "tuning"
    out.mkdir(parents=True, exist_ok=True)
    nsd = fa.seeds("development", n_null, offset=NULL_OFFSET)
    csd = fa.seeds("development", n_cost, offset=COST_OFFSET)
    assert nsd[0] >= 160000 and nsd[-1] < 170000 and csd[0] >= 160000 and csd[-1] < 170000
    f3 = f3_failure_ids()
    assert len(f3) == 11, f3
    cost_cells = [*F1_CELLS, *f3]

    t0 = time.time()
    null_items = [("null", f"null_g{g}_bt{bt:g}", f"{bt:g}", g) for g in GAPS for bt in BTS]
    nulls = run_phase(out / "nulls.jsonl", null_items, nsd, workers)
    fp = {g: {bt: float(np.mean(nulls[f"null_g{g}_bt{bt:g}"]["vals"])) for bt in BTS} for g in GAPS}
    survivors = [g for g in GAPS if all(fp[g][bt] <= ALPHA for bt in BTS)]

    cost_items = [("cost", f"cost_g{g}_{c}", c, g) for g in GAPS for c in cost_cells]
    costs = run_phase(out / "costs.jsonl", cost_items, csd, workers)
    cell_cost = {
        g: {c: float(np.mean(costs[f"cost_g{g}_{c}"]["vals"])) for c in cost_cells} for g in GAPS
    }
    mean_cost = {g: float(np.mean(list(cell_cost[g].values()))) for g in GAPS}

    frozen_g = min(survivors, key=lambda g: mean_cost[g]) if survivors else None
    res = {
        "protocol": "docs/failure_atlas_v1_protocol.md Amendment 8, Candidate",
        "git_head": git_head(),
        "smoke": a.smoke,
        "alpha": ALPHA,
        "null_seeds": [nsd[0], nsd[-1] + 1],
        "cost_seeds": [csd[0], csd[-1] + 1],
        "null_fp": {str(g): {f"{bt:g}": fp[g][bt] for bt in BTS} for g in GAPS},
        "survivors": survivors,
        "mean_cost_over_failure_cells": {str(g): mean_cost[g] for g in GAPS},
        "cost_cells": cost_cells,
        "cell_cost": {str(g): cell_cost[g] for g in GAPS},
        "frozen_g": frozen_g,
        "elapsed_s": time.time() - t0,
        "evidence_status": "development tuning; not confirmatory",
    }
    (out / "results.json").write_text(json.dumps(res, indent=1), "utf-8")

    L = ["# DSS gap tuning (development seeds; locked rule; NOT confirmatory)", ""]
    L += [
        (
            f"null seeds [{nsd[0]}, {nsd[-1] + 1}) n={n_null}; "
            f"cost seeds [{csd[0]}, {csd[-1] + 1}) n={n_cost}"
        ),
        "",
    ]
    L += [
        "## Null false promotion (rho=0.5, d=1, boundary family-3 null twin)",
        "",
        "| g | "
        + " | ".join(f"B/T={bt:g}" for bt in BTS)
        + " | survives (all <= 0.1) | mean cost |",
        "|---|" + "---|" * (len(BTS) + 2),
    ]
    for g in GAPS:
        L.append(
            f"| {g} | "
            + " | ".join(f"{fp[g][bt]:.3f}" for bt in BTS)
            + f" | {'yes' if g in survivors else 'no'} | {mean_cost[g]:.4f} |"
        )
    L += [
        "",
        "## Mean cost per round by failure cell",
        "",
        "| cell | " + " | ".join(f"g={g}" for g in GAPS) + " |",
        "|---|" + "---|" * len(GAPS),
    ]
    for c in cost_cells:
        L.append(f"| {c} | " + " | ".join(f"{cell_cost[g][c]:.4f}" for g in GAPS) + " |")
    L += ["", f"Frozen g: {frozen_g}"]
    (out / "summary.md").write_text("\n".join(L) + "\n", "utf-8")

    frozen = {
        "status": "frozen" if (frozen_g is not None and not a.smoke) else "not_frozen",
        "frozen_g": frozen_g,
        "survivors": survivors,
        "rule": "survivors: null FP <= 0.1 at rho 0.5, B/T in {0.05,0.1,0.25}, d=1; "
        "then min mean dev cost over the 16 failure cells",
        "mean_cost_over_failure_cells": res["mean_cost_over_failure_cells"],
        "source_spec_id": comp.DSS_SOURCE_ID,
        "git_head": res["git_head"],
    }
    if frozen_g is not None:
        sp = comp.dss_spec(frozen_g, True)
        frozen["dss_spec_id"] = sp.spec_id
        frozen["params"] = dict(sp.params)
        frozen["ablation_spec_ids"] = {k: v.spec_id for k, v in comp.dss_ablations(sp).items()}
    name = "frozen_smoke.json" if a.smoke else "frozen.json"
    (out / name).write_text(json.dumps(frozen, indent=1), "utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
