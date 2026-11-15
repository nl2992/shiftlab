"""Risk-budget shield (spec 03F section 4): wraps any inner PolicyAdapter."""

from __future__ import annotations

from dataclasses import replace

import numpy as np

from ..contracts import Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec
from .bounds import BennettMixture


class RiskBudgetShield(PolicyAdapter):
    def __init__(
        self,
        inner: PolicyAdapter,
        R: float,
        delta: float = 0.05,
        pi_menu: tuple[float, ...] = (1.0,),
        margin: float = 0.0,
        label_reserve_frac: float = 0.25,
        ride_out: bool = True,
        use_pending_reserve: bool = True,
        use_rollback_reserve: bool = True,
        use_conf_width: bool = True,
        name: str | None = None,
    ):
        if R < 0 or not pi_menu or min(pi_menu) <= 0 or max(pi_menu) > 1:
            raise ValueError("need R >= 0 and a pi_menu inside (0, 1]")
        self.inner, self.R, self.delta = inner, float(R), delta
        self.pi_menu = tuple(sorted(float(p) for p in pi_menu))
        self.margin, self.label_reserve_frac, self.ride_out = margin, label_reserve_frac, ride_out
        self.use_pending, self.use_rollback = use_pending_reserve, use_rollback_reserve
        self.use_conf = use_conf_width
        self.bound = BennettMixture(delta, self.pi_menu[0])
        self.name = name or f"rbshield[{inner.name}|R={R:g}]"

    # ------------------------------------------------------------------ lifecycle
    def reset(self, spec: ProblemSpec, rng: np.random.Generator) -> None:
        self.spec, self.k, self.T = spec, spec.costs.k, spec.T
        self.L_res = max(0, round(self.label_reserve_frac * spec.B))
        self.inner.reset(spec, np.random.default_rng(int(rng.integers(2**63))))
        self.rng = np.random.default_rng(int(rng.integers(2**63)))
        self.A = self.P = self.V = 0.0
        self.nb = 0
        self.N = 0
        self.exposed: dict[int, list] = {}  # t -> [pi, released]
        self.riding = False
        self.rode_out = False
        self.n_forced_rollbacks = 0
        self.n_vetoed_promotions = 0
        self.I_final = 0.0
        self.I_max = 0.0
        self._a = 0

    def _D(self, V: float) -> float:
        return self.bound.D(V) if self.use_conf else 0.0

    def _I(self, t: int) -> float:
        """Invariant functional after round t (spec I_t, plus remaining horizon in ride-out)."""
        v = self.k * self.N + self.nb + self.A + self._D(self.V)
        if self.use_pending:
            v += self.P
        if self._a and self.use_rollback and not self.riding:
            v += self.k
        if self.riding:
            v += self.T - t
        return v

    # ------------------------------------------------------------------ one round
    def act(self, view: PolicyView) -> Paper3Decision:
        t, prev, g = view.t, view.prev_action, int(view.event.disagree)
        for lab in view.released:  # resolve pending exposed rounds
            e = self.exposed.get(lab.t_request)
            if e is not None and not e[1]:
                e[1] = True
                self.A += -lab.z / e[0]
                self.P -= 1.0 / e[0]
        if abs(self.P) < 1e-12:
            self.P = 0.0

        # inner call (label reserve while undeployed)
        v_in = view
        if prev == 0:
            v_in = replace(view, labels_remaining=max(0, view.labels_remaining - self.L_res))
        dec = self.inner.act(v_in)
        base_k = {"compute": dec.compute, "retrain": dec.retrain}

        P_term = self.P if self.use_pending else 0.0
        R = self.R
        # ---- ride-out
        if self.ride_out and not self.riding and prev == 1:
            lhs = self.k * self.N + self.nb + self.A + P_term + self._D(self.V) + (self.T - t + 1)
            if lhs <= R:
                self.riding = self.rode_out = True
        if self.riding:
            self.nb += g
            self._a = 1
            self.I_final = self._I(t)
            self.I_max = max(self.I_max, self.I_final)
            return Paper3Decision(1, 0, **base_k)

        # ---- shield rule
        action, pi = 0, None  # pi None = blind
        if dec.action == 1:
            reserve = self.k if self.use_rollback else 0.0
            base = self.k * (self.N + (1 if prev == 0 else 0)) + reserve + self.nb + self.A + P_term
            gc = (lambda c: g * c) if self.use_pending else (lambda c: 0.0)
            chosen = None
            if view.labels_remaining > 0:
                for p in self.pi_menu:
                    w = base + gc(1.0 / p) + self._D(self.V + g * (1.0 / p - 1.0))
                    if w <= R - self.margin:
                        chosen = p
                        break
                if chosen is None:
                    w = base + gc(1.0) + self._D(self.V)
                    if w <= R:
                        chosen = 1.0
            else:
                w = base + gc(1.0) + self._D(self.V)
                if w <= R:
                    chosen = 1.0
            if chosen is not None:
                action = 1
                pi = None if view.labels_remaining <= 0 else chosen
            elif prev == 1:
                self.n_forced_rollbacks += 1
            else:
                self.n_vetoed_promotions += 1

        # ---- bookkeeping
        query = 0
        if action == 1:
            if prev == 0:
                self.N += 1
            if g:
                if pi is None:
                    self.nb += 1
                else:
                    self.V += 1.0 / pi - 1.0
                    if pi >= 1.0 or self.rng.random() < pi:
                        query = 1
                        self.exposed[t] = [pi, False]
                        self.P += 1.0 / pi
        else:
            if prev == 1:
                self.N += 1
            elif dec.query and v_in.labels_remaining > 0:
                query = 1  # inner's evidence query while undeployed (x = 0 there)
        self._a = action
        self.I_final = self._I(t)
        self.I_max = max(self.I_max, self.I_final)
        return Paper3Decision(action, query, **base_k)
