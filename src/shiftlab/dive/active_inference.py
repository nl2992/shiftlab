"""Fixed-horizon active-inference baseline for bounded paired-score means.

This is a task adaptation of Zrnic and Candes (ICML 2024), not an anytime-valid
monitor. It uses Bernoulli sampling with an expected label budget, as in the
paper's batch procedure; it does not promise a pathwise cap.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def active_inference_propensities(
    uncertainty: np.ndarray,
    *,
    expected_budget: float,
    uniform_mixture: float = 0.5,
) -> np.ndarray:
    """Calibrate the paper's clipped uncertainty rule and uniform mixture.

    ``uncertainty`` should estimate conditional residual scale for the target
    score. Scaling is chosen on the complete unlabeled batch so the expected
    number of queried labels is at most ``expected_budget``.
    """
    score = np.asarray(uncertainty, dtype=np.float64).reshape(-1)
    if score.size == 0 or not np.isfinite(score).all() or np.any(score < 0):
        raise ValueError("uncertainty must be a nonempty finite nonnegative vector")
    n = len(score)
    if not np.isfinite(expected_budget) or not 0 < expected_budget <= n:
        raise ValueError("expected_budget must lie in (0, batch size]")
    if not np.isfinite(uniform_mixture) or not 0 < uniform_mixture <= 1:
        raise ValueError("uniform_mixture must lie in (0, 1]")

    uniform_q = expected_budget / n
    if np.all(score == 0):
        return np.full(n, uniform_q)

    target = expected_budget
    if np.count_nonzero(score) <= target:
        # The uncertainty rule may have support smaller than the budget; its
        # largest feasible scale is the saturated rule, leaving budget unused.
        active_q = (score > 0).astype(np.float64)
    else:
        low, high = 0.0, 1.0
        while np.minimum(high * score, 1.0).sum() < target:
            high *= 2.0
        for _ in range(80):
            middle = (low + high) / 2.0
            if np.minimum(middle * score, 1.0).sum() <= target:
                low = middle
            else:
                high = middle
        active_q = np.minimum(low * score, 1.0)
    q = (1.0 - uniform_mixture) * active_q + uniform_mixture * uniform_q
    if np.any(q <= 0) or np.any(q > 1) or q.sum() > expected_budget + 1e-8:
        raise RuntimeError("calibrated active-inference propensities violate budget bounds")
    return q


def prediction_powered_mean(
    predictions: np.ndarray,
    query_indicators: np.ndarray,
    observed_scores: np.ndarray,
    propensities: np.ndarray,
    *,
    alpha: float = 0.05,
) -> dict[str, float]:
    """Return the augmented IPW mean and an asymptotic normal interval.

    ``observed_scores`` may contain NaN only at unqueried positions. The
    interval is a fixed-horizon CLT interval, not a finite-sample or sequential
    guarantee.
    """
    prediction = np.asarray(predictions, dtype=np.float64).reshape(-1)
    queried = np.asarray(query_indicators, dtype=bool).reshape(-1)
    observed = np.asarray(observed_scores, dtype=np.float64).reshape(-1)
    q = np.asarray(propensities, dtype=np.float64).reshape(-1)
    if not (len(prediction) == len(queried) == len(observed) == len(q)) or len(q) == 0:
        raise ValueError("predictions, query indicators, outcomes and propensities must align")
    if not np.isfinite(prediction).all() or not np.isfinite(q).all():
        raise ValueError("predictions and propensities must be finite")
    if np.any(q <= 0) or np.any(q > 1):
        raise ValueError("propensities must lie in (0, 1]")
    if np.any(np.isfinite(observed[~queried])):
        raise ValueError("unqueried outcomes must remain unavailable (NaN)")
    if not np.isfinite(observed[queried]).all():
        raise ValueError("every queried outcome must be observed and finite")
    if not 0 < alpha < 1:
        raise ValueError("alpha must lie in (0, 1)")

    increments = prediction.copy()
    increments[queried] += (observed[queried] - prediction[queried]) / q[queried]
    estimate = float(increments.mean())
    standard_error = float(increments.std(ddof=1) / np.sqrt(len(increments)))
    critical = float(norm.ppf(1.0 - alpha / 2.0))
    return {
        "estimate": estimate,
        "standard_error": standard_error,
        "lower": estimate - critical * standard_error,
        "upper": estimate + critical * standard_error,
        "labels_queried": float(queried.sum()),
        "expected_labels": float(q.sum()),
    }
