"""Analysis of the frozen G5 confirmation from the saved per-seed file (the runner crashed on a name clash after saving)."""

import numpy as np
import pandas as pd

N = 600
df = pd.read_parquet("outputs/h2c_next/g5_confirmation_per_seed.parquet")
cell = pd.read_csv(
    "outputs/h2c_next/g5_confirmation_cells.csv", keep_default_na=False, na_values=[""]
)
rng = np.random.default_rng(17)
harm = df[df.role == "harm"]
cells = sorted(set(zip(harm.cond, harm["shift"], strict=True)))


def vec(frac, arm, c):
    x = harm[
        (harm.frac == frac) & (harm.arm == arm) & (harm.cond == c[0]) & (harm["shift"] == c[1])
    ]
    return x.sort_values("seed").detected.astype(float).values


def paired(frac, a, b):
    diffs = np.stack([vec(frac, a, c) - vec(frac, b, c) for c in cells])  # (cells, seeds)
    est = diffs.mean()
    boots = []
    for _ in range(4000):
        ci = rng.integers(0, len(cells), len(cells))
        si = rng.integers(0, N, N)
        boots.append(diffs[ci][:, si].mean())
    return float(est), float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))


verdict = {}
for frac in (0.10, 0.20):
    best_other = {
        c: max(vec(frac, "C1_cost_disc", c).mean(), vec(frac, "C2_cost_ONS", c).mean())
        for c in cells
    }
    # D1 uses the per-cell better of C1/C2 as the comparator
    diffs = np.stack(
        [
            vec(frac, "F1_H2c", c)
            - (
                vec(frac, "C1_cost_disc", c)
                if vec(frac, "C1_cost_disc", c).mean() >= vec(frac, "C2_cost_ONS", c).mean()
                else vec(frac, "C2_cost_ONS", c)
            )
            for c in cells
        ]
    )
    boots = [
        diffs[rng.integers(0, len(cells), len(cells))][:, rng.integers(0, N, N)].mean()
        for _ in range(4000)
    ]
    est, lo, hi = (
        float(diffs.mean()),
        float(np.quantile(boots, 0.025)),
        float(np.quantile(boots, 0.975)),
    )
    verdict[f"D1/{frac}"] = (est >= 0.05 and lo > 0, round(est, 3), round(lo, 3), round(hi, 3))
    e2, _, _ = paired(frac, "F1_H2c", "F2_guided_ONS")
    e3, _, _ = paired(frac, "F1_H2c", "F3_multi_guided")
    verdict[f"D2/{frac}"] = (e2 >= -0.02 and e3 >= -0.02, round(e2, 3), round(e3, 3))
    nul = cell[(cell.role == "null") & (cell.frac == frac)]
    ben = cell[(cell.role == "benign") & (cell.frac == frac)]
    for a in ("F1_H2c", "F2_guided_ONS", "F3_multi_guided"):
        nmax = float(nul[nul.arm == a].false_alarm.max())
        bmean = float(ben[ben.arm == a].false_alarm.mean())
        verdict[f"D3/{frac}/{a}"] = (
            nmax <= 0.07 and bmean <= 0.07,
            round(nmax, 3),
            round(bmean, 3),
        )
    verdict[f"D4/{frac}/F1-C7a"] = round(paired(frac, "F1_H2c", "C7a_cost_SR")[0], 3)
pd.set_option("display.width", 220)
print(
    cell[cell.role.isin(["harm"])]
    .groupby(["frac", "arm"])["detected"]
    .mean()
    .unstack(0)
    .round(3)
    .to_string()
)
print(
    cell[cell.role.isin(["benign", "null"])]
    .groupby(["role", "frac", "arm"])["false_alarm"]
    .mean()
    .unstack(0)
    .round(3)
    .to_string()
)
for k_, v in verdict.items():
    print(k_, v)
print(
    "harm cells",
    len(cells),
    "benign cells",
    int(cell[(cell.role == "benign") & (cell.frac == 0.1) & (cell.arm == "F1_H2c")].shape[0]),
)
