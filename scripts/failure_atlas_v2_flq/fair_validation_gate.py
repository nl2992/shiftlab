"""One-look, in-horizon validation gate for a pre-specified two-model challenger.

This is a conventional fixed-candidate baseline, not a proposed novel method. Its exact
one-sided binomial bound is meaningful only when queried disagreement signs are iid Bernoulli.
"""

from __future__ import annotations

from scipy.stats import beta
from simulator import Event, QueryRequest, ReleasedFeedback


class FairValidationGate:
    def __init__(self, horizon, budget, switch_cost, delay, rng, *, validation_end=400, alpha=0.05):
        del rng
        self.name = "fair_validation_gate"
        self.horizon = int(horizon)
        self.budget = int(budget)
        self.switch_cost = float(switch_cost)
        self.delay = int(delay)
        self.validation_end = int(validation_end)
        self.decision_time = self.validation_end + self.delay
        self.alpha = float(alpha)
        self.disagreements = 0
        self.challenger_wins = 0
        self.promote = False
        self.decided = False

    def predict(self, event: Event) -> int:
        if not self.decided and event.t >= self.decision_time:
            self.decided = True
            n = self.disagreements
            if n:
                p_lower = (
                    0.0
                    if self.challenger_wins == 0
                    else float(
                        beta.ppf(self.alpha, self.challenger_wins, n - self.challenger_wins + 1)
                    )
                )
                gain_lower = 2.0 * p_lower - 1.0
                observed_disagreement_rate = n / self.validation_end
                projected_gain = (self.horizon - event.t) * observed_disagreement_rate * gain_lower
                self.promote = gain_lower > 0.0 and projected_gain > self.switch_cost
        return int(self.promote)

    def request_labels(self, event: Event, remaining_budget: int) -> QueryRequest:
        eligible = (
            event.t < self.validation_end
            and event.model_predictions[0] != event.model_predictions[1]
            and remaining_budget > 0
        )
        return QueryRequest(bool(eligible), 1.0 if eligible else 0.0)

    def observe(self, feedback: list[ReleasedFeedback]) -> None:
        for item in feedback:
            d = int(item.model_losses[0]) - int(item.model_losses[1])
            if d:
                self.disagreements += 1
                self.challenger_wins += int(d > 0)

    def state_dict(self) -> dict:
        return {k: v for k, v in vars(self).items() if k != "name"}

    def load_state_dict(self, state: dict) -> None:
        for key, value in state.items():
            setattr(self, key, value)

    def decision_state(self) -> str:
        return (
            f"n={self.disagreements};wins={self.challenger_wins};"
            f"decided={self.decided};promote={self.promote}"
        )


def _factory(T, budget, cs, cq, alpha, delay, rng):
    del cq, alpha
    return FairValidationGate(T, budget, cs, delay, rng)


EXTRA = {"fair_validation_gate": _factory}
