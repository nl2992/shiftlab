"""Common replay interface for bounded-mean betting comparison baselines."""

from __future__ import annotations

from typing import Literal

import numpy as np

from .eprocess import (
    PredictablePlugInEmpiricalBernsteinEProcess,
    PredictableVarianceAdaptiveEProcess,
)
from .predictable_bound_replay import DEFAULT_STAKES, replay_mixture_log_e

Engine = Literal[
    "fixed08",
    "fixed1",
    "plugin",
    "pm_eb",
    "timans_approx_grapa",
    "timans_grapa",
]


def replay_engine(
    values: np.ndarray,
    bounds: np.ndarray | float,
    engine: Engine | str,
    alpha: float = 0.05,
) -> np.ndarray:
    """Replay one fixed bounded-mean betting engine on a common score path.

    ``bounds`` may be one positive scalar or a positive vector aligned with
    ``values``. Every score must lie in its declared bound. A vector of bounds
    is mathematically valid only when each bound is predictable with respect
    to the filtration in the asserted conditional-mean null. Being chosen
    before the label is not enough if the bound depends on a current covariate
    excluded from that null. The function checks numeric support only; it
    cannot establish predictability, the conditional-mean null, or feedback
    assumptions.

    Engines use the same normalized score ``values / bounds``. ``fixed08`` is
    the repository's default stake mixture; ``fixed1`` adds stake 1 to that
    grid with equal weights. ``plugin`` is the predictable variance-adaptive
    process capped at stake 0.99. ``pm_eb`` is the existing predictable
    plug-in empirical-Bernstein process. The two Timans engines replay the
    existing verified implementation on ``0.5 + 0.5 * values / bounds``, with
    epsilon 0.5 and its source default 100-event burn-in.

    Returns one log-wealth value per input event. For the Timans rules, the
    initial burn-in entries are zero as in the source replay.
    """
    observed = np.asarray(values, dtype=float)
    scale = np.asarray(bounds, dtype=float)
    if observed.ndim != 1 or not len(observed) or not np.isfinite(observed).all():
        raise ValueError("values must be a nonempty finite one-dimensional array")
    if scale.ndim == 0:
        scale = np.full_like(observed, float(scale))
    if scale.shape != observed.shape or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("bounds must be positive finite scalars or match values")
    if not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("alpha must lie strictly between zero and one")
    if engine not in {
        "fixed08",
        "fixed1",
        "plugin",
        "pm_eb",
        "timans_approx_grapa",
        "timans_grapa",
    }:
        raise ValueError(f"unsupported betting engine: {engine!r}")
    if np.any(np.abs(observed) > scale):
        raise ValueError("a value is outside its declared bound")

    normalized = observed / scale
    if engine == "fixed08":
        return replay_mixture_log_e(observed, scale, alpha=alpha)
    if engine == "fixed1":
        return replay_mixture_log_e(
            observed,
            scale,
            alpha=alpha,
            stakes=(*DEFAULT_STAKES, 1.0),
        )
    if engine == "plugin":
        process = PredictableVarianceAdaptiveEProcess(bound=1.0, alpha=alpha, max_stake=0.99)
        return np.asarray([process.update(float(value)) for value in normalized])
    if engine == "pm_eb":
        process = PredictablePlugInEmpiricalBernsteinEProcess(bound=1.0, alpha=alpha)
        return np.asarray([process.update(float(value)) for value in normalized])

    from scripts.reproduce_timans_risk_monitor_paired_cost import _timans_logs

    rule = "approx_grapa" if engine == "timans_approx_grapa" else "grapa"
    score = 0.5 + 0.5 * normalized
    return _timans_logs(
        score,
        rule=rule,
        epsilon=0.5,
        alpha=alpha,
        burn_in=100,
    )
