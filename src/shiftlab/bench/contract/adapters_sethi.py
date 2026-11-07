"""COMMON_CONTRACT_PORT of the Sethi et al. (ICML 2026) sequential Markov test as a SHIFT SENTINEL.

Fidelity notes (every simplification vs the native method):
* native data: a finite ergodic chain observed at every step; here the symbol is the quantile bin of the unlabelled monitor
  signal ``state.x`` (K bins fixed from the first ``warmup`` rounds only: train-only binning).
* null class = {P : pi0 P = pi0} with pi0 = (smoothed) bin frequencies of the warm-up window: "the monitor-signal chain keeps its
  nominal marginal law". This is a DECLARED class chosen by us; it is not a harm null.
* output = alarm evidence only. The test rejects a stationarity null of the MONITOR chain; it says nothing about loss or harm
  (claimed null: 'none'). ``switch_on_alarm`` (default False) additionally promotes the candidate on alarm, which is a naive
  detector-triggered policy and is reported as such, never as a harm-controlled gate.
* labels are not used; delays/missingness do not touch the monitor chain.
"""

from __future__ import annotations

import numpy as np

from shiftlab.sota.sethi import SequentialMarkovTest, StationaryNull

from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState


class SethiSentinelPolicy(BasePolicy):
    name = "sethi_sentinel"

    def __init__(
        self,
        K: int = 4,
        alpha: float = 0.05,
        warmup: int | None = None,
        switch_on_alarm: bool = False,
        check_every: int = 10,
    ) -> None:
        self.K, self.alpha, self.warmup = K, alpha, warmup
        self.switch_on_alarm, self.check_every = switch_on_alarm, check_every

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        self.W = self.warmup or max(20, env.T // 10)
        self.edges = None
        self.test = None
        self.alerted = False

    def _bin(self, x: float) -> int:
        return int(np.searchsorted(self.edges, x))

    def act(self, state: ObservableState):
        t = state.t
        if t < self.W:
            return Action("continue")
        if self.edges is None:  # fit on rounds 1..W-1 (x_hist) only
            warm = np.asarray(state.x_hist[: self.W - 1], float)
            self.edges = np.quantile(warm, np.linspace(0, 1, self.K + 1)[1:-1])
            counts = np.bincount([self._bin(v) for v in warm], minlength=self.K) + 1.0
            self.test = SequentialMarkovTest(
                self.K,
                self.alpha,
                StationaryNull(counts / counts.sum()),
                check_every=self.check_every,
            )
            self.test.update(self._bin(float(state.x_hist[-1])))  # X_0 = last warm-up symbol
        rej = self.test.update(self._bin(float(state.x)))
        acts = []
        if rej and not self.alerted:
            self.alerted = True
            acts.append(Action("alert"))
        if rej and self.switch_on_alarm and state.m == INCUMBENT:
            acts.append(Action("switch", target=CANDIDATE))
        return acts or Action("continue")


class _SethiAdapter:
    name = "sethi_sentinel"
    vocabulary = ("alert", "continue", "switch")
    claimed_null = (
        "none"  # monitors a stationarity null of the monitor chain, not cond/marg/abs_risk
    )
    port_status = "COMMON_CONTRACT_PORT"

    def __init__(self, **kw) -> None:
        self.kw = kw

    def build(self, env: EnvSpec) -> BasePolicy:
        p = SethiSentinelPolicy(**self.kw)
        p.reset(env)
        return p


SethiAdapter = _SethiAdapter()
