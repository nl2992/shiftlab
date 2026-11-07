"""COMMON_CONTRACT_PORT of Gong & Zhang (ICML 2026) paid-observation rules for label acquisition and candidate selection.

See src/shiftlab/sota/gong_zhang/port.py for the mapping and its limits. Short version: exponential weights over
{incumbent, candidate} on released importance-weighted losses; label requests with the paper's p_t = min{1, sqrt(eta_t q_t / c)}
(limited-budget regime) or uniform pacing (sufficient-budget regime), regime picked by Alg 2's threshold; switch when q_cand > 1/2.
The paper has no switching action, no label delay and no drift; its adversarial regret bounds do not transfer.
claimed null: 'none' (no hypothesis test, no certificate).
"""

from __future__ import annotations

from shiftlab.sota.gong_zhang.port import PaidLabelAcquirer

from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState


class GongZhangPolicy(BasePolicy):
    name = "gong_zhang_paid_obs"

    def __init__(self, eta_form: str = "printed") -> None:
        self.eta_form = eta_form

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        self.acq = PaidLabelAcquirer(
            env.T, max(env.costs.c_q, 1e-9), env.budget.label_cap, env.hurdle, self.eta_form
        )
        self.seen: set[int] = set()

    def act(self, state: ObservableState):
        for lab in state.H:
            if lab.label_id in self.seen:
                continue
            self.seen.add(lab.label_id)
            li, lc = lab.loss(INCUMBENT), lab.loss(CANDIDATE)
            if li is not None and lc is not None:
                self.acq.on_release(li, lc, lab.propensity)
        acts = []
        if state.b.label_remaining > 0 and state.u:
            hit, p = self.acq.decide(state.t, state.u[0])
            if hit:
                acts.append(Action("query", propensity=p, u_index=0))
        if state.m == INCUMBENT and self.acq.prefers_candidate():
            acts.append(Action("switch", target=CANDIDATE))
        return acts or Action("continue")


class _GZAdapter:
    name = "gong_zhang_paid_obs"
    vocabulary = ("query", "continue", "switch")
    claimed_null = "none"
    port_status = "COMMON_CONTRACT_PORT"

    def __init__(self, **kw) -> None:
        self.kw = kw

    def build(self, env: EnvSpec) -> BasePolicy:
        p = GongZhangPolicy(**self.kw)
        p.reset(env)
        return p


GongZhangAdapter = _GZAdapter()
