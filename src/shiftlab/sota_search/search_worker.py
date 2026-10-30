"""One immutable development configuration and its raw trajectory."""

import argparse
import json
import os
from pathlib import Path

import numpy as np

from .adapters import AdapterConfig
from .evaluation import evaluate
from .generators import WorldConfig, make_world


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--configuration", required=True)
    args = parser.parse_args()
    config = json.loads(args.configuration)
    world_config = WorldConfig(**config["world"])
    world = make_world(world_config, seed=config["seed"])
    source = make_world(world_config, seed=config["source_seed"], partition="source")
    adapter = AdapterConfig(**config["adapter"])
    result = evaluate(world, source, adapter, query_seed=config["seed"] + 800000)
    path = Path(os.environ["SOTA_RESULT_PATH"])
    with path.with_name("trajectory.npz").open("xb") as stream:
        np.savez_compressed(stream, **result.trajectory)
    metrics = result.metrics
    primary = {
        "Q1": "positive_decision_harm_before_alarm",
        "Q2": "alarm_by_horizon",
        "Q3": "expected_net_cost",
    }[adapter.track]
    payload = {
        "primary_metric": {primary: metrics[primary]},
        "secondary_metrics": metrics,
        "labels_used": metrics["labels_used"],
        "validity_status": metrics["validity_status"],
        "uncertainty_estimates": None,
    }
    with path.open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, allow_nan=False)


if __name__ == "__main__":
    main()
