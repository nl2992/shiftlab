"""Outcome-predictable proxy for paired decision-loss contrasts."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge


class DecisionLossProxy:
    """Ridge proxy with a held-out conditional residual-second-moment model.

    Fit on historical outcomes only. The residual-variance model is fit on a separate
    historical validation slice to avoid the in-sample residual shrinkage of Ridge.
    """

    def __init__(
        self,
        *,
        alpha: float = 1.0,
        seed: int = 0,
        clip: float = 6.0,
        update_every: int = 20,
    ):
        if not np.isfinite(alpha) or alpha < 0:
            raise ValueError("alpha must be finite and nonnegative")
        if not np.isfinite(clip) or clip <= 0:
            raise ValueError("clip must be finite and positive")
        if isinstance(update_every, bool) or update_every < 1:
            raise ValueError("update_every must be a positive integer")
        self.alpha = float(alpha)
        self.seed = int(seed)
        self.clip = float(clip)
        self.model: Ridge | None = None
        self.variance_model: RandomForestRegressor | None = None
        self.diagnostics: dict[str, float] = {}
        self.update_every = int(update_every)
        self._base_x: np.ndarray | None = None
        self._base_z: np.ndarray | None = None
        self._online_x: list[np.ndarray] = []
        self._online_z: list[float] = []

    def fit(
        self,
        x_train: np.ndarray,
        z_train: np.ndarray,
        x_validation: np.ndarray,
        z_validation: np.ndarray,
    ) -> DecisionLossProxy:
        x_train = self._features(x_train)
        x_validation = self._features(x_validation)
        z_train = self._targets(z_train, len(x_train))
        z_validation = self._targets(z_validation, len(x_validation))
        if len(x_train) < 2 or len(x_validation) < 2:
            raise ValueError("proxy training and validation each require at least two rows")
        self._base_x = x_train.copy()
        self._base_z = z_train.copy()
        self.model = Ridge(alpha=self.alpha).fit(x_train, z_train)
        validation_prediction = np.clip(self.model.predict(x_validation), -self.clip, self.clip)
        residual = z_validation - validation_prediction
        residual_square = np.clip(residual**2, 0, (2 * self.clip) ** 2)
        self.variance_model = RandomForestRegressor(
            n_estimators=64,
            max_depth=8,
            min_samples_leaf=max(5, min(30, len(x_validation) // 20)),
            max_features=1.0,
            n_jobs=1,
            random_state=self.seed,
        ).fit(x_validation, residual_square)
        self.diagnostics = {
            "validation_rmse": float(np.sqrt(np.mean(residual**2))),
            "validation_residual_second_moment": float(np.mean(residual_square)),
            "validation_proxy_mean": float(np.mean(validation_prediction)),
        }
        return self

    def observe(self, x: np.ndarray, z: float) -> bool:
        """Incorporate one arrived, queried outcome after the current prediction.

        Call only when feedback actually arrives. In delayed-feedback simulations this
        method must be called at availability time, never at prediction time.
        Returns true when the proxy was refitted.
        """
        if self.model is None or self._base_x is None or self._base_z is None:
            raise RuntimeError("proxy must be fitted before online updates")
        row = self._features(np.asarray(x, dtype=float).reshape(1, -1))
        if not np.isfinite(z):
            raise ValueError("arrived target must be finite")
        self._online_x.append(row[0].copy())
        self._online_z.append(float(np.clip(z, -self.clip, self.clip)))
        if len(self._online_z) % self.update_every:
            return False
        x_all = np.concatenate([self._base_x, np.asarray(self._online_x)])
        z_all = np.concatenate([self._base_z, np.asarray(self._online_z)])
        self.model = Ridge(alpha=self.alpha).fit(x_all, z_all)
        return True

    def predict(self, x: np.ndarray) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("proxy must be fitted before prediction")
        return np.clip(self.model.predict(self._features(x)), -self.clip, self.clip)

    def predict_residual_second_moment(self, x: np.ndarray) -> np.ndarray:
        if self.variance_model is None:
            raise RuntimeError("proxy must be fitted before variance prediction")
        predictions = self.variance_model.predict(self._features(x))
        return np.clip(predictions, 1e-8, (2 * self.clip) ** 2)

    @staticmethod
    def _features(values: np.ndarray) -> np.ndarray:
        values = np.asarray(values, dtype=float)
        if values.ndim != 2 or values.shape[0] == 0 or not np.isfinite(values).all():
            raise ValueError("features must be a nonempty finite 2D array")
        return values

    @staticmethod
    def _targets(values: np.ndarray, rows: int) -> np.ndarray:
        values = np.asarray(values, dtype=float).reshape(-1)
        if len(values) != rows or not np.isfinite(values).all():
            raise ValueError("targets must be finite and match the feature rows")
        return values
