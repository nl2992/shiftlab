import numpy as np
import pandas as pd

df = pd.read_parquet("outputs/h2c_next/dev_per_seed.parquet")
rng = np.random.default_rng(5)
rows = []
for frac in (0.10, 0.20):
    for src in ("G3dev", "G4dev"):
        d = df[(df.frac == frac) & (df.source == src)]
        base = d[d.arm == "C4_H2c_.995"].sort_values("seed").detected.astype(float).values
        for arm in sorted(d.arm.unique()):
            if arm == "C4_H2c_.995":
                continue
            x = d[d.arm == arm].sort_values("seed").detected.astype(float).values
            diff = base - x
            b = diff[rng.integers(0, len(diff), (4000, len(diff)))].mean(1)
            rows.append(
                {
                    "frac": frac,
                    "source": src,
                    "vs": arm,
                    "H2c_minus": round(diff.mean(), 3),
                    "lo": round(float(np.quantile(b, 0.025)), 3),
                    "hi": round(float(np.quantile(b, 0.975)), 3),
                }
            )
out = pd.DataFrame(rows)
out.to_csv("outputs/h2c_next/h2c_paired_dev.csv", index=False)
pd.set_option("display.width", 200)
print(
    out[
        out.vs.isin(
            [
                "C0_cost_parent",
                "C1_cost_disc.995",
                "C2_cost_ONS",
                "C3_guided_ONS",
                "C5_cost_mixture8",
                "C6b_multi_guided",
                "C7a_cost_SR",
                "A_guided_.99",
            ]
        )
    ].to_string(index=False)
)
