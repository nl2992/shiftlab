"""Core baselines behind the ``PolicyAdapter`` interface (labels: see ``LABELS``).

Ported (arithmetic only, re-expressed on ``PolicyView``; deployed action is read from
``view.prev_action`` rather than kept as hidden state, so a gate can override safely):
  * Wald/LCB economic switcher with discounting (lam, gamma) and the late-label cutoff
    ``stop_h``: research/paper1-eqsdp-foundation-2026-11-08@5bda4e73
      scripts/qsg_methods_search/hurdles.py (WaldLCB._q) and scripts/qsg_methods_search/eqs_d.py
      (_gain_away, observe rule), scripts/paper1_eqsdp/stage1_policies.py (keep(): cutoff
      ``t + delay <= T - stop_h``).
  * Budget-paced disagreement acquisition (PacedDisagreementAcquisition):
    same ref, scripts/promising_directions/sota/competitors/controls.py.
Everything else (CUSUM, Page-Hinkley, calendar/uniform acquisition, gate) is IN_HOUSE_HEURISTIC.
No false-promotion guarantee is claimed for any baseline except as stated for ``Gate``.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm

from .contracts import Paper3Decision, PolicyAdapter, PolicyView, ProblemSpec

LABELS = {
    "never": "IN_HOUSE_HEURISTIC",
    "always": "IN_HOUSE_HEURISTIC",
    "periodic": "IN_HOUSE_HEURISTIC",
    "wald_paced": "DOCUMENTED_ADAPTER (EQSDp-arm-R-style Wald/LCB, paced acquisition)",
    "wald_paced_cutoff": "DOCUMENTED_ADAPTER (adds the late-label cutoff)",
    "wald_uniform": "IN_HOUSE_HEURISTIC (uniform random query + Wald switch)",
    "wald_calendar": "IN_HOUSE_HEURISTIC (fixed calendar query + Wald switch)",
    "cusum": "IN_HOUSE_HEURISTIC",
    "page_hinkley": "IN_HOUSE_HEURISTIC",
    "gate_wald": "IN_HOUSE_HEURISTIC (alpha-gate over wald_paced)",
}


class _Base(PolicyAdapter):
    def reset(self, spec: ProblemSpec, rng: np.random.Generator) -> None:
        self.spec, self.rng = spec, rng
        self.T, self.B = spec.T, spec.B
        self.d = spec.delay_known if spec.delay_known is not None else 1
        self._reset()

    def _reset(self) -> None:  # hook
        pass


class NeverSwitch(_Base):
    name = "never"

    def act(self, view: PolicyView) -> Paper3Decision:
        return Paper3Decision(0)


class AlwaysChallenger(_Base):
    name = "always"

    def act(self, view: PolicyView) -> Paper3Decision:
        return Paper3Decision(1)


class PeriodicSwitch(_Base):
    """Toggle the deployed model every ``period`` rounds, no queries (naive scheduled rotation)."""

    def __init__(self, period: int = 50):
        self.period, self.name = period, f"periodic{period}"

    def act(self, view: PolicyView) -> Paper3Decision:
        return Paper3Decision(((view.t - 1) // self.period) % 2)


# ---------------------------------------------------------------------------------- acquisition
class PacedAcq:
    """Spend remaining budget evenly over expected remaining disagreements (floor p_min)."""

    def __init__(self, T, p_min=0.05, prior_rate=0.25, prior_w=20.0):
        self.T, self.p_min, self.prior_rate, self.prior_w = T, p_min, prior_rate, prior_w
        self.n_dis = 0

    def rate(self, t):
        return (self.n_dis + self.prior_rate * self.prior_w) / (t + self.prior_w)

    def propensity(self, t, remaining, disagree):
        if not disagree or remaining <= 0:
            return 0.0
        left = max(self.rate(t) * (self.T - t), 1e-9)
        return float(min(max(remaining / left, self.p_min), 1.0))


class _Acquirer:
    """kind in {paced, uniform, calendar}; ``stop_h`` is the late-label cutoff (None = off)."""

    def __init__(self, kind: str, stop_h: int | None):
        self.kind, self.stop_h = kind, stop_h

    def reset(self, T, B, d, rng):
        self.T, self.B, self.d, self.rng = T, B, d, rng
        self.paced = PacedAcq(T)
        last = T - d - (self.stop_h or 0)
        self.cal = set(np.unique(np.round(np.linspace(1, max(last, 1), B)).astype(int)).tolist())

    def query(self, view: PolicyView) -> int:
        t, rem, dis = view.t, view.labels_remaining, view.event.disagree
        self.paced.n_dis += int(dis)
        open_ = self.stop_h is None or t + self.d <= self.T - self.stop_h
        if rem <= 0 or not open_:
            return 0
        if self.kind == "paced":
            pr = self.paced.propensity(t, rem, dis)
            return int(pr > 0 and self.rng.random() < pr)
        if self.kind == "uniform":
            return int(self.rng.random() < min(1.0, rem / (self.T - t + 1)))
        return int(t in self.cal)


# ---------------------------------------------------------------------------------- switchers
class WaldEconomic(_Base):
    """Discounted disagreement-outcome counts, Wald lower confidence bound, remaining-horizon
    payback: switch away from deployed model m when (adv_LCB) * rate * (T - t) > k."""

    def __init__(self, lam=0.98, gamma=0.3, acq="paced", stop_h=None, name=None):
        self.lam, self.gamma = lam, gamma
        self.acq = _Acquirer(acq, stop_h)
        self.name = name or f"wald_{acq}"

    def _reset(self):
        self.n = self.kk = 0.0
        self.acq.reset(self.T, self.B, self.d, self.rng)
        self.dep = 0

    def _q(self, lev):
        n = max(self.n, 1e-9)
        p = (self.kk + 0.5) / (n + 1.0)
        se = math.sqrt(p * (1 - p) / (n + 1.0))
        return min(1.0, max(0.0, p + norm.ppf(lev) * se))

    def _gain_away(self, dep, t):
        p = self._q(self.gamma if dep == 0 else 1.0 - self.gamma)
        adv = (2 * p - 1) if dep == 0 else (1 - 2 * p)
        rate = self.acq.paced.rate(t)
        return adv * rate * (self.T - t)

    def act(self, view: PolicyView) -> Paper3Decision:
        dep = view.prev_action
        for lab in sorted(view.released, key=lambda x: x.t_request):
            d = lab.ell0 - lab.ell1
            if d == 0:
                continue
            self.n = self.lam * self.n + 1.0
            self.kk = self.lam * self.kk + float(d > 0)
            if self._gain_away(dep, view.t) > self.spec.costs.k:
                dep = 1 - dep
        return Paper3Decision(dep, self.acq.query(view))


class _Detector(_Base):
    """Two-sided sequential detector on released Z; paced acquisition; reset on each switch."""

    def __init__(self, stop_h=None):
        self.acq = _Acquirer("paced", stop_h)

    def _reset(self):
        self.acq.reset(self.T, self.B, self.d, self.rng)
        self._clear()

    def act(self, view: PolicyView) -> Paper3Decision:
        dep = view.prev_action
        for lab in sorted(view.released, key=lambda x: x.t_request):
            z = lab.ell0 - lab.ell1
            if self._update(z if dep == 0 else -z):  # evidence the other model is better
                dep = 1 - dep
                self._clear()
        return Paper3Decision(dep, self.acq.query(view))


class CUSUM(_Detector):
    def __init__(self, delta=0.1, h=4.0, stop_h=None):
        super().__init__(stop_h)
        self.delta, self.h, self.name = delta, h, "cusum"

    def _clear(self):
        self.s = 0.0

    def _update(self, y):
        self.s = max(0.0, self.s + y - self.delta)
        return self.s > self.h


class PageHinkley(_Detector):
    def __init__(self, delta=0.05, lam=5.0, stop_h=None):
        super().__init__(stop_h)
        self.delta, self.lam, self.name = delta, lam, "page_hinkley"

    def _clear(self):
        self.m = self.mn = self.mean = 0.0
        self.i = 0

    def _update(self, y):
        self.i += 1
        self.mean += (y - self.mean) / self.i
        self.m += y - self.mean - self.delta
        self.mn = min(self.mn, self.m)
        return self.m - self.mn > self.lam


# ---------------------------------------------------------------------------------- gate wrapper
class Gate(PolicyAdapter):
    """Blocks the first 0 -> 1 promotion until a betting e-process on released Z reaches 1/alpha.

    W <- W (1 + lam Z), Z in [-1, 1], lam in [0, 1] fixed (predictable): a nonnegative
    supermartingale when E[Z | past] <= 0, so P(W ever >= 1/alpha) <= alpha under the global
    no-benefit null for the observed (released) rounds, provided query decisions are
    history-measurable. Valid only for that null; it says nothing about the economics of a switch.
    After opening, the inner policy is unrestricted (a global-null guarantee only).
    """

    def __init__(self, inner: PolicyAdapter, alpha: float = 0.1, lam: float = 0.25):
        self.inner, self.alpha, self.lam = inner, alpha, lam
        self.name = f"gate_{inner.name.replace('wald_paced', 'wald')}"

    def reset(self, spec, rng):
        self.inner.reset(spec, rng)
        self.w, self.open = 1.0, False

    def act(self, view: PolicyView) -> Paper3Decision:
        for lab in view.released:
            self.w *= 1.0 + self.lam * (lab.ell0 - lab.ell1)
        self.open = self.open or self.w >= 1.0 / self.alpha
        dec = self.inner.act(view)
        if dec.action == 1 and view.prev_action == 0 and not self.open:
            return Paper3Decision(0, dec.query, dec.compute, dec.retrain)
        return dec


def default_baselines(T: int) -> list[PolicyAdapter]:
    cut = max(int(0.15 * T), 1)
    return [
        NeverSwitch(),
        AlwaysChallenger(),
        PeriodicSwitch(max(T // 6, 1)),
        WaldEconomic(0.98, 0.3, "paced", None, "wald_paced"),
        WaldEconomic(0.98, 0.3, "paced", cut, "wald_paced_cutoff"),
        WaldEconomic(0.98, 0.3, "uniform", None, "wald_uniform"),
        WaldEconomic(0.98, 0.3, "calendar", None, "wald_calendar"),
        CUSUM(),
        PageHinkley(),
        Gate(WaldEconomic(0.98, 0.3, "paced", None, "wald_paced")),
    ]
