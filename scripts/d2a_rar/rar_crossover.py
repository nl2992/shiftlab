"""RAR reproduction: mean +- s.e. tables and Full-RAR crossover-rho windows from rar_repro.json.

U(rho) = n_correct - rho * (N_r + Ca_frac N_a + Cb_frac N_b), affine in rho for cost-blind policies.
The window is the open interval of rho where Full RAR beats Binary, Always-Retrain and No-Response
simultaneously, computed on seed-mean (n_correct, cost units) and per seed.
Usage: python scripts/d2a_rar/rar_crossover.py [rar_repro.json] [out.json]
"""

import json
import sys

import numpy as np

CA, CB = 0.05, 0.2
POL = ["no_response", "always_retrain", "binary", "alert_only", "rollback_only", "full_rar"]
RHOS = ("1", "5", "100")


def cost_units(c):
    return c["retrain"] + CA * c["alert"] + CB * c["rollback"]


def window(recs_pol, rivals):
    """Return (lo, hi) of rho>0 where full_rar beats all rivals, or None. recs_pol: policy -> (a, k)."""
    a0, k0 = recs_pol["full_rar"]
    lo, hi = 0.0, np.inf
    for r in rivals:
        a1, k1 = recs_pol[r]
        # a0 - rho k0 > a1 - rho k1  <=>  rho (k1 - k0) > a1 - a0
        dk, da = k1 - k0, a1 - a0
        if dk > 0:
            lo = max(lo, da / dk)
        elif dk < 0:
            hi = min(hi, da / dk)
        elif da >= 0:
            return None
    return (lo, hi) if lo < hi else None


def main():
    f = sys.argv[1] if len(sys.argv) > 1 else "results/d2a_rar/rar_repro.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "results/d2a_rar/rar_crossover.json"
    with open(f) as fh:
        R = json.load(fh)
    streams = sorted({k.split("|")[0] for k in R if k != "_meta"})
    res = {}
    for s in streams:
        recs = [v for k, v in R.items() if k.startswith(s + "|")]
        n = len(recs)
        d = {"n_seeds": n, "U": {}, "counts": {}, "acc": {}, "causes": {}}
        for p in POL:
            for rho in RHOS:
                u = np.array([r["policies"][p]["U"][rho] for r in recs])
                d["U"][f"{p}@{rho}"] = [float(u.mean()), float(u.std(ddof=1) / np.sqrt(n))]
            for key in ("retrain", "alert", "rollback"):
                x = np.array([r["policies"][p]["counts"][key] for r in recs])
                d["counts"][f"{p}:{key}"] = [float(x.mean()), float(x.std(ddof=1) / np.sqrt(n))]
            x = np.array([r["policies"][p]["n_correct"] / r["policies"][p]["n_eval"] for r in recs])
            d["acc"][p] = [float(x.mean()), float(x.std(ddof=1) / np.sqrt(n))]
        rivals = ["binary", "always_retrain", "no_response"]
        mean_pol = {
            p: (
                float(np.mean([r["policies"][p]["n_correct"] for r in recs])),
                float(np.mean([cost_units(r["policies"][p]["counts"]) for r in recs])),
            )
            for p in POL
        }
        d["window_seed_mean"] = window(mean_pol, rivals)
        d["window_per_seed"] = [
            window(
                {
                    p: (r["policies"][p]["n_correct"], cost_units(r["policies"][p]["counts"]))
                    for p in POL
                },
                rivals,
            )
            for r in recs
        ]
        d["mean_a_k"] = mean_pol
        d["causes"] = {}
        for r in recs:
            for c in r["policies"]["full_rar"]["causes"]:
                d["causes"][c] = d["causes"].get(c, 0) + 1
        # canary-removal (rollback_only vs full_rar share canary; here: full_rar - rollback_only at rho=1)
        res[s] = d
    with open(out, "w") as fh:
        json.dump(res, fh, indent=1)
    for s, d in res.items():
        print(s, "window(seed-mean):", d["window_seed_mean"])
        print("   per-seed:", d["window_per_seed"])


main()
