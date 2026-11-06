"""Summarize R5's frozen 20-seed all-14-source descriptive real-stream replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t as student_t

SOURCES = [
    "rialto",
    "spam",
    "weather",
    "openml_ldpa",
    "uci_occupancy",
    "airlines",
    "bank",
    "elec2",
    "criteo",
    "metro",
    "beijing_pm25",
    "bike_hour",
    "appliances",
    "household_power",
]
POLICIES = [
    "R5",
    "D2",
    "A5b",
    "economic_replacement",
    "R:economic_stop",
    "cams_adapter",
    "gated_adaptive_range+front",
]
COMPARATORS = POLICIES[1:]


def mean_ci(x):
    x = np.asarray(x, dtype=float)
    n = len(x)
    m = float(x.mean())
    if n < 2:
        return [m, None, None]
    half = float(student_t.ppf(0.975, n - 1) * x.std(ddof=1) / np.sqrt(n))
    return [m, m - half, m + half]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--json", required=True)
    ap.add_argument("--markdown", required=True)
    a = ap.parse_args()
    root = Path(a.input)
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["argv"]["kind"] == "real"
    assert manifest["argv"]["seeds"] == 20 and manifest["argv"]["seed_base"] == 2026110903
    df = pd.read_json(root / "records.jsonl", lines=True, precise_float=True)
    assert set(df.regime) == set(SOURCES), (set(df.regime), set(SOURCES))
    assert set(df.policy) == set(POLICIES), set(df.policy)
    counts = df.groupby(["regime", "ep", "policy"]).size()
    assert (counts == 20).all(), counts[counts != 20]
    assert set(df.seed) == set(range(20)), set(df.seed)
    assert df.groupby(["regime", "ep", "policy", "seed"]).size().eq(1).all(), (
        "duplicate/missing rows"
    )
    # Seeds are Monte Carlo repetitions for a fixed episode; episodes remain the uncertainty unit.
    episode = (
        df.groupby(["regime", "ep", "policy"], sort=True)
        .agg(
            net=("net", "mean"),
            labels=("labels", "mean"),
            switches=("switches", "mean"),
            promotion_rate=("ever_promote", "mean"),
        )
        .reset_index()
    )
    by_source = {}
    source_cost = {p: [] for p in POLICIES}
    contrast_values = {c: [] for c in COMPARATORS}
    for source in SOURCES:
        g = episode[episode.regime == source]
        pvt = g.pivot(index="ep", columns="policy", values="net")
        out = {
            "episodes": len(pvt),
            "mean_net_cost": {},
            "mean_labels": {},
            "mean_switches": {},
            "promotion_rate": {},
        }
        for p in POLICIES:
            pg = g[g.policy == p]
            out["mean_net_cost"][p] = float(pg.net.mean())
            source_cost[p].append(float(pg.net.mean()))
            out["mean_labels"][p] = float(pg.labels.mean())
            out["mean_switches"][p] = float(pg.switches.mean())
            out["promotion_rate"][p] = float(pg.promotion_rate.mean())
        out["paired_episode_contrasts_R5_minus_comparator"] = {}
        for c in COMPARATORS:
            delta = (pvt["R5"] - pvt[c]).to_numpy(float)
            out["paired_episode_contrasts_R5_minus_comparator"][c] = {
                "mean_t_ci_95": mean_ci(delta),
                "episodes_favoring_R5": int((delta < 0).sum()),
                "episodes_tied": int(np.isclose(delta, 0).sum()),
                "episode_fraction_favoring_R5": float((delta < 0).mean()),
            }
            contrast_values[c].append(float(delta.mean()))
        by_source[source] = out
    result = {
        "title": "R5 all-14-source real-stream cost replay (post-development descriptive)",
        "manifest": str(root / "manifest.json"),
        "seed_base": 2026110903,
        "policy_seeds_per_episode": 20,
        "total_episodes": int(episode.groupby("regime").ep.nunique().sum()),
        "sources": SOURCES,
        "policies": POLICIES,
        "unit": "Mean over 20 policy-randomness seeds within episode; t intervals across chronological episodes within each source.",
        "equal_source_mean_net_cost": {p: float(np.mean(source_cost[p])) for p in POLICIES},
        "equal_source_mean_paired_cost_contrast": {
            c: {
                "mean_of_source_means": float(np.mean(contrast_values[c])),
                "source_means": contrast_values[c],
            }
            for c in COMPARATORS
        },
        "by_source": by_source,
        "limitations": [
            "All sources were previously used or exposed in this sprint; new policy seeds do not create independent dataset evidence.",
            "Episodes within each source are consecutive and may be dependent; t intervals may be optimistic.",
            "Cached Atlas streams lack verified change times and feature-publication timestamps. No late-improvement or causal harm class is inferred.",
            "The evaluator-side real gain field is a proxy, not ground truth; interpretation is based on recorded net cost and resource use.",
        ],
    }
    out = Path(a.json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# R5 all-14-source real-stream cost replay",
        "",
        "Post-development descriptive replay; 20 policy-randomness seeds per fixed episode. All sources are previously exposed. t intervals are computed across within-source chronological episodes and may be optimistic. No event is labeled late, reversal, or null from its realized outcome. See JSON for per-source costs, resource use, promotion rates, and limitations.",
        "",
        "## Paired R5 cost differences by source",
        "",
        "| Source | Episodes | Comparator | R5 − comparator, mean [95% t CI] | Episodes favoring R5 |",
        "|---|---:|---|---:|---:|",
    ]
    for source, v in by_source.items():
        for c, cv in v["paired_episode_contrasts_R5_minus_comparator"].items():
            m, lo, hi = cv["mean_t_ci_95"]
            ci_text = "not estimable (1 episode)" if lo is None else f"[{lo:.2f}, {hi:.2f}]"
            lines.append(
                f"| {source} | {v['episodes']} | {c} | {m:.2f} {ci_text} | {cv['episodes_favoring_R5']}/{v['episodes']} |"
            )
    lines += [
        "",
        "## Equal-source descriptive averages",
        "",
        "| Policy | Mean net cost across 14 source means |",
        "|---|---:|",
    ]
    for p, val in result["equal_source_mean_net_cost"].items():
        lines.append(f"| {p} | {val:.2f} |")
    lines += [
        "",
        "| Comparator | Mean of 14 source-level R5 − comparator contrasts |",
        "|---|---:|",
    ]
    for c, v in result["equal_source_mean_paired_cost_contrast"].items():
        lines.append(f"| {c} | {v['mean_of_source_means']:.2f} |")
    lines += [
        "",
        "This replay covers economic replay only. It cannot establish genuine late-improvement transfer, application-level utility, an anytime guarantee, or independent generalization.",
        "",
    ]
    Path(a.markdown).write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
