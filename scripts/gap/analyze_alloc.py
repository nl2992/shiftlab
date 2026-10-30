import sys

import pandas as pd

d = sys.argv[1]
sm = pd.read_csv(f"outputs/gap_closure/{d}/summary_by_world.csv")
sm["parent"] = sm.config.str.split("|").str[0]
sm["arm"] = sm.config.str.split("|").str[1]
sm["frac"] = sm.config.str.split("|").str[2]
pd.set_option("display.width", 220)
h = sm[sm.role == "harm"].pivot_table(
    index=["parent", "frac", "arm"], values=["power", "harm_before", "labels"], aggfunc="mean"
)
n = (
    sm[sm.role == "nonharm"]
    .groupby(["parent", "frac", "arm"])
    .fa.agg(["mean", "max"])
    .rename(columns={"mean": "fa_nonharm", "max": "fa_max"})
)
t = h.join(n)
t["power_per_100labels"] = 100 * t.power / t.labels
print(t.round(3).to_string())
# paired per-world differences vs uniform and vs variance
pw = sm[sm.role == "harm"].pivot_table(
    index=["parent", "frac", "world"], columns="arm", values="power"
)
for ref in ("uniform", "variance", "robust_mix"):
    for arm in ("growth", "growth_oracle", "growth_harm", "growth_look", "budget_growth"):
        if arm in pw.columns:
            dd = (
                (pw[arm] - pw[ref])
                .groupby(level=[0, 1])
                .agg(["mean", lambda s: (s < -0.03).mean(), lambda s: (s > 0.03).mean()])
            )
            dd.columns = ["mean_diff", "frac_worse>.03", "frac_better>.03"]
            print(f"\n{arm} - {ref}:\n", dd.round(3).to_string())
