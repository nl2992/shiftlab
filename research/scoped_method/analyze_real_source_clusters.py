#!/usr/bin/env python3
"""Equal-source paired contrasts for corrected, previously exposed real replay suites.

Usage:
  python3 research/scoped_method/analyze_real_source_clusters.py \
    /path/to/real_exposed_wmaxfix_20261105/records.jsonl \
    /path/to/real_fresh_wmaxfix_20261105/records.jsonl

Episode-seed observations are paired within each dataset source and averaged first. The t
interval then treats datasets as the independent units. This is descriptive for these exposed
replays; it does not turn them into independent confirmation data.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

POLICIES = (
    "gated_adaptive_range",
    "gated_adaptive_range+front",
    "gated_adaptive_range+pace_tuned",
    "C2",
    "C6",
)
T975 = {5: 2.776, 9: 2.306, 14: 2.160}


def source_effects(paths: list[Path]) -> dict[str, dict[str, float]]:
    paired: dict[tuple[str, str, str], dict[str, float]] = defaultdict(dict)
    for path in paths:
        for line in path.open(encoding="utf-8"):
            row = json.loads(line)
            if row.get("policy") not in POLICIES:
                continue
            key = (row["regime"], str(row["ep"]), str(row["seed"]))
            paired[key][row["policy"]] = float(row["net"])

    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for (source, _episode, _seed), row in paired.items():
        if not all(policy in row for policy in POLICIES):
            continue
        # Candidate minus comparator; negative favors the candidate.
        front = row["gated_adaptive_range+front"]
        values[source]["front_minus_gated"].append(front - row["gated_adaptive_range"])
        values[source]["front_minus_pace"].append(front - row["gated_adaptive_range+pace_tuned"])
        values[source]["front_minus_C2"].append(front - row["C2"])
        values[source]["front_minus_C6"].append(front - row["C6"])
    return {
        source: {name: statistics.mean(diffs) for name, diffs in measures.items()}
        for source, measures in values.items()
    }


def summarize(effects: dict[str, dict[str, float]]) -> dict:
    n = len(effects)
    if n not in T975:
        raise ValueError(f"No predeclared t critical value for n_sources={n}; do not infer one.")
    out = {"n_source_clusters": n, "source_effects": effects, "contrasts": {}}
    for contrast in ("front_minus_gated", "front_minus_pace", "front_minus_C2", "front_minus_C6"):
        vals = [v[contrast] for v in effects.values()]
        mean = statistics.mean(vals)
        se = statistics.stdev(vals) / math.sqrt(n)
        half = T975[n] * se
        out["contrasts"][contrast] = {
            "mean_candidate_minus_comparator": mean,
            "ci95_t": [mean - half, mean + half],
            "n_sources": n,
        }
    return out


def main() -> None:
    paths = [Path(arg) for arg in sys.argv[1:]]
    if not paths:
        raise SystemExit(__doc__)
    result = summarize(source_effects(paths))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
