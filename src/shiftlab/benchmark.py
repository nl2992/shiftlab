"""Shared prequential benchmark with evaluator-only scoring and atomic manifests."""

import argparse
import hashlib
import importlib.metadata
import json
import os
import subprocess
import uuid
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

from .core.config import Config, load_config
from .learner import Learner, LearnerSettings, decision_losses
from .streaming import simulate
from .synthetic import generate


def atomic_json(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")
    os.replace(temporary, path)


def run(config: Config):
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    directory = Path(config.output) / f"{stamp}-{uuid.uuid4().hex[:10]}"
    directory.mkdir(parents=True)
    payload = config.model_dump()
    try:
        commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except subprocess.CalledProcessError:
        commit = None
    metadata = {
        "config": payload,
        "config_hash": hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest(),
        "git_commit": commit,
        "utc": stamp,
        "versions": {
            name: importlib.metadata.version(name)
            for name in ["shiftlab", "numpy", "scipy", "scikit-learn", "pandas", "pydantic"]
        },
        "status": "running",
        "algorithm_randomness": "deterministic Ridge",
    }
    atomic_json(directory / "metadata.json", metadata)
    rows, traces = [], []
    try:
        for seed in config.seeds:
            stream = generate(config, seed)
            atomic_json(directory / f"dgp-{seed}.json", stream.parameters)
            methods = {
                1: ["frozen"],
                2: ["fixed", "rolling"],
                3: ["frozen", "periodic", "triggered"],
            }[config.paper]
            for method in methods:
                a, b = config.train_end, config.calibration_end
                learner = Learner(
                    stream.X[:a],
                    stream.y[:a],
                    stream.X[a:b],
                    stream.y[a:b],
                    LearnerSettings.from_config(config),
                    method,
                )
                events = simulate(
                    stream.X, stream.y, learner, b, config.delay, config.missing, seed + 100000
                )
                frame = pd.DataFrame(events)
                y, pred, radius = (frame[k].to_numpy() for k in ["target", "prediction", "radius"])
                covered = abs(y - pred) <= radius
                frame["covered"] = covered
                frame["seed"], frame["method"] = seed, method
                traces.append(frame)
                cost = config.retrain_cost * len(learner.interventions)
                p = norm.cdf(stream.mean[b:] / stream.sigma[b:])
                risk = np.where(pred >= 0, 1 - p, 5 * p)
                row = {
                    "paper": config.paper,
                    "shift": config.shift,
                    "seed": seed,
                    "method": method,
                    "mse": float(np.mean((y - pred) ** 2)),
                    "coverage": float(np.mean(covered)),
                    "mean_width": float(np.mean(2 * radius)),
                    "decision_loss": float(np.mean(decision_losses(y, pred))),
                    "policy_regret": float(np.sum(risk - np.minimum(1 - p, 5 * p))),
                    "num_interventions": len(learner.interventions),
                    "adaptation_cost": cost,
                    "objective": float(np.sum((y - pred) ** 2) + cost),
                    "training_seconds": learner.training_seconds,
                    "inference_seconds": learner.inference_seconds,
                }
                for regime in [0, 1]:
                    mask = stream.regime[b:] == regime
                    row[f"regime_{regime}_coverage"] = (
                        float(np.mean(covered[mask])) if mask.any() else None
                    )
                for detector, alarms in learner.alarms.items():
                    change = config.change_at if config.shift != "none" else None
                    pre = [t for t in alarms if change is None or t < change]
                    post = [t for t in alarms if change is not None and t >= change]
                    row.update(
                        {
                            f"{detector}_false_alarms": len(pre),
                            f"{detector}_detected": bool(post),
                            f"{detector}_delay": post[0] - change if post else None,
                        }
                    )
                atomic_json(
                    directory / f"events-{seed}-{method}.json",
                    {"alarms": learner.alarms, "interventions": learner.interventions},
                )
                np.savez(
                    directory / f"model-{seed}-{method}.npz",
                    coef=learner.model.coef_,
                    intercept=learner.model.intercept_,
                )
                rows.append(row)
        for name, data in [
            ("metrics", pd.DataFrame(rows)),
            ("trace", pd.concat(traces, ignore_index=True)),
        ]:
            data.to_csv(directory / f"{name}.tmp", index=False)
            os.replace(directory / f"{name}.tmp", directory / f"{name}.csv")
        from .plots import plot

        plot(pd.concat(traces), config, directory)
        metadata["status"] = "complete"
    except Exception as exc:
        metadata.update(status="failed", error=repr(exc))
        raise
    finally:
        atomic_json(directory / "metadata.json", metadata)
    return directory


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/experiments/diagnostics.yaml")
    parser.add_argument("--paper", type=int, choices=[1, 2, 3])
    args = parser.parse_args()
    config = load_config(args.config)
    if args.paper:
        config = Config.model_validate({**config.model_dump(), "paper": args.paper})
    print(run(config))
