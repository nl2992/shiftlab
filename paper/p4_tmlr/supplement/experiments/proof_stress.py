"""Numerical stress tests for the two RB-DP claims in docs/paper4_continuation/rbdp/PROOFS.md.

S1  Breakpoints: on a w grid of step 1/(6 * 2**B) (so most grid points are NOT dyadic), every
    stored value row V(t, beta, n, .) must be linear across each grid point that is not a multiple
    of 2**-n. Reports the largest second difference off the dyadic lattice.
S2  Refinement: the root value on the lattice d * 2**B must not change under 3x and 5x refinement;
    a grid that is not a multiple of 2**B is run as a control.
S3  Reduction: lattice-mode L and U against the exact sequence-form reference (gamma_cell) on
    fresh random cells drawn to favour a positive premium (anti-persistent, asymmetric).

Usage: uv run --no-sync python scripts/paper4_continuation/rbdp/proof_stress.py OUT.json
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from fractions import Fraction as F
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/paper4_continuation/theory_C"))

from gamma_lib import gamma_cell  # noqa: E402

from shiftlab.paper4 import risk_budget_dp_fast as fast  # noqa: E402

SEED = 20261114
ALPHAS = [F(1, 10), F(1, 7), F(3, 20), F(1, 4), F(1, 20)]


def draw(rng: random.Random, anti: bool, t_max: int, b_max: int) -> dict:
    lo, hi = (11, 19) if anti else (1, 19)
    return {
        "T": rng.randint(4, t_max),
        "B": rng.randint(1, b_max),
        "t01": F(rng.randint(lo, hi), 20),
        "t10": F(rng.randint(lo, hi), 20),
        "e0": F(rng.randint(1, 9), 20),
        "e1": F(rng.randint(11, 19), 20),
        "prior": rng.choice([F(0), F(1, 3), F(1, 2)]),
        "c": rng.choice([F(0), F(0), F(1, 100)]),
        "k": rng.choice([F(0), F(0), F(1, 20)]),
        "alpha": rng.choice(ALPHAS),
    }


def cfg(cell: dict, mode: str, **kw) -> fast.RBDPConfig:
    return fast.RBDPConfig(
        T=cell["T"],
        B=min(cell["B"], cell["T"]),
        t01=float(cell["t01"]),
        t10=float(cell["t10"]),
        e0=float(cell["e0"]),
        e1=float(cell["e1"]),
        prior1=float(cell["prior"]),
        c=float(cell["c"]),
        k=float(cell["k"]),
        alpha=float(cell["alpha"]),
        mode=mode,
        n_beta=201,
        **kw,
    )


def root_on_grid(cell: dict, mode: str, n_cells: int) -> float:
    """Upper-DP root value on the uniform w grid with n_cells cells (alpha must be on it)."""
    k = F(n_cells) * cell["alpha"]
    assert k.denominator == 1, "alpha not on grid"
    config = cfg(cell, mode, w_step_div=int(k))
    solver = fast._Solver(config)
    assert solver.N == n_cells
    solver._build_post()
    tab = solver._run_dp(lower=False, keep=False)
    lo, hi = solver.root_indices()
    assert lo == hi
    return solver.root_value(tab, lo)


def s1_breakpoints(cell: dict, mode: str) -> dict:
    b = min(cell["B"], cell["T"])
    n_cells = 6 * 2**b
    # w_step_div is chosen so that round(K / alpha) == n_cells; alpha itself may be off-grid.
    config = cfg(cell, mode, w_step_div=1)
    object.__setattr__(config, "w_step_div", n_cells * float(cell["alpha"]))
    solver = fast._Solver(config)
    assert solver.N == n_cells, (solver.N, n_cells)
    solver._build_post()
    solver._run_dp(lower=False, keep=True)
    worst_off, kinks_on, rows = 0.0, 0, 0
    idx = np.arange(1, n_cells)
    for t in range(1, cell["T"] + 1):
        for n in range(b + 1):
            v = solver.Vup[t][n]
            d2 = v[:, :-2] - 2.0 * v[:, 1:-1] + v[:, 2:]
            on = (idx * 2**n) % n_cells == 0
            scale = 1.0 + np.abs(v).max()
            if (~on).any():
                worst_off = max(worst_off, float(np.abs(d2[:, ~on]).max() / scale))
            kinks_on += int((np.abs(d2[:, on]) > 1e-9 * scale).sum())
            rows += v.shape[0]
    return {"worst_off_lattice_d2": worst_off, "kinks_on_lattice": kinks_on, "rows": rows}


def main(out_path: str) -> None:
    rng = random.Random(SEED)
    out: dict = {
        "seed": SEED,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "solver_sha256": hashlib.sha256(Path(fast.__file__).read_bytes()).hexdigest(),
        "s1": [],
        "s2": [],
        "s3": [],
    }

    for i in range(30):
        cell = draw(rng, anti=i % 2 == 0, t_max=12, b_max=4)
        for mode in ("causal", "iid"):
            rec = {"cell": {k: str(v) for k, v in cell.items()}, "mode": mode}
            rec.update(s1_breakpoints(cell, mode))
            out["s1"].append(rec)
    print("S1 done", flush=True)

    for i in range(20):
        cell = draw(rng, anti=i % 2 == 0, t_max=10, b_max=4)
        b = min(cell["B"], cell["T"])
        base = cell["alpha"].denominator * 2**b
        for mode in ("causal", "iid"):
            vals = {m: root_on_grid(cell, mode, m * base) for m in (1, 3, 5)}
            ctrl_cells = cell["alpha"].denominator * 3  # contains alpha; not a multiple of 2**b for b >= 1
            ctrl = root_on_grid(cell, mode, ctrl_cells)
            out["s2"].append(
                {
                    "cell": {k: str(v) for k, v in cell.items()},
                    "mode": mode,
                    "lattice_cells": base,
                    "root_x1": vals[1],
                    "dev_x3": vals[3] - vals[1],
                    "dev_x5": vals[5] - vals[1],
                    "control_cells": ctrl_cells,
                    "control_minus_lattice": ctrl - vals[1],
                }
            )
    print("S2 done", flush=True)

    for _ in range(40):
        cell = draw(rng, anti=True, t_max=7, b_max=3)
        t0 = time.time()
        ref = gamma_cell(
            cell["T"], cell["B"], 1, cell["t01"], cell["t10"], cell["e0"], cell["e1"],
            cell["prior"], cell["c"], cell["k"], cell["alpha"],
        )  # fmt: skip
        rec = {"cell": {k: str(v) for k, v in cell.items()}, "ref_s": time.time() - t0}
        for mode, key in (("causal", "causal"), ("iid", "IID")):
            res = fast.solve(cfg(cell, mode, lattice_exact=True))
            lo, hi = float(F(ref["L_" + key])), float(F(ref["U_" + key]))
            rec[mode] = {
                "ref_lo": lo,
                "ref_hi": hi,
                "L": res["L"],
                "U": res["U"],
                "U_minus_ref_hi": res["U"] - hi,
                "L_minus_ref_lo": res["L"] - lo,
                "risk_causal": res["risk_causal"],
                "risk_iid": res["risk_iid"],
            }
        rec["gamma_ref"] = rec["causal"]["ref_hi"] - rec["iid"]["ref_hi"]
        out["s3"].append(rec)
    print("S3 done", flush=True)

    Path(out_path).write_text(json.dumps(out, indent=1))
    s1 = out["s1"]
    print("S1 cells", len(s1), "max off-lattice d2", max(r["worst_off_lattice_d2"] for r in s1),
          "kinks on lattice", sum(r["kinks_on_lattice"] for r in s1))  # fmt: skip
    s2 = out["s2"]
    print("S2 max |dev x3|", max(abs(r["dev_x3"]) for r in s2), "max |dev x5|", max(abs(r["dev_x5"]) for r in s2),
          "control: min", min(r["control_minus_lattice"] for r in s2),
          "max", max(r["control_minus_lattice"] for r in s2),
          "n control>1e-9", sum(r["control_minus_lattice"] > 1e-9 for r in s2))  # fmt: skip
    s3 = out["s3"]
    for mode in ("causal", "iid"):
        print("S3", mode, "max |U-ref|", max(abs(r[mode]["U_minus_ref_hi"]) for r in s3),
              "max |L-ref|", max(abs(r[mode]["L_minus_ref_lo"]) for r in s3))  # fmt: skip
    print("S3 cells with Gamma>1e-9:", sum(r["gamma_ref"] > 1e-9 for r in s3), "of", len(s3))


if __name__ == "__main__":
    main(sys.argv[1])
