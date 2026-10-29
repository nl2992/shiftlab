"""Exact first-promotion decomposition of the causal switching game.

The post-promotion continuation is an ordinary delayed-HMM control problem.
Only the pre-promotion portion remains in the robust sequence-form game.
This is a structural solver reduction, not a new policy class.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction as F

import numpy as np

from shiftlab.dive.causal_switching_game import (
    CausalSwitchingGame,
    GameConfig,
    History,
    Outcomes,
    Policy,
)
from shiftlab.dive.delayed_regime_information import RegimeModel

Pending = tuple[tuple[int, int], ...]
Belief = tuple[tuple[int, Pending, F], ...]


class FirstPromotionDecomposedGame(CausalSwitchingGame):
    """Eliminate post-promotion learner sequences using an exact belief DP."""

    def __init__(self, config: GameConfig, model: RegimeModel) -> None:
        super().__init__(config, model)
        self._continuation_actions: dict[tuple, tuple[int, int]] = {}
        self._value_at_cache: dict[tuple[int, int, int, Belief], F] = {}
        self._decision_cache: dict[tuple[int, int, int, Belief], F] = {}
        self._promotion_cache: dict[tuple[int, int, Belief, int], F] = {}

    @staticmethod
    def _canonical(masses: dict[tuple[int, Pending], F]) -> Belief:
        total = sum(masses.values(), F(0))
        if total <= 0:
            raise ValueError("belief must have positive mass")
        return tuple(
            (state, pending, mass / total)
            for (state, pending), mass in sorted(masses.items())
            if mass
        )

    def _transition_belief(self, time: int, belief: Belief, query: int) -> Belief:
        masses: dict[tuple[int, Pending], F] = defaultdict(F)
        model = self.model
        for state, pending, mass in belief:
            positive = model.emission1 if state else model.emission0
            outcomes = ((0, 1 - positive), (1, positive)) if query else ((0, F(1)),)
            for outcome, outcome_mass in outcomes:
                next_pending = pending
                if query:
                    next_pending = tuple(sorted((*pending, (time + self.config.delay, outcome))))
                if state == 0:
                    transitions = ((0, 1 - model.transition01), (1, model.transition01))
                else:
                    transitions = ((0, model.transition10), (1, 1 - model.transition10))
                for next_state, transition_mass in transitions:
                    joint = mass * outcome_mass * transition_mass
                    if joint:
                        masses[next_state, next_pending] += joint
        return self._canonical(masses)

    def _release_due(self, time: int, belief: Belief):
        due_times = {
            release for _, pending, _ in belief for release, _ in pending if release <= time
        }
        if not due_times:
            return ((F(1), belief),)
        due = min(due_times)
        outcomes = sorted(
            {outcome for _, pending, _ in belief for release, outcome in pending if release == due}
        )
        branches = []
        for outcome in outcomes:
            masses: dict[tuple[int, Pending], F] = defaultdict(F)
            branch_mass = F(0)
            for state, pending, mass in belief:
                if (due, outcome) not in pending:
                    continue
                branch_mass += mass
                remaining = tuple(item for item in pending if item != (due, outcome))
                masses[state, remaining] += mass
            if branch_mass:
                branches.append((branch_mass, self._canonical(masses)))
        return tuple(branches)

    def _value_at(self, time: int, old_action: int, remaining: int, belief: Belief) -> F:
        key = (time, old_action, remaining, belief)
        if key in self._value_at_cache:
            return self._value_at_cache[key]
        value = sum(
            probability * self._decision_value(time, old_action, remaining, conditional)
            for probability, conditional in self._release_due(time, belief)
        )
        self._value_at_cache[key] = value
        return value

    def _decision_value(self, time: int, old_action: int, remaining: int, belief: Belief) -> F:
        key = (time, old_action, remaining, belief)
        if key in self._decision_cache:
            return self._decision_cache[key]
        positive = sum(
            mass * (self.model.emission1 if state else self.model.emission0)
            for state, _, mass in belief
        )
        query_choices = (0, 1) if remaining else (0,)
        choices = tuple((action, query) for action in (0, 1) for query in query_choices)
        best_value: F | None = None
        best_choice = None
        for action, query in choices:
            value = positive if action == 0 else 1 - positive
            value += self.config.query_cost * query
            value += self.config.switch_cost * (action != old_action)
            if time < self.config.horizon:
                following = self._transition_belief(time, belief, query)
                value += self._value_at(time + 1, action, remaining - query, following)
            if best_value is None or value < best_value:
                best_value, best_choice = value, (action, query)
        assert best_value is not None and best_choice is not None
        self._continuation_actions[time, old_action, remaining, belief] = best_choice
        self._decision_cache[key] = best_value
        return best_value

    def _promote_value(self, time: int, remaining: int, belief: Belief, query: int) -> F:
        key = (time, remaining, belief, query)
        if key in self._promotion_cache:
            return self._promotion_cache[key]
        if query > remaining:
            raise ValueError("promotion query exceeds remaining budget")
        positive = sum(
            mass * (self.model.emission1 if state else self.model.emission0)
            for state, _, mass in belief
        )
        value = 1 - positive + self.config.query_cost * query
        value += self.config.switch_cost
        if time < self.config.horizon:
            following = self._transition_belief(time, belief, query)
            value += self._value_at(time + 1, 1, remaining - query, following)
        self._promotion_cache[key] = value
        return value

    def _belief_from_history(self, history: History, outcomes: Outcomes) -> Belief:
        time = len(history) + 1
        visible: dict[int, int] = dict(self.information(history, outcomes)[1])
        masses: dict[tuple[int, Pending], F] = defaultdict(F)
        prior1 = self.model.propagate(self.model.prior1, 1)
        paths = ((0, 1 - prior1), (1, prior1))
        # State entries are (current hidden state, pending labels, mass).
        states: list[tuple[int, Pending, F]] = [(state, (), mass) for state, mass in paths if mass]
        for event in range(1, time):
            conditioned: list[tuple[int, Pending, F]] = []
            for state, pending, mass in states:
                due_items: Pending = tuple(item for item in pending if item[0] <= event)
                if any(
                    visible.get(release - self.config.delay) != outcome
                    for release, outcome in due_items
                ):
                    continue
                remaining_pending = tuple(item for item in pending if item[0] > event)
                conditioned.append((state, remaining_pending, mass))
            states = conditioned
            if history[event - 1][1]:
                release = event + self.config.delay
                if release <= time:
                    observed = visible.get(event)
                    if observed is None:
                        raise ValueError("released queried label missing from learner history")
                    outcomes_for_event: tuple[tuple[int, F], ...] = ((observed, F(1)),)
                else:
                    outcomes_for_event = ((0, F(1)), (1, F(1)))
                expanded: list[tuple[int, Pending, F]] = []
                for state, pending, mass in states:
                    p = self.model.emission1 if state else self.model.emission0
                    for outcome, prior_mass in outcomes_for_event:
                        likelihood = p if outcome else 1 - p
                        expanded.append(
                            (
                                state,
                                tuple(sorted((*pending, (release, outcome)))),
                                mass * likelihood * prior_mass,
                            )
                        )
                states = expanded
            if event < time:
                transitioned: list[tuple[int, Pending, F]] = []
                for state, pending, mass in states:
                    if state == 0:
                        transitions = (
                            (0, 1 - self.model.transition01),
                            (1, self.model.transition01),
                        )
                    else:
                        transitions = (
                            (0, self.model.transition10),
                            (1, 1 - self.model.transition10),
                        )
                    transitioned.extend(
                        (next_state, pending, mass * probability)
                        for next_state, probability in transitions
                        if probability
                    )
                states = transitioned
        # Condition on labels released at the current event, before its action is chosen.
        current_conditioned: list[tuple[int, Pending, F]] = []
        for state, pending, mass in states:
            current_due_items: Pending = tuple(item for item in pending if item[0] <= time)
            if any(
                visible.get(release - self.config.delay) != outcome
                for release, outcome in current_due_items
            ):
                continue
            future_pending = tuple(item for item in pending if item[0] > time)
            current_conditioned.append((state, future_pending, mass))
        # Current-event labels are not yet queried; due labels are now removed.
        for state, pending, mass in current_conditioned:
            masses[state, pending] += mass
        return self._canonical(masses)

    def _alternative(self, history, outcomes, sequence, weight, posterior, total_cost):
        self._node()
        time = len(history) + 1
        if time > self.config.horizon:
            self.cost[sequence] += float(weight * total_cost)
            return
        state1 = self.model.propagate(posterior, 1)
        positive = self.model.emission(state1)
        choices = self.choices(history)
        children = self.learner.add(self.information(history, outcomes), sequence, choices)
        old = history[-1][0] if history else 0
        promoted = any(action for action, _ in history)
        for (action, query), child in zip(choices, children, strict=True):
            if action and not promoted:
                belief = self._belief_from_history(history, outcomes)
                continuation = self._promote_value(
                    time,
                    self.config.budget - sum(q for _, q in history),
                    belief,
                    query,
                )
                self.cost[child] += float(weight * (total_cost + continuation))
                continue
            cost = positive if action == 0 else 1 - positive
            cost += self.config.query_cost * query + self.config.switch_cost * (action != old)
            next_history = history + ((action, query),)
            if query:
                for y, probability in ((0, 1 - positive), (1, positive)):
                    likelihood1 = self.model.emission1 if y else 1 - self.model.emission1
                    next_posterior = state1 * likelihood1 / probability
                    self._alternative(
                        next_history,
                        outcomes + ((time, y),),
                        child,
                        weight * probability,
                        next_posterior,
                        total_cost + cost,
                    )
            else:
                self._alternative(next_history, outcomes, child, weight, state1, total_cost + cost)

    def recover(self, realization: np.ndarray) -> tuple[Policy, list[dict]]:
        prepromotion_policy, records = super().recover(realization)

        def policy(history, outcomes):
            if any(action for action, _ in history):
                time = len(history) + 1
                remaining = self.config.budget - sum(query for _, query in history)
                belief = self._belief_from_history(history, outcomes)
                key = (time, history[-1][0], remaining, belief)
                if key not in self._continuation_actions:
                    self._decision_value(time, history[-1][0], remaining, belief)
                action, query = self._continuation_actions[key]
                choices = self.choices(history)
                return tuple(F(choice == (action, query)) for choice in choices)
            return prepromotion_policy(history, outcomes)

        return policy, records
