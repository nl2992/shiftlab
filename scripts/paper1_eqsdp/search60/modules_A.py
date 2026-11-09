# ruff: noqa: RUF012
"""Family A (A01-A10): post-cutoff monitoring and reopening.

All modules act only after the parent's cutoff has closed (``ctx.closed``) and only on events whose
label can still be released before T (``ctx.releasable``); every override is an explicit, logged
cutoff exception. They see predictions and released purchased feedback only.

Conventions shared by family A (interpretations where the catalogue is silent):

* ``reserve`` (default 20 where the catalogue gives none): the maximum number of labels the module
  may spend after the cutoff. It is also held back from the pre-cutoff budget through a ``Reserve``
  whose window starts at the cutoff (budget-cap rule of COMPOSITION_RULES.md).
* Sentinels (A01, A02, A03, A09, A10) are ``force`` purchases; alarm monitors (A04-A08) open a
  window of ``width`` events (A04: ``window``; default 100 elsewhere) during which the cutoff is
  lifted for the parent's own paced draw (kind ``lift``), i.e. the parent behaves as if its cutoff
  had not been set. Monitors are reset when the window ends.
* Monitor baselines are the prediction statistics of the pre-cutoff events, frozen at the cutoff
  (disagreement rate mu0, (1,0)-share, per-model flip rate). Monitors accumulate only after the
  cutoff closes. No label is needed.
"""

from __future__ import annotations

import math
from collections import deque

from compositor import Force, Module, Reserve, register


class _PostCutoff(Module):
    FAMILY = "A"
    DEFAULTS = {"reserve": 20}

    def __init__(self, params, ctx, rng):
        super().__init__(params, ctx, rng)
        self.spent = 0

    def eligible(self, ctx):
        return ctx.closed and ctx.releasable and self.spent < self.params["reserve"]

    def reserves(self, ctx):
        if ctx.t_close is None:
            return []
        return [Reserve(self.ID, int(self.params["reserve"]), lo=ctx.t_close)]

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


# ---------------------------------------------------------------------------------------------
# sentinels
# ---------------------------------------------------------------------------------------------
@register
class A01(_PostCutoff):
    """Periodic sentinel: after the cutoff, buy one disagreement label every ``m`` eligible events
    (eligible = closed, releasable, disagreement). Counter resets on the module's own purchase."""

    ID = "A01"
    DEFAULTS = {"m": 80, "reserve": 10}
    SETTINGS = [{"m": 80, "reserve": 10}, {"m": 40, "reserve": 20}]

    def __init__(self, *a):
        super().__init__(*a)
        self.cnt = 0

    def floor(self, ctx):
        if not self.eligible(ctx):
            return None
        self.cnt += 1
        if self.cnt >= self.params["m"]:
            return Force("force", 1.0, self.ID)
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.cnt = 0
        super().on_purchase(ctx, rec)


@register
class A02(_PostCutoff):
    """Geometric sentinel: interval starts at m0 and is multiplied by ``growth`` after each own
    purchase; a warning resets it to m0. Warning = a label released after the cutoff whose sign
    favours the model that is not deployed, or a deployment change."""

    ID = "A02"
    DEFAULTS = {"m0": 20, "growth": 1.5, "reserve": 20}
    SETTINGS = [{"m0": 20, "growth": 1.2}, {"m0": 40, "growth": 1.5}]

    def __init__(self, *a):
        super().__init__(*a)
        self.m, self.cnt = float(self.params["m0"]), 0

    def floor(self, ctx):
        if not self.eligible(ctx):
            return None
        self.cnt += 1
        if self.cnt >= round(self.m):
            return Force("force", 1.0, self.ID)
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.cnt, self.m = 0, self.m * self.params["growth"]
        super().on_purchase(ctx, rec)

    def on_release(self, ctx, fb):
        if ctx.closed and ((ctx.deployed == 0 and fb.d > 0) or (ctx.deployed == 1 and fb.d < 0)):
            self.m = float(self.params["m0"])

    def on_deploy_change(self, ctx, frm, to):
        self.m = float(self.params["m0"])


@register
class A03(_PostCutoff):
    """Hazard-responsive sentinel: on each eligible event buy with probability
    max(floor, 1 - (1 - hazard)^age), age = events since the last released or requested label
    (posterior probability that the world changed since the last information). Own random stream."""

    ID = "A03"
    DEFAULTS = {"hazard": 0.002, "floor": 0.03, "reserve": 20}
    SETTINGS = [{"hazard": 0.0005, "floor": 0.01}, {"hazard": 0.002, "floor": 0.03}]

    def floor(self, ctx):
        if not self.eligible(ctx):
            return None
        age = ctx.t - max(ctx.last_release_t, ctx.last_buy_t, 0)
        p = max(self.params["floor"], 1.0 - (1.0 - self.params["hazard"]) ** age)
        if self.rng.random() < p:
            return Force("force", float(p), self.ID)
        return None


@register
class A09(_PostCutoff):
    """Feedback-staleness sentinel: force a disagreement query if no label has been released for
    ``max_age`` events and none has been requested for ``max_age`` events (a request in flight is
    information already on its way)."""

    ID = "A09"
    DEFAULTS = {"max_age": 120, "reserve": 20}
    SETTINGS = [{"max_age": 240}, {"max_age": 60}]

    def floor(self, ctx):
        if not self.eligible(ctx):
            return None
        last = max(ctx.last_release_t, ctx.last_buy_t, 0)
        if ctx.t - last >= self.params["max_age"]:
            return Force("force", 1.0, self.ID)
        return None


@register
class A10(_PostCutoff):
    """One-shot reopening window: at the predeclared ``checkpoint`` the cutoff is lifted for
    ``width`` events (the parent's own paced draw), under the module's reserve."""

    ID = "A10"
    DEFAULTS = {"checkpoint": 1000, "width": 100, "reserve": 20}
    SETTINGS = [{"checkpoint": 1000, "width": 100}, {"checkpoint": 1300, "width": 200}]

    def floor(self, ctx):
        c, w = self.params["checkpoint"], self.params["width"]
        if c <= ctx.t < c + w and self.eligible(ctx):
            return Force("lift", reason=self.ID)
        return None


# ---------------------------------------------------------------------------------------------
# alarm monitors (prediction-only) that reopen a bounded query window
# ---------------------------------------------------------------------------------------------
class _Alarm(_PostCutoff):
    WIDTH_KEY = "width"

    def __init__(self, *a):
        super().__init__(*a)
        self.win_end, self.n_alarms = -1, 0
        self.n0 = self.s0 = 0.0  # pre-cutoff disagreement count
        self.frozen = False
        self.mu0 = 0.25
        self._reset()

    def _reset(self):
        pass

    def _pre(self, ctx):
        """Accumulate pre-cutoff baseline statistics (override to add more)."""
        self.n0 += 1
        self.s0 += float(ctx.disagree)

    def _freeze(self, ctx):
        self.mu0 = min(0.98, max(0.02, self.s0 / self.n0)) if self.n0 else 0.25

    def _signal(self, ctx) -> bool:
        return False

    def _track(self, ctx):
        """Update running windows on every event (override when a monitor needs the full stream)."""

    def on_event(self, ctx):
        self._track(ctx)
        if not ctx.closed:
            self._pre(ctx)
            return
        if not self.frozen:
            self._freeze(ctx)
            self.frozen = True
        if ctx.t < self.win_end:
            return
        if self._signal(ctx):
            self.win_end = ctx.t + int(self.params[self.WIDTH_KEY])
            self.n_alarms += 1
            self._reset()

    def floor(self, ctx):
        if ctx.t < self.win_end and self.eligible(ctx):
            return Force("lift", reason=self.ID)
        return None


@register
class A04(_Alarm):
    """Disagreement CUSUM: two-sided CUSUM on the standardised disagreement indicator against the
    frozen pre-cutoff rate, allowance k=0.5; alarm above ``threshold`` reopens ``window`` events."""

    ID = "A04"
    WIDTH_KEY = "window"
    DEFAULTS = {"window": 100, "threshold": 4.0, "k": 0.5, "reserve": 20}
    SETTINGS = [{"window": 50, "threshold": 4.0}, {"window": 100, "threshold": 2.0}]

    def _reset(self):
        self.sp = self.sm = 0.0

    def _signal(self, ctx):
        sd = math.sqrt(self.mu0 * (1 - self.mu0))
        z = (float(ctx.disagree) - self.mu0) / sd
        self.sp = max(0.0, self.sp + z - self.params["k"])
        self.sm = max(0.0, self.sm - z - self.params["k"])
        return max(self.sp, self.sm) > self.params["threshold"]


@register
class A05(_Alarm):
    """Disagreement Page-Hinkley with forgetting ``decay``: m <- decay*m + (x - mu0 -/+ delta),
    PH = m - min(m); two-sided; alarm above ``threshold``. delta = 0.01 (fixed)."""

    ID = "A05"
    DEFAULTS = {"threshold": 5.0, "decay": 0.99, "delta": 0.01, "width": 100, "reserve": 20}
    SETTINGS = [{"threshold": 5.0, "decay": 0.99}, {"threshold": 3.0, "decay": 0.95}]

    def _reset(self):
        self.mu = self.md = self.Mu = self.Md = 0.0

    def _signal(self, ctx):
        a, d, x = self.params["decay"], self.params["delta"], float(ctx.disagree)
        self.mu = a * self.mu + (x - self.mu0 - d)
        self.md = a * self.md + (self.mu0 - x - d)
        self.Mu, self.Md = min(self.Mu, self.mu), min(self.Md, self.md)
        return max(self.mu - self.Mu, self.md - self.Md) > self.params["threshold"]


@register
class A06(_Alarm):
    """Prediction-pair transition alarm: share of (1,0) among (0,1)/(1,0) disagreement patterns in
    the last ``window`` events against the frozen pre-cutoff share; |z| > ``z`` (>=10 patterns)."""

    ID = "A06"
    DEFAULTS = {"window": 100, "z": 3.0, "width": 100, "reserve": 20}
    SETTINGS = [{"window": 200, "z": 3.0}, {"window": 100, "z": 2.0}]

    def __init__(self, *a):
        self.buf = deque()
        self.c10 = self.c01 = 0
        self.p10 = self.p01 = 0
        super().__init__(*a)

    def _pat(self, ctx):
        a, b = ctx.preds[0], ctx.preds[1]
        return 0 if a == b else (1 if (a, b) == (0, 1) else 2)

    def _track(self, ctx):
        v = self._pat(ctx)
        self.buf.append(v)
        self.c01 += v == 1
        self.c10 += v == 2
        if len(self.buf) > self.params["window"]:
            o = self.buf.popleft()
            self.c01 -= o == 1
            self.c10 -= o == 2

    def _pre(self, ctx):
        super()._pre(ctx)
        v = self._pat(ctx)
        self.p01 += v == 1
        self.p10 += v == 2

    def _freeze(self, ctx):
        super()._freeze(ctx)
        m = self.p01 + self.p10
        self.s0b = min(0.95, max(0.05, self.p10 / m)) if m else 0.5

    def _signal(self, ctx):
        m = self.c01 + self.c10
        if m < 10:
            return False
        s = self.c10 / m
        z = (s - self.s0b) / math.sqrt(self.s0b * (1 - self.s0b) / m)
        return abs(z) > self.params["z"]


@register
class A07(_Alarm):
    """Disagreement burst alarm: fast EWMA (span ``fast``) exceeds slow EWMA (span ``slow``) by
    more than z=3 EWMA standard deviations; upward bursts only. Both EWMAs run from t=0."""

    ID = "A07"
    DEFAULTS = {"fast": 20, "slow": 300, "z": 3.0, "width": 100, "reserve": 20}
    SETTINGS = [{"fast": 50, "slow": 300}, {"fast": 20, "slow": 150}]

    def __init__(self, *a):
        self.ef = self.es = None
        super().__init__(*a)

    def _track(self, ctx):
        x = float(ctx.disagree)
        af, as_ = 2 / (self.params["fast"] + 1), 2 / (self.params["slow"] + 1)
        self.ef = x if self.ef is None else self.ef + af * (x - self.ef)
        self.es = x if self.es is None else self.es + as_ * (x - self.es)

    def _signal(self, ctx):
        af = 2 / (self.params["fast"] + 1)
        s = min(0.98, max(0.02, self.es))
        sd = math.sqrt(s * (1 - s) * af / (2 - af))
        return self.ef - self.es > self.params["z"] * sd


@register
class A08(_Alarm):
    """Prediction turnover alarm: per-model prediction-flip frequency over the last ``window``
    events against the frozen pre-cutoff frequency; alarm if either model has |z| > ``z``. This
    is label-free; in the sealed simulator the labels are random, so flips are near-stationary and
    the module is expected to be close to inert."""

    ID = "A08"
    DEFAULTS = {"window": 100, "z": 3.0, "width": 100, "reserve": 20}
    SETTINGS = [{"window": 100, "z": 3.0}, {"window": 50, "z": 2.0}]

    def __init__(self, *a):
        self.prev = None
        self.buf = deque()
        self.cw = [0, 0]
        self.pn = 0
        self.pc = [0, 0]
        super().__init__(*a)

    def _flip(self, ctx):
        if self.prev is None:
            return (0, 0)
        return (int(ctx.preds[0] != self.prev[0]), int(ctx.preds[1] != self.prev[1]))

    def _track(self, ctx):
        f = self._flip(ctx)
        self.prev = ctx.preds
        self.buf.append(f)
        self.cw[0] += f[0]
        self.cw[1] += f[1]
        if len(self.buf) > self.params["window"]:
            o = self.buf.popleft()
            self.cw[0] -= o[0]
            self.cw[1] -= o[1]
        self._f = f

    def _pre(self, ctx):
        super()._pre(ctx)
        self.pn += 1
        self.pc[0] += self._f[0]
        self.pc[1] += self._f[1]

    def _freeze(self, ctx):
        super()._freeze(ctx)
        self.f0 = [min(0.98, max(0.02, c / self.pn)) if self.pn else 0.5 for c in self.pc]

    def _signal(self, ctx):
        w = len(self.buf)
        if w < self.params["window"]:
            return False
        for m in (0, 1):
            f0 = self.f0[m]
            if abs(self.cw[m] / w - f0) / math.sqrt(f0 * (1 - f0) / w) > self.params["z"]:
                return True
        return False
