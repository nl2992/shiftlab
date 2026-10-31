"""A2: screen for the risk-specific timing gap at alpha 1/20 and 1/10 (protocols/A2-binding-alpha-screen.md)."""

import argparse
import itertools
import json
import multiprocessing as mp
import sys
import time
from fractions import Fraction as F
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import a1_exact_separation as a1
import a1d_mixture_comparator as a1d

OUT = Path("docs/promising_directions/results/a2")
LEVELS = ["1/20", "1/10"]
GRID = [
    "0", "1/20", "1/10", "1/8", "3/20", "1/6", "9/50",
    "1/5", "1/4", "3/10", "2/5", "1/2", "3/4", "1",
]  # fmt: skip
EFFECT = F(1, 200)


def families() -> list[dict]:
    out = []
    for acc, trans, prior1, cs in itertools.product(
        ["9/10", "19/20", "49/50"],
        ["1/20", "1/10", "1/5"],
        ["1/20", "1/10", "1/5"],
        ["1/20", "1/5"],
    ):
        e1 = F(acc)
        out.append(
            {
                "T": 8,
                "B": 3,
                "d": 1,
                "trans": trans,
                "e0": str(1 - e1),
                "e1": acc,
                "cq": "1/100",
                "cs": cs,
                "prior1": prior1,
            }
        )
    return out


def fam_key(p: dict) -> str:
    return "|".join(f"{k}={p[k]}" for k in ("e1", "trans", "prior1", "cs"))


def init(root: str) -> None:
    a1.load_solver(root)


def screen_work(p: dict) -> dict:
    try:
        return {**a1.solve_cell(p), "status": "completed"}
    except (MemoryError, RuntimeError) as e:
        return {"params": p, "status": "failed", "error": repr(e)}


def calendar_work(task: tuple[dict, str, tuple]) -> dict:
    fam, a, cal = task
    p = {**fam, "alpha": a}
    try:
        cfg, model = a1.make(p)
        rep = a1._SOLVER["Calendar"](cfg, model, cal).solve()[0]
        return {
            "family": fam_key(fam),
            "a": a,
            "calendar": list(cal),
            "status": "completed",
            "cost": str(F(rep["calibrated_total_cost"])),
            "risk_bound": str(F(rep["calibrated_risk_bound"])),
        }
    except (MemoryError, RuntimeError) as e:
        return {
            "family": fam_key(fam),
            "a": a,
            "calendar": list(cal),
            "status": "failed",
            "error": repr(e),
        }


def run(tasks, fn, path: Path, key, workers: int, deadline: float) -> None:
    done = {key(r) for r in a1.read_jsonl(path)}
    todo = [t for t in tasks if key(t) not in done]
    with mp.Pool(workers, initializer=init, initargs=(a1.DEFAULT_SOLVER_ROOT,)) as pool:
        for row in pool.imap_unordered(fn, todo):
            with path.open("a") as f:
                f.write(json.dumps(row) + "\n")
            if time.time() > deadline:
                pool.terminate()
                break


def screen_key(x: dict) -> str:
    p = x.get("params", x)
    return f"{fam_key(p)}|alpha={p['alpha']}"


def gap(r: dict) -> F:
    return F(r["rel_gap"])


def survivors(rows: list[dict]) -> list[dict]:
    by = {}
    for r in rows:
        if r["status"] == "completed":
            by.setdefault(fam_key(r["params"]), {})[r["params"]["alpha"]] = r
    cands = []
    for cells in by.values():
        if "1" not in cells:
            continue
        g1 = gap(cells["1"])
        for a in LEVELS:
            if a in cells and gap(cells[a]) - g1 >= EFFECT:
                cands.append((gap(cells[a]) - g1, gap(cells[a]), cells[a]["params"], a))
    cands.sort(key=lambda c: (c[0], c[1]), reverse=True)
    seen, out = set(), []
    for exc, g, p, a in cands:
        k = fam_key(p)
        if k in seen:
            continue
        seen.add(k)
        levels = [lv for lv in LEVELS if lv in by[k] and gap(by[k][lv]) - gap(by[k]["1"]) >= EFFECT]
        out.append(
            {"family": {q: p[q] for q in p if q != "alpha"}, "levels": levels, "excess": float(exc)}
        )
        if len(out) == 3:
            break
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["screen", "mixture", "summary"], required=True)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "provenance.json").write_text(
        json.dumps(a1.verify_solver(Path(a1.DEFAULT_SOLVER_ROOT)), indent=2)
    )
    deadline = time.time() + 1.5 * 3600
    screen_path = OUT / "screen.jsonl"
    if args.part == "screen":
        tasks = [{**f, "alpha": a} for f in families() for a in [*LEVELS, "1"]]
        run(tasks, screen_work, screen_path, screen_key, args.workers, deadline)
        return
    surv = survivors(a1.read_jsonl(screen_path))
    mix_path = OUT / "calendar_values.jsonl"
    if args.part == "mixture":
        tasks = [(s["family"], a, cal) for s in surv for a in GRID for cal in a1.calendars(8, 3, 1)]
        run(
            tasks,
            calendar_work,
            mix_path,
            lambda x: (
                f"{x['family'] if isinstance(x, dict) else fam_key(x[0])}|{x['a'] if isinstance(x, dict) else x[1]}|{x['calendar'] if isinstance(x, dict) else list(x[2])}"
            ),
            args.workers,
            deadline,
        )
        return
    screen = {screen_key(r): r for r in a1.read_jsonl(screen_path) if r["status"] == "completed"}
    vals = [r for r in a1.read_jsonl(mix_path) if r["status"] == "completed"]
    results = []
    for s in surv:
        k = fam_key(s["family"])
        pts = {}
        for r in vals:
            if r["family"] == k:
                a, c = F(r["a"]), F(r["cost"])
                pts[a] = min(pts.get(a, c), c)
        hull = a1d.lower_hull(sorted(pts.items()))
        row = {"family": s["family"], "screen_levels": s["levels"], "cells": {}}
        for a in [*LEVELS, "1"]:
            r = screen[f"{k}|alpha={a}"]
            j, cstar = F(r["J"]), F(r["C_star"])
            assert pts[F(a)] == cstar, (k, a)
            cmix = a1d.evaluate(hull, F(a))[0]
            assert j <= cmix <= cstar, (k, a)
            row["cells"][a] = {
                "g": float((cstar - j) / j),
                "g_mix": float((cmix - j) / j),
                "g_mix_exact": str((cmix - j) / j),
            }
        g1 = F(row["cells"]["1"]["g_mix_exact"])
        row["mix_excess"] = {a: float(F(row["cells"][a]["g_mix_exact"]) - g1) for a in LEVELS}
        results.append(row)
    n_fail = sum(r["status"] == "failed" for r in a1.read_jsonl(screen_path))
    decision = (
        "RISK SEPARATION AT PROGRAMME LEVELS"
        if any(v >= float(EFFECT) for r in results for v in r["mix_excess"].values())
        else "CONFINED TO LOOSE ALPHA"
    )
    g_all = {}
    for r in screen.values():
        g_all.setdefault(fam_key(r["params"]), {})[r["params"]["alpha"]] = float(gap(r))
    summary = {
        "protocol": "protocols/A2-binding-alpha-screen.md",
        "screen_cells_completed": len(screen),
        "screen_cells_failed": n_fail,
        "survivors": surv,
        "mixture_results": results,
        "decision": decision,
        "screen_g_by_family": g_all,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(decision, json.dumps(surv), json.dumps([r["mix_excess"] for r in results]))


if __name__ == "__main__":
    main()
