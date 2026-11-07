"""COMMON_CONTRACT_PORT of the simple Q2 controls required by the Mandate (uniform / pending cap / fixed schedule).

NEW file; does not touch the other contract modules. Each control is a ``RuleSwitchPolicy``: a query rule (when to
spend a label) plus the SAME decision rule as ``UniformQueryNaiveSwitch`` (switch to the candidate once the mean
released paired gain over the last ``window`` labels exceeds the public hurdle). Only the acquisition differs, so the
controls isolate the value of a smarter acquisition rule. They make NO validity claim (claimed null 'none');
they are naive references, not certificates.

* ``fixed_schedule``  : deterministic equally spaced calendar over the whole label budget (identical in behaviour to
  ``UniformQueryNaiveSwitch``; registered separately so the ledger names the required control).
* ``uniform_query``   : each round is queried independently with the fixed rate q = B/T using the shared uniform
  ``state.u[0]``; the declared propensity is q (verified by the simulator).
* ``pending_cap``     : query every round while the number of outstanding requests is below ``cap`` (default
  max(1, 0.10 B)) and budget remains (the 'simple pending cap' of Mandate Q2).

``RuleSwitchPolicy`` also accepts custom ``switch_rule`` / ``rollback_rule`` objects (used by Stage-B contract-native
candidates); with the defaults it reproduces ``UniformQueryNaiveSwitch`` exactly (tested).
"""

from __future__ import annotations

import math

from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState

PORT_STATUS = "COMMON_CONTRACT_PORT"


class CalendarRule:
    """Equally spaced deterministic calendar spending the whole label budget."""

    def reset(self, env: EnvSpec) -> None:
        B, T = env.budget.label_cap, env.T
        self.calendar = {max(1, math.ceil(j * T / B)) for j in range(1, B + 1)} if B else set()

    def query(self, state: ObservableState) -> Action | None:
        if state.t in self.calendar and state.b.label_remaining > 0:
            return Action("query")  # deterministic: no randomisation claim
        return None


class UniformRateRule:
    """Bernoulli(q = B/T) per round via the shared uniform; the declared propensity is q."""

    def reset(self, env: EnvSpec) -> None:
        self.q = min(1.0, env.budget.label_cap / env.T)

    def query(self, state: ObservableState) -> Action | None:
        if state.b.label_remaining <= 0 or not state.u:
            return None
        if state.u[0] < self.q:
            return Action("query", propensity=self.q, u_index=0)
        return None


class PendingCapRule:
    """Query whenever fewer than ``cap`` requests are outstanding (deterministic)."""

    def __init__(self, cap: int | None = None, frac: float = 0.10) -> None:
        self.cap0, self.frac = cap, frac

    def reset(self, env: EnvSpec) -> None:
        self.cap = self.cap0 or max(1, round(self.frac * env.budget.label_cap))

    def query(self, state: ObservableState) -> Action | None:
        if state.b.label_remaining > 0 and state.b.pending < self.cap:
            return Action("query")
        return None


class GainSwitchRule:
    """Host decision rule of ``UniformQueryNaiveSwitch`` (mean released gain of the last ``window`` labels > hurdle)."""

    def __init__(self, window: int = 10, min_labels: int = 5) -> None:
        self.window, self.min_labels = window, min_labels

    def reset(self, env: EnvSpec) -> None:
        self.env = env

    def promote(self, state: ObservableState) -> bool:
        if state.m != INCUMBENT or state.available_labels < self.min_labels:
            return False
        gains = [g for g in (lab.gain() for lab in state.H[-self.window :]) if g is not None]
        return len(gains) >= self.min_labels and sum(gains) / len(gains) > self.env.hurdle


class RuleSwitchPolicy(BasePolicy):
    def __init__(self, query_rule=None, switch_rule=None, rollback_rule=None, name="rule_switch"):
        self.name = name
        self.query_rule = query_rule or CalendarRule()
        self.switch_rule = switch_rule or GainSwitchRule()
        self.rollback_rule = rollback_rule

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        for r in (self.query_rule, self.switch_rule, self.rollback_rule):
            if r is not None and hasattr(r, "reset"):
                r.reset(env)
        self.log: list[dict] = []

    def act(self, state: ObservableState):
        acts: list[Action] = []
        q = self.query_rule.query(state)
        if q is not None:
            pcap = self.env.budget.pending_cap
            if pcap is None or state.b.pending < pcap:
                acts.append(q)
        if (
            self.rollback_rule is not None
            and state.m == CANDIDATE
            and self.rollback_rule.rollback(state)
        ):
            acts.append(
                Action("rollback")
                if state.prev_m is not None
                else Action("switch", target=INCUMBENT)
            )
        elif self.switch_rule.promote(state):
            acts.append(Action("switch", target=CANDIDATE))
        return acts or Action("continue")


class _ControlAdapter:
    vocabulary = ("query", "continue", "switch")
    claimed_null = "none"
    port_status = PORT_STATUS

    def __init__(self, name: str, rule_factory) -> None:
        self.name, self.rule_factory = name, rule_factory

    def build(self, env: EnvSpec) -> BasePolicy:
        p = RuleSwitchPolicy(self.rule_factory(), name=self.name)
        p.reset(env)
        return p


FixedScheduleAdapter = _ControlAdapter("fixed_schedule", CalendarRule)
UniformQueryAdapter = _ControlAdapter("uniform_query", UniformRateRule)
PendingCapAdapter = _ControlAdapter("pending_cap", PendingCapRule)
CONTROLS = {
    "fixed_schedule": FixedScheduleAdapter,
    "uniform_query": UniformQueryAdapter,
    "pending_cap": PendingCapAdapter,
}
