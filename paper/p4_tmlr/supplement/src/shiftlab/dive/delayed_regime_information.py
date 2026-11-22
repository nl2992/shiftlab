"""Exact two-regime information reference; not a new method or current-benefit certificate."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction as F


@dataclass(frozen=True)
class RegimeModel:
    transition01: F = F(1, 10)
    transition10: F = F(1, 10)
    emission0: F = F(1, 4)
    emission1: F = F(3, 4)
    prior1: F = F(1, 2)

    def __post_init__(self) -> None:
        values = (self.transition01, self.transition10, self.emission0, self.emission1, self.prior1)
        if any(not isinstance(value, (F, int)) or isinstance(value, bool) for value in values):
            raise ValueError("model probabilities must be exact fractions or integers")
        if not all(0 <= p <= 1 for p in (self.transition01, self.transition10, self.prior1)):
            raise ValueError("transition and prior probabilities must be in [0,1]")
        if not 0 < self.emission0 < F(1, 2) < self.emission1 < 1:
            raise ValueError("emissions must straddle 1/2 and lie strictly inside (0,1)")
        for name in ("transition01", "transition10", "emission0", "emission1", "prior1"):
            object.__setattr__(self, name, F(getattr(self, name)))

    def propagate(self, probability1: F, steps: int) -> F:
        if type(steps) is not int or steps < 0:
            raise ValueError("steps must be a nonnegative integer")
        rate = self.transition01 + self.transition10
        if rate == 0:
            return probability1
        stationary = self.transition01 / rate
        return stationary + (probability1 - stationary) * (1 - rate) ** steps

    def emission(self, probability1: F) -> F:
        return self.emission0 + (self.emission1 - self.emission0) * probability1


@dataclass(frozen=True)
class RegimeFeedback:
    event: int
    outcome: int


class DelayedRegimeInformation:
    """Start-round release then request, under the separate research clock.

    Hidden states and unreleased outcomes are not API inputs. The e-value controls
    global no-benefit-null promotion, not current safety after a regime reversal.
    """

    def __init__(self, *, horizon: int, budget: int, delay: int, model: RegimeModel) -> None:
        if any(type(value) is not int for value in (horizon, budget, delay)):
            raise ValueError("horizon, budget and delay must be integers")
        if horizon < 1 or not 0 <= budget <= horizon or delay < 1:
            raise ValueError("require positive horizon/delay and 0 <= budget <= horizon")
        self.horizon, self.budget, self.delay = horizon, budget, delay
        self.model = model
        self.round = 0
        self.requested = 0
        self.observed = 0
        self.last_observed_event = 0
        self.posterior1 = model.prior1
        self.e_value = F(1)
        self._pending: set[int] = set()

    @property
    def pending_events(self) -> tuple[int, ...]:
        return tuple(sorted(self._pending))

    @property
    def current_probability1(self) -> F:
        return self.model.propagate(self.posterior1, self.round - self.last_observed_event)

    @property
    def current_positive_probability(self) -> F:
        return self.model.emission(self.current_probability1)

    def start_round(self, event: int, feedback: Sequence[RegimeFeedback] = ()) -> None:
        if type(event) is not int or event != self.round + 1 or event > self.horizon:
            raise ValueError("rounds must be sequential and within the horizon")
        supplied = [row.event for row in feedback]
        if len(set(supplied)) != len(supplied):
            raise ValueError("duplicate feedback")
        for row in feedback:
            if type(row.event) is not int or row.event not in self._pending:
                raise ValueError("feedback must correspond to an outstanding request")
            if row.event + self.delay != event:
                raise ValueError("feedback must arrive at its exact availability round")
            if type(row.outcome) is not int or row.outcome not in (0, 1):
                raise ValueError("feedback outcome must be integer 0 or 1")
        due = {s for s in self._pending if s + self.delay == event}
        if set(supplied) != due:
            raise ValueError("all due feedback must be supplied")
        # With one request per event and fixed delay, at most one row is due.
        for row in feedback:
            p1 = self.model.propagate(self.posterior1, row.event - self.last_observed_event)
            prediction = self.model.emission(p1)
            bet = max(F(1, 2), prediction)
            if row.outcome:
                self.posterior1 = p1 * self.model.emission1 / prediction
                self.e_value *= 2 * bet
            else:
                self.posterior1 = p1 * (1 - self.model.emission1) / (1 - prediction)
                self.e_value *= 2 * (1 - bet)
            self.last_observed_event = row.event
            self._pending.remove(row.event)
            self.observed += 1
        self.round = event

    def request(self) -> None:
        if self.round == 0:
            raise ValueError("start a round before requesting its label")
        if self.round in self._pending:
            raise ValueError("this event was already requested")
        if self.requested >= self.budget:
            raise ValueError("hard query budget exhausted")
        self._pending.add(self.round)
        self.requested += 1
