# ruff: noqa: RUF012
"""Family F (F51-F60): pulses, alarm-triggered reserves, fusion, arbitration, learned controller, bundle VOI.

Interpretations (see also modules_E.py, whose Post / voi / Shadow / _IPW helpers are reused):

* F51/F52: forced purchases on a fixed schedule at disagreement events (F51 counts only its own
  packet; the parent's draws are additional). F52 holds its packet with a ``Reserve`` before
  ``start`` and spends it after the cutoff (logged cutoff exceptions).
* F53/F55/F56: reserves are armed before the trigger (held, not yet triggered) like B14/B15.
* F55 free signal = disagreement-rate z-score (last 100 events vs the first 200); paid signal =
  z-score of the challenger-win share of the last 20 released labels vs the older ones.
* F58: the compositor has ONE deployed state, so the "experimental policy" is the composed policy
  while F58 lets it run and the "parent policy" is a frozen shadow replica (modules_E.Shadow).
  While in experiment mode both trajectories are scored on released labels: paired loss difference
  (identifiable, d = l0 - l1) weighted by capped IPW, minus ``penalty`` x cs per extra switch of the
  experiment. A negative score (>= 3 differing labels) hands control to the parent; the
  counterfactual experiment trajectory is not observable in parent mode, so the retry is time based
  (5 x score_window events). Alone (no add-on) the two policies coincide and F58 is inert. HOOK GAP:
  F58 cannot see overrides of the later-precedence families (D, C, B, A) before it decides.
* F59: see ``train_f59`` and ``f59_params.json``.
"""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

from compositor import NEVER, Force, Module, Reserve, register
from modules_E import _IPW, Post, Shadow, _DepHist, gain_q, pace_ok, price, surv, voi

HERE = Path(__file__).resolve().parent
F59_JSON = HERE / "f59_params.json"


class _F(Module):
    FAMILY = "F"

    @staticmethod
    def _can(ctx):
        return (not ctx.closed) and ctx.releasable


@register
class F51(_F):
    """Front-loaded startup pulse: ``packet`` forced labels spread evenly over [0, duration)."""

    ID = "F51"
    DEFAULTS = {"packet": 10, "duration": 200}
    SETTINGS = [{"packet": 5, "duration": 100}, {"packet": 10, "duration": 200}]

    def __init__(self, *a):
        super().__init__(*a)
        self.spent = 0

    def floor(self, ctx):
        p = self.params
        due = ctx.t >= self.spent * p["duration"] / p["packet"]
        if ctx.t < p["duration"] and self.spent < p["packet"] and due and self._can(ctx):
            return Force("force", 1.0, self.ID)
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class F52(_F):
    """Backloaded evidence pulse: ``packet`` labels are reserved before ``start`` and bought at evenly
    spaced disagreement events in [start, T - delay), after the cutoff (cutoff exception)."""

    ID = "F52"
    DEFAULTS = {"packet": 10, "start": 1400}
    SETTINGS = [{"packet": 5, "start": 1100}, {"packet": 10, "start": 1400}]

    def __init__(self, *a):
        super().__init__(*a)
        self.spent = 0

    def floor(self, ctx):
        p = self.params
        s, n = p["start"], p["packet"]
        span = max(1, ctx.T - ctx.delay - s)
        if ctx.t >= s and self.spent < n and ctx.releasable and ctx.t >= s + self.spent * span / n:
            return Force("force", 1.0, self.ID)
        return None

    def reserves(self, ctx):
        return [Reserve(self.ID, int(self.params["packet"]), lo=self.params["start"])]

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


class _Z:
    """Free (disagreement-rate) and paid (released-sign) change z-scores, shared by F53/F55."""

    def _z_init(self, base=200, win=100, rec=20):
        self.base, self.win, self.rec = base, win, rec
        self.dq = deque(maxlen=win)
        self.nb = self.sb = 0
        self.ws = []

    def z_free(self, ctx):
        self.dq.append(int(ctx.disagree))
        if ctx.t < self.base:
            self.nb += 1
            self.sb += int(ctx.disagree)
            return 0.0
        mu = min(0.95, max(0.05, self.sb / max(1, self.nb)))
        if len(self.dq) < self.win:
            return 0.0
        return (sum(self.dq) / self.win - mu) / math.sqrt(mu * (1 - mu) / self.win)

    def z_paid_add(self, fb):
        if fb.d != 0:
            self.ws.append(int(fb.d > 0))

    def z_paid(self):
        r = self.rec
        if len(self.ws) < 2 * r:
            return 0.0
        old = self.ws[:-r]
        po = min(0.95, max(0.05, sum(old) / len(old)))
        return (sum(self.ws[-r:]) / r - po) / math.sqrt(po * (1 - po) / r)


@register
class F53(_Z, _F):
    """Alarm-triggered reserve release. ``reserve`` labels are held (armed) until a free alarm
    (|z_free| > alarm_z) or a paid alarm (|z_paid| > alarm_z); then the cutoff is lifted for the
    parent's paced draw for 150 events until the reserve is spent; re-armed once."""

    ID = "F53"
    DEFAULTS = {"reserve": 10, "alarm_z": 3.0, "W": 150, "max_alarms": 2}
    SETTINGS = [{"reserve": 10, "alarm_z": 3.0}, {"reserve": 20, "alarm_z": 2.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self._z_init()
        self.t0, self.gen, self.spent = None, 0, 0
        self.zp = 0.0

    def on_release(self, ctx, fb):
        self.z_paid_add(fb)
        self.zp = self.z_paid()

    def _active(self, ctx):
        return self.t0 is not None and self.t0 <= ctx.t < self.t0 + self.params["W"]

    def on_event(self, ctx):
        zf = self.z_free(ctx)
        if self._active(ctx) or self.gen >= self.params["max_alarms"] or ctx.t < self.base:
            return
        z = self.params["alarm_z"]
        if abs(zf) > z or abs(self.zp) > z:
            self.t0, self.gen, self.spent = ctx.t, self.gen + 1, 0

    def floor(self, ctx):
        if (
            self._active(ctx)
            and ctx.closed
            and ctx.releasable
            and self.spent < self.params["reserve"]
        ):
            return Force("lift", reason=self.ID)
        return None

    def reserves(self, ctx):
        k, n = f"{self.gen}", int(self.params["reserve"])
        if self._active(ctx):
            return [Reserve(f"w{k}", n, lo=self.t0, hi=self.t0 + self.params["W"])]
        if self.gen < self.params["max_alarms"]:
            return [Reserve(f"a{k}", n, lo=NEVER, hi=NEVER + 1)]
        return []

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class F54(_F):
    """Sequential surprise burst. A released label is surprising if its outcome had predictive
    probability < 0.4 under the parent's posterior mean before it arrived (>= 6 labels seen).
    ``surprises`` consecutive surprises raise the parent's propensity x4 for the next ``burst``
    purchases (within 150 events, parent cutoff respected)."""

    ID = "F54"
    DEFAULTS = {"surprises": 2, "burst": 10, "mult": 4.0}
    SETTINGS = [{"surprises": 2, "burst": 5}, {"surprises": 3, "burst": 10}]

    def __init__(self, *a):
        super().__init__(*a)
        self.mu, self.cnt, self.left, self.end = 0.5, 0, 0, -1

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        pr = self.mu if fb.d > 0 else 1.0 - self.mu
        if ctx.n >= 6 and pr < 0.4:
            self.cnt += 1
        else:
            self.cnt = 0
        if self.cnt >= self.params["surprises"]:
            self.cnt, self.left, self.end = 0, self.params["burst"], fb.t_released + 150
        self.mu = (ctx.k + 1.0) / (ctx.n + 2.0)

    def scale(self, ctx):
        return self.params["mult"] if self.left > 0 and ctx.t < self.end else None

    def on_purchase(self, ctx, rec):
        if self.left > 0 and ctx.t < self.end:
            self.left -= 1


@register
class F55(_Z, _F):
    """Unlabeled/labeled sensor fusion. Free alarm: |z_free| > 3; paid alarm: |z_paid| > 3, each
    latched for ``horizon`` events. ``OR``: either; ``AND``: both latched; ``weighted``:
    0.4 min(|z_f|/3,2) + 0.6 min(|z_p|/3,2) > 1. A fused alarm opens a ``horizon``-event window of
    cutoff lifting (10-label reserve) and x3 propensity."""

    ID = "F55"
    DEFAULTS = {"fusion": "AND", "horizon": 100, "reserve": 10, "zthr": 3.0}
    SETTINGS = [{"fusion": "OR", "horizon": 100}, {"fusion": "weighted", "horizon": 100}]

    def __init__(self, *a):
        super().__init__(*a)
        self._z_init()
        self.zp, self.zf = 0.0, 0.0
        self.lf = self.lp = -(10**9)
        self.end, self.spent = -1, 0

    def on_release(self, ctx, fb):
        self.z_paid_add(fb)
        self.zp = self.z_paid()
        if abs(self.zp) > self.params["zthr"]:
            self.lp = fb.t_released

    def on_event(self, ctx):
        self.zf = self.z_free(ctx)
        if ctx.t < self.base or ctx.t < self.end:
            return
        p, z = self.params, self.params["zthr"]
        if abs(self.zf) > z:
            self.lf = ctx.t
        h = p["horizon"]
        fl, pl = ctx.t - self.lf < h, ctx.t - self.lp < h
        if p["fusion"] == "OR":
            fire = fl or pl
        elif p["fusion"] == "AND":
            fire = fl and pl
        else:
            fire = 0.4 * min(abs(self.zf) / z, 2) + 0.6 * min(abs(self.zp) / z, 2) > 1.0
        if fire:
            self.end, self.spent = ctx.t + h, 0

    def floor(self, ctx):
        if (
            ctx.t < self.end
            and ctx.closed
            and ctx.releasable
            and self.spent < self.params["reserve"]
        ):
            return Force("lift", reason=self.ID)
        return None

    def scale(self, ctx):
        return 3.0 if ctx.t < self.end and not ctx.closed else None

    def reserves(self, ctx):
        if ctx.t_close is None:
            return []
        return [Reserve(self.ID, int(self.params["reserve"]), lo=ctx.t_close)]

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.spent += 1


@register
class F56(_DepHist, _F):
    """Sentinel-to-rollback cascade. After the cutoff each releasable disagreement event is bought
    with probability 0.03 (sentinel, own stream, 15-label reserve). ``alert`` sentinel labels within
    200 events that favour the model NOT deployed at request time raise the alert: the next ``burst``
    eligible events are forced; for ``review`` events after the burst labels are released, if >= 3
    labels bought since the alert show the deployed model losing in > 2/3 of them, the deployment
    is rolled back (override_deploy) once."""

    ID = "F56"
    DEFAULTS = {"alert": 2, "burst": 10, "review": 50, "p_s": 0.03, "reserve": 15}
    SETTINGS = [{"alert": 2, "burst": 5, "review": 50}, {"alert": 3, "burst": 10, "review": 50}]

    def __init__(self, *a):
        super().__init__(*a)
        self._hist_init()
        self.sent, self.spent = set(), 0
        self.bad_t = deque()
        self.alert_t = None
        self.burst_left = 0
        self.post_bad = []  # (is_bad) of labels bought since the alert
        self.since = set()
        self.rollback = False

    def floor(self, ctx):
        if not ctx.closed or not ctx.releasable:
            return None
        if self.burst_left > 0:
            return Force("force", 1.0, self.ID + ":burst")
        if self.spent < self.params["reserve"] and self.rng.random() < self.params["p_s"]:
            return Force("force", float(self.params["p_s"]), self.ID + ":sentinel")
        return None

    def reserves(self, ctx):
        if ctx.t_close is None:
            return []
        return [Reserve(self.ID, int(self.params["reserve"]), lo=ctx.t_close)]

    def on_purchase(self, ctx, rec):
        if self.ID not in rec["by"]:
            if self.alert_t is not None:
                self.since.add(ctx.t)
            return
        self.spent += 1
        self.sent.add(ctx.t)
        if self.burst_left > 0:
            self.burst_left -= 1
            self.since.add(ctx.t)

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        bad = (fb.d > 0) != (self.dep_at(fb.t_requested) == 1)
        if fb.event_id in self.sent and bad:
            self.bad_t.append(fb.t_released)
            while self.bad_t and self.bad_t[0] < fb.t_released - 200:
                self.bad_t.popleft()
            if len(self.bad_t) >= self.params["alert"] and self.alert_t is None:
                self.alert_t, self.burst_left = fb.t_released, self.params["burst"]
                self.bad_t.clear()
        if self.alert_t is not None and fb.event_id in self.since:
            self.post_bad.append(int(bad))
            if len(self.post_bad) >= 3 and sum(self.post_bad) / len(self.post_bad) > 2 / 3:
                self.rollback = True
        if (
            self.alert_t is not None
            and fb.t_released > self.alert_t + ctx.delay + self.params["review"]
        ):
            self.alert_t, self.post_bad, self.since = None, [], set()  # review over, re-arm

    def override_deploy(self, ctx):
        if self.rollback:
            self.rollback = False
            self.alert_t, self.post_bad, self.since = None, [], set()
            return 1 - ctx.deployed
        return None


@register
class F57(_F):
    """Alarm-gated fast/slow evidence. Fast decayed counts (``fast_lambda``) run beside the parent's
    slow ones. A change warning (|mu_fast - mu_slow| > 2 se_slow, >= 6 labels) opens a
    ``duration``-event window; inside it the switch decision uses the fast posterior (parent's
    gamma-quantile payback > cs via override_deploy); outside it the parent's evidence decides."""

    ID = "F57"
    DEFAULTS = {"fast_lambda": 0.9, "duration": 100}
    SETTINGS = [{"fast_lambda": 0.8, "duration": 100}, {"fast_lambda": 0.9, "duration": 200}]

    def __init__(self, *a):
        super().__init__(*a)
        self.kf = self.nf = 0.0
        self.n_lab = 0
        self.end = -1

    def on_release(self, ctx, fb):
        if fb.d == 0:
            return
        lam = self.params["fast_lambda"]
        self.nf = lam * self.nf + 1.0
        self.kf = lam * self.kf + float(fb.d > 0)
        self.n_lab += 1
        if self.n_lab >= 6:
            mf, ms = (self.kf + 1) / (self.nf + 2), (ctx.k + 1) / (ctx.n + 2)
            se = math.sqrt(ms * (1 - ms) / (ctx.n + 2))
            if abs(mf - ms) > 2 * se:
                self.end = max(self.end, fb.t_released + self.params["duration"])

    def override_deploy(self, ctx):
        if ctx.t >= self.end or self.n_lab < 6:
            return None
        p = ctx.parent
        g = gain_q(
            self.kf + 1.0, self.nf - self.kf + 1.0, ctx.deployed, p.gamma, ctx.rate, ctx.T - ctx.t
        )
        return 1 - ctx.deployed if g > p.cs else None


@register
class F58(_IPW, _DepHist, _F):
    """Two-policy economic arbitration (see module docstring for the single-state caveat)."""

    ID = "F58"
    DEFAULTS = {"score_window": 100, "penalty": 1.0, "weight_cap": 10.0, "retry": 5}
    SETTINGS = [{"score_window": 30, "penalty": 1.0}, {"score_window": 100, "penalty": 3.0}]

    def __init__(self, *a):
        super().__init__(*a)
        self._hist_init()
        self._ipw_init(self.params["weight_cap"])
        self.sh = Shadow(self.ctx.parent)
        self.mode, self.t_mode, self.parent_until = "exp", 0, -1
        self.recs = deque(maxlen=int(self.params["score_window"]))
        self.audit = []  # (t, mode, score)

    def scale(self, ctx):
        self._ipw_scale(ctx)

    def on_purchase(self, ctx, rec):
        self._ipw_purchase(ctx, rec)

    def score(self, t_now):
        s, n = 0.0, 0
        for t_req, w, d in self.recs:
            if t_req < self.t_mode:
                continue
            de, dp = self.dep_at(t_req), self.sh.dep_at(t_req)
            if de != dp:
                s += w * d * (1 - 2 * dp)
                n += 1
        t0 = max(self.t_mode, self.recs[0][0]) if self.recs else self.t_mode
        sw_e = sum(1 for x in self.h_t[1:] if t0 <= x <= t_now)
        s -= (
            self.params["penalty"] * self.ctx.parent.cs * max(0, sw_e - self.sh.n_switch(t0, t_now))
        )
        return s, n

    def on_release(self, ctx, fb):
        w = self._ipw_w(fb.event_id)
        self.sh.update(fb)
        if fb.d != 0:
            self.recs.append((fb.t_requested, w, fb.d))
        if self.mode == "exp":
            s, n = self.score(fb.t_released)
            if n >= 3 and s < 0:
                self.mode = "parent"
                self.parent_until = (
                    fb.t_released + self.params["retry"] * self.params["score_window"]
                )
                self.audit.append((fb.t_released, "parent", s))

    def override_deploy(self, ctx):
        if self.mode == "parent" and ctx.t >= self.parent_until:
            self.mode, self.t_mode = "exp", ctx.t
            self.recs.clear()
            self.audit.append((ctx.t, "exp", 0.0))
        return self.sh.dep if self.mode == "parent" else None


@register
class F60(_F):
    """Multi-label short-rollout VOI. Value of a bundle of ``bundle`` labels (all landing at t+delay,
    given the pending ones) over a ``horizon``-event hazard-discounted rollout; when the bundle VOI
    exceeds bundle x (budget-shadowed) label price, buy now and commit to buying the next
    bundle-1 disagreement events as well (a packet); no new bundle test while a packet is open."""

    ID = "F60"
    DEFAULTS = {"bundle": 3, "horizon": 200, "hazard": 0.002}
    SETTINGS = [{"bundle": 2, "horizon": 100}, {"bundle": 4, "horizon": 200}]

    def __init__(self, *a):
        super().__init__(*a)
        self.post = Post(self.params["hazard"])
        self.left = 0

    def on_release(self, ctx, fb):
        self.post.add(fb)

    def floor(self, ctx):
        if ctx.closed or not ctx.releasable or not pace_ok(ctx):
            return None
        if self.left > 0:
            return Force("force", 1.0, self.ID + ":packet")
        b, h = self.params["bundle"], self.params["hazard"]
        H = min(ctx.T - ctx.t - ctx.delay, self.params["horizon"])
        a, bb = self.post.eff(ctx.t)
        v = voi(a, bb, ctx.pending, b, ctx.deployed, ctx.rate, H * surv(H, h), ctx.parent.cs)
        if v > b * price(ctx):
            return Force("force", 1.0, self.ID)
        return None

    def on_purchase(self, ctx, rec):
        if self.ID in rec["by"]:
            self.left = self.left - 1 if self.left > 0 else self.params["bundle"] - 1


# ---------------------------------------------------------------------------------------------
# F59: learned acquisition controller (trained on development episodes only)
# ---------------------------------------------------------------------------------------------
FEATS = ["t_frac", "rem_frac", "pend", "conf", "n20", "gain_lo", "gain_hi", "dep", "age", "rate"]


def f59_features(ctx, qc=None):
    """Observable features; ``qc`` caches the parent's quantile function by (k, n, level)."""
    par, cs = ctx.parent, ctx.parent.cs
    g = par.gamma

    def gain(lev):
        key = (ctx.k, ctx.n, lev)
        if qc is not None and key in qc:
            p = qc[key]
        else:
            p = par._q(lev if ctx.deployed == 0 else 1.0 - lev)
            if qc is not None:
                qc[key] = p
        a = (2 * p - 1) if ctx.deployed == 0 else (1 - 2 * p)
        return a * ctx.rate * (ctx.T - ctx.t)

    mu = (ctx.k + 1.0) / (ctx.n + 2.0)

    def clip(x):
        return max(-3.0, min(3.0, x))

    age = ctx.t - max(ctx.last_release_t, 0)
    return [
        ctx.t / ctx.T, ctx.remaining / ctx.B, ctx.pending / 10.0, abs(2 * mu - 1),
        min(1.0, ctx.n / 20.0), clip(gain(g) / cs), clip(gain(1 - g) / cs),
        float(ctx.deployed), min(1.0, age / 200.0), ctx.rate,
    ]  # fmt: skip


def _tree_pred(node, x):
    while "f" in node:
        node = node["l"] if x[node["f"]] <= node["thr"] else node["r"]
    return node["p"]


def _fit_tree(X, y, depth, min_leaf=30):
    import numpy as np

    def gini(v):
        p = v.mean() if len(v) else 0.0
        return 2 * p * (1 - p) * len(v)

    def grow(idx, d):
        node = {"p": float(y[idx].mean()) if len(idx) else 0.0, "n": len(idx)}
        if d == 0 or len(idx) < 2 * min_leaf or y[idx].min() == y[idx].max():
            return node
        best = (gini(y[idx]), None)
        for f in range(X.shape[1]):
            for thr in np.unique(np.quantile(X[idx, f], [0.2, 0.4, 0.6, 0.8])):
                lm = X[idx, f] <= thr
                if lm.sum() < min_leaf or (~lm).sum() < min_leaf:
                    continue
                g = gini(y[idx][lm]) + gini(y[idx][~lm])
                if g < best[0] - 1e-9:
                    best = (g, (f, float(thr), idx[lm], idx[~lm]))
        if best[1] is None:
            return node
        f, thr, li, ri = best[1]
        return {"f": f, "thr": thr, "l": grow(li, d - 1), "r": grow(ri, d - 1), "p": node["p"]}

    return grow(np.arange(len(y)), depth)


def _fit_logistic(X, y, l2=1.0, iters=25):
    import numpy as np

    mu, sd = X.mean(0), X.std(0) + 1e-9
    Z = np.c_[np.ones(len(X)), (X - mu) / sd]
    w = np.zeros(Z.shape[1])
    R = l2 * np.eye(Z.shape[1])
    R[0, 0] = 0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-Z @ w))
        H = Z.T @ (Z * (p * (1 - p))[:, None]) + R
        w = w + np.linalg.solve(H, Z.T @ (y - p) - R @ w)
    return {"mu": mu.tolist(), "sd": sd.tolist(), "w": w.tolist()}


def _logit_pred(m, x):
    z = m["w"][0] + sum(
        wi * (xi - mi) / si for wi, xi, mi, si in zip(m["w"][1:], x, m["mu"], m["sd"])
    )
    return 1 / (1 + math.exp(-max(-30.0, min(30.0, z))))


# Hand-specified fallback used only if f59_params.json is absent: a logistic over observable
# features whose coefficients were chosen on a constructed toy stream (see tests), never on the
# nine datasets: label value is higher when the posterior is undecided (low conf), evidence is thin,
# the gain is near the switch threshold, little is pending and budget remains.
_FALLBACK = {"ref": 0.03,
             "logistic": {"mu": [0.0] * 10, "sd": [1.0] * 10,
                          "w": [-3.5, -0.5, 0.5, -0.5, -1.5, -0.5, 0.5, 0.5, 0.0, 0.3, 0.0]}}  # fmt: skip


def load_f59():
    try:
        return json.loads(F59_JSON.read_text(encoding="utf-8"))
    except OSError:
        return _FALLBACK


@register
class F59(_F):
    """Lightweight learned acquisition controller. A frozen model (``tree`` of ``depth`` or
    ``logistic``, parameters in f59_params.json, fitted on EVEN development episodes only, see
    ``train_f59``) maps observable state features to P(a purchase here is followed by a deployment
    change within delay+100 events). Output scales the parent's propensity:
    clip(score / ref, 0.5, 3), ref = training base rate (cutoff and pacing of the parent remain)."""

    ID = "F59"
    DEFAULTS = {"model": "tree", "depth": 2}
    SETTINGS = [{"model": "tree", "depth": 2}, {"model": "logistic", "depth": 3}]
    REC: list | None = None  # training recorder: list of dict rows (class level, off by default)
    _SW: list = []

    def __init__(self, *a):
        super().__init__(*a)
        self.par = load_f59() if self.params["model"] != "off" else None
        self._qc: dict = {}

    def _score(self, x):
        m = self.params["model"]
        if m == "logistic":
            return _logit_pred(self.par["logistic"], x)
        node = self.par.get(f"tree{int(self.params['depth'])}") or self.par.get("tree2")
        return _tree_pred(node, x) if node else self.par["ref"]

    def scale(self, ctx):
        if self.par is None:
            return None
        s = self._score(f59_features(ctx, self._qc))
        return max(0.5, min(3.0, s / max(self.par["ref"], 1e-6)))

    def on_purchase(self, ctx, rec):
        if F59.REC is not None:
            F59.REC.append({"t": ctx.t, "x": f59_features(ctx)})

    def on_deploy_change(self, ctx, frm, to):
        if F59.REC is not None:
            F59._SW.append(ctx.t)


def train_f59(out=F59_JSON, n_eps=6, seed=0, workers=1):
    """Fit F59 on DEVELOPMENT (even) episodes of the nine sealed datasets, parent policy as behaviour.

    Behaviour: the frozen parent (arm R + cutoff 1100) with F59 in recorder mode (model 'off': scale
    is 1, so it does not change the policy). Sample = a bought disagreement event; target y = 1 if
    the deployment changed within (t, t + delay + 100]. Features are `FEATS` (observable only).
    Only even episode indices are read; odd episodes are never touched here."""
    import compositor as comp
    import numpy as np
    import trace_run as tr

    spec = {"name": "f59_rec", "modules": [{"id": "F59", "params": {"model": "off"}}]}
    comp.register_specs([spec])
    X, Y, meta = [], [], []
    for ds, (p, delay, sb) in tr.sealed_paths().items():
        z = np.load(p)
        n = z["l0"].shape[0]
        even = [e for e in range(n) if e % 2 == 0]
        sel = even[:: max(1, len(even) // n_eps)][:n_eps]
        for ep in sel:
            losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
            F59.REC, F59._SW = [], []
            tr.run_policies(["f59_rec"], losses, delay, ep, seed, sb, ds, 200)
            sw = np.array(F59._SW)
            for r in F59.REC:
                X.append(r["x"])
                Y.append(float(((sw > r["t"]) & (sw <= r["t"] + delay + 100)).any()))
            meta.append([ds, int(ep)])
    F59.REC = None
    X, Y = np.array(X), np.array(Y)
    par = {"features": FEATS, "ref": float(Y.mean()), "n_samples": len(Y),
           "logistic": _fit_logistic(X, Y), "tree2": _fit_tree(X, Y, 2), "tree3": _fit_tree(X, Y, 3),
           "episodes_used": meta,
           "procedure": "behaviour policy = frozen parent (arm R, cutoff 1100) with F59 recorder; "
                        "even development episodes only; sample = purchase; y = deployment change "
                        "within delay+100 events; logistic = ridge IRLS on standardised features; "
                        "tree = greedy gini, min leaf 30."}  # fmt: skip
    Path(out).write_text(json.dumps(par, indent=1), encoding="utf-8")
    return par
