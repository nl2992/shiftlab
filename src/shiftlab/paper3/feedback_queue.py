"""Pending-feedback queue: request at t, release at t + d_t (integer d_t >= 1), never early."""

from __future__ import annotations

import heapq
from itertools import count
from typing import Any


class PendingFeedbackQueue:
    def __init__(self) -> None:
        self._heap: list[tuple[int, int, int, Any]] = []
        self._seq = count()
        self._clock = 0
        self.delay_log: list[tuple[int, int, int]] = []  # (t_request, delay, available_time)

    def request(self, t: int, payload: Any, delay: int) -> int:
        """Reserve a label requested at round t; returns its available_time = t + delay."""
        if int(delay) != delay or delay < 1:
            raise ValueError("delay must be an integer >= 1")
        if t < self._clock:
            raise ValueError("request in the past of the queue clock")
        avail = int(t + delay)
        heapq.heappush(self._heap, (avail, int(t), next(self._seq), payload))
        self.delay_log.append((int(t), int(delay), avail))
        return avail

    def release(self, t: int) -> list[tuple[int, int, Any]]:
        """Pop labels with available_time <= t as (available_time, t_request, payload)."""
        if t < self._clock:
            raise ValueError("queue clock cannot move backwards")
        self._clock = int(t)
        out = []
        while self._heap and self._heap[0][0] <= t:
            avail, treq, _, payload = heapq.heappop(self._heap)
            out.append((avail, treq, payload))
        return out

    @property
    def n_pending(self) -> int:
        return len(self._heap)
