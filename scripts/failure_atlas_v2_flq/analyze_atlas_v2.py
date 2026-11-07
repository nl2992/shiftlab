"""Summarise Failure Atlas v2 records into algorithm-by-regime tables and paired comparisons.

    uv run python scripts/failure_atlas_v2_flq/analyze_atlas_v2.py RUN_DIR [RUN_DIR ...] \
        --md docs/failure_atlas_v2_flq/results/atlas_tables.md [--pairs host:repair,...]

Paired differences are computed per (regime, ep, seed) unit and summarised by a unit-level
bootstrap (2000 resamples). For real data the resampling unit is the episode (seed-averaged),
because seeds there vary only policy randomness, not the stream.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

CERTIFIED = {"gated_deployment", "discern_style", "SMCS+retain-incumbent", "xu_acquisition_only",
             "P7s_settled"}
METRICS = ["net", "loss", "labels", "switches", "first_deploy", "ever_promote", "final",
           "frac_on_wrong", "regret_expected_oracle", "regret_hindsight", "labels_by_500",
           "exhaust_t"]


def load(dirs):
    return pd.concat([pd.read_json(Path(d) / "records.jsonl", lines=True) for d in dirs],
                     ignore_index=True)


def boot_ci(x, n=2000, seed=0):
    x = np.asarray(x, float)
    if len(x) < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    m = x[rng.integers(0, len(x), (n, len(x)))].mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def units(df):
    """Paired unit: synthetic -> (regime, seed); real -> (regime, ep) averaged over seeds."""
    if (df["kind"] == "real").all():
        return df.groupby(["regime", "ep", "policy"], as_index=False).mean(numeric_only=True)
    return df


def summary(df):
    g = df.groupby(["regime", "policy"])
    s = g[METRICS].mean()
    s["first_deploy_med"] = g["first_deploy"].apply(lambda v: float(np.median(v[v >= 0]))
                                                   if (v >= 0).any() else np.nan)
    s["n"] = g.size()
    return s.reset_index()


def paired(df, a, b):
    u = units(df)
    rows = []
    for reg, d in u.groupby("regime"):
        key = ["ep", "seed"] if "seed" in d and (d["kind"] == "synthetic").all() else ["ep"]
        A = d[d.policy == a].set_index(key)["net"]
        B = d[d.policy == b].set_index(key)["net"]
        j = A.index.intersection(B.index)
        if len(j) == 0:
            continue
        diff = (B.loc[j] - A.loc[j]).to_numpy()
        lo, hi = boot_ci(diff)
        rows.append({"regime": reg, "host": a, "repair": b, "n": len(j),
                     "mean_diff": float(diff.mean()), "lo": lo, "hi": hi,
                     "wins": int((diff < 0).sum()), "losses": int((diff > 0).sum())})
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--md", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--pairs", default="")
    a = ap.parse_args(argv)
    df = load(a.dirs)
    s = summary(df)
    out = ["| regime | policy | net | loss | labels | switches | promote | 1st deploy (med) | "
           "on-wrong | regret vs E-oracle |", "|" + "---|" * 10]
    for reg, d in s.groupby("regime", sort=False):
        d = d.sort_values("net")
        for _, r in d.iterrows():
            out.append(f"| {reg} | {r.policy} | {r.net:.1f} | {r.loss:.1f} | {r.labels:.0f} | "
                       f"{r.switches:.2f} | {r.ever_promote:.2f} | {r.first_deploy_med:.0f} | "
                       f"{r.frac_on_wrong:.2f} | {r.regret_expected_oracle:.1f} |")
    pair_tabs = []
    for p in [x for x in a.pairs.split(",") if x]:
        h, r = p.split(":")
        pair_tabs.append(paired(df, h, r))
    if pair_tabs:
        pt = pd.concat(pair_tabs)
        out += ["", "| regime | host | repair | n | repair-host | 95% CI | wins/losses |",
                "|" + "---|" * 7]
        for _, r in pt.iterrows():
            out.append(f"| {r.regime} | {r.host} | {r.repair} | {r.n} | {r.mean_diff:+.2f} | "
                       f"[{r.lo:+.2f}, {r.hi:+.2f}] | {r.wins}/{r.losses} |")
    text = "\n".join(out)
    if a.md:
        Path(a.md).parent.mkdir(parents=True, exist_ok=True)
        Path(a.md).write_text(text + "\n")
    if a.json:
        Path(a.json).write_text(json.dumps({"summary": s.to_dict("records"),
                                            "pairs": pd.concat(pair_tabs).to_dict("records")
                                            if pair_tabs else []}, indent=1, default=float))
    print(text)


if __name__ == "__main__":
    main()
