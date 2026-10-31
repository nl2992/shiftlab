"""Data contracts. Operational streams (EpisodeBatch) and evaluator-only truth are separate types.

Monitors, controllers and ``evaluation.simulate`` never receive an ``EvaluatorTruth``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass(frozen=True)
class CostContract:
    c_q: float = 0.0  # cost per queried label
    c_s: float = 0.0  # cost per switch (either direction)

    def __post_init__(self):
        if self.c_q < 0 or self.c_s < 0:
            raise ValueError("costs must be nonnegative")


@dataclass(frozen=True)
class FeedbackContract:
    q: float = 1.0  # per-event query probability (uniform acquisition)
    d: int = (
        0  # fixed label delay (event t queried -> released at t+d -> visible at decision t+d+1)
    )
    max_queries: int | None = None  # optional per-episode budget (first B queried events kept)

    def __post_init__(self):
        if not 0.0 <= self.q <= 1.0:
            raise ValueError("q must lie in [0, 1]")
        if self.d < 0 or int(self.d) != self.d:
            raise ValueError("delay d must be a nonnegative integer")
        if self.max_queries is not None and self.max_queries < 0:
            raise ValueError("query budget must be nonnegative")


@dataclass
class EpisodeBatch:
    """Operational data: realised losses of both actions (Setting A) and the query mask."""

    l0: np.ndarray  # (n, T) incumbent realised loss
    l1: np.ndarray  # (n, T) challenger realised loss
    mask: np.ndarray  # (n, T) bool, event t queried

    @property
    def n(self) -> int:
        return self.l0.shape[0]

    @property
    def T(self) -> int:
        return self.l0.shape[1]


@dataclass
class EvaluatorTruth:
    """Evaluator-side oracle truth. Never passed to learners/monitors/controllers."""

    mu0: np.ndarray  # (n, T) expected incumbent loss
    mu1: np.ndarray  # (n, T) expected challenger loss
    regime: np.ndarray  # (n, T) int8 latent regime (0 good, 1 bad / changed)
    tau: np.ndarray  # (n,) change time, nan if none
    params: dict = field(default_factory=dict)

    @property
    def advantage(self) -> np.ndarray:
        return self.mu0 - self.mu1

    @property
    def opportunity(self) -> np.ndarray:
        return self.advantage > 0
