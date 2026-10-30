"""S07 pool-based robust pro-active inference: one-factor-at-a-time variations around a base world."""

import dataclasses

import pandas as pd

from shiftlab.gap import pool_ai as P

base = P.PoolWorld()
vary = {
    "N": (2000, 5000, 20000),
    "n": (100, 300, 1000),
    "n0": (20, 30, 60),
    "hetero": (0.0, 1.0, 2.0),
    "misspec": ("none", "wrong_uncertainty"),
    "blocks": (2, 5, 10),
    "eps": (0.0, 0.1, 0.25, 0.5),
}
rows = []
for k, vals in vary.items():
    for v in vals:
        w = dataclasses.replace(base, **{k: v})
        for m in P.METHODS:
            r = P.evaluate(w, m, reps=150 if w.N <= 5000 else 60, seed0=500_000)
            rows.append({"factor": k, "value": v, "method": m, **r})
    print("done", k, flush=True)
df = pd.DataFrame(rows)
u = df[df.method == "uniform"].set_index(["factor", "value"]).mse
df["mse_ratio_vs_uniform"] = df.apply(lambda r: r.mse / u.loc[(r.factor, r.value)], axis=1)
df.to_csv("outputs/gap_closure/e9_s07_pool.csv", index=False)
print(df[(df.factor == "hetero")].round(4).to_string())
