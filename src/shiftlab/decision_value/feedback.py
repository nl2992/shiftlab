"""Label queue. Event t queried -> label (both losses, Setting A) released at t+d -> processed by
the monitor at decision step t+d+1 (monitors at decision s see releases with release time <= s-1).
With fixed d at most one label is released per step, so event order is trivially preserved."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def make_mask(rng, n: int, T: int, q: float, max_queries: int | None = None) -> np.ndarray:
    mask = rng.random((n, T)) < q
    if max_queries is not None:
        mask &= np.cumsum(mask, axis=1) <= max_queries
    return mask


@dataclass
class Released:
    """Labels visible to the monitor at one decision step. Arrays shape (n,)."""

    l0: np.ndarray
    l1: np.ndarray
    valid: np.ndarray
    event: int  # event index of the released labels (-1 if none)


class LabelQueue:
    def __init__(self, batch, d: int):
        self.batch, self.d = batch, int(d)
        self._none = Released(np.zeros(batch.n), np.zeros(batch.n), np.zeros(batch.n, bool), -1)

    def at(self, s: int) -> Released:
        """Labels first visible at decision step s: those of event e = s-1-d."""
        e = s - 1 - self.d
        if e < 0:
            return self._none
        b = self.batch
        v = b.mask[:, e]
        return Released(np.where(v, b.l0[:, e], 0.0), np.where(v, b.l1[:, e], 0.0), v, e)


def clocks(mask_row: np.ndarray, d: int, T: int) -> dict:
    """Query event / release time / first-visible decision step for one episode (traces)."""
    ev = np.flatnonzero(mask_row)
    return {
        "query_event": ev.tolist(),
        "release_time": (ev + d).tolist(),
        "visible_decision": [int(x) for x in ev + d + 1 if x < T],
    }
