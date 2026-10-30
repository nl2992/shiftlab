"""Draft post-screen selection. Refuses incomplete or duplicated manifests.

Kept outside the running source closure. Selection uses the frozen rule; it does
not generate confirmation worlds or infer statistically credible improvements.
"""

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np


PRIMARY = {
    "Q1": "positive_decision_harm_before_alarm",
    "Q2": "alarm_by_horizon",
    "Q3": "expected_net_cost",
}
ALTERNATIVES = {"harmful_concept", "transient_challenger", "harm_without_accuracy"}
PARENTS = {
    "Q1": {("direct", "uniform"), ("ppe", "uniform")},
    "Q2": {("direct", "uniform"), ("ppe", "uniform")},
    "Q3": {("frozen", "uniform"), ("greedy", "uniform"), ("certified", "uniform")},
}


def select(records, *, expected_count=540):
    if len(records) != expected_count:
        raise ValueError("selection requires the complete terminal archive")
    configurations = [r["configuration_hash"] for r in records]
    if len(set(configurations)) != expected_count:
        raise ValueError("duplicated configuration hashes")
    cells = defaultdict(dict)
    scores = defaultdict(list)
    failures = []
    for record in records:
        if record["execution_status"] != "completed":
            failures.append(record["configuration_hash"])
            continue
        adapter = record["hyperparameters"]
        track = adapter["track"]
        variant = (adapter["method"], adapter["query"])
        world = (record["generator_family"], record["shift_type"], record["random_seed"])
        metric = float(record["secondary_metrics"][PRIMARY[track]])
        if not np.isfinite(metric):
            raise ValueError("nonfinite primary metric")
        if variant in cells[(track, world)]:
            raise ValueError("duplicated method/world result")
        cells[(track, world)][variant] = metric
        if record["shift_type"] in ALTERNATIVES:
            scores[(track, variant)].append(metric)
    summary = {}
    for track in PRIMARY:
        # Missing results never improve a variant's apparent score by dropping
        # difficult worlds. Require all 4*3 alternative worlds for rank selection.
        complete = {
            variant: float(np.mean(values))
            for (kind, variant), values in scores.items()
            if kind == track and len(values) == 12
        }
        ordered = sorted(complete, key=lambda v: ((-1 if track == "Q2" else 1) * complete[v], v))
        ranked = set()
        if ordered:
            cutoff = complete[ordered[min(2, len(ordered) - 1)]]
            ranked = {
                variant for variant in ordered
                if (complete[variant] >= cutoff if track == "Q2" else complete[variant] <= cutoff)
            }
        conditional = set()
        paired = []
        parent = ("frozen", "uniform") if track == "Q3" else ("ppe", "uniform")
        for (kind, world), results in cells.items():
            if kind != track or world[1] not in ALTERNATIVES:
                continue
            if results:
                best = max(results.values()) if track == "Q2" else min(results.values())
                # Strict win means strictly better than every other observed
                # variant; tied cells do not create a strict conditional winner.
                winners = [variant for variant, metric in results.items() if metric == best]
                if len(winners) == 1 and len(results) == 9:
                    conditional.add(winners[0])
            if parent in results:
                for variant, metric in results.items():
                    paired.append({
                        "world": world, "variant": variant,
                        "candidate_minus_parent": metric - results[parent],
                        "parent": parent,
                    })
        survivors = ranked | conditional | PARENTS[track]
        summary[track] = {
            "primary_metric": PRIMARY[track],
            "ranking": [{"variant": v, "mean": complete[v]} for v in ordered],
            "rank_survivors": sorted(ranked),
            "strict_conditional_survivors": sorted(conditional),
            "mandatory_controls": sorted(PARENTS[track]),
            "survivors": sorted(survivors),
            "paired_development_differences": paired,
            "uncertainty": "one seed per scenario; no confirmatory uncertainty estimate",
        }
    return {"tracks": summary, "failed_configuration_hashes": failures,
            "claim": "exploratory survival only; not evidence of SOTA superiority"}


def read_terminal(root):
    with sqlite3.connect((root / "experiments.sqlite").resolve().as_uri() + "?mode=ro", uri=True) as db:
        return [json.loads(row[0]) for row in db.execute("SELECT payload FROM events WHERE phase='terminal'")]


if __name__ == "__main__":
    root = Path("outputs/sota_search/development_screen_v1")
    result = select(read_terminal(root))
    with (root / "exploratory_selection.json").open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
