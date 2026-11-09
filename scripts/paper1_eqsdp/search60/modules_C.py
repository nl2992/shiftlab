# ruff: noqa: RUF012
"""Family C (C21-C30): evidence / belief overlays built from released labels only.

How the parent consumes evidence. The parent (``EQSD``/``Stage1Base``) keeps discounted counts
``n, k`` (informative released labels, ``d = l0 - l1 != 0``), and flips the deployed model inside
its own ``observe`` when ``_gain_away(gamma) > c_s`` where the gain is ``adv(Q_gamma(p)) * rate *
(T - t)`` and ``Q`` is the Beta(k+1, n-k+1) quantile. The compositor offers no hook that replaces
that count update, so every C module is implemented as an **overlay on the same decision rule**:

* it maintains its own belief about the challenger win rate ``p`` from ``on_release`` only;
* with that belief it evaluates the parent's rule for both deployments,
  ``net_d = adv_d(Q_d) * rate * (T - t) - c_s``, at the parent's ``gamma`` (same T, c_s, rate);
* ``on_switch_proposal`` vetoes a parent flip that its own belief does not support;
* ``override_deploy`` promotes or reverses once, at the first prediction after a release, when
  its own belief passes the rule and the parent did not.

When the module's belief equals the parent's (for example C21 with ``mix = 0``) it is inert by
construction. The parent is never silently replaced: every veto / override is a compositor log
record (``reason`` carries the module id and the belief's net gain) and is also kept in
``self.audit``. The Beta-quantile rule is used even when the wrapped parent is the Wald one
(documented approximation); the prior-ensemble module C29 uses the parent's own counts. Only one of
C21, C24, C25, C26, C29, C30 may run (compositor-enforced).
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
from compositor import Module, register
from scipy.stats import beta as _beta

GRID = np.linspace(0.0, 1.0, 401)


def beta_q(u, k, n, a=1.0, b=1.0):
    return float(_beta.ppf(u, k + a, max(n - k, 0.0) + b))


def mix_q(u, ws, ks, ns):
    """Quantile of sum_i w_i Beta(k_i+1, n_i-k_i+1) on a 401-point grid (linear interpolation)."""
    ks, ns = np.asarray(ks, float), np.asarray(ns, float)
    comp_cdf = _beta.cdf(GRID[None, :], (ks + 1)[:, None], (ns - ks + 1)[:, None])
    cdf = (np.asarray(ws)[:, None] * comp_cdf).sum(0)
    return float(np.interp(u, cdf, GRID))


class Overlay(Module):
    """Decision-rule overlay: subclasses define ``update`` and ``quant`` (or override ``nets``)."""

    CAN_VETO = True
    CAN_OVERRIDE = True

    def __init__(self, *a):
        super().__init__(*a)
        self.net = (-1.0, -1.0)
        self.fresh = False
        self.audit: list[dict] = []
        self.n_veto = self.n_override = 0

    # ---- to implement -------------------------------------------------------------------
    def update(self, ctx, fb):
        pass

    def quant(self, u):
        raise NotImplementedError

    def rate(self, ctx):
        return ctx.rate

    def hurdle(self, ctx, t, dep):
        return ctx.parent.cs

    def horizon(self, ctx, t):
        return ctx.T - t

    def gamma(self, ctx, t, dep):
        return ctx.parent.gamma

    def nets(self, ctx, t):
        """(net0, net1): payback of switching away from deployment d minus the hurdle."""
        r, H = self.rate(ctx), self.horizon(ctx, t)
        out = []
        for dep in (0, 1):
            lev = self.gamma(ctx, t, dep)
            p = self.quant(lev if dep == 0 else 1.0 - lev)
            adv = (2 * p - 1) if dep == 0 else (1 - 2 * p)
            out.append(adv * r * H - self.hurdle(ctx, t, dep))
        return tuple(out)

    # ---- hooks --------------------------------------------------------------------------
    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        self.update(ctx, fb)
        self.net = self.nets(ctx, fb.t_released)
        self.fresh = True

    def on_switch_proposal(self, ctx, prop):
        if self.CAN_VETO and self.net[prop.frm] <= 0.0:
            self.n_veto += 1
            self.audit.append({"t": prop.t, "kind": "veto", "net": self.net[prop.frm]})
            prop.veto(f"{self.ID}:belief_net={self.net[prop.frm]:.2f}<=0")

    def override_deploy(self, ctx):
        if not self.fresh:
            return None
        self.fresh = False
        if self.CAN_OVERRIDE and self.net[ctx.deployed] > 0.0:
            self.n_override += 1
            self.audit.append({"t": ctx.t, "kind": "override", "net": self.net[ctx.deployed]})
            return 1 - ctx.deployed
        return None


class _CountOverlay(Overlay):
    """Overlay with own discounted counts (``lam`` defaults to the parent's)."""

    def __init__(self, *a):
        super().__init__(*a)
        self.n = self.k = 0.0

    def quant(self, u):
        return beta_q(u, self.k, self.n)

    def lam(self):
        return self.ctx.parent.lam

    def bump(self, x, lam=None):
        lam = self.lam() if lam is None else lam
        self.n, self.k = lam * self.n + 1.0, lam * self.k + x


@register
class C21(_CountOverlay):
    """Fast/slow Beta blend: quantile = (1-mix) * slow (parent counts) + mix * fast (lambda_fast)."""

    ID, FAMILY = "C21", "C"
    DEFAULTS = {"lambda_fast": 0.9, "mix": 0.2}
    SETTINGS = [{"lambda_fast": 0.8, "mix": 0.2}, {"lambda_fast": 0.9, "mix": 0.5}]

    def update(self, ctx, fb):
        self.bump(float(fb.d > 0), self.params["lambda_fast"])

    def quant(self, u):
        m = self.params["mix"]
        slow = beta_q(u, self.ctx.k, self.ctx.n)
        return (1 - m) * slow + m * beta_q(u, self.k, self.n)


@register
class C22(_CountOverlay):
    """Surprise-triggered discount: if the last three released outcomes had joint predictive
    probability < ``surprise``, the discount drops to ``lambda_alert`` for ``hold`` labels."""

    ID, FAMILY = "C22", "C"
    DEFAULTS = {"surprise": 0.05, "lambda_alert": 0.9, "hold": 10, "run": 3}
    SETTINGS = [{"surprise": 0.01, "lambda_alert": 0.8}, {"surprise": 0.05, "lambda_alert": 0.9}]

    def __init__(self, *a):
        super().__init__(*a)
        self.recent: deque = deque(maxlen=int(self.params["run"]))
        self.alert = 0
        self.n_alert = 0

    def update(self, ctx, fb):
        x = float(fb.d > 0)
        m = (self.k + 1.0) / (self.n + 2.0)
        self.recent.append(m if x else 1.0 - m)
        lam = self.params["lambda_alert"] if self.alert > 0 else self.lam()
        self.alert = max(self.alert - 1, 0)
        self.bump(x, lam)
        full = len(self.recent) == self.recent.maxlen
        if full and math.prod(self.recent) < self.params["surprise"]:
            self.alert, self.n_alert = int(self.params["hold"]), self.n_alert + 1
            self.recent.clear()


@register
class C23(_CountOverlay):
    """Soft posterior reset: a two-sided CUSUM of standardised released outcomes against the current
    posterior mean raises an alarm at ``threshold``; counts are then shrunk by ``shrink``."""

    ID, FAMILY = "C23", "C"
    DEFAULTS = {"shrink": 0.5, "threshold": 3.0, "drift": 0.5}
    SETTINGS = [{"shrink": 0.25, "threshold": 3.0}, {"shrink": 0.5, "threshold": 5.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self.sp = self.sm = 0.0
        self.n_alarm = 0

    def update(self, ctx, fb):
        x = float(fb.d > 0)
        m = min(max((self.k + 1.0) / (self.n + 2.0), 0.02), 0.98)
        z = (x - m) / math.sqrt(m * (1 - m))
        dr = self.params["drift"]
        self.sp, self.sm = max(0.0, self.sp + z - dr), max(0.0, self.sm - z - dr)
        self.bump(x)
        if max(self.sp, self.sm) >= self.params["threshold"]:
            keep = 1.0 - self.params["shrink"]
            self.n, self.k = keep * self.n, keep * self.k
            self.sp = self.sm = 0.0
            self.n_alarm += 1


@register
class C24(Overlay):
    """Hazard-mixture Beta filter: stable component (all released outcomes, undiscounted) versus a
    redrawn component (last ``recent`` outcomes), mixed by Bayes weights with per-label hazard."""

    ID, FAMILY = "C24", "C"
    DEFAULTS = {"hazard": 0.001, "prior_strength": 1.0, "recent": 10}
    SETTINGS = [{"hazard": 0.0001, "prior_strength": 1.0}, {"hazard": 0.001, "prior_strength": 3.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self.ks = self.ns = 0.0
        self.win: deque = deque(maxlen=int(self.params["recent"]))
        self.ws, self.wr = 0.5, 0.5

    def _parts(self):
        s = self.params["prior_strength"]
        kr, nr = sum(self.win), len(self.win)
        return (self.ks + s, self.ns - self.ks + s), (kr + s, nr - kr + s)

    def update(self, ctx, fb):
        x = int(fb.d > 0)
        h = self.params["hazard"]
        (as_, bs), (ar, br) = self._parts()
        ps = as_ / (as_ + bs) if x else bs / (as_ + bs)
        pr = ar / (ar + br) if x else br / (ar + br)
        ws, wr = self.ws * (1 - h) * ps, (self.wr + h * self.ws) * pr
        z = ws + wr
        self.ws, self.wr = ws / z, wr / z
        self.ks, self.ns = self.ks + x, self.ns + 1.0
        self.win.append(x)

    def quant(self, u):
        (as_, bs), (ar, br) = self._parts()
        cdf = self.ws * _beta.cdf(GRID, as_, bs) + self.wr * _beta.cdf(GRID, ar, br)
        return float(np.interp(u, cdf, GRID))


@register
class C25(Overlay):
    """Bayesian run-length posterior (Beta-Bernoulli BOCPD) over released outcomes; the last slot
    absorbs runs longer than ``truncate``. Belief = mixture of per-run Betas."""

    ID, FAMILY = "C25", "C"
    DEFAULTS = {"hazard": 0.002, "truncate": 100}
    SETTINGS = [{"hazard": 0.0005, "truncate": 50}, {"hazard": 0.002, "truncate": 200}]

    def __init__(self, *a):
        super().__init__(*a)
        self.w, self.ks, self.ns = np.array([1.0]), np.array([0.0]), np.array([0.0])

    def update(self, ctx, fb):
        x = float(fb.d > 0)
        h = self.params["hazard"]
        pred = (self.ks + 1.0) / (self.ns + 2.0)
        pred = pred if x else 1.0 - pred
        grow, cp = self.w * pred * (1 - h), float((self.w * pred).sum() * h)
        w = np.concatenate([[cp], grow])
        ks = np.concatenate([[0.0], self.ks + x])
        ns = np.concatenate([[0.0], self.ns + 1.0])
        m = int(self.params["truncate"])
        if len(w) > m + 1:  # absorb the longest runs into the last slot (keeps its own counts)
            w = np.concatenate([w[:m], [w[m:].sum()]])
            ks, ns = ks[: m + 1].copy(), ns[: m + 1].copy()
            ks[m], ns[m] = self.ks[-1] + x, self.ns[-1] + 1.0
        self.w, self.ks, self.ns = w / w.sum(), ks, ns

    def quant(self, u):
        return mix_q(u, self.w, self.ks, self.ns)


@register
class C26(Overlay):
    """Two-regime hidden-state belief: regimes 'challenger better' (win prob 1-smoothing) and
    'incumbent better' (win prob smoothing), persistent with ``self_transition``. The belief about
    p is the two-point distribution {1-s w.p. pi, s w.p. 1-pi}."""

    ID, FAMILY = "C26", "C"
    DEFAULTS = {"self_transition": 0.98, "smoothing": 0.3}
    SETTINGS = [
        {"self_transition": 0.98, "smoothing": 0.3},
        {"self_transition": 0.995, "smoothing": 0.1},
    ]

    def __init__(self, *a):
        super().__init__(*a)
        self.pi = 0.5

    def update(self, ctx, fb):
        r, s = self.params["self_transition"], self.params["smoothing"]
        pi = self.pi * r + (1 - self.pi) * (1 - r)
        x = fb.d > 0
        a, b = pi * (1 - s if x else s), (1 - pi) * (s if x else 1 - s)
        self.pi = a / (a + b)

    def quant(self, u):
        s = self.params["smoothing"]
        return s if u < 1.0 - self.pi else 1.0 - s


@register
class C27(Overlay):
    """Dependence-adjusted effective sample size: the parent's counts are scaled by
    ``1 - min(cap, strength * max(0, rho))`` with rho the lag-1 autocorrelation of the last 30
    released outcomes (release order)."""

    ID, FAMILY = "C27", "C"
    DEFAULTS = {"strength": 1.0, "cap": 0.9, "window": 30}
    SETTINGS = [{"strength": 0.5, "cap": 0.9}, {"strength": 1.0, "cap": 0.9}]

    def __init__(self, *a):
        super().__init__(*a)
        self.xs: deque = deque(maxlen=int(self.params["window"]))
        self.f = 1.0

    def update(self, ctx, fb):
        self.xs.append(float(fb.d > 0))
        x = np.asarray(self.xs)
        rho = 0.0
        if len(x) >= 8 and x[:-1].std() > 0 and x[1:].std() > 0:
            rho = float(np.corrcoef(x[:-1], x[1:])[0, 1])
        self.f = 1.0 - min(self.params["cap"], self.params["strength"] * max(rho, 0.0))

    def quant(self, u):
        return beta_q(u, self.f * self.ctx.k, self.f * self.ctx.n)


@register
class C28(Overlay):
    """Request-time discount: a label's weight is max(min_weight, exp(-(t_release - t_request)
    / age_tau)) recomputed at every release, replacing release-order discounting."""

    ID, FAMILY = "C28", "C"
    DEFAULTS = {"age_tau": 300.0, "min_weight": 0.5}
    SETTINGS = [{"age_tau": 100.0, "min_weight": 0.2}, {"age_tau": 300.0, "min_weight": 0.5}]

    def __init__(self, *a):
        super().__init__(*a)
        self.items: list = []
        self.n = self.k = 0.0

    def update(self, ctx, fb):
        self.items.append((fb.t_requested, float(fb.d > 0)))
        tr = np.array([i[0] for i in self.items], float)
        x = np.array([i[1] for i in self.items])
        age = (fb.t_released - tr) / self.params["age_tau"]
        w = np.maximum(self.params["min_weight"], np.exp(-age))
        self.n, self.k = float(w.sum()), float((w * x).sum())

    def quant(self, u):
        return beta_q(u, self.k, self.n)


@register
class C29(Overlay):
    """Robust Beta prior ensemble on the parent's counts: net gains under priors Beta(a,a) for
    a in {1, 2, 5}; ``mode`` mean (setting 0) or the conservative envelope min (setting 1)."""

    ID, FAMILY = "C29", "C"
    DEFAULTS = {"priors": ((1.0, 1.0), (2.0, 2.0), (5.0, 5.0)), "mode": "min"}
    SETTINGS = [{"mode": "mean"}, {"mode": "min"}]

    def nets(self, ctx, t):
        r, H, g, cs = self.rate(ctx), ctx.T - t, ctx.parent.gamma, ctx.parent.cs
        allnets = []
        for a, b in self.params["priors"]:
            row = []
            for dep in (0, 1):
                p = beta_q(g if dep == 0 else 1 - g, ctx.k, ctx.n, a, b)
                row.append(((2 * p - 1) if dep == 0 else (1 - 2 * p)) * r * H - cs)
            allnets.append(row)
        arr = np.asarray(allnets)
        agg = arr.min(0) if self.params["mode"] == "min" else arr.mean(0)
        return (float(agg[0]), float(agg[1]))


@register
class C30(Overlay):
    """Joint disagreement-and-win-rate belief: the disagreement rate is a discounted Beta filter
    over all events (``rate_lambda``); the win rate a Beta filter over released outcomes
    (``gain_lambda``). Payback = adv(Q_gamma(win)) * rate_hat * (T - t)."""

    ID, FAMILY = "C30", "C"
    DEFAULTS = {"rate_lambda": 0.99, "gain_lambda": 0.98}
    SETTINGS = [
        {"rate_lambda": 0.95, "gain_lambda": 0.9},
        {"rate_lambda": 0.99, "gain_lambda": 0.98},
    ]

    def __init__(self, *a):
        super().__init__(*a)
        self.rn = self.rk = 0.0
        self.n = self.k = 0.0

    def on_event(self, ctx):
        lr = self.params["rate_lambda"]
        self.rn, self.rk = lr * self.rn + 1.0, lr * self.rk + float(ctx.disagree)

    def update(self, ctx, fb):
        lg = self.params["gain_lambda"]
        self.n, self.k = lg * self.n + 1.0, lg * self.k + float(fb.d > 0)

    def rate(self, ctx):
        acq = ctx.parent.acq
        return (self.rk + acq.prior_rate * acq.prior_w) / (self.rn + acq.prior_w)

    def quant(self, u):
        return beta_q(u, self.k, self.n)
