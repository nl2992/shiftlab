"""Draft multi-world evaluator to amortize later confirmation worker startup.

Not used by the running screen. A registered configuration may contain a frozen
list of independent development seeds, retaining every per-world result and raw
trajectory rather than treating events as independent replicates. Confirmation
partition access is deliberately absent from this draft.
"""

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np

from shiftlab.sota_search.adapters import AdapterConfig
from shiftlab.sota_search.evaluation import evaluate
from shiftlab.sota_search.generators import WorldConfig, make_world


def replicate(root: Path, world: WorldConfig, adapter: AdapterConfig, *, seeds, source_offset=100000):
    seeds = tuple(seeds)
    if not seeds or any(type(seed) is not int or seed < 0 for seed in seeds):
        raise ValueError("nonempty explicit independent-world seed list required")
    if len(set(seeds)) != len(seeds):
        raise ValueError("duplicate seeds are not independent replications")
    if type(source_offset) is not int or source_offset <= 0:
        raise ValueError("positive source seed offset required")
    if root.exists():
        raise FileExistsError("replication snapshot must be new")
    root.mkdir(parents=True)
    with (root / "manifest.json").open("x", encoding="utf-8") as stream:
        json.dump({"world": asdict(world), "adapter": asdict(adapter), "seeds": seeds,
                   "source_offset": source_offset, "partition": "development"}, stream, indent=2)
    rows = []
    # Flush each completed world immediately so a failed later world cannot erase
    # the completed prefix. The supervising registry still records the run failure.
    with (root / "per_world.jsonl").open("x", encoding="utf-8") as stream:
        for seed in seeds:
            deployment = make_world(world, seed=seed)
            source = make_world(world, seed=seed + source_offset, partition="source")
            result = evaluate(deployment, source, adapter, query_seed=seed + 800000)
            path = root / f"trajectory_{seed}.npz"
            with path.open("xb") as raw:
                np.savez_compressed(raw, **result.trajectory)
            row = {"seed": seed, "source_seed": seed + source_offset,
                   "metrics": result.metrics, "trajectory": path.name}
            stream.write(json.dumps(row, allow_nan=False) + "\n")
            stream.flush()
            rows.append(row)
    return {
        "independent_worlds": len(rows),
        "alarms": sum(row["metrics"]["alarm_by_horizon"] for row in rows),
        "mean_expected_net_cost": float(np.mean([row["metrics"]["expected_net_cost"] for row in rows])),
        "labels_used": sum(row["metrics"]["labels_used"] for row in rows),
        "source_labels": sum(row["metrics"]["source_labels"] for row in rows),
        "interpretation": "independent development replications; no automatic validity claim",
    }
