"""Track R: empirical cost-risk curves, calibration on development data, and Pareto frontiers.

Input: screen.py runs of the same policies at several nominal alphas (each row carries ``alpha``).
1. ``calibrate``: on DEVELOPMENT runs, for each policy and target r, pick the largest alpha on the grid
   whose pooled null promotion rate over bench2.RISK_NULLS is <= r (point estimate). If even the
   smallest alpha exceeds r, the policy has no operating point at r.
2. ``evaluate``: on SEPARATE seeds, report for each (policy, target) the realised null promotion rate
   (Wilson 95% CI) and the mean alternative cost (95% t-CI over seeds of the per-seed mean over
   bench2.RISK_ALTS), plus the cost-risk Pareto frontier.
An empirical risk level is not an anytime-valid guarantee.

    uv run python scripts/sota_sprint/risk_curves.py --dev DIR [DIR..] --eval DIR [DIR..] --out PATH
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from bench2 import RISK_ALTS, RISK_NULLS, RISK_TARGETS


def _load(dirs):
    df = pd.concat([pd.read_json(Path(d) / "records.jsonl", lines=True, precise_float=True)
                    for d in dirs], ignore_index=True)
    return df.assign(alpha=df.alpha.round(6))


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, c - h), min(1.0, c + h)


def calibrate(dev: pd.DataFrame, nulls=RISK_NULLS, targets=RISK_TARGETS) -> dict:
    risk = dev[dev.regime.isin(nulls)].groupby(["policy", "alpha"]).ever_promote.mean()
    out = {}
    for p in risk.index.get_level_values(0).unique():
        r = risk[p].sort_index()
        out[p] = {t: (round(float(r[r <= v].index.max()), 6) if (r <= v).any() else None)
                  for t, v in targets.items()}
    return out


def evaluate(ev: pd.DataFrame, amap: dict, nulls=RISK_NULLS, alts=RISK_ALTS) -> dict:
    res = {}
    for p, m in amap.items():
        for t, a in m.items():
            if a is None:
                continue
            g = ev[(ev.policy == p) & np.isclose(ev.alpha, a)]
            gn, ga = g[g.regime.isin(nulls)], g[g.regime.isin(alts)]
            if gn.empty or ga.empty:
                continue
            k, n = int(gn.ever_promote.sum()), len(gn)
            per_seed = ga.groupby(["seed", "ep"]).net.mean()
            se = per_seed.std(ddof=1) / np.sqrt(len(per_seed))
            res.setdefault(t, {})[p] = {"alpha": a, "risk": k / n, "risk_ci": wilson(k, n),
                                        "cost": float(per_seed.mean()),
                                        "cost_ci": (float(per_seed.mean() - 1.96 * se),
                                                    float(per_seed.mean() + 1.96 * se))}
    for t, d in res.items():
        pts = sorted(d.items(), key=lambda kv: (kv[1]["risk"], kv[1]["cost"]))
        best, front = float("inf"), []
        for p, v in pts:
            if v["cost"] < best:
                best = v["cost"]
                front.append(p)
        for p in d:
            d[p]["pareto"] = p in front
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dev", nargs="+", required=True)
    ap.add_argument("--eval", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    amap = calibrate(_load(a.dev))
    res = evaluate(_load(a.eval), amap)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps({"calibration": amap, "curves": res}, indent=1, default=float) + "\n")
    L = ["| target | policy | alpha* | realised risk [95% CI] | alt cost [95% CI] | Pareto |", "|---|---|---|---|---|---|"]
    for t, d in res.items():
        for p, v in sorted(d.items(), key=lambda kv: kv[1]["cost"]):
            L.append(f"| {t} | {p} | {v['alpha']} | {v['risk']:.3f} [{v['risk_ci'][0]:.3f},{v['risk_ci'][1]:.3f}] | "
                     f"{v['cost']:.1f} [{v['cost_ci'][0]:.1f},{v['cost_ci'][1]:.1f}] | {'*' if v['pareto'] else ''} |")
    Path(a.out).with_suffix(".md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
