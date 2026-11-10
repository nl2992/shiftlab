"""C1 / C3 repairs vs strongest valid baselines (equal budget, paired streams) + null FP by rho."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "outputs/paper3/atlas"
df = pd.read_pickle(OUT / "dev1_all.pkl")
df = pd.concat(
    [df] + [pd.read_json(OUT / "dev1b" / f"cell_{i:02d}.jsonl", lines=True) for i in range(32)],
    ignore_index=True,
)
RHO = {
    c.cid: c.rho for c in __import__("shiftlab.paper3.atlas.cells", fromlist=["design"]).design()
}
df["rho"] = df.cell.map(RHO)
res = {}


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return round(c - h, 3), round(c + h, 3)


nul = df[df["null"] == 1]
res["null_fp_by_rho"] = {}
for m, g in nul.groupby("method"):
    res["null_fp_by_rho"][m] = {}
    for r, h in g.groupby("rho"):
        k, n = int(h.null_fp.sum()), len(h)
        res["null_fp_by_rho"][m][str(r)] = {
            "k": k,
            "n": n,
            "rate": round(k / n, 4),
            "wilson": wilson(k, n),
        }
alt = df[df["null"] == 0]
P = alt.pivot_table(index=["cell", "seed"], columns="method", values="J")
Q = alt.pivot_table(index=["cell", "seed"], columns="method", values="edd")
rng = np.random.default_rng(1)
seeds = np.arange(30)


def paired(a, b, rho=None, tab=P, nboot=1000):
    cells = sorted(set(P.index.get_level_values(0)))
    if rho is not None:
        cells = [c for c in cells if RHO[c] in rho]
    diff = np.stack([(tab.loc[c][a] - tab.loc[c][b]).values for c in cells])  # cells x seeds
    pt = diff.mean()
    bs = [diff[:, rng.integers(0, 30, 30)].mean() for _ in range(nboot)]
    return round(float(pt), 3), (
        round(float(np.quantile(bs, 0.025)), 3),
        round(float(np.quantile(bs, 0.975)), 3),
    )


res["J_diff_vs_baselines"] = {}
for a in ["c1_gapaware", "c1c3", "c3_spaced_iid", "c1_gapaware_rho80"]:
    res["J_diff_vs_baselines"][a] = {}
    for b in [
        "markov_skeleton",
        "thinned_iid",
        "gated_mope",
        "iid_gate",
        "never_switch",
        "wald_econ",
        "cusum_cal",
    ]:
        if b not in P.columns:
            continue
        res["J_diff_vs_baselines"][a][b] = {
            "all": paired(a, b),
            "rho0-.5": paired(a, b, {0.0, 0.5}),
            "rho.8-.95": paired(a, b, {0.8, 0.95}),
        }
res["promotion_rate_alt"] = alt.groupby("method").ever_prom.mean().round(3).to_dict()
res["mean_J"] = alt.groupby("method").J.mean().round(2).to_dict()
res["mean_edd"] = alt.groupby("method").edd.mean().round(1).to_dict()
res["labels_mean"] = alt.groupby("method").n_q.mean().round(1).to_dict()
res["max_pending_mean"] = alt.groupby("method").max_pending.mean().round(1).to_dict()
# fidelity in the atlas harness: legacy vs fixed
if "discern_legacy" in P.columns:
    res["discern_legacy_minus_fixed_J"] = paired("discern_legacy", "discern_fixed")
    res["discern_legacy_vs_fixed_identical_rows"] = float(
        ((P["discern_legacy"] - P["discern_fixed"]).abs() < 1e-9).mean()
    )
(OUT / "repair_results.json").write_text(json.dumps(res, indent=1))
print(json.dumps(res, indent=1)[:7000])
