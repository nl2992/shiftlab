"""Hard-budget, delayed-feedback adaptation of Online LLM Picker.

This is a comparator adaptation, not a faithful reproduction of the paper's
average-budget, immediate-feedback evaluation protocol and not a new method.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import log, sqrt
from typing import Protocol

import numpy as np


class RandomSource(Protocol):
    def random(self) -> float: ...


@dataclass(frozen=True)
class PickerDecision:
    event: int
    recommended_model: int
    posterior: tuple[float, ...]
    query_probability: float
    query_requested: bool
    released_labels: int
    pending_labels: int
    requests_used: int


@dataclass(frozen=True)
class _PendingLabel:
    release_event: int
    propensity: float
    posterior_at_query: tuple[float, ...]
    losses: tuple[float, ...]


class HardBudgetDelayedOnlinePicker:
    """Online committee/entropy acquisition with pathwise budget and fixed delay.

    `predictions` are the candidate responses for the current prompt. A queried
    loss vector must be submitted separately with `submit_queried_losses`; the
    picker never receives outcomes for unqueried events. Query rights are
    reserved at request time, including requests whose labels remain pending.
    """

    def __init__(
        self,
        *,
        model_count: int,
        budget: int,
        delay: int,
        beta: float = 0.9,
        epsilon: float = 1e-8,
    ) -> None:
        if type(model_count) is not int or model_count < 2:
            raise ValueError("model_count must be an integer of at least two")
        if type(budget) is not int or budget < 0:
            raise ValueError("budget must be a nonnegative integer")
        if type(delay) is not int or delay < 1:
            raise ValueError("delay must be a positive integer")
        if not 0 <= beta < 1 or not np.isfinite(beta):
            raise ValueError("beta must be finite and in [0, 1)")
        if epsilon <= 0 or not np.isfinite(epsilon):
            raise ValueError("epsilon must be finite and positive")

        self.model_count = model_count
        self.budget = budget
        self.delay = delay
        self.beta = float(beta)
        self.epsilon = float(epsilon)
        self.event = 0
        self.requests_used = 0
        self.cumulative_loss = np.zeros(model_count, dtype=float)
        self.variance_ema = 0.0
        self._pending: dict[int, list[_PendingLabel]] = defaultdict(list)
        self._awaiting_submission: tuple[float, tuple[float, ...]] | None = None

    @property
    def pending_labels(self) -> int:
        return sum(map(len, self._pending.values()))

    @property
    def remaining_budget(self) -> int:
        return self.budget - self.requests_used

    def _learning_rate(self) -> float:
        corrected = self.variance_ema / (1 - self.beta**self.event)
        return sqrt(log(self.model_count) / (self.event * (corrected + self.epsilon)))

    def _posterior(self) -> tuple[np.ndarray, float]:
        eta = self._learning_rate()
        logits = -eta * self.cumulative_loss
        logits -= np.max(logits)
        weights = np.exp(logits)
        posterior = weights / weights.sum()
        return posterior, eta

    @staticmethod
    def _disagreement_variance(predictions: tuple[object, ...], posterior: np.ndarray) -> float:
        # The default discrepancy is exact match/mismatch. This handles
        # categorical outputs and keeps the adaptation deterministic.
        largest = 0.0
        for reference in predictions:
            hypothetical_losses = np.fromiter(
                (float(candidate != reference) for candidate in predictions),
                dtype=float,
                count=len(predictions),
            )
            mean = float(np.dot(posterior, hypothetical_losses))
            second = float(np.dot(posterior, hypothetical_losses**2))
            largest = max(largest, second - mean**2)
        return max(0.0, largest)

    def begin_event(
        self,
        predictions: tuple[object, ...] | list[object],
        *,
        rng: RandomSource,
    ) -> PickerDecision:
        """Release due labels, then make this event's recommendation/query choice."""
        if self._awaiting_submission is not None:
            raise RuntimeError("submit the queried loss vector before the next event")
        predictions = tuple(predictions)
        if len(predictions) != self.model_count:
            raise ValueError("one prediction is required for each candidate model")

        self.event += 1
        due = self._pending.pop(self.event, [])
        for pending in due:
            p = np.asarray(pending.posterior_at_query, dtype=float)
            losses = np.asarray(pending.losses, dtype=float)
            self.cumulative_loss += losses / pending.propensity
            observed_mean = float(np.dot(p, losses))
            observed_second = float(np.dot(p, losses**2))
            observed_variance = max(0.0, observed_second - observed_mean**2)
            self.variance_ema = self.beta * self.variance_ema + (1 - self.beta) * observed_variance

        posterior, eta = self._posterior()
        recommended = int(np.argmax(posterior))
        disagreement = self._disagreement_variance(predictions, posterior)
        entropy = -float(np.dot(posterior, np.log(np.maximum(posterior, 1e-300))))
        normalized_entropy = entropy / log(self.model_count)

        if self.remaining_budget == 0 or disagreement == 0:
            propensity = 0.0
        else:
            # The source rule defines a probability as max(disagreement*entropy, eta).
            # Capping at one makes it a valid Bernoulli probability; hard budget
            # reservation separately prevents average-budget overspend.
            propensity = min(1.0, max(disagreement * normalized_entropy, eta))
        requested = propensity > 0 and rng.random() < propensity
        if requested:
            self.requests_used += 1
            self._awaiting_submission = (propensity, tuple(map(float, posterior)))

        return PickerDecision(
            event=self.event,
            recommended_model=recommended,
            posterior=tuple(map(float, posterior)),
            query_probability=propensity,
            query_requested=requested,
            released_labels=len(due),
            pending_labels=self.pending_labels + int(requested),
            requests_used=self.requests_used,
        )

    def submit_queried_losses(self, losses: tuple[float, ...] | list[float]) -> None:
        """Enqueue the requested label vector without updating until its release."""
        if self._awaiting_submission is None:
            raise RuntimeError("there is no requested label awaiting submission")
        losses = tuple(map(float, losses))
        if len(losses) != self.model_count:
            raise ValueError("one queried loss is required for each candidate model")
        if not np.isfinite(losses).all() or any(not 0 <= loss <= 1 for loss in losses):
            raise ValueError("queried losses must be finite and in [0, 1]")

        propensity, posterior = self._awaiting_submission
        release_event = self.event + self.delay
        self._pending[release_event].append(
            _PendingLabel(release_event, propensity, posterior, losses)
        )
        self._awaiting_submission = None
