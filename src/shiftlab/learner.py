"""Shared learner accepts no oracle metadata or future observations."""

import time
from collections import deque
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import Ridge

from .diagnostics import CUSUM, ks_test
from .methods import weighted_conformal_quantile as quantile


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
    def __init__(self, X, y, cal_X, cal_y, config, method, radius_method=None):
        self.config, self.method = LearnerSettings.from_config(config), method
        self.radius_method = radius_method or ("rolling" if method == "rolling" else "fixed")
        if self.radius_method not in {"fixed", "rolling"}:
            raise ValueError("radius_method must be 'fixed' or 'rolling'")
        self.training_seconds = self.inference_seconds = 0.0
        self._fit(X, y)
        pred = self.model.predict(cal_X)
        residual = cal_y - pred
        self.scores = deque(abs(residual), maxlen=config.window)
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
        radius = (
            quantile(self.scores, self.config.alpha)
            if self.radius_method == "rolling"
            else self.fixed_radius
        )
        return pred, radius

    def observe(self, feedback):
        self.feedback_count += 1
        self.scores.append(abs(feedback.target - feedback.prediction))
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
