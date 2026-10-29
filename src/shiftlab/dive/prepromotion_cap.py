"""First-promotion reference restricted by a pre-promotion query cap.

This is a development comparator, not a new algorithm or a novelty claim.
"""

from __future__ import annotations

from shiftlab.dive.first_promotion_decomposition import FirstPromotionDecomposedGame


class PrePromotionCapGame(FirstPromotionDecomposedGame):
    def __init__(self, config, model, *, pre_cap):
        super().__init__(config, model)
        if type(pre_cap) is not int or not 0 <= pre_cap <= config.budget:
            raise ValueError("pre_cap must be an integer between zero and the total budget")
        self.pre_cap = pre_cap

    def choices(self, history):
        choices = super().choices(history)
        if (
            not any(action for action, _ in history)
            and sum(query for _, query in history) >= self.pre_cap
        ):
            return tuple(choice for choice in choices if choice[1] == 0)
        return choices
