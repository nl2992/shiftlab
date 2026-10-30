"""Frozen G5 confirmation (docs/h2c_next/FROZEN_CONFIRMATION_PROTOCOL.md). Run once."""

import numpy as np
import pandas as pd

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g
from shiftlab.sota_search import harness as h

ARMS = {
    "F1_H2c": ("pp_cost_guided", {"mode": "guided_disc", "gamma": 0.995}),
    "F2_guided_ONS": ("pp_cost_guided", {"mode": "guided"}),
    "F3_multi_guided": ("pp_cost_multi", {"guided": True}),
    "C0_cost_parent": ("pp_cost_tight", {}),
    "C1_cost_disc": ("fix_cost", {"gamma": 0.995, "uniform_cap": True}),
    "C2_cost_ONS": ("pp_cost_guided", {"mode": "cost_ons"}),
    "C7a_cost_SR": ("sr_cost_tight", {}),
    "HG_unifcap": ("fix_brier", {"gamma": 0.99, "gate_w": 100, "uniform_cap": True}),
    "ONS_Brier": ("pp_ons", {}),
}
N = 600
rows, k = [], 0
for ci, cond in enumerate(g.G5_CONDITIONS):
    nulls = g.simulate_g5(cond, "none", 400, 99000 + ci)
    for shift in g.G5_SHIFTS:
        sim = g.simulate_g5(cond, shift, N, 90000 + k)
        k += 1
        T = sim["y"].shape[1]
        harmful = bool(sim["harmful"].any())
        role = "null" if shift == "none" else ("harm" if harmful else "benign")
        fh = 700 if harmful else T
        for frac in (0.10, 0.20):
            for arm, (name, extra) in ARMS.items():
                p = {"frac": frac, "delay": 5, "tol": 0.0, **extra}
                thr = det.THEORY_THRESHOLD.get(name)
                if thr is None:
                    thr = h.calibrate(name, p, nulls)
                al = det.first_cross(
                    np.nan_to_num(det.DETECTORS[name](sim, lseed=95000 + k, **p), nan=-np.inf), thr
                )
                det_ = (al < T) & (al >= fh) & harmful
                fa = al < fh
                for s in range(N):
                    rows.append(
                        (
                            cond,
                            shift,
                            role,
                            round(sim["harm_post"], 3),
                            frac,
                            arm,
                            s,
                            bool(det_[s]),
                            bool(fa[s]),
                        )
                    )
        print(cond, shift, role, flush=True)
df = pd.DataFrame(
    rows,
    columns=["cond", "shift", "role", "harm", "frac", "arm", "seed", "detected", "false_alarm"],
)
df.to_parquet("outputs/h2c_next/g5_confirmation_per_seed.parquet")
cell = df.groupby(["cond", "shift", "role", "harm", "frac", "arm"], as_index=False)[
    ["detected", "false_alarm"]
].mean()
cell.to_csv("outputs/h2c_next/g5_confirmation_cells.csv", index=False)

rng = np.random.default_rng(17)
harm = df[df.role == "harm"]
cells = sorted(set(zip(harm.cond, harm.shift, strict=True)))


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
