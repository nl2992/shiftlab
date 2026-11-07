"""Behavioural comparison of the local Choe-Ramdas stand-in with the authors' e-process (W3/P2).

The local ``choe_ramdas_eb`` runs the Waudby-Smith-Ramdas predictable-plug-in EB CS on paired
differences; it is not the authors' construction, so numerical parity is undefined. This script
compares verdicts on FULL-FEEDBACK paired loss streams (no label budget):

* author: ``comparecast.eprocess_expm`` (comparecast 1.0.0) called as ``compare_forecasts`` does for
  a two-sided test: ``c = hi - lo = 2``, ``alpha_opt = alpha/2``; reject "mean <= 0" when the
  e-process reaches ``2/alpha``;
* local: ``PrPlEBCS(alpha)`` on ``W = (x + 1)/2``; reject when the lower bound exceeds 1/2.

``confseq`` (a compiled dependency that does not build here) is stubbed: the default
``eprocess_expm`` path uses comparecast's own gamma-exponential mixture, and the stub raises if
the one imported confseq function is ever called.

    uv run python scripts/p2_benchmark/choe_ramdas_behaviour.py --out docs/p2_benchmark/results/choe_ramdas_behaviour.json
"""

from __future__ import annotations

import argparse
import json
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota/competitors"))
sys.path.insert(0, str(ROOT / "scripts/promising_directions/sota"))


def load_author():
    def _unavailable(*a, **k):
        raise RuntimeError("confseq stub called: this comparecast path needs the real confseq")

    pkg = types.ModuleType("confseq")
    bnd = types.ModuleType("confseq.boundaries")
    for name in ("normal_log_mixture", "normal_mixture_bound", "poly_stitching_bound",
                 "gamma_exponential_mixture_bound"):  # fmt: skip
        setattr(bnd, name, _unavailable)
    pkg.boundaries = bnd
    sys.modules.setdefault("confseq", pkg)
    sys.modules.setdefault("confseq.boundaries", bnd)
    from comparecast.eprocess import eprocess_expm

    return eprocess_expm


REGIMES = {  # (P(challenger better | disagreement), sign persistence rho)
    "null_iid": (0.5, 0.0),
    "null_markov_r8": (0.5, 0.8),
    "alt_p55": (0.55, 0.0),
    "alt_p60": (0.60, 0.0),
    "alt_p70": (0.70, 0.0),
}


def stream(rng, p, rho, T, dis=0.25):
    on = rng.random(T) < dis
    sign = np.empty(T, dtype=bool)
    sign[0] = rng.random() < p
    for t in range(1, T):
        sign[t] = sign[t - 1] if (rho > 0 and rng.random() < rho) else (rng.random() < p)
    return np.where(on, np.where(sign, 1.0, -1.0), 0.0)  # x = l0 - l1 (challenger advantage)


def first(idx):
    return int(idx[0]) if len(idx) else -1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--streams", type=int, default=300)
    ap.add_argument("--T", type=int, default=2000)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args(argv)
    eprocess_expm = load_author()
    import certificate_stops as cs

    rng = np.random.default_rng(20261107)
    out = {"comparecast_version": "1.0.0", "alpha": a.alpha, "T": a.T, "regimes": {}}
    for reg, (p, rho) in REGIMES.items():
        ta, tl = [], []
        for _ in range(a.streams):
            x = stream(rng, p, rho, a.T)
            e = np.asarray(eprocess_expm(x, c=2.0, alpha_opt=a.alpha / 2))
            ta.append(first(np.flatnonzero(e >= 2.0 / a.alpha)))
            m = cs.PrPlEBCS(a.alpha)
            hit = -1
            for t, xi in enumerate(x):
                m.update((xi + 1.0) / 2.0)
                if m.lo > 0.5:
                    hit = t
                    break
            tl.append(hit)
        ta, tl = np.array(ta), np.array(tl)
        both = (ta >= 0) & (tl >= 0)
        out["regimes"][reg] = {
            "reject_author": float((ta >= 0).mean()),
            "reject_local": float((tl >= 0).mean()),
            "verdict_agreement": float(((ta >= 0) == (tl >= 0)).mean()),
            "median_time_author": float(np.median(ta[ta >= 0])) if (ta >= 0).any() else None,
            "median_time_local": float(np.median(tl[tl >= 0])) if (tl >= 0).any() else None,
            "median_local_minus_author_when_both": float(np.median(tl[both] - ta[both]))
            if both.any()
            else None,
        }
        print(reg, out["regimes"][reg])
    if a.out:
        a.out.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
