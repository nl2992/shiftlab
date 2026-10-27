"""Exploratory context-stratified e-process composition.

Kept separate from the frozen baseline e-process module so historical experiment
hashes continue to identify the code that produced their calibration records.
"""

from __future__ import annotations

import numpy as np

from .eprocess import BoundedMeanEProcess


class ContextStratifiedEProcess:
    """Bonferroni family of bounded-mean e-processes for fixed contexts.

    This tests the intersection null that every predeclared context has
    conditional mean at most zero. Context membership must be observable before
    the outcome, and each context-specific conditional-mean null must hold at
    its update times. It does *not* test a population-average mean null when
    context-specific means may offset one another.
    """

    def __init__(
        self,
        *,
        contexts: tuple[str, ...],
        bound: float,
        alpha: float = 0.05,
        stakes: tuple[float, ...] = (0.05, 0.1, 0.2, 0.4, 0.8),
    ):
        if not contexts or len(set(contexts)) != len(contexts) or any(not c for c in contexts):
            raise ValueError("contexts must be nonempty, unique, and nonempty strings")
        if not np.isfinite(bound) or bound <= 0:
            raise ValueError("bound must be finite and positive")
        if not np.isfinite(alpha) or not 0 < alpha < 1:
            raise ValueError("alpha must lie strictly between zero and one")
        self.contexts = contexts
        self.processes = {
            context: BoundedMeanEProcess(
                bound=bound,
                alpha=alpha / len(contexts),
                stakes=stakes,
            )
            for context in contexts
        }

    @property
    def log_e_values(self) -> dict[str, float]:
        return {context: process.log_e_value for context, process in self.processes.items()}

    @property
    def alarmed_contexts(self) -> tuple[str, ...]:
        return tuple(context for context, process in self.processes.items() if process.alarm)

    @property
    def alarm(self) -> bool:
        """Whether any fixed context crossed its Bonferroni-adjusted threshold."""
        return bool(self.alarmed_contexts)

    def update(self, value: float, *, context: str) -> float:
        try:
            process = self.processes[context]
        except KeyError as exc:
            raise ValueError(f"unknown context {context!r}") from exc
        process.update(value)
        return process.log_e_value
