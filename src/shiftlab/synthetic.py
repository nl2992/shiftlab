"""Four paired regression controls. All oracle arrays are evaluator-only."""

from dataclasses import dataclass

import numpy as np


@dataclass
class EvaluatorStream:
    X: np.ndarray
    y: np.ndarray
    mean: np.ndarray
    sigma: np.ndarray
    regime: np.ndarray
    parameters: dict


def generate(config, seed):
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(config.n, 4))
    post = np.arange(config.n) >= config.change_at
    beta = np.tile([1.0, -0.9, 0.0, 0.0], (config.n, 1))
    sigma = np.full(config.n, 0.3)
    if config.shift == "benign":
        X[post, 3] += config.strength
    elif config.shift == "concept":
        beta[post, 0] -= config.strength
    elif config.shift == "variance":
        sigma[post] *= 1 + config.strength
    mean = np.sum(X * beta, axis=1)
    y = mean + sigma * rng.normal(size=config.n)
    regime = post.astype(int) if config.shift != "none" else np.zeros(config.n, dtype=int)
    return EvaluatorStream(
        X,
        y,
        mean,
        sigma,
        regime,
        {
            "beta": beta.tolist(),
            "sigma": sigma.tolist(),
            "family": config.shift,
            "change_at": config.change_at if config.shift != "none" else None,
        },
    )
