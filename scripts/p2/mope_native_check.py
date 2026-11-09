"""Native-endpoint check: MopeCS(endpoint='exact_grid') vs author wealth_lb_2d (and quad port).

    source scripts/p2/env.sh; $PY scripts/p2/mope_native_check.py --out docs/p2/_mope_native.json
Streams: full-feedback (w = 1, wmax = 2) and IPW (wmax = 20, three designs), iid.
"""

# ruff: noqa: C408
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/p2_benchmark"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota/competitors"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))
import certificate_stops as cs
import mope_parity as mp


def run_cs(w, r, alpha, wmax, endpoint):
    m = cs.MopeCS(alpha, wmax, endpoint)
    lo, hi = [], []
    t0 = time.perf_counter()
    for wi, ri in zip(w, r, strict=True):
        m.update(wi, ri)
        lo.append(m.v_lo)
        hi.append(m.v_hi)
    return np.array(lo), np.array(hi), time.perf_counter() - t0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300, help="streams per regime")
    ap.add_argument("--T", type=int, default=300)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    ob = mp.load_author()
    rng = np.random.default_rng(20261109)
    regimes = {}
    for reg in ("full_feedback", "ipw"):
        wmax = 2.0 if reg == "full_feedback" else 20.0
        rows = []
        for i in range(a.n):
            p = float(rng.choice([0.35, 0.5, 0.65]))
            if reg == "full_feedback":
                w = np.ones(a.T)
            else:
                vals, probs = [(np.array([0.0, 5.0]), [0.8, 0.2]),
                               (np.array([0.0, 20.0]), [0.95, 0.05]),
                               (np.array([0.5, 2.0]), [2 / 3, 1 / 3])][i % 3]  # fmt: skip
                w = rng.choice(vals, size=a.T, p=probs)
            r = (rng.random(a.T) < p).astype(float)
            t0 = time.perf_counter()
            la, ua = ob.wealth_lb_2d(list(zip(w, r, strict=True)), 0.0, wmax, a.alpha)
            t_auth = time.perf_counter() - t0
            la, ua = np.array(la), np.array(ua)
            ln, un, t_nat = run_cs(w, r, a.alpha, wmax, "exact_grid")
            lq, uq, t_q = run_cs(w, r, a.alpha, wmax, "quad")

            def miss(lo, hi, p=p):
                return bool(np.any((lo > p) | (hi < p)))

            rows.append(dict(
                p=p, w_nat=float(un[-1] - ln[-1]), w_auth=float(ua[-1] - la[-1]),
                w_quad=float(uq[-1] - lq[-1]),
                final_end_diff=float(max(abs(ln[-1] - la[-1]), abs(un[-1] - ua[-1]))), max_end_diff=float(max(np.abs(ln - la).max(), np.abs(un - ua).max())),
                miss_auth=miss(la, ua), miss_nat=miss(ln, un), miss_quad=miss(lq, uq),
                t_auth=t_auth, t_nat=t_nat, t_quad=t_q))  # fmt: skip
        d = {k: np.array([r[k] for r in rows]) for k in rows[0]}
        ok = d["w_auth"] > 1e-9
        regimes[reg] = dict(
            streams=a.n, T=a.T,
            median_width_ratio_native_over_author=float(np.median(d["w_nat"][ok] / d["w_auth"][ok])),
            median_width_ratio_quad_over_author=float(np.median(d["w_quad"][ok] / d["w_auth"][ok])),
            max_endpoint_abs_diff_native_vs_author=float(d["max_end_diff"].max()),
            median_final_endpoint_abs_diff=float(np.median(d["final_end_diff"])),
            p90_final_endpoint_abs_diff=float(np.quantile(d["final_end_diff"], 0.9)),
            frac_streams_endpoints_identical=float(np.mean(d["max_end_diff"] < 1e-9)),
            miscoverage_author=int(d["miss_auth"].sum()), miscoverage_native=int(d["miss_nat"].sum()),
            miscoverage_quad=int(d["miss_quad"].sum()),
            sec_per_stream=dict(author=float(d["t_auth"].mean()), native=float(d["t_nat"].mean()),
                                quad=float(d["t_quad"].mean())))  # fmt: skip
        print(reg, json.dumps(regimes[reg], indent=1))
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(json.dumps(regimes, indent=1))


if __name__ == "__main__":
    main()
