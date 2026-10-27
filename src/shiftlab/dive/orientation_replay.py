"""Replicate-vectorised replay of sparse-label harm monitors on one fixed data path.

Random orientation: an independent sign S_t in {-1,+1} swaps the deployed/reference roles, so the
monitor sees S_t * Z_t while the disagreement indicator is unchanged. Given the path and the past,
E[S_t Z_t] = 0, so any valid monitor alarms with probability at most alpha. The same code replays
injected-harm streams (signs=None or a modified paired cost).

Every arm reproduces the scalar reference implementations (``replay_gated`` and the
``eprocess`` classes) in the same floating-point operation order: fixed-stake log wealth is a
cumulative sum, and the empirical-Bernstein recursion is expressed through cumulative sums of
quantities that do not depend on the process state.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .eprocess import PredictableBoundMeanEProcess
from .gated_monitor_comparison import DisagreementPacer

ARMS = ("full_feedback", "ungated_ht", "gated_ht_fixed", "gated_ht_paced", "gated_eb_paced")
_GATED = ("gated_ht_fixed", "gated_ht_paced", "gated_eb_paced")
_STAKES = (0.05, 0.1, 0.2, 0.4, 0.8)
_CHUNK = 64
_MAX_TARIFF = 2.5


@dataclass(frozen=True)
class ReplayBatch:
    first_alarm: np.ndarray  # (R,) int64, -1 if none
    labels: np.ndarray  # (R,) int64 queried events processed
    dollars: np.ndarray  # (R,) float64 spent
    processed: np.ndarray  # (R,) int64 events processed before the reserve stop
    max_log_e: np.ndarray  # (R,) float64 over processed events (-inf if none processed)


def _mixture_log_e(ratio: np.ndarray) -> np.ndarray:
    """Log of the equal-weight stake mixture for ratios value/bound, shape (c, n)."""
    log_weight = np.log(np.full(len(_STAKES), 1 / len(_STAKES)))
    wealth = [
        np.cumsum(np.log(1 + stake * ratio), axis=1) + log_weight[k]
        for k, stake in enumerate(_STAKES)
    ]
    top = wealth[0].copy()
    for w in wealth[1:]:
        np.maximum(top, w, out=top)
    total = np.zeros_like(top)
    for w in wealth:
        total += np.exp(w - top)
    return top + np.log(total)


def _eb_log_e(ratio: np.ndarray, alpha: float, max_stake: float = 0.5) -> np.ndarray:
    """PM-EB log wealth (bound 1) via cumulative sums; ratio is value/bound in [-1, 1]."""
    n = ratio.shape[1]
    obs = 0.5 * (ratio / 1.0 + 1)
    time = np.arange(1, n + 1, dtype=float)
    mean = (0.5 + np.cumsum(obs, axis=1)) / (time + 1)
    dev = np.cumsum((obs - mean) ** 2, axis=1)
    variance = (0.25 + dev) / (time + 1)
    prev_mean = np.concatenate([np.full((len(obs), 1), 0.5), mean[:, :-1]], axis=1)
    prev_var = np.concatenate([np.full((len(obs), 1), 0.25), variance[:, :-1]], axis=1)
    numerator = 2 * np.log(2 / alpha)
    stake = np.minimum(max_stake, np.sqrt(numerator / (prev_var * time * np.log1p(time))))
    psi = (-np.log1p(-stake) - stake) / 4
    increment = stake * (obs - 0.5) - 4 * (obs - prev_mean) ** 2 * psi
    return np.cumsum(increment, axis=1)


def _propensity_path(arm, active, tariffs, v_active, v_tariffs, budget_rate):
    pacer = DisagreementPacer(v_active, v_tariffs, budget_rate)
    n = len(active)
    q = np.empty(n)
    for i in range(n):
        q[i] = pacer.fixed if arm == "gated_ht_fixed" else pacer.propensity
        pacer.observe(bool(active[i]), float(tariffs[i]))
    return q, pacer.target * n


def replay_batch(
    arm: str,
    *,
    paired_cost,
    disagreement,
    tariffs,
    signs,
    uniforms,
    validation_disagreement,
    validation_tariffs,
    budget_rate: float,
    epsilon: float = 0.1,
    alpha: float = 0.05,
    cost_bound: float = 5.0,
    device: str = "cpu",
) -> ReplayBatch:
    """Replay ``arm`` for R replicates of one path; see module docstring for semantics."""
    if arm not in ARMS:
        raise ValueError("unknown arm")
    if device != "cpu":
        raise ValueError("only the numpy cpu backend is implemented")
    z = np.asarray(paired_cost, dtype=float)
    active = np.asarray(disagreement, dtype=bool)
    prices = np.asarray(tariffs, dtype=float)
    if z.ndim != 1 or not len(z) or active.shape != z.shape or prices.shape != z.shape:
        raise ValueError("path arrays must be matching nonempty vectors")
    n = len(z)
    if not np.isfinite(z).all() or not np.isfinite(prices).all():
        raise ValueError("path arrays must be finite")
    if np.any((prices < 0.5) | (prices > _MAX_TARIFF)):
        raise ValueError("tariffs must lie in [0.5,2.5]")
    if not np.isfinite(cost_bound) or cost_bound <= 0:
        raise ValueError("cost_bound must be finite and positive")
    if arm in _GATED and cost_bound != 5.0:
        raise ValueError("gated arms hardcode the registered cost bound 5")
    if np.any(np.abs(z) > cost_bound):
        raise ValueError("paired cost must lie in [-cost_bound, cost_bound]")
    if np.any(z[~active] != 0):
        raise ValueError("paired cost must be exactly zero where there is no disagreement")
    if not np.isfinite(epsilon) or epsilon < 0 or not np.isfinite(alpha) or not 0 < alpha < 1:
        raise ValueError("epsilon must be nonnegative and alpha in (0,1)")
    if signs is None:
        sign_arr = None
    else:
        sign_arr = np.asarray(signs, dtype=float)
        if sign_arr.ndim != 2 or sign_arr.shape[1] != n or not np.all(np.abs(sign_arr) == 1):
            raise ValueError("signs must be (R,n) with entries in {-1,+1}")
    if arm == "full_feedback" and uniforms is None:
        coins = None
    else:
        if uniforms is None:
            raise ValueError("uniforms are required")
        coins = np.asarray(uniforms, dtype=float)
        if coins.ndim != 2 or coins.shape[1] != n:
            raise ValueError("uniforms must be (R,n)")
        if not np.isfinite(coins).all() or np.any((coins < 0) | (coins >= 1)):
            raise ValueError("query uniforms must lie in [0,1)")
    if sign_arr is not None and coins is not None and sign_arr.shape[0] != coins.shape[0]:
        raise ValueError("signs and uniforms must share the replicate count")
    if sign_arr is not None:
        reps = sign_arr.shape[0]
    elif coins is not None:
        reps = coins.shape[0]
    else:
        raise ValueError("full_feedback needs signs or uniforms to define the replicate count")

    vt = np.asarray(validation_tariffs, dtype=float)
    if arm == "full_feedback":
        q_path = np.ones(n)
        budget = np.inf
        bound_path = np.full(n, cost_bound + epsilon)
    elif arm == "ungated_ht":
        if vt.ndim != 1 or not len(vt) or not np.isfinite(vt).all():
            raise ValueError("validation tariffs must be a nonempty finite vector")
        if np.any((vt < 0.5) | (vt > _MAX_TARIFF)):
            raise ValueError("tariffs must lie in [0.5,2.5]")
        if not np.isfinite(budget_rate) or not 0 < budget_rate <= 1:
            raise ValueError("budget rate must lie in (0,1]")
        q_const = min(1.0, budget_rate * float(vt.mean()) / float(vt.mean()))
        q_path = np.full(n, q_const)
        budget = budget_rate * float(vt.mean()) * n
        bound_path = cost_bound / q_path + epsilon
    else:
        q_path, budget = _propensity_path(
            arm, active, prices, validation_disagreement, validation_tariffs, budget_rate
        )
        bound_path = 5 / q_path + epsilon

    out_first = np.full(reps, -1, dtype=np.int64)
    out_labels = np.zeros(reps, dtype=np.int64)
    out_dollars = np.zeros(reps)
    out_processed = np.full(reps, n, dtype=np.int64)
    out_max = np.full(reps, -np.inf)
    index = np.arange(n)
    threshold = -np.log(alpha)
    for start in range(0, reps, _CHUNK):
        c = min(_CHUNK, reps - start)
        sl = slice(start, start + c)
        cost = np.broadcast_to(
            z[None, :] if sign_arr is None else sign_arr[sl] * z[None, :], (c, n)
        )
        if arm == "full_feedback":
            value = cost - epsilon
            processed = np.full(c, n, dtype=np.int64)
            labels = np.zeros(c, dtype=np.int64)
            dollars = np.zeros(c)
        else:
            assert coins is not None
            gate = active[None, :] if arm != "ungated_ht" else True
            query = gate & (coins[sl] < q_path[None, :])
            value = np.where(query, cost / q_path[None, :], 0.0) - epsilon
            spend = np.cumsum(prices[None, :] * query, axis=1)
            stop = np.empty((c, n), dtype=bool)
            stop[:, 0] = budget + 1e-12 < _MAX_TARIFF
            stop[:, 1:] = budget - spend[:, :-1] + 1e-12 < _MAX_TARIFF
            processed = np.where(stop.any(axis=1), stop.argmax(axis=1), n).astype(np.int64)
            keep = index[None, :] < processed[:, None]
            labels = (query & keep).sum(axis=1).astype(np.int64)
            before = np.concatenate([np.zeros((c, 1)), spend], axis=1)
            dollars = before[np.arange(c), processed]
        ratio = value / bound_path[None, :]
        log_e = _eb_log_e(ratio, alpha) if arm == "gated_eb_paced" else _mixture_log_e(ratio)
        keep = index[None, :] < processed[:, None]
        hits = (log_e >= threshold) & keep
        out_first[sl] = np.where(hits.any(axis=1), hits.argmax(axis=1), -1)
        out_max[sl] = np.where(keep, log_e, -np.inf).max(axis=1)
        out_labels[sl], out_dollars[sl], out_processed[sl] = labels, dollars, processed
    return ReplayBatch(out_first, out_labels, out_dollars, out_processed, out_max)


def _scalar_ungated_ht(
    *,
    paired_cost,
    tariffs,
    uniforms,
    validation_tariffs,
    budget_rate: float,
    epsilon: float = 0.1,
    alpha: float = 0.05,
    cost_bound: float = 5.0,
) -> tuple[int, int, float, int, float]:
    """Scalar reference for the ungated uniform HT arm: (first, labels, dollars, processed, max)."""
    vt = np.asarray(validation_tariffs, dtype=float)
    q = min(1.0, budget_rate * float(vt.mean()) / float(vt.mean()))
    budget = budget_rate * float(vt.mean()) * len(paired_cost)
    process = PredictableBoundMeanEProcess(alpha=alpha)
    spent, labels, first, processed, top = 0.0, 0, -1, 0, -np.inf
    for i in range(len(paired_cost)):
        if budget - spent + 1e-12 < _MAX_TARIFF:
            break
        query = bool(uniforms[i] < q)
        value = (float(paired_cost[i]) if query else 0.0) / q - epsilon
        log_e = process.update(value, bound=cost_bound / q + epsilon)
        if query:
            spent += float(tariffs[i])
            labels += 1
        processed += 1
        top = max(top, log_e)
        if first < 0 and log_e >= -np.log(alpha):
            first = i
    return first, labels, spent, processed, top
