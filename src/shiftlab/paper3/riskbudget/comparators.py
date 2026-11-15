"""Risk-aware comparators for the F3 study: CUSUM rollback and the naive stop-loss plugin.

Both wrap an inner PolicyAdapter (tuned Wald+cutoff). While deployed they query every
disagreement round if labels remain, so monitoring label use is comparable to the shield (pi=1).
"""

from __future__ import annotations

import numpy as np

from ..contracts import Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec


class _Wrap(PolicyAdapter):
    def reset(self, spec: ProblemSpec, rng: np.random.Generator) -> None:
        self.spec, self.k = spec, spec.costs.k
        self.inner.reset(spec, np.random.default_rng(int(rng.integers(2**63))))
        self.blocked = False
        self.n_forced_rollbacks = 0
        self.N = 0
        self._reset()

    def _reset(self) -> None:
        pass

    def _out(self, view: PolicyView, dec: Paper3Decision, action: int) -> Paper3Decision:
        query = dec.query
        if action == 1 and view.event.disagree:
            query = int(view.labels_remaining > 0)
        if view.labels_remaining <= 0:
            query = 0
        if action != view.prev_action:
            self.N += 1
        return Paper3Decision(action, query, dec.compute, dec.retrain)


class CusumRollback(_Wrap):
    """One-sided CUSUM on -z of labels requested while deployed; s > h forces a rollback."""

    def __init__(
        self, inner: PolicyAdapter, h: float, delta_c: float = 0.1, allow_repromote: bool = True
    ):
        self.inner, self.h, self.delta_c, self.allow = inner, h, delta_c, allow_repromote
        self.name = f"cusum_rb[{inner.name}|h={h:g}]"

    def _reset(self):
        self.s, self.t_promo, self.monitoring = 0.0, None, False

    def act(self, view: PolicyView) -> Paper3Decision:
        prev, force = view.prev_action, False
        if self.monitoring and prev == 1:
            for lab in sorted(view.released, key=lambda x: x.t_request):
                if lab.t_request < self.t_promo:
                    continue
                self.s = max(0.0, self.s + (-lab.z) - self.delta_c)
                if self.s > self.h:
                    force = True
                    break
        dec = self.inner.act(view)
        action = dec.action
        if force:
            action = 0
            self.n_forced_rollbacks += 1
            self.s, self.monitoring = 0.0, False
            if not self.allow:
                self.blocked = True
        elif self.blocked:
            action = 0
        if action == 1 and prev == 0:
            self.t_promo, self.s, self.monitoring = view.t, 0.0, True
        elif action == 0:
            self.monitoring = False
        return self._out(view, dec, action)


class StopLossPlugin(_Wrap):
    """Naive risk budget: roll back for good when k N + A > R - k (no pending reserve, no width)."""

    def __init__(self, inner: PolicyAdapter, R: float):
        self.inner, self.R = inner, float(R)
        self.name = f"stoploss[{inner.name}|R={R:g}]"

    def _reset(self):
        self.A = 0.0
        self.queried_dep: set[int] = set()

    def act(self, view: PolicyView) -> Paper3Decision:
        prev = view.prev_action
        for lab in view.released:
            if lab.t_request in self.queried_dep:
                self.A += -lab.z
        dec = self.inner.act(view)
        action = dec.action
        if self.blocked:
            action = 0
        elif action == 1:
            n_eff = self.N + (1 if prev == 0 else 0)
            if self.k * n_eff + self.A > self.R - self.k:
                action = 0
                self.blocked = True
                if prev == 1:
                    self.n_forced_rollbacks += 1
        out = self._out(view, dec, action)
        if action == 1 and out.query and view.event.disagree:
            self.queried_dep.add(view.t)
        return out
