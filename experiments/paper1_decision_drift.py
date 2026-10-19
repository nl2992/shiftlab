"""P1: prediction-error detector vs asymmetric downstream decision-loss detector."""

import argparse
import json

import numpy as np

from shiftlab.data import make_stream
from shiftlab.methods import fit_ridge
from shiftlab.metrics import decision_cost, mse


def first_alarm(values, baseline, threshold, patience=5):
    # Placeholder detector, not a validated sequential test.
    streak = 0
    for t, v in enumerate(values):
        streak = streak + 1 if v > baseline + threshold else 0
        if streak >= patience:
            return t
    return None


def run(seed=42, n=3000, change_at=1500):
    stream = make_stream(n=n, change_at=change_at, seed=seed)
    train_end = int(change_at * 0.65)
    model = fit_ridge(stream.X[:train_end], stream.y[:train_end])
    pred = model.predict(stream.X)
    window = 75
    errors = (stream.y - pred) ** 2
    losses = 5 * ((stream.y >= 0) & (pred < 0)) + 1 * ((stream.y < 0) & (pred >= 0))

    def rolling(a):
        return np.convolve(a, np.ones(window) / window, mode="valid")

    err_roll, loss_roll = rolling(errors), rolling(losses)
    base_end = max(window, train_end - window)

    # IMPORTANT: threshold selected entirely on pre-change data.
    def threshold(a):
        pre = a[:base_end]
        return float(np.quantile(pre, 0.995) - np.median(pre))

    err_at = first_alarm(err_roll, float(np.median(err_roll[:base_end])), threshold(err_roll))
    loss_at = first_alarm(loss_roll, float(np.median(loss_roll[:base_end])), threshold(loss_roll))
    return {
        "seed": seed,
        "change_at": change_at,
        "error_alarm": None if err_at is None else int(err_at + window - 1),
        "decision_alarm": None if loss_at is None else int(loss_at + window - 1),
        "pre_mse": mse(stream.y[:change_at], pred[:change_at]),
        "post_mse": mse(stream.y[change_at:], pred[change_at:]),
        "pre_decision_cost": decision_cost(stream.y[:change_at], pred[:change_at]),
        "post_decision_cost": decision_cost(stream.y[change_at:], pred[change_at:]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    a = parser.parse_args()
    print(json.dumps(run(seed=a.seed), indent=2))
