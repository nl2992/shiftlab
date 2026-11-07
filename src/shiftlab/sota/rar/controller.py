"""RAR state machine (Algorithms 1-2 of arXiv:2611.02251v1), PAPER_RECONSTRUCTION.

Time model.  ``step(t, x_t, released)`` is the only entry point.  ``released`` is the list of
``(i, y_i)`` pairs whose label becomes available at time t (the harness enforces release = request
time + tau).  The controller never receives y_t before release; it raises ``LeakageError`` if a label
is handed over before the label frontier ``i <= t - tau`` or for an un-requested instance.
Label-dependent quantities (detector, accuracies, canary tallies) are updated only on release; live
quantities (q_t, hold and canary clocks, routing) run at t.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .components import AllLabelsPolicy, HookContext, ThetaLGate, ThetaRGate
from .config import MODES, RARConfig

SERVING, CANARY1, CANARY2, HOLD_SOFT, HOLD_HARD = (
    "Serving",
    "Canary-1",
    "Canary-2",
    "Alert-Hold-Soft",
    "Alert-Hold-Hard",
)
STATES = (SERVING, CANARY1, CANARY2, HOLD_SOFT, HOLD_HARD)


class LeakageError(RuntimeError):
    pass


@dataclass
class StepOutput:
    pred: int
    request_label: bool
    state: str
    routed_to_new: bool


class RARController:
    def __init__(
        self,
        cfg: RARConfig,
        factory,
        detector,
        *,
        quality=None,
        label_policy=None,
        gate2=None,
        gate3=None,
        strict=True,
    ):
        self.cfg = cfg
        self.m = MODES[cfg.mode]
        self.factory, self.det = factory, detector
        self.use_prefilter = self.m["canary"] or self.m["alert"]
        self.quality = quality if (quality is not None and self.use_prefilter) else None
        self.label_policy = label_policy or AllLabelsPolicy()
        self.gate2, self.gate3 = gate2 or ThetaLGate(), gate3 or ThetaRGate()
        self.strict = strict
        self.rng = np.random.default_rng(cfg.seed)
        self.state = SERVING
        self.model = None
        self.old = None
        self.new = None
        # per-instance records
        self.X = []
        self.served = []
        self.p_old = []
        self.p_new = []
        self.routed = []
        self.stage = []
        self.episode = []
        self.requested = []
        self.labeled = []
        self.y = []
        self.corrupt = []
        self.correct = []
        self.counts = {"retrain": 0, "alert": 0, "rollback": 0, "query": 0}
        self.log = []
        self.n_released = 0
        self.n_requested = 0
        # detector / flag
        self.birth_t = 0
        self.det_updates = 0
        self.flag = None
        self.last_t_d = None
        self.detections = []
        self.alerted = set()
        self.last_a3 = -(10**9)
        # canary
        self.ep = 0
        self.c = None
        # holds
        self.hold = None
        self.corrupt_run = 0
        self.clean_run = 0
        self.r2_armed = True
        self.t = -1

    # ------------------------------------------------------------------ setup
    def start(self, Xw, yw):
        """Train M_old on the warm-up prefix (historic, offline)."""
        self.model = self.factory.fit(np.asarray(Xw), np.asarray(yw))
        if self.quality is not None:
            self.quality.fit(Xw)
        self._log(-1, "init", model="M_old", n_warmup=len(yw))

    # ------------------------------------------------------------------ logging
    def _log(self, t, event, **detail):
        self.log.append(dict(t=int(t), event=event, state=self.state, **detail))

    def _set_state(self, t, new, **d):
        self._log(t, "transition", to=new, **d)
        self.state = new

    def _act(self, t, action, **d):
        """Single place where an action is performed AND its cost counter incremented."""
        self.counts[action] += 1
        self._log(t, "action:" + action, **d)

    def ctx(self, t, routed=False, win=0, acc_pre=None, acc_cur=None) -> HookContext:
        return HookContext(
            t=t,
            state=self.state,
            tau=self.cfg.tau,
            cfg=self.cfg,
            n_labels_released=self.n_released,
            n_pending=self.n_requested - self.n_released,
            routed_to_new=routed,
            canary_stage={CANARY1: 1, CANARY2: 2}.get(self.state, 0),
            labeled_in_window=win,
            t_hat_d=None if self.flag is None else self.flag["t_d"],
            acc_pre=acc_pre,
            acc_cur=acc_cur,
            rho=self.cfg.rho,
        )

    # ------------------------------------------------------------------ accuracy helpers
    def _acc_window(self, lo, hi):
        """Mean served-correctness over labelled, incumbent-served instances in [lo, hi]."""
        lo = max(lo, 0)
        hi = min(hi, len(self.labeled) - 1)
        if hi < lo:
            return None
        v = [self.correct[i] for i in range(lo, hi + 1) if self.labeled[i] and self.stage[i] == 0]
        return float(np.mean(v)) if v else None

    def _acc_cur(self, t):
        f = t - self.cfg.tau
        return self._acc_window(f - self.cfg.W_cur + 1, f)

    def _acc_pre(self, t_d):
        e = t_d - self.cfg.g
        return self._acc_window(e - self.cfg.W_ref + 1, e)

    def _acc_ref_recent(self, t):
        e = t - self.cfg.tau - self.cfg.W_cur
        return self._acc_window(e - self.cfg.W_ref + 1, e)

    def _labeled_in_window(self, t_d, t):
        hi = min(t - self.cfg.tau, t_d + self.cfg.W_train - 1)
        if hi < t_d:
            return 0
        return int(sum(self.labeled[t_d : hi + 1]))

    # ------------------------------------------------------------------ main entry
    def step(self, t, x, released=()) -> StepOutput:
        cfg = self.cfg
        if t != len(self.X):
            raise ValueError("steps must be consecutive from 0")
        self.t = t
        x = np.asarray(x, float)
        self.X.append(x)
        for lst, v in (
            (self.served, -1),
            (self.p_old, -1),
            (self.p_new, -1),
            (self.routed, False),
            (self.stage, 0),
            (self.episode, -1),
            (self.requested, False),
            (self.labeled, False),
            (self.y, -1),
            (self.correct, 0.0),
        ):
            lst.append(v)
        is_corrupt = bool(self.quality.corrupt(x)) if self.quality is not None else False
        self.corrupt.append(is_corrupt)
        if is_corrupt:
            self.corrupt_run += 1
            self.clean_run = 0
        else:
            self.corrupt_run = 0
            self.clean_run += 1
            self.r2_armed = True
        for i, yi in released:  # 1. labels at the frontier
            self._observe(t, i, yi)
        self._live(t)  # 2. live clocks
        if self.state == SERVING:  # 3. decisions
            self._decide(t)
        pred, routed = self._serve(t, x)  # 4. serve
        req = bool(self.label_policy.request(self.ctx(t, routed=routed)))
        self.requested[t] = req
        if req:
            self.n_requested += 1
            if cfg.c_query:
                self.counts["query"] += 1
        return StepOutput(pred, req, self.state, routed)

    # ------------------------------------------------------------------ serving
    def _serve(self, t, x):
        cfg = self.cfg
        routed = False
        if self.state in (CANARY1, CANARY2):
            po = int(self.old.predict(x))
            pn = -1
            if self.state == CANARY1:
                c = self.c
                k = t - c["start"]
                routed = math.floor((k + 1) * cfg.p1 + c["phi"]) > math.floor(k * cfg.p1 + c["phi"])
                if routed:
                    pn = int(self.new.predict(x))
                pred = pn if routed else po
                self.stage[t] = 1
            else:
                pn = int(self.new.predict(x))
                pred = pn
                routed = True
                self.stage[t] = 2
            self.episode[t] = self.ep
        else:
            po = int(self.model.predict(x))
            pn = -1
            pred = po
            self.stage[t] = 0
        self.served[t] = pred
        self.p_old[t] = po
        self.p_new[t] = pn
        self.routed[t] = routed
        return pred, routed

    # ------------------------------------------------------------------ label release
    def _observe(self, t, i, yi):
        if self.strict:
            if i > t - self.cfg.tau or i < 0:
                raise LeakageError(
                    f"label {i} released at t={t} before frontier t-tau={t - self.cfg.tau}"
                )
            if not self.requested[i] or self.labeled[i]:
                raise LeakageError(f"label {i} released without request or twice")
        self.labeled[i] = True
        self.y[i] = int(yi)
        self.n_released += 1
        self.correct[i] = float(self.served[i] == yi)
        st = self.stage[i]
        if st in (1, 2):
            c = self.c
            if (
                c is not None
                and self.episode[i] == c["ep"]
                and st == c["stage"]
                and (st == 2 or self.routed[i])
            ):
                c["n"] += 1
                nw = float(self.p_new[i] == yi)
                od = float(self.p_old[i] == yi)
                c["new_c"] += nw
                c["old_c"] += od
                c["n01"] += int(nw == 1 and od == 0)
                c["n10"] += int(nw == 0 and od == 1)
                c["cls"][int(yi)] = c["cls"].get(int(yi), 0) + 1
            return
        # incumbent-served instance: detector update (quarantined / guard-gap instances skipped)
        if not self.corrupt[i] and i >= self.birth_t + self.cfg.g:
            self.det_updates += 1
            fired = self.det.update(int(self.served[i] != yi))
            if fired and self.det_updates >= self.cfg.detector_warmup:
                t_d = max(i - self.det.width + 1, self.birth_t)
                self.detections.append(i)
                if self.flag is None:
                    self.flag = {"t_d": int(t_d), "raised": int(t), "evaluated": False}
                    self.last_t_d = int(t_d)
                    self._log(t, "detector_flag", frontier=i, t_hat_d=int(t_d))

    # ------------------------------------------------------------------ live clocks
    def _live(self, t):
        cfg = self.cfg
        if self.m["holds"] and self.corrupt_run >= cfg.r2_run and self.r2_armed:
            self.r2_armed = False
            if self.state in (CANARY1, CANARY2):
                self._rollback(t, "R2")
                return
            if self.state == SERVING and cfg.r2_hold_in_serving:
                self._enter_hold(t, HOLD_HARD, "R2_serving")
                return
            if self.state == HOLD_SOFT:
                self._enter_hold(t, HOLD_HARD, "R2_in_soft_hold")
                return
        if self.state in (CANARY1, CANARY2):
            self._canary_progress(t)
            return
        if self.state in (HOLD_SOFT, HOLD_HARD):
            self._hold_progress(t)
        if self.flag is not None and t - self.flag["t_d"] > cfg.flag_ttl:
            self._log(t, "flag_expired", t_hat_d=self.flag["t_d"])
            self.flag = None

    # ------------------------------------------------------------------ serving-state decisions
    def _train_window_indices(self, t_d, t):
        hi = min(t - self.cfg.tau, t_d + self.cfg.W_train - 1)
        return [i for i in range(t_d, hi + 1) if self.labeled[i]]

    def _last_labeled_indices(self, t, n):
        out = []
        for i in range(t - self.cfg.tau, -1, -1):
            if self.labeled[i]:
                out.append(i)
                if len(out) >= n:
                    break
        return out[::-1]

    def _decide(self, t):
        cfg, m = self.cfg, self.m
        if m["periodic"]:
            if t > 0 and t % cfg.W_train == 0:
                self._do_retrain(
                    t, self._last_labeled_indices(t, cfg.W_train), anchor=None, reason="periodic"
                )
            return
        if self.flag is None:
            if m["alert"] and m["gates"]:
                self._maybe_a3(t)
            return
        fl = self.flag
        t_d = fl["t_d"]
        a_pre, a_cur = self._acc_pre(t_d), self._acc_cur(t)
        if not m["gates"]:
            if fl["evaluated"]:
                return
            fl["evaluated"] = True
            if not m["retrain"]:
                return
            if m["cost_gate"]:
                d_hat = 0.0 if (a_pre is None or a_cur is None) else max(0.0, a_pre - a_cur)
                H = float(np.mean(np.diff(self.detections))) if len(self.detections) >= 2 else 0.0
                H = max(H, float(cfg.W_train))
                ok = d_hat * H >= cfg.rho
                self._log(t, "cost_gate", d_hat=d_hat, H=H, rho=cfg.rho, passes=ok)
                if not ok:
                    self.flag = None
                    return
            self._do_retrain(
                t, self._last_labeled_indices(t, cfg.W_train), anchor=None, reason="binary_flag"
            )
            return
        win = self._labeled_in_window(t_d, t)
        c = self.ctx(t, win=win, acc_pre=a_pre, acc_cur=a_cur)
        g2 = bool(self.gate2.passes(c))
        g3 = bool(self.gate3.passes(c)) if g2 else False
        if g2 and g3:
            if not m["retrain"]:
                self._alert(t, "A_blocked", fl)
                return
            self._do_retrain(t, self._train_window_indices(t_d, t), anchor=t_d, reason="gates_pass")
            return
        if m["alert"]:
            self._alert(t, "A1" if not g2 else "A2", fl)

    def _alert(self, t, kind, fl):
        key = (fl["t_d"], kind)
        if key in self.alerted:
            return
        self.alerted.add(key)
        self._act(t, "alert", kind=kind, t_hat_d=fl["t_d"])

    def _maybe_a3(self, t):
        cfg = self.cfg
        if t - self.last_a3 < cfg.W_mon:
            return
        cur, ref = self._acc_cur(t), self._acc_ref_recent(t)
        if cur is not None and ref is not None and ref - cur >= cfg.soft_thr:
            self.last_a3 = t
            self._act(t, "alert", kind="A3", drop=ref - cur)

    # ------------------------------------------------------------------ retrain / canary
    def _do_retrain(self, t, idx, anchor, reason):
        cfg = self.cfg
        if len(idx) < cfg.min_train:
            self._log(t, "retrain_skipped", reason="too_few_labels", n=len(idx))
            self.flag = None
            return
        Xtr = np.array([self.X[i] for i in idx])
        ytr = np.array([self.y[i] for i in idx])
        new = self.factory.fit(Xtr, ytr)
        self._act(t, "retrain", reason=reason, n_train=len(idx), anchor=anchor)
        self.flag = None
        if not self.m["canary"]:
            self.model = new
            self._rebirth(t, "immediate_deploy")
            return
        self.old, self.new = self.model, new
        self.ep += 1
        self._start_stage(t, 1)
        self._set_state(t, CANARY1, episode=self.ep)

    def _start_stage(self, t, stage):
        cfg = self.cfg
        nominal = (cfg.tau + math.ceil(cfg.W1 / cfg.p1)) if stage == 1 else (cfg.tau + cfg.W2)
        self.c = {
            "ep": self.ep,
            "stage": stage,
            "start": t,
            "n": 0,
            "new_c": 0.0,
            "old_c": 0.0,
            "n01": 0,
            "n10": 0,
            "cls": {},
            "phi": float(self.rng.random()),
            "timeout": int(cfg.kappa_canary_mult * nominal),
            "done_interim": set(),
        }

    def _canary_progress(self, t):
        cfg, c = self.cfg, self.c
        W = cfg.W1 if c["stage"] == 1 else cfg.W2
        if t - c["start"] > c["timeout"]:
            self._rollback(t, "timeout")
            return
        if c["n"] == 0:
            return
        a_new = c["new_c"] / c["n"]
        a_old = c["old_c"] / c["n"]
        for f in cfg.interim_fracs:
            if f not in c["done_interim"] and f * W <= c["n"] < W:
                c["done_interim"].add(f)
                if a_new < a_old - cfg.interim_margin_mult * cfg.delta:
                    self._rollback(t, "R1_interim")
                    return
        if c["n"] < W:
            return
        maj = max(c["cls"].values()) / c["n"]
        if a_new < maj - 1e-12 and a_new < a_old:  # R3 sanity vs majority-class predictor
            self._rollback(t, "R3")
            return
        if a_new < a_old - cfg.delta:  # R1 margin screen
            self._rollback(t, "R1")
            return
        if c["stage"] == 1:
            self._log(t, "stage1_pass", a_new=a_new, a_old=a_old, n=c["n"])
            self._start_stage(t, 2)
            self._set_state(t, CANARY2, episode=self.ep)
            return
        d = c["n01"] + c["n10"]
        z = (c["n01"] - c["n10"]) / math.sqrt(d) if d > 0 else 0.0
        if z >= cfg.z_commit - 1e-12:
            self._log(t, "commit", z=z, a_new=a_new, a_old=a_old)
            self.model, self.old, self.new, self.c = self.new, None, None, None
            self._rebirth(t, "commit")
            self._set_state(t, SERVING)
        else:
            self._log(t, "dead_band_discard", z=z, a_new=a_new, a_old=a_old)
            self.model = self.old
            self.old = self.new = self.c = None
            self._rebirth(t, "dead_band")
            self._set_state(t, SERVING)

    def _rebirth(self, t, why):
        self.birth_t = t
        self.det.reset()
        self.det_updates = 0
        self.flag = None
        self._log(t, "model_birth", why=why)

    # ------------------------------------------------------------------ rollback / holds (Algorithm 2)
    def _rollback(self, t, cause):
        self._act(t, "rollback", cause=cause)
        self.model = self.old
        self.old = self.new = self.c = None
        self._rebirth(t, "rollback_" + cause)
        if cause == "timeout" and self.cfg.alert_on_timeout and self.m["alert"]:
            self._act(t, "alert", kind="canary_timeout")
        self._enter_hold(t, HOLD_HARD if cause == "R2" else HOLD_SOFT, cause)

    def _enter_hold(self, t, kind, cause):
        dur = self.cfg.kappa_long if kind == HOLD_HARD else self.cfg.kappa_short
        self.hold = {"start": t, "left": dur, "kind": kind, "cause": cause}
        self.flag = None
        self._set_state(t, kind, cause=cause, duration=dur)

    def _hold_progress(self, t):
        cfg, h = self.cfg, self.hold
        h["left"] -= 1
        if self.state == HOLD_HARD:
            if h["left"] <= 0 or self.clean_run >= cfg.m_clear:
                self._log(t, "hold_exit", reason="expiry" if h["left"] <= 0 else "clean_run")
                self._set_state(t, SERVING)
                self.hold = None
            return
        if h["left"] <= 0:
            self._log(t, "hold_exit", reason="expiry")
            self._set_state(t, SERVING)
            self.hold = None
            return
        if (
            t - h["start"] >= cfg.kappa_min
            and self.corrupt_run == 0
            and self.last_t_d is not None
            and self.m["gates"]
            and self.m["retrain"]
        ):
            anchor = max(self.last_t_d, t - cfg.tau - cfg.W_train + 1)
            cur, ref = self._acc_cur(t), self._acc_ref_recent(t)
            c = self.ctx(t, win=self._labeled_in_window(anchor, t), acc_pre=ref, acc_cur=cur)
            if (
                cur is not None
                and ref is not None
                and cur < ref - cfg.delta_crit_mult * cfg.theta_R
                and self.gate2.passes(c)
            ):
                self._log(t, "emergency_override", cur=cur, ref=ref, anchor=anchor)
                self._set_state(t, SERVING)
                self.hold = None
                self._do_retrain(
                    t,
                    self._train_window_indices(anchor, t),
                    anchor=anchor,
                    reason="emergency_override",
                )

    # ------------------------------------------------------------------ accounting
    def objective(self, n_correct: float) -> float:
        """U = sum 1{yhat=y} - C_r N_r - C_a N_a - C_b N_b (Eq. 3); each cost charged once per action."""
        cfg = self.cfg
        return (
            n_correct
            - cfg.C_r * self.counts["retrain"]
            - cfg.C_a * self.counts["alert"]
            - cfg.C_b * self.counts["rollback"]
            - cfg.c_query * self.counts["query"]
        )
