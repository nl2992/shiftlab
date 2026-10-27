"""Paper-driven independent implementation of the UPF cost decision rule.

This module implements the finite-horizon quantile recursion described in
Regol et al. (ICML 2025). It does not implement the paper's Proposition 3.1,
which is audited separately in ``scripts/audit_upf_retrain_count_bound.py``.
The forecaster is fitted only on performance entries supplied by the caller;
callers are responsible for passing entries available by the decision time.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch
from sklearn.linear_model import ElasticNetCV


@dataclass(frozen=True)
class PerformanceObservation:
    """One observed bounded model loss and the period when its label matured."""

    training_period: int
    evaluation_period: int
    feature_shift_l1: float
    normalized_loss: float
    available_period: int


def build_upf_features(
    training_period: np.ndarray,
    evaluation_period: np.ndarray,
    feature_shift_l1: float | np.ndarray,
) -> np.ndarray:
    """Construct the paper's [i, j, j-i, z_shift] feature vectors."""
    train = np.asarray(training_period)
    evaluate = np.asarray(evaluation_period)
    shift = np.asarray(feature_shift_l1, dtype=np.float64)
    if train.ndim != 1 or evaluate.shape != train.shape:
        raise ValueError("training_period and evaluation_period must be matching vectors")
    if not np.issubdtype(train.dtype, np.integer) or not np.issubdtype(evaluate.dtype, np.integer):
        raise ValueError("period indices must be integers")
    if np.any(train < 0) or np.any(evaluate < train):
        raise ValueError("periods must satisfy 0 <= training_period <= evaluation_period")
    if shift.ndim == 0:
        shift = np.full(len(train), float(shift), dtype=np.float64)
    if shift.shape != train.shape or not np.isfinite(shift).all() or np.any(shift < 0):
        raise ValueError("feature_shift_l1 must be finite, nonnegative, and match periods")
    return np.column_stack((train, evaluate, evaluate - train, shift)).astype(
        np.float64, copy=False
    )


@dataclass(frozen=True)
class BetaPerformanceForecaster:
    """Elastic-net mean forecast and constant residual variance."""

    model: ElasticNetCV
    residual_variance: float
    n_observations: int

    def predict_beta_parameters(
        self,
        features: np.ndarray,
        *,
        epsilon: float = 1e-5,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Predict bounded Beta parameters using the paper's moment conversion."""
        x = np.asarray(features, dtype=np.float64)
        if x.ndim != 2 or x.shape[1] != 4 or not np.isfinite(x).all():
            raise ValueError("features must be a finite (n, 4) array")
        if not 0 < epsilon < 0.01:
            raise ValueError("epsilon must lie in (0, 0.01)")
        mean = np.clip(self.model.predict(x), epsilon, 1 - epsilon)
        maximum_variance = mean * (1 - mean) * 0.99
        variance = np.minimum(max(self.residual_variance, epsilon**2), maximum_variance)
        concentration = mean * (1 - mean) / variance - 1
        concentration = np.maximum(concentration, epsilon)
        alpha = np.maximum(mean * concentration, epsilon)
        beta = np.maximum((1 - mean) * concentration, epsilon)
        if not np.isfinite(alpha).all() or not np.isfinite(beta).all():
            raise FloatingPointError("Beta parameter conversion was nonfinite")
        return alpha, beta


def fit_beta_performance_forecaster(
    features: np.ndarray,
    losses: np.ndarray,
    *,
    seed: int = 0,
    max_cv: int = 5,
) -> BetaPerformanceForecaster:
    """Fit ElasticNetCV to observed [0,1] losses with a constant Gaussian variance."""
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(losses, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 4 or len(x) != len(y):
        raise ValueError("expected matching features (n, 4) and losses (n,)")
    if len(y) < 3 or max_cv < 2:
        raise ValueError("at least three observations and max_cv >= 2 are required")
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("forecaster data must be finite")
    if np.any((y < 0) | (y > 1)):
        raise ValueError("UPF Beta losses must lie in [0, 1]")
    cv = min(max_cv, len(y))
    model = ElasticNetCV(cv=cv, random_state=seed, max_iter=50_000)
    model.fit(x, y)
    residual = y - model.predict(x)
    residual_variance = float(np.mean(np.square(residual)))
    if not np.isfinite(residual_variance):
        raise FloatingPointError("forecaster residual variance was nonfinite")
    return BetaPerformanceForecaster(model, residual_variance, len(y))


def fit_available_performance_forecaster(
    observations: Sequence[PerformanceObservation],
    *,
    max_available_period: int,
    seed: int = 0,
) -> BetaPerformanceForecaster:
    """Fit only losses mature by the caller's stated decision-time cutoff."""
    if (
        isinstance(max_available_period, bool)
        or not isinstance(max_available_period, int)
        or max_available_period < 0
    ):
        raise ValueError("max_available_period must be a nonnegative integer")
    eligible: list[PerformanceObservation] = []
    for observation in observations:
        values = (
            observation.training_period,
            observation.evaluation_period,
            observation.available_period,
        )
        if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
            raise ValueError("observation periods must be integers")
        if (
            observation.training_period < 0
            or observation.evaluation_period < observation.training_period
            or observation.available_period < observation.evaluation_period
        ):
            raise ValueError("observations must have valid training/evaluation/availability order")
        if not np.isfinite(observation.feature_shift_l1) or observation.feature_shift_l1 < 0:
            raise ValueError("feature_shift_l1 must be finite and nonnegative")
        if (
            not np.isfinite(observation.normalized_loss)
            or not 0 <= observation.normalized_loss <= 1
        ):
            raise ValueError("normalized_loss must lie in [0, 1]")
        if observation.available_period <= max_available_period:
            eligible.append(observation)
    if len(eligible) < 3:
        raise ValueError("fewer than three eligible observations are available by the cutoff")
    features = build_upf_features(
        np.asarray([item.training_period for item in eligible], dtype=np.int64),
        np.asarray([item.evaluation_period for item in eligible], dtype=np.int64),
        np.asarray([item.feature_shift_l1 for item in eligible], dtype=np.float64),
    )
    losses = np.asarray([item.normalized_loss for item in eligible], dtype=np.float64)
    return fit_beta_performance_forecaster(features, losses, seed=seed)


def upf_retraining_schedule(
    alpha_beta: np.ndarray,
    beta_beta: np.ndarray,
    *,
    retraining_cost: float,
    quantile: float = 0.95,
    monte_carlo_draws: int = 20_000,
    seed: int = 0,
    device: str | torch.device = "cpu",
) -> tuple[np.ndarray, np.ndarray]:
    """Compute the paper's deterministic quantile policy by backward recursion.

    Parameters use a triangular performance matrix indexed as ``[model, time]``:
    model 0 is the initial incumbent; a model trained at time ``t`` is model
    index ``t``. Columns represent test periods 1..T. Only cells with
    ``model <= time`` are sampled. The returns are the selected retraining bit
    for each ``(time, incumbent_model)`` state and the Monte Carlo quantile
    comparison margins for those states. The first action from the current
    state should be applied; callers may update the forecaster and recompute
    after new feedback arrives.

    Performance cells are sampled independently, matching the factorization
    assumed in the paper. Torch performs sampling on CUDA when requested and
    available; the forecaster itself is intentionally the paper's small
    ElasticNetCV model on CPU.
    """
    alpha = np.asarray(alpha_beta, dtype=np.float64)
    beta = np.asarray(beta_beta, dtype=np.float64)
    if alpha.ndim != 2 or alpha.shape != beta.shape:
        raise ValueError("alpha and beta must be same-shape 2D triangular matrices")
    horizon = alpha.shape[1]
    if horizon < 1 or alpha.shape[0] != horizon + 1:
        raise ValueError("parameter matrices must have shape (T + 1, T)")
    if (
        not np.isfinite(alpha).all()
        or not np.isfinite(beta).all()
        or np.any(alpha <= 0)
        or np.any(beta <= 0)
    ):
        raise ValueError("Beta parameters must be finite and positive")
    if not np.isfinite(retraining_cost) or retraining_cost < 0:
        raise ValueError("retraining_cost must be finite and nonnegative")
    if not 0 < quantile < 1:
        raise ValueError("quantile must lie strictly between zero and one")
    if (
        isinstance(monte_carlo_draws, bool)
        or not isinstance(monte_carlo_draws, int)
        or monte_carlo_draws < 100
    ):
        raise ValueError("monte_carlo_draws must be an integer of at least 100")

    resolved_device = torch.device(device)
    if resolved_device.type == "cuda" and not torch.cuda.is_available():
        resolved_device = torch.device("cpu")
    parameter_a = torch.as_tensor(alpha, dtype=torch.float64, device=resolved_device)
    parameter_b = torch.as_tensor(beta, dtype=torch.float64, device=resolved_device)
    samples = torch.zeros(
        (horizon + 1, horizon, monte_carlo_draws),
        dtype=torch.float64,
        device=resolved_device,
    )
    rng_devices = (
        [resolved_device.index or torch.cuda.current_device()]
        if resolved_device.type == "cuda"
        else []
    )
    with torch.random.fork_rng(devices=rng_devices):
        torch.manual_seed(seed)
        if resolved_device.type == "cuda":
            torch.cuda.manual_seed_all(seed)
        for test_time in range(1, horizon + 1):
            for model_index in range(test_time + 1):
                distribution = torch.distributions.Beta(
                    parameter_a[model_index, test_time - 1],
                    parameter_b[model_index, test_time - 1],
                )
                samples[model_index, test_time - 1] = distribution.sample((monte_carlo_draws,))

    value = torch.zeros(
        (horizon + 2, horizon + 1, monte_carlo_draws),
        dtype=torch.float64,
        device=resolved_device,
    )
    schedule = np.zeros((horizon + 1, horizon + 1), dtype=bool)
    margins = np.zeros((horizon + 1, horizon + 1), dtype=np.float64)
    for test_time in range(horizon, 0, -1):
        for incumbent in range(test_time):
            keep = samples[incumbent, test_time - 1] + value[test_time + 1, incumbent]
            retrain = (
                retraining_cost
                + samples[test_time, test_time - 1]
                + value[test_time + 1, test_time]
            )
            keep_quantile = torch.quantile(keep, quantile)
            retrain_quantile = torch.quantile(retrain, quantile)
            retrain_now = bool((retrain_quantile < keep_quantile).item())
            schedule[test_time, incumbent] = retrain_now
            margins[test_time, incumbent] = float((keep_quantile - retrain_quantile).item())
            value[test_time, incumbent] = retrain if retrain_now else keep
    if resolved_device.type == "cuda":
        torch.cuda.synchronize(resolved_device)
    return schedule, margins
