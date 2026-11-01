"""Calibration, world pools, and per-run metrics for the Q1 search (see docs/sota_synthetic_search/03_*)."""

from __future__ import annotations

import time

import numpy as np

from shiftlab.sota_search import detectors as det
from shiftlab.sota_search import generators as g

ALPHA = 0.05


def dev_pool() -> list[g.World]:
    w = [
        g.World(kind="concept", delta=d, shape=s, t0=800)
        for d in (1.5, 2.0, 3.0)
        for s in ("abrupt", "gradual", "transient")
    ]
    w.append(g.World(kind="subgroup", delta=4.0))
    w += [
        g.World(kind="cov_benign", delta=d, shape=s)
        for d in (2.0, 3.0)
        for s in ("abrupt", "gradual")
    ]
    w += [g.World(kind="cov_inform", delta=d) for d in (1.0, 2.0)]
    w += [g.World(kind="prior", delta=d) for d in (1.0, 2.0)]
    w.append(g.World(kind="none"))
    return w


def heldout_pool() -> list[g.World]:
    return [
        g.World(kind="concept", delta=2.5, shape="recurrent", t0=500, period=500),
        g.World(kind="concept", delta=1.2, shape="abrupt", t0=1100),
        g.World(kind="concept", delta=2.5, shape="gradual", t0=500, ramp=400),
        g.World(kind="subgroup", delta=4.0, shape="recurrent", t0=500, period=600),
        g.World(kind="cov_benign", delta=2.5, shape="recurrent", t0=500, period=500),
        g.World(kind="cov_inform", delta=1.5, shape="gradual", t0=500, ramp=300),
        g.World(kind="prior", delta=1.5, shape="abrupt", t0=1100),
        g.World(kind="none"),
    ]


def heldout_g2_pool() -> list[g.World]:
    """Second generator family (nonlinear truth, misspecified linear deployed model). Frozen before running."""
    fam = {"family": "G2"}
    return [
        g.World(kind="concept", delta=2.0, shape="abrupt", t0=700, **fam),
        g.World(kind="concept", delta=3.0, shape="gradual", t0=600, ramp=300, **fam),
        g.World(kind="concept", delta=2.0, shape="recurrent", t0=500, period=500, **fam),
        g.World(kind="cov_benign", delta=3.0, shape="abrupt", t0=700, **fam),
        g.World(kind="cov_inform", delta=1.0, shape="abrupt", t0=700, **fam),
        g.World(kind="cov_inform", delta=2.0, shape="gradual", t0=600, ramp=300, **fam),
        g.World(kind="prior", delta=1.0, shape="abrupt", t0=700, **fam),
        g.World(kind="subgroup", delta=4.0, shape="abrupt", t0=700, **fam),
        g.World(kind="none", **fam),
    ]


def role(world: g.World) -> str:
    tr = g.truth(world)
    if world.kind == "none":
        return "null"
    return "harm" if tr["harmful"].any() else "benign"


def calibrate(name: str, params: dict, null_sim, lseed: int = 77) -> float:
    """Empirical threshold = (1-alpha) quantile of the horizon maximum on the null stream."""
    if name in det.THEORY_THRESHOLD:
        return det.THEORY_THRESHOLD[name]
    stat = det.DETECTORS[name](null_sim, lseed=lseed, **params)
    stat = np.where(np.isfinite(stat), stat, -np.inf)
    return float(np.quantile(stat.max(1), 1 - ALPHA))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (float(c - h), float(c + h))


def score(alarm: np.ndarray, world: g.World, frac: float | None, labels=None) -> dict:
    tr = g.truth(world)
    T = world.T
    first_harm = int(tr["harmful"].argmax()) if tr["harmful"].any() else T
    fired = alarm < T
    detected = fired & (alarm >= first_harm) & tr["harmful"].any()
    false_alarm = fired & (alarm < first_harm)
    cum = np.cumsum(np.maximum(tr["harm"], 0.0))
    harm_before = cum[np.minimum(alarm, T - 1)]
    n = len(alarm)
    return {
        "detect_prob": float(detected.mean()),
        "false_alarm_prob": float(false_alarm.mean()),
        "false_alarm_ci": wilson(int(false_alarm.sum()), n),
        "detect_ci": wilson(int(detected.sum()), n),
        "mean_delay": float((alarm[detected] - first_harm).mean()) if detected.any() else None,
        "mean_harm_before_alarm": float(harm_before.mean()),
        "mean_labels": float(labels[np.arange(n), np.minimum(alarm, T - 1)].mean())
        if labels is not None
        else float((frac or 0.0) * np.minimum(alarm, T).mean()),
        "first_harm": first_harm,
    }


def evaluate(
    name: str, params: dict, world: g.World, sim, thr: float, lseed: int
) -> tuple[dict, float]:
    t0 = time.time()
    stat = det.DETECTORS[name](sim, lseed=lseed, **params)
    alarm = det.first_cross(np.where(np.isfinite(stat), stat, -np.inf), thr)
    return score(alarm, world, params.get("frac"), sim.pop("_labels", None)), time.time() - t0
