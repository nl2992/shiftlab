"""Vectorized COCOB optimizer primitive for the active-RCPS adaptation.

Port of author-vendored cocob.py (a67f85d), Copyright (c) 2023 Francesco
Orabona, MIT license; see COCOB_LICENSE.txt. This is known optimizer machinery,
not a new acquisition algorithm. Leading dimensions are independent learners.
"""

import numpy as np


class Cocob:
    def __init__(self, initial, *, alpha=100, eps=1e-8):
        self.value = np.asarray(initial, dtype=float).copy()
        if not np.isfinite(self.value).all() or alpha < 0 or eps <= 0:
            raise ValueError("finite initial values and positive epsilon required")
        self.initial = self.value.copy()
        self.alpha = alpha
        self.scale = np.full_like(self.value, eps)
        self.negative_gradients = np.zeros_like(self.value)
        self.gradient_norm = np.zeros_like(self.value)
        self.reward = np.zeros_like(self.value)

    def step(self, gradient):
        gradient = np.asarray(gradient, dtype=float)
        if gradient.shape != self.value.shape or not np.isfinite(gradient).all():
            raise ValueError("finite gradient matching parameters required")
        self.scale = np.maximum(self.scale, np.abs(gradient))
        self.negative_gradients -= gradient
        self.gradient_norm += np.abs(gradient)
        self.reward = np.maximum(0, self.reward - gradient * (self.value - self.initial))
        denominator = (
            np.maximum(self.gradient_norm + self.scale, self.alpha * self.scale) * self.scale
        )
        self.value = (
            self.initial + (self.reward + self.scale) * self.negative_gradients / denominator
        )
        return self.value


def fixed_question_features(guess):
    """Author sim_featurize with three knots and fixed beta=.5, plus bias."""
    guess = np.asarray(guess, dtype=float)
    if guess.ndim != 1 or not np.isfinite(guess).all() or np.any((guess < 0) | (guess > 1)):
        raise ValueError("bounded one-dimensional proxy required")
    digit = np.column_stack(
        [np.maximum(1 - 2 * guess, 0), 1 - np.abs(2 * guess - 1), np.maximum(2 * guess - 1, 0)]
    )
    beta = np.array([0.0, 1.0, 0.0, 1.0])
    return np.column_stack(
        [(beta[None, :, None] * digit[:, None, :]).reshape(len(guess), -1), np.ones(len(guess))]
    )


class FixedRiskPredictor:
    """One-beta LinearRiskPredictor, with the native clamp and COCOB update."""

    def __init__(self, paths):
        self.optimizer = Cocob(np.zeros((paths, 13)))

    def predict(self, features):
        return np.clip(np.sum(self.optimizer.value * features, axis=1), 0, 1)

    def update(self, features, target, observed):
        raw = np.sum(self.optimizer.value * features, axis=1)
        derivative = 2 * (np.clip(raw, 0, 1) - target) * ((raw >= 0) & (raw <= 1)) * observed
        self.optimizer.step(derivative[:, None] * features)


class QueryNormalizer:
    """Native query/dual normalization, or the explicit paper-payoff variant.

    Neither expected-rate guarantee is claimed after adding a hard-cap wrapper.
    The native finite dual cap is retained in both variants for transparency.
    """

    def __init__(self, paths, *, target=0.2, floor=0.05, objective="source"):
        if not 0 < floor <= target <= 1 or objective not in ("source", "paper"):
            raise ValueError("invalid normalization contract")
        self.target, self.floor, self.objective = target, floor, objective
        self.optimizer = Cocob(np.zeros(paths))
        self.history = np.zeros((256, paths))
        self.total = np.zeros(paths)
        self.index = 0

    def predict(self, variance):
        if self.objective == "paper":
            # Evaluate the same clipped ratio in log space; c may be very negative.
            with np.errstate(divide="ignore"):
                log_raw = 0.5 * np.log(variance) - self.optimizer.value
            raw = np.exp(np.minimum(log_raw, 1))
            return np.clip(raw, self.floor, 1), raw, np.zeros_like(raw)
        inverse = np.exp(-self.optimizer.value)
        if not np.isfinite(inverse).all():
            raise ArithmeticError("normalizer overflow")
        raw = np.sqrt(variance) * inverse
        return np.clip(raw, self.floor, 1), raw, inverse

    def update(self, q, raw, inverse, active):
        violation = (q - self.target) * active
        dual = (self.total + violation > 0) * (1 - np.log(2))
        gradient = (
            -inverse if self.objective == "source" else np.ones_like(inverse)
        ) - dual * q * ((raw >= self.floor) & (raw <= 1))
        self.optimizer.step(gradient * active)
        if self.objective == "paper":
            # Explicit projected variant: the native dual cap need not stabilize this payoff.
            self.optimizer.value = np.clip(self.optimizer.value, -20, 20)
        slot = self.index % 256
        self.total += violation - self.history[slot]
        self.history[slot] = violation
        self.index += 1
