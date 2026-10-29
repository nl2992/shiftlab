"""Known-alternative planner guarded by a delayed e-process promotion rule.

This is a source-matched safety/test-planning baseline, not a novelty claim.
Before first promotion it optimizes HMM cost over states containing the exact
economic belief and a capped betting-process state. After promotion it delegates
to the exact delayed-HMM continuation DP.
"""

from __future__ import annotations

from collections import defaultdict
from fractions import Fraction as F

from shiftlab.dive.causal_switching_game import History, Outcomes
from shiftlab.dive.first_promotion_decomposition import Belief, FirstPromotionDecomposedGame


class EProcessGatedPlanner(FirstPromotionDecomposedGame):
    """Optimize alternative cost subject to a fixed-stake evidence gate."""

    def __init__(self, config, model, *, stake: F = F(1), threshold: F = F(4)):
        super().__init__(config, model)
        if not isinstance(stake, F) or not 0 < stake <= 1:
            raise ValueError("stake must be an exact fraction in (0, 1]")
        if not isinstance(threshold, F) or threshold <= 1:
            raise ValueError("threshold must be an exact fraction greater than one")
        self.stake = stake
        self.threshold = threshold
        self._gated_actions: dict[tuple, tuple[int, int]] = {}
        self._gated_value_cache: dict[tuple, F] = {}
        self._gated_decision_cache: dict[tuple, F] = {}

    def _update_wealth(self, wealth: F, labels: tuple[int, ...]) -> F:
        if wealth >= self.threshold:
            return self.threshold
        for label in labels:
            factor = 1 + self.stake * (2 * label - 1)
            wealth *= factor
            if wealth >= self.threshold:
                return self.threshold
        return wealth

    @staticmethod
    def _release_due_tagged(time: int, belief: Belief):
        due_times = {
            release for _, pending, _ in belief for release, _ in pending if release <= time
        }
        if not due_times:
            return ((F(1), belief, ()),)
        due = min(due_times)
        outcomes = sorted(
            {outcome for _, pending, _ in belief for release, outcome in pending if release == due}
        )
        branches = []
        for outcome in outcomes:
            masses: dict[tuple[int, tuple[tuple[int, int], ...]], F] = defaultdict(F)
            branch_mass = F(0)
            for state, pending, mass in belief:
                if (due, outcome) not in pending:
                    continue
                branch_mass += mass
                remaining = tuple(item for item in pending if item != (due, outcome))
                masses[state, remaining] += mass
            if branch_mass:
                conditional = tuple(
                    (state, pending, mass / branch_mass)
                    for (state, pending), mass in sorted(masses.items())
                    if mass
                )
                branches.append((branch_mass, conditional, (outcome,)))
        return tuple(branches)

    def _gated_value_at(self, time: int, remaining: int, belief: Belief, wealth: F) -> F:
        key = (time, remaining, belief, wealth)
        if key in self._gated_value_cache:
            return self._gated_value_cache[key]
        value = F(0)
        for probability, conditional, labels in self._release_due_tagged(time, belief):
            following_wealth = self._update_wealth(wealth, labels)
            value += probability * self._gated_decision_value(
                time, remaining, conditional, following_wealth
            )
        self._gated_value_cache[key] = value
        return value

    def _gated_decision_value(self, time: int, remaining: int, belief: Belief, wealth: F) -> F:
        key = (time, remaining, belief, wealth)
        if key in self._gated_decision_cache:
            return self._gated_decision_cache[key]
        positive = sum(
            mass * (self.model.emission1 if state else self.model.emission0)
            for state, _, mass in belief
        )
        queries = (0, 1) if remaining else (0,)
        choices = tuple(
            (action, query)
            for action in ((0, 1) if wealth >= self.threshold else (0,))
            for query in queries
        )
        best_value: F | None = None
        best_choice = None
        for action, query in choices:
            if action:
                value = self._promote_value(time, remaining, belief, query)
            else:
                value = positive + self.config.query_cost * query
                if time < self.config.horizon:
                    following = self._transition_belief(time, belief, query)
                    value += self._gated_value_at(time + 1, remaining - query, following, wealth)
            if best_value is None or value < best_value:
                best_value, best_choice = value, (action, query)
        assert best_value is not None and best_choice is not None
        self._gated_actions[key] = best_choice
        self._gated_decision_cache[key] = best_value
        return best_value

    def solve_gated(self):
        """Return the raw optimal gated controller and its alternative cost."""
        initial = self._belief_from_history((), ())
        cost = self._gated_value_at(1, self.config.budget, initial, F(1))
        return cost, self.policy

    def policy(self, history: History, outcomes: Outcomes):
        time = len(history) + 1
        remaining = self.config.budget - sum(query for _, query in history)
        belief = self._belief_from_history(history, outcomes)
        choices = self.choices(history)
        if any(action for action, _ in history):
            key = (time, history[-1][0], remaining, belief)
            if key not in self._continuation_actions:
                self._decision_value(time, history[-1][0], remaining, belief)
            choice = self._continuation_actions[key]
        else:
            wealth = F(1)
            visible = tuple(
                outcome for event, outcome in outcomes if event + self.config.delay <= time
            )
            wealth = self._update_wealth(wealth, visible)
            key = (time, remaining, belief, wealth)
            if key not in self._gated_actions:
                # Off-policy histories receive a safe, nonpromoting fallback.
                choice = (0, 0)
            else:
                choice = self._gated_actions[key]
        return tuple(F(item == choice) for item in choices)

    def state_counts(self) -> dict[str, int]:
        return {
            "prepromotion_value_states": len(self._gated_value_cache),
            "prepromotion_decision_states": len(self._gated_decision_cache),
            "postpromotion_decision_states": len(self._decision_cache),
        }


def mix_with_never_promote(game, policy, activation: F):
    """Behavioral realization of a root lottery between two deterministic plans."""
    safe_choice = (0, 0)

    def safe(history, outcomes):
        return tuple(F(choice == safe_choice) for choice in game.choices(history))

    def consistent(plan, history, outcomes):
        for index, observed_choice in enumerate(history):
            prefix_history = history[:index]
            decision_time = index + 1
            prefix = tuple(row for row in outcomes if row[0] + game.config.delay <= decision_time)
            probabilities = plan(prefix_history, prefix)
            selected = game.choices(prefix_history)
            if (
                sum(
                    (
                        prob
                        for choice, prob in zip(selected, probabilities, strict=True)
                        if choice == observed_choice
                    ),
                    F(0),
                )
                == 0
            ):
                return False
        return True

    def mixture(history, outcomes):
        branches = ((activation, policy), (1 - activation, safe))
        active = [
            (weight, plan)
            for weight, plan in branches
            if weight and consistent(plan, history, outcomes)
        ]
        total = sum((weight for weight, _ in active), F(0))
        if not total:
            return safe(history, outcomes)
        probabilities = [F(0)] * len(game.choices(history))
        for weight, plan in active:
            branch_probabilities = plan(history, outcomes)
            for index, probability in enumerate(branch_probabilities):
                probabilities[index] += weight * probability / total
        return tuple(probabilities)

    return mixture
