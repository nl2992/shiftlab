"""Numerical parity of the local MOPE port against the author code (W3/P1, 2026-11-07).

Author code: ``vendor_sota/mope`` at n17s/mope@a4b8584b (Karampatziakis, Mineiro & Ramdas, ICML 2021).
``numba`` and ``cvxpy`` are stubbed: ``njit`` only compiles and ``cvxpy`` is used by ablations not
exercised here, so the author's own Python arithmetic runs unchanged.

Checks on identical (w, r) streams:
1. Bet parity: given the same sufficient statistics and endpoint, the author's ``solve_quad`` and
   the local ``MopeLowerCS._bet`` choose the same bet.
2. Interval parity: author ``wealth_lb_2d`` (exact log wealth on a 1000-point grid) vs local
   ``MopeCS`` (quadratic lower bound on log wealth). The local interval should contain the author's
   up to grid resolution; endpoint gaps and crossing times of fixed thresholds are reported.

    uv run python scripts/p2_benchmark/mope_parity.py --out docs/p2_benchmark/results/mope_parity.json
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor_sota/mope"
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota/competitors"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))


def load_author():
    numba = types.ModuleType("numba")
    numba.njit = lambda f=None, **k: f if f is not None else (lambda g: g)
    sys.modules.setdefault("numba", numba)
    sys.modules.setdefault("cvxpy", types.ModuleType("cvxpy"))
    sys.path.insert(0, str(VENDOR))
    import opebet  # author module

    return opebet


def streams(rng, n_streams, T):
    """(name, w, r) streams with E[w] = 1 and w <= wmax."""
    designs = {
        "ipw_q.2": (np.array([0.0, 5.0]), np.array([0.8, 0.2])),
        "ipw_q.05": (np.array([0.0, 20.0]), np.array([0.95, 0.05])),
        "mixed": (np.array([0.5, 2.0]), np.array([2 / 3, 1 / 3])),
    }
    out = []
    for i in range(n_streams):
        name = list(designs)[i % 3]
        vals, probs = designs[name]
        p = (0.35, 0.5, 0.65)[(i // 3) % 3]
        w = rng.choice(vals, size=T, p=probs)
        r = (rng.random(T) < p).astype(float)
        out.append((f"{name}|p{p}", w, r))
    return out


def author_bet(opebet, d, v, wmax):
    cp = np.array([[0.0, -1.0, wmax - 1.0], [1.0, -1.0, -1.0]])
    dp = np.array([0.0, -0.5, -0.5])
    cands = np.zeros((6, 2))
    cands[3, :] = [0.5, 0]
    cands[4, :] = [0, 0.5]
    cands[5, :] = [-0.5 / (wmax - 1), 0.0]
    prob = opebet.Problem(A=np.zeros((2, 2)), b=np.zeros(2), c=cp, d=dp, e=np.zeros(3),
                          f=np.zeros((6, 2)), g=np.zeros((2, 3)), h=np.zeros(6), x=np.zeros(2),
                          wmax=wmax, cands=cands)  # fmt: skip
    return np.array(opebet.solve_quad(prob, d, v))


def bet_parity(opebet, w, r, wmax, alpha):
    import certificate_stops as cs

    local = cs.MopeLowerCS(alpha, wmax)
    d = defaultdict(float)
    worst_pd, mism_pd, mism_singular, n = 0.0, 0, 0, 0
    A, b = np.zeros((2, 2)), np.zeros(2)
    for wi, ri in zip(w, r, strict=True):
        local.update(wi, ri)
        d = opebet.update_stats(d, wi, ri, 0)
        a = author_bet(opebet, d, local.v, wmax)
        diff = float(np.abs(a - np.array([local.lam1, local.lam2])).max())
        opebet.fill_quad(d, local.v, A, b)
        pd = A[0, 0] > 0 and A[0, 0] * A[1, 1] - A[0, 1] * A[1, 0] > 0
        n += 1
        if pd:
            worst_pd = max(worst_pd, diff)
            mism_pd += diff > 1e-9
        else:
            mism_singular += diff > 1e-9
    return {"steps": n, "max_diff_when_pd": worst_pd, "mismatch_pd": mism_pd,
            "mismatch_singular": mism_singular}  # fmt: skip


def coverage(opebet, n, T, alpha, wmax):
    """Time-uniform miscoverage of the true V = p (w independent of r, E[w] = 1) for both CSs."""
    import certificate_stops as cs

    rng = np.random.default_rng(20261108)
    out = {}
    for name, w, r in streams(rng, n, T):
        p = float(name.split("|p")[1])
        lb_a, ub_a = opebet.wealth_lb_2d(list(zip(w, r, strict=True)), 0.0, wmax, alpha)
        m = cs.MopeCS(alpha, wmax)
        miss_l, wid_l = False, 0.0
        for wi, ri in zip(w, r, strict=True):
            m.update(wi, ri)
            miss_l |= not (m.v_lo <= p <= m.v_hi)
        wid_l = m.v_hi - m.v_lo
        miss_a = bool(np.any((np.array(lb_a) > p) | (np.array(ub_a) < p)))
        o = out.setdefault(name.split("|")[0], {"n": 0, "miss_author": 0, "miss_local": 0,
                                                 "width_author": [], "width_local": []})  # fmt: skip
        o["n"] += 1
        o["miss_author"] += miss_a
        o["miss_local"] += bool(miss_l)
        o["width_author"].append(ub_a[-1] - lb_a[-1])
        o["width_local"].append(wid_l)
    for o in out.values():
        o["width_author"] = float(np.median(o["width_author"]))
        o["width_local"] = float(np.median(o["width_local"]))
    return out


def first_cross(seq, thr, above=True):
    seq = np.asarray(seq)
    hit = np.flatnonzero(seq > thr if above else seq < thr)
    return int(hit[0]) if len(hit) else -1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", type=int, default=36)
    ap.add_argument("--T", type=int, default=1000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--wmax", type=float, default=20.0)
    ap.add_argument("--coverage-streams", type=int, default=0)
    ap.add_argument("--coverage-T", type=int, default=500)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    opebet = load_author()
    import certificate_stops as cs

    rng = np.random.default_rng(20261107)
    rows = []
    for name, w, r in streams(rng, a.streams, a.T):
        lb_a, ub_a = opebet.wealth_lb_2d(list(zip(w, r, strict=True)), 0.0, a.wmax, a.alpha)
        m = cs.MopeCS(a.alpha, a.wmax)
        lb_l, ub_l = [], []
        for wi, ri in zip(w, r, strict=True):
            m.update(wi, ri)
            lb_l.append(m.v_lo)
            ub_l.append(m.v_hi)
        lb_a, ub_a, lb_l, ub_l = map(np.array, (lb_a, ub_a, lb_l, ub_l))
        true_v = float(np.mean(w * r))
        thr_lo, thr_hi = 0.45, 0.55
        rows.append(
            {
                "stream": name,
                "bet": bet_parity(opebet, w, r, a.wmax, a.alpha),
                "local_lo_minus_author_lo_max": float((lb_l - lb_a).max()),
                "author_hi_minus_local_hi_max": float((ub_a - ub_l).max()),
                "width_ratio_final": float((ub_l[-1] - lb_l[-1]) / max(ub_a[-1] - lb_a[-1], 1e-12)),
                "author_final": [float(lb_a[-1]), float(ub_a[-1])],
                "local_final": [float(lb_l[-1]), float(ub_l[-1])],
                "cross_lo_author_local": [first_cross(lb_a, thr_lo), first_cross(lb_l, thr_lo)],
                "cross_hi_author_local": [
                    first_cross(ub_a, thr_hi, False),
                    first_cross(ub_l, thr_hi, False),
                ],
                "empirical_wr_mean": true_v,
            }
        )
        print(f"{name:14s} bet diff(pd) {rows[-1]['bet']['max_diff_when_pd']:.2e} "
              f"singular-mismatch {rows[-1]['bet']['mismatch_singular']}  "
              f"lo gap {rows[-1]['local_lo_minus_author_lo_max']:+.4f}  "
              f"width ratio {rows[-1]['width_ratio_final']:.3f}")  # fmt: skip
    grid = 1.0 / 999
    summary = {
        "author_commit": "a4b8584b622f3a8296932568c520c1bb3e1957f0",
        "streams": len(rows),
        "T": a.T,
        "alpha": a.alpha,
        "wmax": a.wmax,
        "bet_max_abs_diff_when_pd": max(r["bet"]["max_diff_when_pd"] for r in rows),
        "bet_mismatch_steps_pd": sum(r["bet"]["mismatch_pd"] for r in rows),
        "bet_mismatch_steps_singular": sum(r["bet"]["mismatch_singular"] for r in rows),
        "bet_steps": sum(r["bet"]["steps"] for r in rows),
        "containment_violation_max": max(
            max(r["local_lo_minus_author_lo_max"], r["author_hi_minus_local_hi_max"]) for r in rows
        ),
        "grid_resolution": grid,
        "width_ratio_final_median": float(np.median([r["width_ratio_final"] for r in rows])),
        "rows": rows,
    }
    if a.coverage_streams:
        summary["coverage"] = coverage(opebet, a.coverage_streams, a.coverage_T, a.alpha, a.wmax)
    print({k: v for k, v in summary.items() if k != "rows"})
    if a.out:
        a.out.write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
