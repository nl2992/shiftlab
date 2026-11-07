"""Policy base class, smoke policies, and deliberately defective policies (tests only)."""

from __future__ import annotations

import math

from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState


class BasePolicy:
    name = "base"

    def reset(self, env: EnvSpec) -> None:
        self.env = env

    def act(self, state: ObservableState):  # pragma: no cover
        raise NotImplementedError


class AlwaysContinue(BasePolicy):
    name = "always_continue"

    def act(self, state):
        return Action("continue")


class UniformQueryNaiveSwitch(BasePolicy):
    """Query on an equally spaced calendar spending the whole label budget; switch to the
    candidate once the mean released paired gain over the last ``window`` labels exceeds the
    hurdle. No evidence control, no rollback: a naive reference, not a competitive baseline."""

    name = "uniform_query_naive_switch"

    def __init__(self, window: int = 10, min_labels: int = 5) -> None:
        self.window, self.min_labels = window, min_labels

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        B, T = env.budget.label_cap, env.T
        self.calendar = {max(1, math.ceil(j * T / B)) for j in range(1, B + 1)} if B else set()

    def act(self, state):
        acts = []
        if state.t in self.calendar and state.b.label_remaining > 0:
            acts.append(Action("query"))  # deterministic calendar: no randomisation claim
        if state.m == INCUMBENT and state.available_labels >= self.min_labels:
            gains = [g for g in (lab.gain() for lab in state.H[-self.window :]) if g is not None]
            if len(gains) >= self.min_labels and sum(gains) / len(gains) > self.env.hurdle:
                acts.append(Action("switch", target=CANDIDATE))
        return acts or Action("continue")


# ------------------------------------------------------------ defective policies (tests only)
class LeakyTruthPolicy(BasePolicy):
    """Holds the evaluator truth (smuggled in) and peeks at it."""

    name = "leaky_truth"

    def __init__(self, truth) -> None:
        self._t = truth

    def act(self, state):
        if self._t.gain_marg[state.t - 1] > 0:
            return Action("switch", target=CANDIDATE)
        return Action("continue")


class LeakyStreamPolicy(BasePolicy):
    name = "leaky_stream"

    def __init__(self, stream) -> None:
        self._s = stream

    def act(self, state):
        _ = self._s.loss_cand[state.t - 1]
        return Action("continue")


class LeakyPendingPolicy(BasePolicy):
    """Queries at t=1 then reads the pending label's value before release."""

    name = "leaky_pending"

    def act(self, state):
        for q in state.Q:
            _ = q.value
        return Action("query") if state.t == 1 else Action("continue")


class SwallowingLeakPolicy(LeakyTruthPolicy):
    """Catches the guard exception; the run must still fail."""

    name = "leaky_swallow"

    def act(self, state):
        try:
            return super().act(state)
        except Exception:  # noqa: BLE001
            return Action("continue")


class OverspendPolicy(BasePolicy):
    name = "overspend"

    def act(self, state):
        return Action("query")


class ActionSpamPolicy(BasePolicy):
    """Issues duplicate/infeasible actions every round; only feasible ones may be charged."""

    name = "action_spam"

    def act(self, state):
        return [
            Action("switch", target=CANDIDATE),
            Action("switch", target=CANDIDATE),
            Action("rollback"),
            Action("retrain"),
            Action("alert"),
            Action("alert"),
        ]
