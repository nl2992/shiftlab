import sys

import pandas as pd

d = sys.argv[1] if len(sys.argv) > 1 else "e2_s03_screen"
sm = pd.read_csv(f"outputs/gap_closure/{d}/summary_by_world.csv")
A = ("bias_after_shift", "anti", "subgroup", "calibration")
Bn = ("accurate", "oracle_adapt")


def grp(w):
    if "concept2" in w:
        px = w.split("|")[-1]
        return "A" if px in A else ("B" if px in Bn else "?")
    return "N"


sm["grp"] = sm.world.map(grp)
sm["parent"] = sm.config.str.split("|").str[0]
piv = lambda col: sm.pivot_table(index="config", columns="grp", values=col)
pw, fa = piv("power"), piv("fa")
res = pd.DataFrame(
    {
        "powA": pw["A"],
        "powB": pw["B"],
        "faN": fa["N"],
        "faN_max": sm[sm.grp == "N"].groupby("config").fa.max(),
        "hb": sm[sm.role == "harm"].groupby("config").harm_before.mean(),
    }
)
res["parent"] = res.index.str.split("|").str[0]
base = res[res.index.str.endswith("|parent")]
rows = []
for c, r in res.iterrows():
    if c.endswith("|parent"):
        continue
    b = base.loc[f"{r.parent}|parent"]
    rows.append(
        {
            "config": c,
            "dA": r.powA - b.powA,
            "dB": r.powB - b.powB,
            "dFA": r.faN - b.faN,
            "faN_max": r.faN_max,
            "powA": r.powA,
            "accept": (r.powA - b.powA >= 0.05)
            and (r.powB - b.powB >= -0.03)
            and (r.faN - b.faN <= 0.02)
            and r.faN_max <= 0.07 + 1e-9,
        }
    )
out = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print(base.round(3).to_string())
print("\nacceptance (prereg): n accepted =", int(out.accept.sum()), "of", len(out))
for p, g_ in out.groupby(out.config.str.split("|").str[0]):
    print(f"\n== parent {p}: top 8 by dA subject to dB>=-0.03, dFA<=0.02")
    ok = g_[(g_.dB >= -0.03) & (g_.dFA <= 0.02)].sort_values("dA", ascending=False).head(8)
    print(ok.round(3).to_string(index=False))
    print(
        "best dA overall:",
        g_.dA.max().round(3),
        " median dA:",
        g_.dA.median().round(3),
        " median dB:",
        g_.dB.median().round(3),
    )
    print("by gate/fallback median dA:")
    gg = g_.assign(gate=g_.config.str.split("|").str[-1], fb=g_.config.str.split("|").str[-2])
    print(gg.groupby(["gate", "fb"]).dA.median().round(3).unstack().to_string())
out.to_csv(f"outputs/gap_closure/{d}/acceptance.csv", index=False)
