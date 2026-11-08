"""Frozen C3 analysis (docs/qsg_methods_search/synthetic_confirmation_protocol.md)."""

import json
import sys

import numpy as np
import pandas as pd
from analyze_d2 import CHANGE, GUARD, seedmean
from scipy import stats

ARMS = ("EQSDp_l0.95_g0.2", "EQSDp_l0.9_g0.2")
COMPS = ("gongT_w100_m10", "qiu_delayed_movement")


def ttest(x):
    m, se = x.mean(), x.std(ddof=1) / np.sqrt(len(x))
    h = stats.t.ppf(0.975, len(x) - 1) * se
    p = 2 * stats.t.sf(abs(m / se), len(x) - 1)
    return {"mean": m, "lo": m - h, "hi": m + h, "p": p}


def holm(ps):
    order = np.argsort(ps)
    adj = np.empty(len(ps))
    run = 0.0
    for i, j in enumerate(order):
        run = max(run, (len(ps) - i) * ps[j])
        adj[j] = min(1.0, run)
    return adj


def main(path):
    d = pd.read_json(path, lines=True)
    fam, gu, ch = seedmean(d, CHANGE + GUARD), seedmean(d, GUARD), seedmean(d, CHANGE)
    eo = d[d.regime.isin(CHANGE + GUARD)].groupby("policy").regret_expected_oracle.mean()
    res = {"n_seeds": int(fam.shape[0]), "contrasts": [], "arms": {}}
    rows = [(a, c, ttest(fam[a] - fam[c])) for a in ARMS for c in COMPS]
    adj = holm(np.array([r[2]["p"] for r in rows]))
    for (a, c, t), pa in zip(rows, adj, strict=True):
        res["contrasts"].append(
            {
                "arm": a,
                "comp": c,
                **t,
                "p_holm": float(pa),
                "rel_cost_pct": 100 * t["mean"] / fam[c].mean(),
                "rel_regret_pct": 100 * t["mean"] / eo[c],
            }
        )
    abl = {
        m: ttest(fam["EQSDp_l0.95_g0.2"] - fam[m])
        for m in ("EQSDp_l0.95_g0.5_m10", "EQSDp_l0.95_g0.5_m20")
    }
    best_abl = min(abl, key=lambda m: fam[m].mean())
    for a in ARMS:
        cs = [x for x in res["contrasts"] if x["arm"] == a]
        sig = all(x["p_holm"] < 0.05 and x["mean"] < 0 for x in cs)
        guard_ok = bool(gu[a].mean() - gu["econF_mo5_m5"].mean() <= 5)
        mech = True if a != ARMS[0] else bool(abl[best_abl]["hi"] < 0)
        res["arms"][a] = {
            "contrasts_sig": sig,
            "guard_ok": guard_ok,
            "guard_minus_econF": float(gu[a].mean() - gu["econF_mo5_m5"].mean()),
            "mechanism_ok": mech,
            "C3_PASS": bool(sig and guard_ok and mech),
        }
    res["ablation_vs_best_margin"] = {"best_margin_arm": best_abl, **abl[best_abl]}
    summ = pd.DataFrame(
        {"family": fam.mean(), "change": ch.mean(), "guard": gu.mean(), "exp_oracle_regret": eo}
    )
    summ["null_prom"] = (
        d[d.regime.isin(["F0_null", "V_null", "V_worse"])].groupby("policy").ever_promote.mean()
    )
    summ["sw_null"] = d[d.regime.isin(["F0_null", "V_null"])].groupby("policy").switches.mean()
    pv = d.pivot_table(index="policy", columns="regime", values="net", aggfunc="mean")
    pd.set_option("display.width", 260)
    print(summ.sort_values("family").round(2).to_string())
    print(pv[CHANGE + GUARD].round(1).to_string())
    print(json.dumps(res, indent=1, default=float))
    return res, summ, pv


if __name__ == "__main__":
    main(sys.argv[1])
