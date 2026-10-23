"""Transparent one-step, cost-aware intervention selection with hard gates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np


class Intervention(StrEnum):
    CONTINUE = "continue"
    QUERY = "query"
    RECALIBRATE = "recalibrate"
    UPDATE = "update"
    RETRAIN = "retrain"
    PROMOTE = "promote"
    FALLBACK = "fallback"


@dataclass(frozen=True)
class ActionEstimate:
    """One-step forecast of loss reduction and explicit resource costs."""

    expected_loss_reduction: float
    label_cost: float = 0.0
    compute_cost: float = 0.0
    switching_cost: float = 0.0

    def net_value(self) -> float:
        values = (
            self.expected_loss_reduction,
            self.label_cost,
            self.compute_cost,
            self.switching_cost,
        )
        if not all(np.isfinite(value) for value in values):
            raise ValueError("action values and costs must be finite")
        if min(self.label_cost, self.compute_cost, self.switching_cost) < 0:
            raise ValueError("resource costs must be nonnegative")
        return float(self.expected_loss_reduction - sum(values[1:]))


class InterventionController:
    """Choose maximum estimated net value without overriding certification gates.

    The controller is a heuristic allocator, not a safety or utility guarantee.
    Promotion and fallback decisions remain blocked until their separate gates pass.
    """

    def choose(
        self,
        estimates: Mapping[Intervention, ActionEstimate],
        *,
        promotion_certified: bool = False,
        fallback_authorized: bool = False,
    ) -> Intervention:
        if Intervention.CONTINUE not in estimates:
            raise ValueError("estimates must include a continue action")
        candidates = []
        for action, estimate in estimates.items():
            if action == Intervention.PROMOTE and not promotion_certified:
                continue
            if action == Intervention.FALLBACK and not fallback_authorized:
                continue
            candidates.append((estimate.net_value(), action))
        value, action = max(
            candidates, key=lambda pair: (pair[0], pair[1] == Intervention.CONTINUE)
        )
        return action if value > 0 else Intervention.CONTINUE
