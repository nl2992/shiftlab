"""Delayed, pathwise-budgeted adaptation of stochastic CAMS.

The adapter preserves CAMS's exponential weights over contextual policies,
weighted-vote recommendation, and disagreement-based query probability. It
adds fixed-delay label release and reserves each query right at request time.
It is a comparator adaptation; CAMS's published guarantees are not claimed.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import log, sqrt
from typing import Protocol

import numpy as np

ContextPolicy = Callable[[object], Sequence[float]]


class RandomSource(Protocol):
    def random(self) -> float: ...


@dataclass(frozen=True)
class CamsDecision:
    event: int
    recommended_model: int
    policy_weights: tuple[float, ...]
    model_weights: tuple[float, ...]
    query_probability: float
    query_requested: bool
    released_labels: int
    pending_labels: int
    requests_used: int


@dataclass(frozen=True)
class _PendingLabel:
    release_event: int
    propensity: float
    expert_action_distributions: tuple[tuple[float, ...], ...]
    predictions: tuple[int, ...]
    model_losses: tuple[float, ...]


class HardBudgetDelayedCams:
    """CAMS stochastic algorithm with fixed-delay feedback and a hard request cap.

    The supplied contextual policies return distributions over the base models.
    CAMS's constant single-model policies are appended automatically. At each
    event, `begin_event` reveals current contexts and predictions only. Queried
    truth is submitted separately and hidden until exactly `delay` events later.
    Switching fees are deliberately evaluated outside this cost-oblivious rule.
    """

    def __init__(
        self,
        *,
        model_count: int,
        class_count: int,
        budget: int,
        delay: int,
        policies: Sequence[ContextPolicy] = (),
    ) -> None:
        if type(model_count) is not int or model_count < 2:
            raise ValueError("model_count must be an integer of at least two")
        if type(class_count) is not int or class_count < 2:
            raise ValueError("class_count must be an integer of at least two")
        if type(budget) is not int or budget < 0:
            raise ValueError("budget must be a nonnegative integer")
        if type(delay) is not int or delay < 1:
            raise ValueError("delay must be a positive integer")

        self.model_count = model_count
        self.class_count = class_count
        self.budget = budget
        self.delay = delay
        self.policies = tuple(policies)
        self.expert_count = len(self.policies) + model_count
        self.event = 0
        self.requests_used = 0
        self.cumulative_policy_loss = np.zeros(self.expert_count, dtype=float)
        self._pending: dict[int, list[_PendingLabel]] = defaultdict(list)
        self._awaiting_submission: _PendingLabel | None = None

    @property
    def pending_labels(self) -> int:
        return sum(map(len, self._pending.values()))

    @property
    def remaining_budget(self) -> int:
        return self.budget - self.requests_used

    def _policy_distributions(self, context: object) -> tuple[tuple[float, ...], ...]:
        distributions: list[tuple[float, ...]] = []
        for policy in self.policies:
            distribution = tuple(map(float, policy(context)))
            if len(distribution) != self.model_count:
                raise ValueError("each policy must return one weight per model")
            if not np.isfinite(distribution).all() or any(weight < 0 for weight in distribution):
                raise ValueError("policy weights must be finite and nonnegative")
            if not np.isclose(sum(distribution), 1.0, atol=1e-10):
                raise ValueError("each policy distribution must sum to one")
            distributions.append(distribution)
        distributions.extend(
            tuple(float(model == index) for model in range(self.model_count))
            for index in range(self.model_count)
        )
        return tuple(distributions)

    def _policy_weights(self) -> np.ndarray:
        eta = sqrt(log(self.expert_count) / self.event)
        logits = -eta * self.cumulative_policy_loss
        logits -= float(np.max(logits))
        weights = np.exp(logits)
        return weights / weights.sum()

    def _query_score(self, predictions: tuple[int, ...], model_weights: np.ndarray) -> float:
        disagreement = 0.0
        for label in range(self.class_count):
            expected_loss = float(
                sum(
                    model_weights[index] * float(prediction != label)
                    for index, prediction in enumerate(predictions)
                )
            )
            if 0 < expected_loss < 1:
                disagreement += expected_loss * log(1 / expected_loss, self.class_count)
        return disagreement / self.class_count

    def begin_event(
        self,
        context: object,
        predictions: Sequence[int],
        *,
        rng: RandomSource,
    ) -> CamsDecision:
        """Release due labels, then return the weighted-vote/query decision."""
        if self._awaiting_submission is not None:
            raise RuntimeError("submit the queried label before the next event")
        predictions = tuple(predictions)
        if len(predictions) != self.model_count:
            raise ValueError("one prediction is required for each model")
        if any(
            type(label) is not int or not 0 <= label < self.class_count for label in predictions
        ):
            raise ValueError("predictions must be integer class indices")

        self.event += 1
        due = self._pending.pop(self.event, [])
        for pending in due:
            losses = np.asarray(pending.model_losses, dtype=float)
            policy_distributions = np.asarray(pending.expert_action_distributions, dtype=float)
            expert_losses = policy_distributions @ losses
            self.cumulative_policy_loss += expert_losses / pending.propensity

        expert_weights = self._policy_weights()
        current_policy_distributions = self._policy_distributions(context)
        model_weights = expert_weights @ np.asarray(current_policy_distributions, dtype=float)
        ties = np.flatnonzero(np.isclose(model_weights, np.max(model_weights), atol=1e-12))
        tie_index = min(int(rng.random() * len(ties)), len(ties) - 1)
        recommended = int(ties[tie_index])

        if self.remaining_budget == 0:
            propensity = 0.0
        else:
            # CAMS Eq. (4): z_t = max(t^(-1/2), contextual disagreement).
            # For c >= 2 the disagreement term is at most one; the floor is too.
            propensity = max(1 / sqrt(self.event), self._query_score(predictions, model_weights))
        requested = propensity > 0 and rng.random() < propensity
        if requested:
            self.requests_used += 1
            self._awaiting_submission = _PendingLabel(
                release_event=self.event + self.delay,
                propensity=propensity,
                expert_action_distributions=current_policy_distributions,
                predictions=predictions,
                model_losses=(),
            )

        return CamsDecision(
            event=self.event,
            recommended_model=recommended,
            policy_weights=tuple(map(float, expert_weights)),
            model_weights=tuple(map(float, model_weights)),
            query_probability=propensity,
            query_requested=requested,
            released_labels=len(due),
            pending_labels=self.pending_labels + int(requested),
            requests_used=self.requests_used,
        )

    def submit_queried_label(self, label: int) -> None:
        """Submit the requested ground-truth class without an early policy update."""
        if self._awaiting_submission is None:
            raise RuntimeError("there is no requested label awaiting submission")
        if type(label) is not int or not 0 <= label < self.class_count:
            raise ValueError("label must be an integer class index")

        pending = self._awaiting_submission
        losses = tuple(float(prediction != label) for prediction in pending.predictions)
        self._pending[pending.release_event].append(
            _PendingLabel(
                release_event=pending.release_event,
                propensity=pending.propensity,
                expert_action_distributions=pending.expert_action_distributions,
                predictions=pending.predictions,
                model_losses=losses,
            )
        )
        self._awaiting_submission = None
