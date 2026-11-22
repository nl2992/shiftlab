"""Tally the 100-stream screen by the locked criterion (protocol 05G).

S1: every shield arm has zero runs above its own budget in all three conditions.
S2: on clean feedback, the better of f3_pi1_h50 / f3v2d_h50 has mean J below never switching.
Writes outputs/paper3/riskbudget/screen100/tally.json and prints per-group and overall counts.
"""

import json
from collections import defaultdict

import numpy as np

from shiftlab.paper3.riskbudget.harness import ROOT
from shiftlab.paper3.riskbudget.real_streams import CONDITIONS, R_of

DATA = ROOT / "data" / "screen100_losses"
OUT = ROOT / "outputs" / "paper3" / "riskbudget" / "screen100"
SHIELDS = {"f3_pi1_h14": R_of(14), "f3v2d_h14": R_of(14), "f3_pi1_h50": R_of(50), "f3v2d_h50": R_of(50)}
COMPARATORS = ("wald_cut", "cusum", "gate_wald", "cusum_rb_h8", "stoploss_h14")


def main():
    stats = json.loads((DATA / "stats.json").read_text())
    rows = []
    for s in stats:
        name = s["name"]
        if s["status"] != "built":
            rows.append({"name": name, "group": s["group"], "status": "unbuildable"})
            continue
        res = {c: json.loads((OUT / c / f"{name}.json").read_text()) for c in CONDITIONS}
        arms = res["clean"]["arms"]
        A = {c: {f: np.array(v, dtype=float) for f, v in res[c]["fields"].items()} for c in CONDITIONS}
        viol = {a: int(sum((A[c]["sup_harm"][arms.index(a)] > R + 1e-9).sum() for c in CONDITIONS))
                for a, R in SHIELDS.items()}  # fmt: skip
        comp_exceed = {a: int(sum((A[c]["sup_harm"][arms.index(a)] > R_of(14) + 1e-9).sum() for c in CONDITIONS))
                       for a in COMPARATORS}  # fmt: skip
        J = A["clean"]["J"].mean(axis=(1, 2))
        j = dict(zip(arms, J.tolist()))
        j_never = float(A["clean"]["J_never"].mean())
        best = min(j["f3_pi1_h50"], j["f3v2d_h50"])
        s1, s2 = all(v == 0 for v in viol.values()), best < j_never
        rows.append({
            "name": name, "group": s["group"], "status": "supported" if (s1 and s2) else "not_supported",
            "S1": s1, "S2": s2, "shield_violations": viol, "comparator_exceed_R24": comp_exceed,
            "J_never": j_never, "J_shield_best_h50": best, "J_wald": j["wald_cut"],
            "shield_gain_vs_never": j_never - best, "wald_gain_vs_never": j_never - j["wald_cut"],
            "x_h50": s["disagreement"] * s["delay"] / 50, "disagreement": s["disagreement"],
            "challenger_better_mean": s["incumbent_err"] - s["challenger_err"],
        })  # fmt: skip
    g = defaultdict(lambda: defaultdict(int))
    for r in rows:
        g[r["group"]][r["status"]] += 1
        g["ALL"][r["status"]] += 1
    (OUT / "tally.json").write_text(json.dumps({"rows": rows, "groups": g}, indent=1))
    for k, v in g.items():
        print(f"{k:14s} " + "  ".join(f"{s}={n}" for s, n in sorted(v.items())))
    ns = [r for r in rows if r["status"] == "not_supported"]
    print("S1 failures:", sum(not r["S1"] for r in ns), " S2 failures:", sum(not r["S2"] for r in ns))


if __name__ == "__main__":
    main()
