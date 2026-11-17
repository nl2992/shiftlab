"""Budget-calibrated comparators for F3 (new file; ``comparators.py`` is unchanged).

``StopLossMargin``: the naive stop-loss with an extra safety margin c >= 0 (c = 0 reproduces
``StopLossPlugin`` exactly). ``CusumRollbackBudget``: CUSUM rollback plus a permanent stop when
the realised resolved harm k N + A exceeds R - k. Both are calibrated on simulation seeds only
(scripts/paper3/riskbudget/calibrate_comparators.py).
"""

from __future__ import annotations

from ..contracts import Paper3Decision, PolicyView
from .comparators import CusumRollback, StopLossPlugin


class StopLossMargin(StopLossPlugin):
    """Roll back for good when k N + A > R - k - c (c = 0 is the plain stop-loss)."""

    def __init__(self, inner, R: float, c: float = 0.0):
        super().__init__(inner, R)
        self.c = float(c)
        self.name = f"stoploss_cal[{inner.name}|R={R:g},c={c:g}]"

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
            if self.k * n_eff + self.A > self.R - self.k - self.c:
                action = 0
                self.blocked = True
                if prev == 1:
                    self.n_forced_rollbacks += 1
        out = self._out(view, dec, action)
        if action == 1 and out.query and view.event.disagree:
            self.queried_dep.add(view.t)
        return out


class CusumRollbackBudget(CusumRollback):
    """CUSUM rollback (re-promotion allowed) plus a permanent budget stop k N + A > R - k."""

    def __init__(self, inner, h: float, R: float, delta_c: float = 0.1):
        super().__init__(inner, h, delta_c, allow_repromote=True)
        self.R = float(R)
        self.name = f"cusumrb_cal[{inner.name}|h={h:g},R={R:g}]"

    def _reset(self):
        super()._reset()
        self.A = 0.0
        self.queried_dep: set[int] = set()
        self.budget_stopped = False

    def act(self, view: PolicyView) -> Paper3Decision:
        prev, force = view.prev_action, False
        for lab in view.released:
            if lab.t_request in self.queried_dep:
                self.A += -lab.z
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
        if self.blocked:
            action = 0
        elif action == 1:
            n_eff = self.N + (1 if prev == 0 else 0)
            if self.k * n_eff + self.A > self.R - self.k:
                action = 0
                self.blocked = self.budget_stopped = True
                if prev == 1 and not force:
                    self.n_forced_rollbacks += 1
                self.monitoring = False
        if action == 1 and prev == 0:
            self.t_promo, self.s, self.monitoring = view.t, 0.0, True
        elif action == 0:
            self.monitoring = False
        out = self._out(view, dec, action)
        if action == 1 and out.query and view.event.disagree:
            self.queried_dep.add(view.t)
        return out
