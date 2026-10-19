"""P3: compare no retraining, periodic retraining and drift-triggered retraining."""

import argparse
import json

import numpy as np

from shiftlab.data import make_stream
from shiftlab.methods import fit_ridge
from shiftlab.metrics import mse


def run(seed=42, policy="trigger", retrain_cost=30.0, window=300):
    s = make_stream(seed=seed)
    train_end = 900
    model = fit_ridge(s.X[:train_end], s.y[:train_end])
    preds = []
    updates = 0
    errors = []
    alarm_cooldown = 0
    initial_loss = np.mean((s.y[:train_end] - model.predict(s.X[:train_end])) ** 2)
    for t in range(train_end, len(s.y)):
        # prequential: prediction before observe y[t]
        p = float(model.predict(s.X[t : t + 1])[0])
        preds.append(p)
        loss = (s.y[t] - p) ** 2
        errors.append(loss)
        alarm_cooldown = max(0, alarm_cooldown - 1)
        periodic = policy == "periodic" and (t - train_end) % 250 == 249
        # illustrative trigger; requires calibration for a publishable experiment
        trigger = (
            policy == "trigger"
            and len(errors) >= 50
            and np.mean(errors[-50:]) > 3 * initial_loss
            and alarm_cooldown == 0
        )
        if periodic or trigger:
            a = max(0, t - window + 1)
            model = fit_ridge(s.X[a : t + 1], s.y[a : t + 1])
            updates += 1
            alarm_cooldown = 100
    y = s.y[train_end:]
    return {
        "seed": seed,
        "policy": policy,
        "mse": mse(y, preds),
        "num_retrains": updates,
        "retrain_cost": retrain_cost,
        "objective": float(np.sum((y - np.asarray(preds)) ** 2) + retrain_cost * updates),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--policy", choices=["none", "periodic", "trigger"], default="trigger")
    p.add_argument("--retrain-cost", type=float, default=30.0)
    a = p.parse_args()
    print(json.dumps(run(seed=a.seed, policy=a.policy, retrain_cost=a.retrain_cost), indent=2))
