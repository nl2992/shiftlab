"""Secondary (odd episodes): B3 (chosen config, v=.002, h=100) as a one-switch-held-to-end rule, cost J vs the Paper 1
Wald+cutoff reference under the transfer-port contract (Costs: T=2000, B=200, cq=.05, cs=5).
Contract differences: B3 uses B=150, queries every round of its batch (not disagreement-gated), single switch only,
payback certificate targets h=100 not the remaining horizon; Wald is multi-switch with paced disagreement purchases."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.paper3.transfer.sim import PRIMARY, simulate

DATA = Path("../shift-research-starter/data/c4_sealed")
b3 = pd.read_csv("outputs/paper3/payback/b3/odd_v002_h100.csv")
b3 = b3[b3.cert == "C3"].set_index(["stream", "episode"])
GRID = np.array([[0.98, 0.3, 300.0], [0.97, 0.2, 0.0]])  # wald+cutoff(0.15T), Paper 1 REF_CFG
rows = []
for f in sorted(DATA.glob("*.npz")):
    z = np.load(f)
    l0, l1, d = z["l0"][1::2], z["l1"][1::2], int(z["delay"])
    eps = np.arange(1, z["l0"].shape[0], 2)
    out = simulate(l0, l1, d, PRIMARY, grid=GRID, seed=0)
    Z = l0.astype(float) - l1
    for i, ep in enumerate(eps):
        r = b3.loc[(f.stem, ep)]
        j = l0[i].sum() + PRIMARY.cq * r["labels"]
        if r["certified"]:
            t = int(r["t"])
            j = j - Z[i, t - 1 :].sum() + PRIMARY.cs
        rows.append((f.stem, ep, l0[i].sum(), j, out["J"][i, 0], out["J"][i, 1]))
df = pd.DataFrame(
    rows, columns=["stream", "episode", "J_never", "J_B3", "J_wald_cut", "J_wald_ref"]
)
df.to_csv("outputs/paper3/payback/b3/odd_vs_wald.csv", index=False)
rng = np.random.default_rng(20261110)
ps = df.groupby("stream")[["J_never", "J_B3", "J_wald_cut", "J_wald_ref"]].mean()
res = {"means_stream_equal": ps.mean().to_dict()}
for a, b in (
    ("J_B3", "J_wald_cut"),
    ("J_B3", "J_wald_ref"),
    ("J_B3", "J_never"),
    ("J_wald_cut", "J_never"),
):
    d = (ps[a] - ps[b]).to_numpy()
    m = d[rng.integers(0, len(d), (10000, len(d)))].mean(1)
    res[f"{a}-{b}"] = [float(d.mean()), *map(float, np.percentile(m, [2.5, 97.5]))]
print(json.dumps(res, indent=1))
json.dump(res, open("outputs/paper3/payback/b3/odd_vs_wald.json", "w"), indent=1)  # noqa: SIM115
