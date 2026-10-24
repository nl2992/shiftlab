"""Transparent one-step, cost-aware intervention selection with hard gates."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from .eprocess import BoundedMeanEProcess


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


@dataclass(frozen=True)
class InterventionStep:
    """Outcome of one evidence-gated controller update."""

    action: Intervention
    queried: bool
    log_e_value: float


class CertifiedPromotionRollback:
    """Promote a frozen candidate on evidence, then fall back on evidence of harm.

    The promotion process tests positive paired improvement beyond the promotion
    cost amortized over a fixed deployment horizon. After promotion, an independent
    rollback process tests candidate harm beyond the rollback cost, again amortized
    over a fixed horizon. Separate alpha allocations and nonnegative e-processes
    control the two crossing probabilities under their respective conditional-mean
    nulls. The caller supplies unbiased, bounded gain estimates and enforces the
    query/resource budget; this class controls only the intervention state machine.

    A conditional rollback guarantee after data-dependent promotion additionally
    requires the deployment feedback to satisfy its null conditional on the
    promotion history. An independent forward deployment slice is one sufficient
    design, but arbitrary post-promotion feedback is not covered automatically.
    """

    def __init__(
        self,
        *,
        promotion_bound: float,
        rollback_bound: float,
        deployment_horizon: int,
        promotion_cost: float,
        rollback_cost: float,
        alpha_total: float = 0.05,
        promotion_alpha: float | None = None,
        rollback_alpha: float | None = None,
    ):
        if (
            isinstance(deployment_horizon, bool)
            or not isinstance(deployment_horizon, int)
            or deployment_horizon < 1
        ):
            raise ValueError("deployment_horizon must be a positive integer")
        for value, name in (
            (promotion_cost, "promotion_cost"),
            (rollback_cost, "rollback_cost"),
        ):
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if not np.isfinite(alpha_total) or not 0 < alpha_total < 1:
            raise ValueError("alpha_total must lie strictly between zero and one")
        if promotion_alpha is None:
            promotion_alpha = alpha_total / 2
        if rollback_alpha is None:
            rollback_alpha = alpha_total - promotion_alpha
        if (
            not np.isfinite(promotion_alpha)
            or not np.isfinite(rollback_alpha)
            or promotion_alpha <= 0
            or rollback_alpha <= 0
            or promotion_alpha + rollback_alpha > alpha_total + 1e-12
        ):
            raise ValueError("positive stage alpha allocations must sum to at most alpha_total")

        self.deployment_horizon = deployment_horizon
        self.promotion_cost = float(promotion_cost)
        self.rollback_cost = float(rollback_cost)
        self.promotion_rate = self.promotion_cost / deployment_horizon
        self.rollback_rate = self.rollback_cost / deployment_horizon
        self.alpha_total = float(alpha_total)
        self.promotion_alpha = float(promotion_alpha)
        self.rollback_alpha = float(rollback_alpha)
        self.promotion_process = BoundedMeanEProcess(
            bound=promotion_bound,
            alpha=self.promotion_alpha,
        )
        self.rollback_process = BoundedMeanEProcess(
            bound=rollback_bound,
            alpha=self.rollback_alpha,
        )
        self.promotion_event: int | None = None
        self.rollback_event: int | None = None
        self.last_shadow_event: int | None = None
        self.last_deployment_event: int | None = None

    @property
    def promoted(self) -> bool:
        return self.promotion_event is not None

    @property
    def rolled_back(self) -> bool:
        return self.rollback_event is not None

    def observe_shadow(
        self,
        *,
        event_index: int,
        estimated_gain: float,
        queried: bool,
    ) -> InterventionStep:
        """Test fresh paired incumbent-minus-candidate gains before deployment."""
        if self.promoted:
            raise ValueError("shadow monitoring cannot continue after promotion")
        if (
            isinstance(event_index, bool)
            or not isinstance(event_index, (int, np.integer))
            or event_index < 0
        ):
            raise ValueError("event_index must be a nonnegative integer")
        if self.last_shadow_event is not None and event_index <= self.last_shadow_event:
            raise ValueError("shadow events must be strictly increasing")
        if not np.isfinite(estimated_gain):
            raise ValueError("estimated_gain must be finite")
        self.last_shadow_event = int(event_index)
        log_e = self.promotion_process.update(estimated_gain - self.promotion_rate)
        if self.promotion_process.alarm:
            self.promotion_event = int(event_index)
            action = Intervention.PROMOTE
        else:
            action = Intervention.QUERY if queried else Intervention.CONTINUE
        return InterventionStep(action=action, queried=queried, log_e_value=log_e)

    def observe_deployment(
        self,
        *,
        event_index: int,
        estimated_gain: float,
        queried: bool,
    ) -> InterventionStep:
        """Monitor the promoted candidate and return FALLBACK at first harm crossing."""
        if not self.promoted:
            raise ValueError("candidate must be certified before deployment monitoring")
        if self.rolled_back:
            raise ValueError("deployment monitoring cannot continue after fallback")
        if (
            isinstance(event_index, bool)
            or not isinstance(event_index, (int, np.integer))
            or event_index < 0
        ):
            raise ValueError("event_index must be a nonnegative integer")
        if self.last_shadow_event is not None and event_index <= self.last_shadow_event:
            raise ValueError("deployment events must follow the shadow period")
        if self.last_deployment_event is not None and event_index <= self.last_deployment_event:
            raise ValueError("deployment events must be strictly increasing")
        if not np.isfinite(estimated_gain):
            raise ValueError("estimated_gain must be finite")
        self.last_deployment_event = int(event_index)
        log_e = self.rollback_process.update(-estimated_gain - self.rollback_rate)
        if self.rollback_process.alarm:
            self.rollback_event = int(event_index)
            action = Intervention.FALLBACK
        else:
            action = Intervention.QUERY if queried else Intervention.CONTINUE
        return InterventionStep(action=action, queried=queried, log_e_value=log_e)
