# ruff: noqa: RUF012
"""Family D (D31-D40): switching and rollback overlays on the parent's decision rule.

The parent flips inside its own ``observe``; the compositor lets modules (i) veto that flip
(``on_switch_proposal``) and (ii) force the deployed model at the next prediction
(``override_deploy``). Modules that change the *rule* (D34 direction gammas, D35 hurdle, D36
horizon, D37 alarm hurdle, D39 gamma schedule, D40 band) re-evaluate the parent's own rule
``adv(Q_gamma(p)) * rate * H - hurdle`` on the parent's counts (``parent._q``, so Beta for EQSDp
and Wald for the Wald parent) and veto parent flips they do not support; those that can only be
*more* conservative than the parent (D35, D36, D40) are veto-only, those that may also be more
aggressive (D34, D37, D39) can additionally promote/reverse once after a release. With default
parameters equal to the parent's they are inert by construction.

Hook gap: ``override_deploy`` is not routed through ``on_switch_proposal``, so a D veto cannot
block a C-family override (C modules decide on their own belief); and rollback modules (D32, D33)
re-use ``override_deploy``. Re-promotion after a rollback is blocked by a ``cooldown`` veto.
"""

from __future__ import annotations

import math

from compositor import Force, Module, register
from modules_C import Overlay


class _D(Module):
    FAMILY = "D"


class _POverlay(Overlay):
    """Overlay on the parent's own evidence (parent._q), family D."""

    FAMILY = "D"

    def quant(self, u):
        return self.ctx.parent._q(u)


@register
class D31(_D):
    """Promotion confirmation: the first parent promotion proposal is vetoed; it is allowed once
    ``needed`` further informative released labels arrived and the parent still proposes it,
    within ``timeout`` events (otherwise the clock restarts)."""

    ID = "D31"
    DEFAULTS = {"needed": 1, "timeout": 100}
    SETTINGS = [{"needed": 1, "timeout": 100}, {"needed": 2, "timeout": 200}]

    def __init__(self, *a):
        super().__init__(*a)
        self.first_t, self.cnt, self.n_veto = None, 0, 0

    def on_release(self, ctx, fb):
        if fb.d != 0 and self.first_t is not None:
            self.cnt += 1

    def on_switch_proposal(self, ctx, prop):
        if prop.frm != 0:
            return
        if (
            self.first_t is not None
            and prop.t - self.first_t <= self.params["timeout"]
            and self.cnt >= self.params["needed"]
        ):
            self.first_t, self.cnt = None, 0
            return
        if self.first_t is None or prop.t - self.first_t > self.params["timeout"]:
            self.first_t, self.cnt = prop.t, 0
        self.n_veto += 1
        prop.veto(f"D31:confirm {self.cnt}/{self.params['needed']}")


class _Probation(_D):
    """Shared state: probation window after a promotion, rollback + re-promotion cooldown."""

    DEFAULTS = {"probation": 100, "cooldown": 50}

    def __init__(self, *a):
        super().__init__(*a)
        self.prom_t = None
        self.ds: list = []
        self.cool_until = -1
        self.rb = False
        self.n_rollback = 0

    def active(self, t):
        return self.prom_t is not None and t < self.prom_t + self.params["probation"]

    def adverse(self):  # subclass: True when the probation labels call for a rollback
        return False

    def on_deploy_change(self, ctx, frm, to):
        if to == 1 and frm == 0:
            self.prom_t, self.ds, self.rb = ctx.t, [], False
        else:
            self.prom_t = None

    def on_release(self, ctx, fb):
        if fb.d == 0 or not self.active(fb.t_released) or ctx.deployed != 1:
            return
        self.ds.append(fb.d)
        if self.adverse():
            self.rb = True

    def on_switch_proposal(self, ctx, prop):
        if prop.frm == 0 and prop.t < self.cool_until:
            prop.veto(f"{self.ID}:cooldown")

    def override_deploy(self, ctx):
        if self.rb and ctx.deployed == 1:
            self.rb, self.prom_t = False, None
            self.cool_until = ctx.t + self.params["cooldown"]
            self.n_rollback += 1
            return 0
        self.rb = False
        return None


@register
class D32(_Probation):
    """Probation after a promotion: ``extra_queries`` forced labels (cutoff permitting) and a
    conditional rollback when >= ``min_labels`` probation labels have net loss gap <= -``rb_net``."""

    ID = "D32"
    DEFAULTS = {**_Probation.DEFAULTS, "extra_queries": 5, "min_labels": 3, "rb_net": 2}
    SETTINGS = [{"probation": 50, "extra_queries": 5}, {"probation": 100, "extra_queries": 10}]

    def __init__(self, *a):
        super().__init__(*a)
        self.spent = 0

    def on_deploy_change(self, ctx, frm, to):
        super().on_deploy_change(ctx, frm, to)
        if to == 1 and frm == 0:
            self.spent = 0

    def adverse(self):
        return len(self.ds) >= self.params["min_labels"] and sum(self.ds) <= -self.params["rb_net"]

    def floor(self, ctx):
        if (
            self.active(ctx.t)
            and ctx.deployed == 1
            and not ctx.closed
            and self.spent < self.params["extra_queries"]
        ):
            return Force("force", 1.0, self.ID)
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class D33(_Probation):
    """Fast rollback: during probation, reverse when the net loss gap of the last ``window``
    released labels is <= -``threshold``."""

    ID = "D33"
    DEFAULTS = {**_Probation.DEFAULTS, "window": 10, "threshold": 4}
    SETTINGS = [{"window": 5, "threshold": 2}, {"window": 10, "threshold": 4}]

    def adverse(self):
        return sum(self.ds[-int(self.params["window"]) :]) <= -self.params["threshold"]


@register
class D34(_POverlay):
    """Direction-specific gamma: ``gamma_enter`` for promotion (0->1), ``gamma_exit`` for reversal."""

    ID = "D34"
    DEFAULTS = {"gamma_enter": 0.3, "gamma_exit": 0.3}
    SETTINGS = [{"gamma_enter": 0.2, "gamma_exit": 0.1}, {"gamma_enter": 0.35, "gamma_exit": 0.3}]

    def gamma(self, ctx, t, dep):
        return self.params["gamma_enter" if dep == 0 else "gamma_exit"]


@register
class D35(_POverlay):
    """Switch-count hurdle: c_s * (1 + slope * sum_i exp(-(t - t_i)/decay)) over earlier reversals
    (every deployment change after the first). Veto-only (it can only raise the hurdle)."""

    ID = "D35"
    DEFAULTS = {"slope": 1.0, "decay": 200.0}
    SETTINGS = [{"slope": 1.0, "decay": 100.0}, {"slope": 3.0, "decay": 300.0}]
    CAN_OVERRIDE = False

    def __init__(self, *a):
        super().__init__(*a)
        self.sw: list = []

    def on_deploy_change(self, ctx, frm, to):
        self.sw.append(ctx.t)

    def hurdle(self, ctx, t, dep):
        s = sum(math.exp(-(t - ti) / self.params["decay"]) for ti in self.sw[1:])
        return ctx.parent.cs * (1.0 + self.params["slope"] * s)


@register
class D36(_POverlay):
    """Persistence-adjusted payback: remaining horizon R replaced by
    max(floor_horizon, (1 - exp(-hazard R)) / hazard), capped at R. Veto-only."""

    ID = "D36"
    DEFAULTS = {"hazard": 0.001, "floor_horizon": 200}
    SETTINGS = [{"hazard": 0.0005, "floor_horizon": 100}, {"hazard": 0.002, "floor_horizon": 300}]
    CAN_OVERRIDE = False

    def horizon(self, ctx, t):
        R = max(ctx.T - t, 0.0)
        h = self.params["hazard"]
        return min(R, max(self.params["floor_horizon"], (1.0 - math.exp(-h * R)) / h))


@register
class D37(_POverlay):
    """Alarm-conditioned emergency promotion: a CUSUM of released challenger-favouring outcomes
    (drift ``cusum_k``) alarms at ``alarm_h``; for ``window`` events the promotion hurdle is
    c_s * ``hurdle_scale``. Can only promote (no veto)."""

    ID = "D37"
    DEFAULTS = {"hurdle_scale": 0.8, "window": 100, "cusum_k": 0.2, "alarm_h": 3.0}
    SETTINGS = [{"hurdle_scale": 0.6, "window": 100}, {"hurdle_scale": 0.8, "window": 200}]
    CAN_VETO = False

    def __init__(self, *a):
        super().__init__(*a)
        self.s, self.until, self.n_alarm = 0.0, -1, 0

    def update(self, ctx, fb):
        self.s = max(0.0, self.s + fb.d - self.params["cusum_k"])
        if self.s >= self.params["alarm_h"]:
            self.s, self.until = 0.0, fb.t_released + self.params["window"]
            self.n_alarm += 1

    def hurdle(self, ctx, t, dep):
        cs = ctx.parent.cs
        return cs * self.params["hurdle_scale"] if (dep == 0 and t < self.until) else cs


@register
class D38(_D):
    """Query-burst confirmation: when the deployed model's payback is within ``band`` loss units
    below the hurdle after a released label, force ``packet`` disagreement labels (cutoff open)
    within 60 events, at most ``max_bursts`` times, ``cooldown`` events apart."""

    ID = "D38"
    DEFAULTS = {"packet": 3, "band": 2.0, "cooldown": 100, "max_bursts": 6, "span": 60}
    SETTINGS = [{"packet": 3, "band": 2.0}, {"packet": 5, "band": 5.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self.left, self.until, self.next_ok, self.bursts = 0, -1, 0, 0

    def on_release(self, ctx, fb):
        if fb.d == 0 or self.left > 0 or self.bursts >= self.params["max_bursts"]:
            return
        if fb.t_released < self.next_ok or ctx.closed:
            return
        g = ctx.gain_away(ctx.parent.gamma) - ctx.parent.cs
        if -self.params["band"] < g <= 0.0:
            self.left, self.until = int(self.params["packet"]), fb.t_released + self.params["span"]
            self.next_ok = fb.t_released + self.params["cooldown"]
            self.bursts += 1

    def floor(self, ctx):
        if self.left > 0 and ctx.t < self.until and not ctx.closed:
            return Force("force", 1.0, self.ID)
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.left -= 1


@register
class D39(_POverlay):
    """Horizon-dependent quantile level: gamma(t) = gamma_early + (gamma_late - gamma_early) t/T."""

    ID = "D39"
    DEFAULTS = {"gamma_early": 0.3, "gamma_late": 0.3}
    SETTINGS = [{"gamma_early": 0.3, "gamma_late": 0.1}, {"gamma_early": 0.45, "gamma_late": 0.2}]

    def gamma(self, ctx, t, dep):
        f = min(max(t / ctx.T, 0.0), 1.0)
        return (
            self.params["gamma_early"]
            + (self.params["gamma_late"] - self.params["gamma_early"]) * f
        )


@register
class D40(_POverlay):
    """Posterior no-action band: extra hurdle ``band`` * 0.05 * sd of the payback, with
    sd = 2 sd(p) * rate * (T - t) and sd(p) the Beta posterior sd on the parent's counts. Veto-only."""

    ID = "D40"
    DEFAULTS = {"band": 3.0}
    SETTINGS = [{"band": 1.0}, {"band": 5.0}]
    CAN_OVERRIDE = False

    def hurdle(self, ctx, t, dep):
        m = (ctx.k + 1.0) / (ctx.n + 2.0)
        sd_p = math.sqrt(m * (1 - m) / (ctx.n + 3.0))
        extra = self.params["band"] * 0.05 * 2.0 * sd_p * ctx.rate * (ctx.T - t)
        return ctx.parent.cs + extra
