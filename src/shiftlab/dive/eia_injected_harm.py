"""Injected under-procurement harm for the EIA paired decision task (synthetic research injection, not observed harm)."""

from __future__ import annotations

import numpy as np

from shiftlab.dive.reserve_costs import paired_cost

MIN_PROCURE_EVENTS = 20


def onset_index(n: int, fraction: float) -> int:
    """Index at which injected harm begins: floor(fraction * n)."""
    if n < 1 or not 0.0 < fraction < 1.0:
        raise ValueError("need n >= 1 and 0 < fraction < 1")
    return int(np.floor(fraction * n))


def select_band(rehearsal_margin: np.ndarray, rehearsal_action: np.ndarray) -> tuple[float, float]:
    """Band (0, median margin of procure events] from a pre-window rehearsal period."""
    margin = np.asarray(rehearsal_margin, dtype=float)
    action = np.asarray(rehearsal_action)
    if margin.shape != action.shape:
        raise ValueError("margins and actions must have the same shape")
    if not np.isfinite(margin).all():
        raise ValueError("margins must be finite")
    if not np.isin(action, (0, 1)).all():
        raise ValueError("actions must be binary")
    procure = action == 1
    if int(procure.sum()) < MIN_PROCURE_EVENTS:
        raise ValueError(f"need at least {MIN_PROCURE_EVENTS} procure events")
    if (margin[procure] <= 0).any():
        raise ValueError("procure events must have margin > 0")
    return (0.0, float(np.median(margin[procure])))


def inject_under_procurement(
    deployed_action: np.ndarray,
    frozen_margin: np.ndarray,
    onset: int,
    band: tuple[float, float],
) -> np.ndarray:
    """Return a copy where procure events with margin in (band[0], band[1]] after onset are set to 0."""
    acts = np.asarray(deployed_action)
    margin = np.asarray(frozen_margin, dtype=float)
    if acts.shape != margin.shape or acts.ndim != 1:
        raise ValueError("actions and margins must be 1-D arrays of the same shape")
    if not np.isin(acts, (0, 1)).all():
        raise ValueError("actions must be binary")
    if not np.isfinite(margin).all():
        raise ValueError("margins must be finite")
    n = acts.shape[0]
    if not 0 <= onset <= n:
        raise ValueError("onset must satisfy 0 <= onset <= n")
    if not (np.isfinite(band[0]) and np.isfinite(band[1]) and band[0] < band[1]):
        raise ValueError("band must be finite with band[0] < band[1]")
    out = acts.astype(np.int8, copy=True)
    idx = np.arange(n)
    hit = (idx >= onset) & (acts == 1) & (margin > band[0]) & (margin <= band[1])
    out[hit] = 0
    return out


def injected_paired_cost(
    deployed_action: np.ndarray,
    frozen_margin: np.ndarray,
    reference_action: np.ndarray,
    demand: np.ndarray,
    tau: float,
    onset: int,
    band: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (new deployed action, new paired cost Z, new disagreement) after injection."""
    new_action = inject_under_procurement(deployed_action, frozen_margin, onset, band)
    z = paired_cost(new_action, reference_action, demand, tau)
    disagreement = new_action != np.asarray(reference_action)
    return new_action, z, disagreement
