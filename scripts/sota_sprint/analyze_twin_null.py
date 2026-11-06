"""Analysis registered in docs/sota_sprint/p2_known_null_protocol.md (K0-K3), split-clustered bootstrap.

uv run python scripts/sota_sprint/analyze_twin_null.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / "outputs/sota_sprint/twin_null"
DATA = ROOT / "data/sprint_twin_losses"
DOC = ROOT / "docs/sota_sprint/validation"
BOUND = 0.0936
POWERED = [
    "gated_adaptive_range",
    "gated_adaptive_range+front",
    "discern_design_floor",
    "SMCS+retain-incumbent",
    "xu_acquisition_only",
    "choe_ramdas_eb",
    "choe_ramdas_eb+front",
    "gated_deployment+QCE",
    "gated_deployment+QCE+front",
]
ORDER = [
    "gated_deployment",
    "discern_style",
    *POWERED,
    "A5b",
    "A1b",
    "rmm:gated_deployment+RMM",
    "rmm:discern_style+RMM",
    "rmm:SMCS+retain-incumbent+RMM",
    "rmm:gated_adaptive_range+RMM",
    "D1",
    "D2",
    "QSG",
    "model_picker_adapter",
    "cams_adapter",
]


def boot(per_split: np.ndarray, n=2000, seed=0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    m = per_split[rng.integers(0, len(per_split), (n, len(per_split)))].mean(axis=1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def wilson_hi(k, n, z=1.96):
    p = k / n
    return (p + z * z / (2 * n) + z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / (
        1 + z * z / n
    )


def main():
    df = pd.read_json(RUN / "records.jsonl", lines=True)
    stats = json.loads((DATA / "stats.json").read_text())
    res = {"K0": {}, "datasets": {}, "K1": {}, "K2": {}}
    for reg, g in df.groupby("regime"):
        ds = reg.removeprefix("twin_")
        z = np.load(DATA / f"{reg}.npz")
        split = z["split"]
        adv_ep = (z["l0"].astype(float) - z["l1"]).mean(axis=1)  # realised challenger advantage
        g = g.assign(split=split[g.ep.to_numpy()], adv=adv_ep[g.ep.to_numpy()])
        ps = pd.Series(adv_ep).groupby(split).mean().to_numpy()
        ci = boot(ps)
        res["K0"][ds] = {
            "mean_adv": float(ps.mean()),
            "ci": ci,
            "contains_0": bool(ci[0] <= 0 <= ci[1]),
        }
        never = g[g.policy == "CONTROL_never_switch"].set_index(["ep", "seed"]).net
        cell = {
            "median_rho_hat": stats[ds]["median_rho_hat"],
            "disagreement": stats[ds]["disagreement"],
            "policies": {},
        }
        for p, gp in g.groupby("policy"):
            per = gp.groupby("split").ever_promote.mean().to_numpy()
            lo, hi = boot(per)
            k, n = int(gp.ever_promote.sum()), len(gp)
            harm = gp.set_index(["ep", "seed"]).net - never
            harmful = gp[(gp.ever_promote == 1) & (gp.adv <= 0)]
            cell["policies"][p] = {
                "promote": float(per.mean()),
                "boot_lo": lo,
                "boot_hi": hi,
                "pooled_wilson_hi": round(wilson_hi(k, n), 4),
                "runs": n,
                "harm_vs_never": float(harm.mean()),
                "harmful_promotion_rate": float(len(harmful) / n),
            }
        res["datasets"][ds] = cell
    eligible = [d for d, c in res["datasets"].items() if (c["median_rho_hat"] or 0) >= 0.5]
    for p in POWERED:
        fails = [
            d
            for d in eligible
            if res["datasets"][d]["policies"][p]["promote"] > BOUND
            and res["datasets"][d]["policies"][p]["boot_lo"] > 0.05
        ]
        res["K1"][p] = fails
    res["K1_n_failing"] = sum(bool(v) for v in res["K1"].values())
    res["K1_pass"] = res["K1_n_failing"] >= 5
    res["K2"] = {
        d: res["datasets"][d]["policies"]["A5b"]["boot_hi"] <= BOUND for d in res["datasets"]
    }
    res["K2_pass"] = all(res["K2"].values())
    DOC.mkdir(parents=True, exist_ok=True)
    (DOC / "twin_null_results.json").write_text(json.dumps(res, indent=1) + "\n")
    dss = list(res["datasets"])
    L = [
        "# P2 known-null real streams (exchangeable twins): results",
        "",
        (
            "Protocol: [../p2_known_null_protocol.md](../p2_known_null_protocol.md) (registered 36d9796 before any build). "
            "20 splits x K episodes x 3 policy seeds per dataset; promotion = fraction of runs that ever promote "
            "on a known-null stream; 95% CI = cluster bootstrap over splits. Bold = point > .0936 with lower bound > .05."
        ),
        "",
        "| dataset | median rho-hat | disagreement | mean realised adv [CI] (K0) |",
        "|---|---|---|---|",
    ]
    for d in dss:
        c, k0 = res["datasets"][d], res["K0"][d]
        L.append(
            f"| {d} | {c['median_rho_hat']} | {c['disagreement']:.3f} | {k0['mean_adv']:+.4f} "
            f"[{k0['ci'][0]:+.4f},{k0['ci'][1]:+.4f}] |"
        )
    L += ["", "| policy | " + " | ".join(dss) + " |", "|---|" + "---|" * len(dss)]
    for p in ORDER:
        cells = []
        for d in dss:
            v = res["datasets"][d]["policies"].get(p)
            if v is None:
                cells.append("")
                continue
            r = f"{v['promote']:.3f}"
            if v["promote"] > BOUND and v["boot_lo"] > 0.05:
                r = f"**{r}**"
            cells.append(
                f"{r} [{v['boot_lo']:.3f},{v['boot_hi']:.3f}]; harm {v['harm_vs_never']:+.1f}"
            )
        L.append(f"| {p} | " + " | ".join(cells) + " |")
    L += [
        "",
        f"**K1 (>= 5/9 powered certified ports break the bound on a rho-hat >= .5 dataset): "
        f"{'PASS' if res['K1_pass'] else 'FAIL'}** ({res['K1_n_failing']}/9): "
        + "; ".join(f"{p}: {v or 'none'}" for p, v in res["K1"].items()),
        f"**K2 (A5b bootstrap upper bound <= .0936 on every dataset): {'PASS' if res['K2_pass'] else 'FAIL'}** {res['K2']}",
    ]
    (DOC / "twin_null_results.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
