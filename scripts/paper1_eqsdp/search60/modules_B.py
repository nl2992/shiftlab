# ruff: noqa: RUF012
"""Family B (B11-B20): budgeted label acquisition (gates, floors, reserves, pacing scales).

Interpretations where the catalogue is silent (see also COMPOSITION_RULES.md):

* B11, B16, B17, B18, B19, B20 honour the parent cutoff (they never buy after it closes); B12,
  B14, B15 are explicit cutoff exceptions and are logged as such.
* B12: the parent's pacer already has a propensity floor of 0.05 before the cutoff, so a floor
  ``p_min <= 0.05`` can only matter after the cutoff. The module therefore buys each closed,
  releasable disagreement event with probability ``p_min`` (own random stream), capped by
  ``reserve`` (default 20, held back before the cutoff like family A).
* B14/B15: a packet of labels is held back (armed) from the pre-promotion / pre-reversal budget; in
  the ``W`` events after a promotion to model 1 (B14) or a return to model 0 (B15) the cutoff is
  lifted for the parent's paced draw until ``packet`` labels were spent. The reserve is released
  after the window and re-armed at the next such switch.
* B13: the reserve is ``reserve`` x B labels for t > ``after`` (800). Anything that buys inside the
  window (parent while open, or a family A sentinel) draws it down.
"""

from __future__ import annotations

import math

from compositor import NEVER, Force, Module, Reserve, register


class _B(Module):
    FAMILY = "B"


@register
class B11(_B):
    """Maximum eligible-query gap: after ``G`` disagreement opportunities (cutoff open) without a
    purchase, buy the next one (floor). Counter resets on any purchase."""

    ID = "B11"
    DEFAULTS = {"G": 50}
    SETTINGS = [{"G": 100}, {"G": 20}]

    def __init__(self, *a):
        super().__init__(*a)
        self.cnt = 0

    def floor(self, ctx):
        if ctx.closed:
            return None
        if self.cnt >= self.params["G"]:
            return Force("force", 1.0, self.ID)
        self.cnt += 1
        return None

    def on_purchase(self, ctx, rec):
        self.cnt = 0


@register
class B12(_B):
    """Randomised minimum propensity after the cutoff (see module docstring)."""

    ID = "B12"
    DEFAULTS = {"p_min": 0.03, "reserve": 20}
    SETTINGS = [{"p_min": 0.01}, {"p_min": 0.05}]

    def __init__(self, *a):
        super().__init__(*a)
        self.spent = 0

    def floor(self, ctx):
        eligible = ctx.closed and ctx.releasable and self.spent < self.params["reserve"]
        if eligible and self.rng.random() < self.params["p_min"]:
            return Force("force", float(self.params["p_min"]), self.ID)
        return None

    def reserves(self, ctx):
        if ctx.t_close is None:
            return []
        return [Reserve(self.ID, int(self.params["reserve"]), lo=ctx.t_close)]

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class B13(_B):
    """Split-period budget reserve: ``reserve`` x B labels are kept for t > ``after``."""

    ID = "B13"
    DEFAULTS = {"reserve": 0.2, "after": 800}
    SETTINGS = [{"reserve": 0.1}, {"reserve": 0.3}]

    def reserves(self, ctx):
        return [
            Reserve(self.ID, round(self.params["reserve"] * ctx.B), lo=self.params["after"] + 1)
        ]


class _Packet(_B):
    TO = 1
    DEFAULTS = {"packet": 5, "W": 100}
    SETTINGS = [{"packet": 5, "W": 100}, {"packet": 10, "W": 200}]

    def __init__(self, *a):
        super().__init__(*a)
        self.t0, self.gen, self.spent = None, 0, 0

    def on_deploy_change(self, ctx, frm, to):
        if to == self.TO:
            self.t0, self.gen, self.spent = ctx.t, self.gen + 1, 0

    def _active(self, ctx):
        return self.t0 is not None and self.t0 <= ctx.t < self.t0 + self.params["W"]

    def floor(self, ctx):
        if (
            self._active(ctx)
            and ctx.closed
            and ctx.releasable
            and self.spent < self.params["packet"]
        ):
            return Force("lift", reason=self.ID)
        return None

    def reserves(self, ctx):
        k, n = f"{self.gen}", int(self.params["packet"])
        if self._active(ctx):
            return [Reserve(f"w{k}", n, lo=self.t0, hi=self.t0 + self.params["W"])]
        return [Reserve(f"a{k}", n, lo=NEVER, hi=NEVER + 1)]  # armed: held, not yet triggered

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class B14(_Packet):
    """Post-promotion reserve (a switch to model 1)."""

    ID = "B14"
    TO = 1


@register
class B15(_Packet):
    """Post-reversal reserve (a return to model 0)."""

    ID = "B15"
    TO = 0


@register
class B16(_B):
    """Pending-queue cap: veto a purchase when ``pending_cap`` or more labels are in flight."""

    ID = "B16"
    DEFAULTS = {"pending_cap": 10}
    SETTINGS = [{"pending_cap": 20}, {"pending_cap": 5}]

    def veto(self, ctx):
        return "pending_cap" if ctx.pending >= self.params["pending_cap"] else None


@register
class B17(_B):
    """Pending-age priority: labels already in flight that will arrive within ``max_pending_age``
    events are likely to arrive early enough to inform the next action, so a new purchase is
    down-weighted: scale = 1 / (1 + age_penalty * n_early), n_early = in-flight labels whose release
    time is at most ``max_pending_age`` events away."""

    ID = "B17"
    DEFAULTS = {"max_pending_age": 100, "age_penalty": 0.3}
    SETTINGS = [
        {"max_pending_age": 50, "age_penalty": 0.3},
        {"max_pending_age": 100, "age_penalty": 1.0},
    ]

    def scale(self, ctx):
        n = sum(
            1
            for t0 in ctx.pend_t.values()
            if t0 + ctx.delay - ctx.t <= self.params["max_pending_age"]
        )
        return 1.0 / (1.0 + self.params["age_penalty"] * n)


@register
class B18(_B):
    """Posterior-uncertainty pacing: scale = clip(gain * 12 * Var[p], floor, 2) with Var the Beta(k+1,
    n-k+1) variance of the parent's evidence (12 x the Beta(1,1) variance = 1)."""

    ID = "B18"
    DEFAULTS = {"gain": 1.5, "floor": 0.3}
    SETTINGS = [{"gain": 0.5, "floor": 0.1}, {"gain": 1.5, "floor": 0.3}]

    def scale(self, ctx):
        a, b = ctx.k + 1.0, ctx.n - ctx.k + 1.0
        var = a * b / ((a + b) ** 2 * (a + b + 1.0))
        return min(2.0, max(self.params["floor"], self.params["gain"] * 12.0 * var))


@register
class B19(_B):
    """Decision-boundary proximity pacing: with g the parent's payback of switching away at its own
    gamma-quantile, prox = max(0, 1 - |g - c_s| / (band * c_s)) and scale = floor + (1 - floor) *
    prox, i.e. buying is relatively higher near the boundary and never below ``floor``. Inactive
    (scale 1) until ``warm`` = 5 labels have been released."""

    ID = "B19"
    DEFAULTS = {"band": 5.0, "floor": 0.15, "warm": 5}
    SETTINGS = [{"band": 5.0, "floor": 0.15}, {"band": 10.0, "floor": 0.05}]

    def scale(self, ctx):
        if ctx.n < self.params["warm"]:
            return None
        cs = ctx.parent.cs
        g = ctx.gain_away(ctx.parent.gamma)
        prox = max(0.0, 1.0 - abs(g - cs) / (self.params["band"] * cs))
        if math.isnan(prox):
            return None
        return self.params["floor"] + (1.0 - self.params["floor"]) * prox


@register
class B20(_B):
    """Prediction-pattern stratified acquisition: purchases are tracked per disagreement pattern
    ((0,1) vs (1,0)). Once 10 labels were bought, a purchase on a pattern whose share of purchases
    exceeds ``target_balance`` is vetoed unless a random pass with probability ``min_rate`` fires."""

    ID = "B20"
    DEFAULTS = {"target_balance": 0.5, "min_rate": 0.01}
    SETTINGS = [
        {"target_balance": 0.75, "min_rate": 0.01},
        {"target_balance": 0.5, "min_rate": 0.01},
    ]

    def __init__(self, *a):
        super().__init__(*a)
        self.c = {(0, 1): 0, (1, 0): 0}

    def veto(self, ctx):
        tot = sum(self.c.values())
        pat = tuple(ctx.preds)
        if tot < 10 or pat not in self.c:
            return None
        if self.c[pat] / tot > self.params["target_balance"]:
            if self.rng.random() < self.params["min_rate"]:
                return None
            return "pattern_quota"
        return None

    def on_purchase(self, ctx, rec):
        pat = tuple(ctx.preds)
        if pat in self.c:
            self.c[pat] += 1
