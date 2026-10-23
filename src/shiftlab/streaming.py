"""Evaluator owns targets; learners receive only prediction requests and arrived feedback."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Observation:
    time: int | float
    features: tuple[float, ...]


@dataclass(frozen=True)
class Feedback:
    time: int | float
    available_at: int | float
    features: tuple[float, ...]
    target: float
    prediction: float


def simulate(X, y, learner, start, delay=0, missing=0.0, seed=0):
    pending, events = {}, []
    rng = np.random.default_rng(seed)
    for t in range(start, len(y)):
        obs = Observation(t, tuple(X[t]))
        pred, radius = learner.predict(obs)
        events.append({"time": t, "target": float(y[t]), "prediction": pred, "radius": radius})
        if rng.random() >= missing:
            message = Feedback(t, t + delay, obs.features, float(y[t]), pred)
            pending.setdefault(message.available_at, []).append(message)
        # Prediction precedes feedback even at zero delay.
        for message in pending.pop(t, []):
            learner.observe(message)
    return events
