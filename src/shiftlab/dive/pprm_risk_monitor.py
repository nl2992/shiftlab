"""Prediction-powered monitoring of one model's predictive risk.

This module implements the PPRM estimand and PPI batch estimator from Zhang
et al. (ICML 2026). It uses a one-sided Waudby-Smith/Ramdas betting upper
confidence bound for the source risk and the repository's finite-mixture
CM-EB lower confidence sequence for test risk. It does not monitor paired
decision cost.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from .eprocess import PPIBlockConfidenceSequence


def _bounded_vector(values: np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.ndim != 1 or array.size == 0:
        raise ValueError(f"{name} must be a nonempty one-dimensional array")
    if not np.isfinite(array).all() or np.any(array < 0) or np.any(array > 1):
        raise ValueError(f"{name} must contain finite losses in [0, 1]")
    return array


@dataclass(frozen=True)
class PPRMBatchEstimate:
    """One round's prediction-powered estimate and predictable coefficient."""

    estimate: float
    reliance: float
    labeled_count: int
    unlabeled_count: int


def prediction_powered_batch_risk(
    true_labeled_loss: np.ndarray,
    proxy_labeled_loss: np.ndarray,
    proxy_unlabeled_loss: np.ndarray,
    *,
    reliance: float,
) -> PPRMBatchEstimate:
    """Compute ``eta * mean(proxy_U) + mean(true_L - eta * proxy_L)``.

    Callers are responsible for ensuring that labeled and unlabeled samples
    are disjoint, conditionally independent, and drawn from the same round
    distribution, as required by the PPRM unbiasedness argument.
    """
    true_loss = _bounded_vector(true_labeled_loss, name="true_labeled_loss")
    proxy_labeled = _bounded_vector(proxy_labeled_loss, name="proxy_labeled_loss")
    proxy_unlabeled = _bounded_vector(proxy_unlabeled_loss, name="proxy_unlabeled_loss")
    if true_loss.shape != proxy_labeled.shape:
        raise ValueError("true and proxy labeled loss arrays must have equal length")
    if not np.isfinite(reliance) or reliance < 0:
        raise ValueError("reliance must be finite and nonnegative")
    estimate = reliance * float(proxy_unlabeled.mean()) + float(
        (true_loss - reliance * proxy_labeled).mean()
    )
    return PPRMBatchEstimate(
        estimate=estimate,
        reliance=float(reliance),
        labeled_count=int(true_loss.size),
        unlabeled_count=int(proxy_unlabeled.size),
    )


def source_prediction_powered_values(
    true_labeled_loss: np.ndarray,
    proxy_labeled_loss: np.ndarray,
    proxy_unlabeled_loss: np.ndarray,
    *,
    reliance: float = 1.0,
) -> np.ndarray:
    """Return source per-sample PPI values using disjoint equal-size U blocks.

    This is the construction in Appendix A.2: every labeled source example is
    paired with a disjoint block of unlabeled proxy losses. Equal block sizes
    are required so that the mean of returned values equals the source PPI
    estimator.
    """
    true_loss = _bounded_vector(true_labeled_loss, name="true_labeled_loss")
    proxy_labeled = _bounded_vector(proxy_labeled_loss, name="proxy_labeled_loss")
    proxy_unlabeled = _bounded_vector(proxy_unlabeled_loss, name="proxy_unlabeled_loss")
    if true_loss.shape != proxy_labeled.shape:
        raise ValueError("true and proxy labeled loss arrays must have equal length")
    n = true_loss.size
    if proxy_unlabeled.size % n:
        raise ValueError("source unlabeled count must be divisible by labeled count")
    if not np.isfinite(reliance) or reliance < 0:
        raise ValueError("reliance must be finite and nonnegative")
    block_size = proxy_unlabeled.size // n
    blocks = proxy_unlabeled.reshape(n, block_size)
    return reliance * blocks.mean(axis=1) + true_loss - reliance * proxy_labeled


class PPRMRiskMonitor:
    """Monitor running predictive risk relative to a source-risk upper bound.

    The test confidence sequence is the published CM-EB construction using a
    finite discrete mixing distribution. The ``source_upper_bound`` must have
    been computed from an independent nominal sample and a disjoint source
    unlabeled pool. The class cannot check those sampling conditions.
    """

    def __init__(
        self,
        *,
        source_upper_bound: float,
        tolerance: float,
        max_reliance: float,
        alpha_test: float = 0.025,
        lambda_count: int = 128,
        root_iterations: int = 48,
    ) -> None:
        if not np.isfinite(source_upper_bound) or not 0 <= source_upper_bound <= 1:
            raise ValueError("source_upper_bound must lie in [0, 1]")
        if not np.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and nonnegative")
        if not np.isfinite(max_reliance) or max_reliance < 0:
            raise ValueError("max_reliance must be finite and nonnegative")
        if source_upper_bound + tolerance > 1:
            raise ValueError("source upper bound plus tolerance cannot exceed one")
        self.source_upper_bound = float(source_upper_bound)
        self.tolerance = float(tolerance)
        self.threshold = self.source_upper_bound + self.tolerance
        self.max_reliance = float(max_reliance)
        self.alpha_test = float(alpha_test)
        self.sequence = PPIBlockConfidenceSequence(
            max_reliance=max_reliance,
            threshold=self.threshold,
            alpha=alpha_test,
            lambda_count=lambda_count,
            root_iterations=root_iterations,
        )
        self.estimates: list[PPRMBatchEstimate] = []

    @property
    def lower_bound(self) -> float:
        return self.sequence.lower_bound

    @property
    def alarm(self) -> bool:
        return self.sequence.alarm

    def update(self, batch: PPRMBatchEstimate) -> bool:
        """Add one completed test round; return whether PPRM's threshold crossed."""
        if batch.reliance > self.max_reliance + 1e-12:
            raise ValueError("round reliance exceeds the predeclared maximum")
        self.estimates.append(batch)
        return self.sequence.update(batch.estimate)


class PredictableReliance:
    """Sliding-window plug-in eta from Eq. (27) of the PPRM paper.

    ``choose`` must be called before inspecting the current round. ``update``
    is called only after its labels and both proxy-loss batches are available,
    so the next coefficient is history-predictable.
    """

    def __init__(
        self,
        *,
        window_rounds: int = 60,
        max_reliance: float = 1.0,
        initial_reliance: float = 1.0,
        minimum_variance: float = 1e-12,
    ) -> None:
        if (
            isinstance(window_rounds, bool)
            or not isinstance(window_rounds, int)
            or window_rounds < 1
        ):
            raise ValueError("window_rounds must be a positive integer")
        if not np.isfinite(max_reliance) or max_reliance < 0:
            raise ValueError("max_reliance must be finite and nonnegative")
        if not np.isfinite(initial_reliance) or not 0 <= initial_reliance <= max_reliance:
            raise ValueError("initial_reliance must lie in [0, max_reliance]")
        if not np.isfinite(minimum_variance) or minimum_variance <= 0:
            raise ValueError("minimum_variance must be finite and positive")
        self.window_rounds = window_rounds
        self.max_reliance = float(max_reliance)
        self.initial_reliance = float(initial_reliance)
        self.minimum_variance = float(minimum_variance)
        self._history: deque[tuple[np.ndarray, np.ndarray, np.ndarray]] = deque(
            maxlen=window_rounds
        )

    def choose(self, *, labeled_count: int, unlabeled_count: int) -> float:
        if labeled_count <= 0 or unlabeled_count <= 0:
            raise ValueError("each PPRM round requires positive labeled and unlabeled counts")
        if not self._history:
            return self.initial_reliance
        true_labeled = np.concatenate([row[0] for row in self._history])
        proxy_labeled = np.concatenate([row[1] for row in self._history])
        proxy_unlabeled = np.concatenate([row[2] for row in self._history])
        if true_labeled.size < 2 or proxy_unlabeled.size < 2:
            return self.initial_reliance
        covariance = float(np.cov(true_labeled, proxy_labeled, ddof=1)[0, 1])
        proxy_variance = float(np.var(proxy_unlabeled, ddof=1))
        if not np.isfinite(covariance) or not np.isfinite(proxy_variance):
            return self.initial_reliance
        if proxy_variance <= self.minimum_variance:
            return 0.0
        ratio = 1.0 + true_labeled.size / proxy_unlabeled.size
        eta = covariance / (ratio * proxy_variance)
        return float(np.clip(eta, 0.0, self.max_reliance))

    def update(
        self,
        true_labeled_loss: np.ndarray,
        proxy_labeled_loss: np.ndarray,
        proxy_unlabeled_loss: np.ndarray,
    ) -> None:
        true_loss = _bounded_vector(true_labeled_loss, name="true_labeled_loss")
        proxy_labeled = _bounded_vector(proxy_labeled_loss, name="proxy_labeled_loss")
        proxy_unlabeled = _bounded_vector(proxy_unlabeled_loss, name="proxy_unlabeled_loss")
        if true_loss.shape != proxy_labeled.shape:
            raise ValueError("true and proxy labeled loss arrays must have equal length")
        self._history.append((true_loss.copy(), proxy_labeled.copy(), proxy_unlabeled.copy()))


def source_risk_upper_bound_cm_eb(
    source_ppi_values: np.ndarray,
    *,
    max_reliance: float,
    alpha_source: float = 0.025,
    lambda_count: int = 128,
    root_iterations: int = 48,
) -> float:
    """Compute a CM-EB upper bound for the source PPI mean.

    The paper's default uses a betting bound. This implementation reuses the
    valid CM-EB lower sequence on the reflected, normalized source values. It
    is an explicit efficiency-method deviation while retaining a time-uniform
    source bound under independent bounded source PPI values.
    """
    values = np.asarray(source_ppi_values, dtype=np.float64)
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        raise ValueError("source_ppi_values must be finite, one-dimensional, and length >= 2")
    if not np.isfinite(max_reliance) or max_reliance < 0:
        raise ValueError("max_reliance must be finite and nonnegative")
    lo, hi = -max_reliance, 1 + max_reliance
    if np.any(values < lo - 1e-12) or np.any(values > hi + 1e-12):
        raise ValueError("source PPI value is outside its declared support")
    normalized = (values + max_reliance) / (1 + 2 * max_reliance)
    reflected = 1.0 - normalized
    lower_sequence = PPIBlockConfidenceSequence(
        max_reliance=0,
        threshold=0,
        alpha=alpha_source,
        lambda_count=lambda_count,
        root_iterations=root_iterations,
    )
    for value in reflected:
        lower_sequence.update(float(value))
    upper_normalized = 1.0 - lower_sequence.lower_bound
    return float(np.clip(-max_reliance + (1 + 2 * max_reliance) * upper_normalized, 0, 1))


def source_risk_upper_bound_betting(
    source_ppi_values: np.ndarray,
    *,
    max_reliance: float,
    alpha_source: float = 0.025,
    grid_size: int = 1000,
    truncation: float = 0.5,
) -> float:
    """Betting-based one-sided upper confidence bound for source PPI risk.

    The implementation follows the one-sided ``betting_cs`` construction in
    ConfSeq's MIT-licensed ``betting.py`` (Waudby-Smith and Ramdas, 2024):
    predictable plug-in empirical-Bernstein bets are inverted over candidate
    means. The first-crossing point is the first rejected candidate and thus
    the upper endpoint; the source PPI values must be independent and bounded.
    """
    values = np.asarray(source_ppi_values, dtype=np.float64)
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        raise ValueError("source_ppi_values must be finite, one-dimensional, and length >= 2")
    if not np.isfinite(max_reliance) or max_reliance < 0:
        raise ValueError("max_reliance must be finite and nonnegative")
    if not 0 < alpha_source < 1:
        raise ValueError("alpha_source must lie in (0, 1)")
    if isinstance(grid_size, bool) or not isinstance(grid_size, int) or grid_size < 2:
        raise ValueError("grid_size must be an integer of at least two")
    if not np.isfinite(truncation) or not 0 < truncation <= 1:
        raise ValueError("truncation must lie in (0, 1]")
    lo, hi = -max_reliance, 1 + max_reliance
    if np.any(values < lo - 1e-12) or np.any(values > hi + 1e-12):
        raise ValueError("source PPI value is outside its declared support")

    observations = (values + max_reliance) / (1 + 2 * max_reliance)
    time = np.arange(1, observations.size + 1, dtype=np.float64)
    cumulative = np.cumsum(observations)
    predicted_mean = (0.5 + cumulative) / (time + 1.0)
    variance = (0.25 + np.cumsum((observations - predicted_mean) ** 2)) / (time + 1.0)
    variance_before = np.concatenate(([0.25], variance[:-1]))
    base_bets = np.sqrt(
        2.0 * np.log(1.0 / alpha_source) / (time * np.log1p(time) * variance_before)
    )
    candidates = np.arange(grid_size, dtype=np.float64) / grid_size
    log_threshold = np.log(1.0 / alpha_source)
    for candidate in candidates:
        if candidate >= 1.0:
            continue
        bets = np.minimum(base_bets, truncation / (1.0 - candidate))
        log_wealth = float(np.log1p(bets * (candidate - observations)).sum())
        if log_wealth >= log_threshold:
            upper_normalized = candidate
            return float(
                np.clip(
                    -max_reliance + (1 + 2 * max_reliance) * upper_normalized,
                    0.0,
                    1.0,
                )
            )
    return 1.0
