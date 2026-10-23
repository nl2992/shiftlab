"""Population-level oracle checks for the paired decision-harm benchmark."""

from __future__ import annotations

import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr, ndtri


def gaussian_threshold_excess_risk(
    scenario: str,
    *,
    noise: float = 0.3,
    severity: float = 1.5,
    false_negative_cost: float = 5.0,
    false_positive_cost: float = 1.0,
    integration_tolerance: float = 1e-11,
) -> float:
    """Integrate population excess cost for the benchmark's fixed threshold policies.

    The score ``S = X0 - .9 X1`` is Normal(0, 1.81). The reference predicts positive
    when the *source* posterior exceeds the asymmetric-cost threshold; the incumbent
    predicts positive at source posterior 1/2. The supported scenarios change only the
    conditional outcome law or nuisance coordinates, so this one-dimensional integral
    is exact up to Gauss-Hermite quadrature error.
    """
    supported = {"stationary", "benign_nuisance", "boundary_local_harm", "residual_variance"}
    if scenario not in supported:
        raise ValueError(f"scenario must be one of {sorted(supported)}")
    if not np.isfinite(noise) or noise <= 0:
        raise ValueError("noise must be finite and positive")
    if not np.isfinite(severity) or severity < 0:
        raise ValueError("severity must be finite and nonnegative")
    if (
        not np.isfinite(false_negative_cost)
        or not np.isfinite(false_positive_cost)
        or false_negative_cost <= 0
        or false_positive_cost <= 0
    ):
        raise ValueError("decision costs must be finite and positive")
    cost_threshold = false_positive_cost / (false_negative_cost + false_positive_cost)
    if not np.isfinite(integration_tolerance) or integration_tolerance <= 0:
        raise ValueError("integration_tolerance must be finite and positive")
    source_boundary = float(noise * ndtri(cost_threshold))
    score_sd = np.sqrt(1.81)

    def integrand(score: float) -> float:
        source_probability = float(ndtr(score / noise))
        if scenario == "boundary_local_harm":
            probability = float(ndtr((score + severity * np.exp(-5 * abs(score))) / noise))
        elif scenario == "residual_variance":
            probability = float(ndtr(score / (noise * (1 + severity))))
        else:
            probability = source_probability
        incumbent_action = score >= 0
        reference_action = source_probability >= cost_threshold
        incumbent_cost = (
            false_positive_cost * (1 - probability)
            if incumbent_action
            else false_negative_cost * probability
        )
        reference_cost = (
            false_positive_cost * (1 - probability)
            if reference_action
            else false_negative_cost * probability
        )
        density = np.exp(-0.5 * (score / score_sd) ** 2) / (score_sd * np.sqrt(2 * np.pi))
        return float((incumbent_cost - reference_cost) * density)

    # Split at both action boundaries (and the local-shift cusp at zero) so adaptive
    # integration does not smear the discontinuous policy indicator.
    segments = ((-np.inf, source_boundary), (source_boundary, 0.0), (0.0, np.inf))
    return float(
        sum(
            quad(integrand, left, right, epsabs=integration_tolerance)[0]
            for left, right in segments
        )
    )


def source_threshold_score(
    *, noise: float = 0.3, false_negative_cost: float = 5.0, false_positive_cost: float = 1.0
) -> float:
    """Return the score boundary of the cost-optimal source reference policy."""
    threshold = false_positive_cost / (false_negative_cost + false_positive_cost)
    return float(noise * ndtri(threshold))
