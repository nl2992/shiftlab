"""Resource-Constrained Concept Drift Adaptation (RCCDA) policy rule.

This module implements the published virtual-queue threshold and the paper's
P/D history estimator. It is a scheduling policy, not a decision-harm test.
The estimate error is not covered by RCCDA's ideal-estimator resource theorem.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class RCCDADecision:
    """One auditable RCCDA decision and its virtual-queue transition."""

    update: bool
    estimated_gain: float
    threshold: float
    queue_before: float
    queue_after: float


class RCCDAState:
    """Stateful RCCDA threshold policy for equal-cost model updates.

    The estimator is
    ``Kp * (current_loss - best_observed_loss) + Kd * (current_loss - previous_loss)``.
    ``previous_loss`` must be the prior available inference loss; passing the
    current loss twice silently removes the derivative component, as happened
    in the inspected official PACS evaluator.
    """

    def __init__(
        self,
        *,
        update_cost: float = 1.0,
        average_update_budget: float = 0.1,
        tradeoff: float = 10.0,
        proportional_gain: float = 1.0,
        derivative_gain: float = 0.3,
    ) -> None:
        values = (
            update_cost,
            average_update_budget,
            tradeoff,
            proportional_gain,
            derivative_gain,
        )
        if not all(math.isfinite(value) for value in values):
            raise ValueError("RCCDA parameters must be finite")
        if update_cost <= 0 or average_update_budget <= 0:
            raise ValueError("update cost and average update budget must be positive")
        if tradeoff <= 0 or proportional_gain < 0 or derivative_gain < 0:
            raise ValueError("tradeoff must be positive and gains nonnegative")
        self.update_cost = float(update_cost)
        self.average_update_budget = float(average_update_budget)
        self.tradeoff = float(tradeoff)
        self.proportional_gain = float(proportional_gain)
        self.derivative_gain = float(derivative_gain)
        self.queue = 0.0
        self.steps = 0

    def decide(
        self,
        *,
        current_loss: float,
        previous_loss: float,
        best_observed_loss: float,
    ) -> RCCDADecision:
        """Choose the next update using only losses available by this decision."""
        losses = (current_loss, previous_loss, best_observed_loss)
        if not all(math.isfinite(value) and 0 <= value <= 1 for value in losses):
            raise ValueError("RCCDA losses must be finite and lie in [0, 1]")
        if best_observed_loss > current_loss + 1e-12:
            raise ValueError("best_observed_loss cannot exceed current_loss")

        gain = self.proportional_gain * (current_loss - best_observed_loss)
        gain += self.derivative_gain * (current_loss - previous_loss)
        threshold = self.update_cost * self.queue + 0.5 * (
            self.update_cost**2 - 2 * self.average_update_budget * self.update_cost
        )
        update = self.tradeoff * gain >= threshold
        queue_before = self.queue
        self.queue = max(
            0.0,
            self.queue + self.update_cost * int(update) - self.average_update_budget,
        )
        self.steps += 1
        return RCCDADecision(
            update=bool(update),
            estimated_gain=float(gain),
            threshold=float(threshold),
            queue_before=float(queue_before),
            queue_after=float(self.queue),
        )
