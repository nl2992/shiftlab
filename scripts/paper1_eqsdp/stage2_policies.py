"""Stage 2 policies (docs/paper1_eqsdp/10_JOINTBAYES_PLAN.md, Stage 2).

Everything subclasses Stage 1 classes (which subclass the frozen ``EQSD``); no frozen code is edited.
Information rule as in Stage 1: a policy sees the event (t, predictions), the remaining budget,
released paired losses (at release time) and the declared contract (T, B, c_s, delay).

``Stage2Policy`` = EQSDp (arm R evidence, Beta posterior) with optional modules:

* C1 gate (``rho0 > 0``): Stage 1 reachability gate + shadow price, unchanged.
* stop ``stop_h`` (``None`` = off): no purchase when t + delay > T - stop_h (``0`` = only labels
  that can never be released). Skips caused by the stop are not debited from the pacer view.
* module B (``bw``): pending labels enter the reachability lookahead with weight bw,
  L = round(bw * pending) + 1 + h. bw = 1 is Stage 1 C1; bw = 0 ignores in-flight labels.
* module G (``gs``): dependence-calibrated belief. The lag-1 autocorrelation r of successive
  released disagreement outcomes is estimated online exactly as in ``DepWald``
  (scripts/qsg_methods_search/next_method.py, discounted pair counts, factor 0.98, prior 10
  pseudo-pairs) and the Beta counts are divided by f = ((1 + r) / (1 - r)) ** gs, an effective
  sample size correction. gs = 0 is the plain posterior.

With bw = 1, gs = 0, stop_h = None it equals ``Stage1C1`` exactly; with rho0 = 0 and gs = 0 it equals
EQSDp plus the stop (``Stage1C1Stop``) exactly (both tested).
"""

from __future__ import annotations

import math

from scipy.stats import beta as _beta
from scipy.stats import betabinom as _bb
from stage1_policies import Stage1C1, Stage1C1Stop, Stage1WaldStop

LAM_R, R_CAP, R_PRIOR = 0.98, 0.9, 10.0  # DepWald defaults (NEXT_METHOD_RESULTS stage 6)


class Stage2Policy(Stage1C1):
    def __init__(self, *a, stop_h=None, bw=1.0, gs=0.0, thin=1.0, **kw):
        super().__init__(*a, **kw)
        self.thin = float(thin)  # uniform keep-probability (reference-grid control only)
        self.stop_h = None if stop_h is None else int(stop_h)
        self.bw, self.gs = float(bw), float(gs)
        self.undo = 0  # stop-caused skips (not debited from the pacer view)
        self.prev = None
        self.c11 = self.c1x = self.cx1 = self.cp = 0.0
        self.r = 0.0

    # --- module G -------------------------------------------------------------------------
    def _f(self):
        if self.gs <= 0.0:
            return 1.0
        return ((1.0 + self.r) / (1.0 - self.r)) ** self.gs

    def _q(self, lev):
        f = self._f()
        return float(_beta.ppf(lev, self.k / f + 1.0, (self.n - self.k) / f + 1.0))

    def observe(self, feedback):
        for fb in sorted(feedback, key=lambda f: f.event_id):
            self.pending -= 1
            d = int(fb.model_losses[0]) - int(fb.model_losses[1])
            if d == 0:
                continue
            z = float(d > 0)
            if self.prev is not None:  # DepWald's lag-1 estimate, ported unchanged
                lr = LAM_R
                self.cp = lr * self.cp + 1.0
                self.c11 = lr * self.c11 + self.prev * z
                self.c1x = lr * self.c1x + self.prev
                self.cx1 = lr * self.cx1 + z
                pa, pb = self.c1x / self.cp, self.cx1 / self.cp
                cov = self.c11 / self.cp - pa * pb
                var = math.sqrt(max(pa * (1 - pa) * pb * (1 - pb), 1e-9))
                r = (cov / var) * self.cp / (self.cp + R_PRIOR)
                self.r = min(R_CAP, max(0.0, r))
            self.prev = z
            self.n = self.lam * self.n + 1.0
            self.k = self.lam * self.k + z
            self.t = fb.t_released
            if self._gain_away(self.gamma) > self.cs:
                self.deployed = 1 - self.deployed

    # --- C1 reachability with module B and G ------------------------------------------------
    def _gain(self, n2, k2, tt, rate):
        f = self._f()
        lev = self.gamma if self.deployed == 0 else 1.0 - self.gamma
        p = float(_beta.ppf(lev, k2 / f + 1.0, (n2 - k2) / f + 1.0))
        adv = (2 * p - 1) if self.deployed == 0 else (1 - 2 * p)
        return adv * rate * (self.T - tt)

    def p_cross(self, t):
        L = round(self.bw * self.pending) + 1 + self.h
        lam = self.lam
        geo = (1.0 - lam**L) / (1.0 - lam)
        w = geo / L
        n_dec, k_dec = lam**L * self.n, lam**L * self.k
        n2 = n_dec + L * w
        tt = t + self.delay
        rate = self._rate()
        if self.T - tt <= 0 or rate * (self.T - tt) <= self.cs:
            return 0.0

        def reach_gain(o):
            ones = o if self.deployed == 0 else L - o
            return self._gain(n2, k_dec + ones * w, tt, rate)

        if reach_gain(L) <= self.cs:
            return 0.0
        if reach_gain(0) > self.cs:
            return 1.0
        lo, hi = 0, L
        while hi - lo > 1:
            mid = (lo + hi) // 2
            lo, hi = (lo, mid) if reach_gain(mid) > self.cs else (mid, hi)
        f = self._f()
        a, b = (self.k / f + 1.0, (self.n - self.k) / f + 1.0)
        if self.deployed == 1:
            a, b = b, a
        return float(_bb.sf(hi - 1, L, a, b))

    def virtual_remaining(self, remaining_budget):
        if remaining_budget <= 0:
            return remaining_budget
        return max(remaining_budget - self.kappa * (self.skipped - self.undo), 1.0)

    def keep(self, event, remaining_budget):
        if self.stop_h is not None and event.t + self.delay > self.T - self.stop_h:
            self.undo += 1
            return False
        if self.thin < 1.0 and not bool(self.rng.random() < self.thin):
            return False
        if self.rho0 <= 0.0:
            return True
        return super().keep(event, remaining_budget)


class Stage2Wald(Stage1WaldStop):
    """Wald reference family with a hard stop and optional uniform thinning (pacer-debited)."""

    def __init__(self, *a, thin=1.0, kappa=1.0, **kw):
        super().__init__(*a, **kw)
        self.thin, self.kappa = float(thin), float(kappa)
        self.undo = 0

    def virtual_remaining(self, remaining_budget):
        if remaining_budget <= 0 or self.thin >= 1.0:
            return remaining_budget
        return max(remaining_budget - self.kappa * (self.skipped - self.undo), 1.0)

    def keep(self, event, remaining_budget):
        if event.t + self.delay > self.T - self.stop_h:
            self.undo += 1
            return False
        return self.thin >= 1.0 or bool(self.rng.random() < self.thin)


# ----------------------------------------------------------------------------------------------
# registry
# ----------------------------------------------------------------------------------------------
WALD_LAMS = (0.95, 0.97, 0.98, 0.99)
WALD_GAMS = (0.1, 0.2, 0.3)
H_GRID = (0, 500, 900, 1100, 1300, 1500, 1750)
THIN_K = (0.5, 0.25)
DYN: dict = {}  # name -> factory, filled at run time for Bayesian-optimisation configurations


def wald_name(lam, g, h, thin=1.0):
    base = f"s2wald_l{lam}_g{g}_H{h}"
    return base if thin >= 1.0 else f"{base}_k{thin}"


def armr_name(h, thin=1.0):
    return f"s2armr_H{h}" if thin >= 1.0 else f"s2armr_H{h}_k{thin}"


def factory(cls, name, **kw):
    def f(T, B, cs, cq, alpha, delay, r):
        return cls(T, B, cs, rng=r("EQSD"), delay=delay, name=name, cq=cq, **kw)

    return f


def stage2_factory(cfg: dict, name: str):
    return factory(Stage2Policy, name, **cfg)


def registry_entries() -> dict:
    reg = {}
    for lam in WALD_LAMS:
        for g in WALD_GAMS:
            for h in H_GRID:
                n = wald_name(lam, g, h)
                reg[n] = factory(Stage2Wald, n, lam=lam, gamma=g, stop_h=h)
                for k in THIN_K:
                    n = wald_name(lam, g, h, k)
                    reg[n] = factory(Stage2Wald, n, lam=lam, gamma=g, stop_h=h, thin=k)
    for h in H_GRID:
        reg[armr_name(h)] = factory(Stage1C1Stop, armr_name(h), stop_h=h)
        for k in THIN_K:  # arm R (gate off, no module G) + stop + uniform thinning
            n = armr_name(h, k)
            reg[n] = factory(Stage2Policy, n, rho0=0.0, bw=0.0, stop_h=h, thin=k)
    reg["s2full_default"] = factory(Stage2Policy, "s2full_default")
    reg.update(DYN)
    return reg
