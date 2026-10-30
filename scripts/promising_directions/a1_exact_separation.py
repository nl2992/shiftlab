"""A1: exact joint planner vs best fixed query calendar (registered protocol A1-exact-separation).

Runs the registered grid; see docs/promising_directions/protocols/A1-exact-separation.md.
Development kill test, not confirmatory evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import random
import subprocess
import sys
import time
from datetime import UTC, datetime
from fractions import Fraction as F
from itertools import combinations, product
from pathlib import Path

SOLVER_COMMIT_PREFIX = "2bd2e8e"
SOLVER_FILES = (
    "src/shiftlab/dive/causal_switching_game.py",
    "scripts/decompose_switching_calendar_gap.py",
)
DEFAULT_SOLVER_ROOT = "C:/Users/nigel/OneDrive/桌面/ICML/shiftlab-risk-approx-2026-10-29"
DEFAULT_OUT = Path(__file__).resolve().parents[2] / "docs/promising_directions/results/a1"
TOL = 1e-12
MAX_NODES = 200_000

_SOLVER: dict = {}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def verify_solver(root: Path) -> dict:
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    if not head.startswith(SOLVER_COMMIT_PREFIX):
        raise SystemExit(f"solver root at {head!r}, expected {SOLVER_COMMIT_PREFIX}*")
    for rel in SOLVER_FILES:
        if git(root, "diff", "--quiet", "HEAD", "--", rel).returncode != 0:
            raise SystemExit(f"{rel} modified relative to HEAD")
    return {
        "solver_commit": head,
        "solver_file_sha256": {rel: sha256_file(root / rel) for rel in SOLVER_FILES},
    }


def load_solver(root: str) -> None:
    root_path = Path(root)
    for sub in ("src", "scripts"):
        p = str(root_path / sub)
        if p not in sys.path:
            sys.path.insert(0, p)
    from decompose_switching_calendar_gap import CalendarOpportunityGame

    from shiftlab.dive.causal_switching_game import GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel
    from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame

    _SOLVER.update(
        Calendar=CalendarOpportunityGame,
        GameConfig=GameConfig,
        RegimeModel=RegimeModel,
        Joint=FirstPromotionDecomposedGame,
    )


def init_worker(root: str) -> None:
    load_solver(root)


def make(p: dict):
    cfg = _SOLVER["GameConfig"](
        horizon=p["T"],
        budget=p["B"],
        delay=p["d"],
        alpha=F(p["alpha"]),
        query_cost=F(p["cq"]),
        switch_cost=F(p["cs"]),
        max_nodes=MAX_NODES,
    )
    model = _SOLVER["RegimeModel"](
        transition01=F(p["trans"]),
        transition10=F(p["trans"]),
        emission0=F(p["e0"]),
        emission1=F(p["e1"]),
        prior1=F(p["prior1"]),
    )
    return cfg, model


def calendars(T: int, B: int, d: int, all_slots: bool = False):
    # The T8_B4 source runner uses eligible slots 1..T-d: queries released after the horizon
    # carry no information and only cost, so they are dominated. all_slots=True uses 1..T.
    slots = range(1, (T if all_slots else T - d) + 1)
    return [c for k in range(B + 1) for c in combinations(slots, k)]


def solve_cell(p: dict, all_slots: bool = False) -> dict:
    cfg, model = make(p)
    t0 = time.perf_counter()
    jrep = _SOLVER["Joint"](cfg, model).solve()[0]
    j = F(jrep["calibrated_total_cost"])
    rows = []
    for cal in calendars(p["T"], p["B"], p["d"], all_slots):
        rep = _SOLVER["Calendar"](cfg, model, cal).solve()[0]
        assert F(rep["calibrated_risk_bound"]) <= cfg.alpha
        rows.append((F(rep["calibrated_total_cost"]), cal, rep["nodes"]))
    c_star, best, _ = min(rows, key=lambda r: (r[0], len(r[1]), r[1]))
    abs_gap = c_star - j
    return {
        "params": p,
        "J": str(j),
        "J_float": float(j),
        "C_star": str(c_star),
        "C_star_float": float(c_star),
        "best_calendar": list(best),
        "abs_gap": str(abs_gap),
        "abs_gap_float": float(abs_gap),
        "rel_gap": str(abs_gap / j),
        "rel_gap_float": float(abs_gap / j),
        "j_le_cstar_within_tol": bool(float(j) - float(c_star) <= TOL),
        "n_calendars": len(rows),
        "joint_nodes": jrep["nodes"],
        "solve_seconds": time.perf_counter() - t0,
    }


def work(task: tuple[dict, float | None]) -> dict:
    p, deadline = task
    if deadline is not None and time.time() > deadline:
        return {"params": p, "status": "not_run_time_cap"}
    try:
        out = solve_cell(p)
        out["status"] = "completed"
        return out
    except Exception as exc:  # noqa: BLE001 - record every failure
        return {"params": p, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}


def key_of(p: dict) -> str:
    return json.dumps(p, sort_keys=True)


def grid(d: int) -> list[dict]:
    cells = []
    # Slice-major order: all T for a slice are consecutive, so a time cap leaves whole slices.
    for B, trans, (e0, e1), alpha, cs in product(
        (2, 3, 4),
        ("1/20", "1/10"),
        (("1/10", "9/10"), ("1/50", "49/50")),
        ("1/20", "1/10"),
        ("1/10", "1/2"),
    ):
        for T in (6, 7, 8):
            cells.append(
                {
                    "T": T, "B": B, "d": d, "trans": trans, "e0": e0, "e1": e1,
                    "alpha": alpha, "cq": "1/100", "cs": cs, "prior1": "1/2",
                }
            )  # fmt: skip
    return cells


def adversarial_instances() -> list[dict]:
    rng = random.Random(20261030)
    trans = [F(k, 20) for k in range(1, 10)]
    acc = [F(11, 20), F(3, 5), F(7, 10), F(4, 5), F(9, 10), F(19, 20), F(49, 50)]
    out = []
    for i in range(200):
        a = rng.choice(acc)
        out.append(
            {
                "T": 6, "B": 3, "d": 2, "trans": str(rng.choice(trans)),
                "e0": str(1 - a), "e1": str(a),
                "alpha": str(rng.choice([F(1, 20), F(1, 10)])),
                "cq": str(rng.choice([F(1, 100), F(1, 20), F(1, 10)])),
                "cs": str(rng.choice([F(1, 20), F(1, 10), F(1, 4), F(1, 2), F(1)])),
                "prior1": "1/2", "idx": i,
            }
        )  # fmt: skip
    return out


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def run_cells(cells, jsonl: Path, workers: int, root: str, deadline: float | None) -> None:
    done = {key_of(r["params"]) for r in read_jsonl(jsonl) if r.get("status") == "completed"}
    todo = [(c, deadline) for c in cells if key_of(c) not in done]
    print(f"{len(cells) - len(todo)} done, {len(todo)} to run -> {jsonl.name}", flush=True)
    if not todo:
        return
    with (
        mp.Pool(workers, initializer=init_worker, initargs=(root,)) as pool,
        jsonl.open("a", encoding="utf-8") as fh,
    ):
        for res in pool.imap(work, todo, chunksize=1):
            if res["status"] == "not_run_time_cap":
                continue
            fh.write(json.dumps(res) + "\n")
            fh.flush()
            print(
                res["status"],
                res["params"],
                res.get("rel_gap_float"),
                f"{res.get('solve_seconds', 0):.1f}s",
                flush=True,
            )


def monotone_analysis(rows: list[dict]) -> list[dict]:
    slices: dict[str, dict[int, float]] = {}
    for r in rows:
        p = r["params"]
        k = json.dumps({x: p[x] for x in p if x != "T"}, sort_keys=True)
        slices.setdefault(k, {})[p["T"]] = r["rel_gap_float"]
    out = []
    for k, by_t in sorted(slices.items()):
        if set(by_t) != {6, 7, 8}:
            out.append({"slice": json.loads(k), "complete": False, "g_by_T": by_t})
            continue
        g6, g7, g8 = by_t[6], by_t[7], by_t[8]
        mono = g6 <= g7 + TOL and g7 <= g8 + TOL
        out.append(
            {
                "slice": json.loads(k),
                "complete": True,
                "g_by_T": by_t,
                "monotone_nondecreasing": mono,
                "total_increase": g8 - g6,
                "monotone_increase_gt_0.01": bool(mono and g8 - g6 > 0.01),
                "monotone_increase_gt_0.02": bool(mono and g8 - g6 > 0.02),
            }
        )
    return out


def decide(rows: list[dict]) -> dict:
    if not rows:
        return {"decision": "NO_DATA"}
    mx = max(rows, key=lambda r: r["rel_gap_float"])
    mono = monotone_analysis(rows)
    comp = [m for m in mono if m["complete"]]
    any10 = any(r["rel_gap_float"] >= 0.10 for r in rows)
    mono02 = any(m["monotone_increase_gt_0.02"] for m in comp)
    mono01 = any(m["monotone_increase_gt_0.01"] for m in comp)
    if any10 or mono02:
        dec = "CONTINUE"
    elif mx["rel_gap_float"] < 0.05 and not mono01:
        dec = "KILL"
    else:
        dec = "INCONCLUSIVE"
    return {
        "decision": dec,
        "n_cells": len(rows),
        "max_rel_gap": mx["rel_gap_float"],
        "max_rel_gap_exact": mx["rel_gap"],
        "max_rel_gap_params": mx["params"],
        "n_cells_ge_0.10": sum(r["rel_gap_float"] >= 0.10 for r in rows),
        "n_cells_ge_0.05": sum(r["rel_gap_float"] >= 0.05 for r in rows),
        "n_cells_positive_gap": sum(F(r["abs_gap"]) > 0 for r in rows),
        "j_le_cstar_violations": sum(not r["j_le_cstar_within_tol"] for r in rows),
        "n_complete_T_slices": len(comp),
        "n_slices_monotone_increase_gt_0.01": sum(m["monotone_increase_gt_0.01"] for m in comp),
        "n_slices_monotone_increase_gt_0.02": sum(m["monotone_increase_gt_0.02"] for m in comp),
        "monotone_by_slice": mono,
    }


def summarize(out: Path, provenance: dict) -> dict:
    completed = {}
    for name in ("primary", "secondary", "adversarial"):
        allrows = read_jsonl(out / f"{name}.jsonl")
        completed[name] = (
            [r for r in allrows if r.get("status") == "completed"],
            [r for r in allrows if r.get("status") == "failed"],
        )
    grid_rows = completed["primary"][0] + completed["secondary"][0]
    adv = completed["adversarial"][0]
    summary = {
        "protocol": "A1-exact-separation (registered 0d03912, sha256 35b0db11...)",
        "generated_utc": datetime.now(UTC).isoformat(),
        "provenance": provenance,
        "cells_completed": {
            "primary": f"{len(completed['primary'][0])}/144",
            "secondary": f"{len(completed['secondary'][0])}/144",
            "adversarial": f"{len(adv)}/200",
        },
        "cells_failed": {k: len(v[1]) for k, v in completed.items()},
        "decision_primary_only": decide(completed["primary"][0]),
        "decision_grid_primary_plus_secondary": decide(grid_rows),
        "adversarial": {
            "n": len(adv),
            "max_rel_gap": max((r["rel_gap_float"] for r in adv), default=None),
            "max_rel_gap_params": (
                max(adv, key=lambda r: r["rel_gap_float"])["params"] if adv else None
            ),
            "n_ge_0.10": sum(r["rel_gap_float"] >= 0.10 for r in adv),
            "n_ge_0.05": sum(r["rel_gap_float"] >= 0.05 for r in adv),
            "j_le_cstar_violations": sum(not r["j_le_cstar_within_tol"] for r in adv),
        },
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    insight = os.environ.get("LOOP_INSIGHT_PATH")
    if insight:
        d = summary["decision_grid_primary_plus_secondary"]
        Path(insight).write_text(
            f"A1 decision={d.get('decision')} cells={summary['cells_completed']} "
            f"max_rel_gap={d.get('max_rel_gap')} adversarial_max="
            f"{summary['adversarial']['max_rel_gap']}\n",
            encoding="utf-8",
        )
    return summary


def sanity(out: Path, provenance: dict) -> bool:
    base = {
        "T": 6, "B": 3, "d": 2, "trans": "1/10", "e0": "1/10", "e1": "9/10",
        "alpha": "1/10", "cq": "1/100", "cs": "1/10", "prior1": "1/2",
    }  # fmt: skip
    r6 = solve_cell(base)
    r6all = solve_cell(base, all_slots=True)
    r8 = solve_cell({**base, "T": 8, "B": 4})
    checks = [
        ("T6B3d2 J == 22083523/7812500", r6["J"] == "22083523/7812500", r6["J"]),
        ("T6B3d2 J <= C*", r6["j_le_cstar_within_tol"], r6["abs_gap"]),
        (
            "calendar slots 1..T equal 1..T-d (T6B3d2)",
            r6all["C_star"] == r6["C_star"],
            [r6all["C_star"], r6["C_star"]],
        ),
        (
            "T8B4 gap C*-J == 6744087/781250000",
            r8["abs_gap"] == "6744087/781250000",
            r8["abs_gap"],
        ),
        ("T8B4 J <= C*", r8["j_le_cstar_within_tol"], r8["abs_gap"]),
    ]
    ok = all(c[1] for c in checks)
    res = {
        "passed": ok,
        "checks": [{"name": n, "ok": o, "value": v} for n, o, v in checks],
        "cells": [r6, r6all, r8],
        "provenance": provenance,
    }
    (out / "sanity.json").write_text(json.dumps(res, indent=2, default=str) + "\n", "utf-8")
    for n, o, v in checks:
        print("PASS" if o else "FAIL", n, v, flush=True)
    return ok


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver-root", default=DEFAULT_SOLVER_ROOT)
    ap.add_argument(
        "--part", required=True, choices=["sanity", "primary", "secondary", "adversarial"]
    )
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--time-limit-seconds", type=float, default=None)
    ap.add_argument("--deadline-epoch", type=float, default=None)
    args = ap.parse_args()
    workers = min(args.workers, 2)
    root = Path(args.solver_root)
    provenance = verify_solver(root)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    load_solver(str(root))
    deadline = args.deadline_epoch
    if deadline is None and args.time_limit_seconds is not None:
        deadline = time.time() + args.time_limit_seconds
    if args.part == "sanity":
        sys.exit(0 if sanity(args.out_dir, provenance) else 1)
    if args.part == "primary":
        cells = grid(2)
    elif args.part == "secondary":
        cells = grid(1)
    else:
        cells = adversarial_instances()
    run_cells(cells, args.out_dir / f"{args.part}.jsonl", workers, str(root), deadline)
    s = summarize(args.out_dir, provenance)
    print(json.dumps({k: s[k] for k in ("cells_completed", "cells_failed")}), flush=True)


if __name__ == "__main__":
    main()
