"""Q3 / S10 cost-aware switching benchmark: 6 scenarios x 8 policies x structured cost grid; per-seed records."""

import time

import numpy as np
import pandas as pd

from shiftlab.gap import q3

OUT = "outputs/gap_closure/e8_q3"
BASE = {"query": 0.01, "retrain": 0.05, "switch": 0.05, "rollback": 0.05}
LEVELS = {
    "query": (0, 0.01, 0.05),
    "retrain": (0, 0.05, 0.20),
    "switch": (0, 0.01, 0.05, 0.20),
    "rollback": (0, 0.05, 0.20),
}


def cost_grid():
    out = {"base": dict(BASE)}
    for k, lv in LEVELS.items():
        for v in lv:
            if v != BASE[k]:
                out[f"{k}={v}"] = {**BASE, k: v}
    out["all0"] = dict.fromkeys(BASE, 0.0)
    out["allmax"] = {k: max(v) for k, v in LEVELS.items()}
    return out


if __name__ == "__main__":
    import os

    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    null = q3.make(q3.Scenario("null_cal", "none"), 300, 7777)
    r = q3.run_policy(null, "ph_switch", ph_thr=1e9)
    thr = float(np.quantile(r["ph_peak"], 0.95))
    print("PH threshold (95% null quantile of max):", round(thr, 2), flush=True)
    grid = cost_grid()
    rows = []
    S = 120
    for si, sc in enumerate(q3.SCENARIOS):
        st = q3.make(sc, S, 8000 + si)
        for pol in q3.POLICIES:
            if pol == "cert_gated":
                continue
            res = q3.run_policy(st, pol, ph_thr=thr)
            for cname, c in grid.items():
                tc = q3.total_cost(res, c, pol)
                rows.append(
                    pd.DataFrame(
                        {
                            "scenario": sc.name,
                            "policy": pol,
                            "cost": cname,
                            "seed": np.arange(S) + 8000 * 1000 + si * 1000,
                            "loss": res["loss"],
                            "total": tc,
                            "regret": tc - res["loss_star"],
                            "n_q": res["n_q"],
                            "n_sw": res["n_sw"],
                            "n_rb": res["n_rb"],
                            "n_rt": res["n_rt"],
                            "n_rc": res["n_rc"],
                            "n_false": res["n_false"],
                            "runtime_s_per_seed": res["runtime_s"] / S,
                        }
                    )
                )
        for cname, c in grid.items():
            res = q3.run_policy(st, "cert_gated", costs=c)
            tc = q3.total_cost(res, c, "cert_gated")
            rows.append(
                pd.DataFrame(
                    {
                        "scenario": sc.name,
                        "policy": "cert_gated",
                        "cost": cname,
                        "seed": np.arange(S) + 8000 * 1000 + si * 1000,
                        "loss": res["loss"],
                        "total": tc,
                        "regret": tc - res["loss_star"],
                        "n_q": res["n_q"],
                        "n_sw": res["n_sw"],
                        "n_rb": res["n_rb"],
                        "n_rt": res["n_rt"],
                        "n_rc": res["n_rc"],
                        "n_false": res["n_false"],
                        "runtime_s_per_seed": res["runtime_s"] / S,
                    }
                )
            )
        print("scenario done", sc.name, round(time.time() - t0), flush=True)
    df = pd.concat(rows, ignore_index=True)
    df.to_parquet(f"{OUT}/perseed.parquet", index=False)
    pd.DataFrame([{"ph_threshold": thr}]).to_csv(f"{OUT}/calibration.csv", index=False)
    print("rows", len(df))
