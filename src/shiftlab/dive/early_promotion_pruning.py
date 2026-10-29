"""Development adapter: skip dominated first-promotion continuations.

The reference solver and its information sets are unchanged. The numerical LP
wrapper is process-global and therefore only safe in the isolated serial runner.
"""

from __future__ import annotations

from fractions import Fraction as F
from unittest.mock import patch

from scipy.optimize import linprog

import shiftlab.dive.causal_switching_game as reference
from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame


class EarlyPromotionPruning(FirstPromotionDecomposedGame):
    def __init__(self, config, model, *, epsilon=F(0)):
        super().__init__(config, model)
        if not isinstance(epsilon, F) or epsilon < 0:
            raise ValueError("epsilon must be a nonnegative exact fraction")
        self.epsilon = epsilon
        self.forbidden_columns: set[int] = set()
        self.skipped_continuations = 0
        self.marked_information = set()

    def dominated(self, time, belief):
        p1 = sum((mass for state, _, mass in belief if state == 1), F(0))
        stay, lower = F(0), self.config.switch_cost
        for event in range(time, self.config.horizon + 1):
            positive = self.model.emission(p1)
            stay += positive
            if event == time:
                lower += 1 - positive
            else:
                lower += (1 - p1) * min(self.model.emission0, 1 - self.model.emission0)
                lower += p1 * min(self.model.emission1, 1 - self.model.emission1)
            p1 = self.model.propagate(p1, 1)
        return lower >= stay - self.epsilon

    def _alternative(self, history, outcomes, sequence, weight, posterior, total_cost):
        self._node()
        time = len(history) + 1
        if time > self.config.horizon:
            self.cost[sequence] += float(weight * total_cost)
            return
        state1 = self.model.propagate(posterior, 1)
        positive = self.model.emission(state1)
        choices = self.choices(history)
        info = self.information(history, outcomes)
        children = self.learner.add(info, sequence, choices)
        for (action, query), child in zip(choices, children, strict=True):
            if action:
                belief = self._belief_from_history(history, outcomes)
                if self.dominated(time, belief):
                    self.forbidden_columns.add(child)
                    self.marked_information.add(info)
                    self.skipped_continuations += 1
                    continue
                continuation = self._promote_value(
                    time, self.config.budget - sum(q for _, q in history), belief, query
                )
                self.cost[child] += float(weight * (total_cost + continuation))
                continue
            cost = positive + self.config.query_cost * query
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

    def solve(self):
        self.build()

        def restrict(*args, **kwargs):
            bounds = list(kwargs["bounds"])
            for column in self.forbidden_columns:
                bounds[column] = (0, 0)
            kwargs["bounds"] = bounds
            return linprog(*args, **kwargs)

        with patch.object(reference, "linprog", restrict):
            return super().solve()
