"""WP3 past-only observation control and finite-horizon evidence replays."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from scipy.special import logsumexp

from .comparison_betting_engines import replay_engine
from .gated_monitor_comparison import DisagreementPacer
from .horizon_edetectors import HorizonCalibratedEDetector

HORIZON = 2400
ALPHA = 0.05
BOUND = 5.1
STAKES = (0.05, 0.1, 0.2, 0.4, 0.8, 1.0)
STARTS = (0, 600, 1200, 1800)
ENGINES = ("fixed1", "plugin", "timans_approx_grapa", "timans_grapa")


def optional_policy_replay(
    x: np.ndarray,
    active: np.ndarray,
    tariffs: np.ndarray,
    centered_cost: np.ndarray,
    uniforms: np.ndarray,
    *,
    validation_active: np.ndarray,
    validation_tariffs: np.ndarray,
    budget: float,
    policy: str,
) -> dict[str, Any]:
    """Replay one pre-current-X WP3 observation policy on a monitoring slice.

    The selection coin is resolved from a policy intensity based only on past
    monitor data and the disjoint validation pilot. Current disagreement,
    tariff and cost are used only after that choice. Selected agreements score
    ``-0.10`` without a label; selected disagreements reveal their centered
    cost; unselected events score zero. A hard-cap stop is triggered before
    observing the current event when less than the maximum tariff (2.5) remains.

    ``x`` is accepted as the monitoring feature matrix to make the information
    contract explicit. It is validated but never used by the controller.
    """
    features = np.asarray(x, dtype=float)
    disagreement = np.asarray(active, dtype=bool)
    cost = np.asarray(tariffs, dtype=float)
    outcome = np.asarray(centered_cost, dtype=float)
    coin = np.asarray(uniforms, dtype=float)
    pilot_active = np.asarray(validation_active, dtype=bool)
    pilot_cost = np.asarray(validation_tariffs, dtype=float)
    if features.ndim != 2 or not np.isfinite(features).all():
        raise ValueError("x must be a finite two-dimensional feature matrix")
    n = len(features)
    if any(array.shape != (n,) for array in (disagreement, cost, outcome, coin)):
        raise ValueError("monitor inputs must be matching one-dimensional vectors")
    if pilot_active.ndim != 1 or not len(pilot_active) or pilot_cost.shape != pilot_active.shape:
        raise ValueError("validation inputs must be matching nonempty vectors")
    if not np.isfinite(cost).all() or np.any((cost < 0.5) | (cost > 2.5)):
        raise ValueError("monitor tariffs must lie in [0.5, 2.5]")
    if not np.isfinite(pilot_cost).all() or np.any((pilot_cost < 0.5) | (pilot_cost > 2.5)):
        raise ValueError("validation tariffs must lie in [0.5, 2.5]")
    if not np.isfinite(outcome).all() or np.any(np.abs(outcome) > BOUND):
        raise ValueError("centered costs must be finite and bounded by 5.1")
    if not np.isfinite(coin).all() or np.any((coin < 0) | (coin >= 1)):
        raise ValueError("uniforms must lie in [0, 1)")
    if not np.isfinite(budget) or budget <= 0:
        raise ValueError("budget must be finite and positive")
    if policy not in {"uniform", "paced", "temporal", "candidate"}:
        raise ValueError("policy must be uniform, paced, temporal, or candidate")
    if n > HORIZON:
        raise ValueError("monitor input exceeds the registered 2400-event horizon")

    budget_rate = float(budget) / (HORIZON * float(pilot_cost.mean()))
    if not 0 < budget_rate <= 1:
        raise ValueError("budget implies a rate outside (0, 1]")
    pacer = DisagreementPacer(pilot_active, pilot_cost, budget_rate)
    detector = HorizonCalibratedEDetector(
        bound=BOUND,
        horizon=HORIZON,
        alpha=ALPHA,
        kind="sr",
        stakes=STAKES,
    )

    scores = np.zeros(n, dtype=float)
    selected = np.zeros(n, dtype=bool)
    labels = np.zeros(n, dtype=bool)
    theta = np.zeros(n, dtype=float)
    controller_log: list[dict[str, float | bool | None]] = []
    spent = 0.0
    stopped = False

    for t in range(n):
        log_r_previous = detector.log_statistic
        if policy == "uniform":
            base_theta = pacer.fixed
            multiplier = 1.0
        else:
            base_theta = pacer.propensity
            if policy == "temporal":
                multiplier = 0.25 if t < 1200 else 1.75
            elif policy == "candidate":
                evidence_fraction = np.clip(
                    (log_r_previous - math.log(t + 1)) / math.log(20), 0.0, 1.0
                )
                multiplier = float(0.25 + 3.75 * evidence_fraction)
            else:
                multiplier = 1.0

        planned_theta = float(np.clip(base_theta * multiplier, 0.01, 1.0))
        if not stopped and budget - spent < 2.5:
            stopped = True
        effective_theta = 0.0 if stopped else planned_theta
        theta[t] = effective_theta
        selected[t] = bool(coin[t] < effective_theta)
        if selected[t]:
            if disagreement[t]:
                labels[t] = True
                scores[t] = outcome[t]
                spent += float(cost[t])
            else:
                scores[t] = -0.10

        # Selection is made before current X. Only after it is fixed do current
        # disagreement and tariff enter the next-event pacer state.
        pacer.observe(bool(disagreement[t]), float(cost[t]))
        detector.update(float(scores[t]), skip=not selected[t])
        controller_log.append(
            {
                "calendar_index": float(t),
                "log_R_previous": (float(log_r_previous) if np.isfinite(log_r_previous) else None),
                "base_theta": float(base_theta),
                "multiplier": float(multiplier),
                "planned_theta": planned_theta,
                "theta": effective_theta,
                "selected": bool(selected[t]),
                "cap_stopped": stopped,
            }
        )

    return {
        "scores": scores,
        "selected": selected,
        "labels_mask": labels,
        "theta": theta,
        "labels": int(labels.sum()),
        "dollars": float(spent),
        "budget": float(budget),
        "budget_respected": bool(spent <= budget + 1e-9),
        "controller_log": controller_log,
        "cap_stop_index": next(
            (index for index, entry in enumerate(controller_log) if entry["cap_stopped"]),
            None,
        ),
    }


def _log_factors_to_detector(
    log_factors: np.ndarray, *, kind: str
) -> tuple[np.ndarray, int | None]:
    """Apply SR/CUSUM recursion to already-predictable one-step log factors."""
    component = -np.inf
    log_statistics = np.empty(len(log_factors), dtype=float)
    for t, log_factor in enumerate(log_factors):
        prior = np.logaddexp(0.0, component) if kind == "sr" else max(0.0, component)
        component = float(log_factor) + prior
        log_statistics[t] = component
    threshold = math.log(HORIZON / ALPHA)
    crossing = np.flatnonzero(log_statistics >= threshold)
    return log_statistics, int(crossing[0]) if len(crossing) else None


def _fixed_stake_detector(normalized: np.ndarray, *, kind: str) -> tuple[np.ndarray, int | None]:
    """Mix fixed-stake SR/CUSUM component statistics with equal weights."""
    with np.errstate(divide="ignore"):
        log_factors = np.log1p(normalized[:, None] * np.asarray(STAKES)[None, :])
    components = np.full(len(STAKES), -np.inf, dtype=float)
    log_statistics = np.empty(len(normalized), dtype=float)
    for t, factors in enumerate(log_factors):
        prior = np.logaddexp(0.0, components) if kind == "sr" else np.maximum(0.0, components)
        components = factors + prior
        log_statistics[t] = float(logsumexp(components) - math.log(len(STAKES)))
    threshold = math.log(HORIZON / ALPHA)
    crossing = np.flatnonzero(log_statistics >= threshold)
    return log_statistics, int(crossing[0]) if len(crossing) else None


def evidence_replays(
    values: np.ndarray,
    bounds: np.ndarray | float,
    skipmask: np.ndarray | None = None,
) -> dict[str, Any]:
    """Replay the frozen WP3 engines, horizon detectors and started mixtures.

    Paths shorter than 2400 calendar events are padded with factor-one skips.
    Every reported alarm index is zero-based calendar time. Started-engine
    paths restart the betting rule at each registered start; they are not
    obtained by differencing the global path.
    """
    observed = np.asarray(values, dtype=float)
    scale = np.asarray(bounds, dtype=float)
    if observed.ndim != 1 or not len(observed) or not np.isfinite(observed).all():
        raise ValueError("values must be a nonempty finite vector")
    if scale.ndim == 0:
        scale = np.full(len(observed), float(scale))
    if scale.shape != observed.shape or not np.isfinite(scale).all() or np.any(scale <= 0):
        raise ValueError("bounds must be positive finite and match values")
    if len(observed) > HORIZON:
        raise ValueError("values exceed the registered 2400-event horizon")
    if np.any(np.abs(observed) > scale):
        raise ValueError("a value is outside its declared bound")
    if skipmask is None:
        skipped = np.zeros(len(observed), dtype=bool)
    else:
        skipped = np.asarray(skipmask, dtype=bool)
        if skipped.shape != observed.shape:
            raise ValueError("skipmask must match values")

    actual_length = len(observed)
    padded_values = np.zeros(HORIZON, dtype=float)
    padded_bounds = np.full(HORIZON, float(scale[-1]), dtype=float)
    padded_skips = np.ones(HORIZON, dtype=bool)
    padded_values[:actual_length] = observed
    padded_bounds[:actual_length] = scale
    padded_skips[:actual_length] = skipped
    effective_values = padded_values.copy()
    effective_values[padded_skips] = 0.0

    engine_log_wealth: dict[str, np.ndarray] = {}
    one_step_log_factors: dict[str, np.ndarray] = {}
    fixed_start_paths: dict[str, np.ndarray] = {}
    started_paths: dict[str, dict[int, np.ndarray]] = {}
    started_mixtures: dict[str, np.ndarray] = {}

    for engine in ENGINES:
        wealth = replay_engine(effective_values, padded_bounds, engine, alpha=ALPHA)
        wealth = np.asarray(wealth, dtype=float)
        engine_log_wealth[engine] = wealth
        one_step = np.diff(np.concatenate(([0.0], wealth)))
        one_step[padded_skips] = 0.0
        one_step_log_factors[engine] = one_step
        fixed_start_paths[engine] = wealth.copy()

        starts_for_engine: dict[int, np.ndarray] = {}
        for start in STARTS:
            path = np.zeros(HORIZON, dtype=float)
            if start < HORIZON:
                replay = replay_engine(
                    effective_values[start:], padded_bounds[start:], engine, alpha=ALPHA
                )
                path[start:] = replay
            starts_for_engine[start] = path
        started_paths[engine] = starts_for_engine
        started_mixtures[engine] = logsumexp(
            np.stack(tuple(starts_for_engine.values())), axis=0
        ) - math.log(len(STARTS))

    detector_logs: dict[str, dict[str, np.ndarray]] = {"sr": {}, "cusum": {}}
    detector_alarms: dict[str, dict[str, int | None]] = {"sr": {}, "cusum": {}}
    for engine in ENGINES:
        if engine == "fixed1":
            normalized = effective_values / padded_bounds
            for kind in ("sr", "cusum"):
                path, alarm = _fixed_stake_detector(normalized, kind=kind)
                detector_logs[kind][engine] = path
                detector_alarms[kind][engine] = alarm
        else:
            for kind in ("sr", "cusum"):
                path, alarm = _log_factors_to_detector(one_step_log_factors[engine], kind=kind)
                detector_logs[kind][engine] = path
                detector_alarms[kind][engine] = alarm

    fixed_start_alarms = {
        engine: _first_crossing(path, -math.log(ALPHA))
        for engine, path in fixed_start_paths.items()
    }
    started_alarms = {
        engine: _first_crossing(path, -math.log(ALPHA)) for engine, path in started_mixtures.items()
    }
    return {
        "engine_log_wealth": engine_log_wealth,
        "one_step_log_factors": one_step_log_factors,
        "fixed_start_log_wealth": fixed_start_paths,
        "fixed_start_alarms": fixed_start_alarms,
        "started_log_wealth": started_paths,
        "started_mixture_log_wealth": started_mixtures,
        "started_mixture_alarms": started_alarms,
        "sr_log_statistics": detector_logs["sr"],
        "cusum_log_statistics": detector_logs["cusum"],
        "sr_alarms": detector_alarms["sr"],
        "cusum_alarms": detector_alarms["cusum"],
        "horizon_threshold": HORIZON / ALPHA,
        "started_mixture_threshold": 1 / ALPHA,
        "starts": STARTS,
        "engines": ENGINES,
        "horizon": HORIZON,
        "alpha": ALPHA,
        "actual_length": actual_length,
    }


def _first_crossing(log_values: np.ndarray, log_threshold: float) -> int | None:
    crossings = np.flatnonzero(np.asarray(log_values) >= log_threshold)
    return int(crossings[0]) if len(crossings) else None
