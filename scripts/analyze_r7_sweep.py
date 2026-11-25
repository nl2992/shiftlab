"""Summarise the R7 adaptation-strength sweep (docs/r7_adaptation_strength_sweep_protocol.md)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/r7_sweep"
ARMS = [
    "gated_ht_fixed",
    "gated_ht_paced",
    "gated_ht_fixed__timans_grapa",
    "gated_ht_paced__timans_grapa",
    "uniform_ppi",
    "ppe_gated",
    "full_feedback",
]


def exact_upper(k: int, n: int, level: float = 0.95) -> float:
    return 1.0 if k >= n else float(beta.ppf(level, k + 1, n - k))


def main() -> None:
    d = pd.read_parquet(OUT / "streams.parquet")
    d = d[d.arm.isin(ARMS)].copy()
    harm = d[d.onset.notna()]
    null = d[d.onset.isna()]
    keys = ["adaptation_strength", "budget_rate", "arm"]

    det = (
        harm.groupby(keys)
        .agg(n=("seed", "size"), detect=("detected", "mean"), delay=("censored_delay", "mean"),
             horizon=("processed", "mean"), q_post=("q_mean_post_onset", "mean"))
        .reset_index()
    )
    det.to_csv(OUT / "detection_by_cell.csv", index=False)

    mat = (
        pd.read_parquet(OUT / "streams.parquet", columns=["adaptation_strength", "budget_rate", "seed", "onset", "arm",
                                                          "disagreement_post"])
        .query("arm == 'full_feedback'")
        .groupby(["adaptation_strength"])
        .agg(harm_rate=("onset", lambda s: s.notna().mean()), disagree_post=("disagreement_post", "mean"))
    )
    print("material-harm fraction and post-onset disagreement by strength")
    print(mat.round(3).to_string())

    for engine, a, b in (("fixed08", "gated_ht_fixed", "gated_ht_paced"),
                         ("timans_grapa", "gated_ht_fixed__timans_grapa", "gated_ht_paced__timans_grapa")):
        print(f"\nDETECTION, fixed vs paced gating ({engine}); harm-path cells only")
        piv = det[det.arm.isin([a, b])].pivot_table(index=["adaptation_strength", "budget_rate"],
                                                    columns="arm", values="detect")
        piv["fixed-paced"] = piv[a] - piv[b]
        print(piv.round(2).to_string())

    print("\nRESERVE HORIZON (events processed of 2400), fixed vs paced")
    hz = det[det.arm.isin(["gated_ht_fixed", "gated_ht_paced"])].pivot_table(
        index=["adaptation_strength", "budget_rate"], columns="arm", values="horizon")
    print(hz.round(0).to_string())

    print("\nMEAN DETECTION BY ARM (budget r<=0.05 pooled)")
    low = det[det.budget_rate <= 0.05]
    print(low.groupby(["adaptation_strength", "arm"]).detect.mean().unstack().round(2).to_string())

    print("\nPRE-ONSET ALARM RATE (worst cell per arm; exact one-sided 95% upper bound)")
    fa = d[d.onset.notna()].groupby(keys).agg(n=("seed", "size"), k=("false_alarm", "sum")).reset_index()
    nl = null.groupby(keys).agg(n=("seed", "size"), k=("false_alarm", "sum")).reset_index()
    fa = pd.concat([fa, nl]).groupby(keys).sum().reset_index()
    fa["upper"] = [exact_upper(int(k), int(n)) for k, n in zip(fa.k, fa.n)]
    print(fa.groupby("arm").apply(lambda g: pd.Series({"max_rate": (g.k / g.n).max(), "max_upper": g.upper.max()}),
                                   include_groups=False).round(3).to_string())


if __name__ == "__main__":
    main()
