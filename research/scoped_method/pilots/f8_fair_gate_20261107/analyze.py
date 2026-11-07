"""Deterministic paired analysis for the frozen fair-gate pilot."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
rows = [
    json.loads(line)
    for line in (HERE / "run/records.jsonl").read_text().splitlines()
    if line.strip()
]
methods = [
    "fair_validation_gate",
    "cams_adapter",
    "SMCS+retain-incumbent",
    "gated_deployment",
    "CONTROL_never_switch",
    "fixed_challenger",
]
data: dict[str, dict[str, dict[int, dict]]] = {}
for row in rows:
    data.setdefault(row["regime"], {}).setdefault(row["policy"], {})[row["seed"]] = row

rng = np.random.default_rng(2026110720)
out = {
    "protocol": "PROTOCOL.md",
    "run_manifest": "run/manifest.json",
    "bootstrap_replicates": 20_000,
    "bootstrap_seed": 2026110720,
    "results": {},
}
for regime, by_method in data.items():
    episode_ids = sorted(by_method["fair_validation_gate"])
    n = len(episode_ids)
    result = {"n": n, "methods": {}, "paired_differences": {}}
    for method in methods:
        vals = [by_method[method][i] for i in episode_ids]
        net = np.asarray([x["net"] for x in vals], float)
        loss = np.asarray([x["loss"] for x in vals], float)
        labels = np.asarray([x["labels"] for x in vals], float)
        switches = np.asarray([x["switches"] for x in vals], float)
        promotions = np.asarray([x["ever_promote"] for x in vals], int)
        first = np.asarray([x["first_deploy"] for x in vals], float)
        promoted_at = first[first >= 0]
        result["methods"][method] = {
            "mean_net_cost": float(net.mean()),
            "mean_prediction_loss": float(loss.mean()),
            "mean_label_count": float(labels.mean()),
            "mean_label_cost": float((labels * 0.05).mean()),
            "mean_switch_count": float(switches.mean()),
            "mean_switch_cost": float((switches * 5.0).mean()),
            "promotions": int(promotions.sum()),
            "promotion_rate": float(promotions.mean()),
            "mean_promotion_event_given_promoted": (
                float(promoted_at.mean()) if len(promoted_at) else None
            ),
        }
    for comparator in methods:
        if comparator == "fair_validation_gate":
            continue
        d = np.asarray(
            [
                by_method["fair_validation_gate"][i]["net"] - by_method[comparator][i]["net"]
                for i in episode_ids
            ],
            float,
        )
        sampled = rng.integers(0, n, size=(20_000, n))
        means = d[sampled].mean(axis=1)
        result["paired_differences"][f"fair_minus_{comparator}"] = {
            "mean": float(d.mean()),
            "ci95_percentile": [float(x) for x in np.quantile(means, [0.025, 0.975])],
            "sd": float(d.std(ddof=1)),
        }
    out["results"][regime] = result

(HERE / "RESULTS.json").write_text(json.dumps(out, indent=2) + "\n")
for regime, result in out["results"].items():
    print(regime)
    for method, stats in result["methods"].items():
        print(
            method,
            round(stats["mean_net_cost"], 3),
            "labels",
            round(stats["mean_label_count"], 2),
            "switches",
            round(stats["mean_switch_count"], 2),
            "promoted",
            stats["promotions"],
            "time",
            stats["mean_promotion_event_given_promoted"],
        )
    for comp, stats in result["paired_differences"].items():
        print(comp, round(stats["mean"], 3), stats["ci95_percentile"])
