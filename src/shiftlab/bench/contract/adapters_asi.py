"""COMMON_CONTRACT_PORT of Active Statistical Inference (Zrnic & Candes 2024) as a label-efficient candidate-vs-incumbent monitor.

Labelled COMMON_CONTRACT_PORT / ASI-inspired; see src/shiftlab/sota/asi/streaming.py for what is from the papers and what is ours.
Fidelity notes:
* target d_t = loss_inc - loss_cand in [-1, 1] (losses in [0,1]); predictor f_t = shrunk running mean of RELEASED gains
  (prior 0, weight ``n0``); uncertainty u_t(x) = smoothed running mean |d - f| in quantile bins of the monitor signal (bins fixed from
  the first ``warmup`` rounds) for the sampling rule of Eq. (8) with tau = 0.5 mixing and budget n_b = label cap, n = T.
* propensity pi_t is drawn with state.u[0] and declared; pi_t >= pi_min = tau n_b / n by the mixture. The label is used at release,
  with the f_t and pi_t frozen at request. Increments are consumed in round order (see StreamingASI).
* decision: switch to the candidate once the anytime-valid one-sided evidence for H0_cond: E[d_t | past] <= h (h = env.hurdle)
  crosses 1/alpha (claimed null: 'cond', validity only under the stated assumptions: bounded losses, propensity predictable,
  selection by declared randomisation, f_t from released labels). No rollback, no retrain.
* the one-sided validity is our derivation, not a theorem of the ASI paper (see streaming.py); the IPW range ~1/pi_min makes it
  conservative.
"""

from __future__ import annotations

import numpy as np

from shiftlab.sota.asi import SequentialRule, StreamingASI

from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState


class ASIMonitorPolicy(BasePolicy):
    name = "asi_streaming"

    def __init__(
        self,
        alpha: float = 0.05,
        tau: float = 0.5,
        n0: float = 5.0,
        K: int = 3,
        warmup: int = 20,
        fill_every: int = 0,
    ) -> None:
        self.alpha, self.tau, self.n0, self.K, self.warmup, self.fill_every = (
            alpha,
            tau,
            n0,
            K,
            warmup,
            fill_every,
        )

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        B = max(env.budget.label_cap, 1)
        self.rule = SequentialRule(n=env.T, n_b=B, tau=self.tau, fill_every=self.fill_every)
        pi_min = self.tau * B / env.T
        self.mon = StreamingASI(
            d_lo=-1.0, d_hi=1.0, pi_min=pi_min, alpha=self.alpha, hurdle=env.hurdle
        )
        self.sum_d, self.n_d = 0.0, 0
        self.err_sum = np.zeros(self.K)
        self.err_n = np.zeros(self.K)
        self.edges = None
        self.seen: set[int] = set()
        self.reqs: dict[int, tuple[float, float]] = {}  # label_round -> (f, pi) frozen at request

    def _bin(self, x: float) -> int:
        return 0 if self.edges is None else int(np.searchsorted(self.edges, x))

    def _f(self) -> float:
        return self.sum_d / (self.n_d + self.n0)

    def _u(self, x: float) -> float:
        k = self._bin(x)
        return (self.err_sum[k] + 0.5) / (self.err_n[k] + 1.0)  # smoothed mean |d - f| (prior 0.5)

    def act(self, state: ObservableState):
        t = state.t
        # 1. consume newly released labels (delivery order)
        for lab in state.H:
            if lab.label_id in self.seen:
                continue
            self.seen.add(lab.label_id)
            g = lab.gain()
            if g is None or lab.label_round not in self.reqs:
                continue
            f_req, _ = self.reqs[lab.label_round]
            self.mon.resolve(lab.label_round, g)
            k = self._bin(float(state.x_hist[lab.label_round - 1]))
            self.err_sum[k] += abs(g - f_req)
            self.err_n[k] += 1
            self.sum_d += g
            self.n_d += 1
        if self.edges is None and t > self.warmup:
            self.edges = np.quantile(
                np.asarray(state.x_hist[: self.warmup], float), np.linspace(0, 1, self.K + 1)[1:-1]
            )
        # 2. query decision at t (f_t, pi_t frozen now)
        acts = []
        u_t = self._u(state.x)
        pi = self.rule.propose(u_t)
        f = self._f()
        queried = False
        if state.b.label_remaining > 0 and state.u and state.u[0] < pi:
            acts.append(Action("query", propensity=pi, u_index=0))
            queried = True
            self.reqs[t] = (f, pi)
        self.rule.record(int(queried), u_t)
        self.mon.register(t, f, pi, queried)
        if state.m == INCUMBENT and self.mon.alarm():
            acts.append(Action("switch", target=CANDIDATE))
        return acts or Action("continue")


class _ASIAdapter:
    name = "asi_streaming"
    vocabulary = ("query", "continue", "switch")
    claimed_null = "cond"
    port_status = "COMMON_CONTRACT_PORT"

    def __init__(self, **kw) -> None:
        self.kw = kw

    def build(self, env: EnvSpec) -> BasePolicy:
        p = ASIMonitorPolicy(**self.kw)
        p.reset(env)
        return p


ASIAdapter = _ASIAdapter()
