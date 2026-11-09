# ruff: noqa: RUF012
"""Family E (E41-E50): posterior / risk / value-of-information modules.

Shared machinery (also used by family F):

* ``Post``: posterior over p = P(challenger correct | disagreement) built from *released labels only*
  (ties d = 0 skipped). It is a closed-form change-hazard mixture, moment-matched to one Beta:
  (S) stationary Beta over all labels, (W) "a change happened inside the recent ``mw`` labels"
  (BOCPD-style weights: hazard prior x beta-binomial marginal likelihood) and (R) a reset component,
  Beta(1,1), with weight 1-(1-h)^age, age = events since the last released label was *requested*.
  The R term is what a stationary posterior lacks: a belief with no fresh label is stale, its
  variance grows, and the value of a label recovers (doc 15 trace: stationary beliefs starve the
  labelling when the stream changes mid-episode).
* ``voi``: exact finite sum. Pending (requested, unreleased) labels are uncertain futures landing at
  t+delay: they are averaged out with their beta-binomial predictive before the value of ``nn``
  extra labels is computed. Value of a state = max(0, adv * rate * H - cs) (payback of a switch
  against the switch cost), so VOI >= 0 by convexity.
* ``Shadow``: a frozen-parent replica (same lam/gamma/cs rule) driven by the same released labels,
  with a deployment history; used by E45 and F58 (the compositor keeps a single deployed state and
  a vetoed or overridden parent decision is otherwise lost).
* ``_IPW``: capped inverse-propensity weights. The compositor does not hand ``p_final`` to modules
  (``rec`` has t, by, kind only; the log has p_final but only when logging is on and is not a
  module-visible object), so the propensity is *reconstructed*: the parent's paced propensity
  (same formula as ``PacedDisagreementAcquisition.propensity`` x mf, evaluated in ``scale`` after
  ``note_event``), and 1 for forced purchases. Other modules' scale multipliers are not included
  (documented gap). Event ids equal event times in the simulator.

Forced purchases (VOI family) respect the parent cutoff (never buy while ``ctx.closed``) and a
pacing guard ``pace_ok`` (spend <= 25% + 70% * t / t_end of B) so a module cannot drain B early.
"""

from __future__ import annotations

import math
from bisect import bisect_right
from collections import deque
from functools import lru_cache

from compositor import Force, Module, Proposal, register
from scipy.stats import beta as _beta

LB = math.lgamma


def lbeta(a, b):
    return LB(a) + LB(b) - LB(a + b)


def phi(z):
    return math.exp(-0.5 * z * z) / math.sqrt(2 * math.pi)


def Phi(z):
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def pace_ok(ctx, base=0.25, slope=0.7):
    t_end = ctx.t_close if ctx.t_close else ctx.T - ctx.delay
    used = (ctx.B - ctx.remaining) / ctx.B
    return used <= base + slope * min(1.0, ctx.t / max(1, t_end))


def price(ctx):
    """Label price with a budget shadow multiplier when spending is ahead of plan."""
    t_end = ctx.t_close if ctx.t_close else ctx.T - ctx.delay
    ahead = (ctx.B - ctx.remaining) / ctx.B - min(1.0, ctx.t / max(1, t_end))
    return ctx.parent.cq * (1.0 + 20.0 * max(0.0, ahead))


def adv(mu, dep):
    return (2 * mu - 1) if dep == 0 else (1 - 2 * mu)


@lru_cache(maxsize=8192)
def _ppf(q, a, b):
    return float(_beta.ppf(q, a, b))


def gain_q(a, b, dep, lev, rate, H):
    """Payback at quantile ``lev`` of p (parent convention) for Beta(a,b)."""
    q = _ppf(lev if dep == 0 else 1.0 - lev, a, b)
    return adv(q, dep) * rate * H


def surv(H, h):
    """Mean survival of the current regime over a horizon H under hazard h."""
    return 1.0 if h <= 0 or H <= 0 else (1.0 - (1.0 - h) ** H) / (h * H)


class Post:
    def __init__(self, hazard, mw=8):
        self.h, self.mw = float(hazard), mw
        self.w, self.cw, self.treq = [], [0], []

    def add(self, fb):
        if fb.d == 0:
            return
        self.w.append(int(fb.d > 0))
        self.cw.append(self.cw[-1] + self.w[-1])
        self.treq.append(fb.t_requested)

    def eff(self, t):
        """Moment-matched (a, b) of the hazard-mixture posterior at time t."""
        n, h = len(self.w), self.h
        k = self.cw[-1]
        if n == 0:
            return 1.0, 1.0
        comps = [(1.0, k + 1.0, n - k + 1.0)]
        m = min(self.mw, n)
        if n > m and h > 0:
            kn = self.cw[n] - self.cw[n - m]
            ko = k - kn
            span = max(1, self.treq[-1] - self.treq[n - m])
            pi = 1.0 - (1.0 - h) ** span
            ls = math.log(1.0 - pi) + lbeta(k + 1, n - k + 1)
            lw = math.log(pi) + lbeta(ko + 1, n - m - ko + 1) + lbeta(kn + 1, m - kn + 1)
            mx = max(ls, lw)
            ws, ww = math.exp(ls - mx), math.exp(lw - mx)
            z = ws + ww
            comps = [(ws / z, k + 1.0, n - k + 1.0), (ww / z, kn + 1.0, m - kn + 1.0)]
        pf = 1.0 - (1.0 - h) ** max(0, t - self.treq[-1]) if h > 0 else 0.0
        comps = [(w * (1 - pf), a, b) for w, a, b in comps] + [(pf, 1.0, 1.0)]
        mu = sum(w * a / (a + b) for w, a, b in comps)
        e2 = sum(
            w * (a * b / ((a + b) ** 2 * (a + b + 1)) + (a / (a + b)) ** 2) for w, a, b in comps
        )
        var = max(e2 - mu * mu, 1e-9)
        ess = max(mu * (1 - mu) / var - 1.0, 2.0)
        return mu * ess, (1 - mu) * ess


def _bb_all(n, a, b):
    """Beta-binomial pmf over 0..n by the ratio recurrence."""
    p = math.exp(LB(b + n) - LB(b) - LB(a + b + n) + LB(a + b))
    out = [p]
    for x in range(n):
        p *= (n - x) / (x + 1) * (a + x) / (b + n - x - 1)
        out.append(p)
    return out


def voi(a, b, m, nn, dep, rate, H, cs):
    """Value of ``nn`` extra labels given ``m`` pending ones, horizon H, switch cost cs."""
    if H <= 0 or rate <= 0:
        return 0.0
    m = min(int(m), 10)
    tot = a + b + m + nn
    # exact early exit: if every outcome lands on the same side of the switch threshold the value
    # function is linear there and the expected value is unchanged (VOI = 0)
    lo = adv(a / tot, dep) if dep == 0 else adv((a + m + nn) / tot, dep)
    hi = adv((a + m + nn) / tot, dep) if dep == 0 else adv(a / tot, dep)
    if lo * rate * H >= cs or hi * rate * H <= cs:
        return 0.0
    out = 0.0
    for j, wj in enumerate(_bb_all(m, a, b)):
        if wj < 1e-9:
            continue
        a1, b1 = a + j, b + m - j
        v0 = max(0.0, adv(a1 / (a1 + b1), dep) * rate * H - cs)
        v1 = 0.0
        for x, px in enumerate(_bb_all(nn, a1, b1)):
            v1 += px * max(0.0, adv((a1 + x) / (a1 + b1 + nn), dep) * rate * H - cs)
        out += wj * (v1 - v0)
    return max(0.0, out)


class Shadow:
    """Replica of the frozen parent's evidence and switching rule (k, n, deployed) on released labels."""

    def __init__(self, parent):
        self.p = parent
        self.k = self.n = 0.0
        self.dep = 0
        self.ts, self.deps = [-1], [0]

    def update(self, fb):
        if fb.d == 0:
            return
        p = self.p
        self.n = p.lam * self.n + 1.0
        self.k = p.lam * self.k + float(fb.d > 0)
        g = gain_q(
            self.k + 1, self.n - self.k + 1, self.dep, p.gamma, p._rate(), p.T - fb.t_released
        )
        if g > p.cs:
            self.dep = 1 - self.dep
            self.ts.append(fb.t_released)
            self.deps.append(self.dep)

    def dep_at(self, t):
        return self.deps[bisect_right(self.ts, t) - 1]

    def n_switch(self, t0, t1):
        return sum(1 for s in self.ts[1:] if t0 <= s <= t1)


class _DepHist:
    """Mixin: composed deployment history for ``dep_at(t_requested)``."""

    def _hist_init(self):
        self.h_t, self.h_d = [-1], [0]

    def on_deploy_change(self, ctx, frm, to):
        self.h_t.append(ctx.t)
        self.h_d.append(int(to))

    def dep_at(self, t):
        return self.h_d[bisect_right(self.h_t, t) - 1]


class _IPW:
    """Mixin: reconstructed positive propensities and capped inverse weights (see module docstring)."""

    def _ipw_init(self, cap):
        self.cap, self.q_at, self.w_at = float(cap), {}, {}

    def _ipw_scale(self, ctx):
        a, par = ctx.parent.acq, ctx.parent
        rate = (a.n_disagree - 1 + a.prior_rate * a.prior_w) / (ctx.t + a.prior_w)
        left = max(rate * (ctx.T - ctx.t), 1e-9)
        q = max(ctx.remaining / left, a.p_min)
        self.q_at[ctx.t] = min(1.0, min(1.0, q) * par.mf)

    def _ipw_purchase(self, ctx, rec):
        q = 1.0 if rec["kind"] == "force" else self.q_at.get(ctx.t, 1.0)
        self.w_at[ctx.t] = min(self.cap, 1.0 / max(q, 1e-6))
        self.q_at.pop(ctx.t, None)

    def _ipw_w(self, event_id):
        return self.w_at.pop(event_id, 1.0)


class _E(Module):
    FAMILY = "E"


class _VOI(_E):
    """Base for the VOI modules: owns a ``Post`` and an ``h`` hazard."""

    def __init__(self, *a):
        super().__init__(*a)
        self.post = Post(self.params["hazard"])

    def on_release(self, ctx, fb):
        self.post.add(fb)

    def _v(self, ctx, nn, H):
        a, b = self.post.eff(ctx.t)
        Hx = max(0.0, H) * surv(H, self.params["hazard"])
        return voi(a, b, ctx.pending, nn, ctx.deployed, ctx.rate, Hx, ctx.parent.cs)

    @staticmethod
    def _open(ctx):
        return (not ctx.closed) and ctx.releasable and pace_ok(ctx)


@register
class E41(_VOI):
    """Missed-switch expected-loss proxy. Buy (force) when the value of one more label, over a
    ``rollout_h``-event rollout discounted by the hazard of a regime change, exceeds the (budget-
    shadowed) label price. Posterior = hazard mixture of released labels; pending labels are
    integrated out."""

    ID = "E41"
    DEFAULTS = {"rollout_h": 300, "hazard": 0.002}
    SETTINGS = [{"rollout_h": 100, "hazard": 0.0005}, {"rollout_h": 300, "hazard": 0.002}]

    def floor(self, ctx):
        if not self._open(ctx):
            return None
        H = min(ctx.T - ctx.t - ctx.delay, self.params["rollout_h"])
        return Force("force", 1.0, self.ID) if self._v(ctx, 1, H) > price(ctx) else None


@register
class E42(_VOI):
    """Paired-cost tail-aware acquisition. The upper-``alpha`` tail of the excess cost of staying with
    the incumbent (payback at the alpha quantile of the hazard-mixture posterior, to the end of the
    horizon) is weighted by ``risk_weight``; buy when risk_weight * (tail - cs) > cs, at most the
    parent's p_cap (10) labels in flight."""

    ID = "E42"
    DEFAULTS = {"alpha": 0.9, "risk_weight": 2.0, "hazard": 0.002}
    SETTINGS = [{"alpha": 0.9, "risk_weight": 2.0}, {"alpha": 0.95, "risk_weight": 0.5}]

    def floor(self, ctx):
        if not self._open(ctx) or ctx.pending >= 10:
            return None
        a, b = self.post.eff(ctx.t)
        H = ctx.T - ctx.t - ctx.delay
        tail = gain_q(a, b, ctx.deployed, self.params["alpha"], ctx.rate, H)
        cs = ctx.parent.cs
        if self.params["risk_weight"] * max(0.0, tail - cs) > cs:
            return Force("force", 1.0, self.ID)
        return None


def _wrong_loss(mu, var, to, rate, H):
    """E[max(0, -adv_to)] * rate * H under a normal approximation of the posterior of p."""
    m = adv(mu, 1 - to)  # advantage of `to` (to=1: 2mu-1)
    s = 2.0 * math.sqrt(max(var, 1e-12))
    z = m / s
    return (-m * Phi(-z) + s * phi(z)) * rate * H


@register
class E43(_E):
    """Posterior risk budget per deployment. Each approved switch spends its expected downside
    (posterior E[max(0,-adv)] x rate x (2*delay+50) events, i.e. until corrective evidence can
    arrive); spend decays with half-life 300 events. A proposal is vetoed when decayed spend plus
    its own downside exceeds ``risk_budget`` (loss units). Not a guarantee."""

    ID = "E43"
    DEFAULTS = {"risk_budget": 10.0}
    SETTINGS = [{"risk_budget": 5.0}, {"risk_budget": 20.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self.spent, self.t_spent = 0.0, 0

    def on_switch_proposal(self, ctx, prop: Proposal):
        k, n = ctx.k + 1.0, ctx.n + 2.0
        mu = k / n
        var = mu * (1 - mu) / (n + 1.0)
        down = _wrong_loss(mu, var, prop.to, ctx.rate, 2 * ctx.delay + 50)
        sp = self.spent * 0.5 ** ((prop.t - self.t_spent) / 300.0)
        if sp + down > self.params["risk_budget"]:
            prop.veto(f"E43:risk {sp + down:.1f}>{self.params['risk_budget']}")
        else:
            self.spent, self.t_spent = sp + down, prop.t


@register
class E44(_E):
    """Prior-robust payback envelope. A proposed switch must pay back (> cs, horizon T-t) under every
    prior of the set: weak = {Beta(1,1), Beta(.5,.5), incumbent-skeptic Beta(1,3)/(3,1)}, balanced =
    {Beta(2,2), Beta(5,5), skeptic Beta(2,4)/(4,2)}, on the parent's decayed counts. ``quantile`` uses
    the parent's gamma-quantile of each posterior, ``mean`` the posterior mean."""

    ID = "E44"
    DEFAULTS = {"priors": "balanced", "envelope": "quantile"}
    SETTINGS = [{"priors": "weak", "envelope": "quantile"},
                {"priors": "balanced", "envelope": "mean"}]  # fmt: skip

    def on_switch_proposal(self, ctx, prop: Proposal):
        sk = (1.0, 3.0) if prop.frm == 0 else (3.0, 1.0)
        pri = ([(1.0, 1.0), (0.5, 0.5), sk] if self.params["priors"] == "weak"
               else [(2.0, 2.0), (5.0, 5.0), (sk[0] + 1, sk[1] + 1)])  # fmt: skip
        H, rate, g = ctx.T - prop.t, ctx.rate, ctx.parent.gamma
        gs = []
        for a0, b0 in pri:
            a, b = ctx.k + a0, ctx.n - ctx.k + b0
            if self.params["envelope"] == "mean":
                gs.append(adv(a / (a + b), prop.frm) * rate * H)
            else:
                gs.append(gain_q(a, b, prop.frm, g, rate, H))
        if min(gs) <= ctx.parent.cs:
            prop.veto(f"E44:envelope {min(gs):.1f}<=cs")


@register
class E45(_E):
    """Ambiguity-triggered parent fallback. A shadow replica of the frozen parent (same lam, gamma,
    cs) is driven by the same released labels. If the composed deployment differs from the shadow's
    and the posterior probability (parent evidence) that the composed choice is the better model is
    below 1-``ambiguity``, ``override_deploy`` returns the shadow's (parent's) action, and keeps
    doing so for ``cooldown`` events. HOOK GAP: the compositor does not pass other modules'
    proposals; this is implemented through the shadow state. Alone it is inert by construction."""

    ID = "E45"
    DEFAULTS = {"ambiguity": 0.1, "cooldown": 50}
    SETTINGS = [{"ambiguity": 0.05, "cooldown": 50}, {"ambiguity": 0.1, "cooldown": 100}]

    def __init__(self, *a):
        super().__init__(*a)
        self.sh = Shadow(self.ctx.parent)
        self.until = -1
        self.n_fallback = 0

    def on_release(self, ctx, fb):
        self.sh.update(fb)

    def override_deploy(self, ctx):
        cur = ctx.deployed
        if cur == self.sh.dep:
            return None
        if ctx.t < self.until:
            return self.sh.dep
        c = float(_beta.cdf(0.5, ctx.k + 1.0, ctx.n - ctx.k + 1.0))  # P(p < .5)
        conf = (1.0 - c) if cur == 1 else c
        if 1.0 - conf > self.params["ambiguity"]:
            self.until = ctx.t + self.params["cooldown"]
            self.n_fallback += 1
            return self.sh.dep
        return None


@register
class E46(_IPW, _E):
    """Positive-propensity feedback correction. Self-normalised, capped (``weight_cap``) inverse-
    propensity estimate of p from released labels (decayed with the parent's lam); the switch
    proposal is re-checked with counts n*p_mix, p_mix = shrink*p_plain + (1-shrink)*p_ipw, and vetoed
    when the corrected evidence no longer pays back (> cs at the parent's gamma quantile). Valid only
    if the (reconstructed) propensity is positive and depends on observables (it does)."""

    ID = "E46"
    DEFAULTS = {"weight_cap": 10.0, "shrink": 0.5}
    SETTINGS = [{"weight_cap": 5.0, "shrink": 0.25}, {"weight_cap": 10.0, "shrink": 0.5}]

    def __init__(self, *a):
        super().__init__(*a)
        self._ipw_init(self.params["weight_cap"])
        self.sw = self.sk = 0.0

    def scale(self, ctx):
        self._ipw_scale(ctx)

    def on_purchase(self, ctx, rec):
        self._ipw_purchase(ctx, rec)

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        w, lam = self._ipw_w(fb.event_id), ctx.parent.lam
        self.sw = lam * self.sw + w
        self.sk = lam * self.sk + w * float(fb.d > 0)

    def on_switch_proposal(self, ctx, prop: Proposal):
        if self.sw <= 0 or ctx.n <= 0:
            return
        s = self.params["shrink"]
        pm = s * (ctx.k / ctx.n) + (1 - s) * (self.sk / self.sw)
        k = ctx.n * pm
        g = gain_q(k + 1.0, ctx.n - k + 1.0, prop.frm, ctx.parent.gamma, ctx.rate, ctx.T - prop.t)
        if g <= ctx.parent.cs:
            prop.veto(f"E46:ipw g={g:.1f}")


@register
class E47(_DepHist, _E):
    """Released-loss CUSUM. x = +1 if the released label favours the model deployed when it was
    requested, else -1; S <- max(0, S - x - 0.1) at release time (so the explicit delay is in the
    statistic). Alarm at S > ``threshold`` (reset soft: S/2, hard: 0) opens a 100-event window in
    which up to 10 labels are forced (open cutoff only). Monitoring floor: a label is forced if
    none was bought in the last 80 events. Rollback is left to the parent's evidence."""

    ID = "E47"
    DEFAULTS = {"threshold": 3.0, "reset": "soft", "k": 0.1, "packet": 10, "floor_gap": 80}
    SETTINGS = [{"threshold": 3.0, "reset": "soft"}, {"threshold": 5.0, "reset": "hard"}]

    def __init__(self, *a):
        super().__init__(*a)
        self._hist_init()
        self.S, self.until, self.spent, self.n_alarm = 0.0, -1, 0, 0

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        good = (fb.d > 0) == (self.dep_at(fb.t_requested) == 1)
        self.S = max(0.0, self.S - (1.0 if good else -1.0) - self.params["k"])
        if self.S > self.params["threshold"]:
            self.n_alarm += 1
            self.S = self.S / 2 if self.params["reset"] == "soft" else 0.0
            self.until, self.spent = fb.t_released + 100, 0

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable or not pace_ok(ctx):
            return None
        if ctx.t < self.until and self.spent < self.params["packet"]:
            return Force("force", 1.0, self.ID + ":alarm")
        if ctx.t - max(ctx.last_buy_t, 0) >= self.params["floor_gap"]:
            return Force("force", 1.0, self.ID + ":floor")
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class E48(_VOI):
    """Next-information arrival value. A label bought now arrives at t+delay; its value is
    ``arrival_discount`` x VOI over the horizon left after arrival and ``lookahead`` events of
    execution (T - t - delay - lookahead). Parent/lifted purchases whose discounted VOI is below the
    label price are vetoed; switch proposals whose discounted mean payback over (T - t - lookahead)
    does not exceed cs are vetoed."""

    ID = "E48"
    DEFAULTS = {"arrival_discount": 1.0, "lookahead": 50, "hazard": 0.002}
    SETTINGS = [{"arrival_discount": 0.5, "lookahead": 50},
                {"arrival_discount": 1.0, "lookahead": 150}]  # fmt: skip

    def veto(self, ctx):
        H = ctx.T - ctx.t - ctx.delay - self.params["lookahead"]
        v = self.params["arrival_discount"] * self._v(ctx, 1, H)
        return f"voi {v:.3f}<price" if v < price(ctx) else None

    def on_switch_proposal(self, ctx, prop: Proposal):
        H = max(0, ctx.T - prop.t - self.params["lookahead"])
        mu = (ctx.k + 1.0) / (ctx.n + 2.0)
        g = self.params["arrival_discount"] * adv(mu, prop.frm) * ctx.rate * H
        if g <= ctx.parent.cs:
            prop.veto(f"E48:late g={g:.1f}")


@register
class E49(_E):
    """Posterior lock-in detector. Flag the state when the parent's posterior puts >= ``confidence``
    on the deployed model being the better one while at most 2 labels were bought in the last ``age``
    events; force a monitoring label (open cutoff, pace guard)."""

    ID = "E49"
    DEFAULTS = {"confidence": 0.95, "age": 80, "few": 2}
    SETTINGS = [{"confidence": 0.95, "age": 80}, {"confidence": 0.99, "age": 160}]

    def __init__(self, *a):
        super().__init__(*a)
        self.buys = deque()

    def on_purchase(self, ctx, rec):
        self.buys.append(ctx.t)

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable or not pace_ok(ctx) or ctx.n < 3:
            return None
        age = self.params["age"]
        while self.buys and self.buys[0] <= ctx.t - age:
            self.buys.popleft()
        if len(self.buys) > self.params["few"] or ctx.t < age:
            return None
        c = float(_beta.cdf(0.5, ctx.k + 1.0, ctx.n - ctx.k + 1.0))
        conf = (1.0 - c) if ctx.deployed == 1 else c
        return Force("force", 1.0, self.ID) if conf >= self.params["confidence"] else None


@register
class E50(_DepHist, _IPW, _E):
    """Observed-regret risk score. Over the last ``window`` released labels, bad = the label favoured
    the model *not* deployed at request time; propensity-weighted (capped IPW, reconstructed
    propensity) share with an effective-sample-size normal upper bound at ``upper_q``. If the upper
    bound exceeds 0.5 (deployed model plausibly worse) force labels (<= 4 in flight)."""

    ID = "E50"
    DEFAULTS = {"window": 30, "upper_q": 0.9, "weight_cap": 10.0}
    SETTINGS = [{"window": 10, "upper_q": 0.9}, {"window": 30, "upper_q": 0.95}]

    def __init__(self, *a):
        super().__init__(*a)
        self._hist_init()
        self._ipw_init(self.params["weight_cap"])
        self.win = deque(maxlen=int(self.params["window"]))

    def scale(self, ctx):
        self._ipw_scale(ctx)

    def on_purchase(self, ctx, rec):
        self._ipw_purchase(ctx, rec)

    def on_release(self, ctx, fb):
        w = self._ipw_w(fb.event_id)
        if fb.d == 0:
            return
        bad = int((fb.d > 0) != (self.dep_at(fb.t_requested) == 1))
        self.win.append((w, bad))

    def score(self):
        if len(self.win) < 5:
            return 0.0
        sw = sum(w for w, _ in self.win)
        pbar = sum(w * x for w, x in self.win) / sw
        ess = sw * sw / sum(w * w for w, _ in self.win)
        z = {0.9: 1.2816, 0.95: 1.6449}.get(self.params["upper_q"], 1.2816)
        return pbar + z * math.sqrt(max(pbar * (1 - pbar), 0.05) / ess)

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable or not pace_ok(ctx) or ctx.pending >= 4:
            return None
        return Force("force", 1.0, self.ID) if self.score() > 0.5 else None
