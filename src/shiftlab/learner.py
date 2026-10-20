"""Shared learner accepts no oracle metadata or future observations."""

import time
from collections import deque
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import Ridge

from .diagnostics import CUSUM, ks_test
from .methods import (
    exponentially_weighted_conformal_quantile,
)
from .methods import (
    weighted_conformal_quantile as quantile,
)


def decision_losses(y, pred):
    return 5 * ((y >= 0) & (pred < 0)) + 1 * ((y < 0) & (pred >= 0))


@dataclass(frozen=True)
class LearnerSettings:
    """Operational parameters only: no true changepoint or regime information."""

    window: int
    alpha: float
    threshold: float
    period: int
    budget: int

    @classmethod
    def from_config(cls, config):
        return cls(config.window, config.alpha, config.threshold, config.period, config.budget)


class Learner:
    def __init__(
        self,
        X,
        y,
        cal_X,
        cal_y,
        config,
        method,
        radius_method=None,
        cal_score_times=None,
        radius_half_life=None,
    ):
        self.config, self.method = LearnerSettings.from_config(config), method
        self.radius_method = radius_method or ("rolling" if method == "rolling" else "fixed")
        if self.radius_method not in {"fixed", "rolling", "exponential"}:
            raise ValueError("radius_method must be 'fixed', 'rolling', or 'exponential'")
        self.radius_half_life = float(
            config.window if radius_half_life is None else radius_half_life
        )
        if not np.isfinite(self.radius_half_life) or self.radius_half_life <= 0:
            raise ValueError("radius_half_life must be finite and positive")
        self.training_seconds = self.inference_seconds = 0.0
        self._fit(X, y)
        pred = self.model.predict(cal_X)
        residual = cal_y - pred
        self.scores = deque(abs(residual), maxlen=config.window)
        if cal_score_times is None:
            if self.radius_method == "exponential":
                raise ValueError("cal_score_times are required for an exponential radius")
            initial_score_times = np.zeros(len(residual), dtype=float)
        else:
            initial_score_times = np.asarray(cal_score_times, dtype=float)
            if (
                initial_score_times.shape != residual.shape
                or not np.isfinite(initial_score_times).all()
            ):
                raise ValueError("cal_score_times must be finite and match calibration rows")
        self.score_times = deque(initial_score_times, maxlen=config.window)
        self.fixed_radius = quantile(abs(residual), config.alpha)
        self.reference = cal_X[-config.window :].copy()
        self.features = deque(maxlen=config.window)
        self.history = deque(zip(X.tolist(), y.tolist()), maxlen=config.window)
        costs = decision_losses(cal_y, pred)
        self.loss_detector = CUSUM(np.mean(costs), np.std(costs), config.threshold)
        self.error_detector = CUSUM(np.mean(residual**2), np.std(residual**2), config.threshold)
        self.alarms = {"ks": [], "loss_cusum": [], "error_cusum": []}
        self.interventions = []
        self.feedback_count = self.cooldown = 0

    def _fit(self, X, y):
        start = time.perf_counter()
        self.model = Ridge(alpha=1.0).fit(X, y)
        self.training_seconds += time.perf_counter() - start

    def predict(self, observation):
        x = np.asarray(observation.features)
        self.features.append(x)
        if (
            len(self.features) == self.config.window
            and observation.time % self.config.window == 0
            and ks_test(self.reference, np.asarray(self.features)) < 0.01
        ):
            self.alarms["ks"].append(observation.time)
        start = time.perf_counter()
        pred = float(self.model.predict(x[None, :])[0])
        self.inference_seconds += time.perf_counter() - start
        if self.radius_method == "rolling":
            radius = quantile(self.scores, self.config.alpha)
        elif self.radius_method == "exponential":
            score_times = np.asarray(self.score_times, dtype=float)
            prior = score_times < observation.time
            radius = exponentially_weighted_conformal_quantile(
                np.asarray(self.scores, dtype=float)[prior],
                observation.time - score_times[prior],
                self.config.alpha,
                self.radius_half_life,
            )
        else:
            radius = self.fixed_radius
        return pred, radius

    def observe(self, feedback):
        self.feedback_count += 1
        self.scores.append(abs(feedback.target - feedback.prediction))
        self.score_times.append(feedback.available_at)
        self.history.append((feedback.features, feedback.target))
        loss = float(
            decision_losses(np.array([feedback.target]), np.array([feedback.prediction]))[0]
        )
        if self.loss_detector.update(loss):
            self.alarms["loss_cusum"].append(feedback.available_at)
        alarm = self.error_detector.update((feedback.target - feedback.prediction) ** 2)
        if alarm:
            self.alarms["error_cusum"].append(feedback.available_at)
        self.cooldown = max(0, self.cooldown - 1)
        periodic = self.method == "periodic" and self.feedback_count % self.config.period == 0
        triggered = self.method == "triggered" and alarm and self.cooldown == 0
        if (periodic or triggered) and len(self.interventions) < self.config.budget:
            X, y = zip(*self.history)
            self._fit(np.asarray(X), np.asarray(y))
            self.interventions.append(feedback.available_at)
            self.cooldown = self.config.window
