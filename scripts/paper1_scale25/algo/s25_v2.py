# ruff: noqa
"""v2 candidate modules (development search only; see docs/paper1_scale25/04_ALGORITHM_DEVELOPMENT.md).

All sit on the frozen parent (EQSDp or Wald + cutoff 1100) through the compositor and see only ctx
(t, parent evidence on released labels, pending count, remaining budget, declared contract).
Imported by s25_modules (so every worker registers them).
"""

from __future__ import annotations

import json
from collections import deque

import numpy as np
import s25_common
from compositor import Force, Module, register
from modules_E import E48, Post, _bb_all, adv, gain_q, pace_ok, surv
from modules_F import F60


class _V2(Module):
    FAMILY = "E"


def _hx(ctx, t, h):
    H = max(0, ctx.T - t)
    return H * surv(H, h)


class _Override:
    """Mixin: a decision made at a release is applied once, at the next prediction."""

    def _ov_init(self):
        self.want = None

    def override_deploy(self, ctx):
        w, self.want = self.want, None
        if w is not None and w != ctx.parent.deployed:
            return w
        return None

    def on_deploy_change(self, ctx, frm, to):
        self.want = None


@register
class EAP(_Override, _V2):
    """Early adoption under a change-hazard posterior (released labels only).

    At each released label form the hazard-mixture posterior (Post, moment-matched Beta). mode 'q':
    adopt the other model when the ``gamma2``-quantile payback over the hazard-discounted remaining
    horizon exceeds ``mult`` x c_s. mode 'dp': one-step optimal stopping: adopt iff the posterior-mean
    payback net of c_s is positive and at least the value of waiting for the labels in flight (they
    land within ``delay``; waiting shortens the horizon by delay/2). Applied through override_deploy;
    the parent's own rule keeps running."""

    ID = "EAP"
    DEFAULTS = {"gamma2": 0.4, "hazard": 0.002, "mw": 8, "mult": 1.0, "min_n": 3, "mode": "q"}
    SETTINGS = [{"gamma2": 0.4}, {"gamma2": 0.5}]

    def __init__(self, *a):
        super().__init__(*a)
        self._ov_init()
        self.post = Post(self.params["hazard"], self.params["mw"])
        self.nl = 0

    def on_release(self, ctx, fb):
        self.post.add(fb)
        if fb.d == 0:
            return
        self.nl += 1
        if self.nl < self.params["min_n"]:
            return
        t, h, dep, cs = fb.t_released, self.params["hazard"], ctx.deployed, ctx.parent.cs
        a, b = self.post.eff(t)
        Hx = _hx(ctx, t, h)
        rate = ctx.rate
        if self.params["mode"] == "q":
            ok = gain_q(a, b, dep, self.params["gamma2"], rate, Hx) > self.params["mult"] * cs
        else:
            v_now = adv(a / (a + b), dep) * rate * Hx - cs * self.params["mult"]
            m = min(ctx.pending, 10)
            Hw = max(0.0, Hx - ctx.delay / 2)
            v_wait = 0.0
            for j, wj in enumerate(_bb_all(m, a, b)):
                v_wait += wj * max(0.0, adv((a + j) / (a + b + m), dep) * rate * Hw - cs)
            ok = v_now > 0.0 and v_now >= v_wait
        self.want = (1 - dep) if ok else None


@register
class DPW(EAP):
    ID = "DPW"
    DEFAULTS = {**EAP.DEFAULTS, "mode": "dp"}
    SETTINGS = [{"mode": "dp"}, {"mode": "dp", "mw": 12}]


class _AdaptiveHaz:
    """Mixin: scale the change hazard by recent-vs-overall disagreement of released labels."""

    def _ah_init(self):
        self.recw = deque(maxlen=8)
        self.sum_all = 0
        self.n_all = 0
        self.h0 = self.params["hazard"]

    def _ah_update(self, fb):
        if fb.d == 0:
            return
        x = int(fb.d > 0)
        self.recw.append(x)
        self.sum_all += x
        self.n_all += 1
        if len(self.recw) >= 4:
            z = abs(np.mean(self.recw) - self.sum_all / self.n_all) * np.sqrt(len(self.recw)) / 0.5
            h = min(self.params["hmax"], self.h0 * float(np.exp(self.params["kappa"] * z)))
            self.params["hazard"] = h
            self.post.h = h


@register
class E48A(_AdaptiveHaz, E48):
    ID = "E48A"
    DEFAULTS = {**E48.DEFAULTS, "kappa": 1.0, "hmax": 0.02}
    SETTINGS = [
        {"arrival_discount": 0.5, "lookahead": 50, "kappa": 1.0},
        {"arrival_discount": 0.5, "lookahead": 50, "kappa": 2.0},
    ]

    def __init__(self, *a):
        super().__init__(*a)
        self._ah_init()

    def on_release(self, ctx, fb):
        self._ah_update(fb)
        super().on_release(ctx, fb)


@register
class F60A(_AdaptiveHaz, F60):
    ID = "F60A"
    DEFAULTS = {**F60.DEFAULTS, "kappa": 1.0, "hmax": 0.02}
    SETTINGS = [
        {"bundle": 2, "horizon": 100, "kappa": 1.0},
        {"bundle": 2, "horizon": 100, "kappa": 2.0},
    ]

    def __init__(self, *a):
        super().__init__(*a)
        self._ah_init()

    def on_release(self, ctx, fb):
        self._ah_update(fb)
        super().on_release(ctx, fb)


@register
class INS(_V2):
    """Evidence-insurance floor: buy a disagreement event when no label has been requested for
    ``age`` events (pacing guard, cutoff and delay respected; not suppressed by gates)."""

    ID = "INS"
    DEFAULTS = {"age": 150}
    SETTINGS = [{"age": 150}, {"age": 80}]

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable or not pace_ok(ctx):
            return None
        last = ctx.last_buy_t if ctx.last_buy_t >= 0 else 0
        return Force("force", 1.0, "INS") if ctx.t - last >= self.params["age"] else None


# ---- learned switching controller (LSW) -----------------------------------------------------
LSW_JSON = s25_common.OUT / "lsw_params.json"
LSW_FEATS = ["mu_d", "m8", "m3", "m_all", "bias"]


def lsw_features(parent, rec, sum_all, n_all):
    mu = (parent.k + 1.0) / (parent.n + 2.0)
    m8 = (sum(rec) + 1.0) / (len(rec) + 2.0)
    r3 = list(rec)[-3:]
    m3 = (sum(r3) + 1.0) / (len(r3) + 2.0)
    return [mu, m8, m3, (sum_all + 1.0) / (n_all + 2.0), 1.0]


@register
class LREC(_V2):
    """Recorder (no behaviour change): features at each release; targets are attached offline."""

    ID = "LREC"
    DEFAULTS = {}
    SETTINGS = [{}, {}]
    REC: list | None = None

    def __init__(self, *a):
        super().__init__(*a)
        self.recw = deque(maxlen=8)
        self.sa = self.na = 0

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        x = int(fb.d > 0)
        self.recw.append(x)
        self.sa += x
        self.na += 1
        if LREC.REC is not None and self.na >= 3:
            LREC.REC.append(
                {
                    "t": fb.t_released,
                    "x": lsw_features(ctx.parent, self.recw, self.sa, self.na),
                    "n": ctx.n,
                    "rate": ctx.rate,
                }
            )


@register
class LSW(_Override, _V2):
    """Learned switching: ridge model (fitted on EVEN development episodes only, lsw_train.py)
    predicts the future P(challenger correct | disagreement) over the next 300 disagreement events
    from observable features; adopt the other model when
    (adv_hat - 2 z sigma(n)) * rate * H_eff > mult * c_s."""

    ID = "LSW"
    DEFAULTS = {"z": 0.5, "mult": 1.0, "hazard": 0.002, "min_n": 3}
    SETTINGS = [{"z": 0.5}, {"z": 0.0}]
    _PAR = None

    def __init__(self, *a):
        super().__init__(*a)
        self._ov_init()
        if LSW._PAR is None:
            LSW._PAR = json.loads(LSW_JSON.read_text(encoding="utf-8"))
        self.par = LSW._PAR
        self.recw = deque(maxlen=8)
        self.sa = self.na = 0

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        x = int(fb.d > 0)
        self.recw.append(x)
        self.sa += x
        self.na += 1
        if self.na < self.params["min_n"]:
            return
        f = lsw_features(ctx.parent, self.recw, self.sa, self.na)
        p_hat = float(np.clip(np.dot(np.array(self.par["w"]), f), 0.0, 1.0))
        sig = self.par["sigma0"] / np.sqrt(max(1.0, 1.0 + 0.5 * ctx.n))
        dep = ctx.deployed
        a = (2 * p_hat - 1) if dep == 0 else (1 - 2 * p_hat)
        Hx = _hx(ctx, fb.t_released, self.params["hazard"])
        g = (a - 2 * self.params["z"] * sig) * ctx.rate * Hx
        self.want = (1 - dep) if g > self.params["mult"] * ctx.parent.cs else None
