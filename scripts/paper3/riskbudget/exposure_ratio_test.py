"""Does the cost of the guarantee track exposure-in-delay over headroom? (written 2026-11-16,
committed before it was first run; uses existing outputs only, no new simulation)

Unit = (regime or real stream, F3 arm, headroom h). Arms: f3_pi1, f3v2d, v3.
Sources: scarce family fresh seeds (outputs/.../v3_scarce, 47 regimes) and the 14 real streams,
clean condition (outputs/.../real and real_v3).
Units are kept only where wald_cut gains at least 10% of J(never) (otherwise the ratio is undefined).

  x = r * d / h          r = disagreement rate (config r; real: mean of l0 != l1), d = label delay
  L = (J_F3 - J_wald) / (J_never - J_wald)    share of wald_cut's improvement that F3 gives up

Prediction stated before running (Proposition 3): L increases with x. Primary: Spearman(x, L) > 0
with a unit-bootstrap 95% CI above 0, separately for each (source, arm), 6 tests. Descriptive:
median L in x bins [0,.5), [.5,1), [1,2), [2,inf). Check for confounding: OLS of L on log x and
log(B/(r T)) (labels per exposed round); report whether log x keeps a positive coefficient.
"""

import glob
import json
import os
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

from shiftlab.paper3.riskbudget.harness import ROOT

O = ROOT / "outputs" / "paper3" / "riskbudget"
RES = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/results/riskbudget"
ARMS = ("f3_pi1", "f3v2d", "v3")
HS = (6, 14, 24, 50, 100)
MIN_GAIN = 0.10


def mean_of(d, arm, key="J"):
    if arm not in d["arms"]:
        return None
    return float(np.mean(np.array(d["fields"][key][d["arms"].index(arm)], float)))


def scarce_units():
    cfg = json.loads((ROOT / "configs/paper3/regimes_f3_scarce_v1.json").read_text())
    df = cfg["defaults"]
    out = []
    for g in cfg["regimes"]:
        d = json.loads((O / "v3_scarce" / f"{g['id']}.json").read_text())
        r = g.get("r", df["r"])
        dl = g.get("delay", df["delay"])["d"]
        B, T = g.get("B", df["B"]), 2000
        Jn, Jw = mean_of(d, "never"), mean_of(d, "wald_cut")
        for a in ARMS:
            for h in HS:
                J = mean_of(d, f"{a}_h{h}")
                if J is not None:
                    out.append(("scarce", g["id"], a, h, r, dl, B / (r * T), Jn, Jw, J))
    return out


def real_units():
    from shiftlab.paper3.riskbudget import real_streams as rs

    out = []
    for f in sorted(glob.glob(str(O / "real" / "clean" / "*.json"))):
        name = os.path.basename(f)[:-5]
        if name not in rs.STREAMS:  # streams dropped for missing provenance (real_streams.EXCLUDED)
            continue
        d = json.loads(Path(f).read_text())
        d3 = json.loads((O / "real_v3" / "clean" / f"{name}.json").read_text())
        l0, l1 = rs.load_stream(name)
        r = float(np.mean(np.asarray(l0) != np.asarray(l1)))
        Jn, Jw = mean_of(d, "never"), mean_of(d, "wald_cut")
        for a in ARMS:
            for h in HS:
                src = d3 if a == "v3" else d
                J = mean_of(src, f"{a}_h{h}")
                if J is not None:
                    out.append(("real", name, a, h, r, d["delay"], 200 / (r * 2000), Jn, Jw, J))
    return out


def main():
    rows = []
    for s, u, a, h, r, dl, lab, Jn, Jw, J in scarce_units() + real_units():
        if Jn - Jw < MIN_GAIN * Jn:
            continue
        rows.append(
            {
                "source": s,
                "unit": u,
                "arm": a,
                "h": h,
                "r": r,
                "d": dl,
                "x": r * dl / h,
                "labels_per_exposure": lab,
                "L": (J - Jw) / (Jn - Jw),
            }
        )
    rng = np.random.default_rng(0)
    res = {"n_units": len(rows), "tests": {}, "bins": {}, "ols": {}}
    for s in ("scarce", "real"):
        for a in ARMS:
            R = [w for w in rows if w["source"] == s and w["arm"] == a]
            x, L = np.array([w["x"] for w in R]), np.array([w["L"] for w in R])
            rho = spearmanr(x, L).statistic
            units = sorted({w["unit"] for w in R})
            bs = []
            for _ in range(2000):  # resample regimes/streams, keep all h of a drawn unit
                pick = rng.choice(units, len(units))
                idx = [i for p in pick for i, w in enumerate(R) if w["unit"] == p]
                bs.append(spearmanr(x[idx], L[idx]).statistic)
            lo, hi = np.nanpercentile(bs, [2.5, 97.5])
            res["tests"][f"{s}/{a}"] = {
                "n": len(R),
                "n_units": len(units),
                "spearman": float(rho),
                "lo": float(lo),
                "hi": float(hi),
                "supported": bool(lo > 0),
            }
            edges = [0, 0.5, 1, 2, np.inf]
            res["bins"][f"{s}/{a}"] = {
                f"[{edges[i]},{edges[i + 1]})": {
                    "n": int(m.sum()),
                    "median_L": float(np.median(L[m])) if m.any() else None,
                }
                for i in range(4)
                for m in [(x >= edges[i]) & (x < edges[i + 1])]
            }
            X = np.column_stack(
                [np.ones(len(R)), np.log(x), np.log([w["labels_per_exposure"] for w in R])]
            )
            beta, *_ = np.linalg.lstsq(X, L, rcond=None)
            res["ols"][f"{s}/{a}"] = {"b_logx": float(beta[1]), "b_log_labels": float(beta[2])}
    RES.mkdir(parents=True, exist_ok=True)
    (RES / "exposure_ratio_test.json").write_text(
        json.dumps({"summary": res, "rows": rows}, indent=1)
    )
    for k, v in res["tests"].items():
        print(k, {q: (round(z, 3) if isinstance(z, float) else z) for q, z in v.items()})
    for k, v in res["bins"].items():
        print(
            k,
            {
                b: (w["n"], None if w["median_L"] is None else round(w["median_L"], 3))
                for b, w in v.items()
            },
        )
    for k, v in res["ols"].items():
        print(k, {q: round(z, 3) for q, z in v.items()})


if __name__ == "__main__":
    main()
