"""Validation of the d = 2 RB-DP solver against the certified exact reference (gamma_cell).

Writes docs/paper4_continuation/rbdp/results/d2_validation_v1.json (refuses to overwrite).
Run:  uv run --no-sync python scripts/paper4_continuation/rbdp/d2_validation.py [--out PATH]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/paper4_continuation/theory_C"))

from gamma_lib import gamma_cell  # noqa: E402

from shiftlab.paper4.risk_budget_dp_d2 import RBDP2Config, solve  # noqa: E402

N_CELLS = 30
RESOLUTIONS = (20, 40, 80)


def random_cells(seed: int = 20260521) -> list[dict]:
    rng = random.Random(seed)
    cells = []
    for i in range(N_CELLS):
        anti = i % 2 == 0
        tr = (lambda: F(rng.randint(11, 19), 20)) if anti else (lambda: F(rng.randint(1, 10), 20))
        cells.append(
            dict(
                T=rng.randint(4, 7),
                B=rng.randint(1, 3),
                t01=tr(),
                t10=tr(),
                e0=F(rng.randint(1, 9), 20),
                e1=F(rng.randint(11, 19), 20),
                prior=rng.choice([F(0), F(1, 3), F(1, 2)]),
                c=rng.choice([F(0), F(1, 100)]),
                k=rng.choice([F(0), F(1, 20)]),
                alpha=rng.choice([F(1, 10), F(1, 5)]),
                anti_persistent=anti,
            )
        )
    return cells


def cfg_for(cell: dict, mode: str, n_w: int) -> RBDP2Config:
    return RBDP2Config(
        T=cell["T"],
        B=cell["B"],
        t01=float(cell["t01"]),
        t10=float(cell["t10"]),
        e0=float(cell["e0"]),
        e1=float(cell["e1"]),
        prior1=float(cell["prior"]),
        c=float(cell["c"]),
        k=float(cell["k"]),
        alpha=float(cell["alpha"]),
        n_w_override=n_w,
        mode=mode,
    )


def reference(cell: dict) -> dict:
    kw = {k: v for k, v in cell.items() if k != "anti_persistent"}
    t0 = time.perf_counter()
    g = gamma_cell(d=2, **kw)
    return {
        "L_IID": float(F(g["L_IID"])),
        "U_IID": float(F(g["U_IID"])),
        "L_causal": float(F(g["L_causal"])),
        "U_causal": float(F(g["U_causal"])),
        "Gamma_lo": g["Gamma_lo_f"],
        "Gamma_hi": g["Gamma_hi_f"],
        "Gamma_positive_certified": bool(g["Gamma_positive_certified"]),
        "gamma_time": time.perf_counter() - t0,
    }


def run_cell(cell: dict, ref: dict, n_ws: tuple[int, ...]) -> list[dict]:
    rows = []
    for mode in ("iid", "causal"):
        exact = ref["U_IID"] if mode == "iid" else ref["U_causal"]
        low = ref["L_IID"] if mode == "iid" else ref["L_causal"]
        by_n = {}
        for n_w in n_ws:
            r = solve(cfg_for(cell, mode, n_w))
            by_n[n_w] = {
                "U": r["U"],
                "dp_value": r["dp_value"],
                "gap": r["U"] - exact,
                "risk_causal": r["risk_causal"],
                "risk_iid": r["risk_iid"],
                "C0": r["C0"],
                "time": r["time_total"],
                "n_beta_grid": r["n_beta_grid"],
                "belief_grid": r["belief_grid"],
            }
        rows.append({"mode": mode, "exact_upper": exact, "exact_lower": low, "by_N": by_n})
    return rows


def lattice_scan(cell: dict, ref: dict) -> dict:
    """Gap versus N over many N for one cell (alpha must land on the grid)."""
    alpha = cell["alpha"]
    d_alpha = alpha.denominator
    ns = sorted({d_alpha * m for m in range(1, 13) if d_alpha * m <= 120} | {d_alpha * 2**cell["B"] * m for m in (1, 2)})
    out = {"cell": {k: str(v) for k, v in cell.items()}, "d_alpha": d_alpha, "B": cell["B"], "scan": {}}
    for mode in ("iid", "causal"):
        exact = ref["U_IID"] if mode == "iid" else ref["U_causal"]
        res = {}
        for n_w in ns:
            if n_w > 120:
                continue
            r = solve(cfg_for(cell, mode, n_w))
            res[n_w] = {
                "gap": r["U"] - exact,
                "risk_own_mode": r["risk_iid"] if mode == "iid" else r["risk_causal"],
                "multiple_of_2B_dalpha": n_w % (2 ** cell["B"] * d_alpha) == 0,
                "multiple_of_3_2B": n_w % (3 * 2 ** cell["B"]) == 0,
                "multiple_of_3_dalpha": n_w % (3 * d_alpha) == 0,
            }
        out["scan"][mode] = res
    return out


def hunt_cells(seed: int = 7, n: int = 100) -> list[dict]:
    """Extra random cells (T 6..7, B 2..3, wider transitions) used only to find hard cells."""
    rng = random.Random(seed)
    cells = []
    for _ in range(n):
        anti = rng.random() < 0.6
        tr = (lambda: F(rng.randint(11, 19), 20)) if anti else (lambda: F(rng.randint(1, 19), 20))
        cells.append(
            dict(
                T=rng.choice([6, 7]),
                B=rng.choice([2, 3]),
                t01=tr(),
                t10=tr(),
                e0=F(rng.randint(1, 9), 20),
                e1=F(rng.randint(11, 19), 20),
                prior=rng.choice([F(0), F(1, 3), F(1, 2)]),
                c=rng.choice([F(0), F(1, 100)]),
                k=rng.choice([F(0), F(1, 20)]),
                alpha=rng.choice([F(1, 10), F(1, 5)]),
                anti_persistent=anti,
            )
        )
    return cells


def coarse_gap(cell: dict, ref: dict) -> float:
    """Largest gap over both modes at N = d_alpha and 2 d_alpha (coarse grids expose problems)."""
    d_alpha = cell["alpha"].denominator
    worst = 0.0
    for mode in ("iid", "causal"):
        exact = ref["U_IID"] if mode == "iid" else ref["U_causal"]
        for n_w in (d_alpha, 2 * d_alpha):
            worst = max(worst, solve(cfg_for(cell, mode, n_w))["U"] - exact)
    return worst


def scaling() -> list[dict]:
    rows = []
    for T, n_w, n_beta in ((12, 20, 101), (12, 40, 401), (20, 20, 101), (20, 40, 401), (32, 20, 101), (32, 40, 401)):
        cfg = RBDP2Config(
            T=T,
            B=3,
            t01=0.75,
            t10=0.75,
            e0=0.1,
            e1=0.9,
            prior1=0.5,
            c=0.0,
            k=0.0,
            alpha=0.1,
            n_w_override=n_w,
            mode="causal",
            belief_grid="uniform",
            n_beta=n_beta,
        )
        r = solve(cfg)
        rows.append({"T": T, "B": 3, "N": n_w, "n_beta": n_beta, **{k: r[k] for k in ("U", "dp_value", "C0", "risk_causal", "risk_iid", "belief_grid", "n_beta_grid", "n_hull2", "n_eval_nodes", "time_total")}})
        print("scaling", rows[-1], flush=True)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "docs/paper4_continuation/rbdp/results/d2_validation_v1.json"))
    ap.add_argument("--skip-scaling", action="store_true")
    ap.add_argument("--max-cells", type=int, default=N_CELLS)
    args = ap.parse_args()
    if os.path.exists(args.out):
        print(f"refusing to overwrite {args.out}", file=sys.stderr)
        sys.exit(2)
    cells = random_cells()[: args.max_cells]
    records = []
    refs = []
    for i, cell in enumerate(cells):
        ref = reference(cell)
        refs.append(ref)
        n_ws = tuple(n for n in RESOLUTIONS if (cell["alpha"] * n).denominator == 1)
        rows = run_cell(cell, ref, n_ws)
        records.append(
            {
                "cell_id": i,
                "cell": {k: str(v) if isinstance(v, F) else v for k, v in cell.items()},
                "reference": ref,
                "premium_positive": ref["Gamma_positive_certified"],
                "results": rows,
            }
        )
        worst = max(max(r["by_N"][n]["gap"] for n in r["by_N"]) for r in rows)
        print(i, cell["T"], cell["B"], "gamma>0", ref["Gamma_positive_certified"], "max gap", worst, flush=True)
    pool = [(f"main{i}", c, r) for i, (c, r) in enumerate(zip(cells, refs, strict=True))]
    for j, cell in enumerate(hunt_cells()):
        pool.append((f"hunt{j}", cell, reference(cell)))
    scored = sorted(((coarse_gap(c, r), name, c, r) for name, c, r in pool), key=lambda x: -x[0])
    print("hardest cells (coarse-grid gap):", [(n, round(g, 6)) for g, n, _, _ in scored[:8]], flush=True)
    lattice = [
        lattice_scan(c, r) | {"cell_id": name, "coarse_gap": g} for g, name, c, r in scored[:5]
    ]
    n_bad = sum(1 for g, *_ in scored if g > 1e-9)
    dyadic = {}
    for g, name, c, r in scored:
        if g <= 1e-9:
            continue
        n_dy = c["alpha"].denominator * 2 ** c["B"]
        dyadic[name] = {"N": n_dy, "B": c["B"]}
        for mode in ("iid", "causal"):
            exact = r["U_IID"] if mode == "iid" else r["U_causal"]
            dyadic[name][mode + "_gap"] = solve(cfg_for(c, mode, n_dy))["U"] - exact
    print("gap at N = d_alpha * 2^B for every cell with a coarse gap:", dyadic, flush=True)
    payload = {
        "seed": 20260521,
        "records": records,
        "lattice": lattice,
        "hunt": {"pool_size": len(pool), "cells_with_coarse_gap_gt_1e-9": n_bad,
                 "coarse_gaps": {name: g for g, name, _, _ in scored},
                 "gap_at_dyadic_lattice_N_eq_dalpha_2B": dyadic},
        "scaling": [] if args.skip_scaling else scaling(),
    }
    with open(args.out, "w") as fh:
        json.dump(payload, fh, indent=1, default=str)
    print("wrote", args.out)


if __name__ == "__main__":
    main()
