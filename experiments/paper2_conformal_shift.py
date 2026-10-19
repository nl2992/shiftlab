"""P2: fixed split conformal versus rolling residual quantile under regime shifts."""

import argparse
import json

import numpy as np

from shiftlab.data import make_stream
from shiftlab.methods import fit_ridge, rolling_quantile, weighted_conformal_quantile
from shiftlab.metrics import interval_coverage


def run(seed=42, change_at=1500):
    s = make_stream(seed=seed, change_at=change_at)
    train_end = 900
    cal_end = 1200
    model = fit_ridge(s.X[:train_end], s.y[:train_end])
    p = model.predict(s.X)
    fixed_q = weighted_conformal_quantile(np.abs(s.y[train_end:cal_end] - p[train_end:cal_end]))
    # Strict prequential experiment: today's true response may update tomorrow's interval ONLY.
    scores = np.abs(s.y[cal_end:] - p[cal_end:])
    history = np.abs(s.y[train_end:cal_end] - p[train_end:cal_end])
    rolling_q = rolling_quantile(np.r_[history, scores], width=250)[len(history) :]
    y = s.y[cal_end:]
    mu = p[cal_end:]
    mask = np.arange(cal_end, len(s.y)) >= change_at
    out = {
        "seed": seed,
        "nominal_coverage": 0.9,
        "fixed_width": float(2 * fixed_q),
        "rolling_mean_width": float(2 * np.mean(rolling_q[np.isfinite(rolling_q)])),
    }
    for name, q in [("fixed", np.full(len(y), fixed_q)), ("rolling", rolling_q)]:
        for label, m in [("pre", ~mask), ("post", mask)]:
            out[f"{name}_{label}_coverage"] = interval_coverage(y[m], mu[m] - q[m], mu[m] + q[m])
            out[f"{name}_{label}_width"] = float(np.mean(2 * q[m]))
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    a = parser.parse_args()
    print(json.dumps(run(seed=a.seed), indent=2))
