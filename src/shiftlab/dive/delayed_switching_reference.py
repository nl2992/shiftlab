"""Uniform-query delayed Hedge reference, not a statistically safe switching method.

See docs/switching_reference_protocol_v1.md for the fixed-comparator bound.
The learner accepts only requested, arrived paired losses; evaluator truth is absent.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import exp, isfinite
from random import Random


@dataclass(frozen=True)
class PairedFeedback:
    event: int
    loss0: float
    loss1: float


@dataclass(frozen=True)
class SwitchingDecision:
    action: int
    query: bool
    probability1: float


class DelayedBudgetHedge:
    """Hold a coupled action per block and request one random label per block.

    Feedback must be supplied at the start of its exact availability round.
    query_seed and deployment_uniform must be independently generated for the bound.
    """

    def __init__(
        self,
        *,
        horizon: int,
        blocks: int,
        budget: int,
        delay: int,
        eta: float,
        query_seed: int,
        deployment_uniform: float,
    ) -> None:
        if any(type(x) is not int for x in (horizon, blocks, budget, delay)):
            raise ValueError("horizon, blocks, budget, delay must be integers")
        if not 1 <= blocks <= budget <= horizon or horizon % blocks:
            raise ValueError("require blocks <= budget <= horizon and equal integer blocks")
        if delay < 1 or not isfinite(eta) or eta <= 0:
            raise ValueError("require positive delay and finite positive eta")
        if not isfinite(deployment_uniform) or not 0 <= deployment_uniform < 1:
            raise ValueError("deployment_uniform must be in [0, 1)")
        self.horizon = horizon
        self.delay = delay
        self.block_length = horizon // blocks
        self.eta = eta
        self._query_rng = Random(query_seed)
        self._deployment_uniform = deployment_uniform
        self._next_round = 1
        self._query_event = 0
        self._pending: set[int] = set()
        self._ready_scores: list[float] = []
        self._score = 0.0
        self._probability = 0.5
        self._action = 0
        self.queries = 0

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def step(self, event: int, feedback: Sequence[PairedFeedback] = ()) -> SwitchingDecision:
        if type(event) is not int or event != self._next_round or event > self.horizon:
            raise ValueError("rounds must be called exactly once, in order, within horizon")
        received = [row.event for row in feedback]
        if len(set(received)) != len(received):
            raise ValueError("duplicate feedback")
        # Validate the complete input before changing state, so a bad call can be retried.
        for row in feedback:
            if type(row.event) is not int or row.event not in self._pending:
                raise ValueError("feedback must refer to an outstanding requested event")
            if event != row.event + self.delay:
                raise ValueError("feedback must arrive at its exact availability round")
            if not all(isfinite(x) and 0 <= x <= 1 for x in (row.loss0, row.loss1)):
                raise ValueError("paired losses must be finite and in [0, 1]")
        due = {s for s in self._pending if s + self.delay == event}
        if due != set(received):
            raise ValueError("all feedback due this round must be supplied")
        for row in feedback:
            self._pending.remove(row.event)
            self._ready_scores.append(row.loss0 - row.loss1)
        if (event - 1) % self.block_length == 0:
            self._score += sum(self._ready_scores)
            self._ready_scores.clear()
            log_odds = self.eta * self._score
            if log_odds >= 0:
                self._probability = 1 / (1 + exp(-log_odds))
            else:
                odds = exp(log_odds)
                self._probability = odds / (1 + odds)
            self._action = int(self._deployment_uniform < self._probability)
            self._query_event = event + self._query_rng.randrange(self.block_length)
        query = event == self._query_event
        if query:
            self._pending.add(event)
            self.queries += 1
        self._next_round += 1
        return SwitchingDecision(self._action, query, self._probability)
