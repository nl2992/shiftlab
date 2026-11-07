"""COMMON_CONTRACT_PORT of RAR (Retrain / Alert / Rollback, arXiv:2611.02251v1) and of its Cost-Aware Binary comparator.

Source of the logic: ``src/shiftlab/sota/rar/`` (PAPER_RECONSTRUCTION; native Suite A semantics live there). This module
re-expresses the RAR state machine as a contract policy that reads ONLY ``ObservableState``. Claimed null: 'none'
(RAR runs no hypothesis test at its gates; the canary margin screen and the z>=1 commit rule are operational screens, see
docs/d2a_rar/baselines/RAR.md and registry/null_assumptions.yaml entries rar_gates / rar_canary_rollback).
Do not score it on conditional- or marginal-null false promotions.

Mapping (native -> contract) and every deviation
------------------------------------------------
* Models: incumbent = model 0. RAR's retrained model M_new = model 2 (``retrain`` action). Model 1 (candidate) is never used.
* Gate 1 (detector): ADWIN (river, delta 0.002) on the SERVED-model loss of released labels from phase-0 rounds (not
  canary rounds), fed in label_round order after a guard gap ``g`` and ``detector_warmup`` updates since the last model birth.
  Onset t_hat_d = label_round of the oldest element in the ADWIN window. Labels may arrive out of order and sparsely
  (requested subset): the detector index is "labels fed", not rounds. The contract's unlabelled monitor signal ``state.x`` is
  not used (RAR's detector is label-driven). Native RAR also has a corruption pre-filter q_t / rollback cause R2: the contract
  stream has no corrupt-feature channel, so R2 and Alert-Hold-Hard are NOT mapped (soft holds only).
* Flag lifetime: tau_hat + W_train rounds counted from the RAISE time (native: from t_hat_d), because at contract scale
  the ADWIN window width can exceed W_train and a t_hat_d-based lifetime would expire the flag on arrival.
* Gate 2 (label fraction) and Gate 3 (accuracy drop): ``GateRule`` objects from ``shiftlab.sota.rar.components`` (the very
  same ThetaLGate / ThetaRGate classes as the native code). Hook context numerators come from released labels only
  (``state.H``), never truth. A_pre = served accuracy over [t_hat_d-g-W_ref+1, t_hat_d-g]; A_cur = over the last W_cur rounds
  ending at t - tau_hat, tau_hat = median observed release delay (observable). A window with < ``min_window_labels`` labels
  yields None (native has no minimum; needed because requests may be sparse). Swap ``gate2`` / ``gate3`` to replace ONLY
  the gated decision.
* Label requests: ``LabelRequestPolicy`` hook (default AllLabelsPolicy = RAR's "labels eventually arrive", here: request
  every round while label budget remains). Under a finite label cap this exhausts the budget early; that is native behaviour,
  not a bug, and it is the component a new label-request policy replaces. No propensity is declared (deterministic rule).
* Alerts: A1 (gate 1 pass, gate 2 fail), A2 (gates 1-2 pass, gate 3 fail), A3 (soft anomaly, no flag, rate-limited by W_mon),
  A_blocked (gates pass but a retrain is impossible: replaceable slot taken or cap reached), canary timeout -> ``alert``.
  De-duplicated per (t_hat_d, kind); at most one alert emitted per round (queued; the contract refuses a duplicate kind per
  round). c_a is the contract price.
* Retrain: ``retrain`` action (c_r). The contract trains on its own window W_train = ``clocks.w_train``; native "train on the
  labelled rows of the anchored window" is realised by the simulator's retrain-quality model (BENCHMARK_CONTRACT 4a).
* Staged canary: requires ``ClockSpec.deploy_on_complete=False`` (use ``canary_clocks``). Stage 1 = ``route(RETRAINED, p1)``;
  it ends after ``W1`` released routed labels. Stage 2 = ``switch(RETRAINED)`` (full traffic, old model shadow-scored when
  ``obs_mode='shadow'``) for ``W2`` released labels. Commit iff z=(n01-n10)/sqrt(n01+n10) >= z_commit on paired discordant
  pairs, else revert. If ``deploy_on_complete=True`` the retrained model is already in force at completion: stage 1 is
  skipped (canary_degraded) and only the stage-2 verification and ``rollback`` remain.
  In ``obs_mode='deployed'`` the old model's loss on routed rounds is not identifiable: the paired z-test is replaced by
  "commit iff A_new >= A_old" with A_old = pre-canary accuracy (logged as ``unpaired``).
* Rollback causes: R1 margin screen A_new < A_old - delta (interim checkpoint at 50% of the stage with margin 2 delta);
  R3 "worse than majority class" becomes "A_new < 0.5 and A_new < A_old" (contract losses are 0/1 without class identity);
  timeout = 2x nominal stage duration (+ alert). Causes live in the policy ``log``; the audit only sees ``rollback`` /
  ``route``-clearing.
* Costs: contract prices apply. DEVIATIONS: (i) a failed STAGE 1 only clears the route (free; native charges C_b);
  (ii) committing a successful canary costs c_s (native: none; the contract charges every model change); (iii) a
  stage-2 failure / dead-band revert is a ``rollback`` (c_b; native dead-band revert is free, other stage-2 failures charge C_b).
* Holds: Alert-Hold-Soft (kappa_short rounds) after any abort/rollback; retrains blocked while held; emergency override after
  kappa_min if A_cur < A_ref - 2 theta_R and Gate 2 passes (native). Rounds are contract rounds, constants are contract-scale
  CHOICES (not tuned; see ``CONTRACT_DEFAULTS``).
* Single replaceable slot: the contract has one retrained-model id. After a COMMIT the retrained model is in force, so a
  further native retrain would replace it in place and cannot be canaried; the port blocks further retrains until a
  rollback restores the incumbent (A_blocked alert). Native RAR can repeat retrain cycles indefinitely.
* No hidden state: the policy never touches ``Stream`` / ``EvaluatorTruth``; ``PendingView.value`` is never read.

Cost-Aware Binary (paper's cost-aware comparator): ADWIN flag -> retrain iff max(0, A_pre - A_cur) * H_hat >= cost, with
H_hat = mean inter-detection interval so far floored at W_train, evaluated once per flag; cost = c_r (+ c_s when the
retrained model must be switched in explicitly). No canary / rollback / alerts. ``BinaryAdapter`` is the same policy
with the economic test disabled (retrain on every flag).
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from shiftlab.sota.rar.components import (
    ADWINDetector,
    AllLabelsPolicy,
    GateRule,
    HookContext,
    LabelRequestPolicy,
    ThetaLGate,
    ThetaRGate,
)
from shiftlab.sota.rar.config import RARConfig

from .policies import BasePolicy
from .types import INCUMBENT, RETRAINED, Action, ClockSpec, EnvSpec, ObservableState

# Contract-scale choices for constants the native config expresses in ~45k-instance units.
# NOT tuned on any stream; every value is a reconstruction choice (native values in sota/rar/config.py).
CONTRACT_DEFAULTS: dict[str, Any] = {
    "tau": 10,  # initial delay guess; replaced by the median observed delay
    "W_ref": 100,
    "W_cur": 40,
    "g": 10,
    "detector_warmup": 15,
    "p1": 0.2,
    "W1": 20,
    "W2": 40,
    "kappa_short": 150,
    "kappa_min": 50,
    "W_mon": 100,
    "soft_thr": 0.10,  # native 0.03; contract windows of ~40 labels have s.e. ~0.07
}

SERVING, RETRAINING, CANARY1, SWITCHING, CANARY2, HOLD = (
    "SERVING",
    "RETRAINING",
    "CANARY1",
    "SWITCHING",
    "CANARY2",
    "HOLD_SOFT",
)


def canary_clocks(**kw) -> ClockSpec:
    """ClockSpec with deploy_on_complete=False, required for RAR's stage-1 canary route."""
    return ClockSpec(deploy_on_complete=False, **kw)


class _MonitorBase(BasePolicy):
    """Label ingestion, Gate-1 detector, accuracy windows and the label-request hook (shared by RAR and Binary)."""

    def __init__(
        self,
        *,
        label_policy: LabelRequestPolicy | None = None,
        detector_factory=ADWINDetector,
        cfg_overrides: dict[str, Any] | None = None,
        min_window_labels: int = 5,
    ) -> None:
        self.label_policy = label_policy or AllLabelsPolicy()
        self.detector_factory = detector_factory
        self.cfg_overrides = dict(cfg_overrides or {})
        self.min_window_labels = min_window_labels

    # ------------------------------------------------------------------ setup
    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        base = dict(CONTRACT_DEFAULTS)
        base.update(W_train=env.clocks.w_train, rho=float(env.costs.c_r))
        base.update(self.cfg_overrides)
        self.cfg = RARConfig(**base)
        self.det = self.detector_factory()
        self.log: list[dict] = []
        self.labels: list[
            tuple[int, int, float, Any]
        ] = []  # (label_round, served model, served loss, label)
        self.delays: list[int] = []
        self.phase: dict[int, int] = {}  # round -> 0 serving, 1 stage-1, 2 stage-2 (as served)
        self._h_ptr = 0
        self._m_prev: int | None = None
        self.birth_t = -self.cfg.g
        self.det_updates = 0
        self.det_rounds: list[int] = []
        self.detections: list[int] = []
        self.flag: dict | None = None
        self.last_t_d: int | None = None
        self.alerted: set[tuple] = set()
        self.alert_queue: list[tuple[str, dict]] = []
        self.last_a3 = -(10**9)
        self.st = SERVING
        self._retrain_used0 = 0

    def _log(self, t: int, event: str, **d) -> None:
        self.log.append({"t": t, "event": event, "state": self.st, **d})

    # ------------------------------------------------------------------ per-round intake
    def _tau_hat(self) -> int:
        return int(np.median(self.delays)) if self.delays else int(self.cfg.tau)

    def _rebirth(self, t: int, why: str) -> None:
        self.birth_t = t
        self.det = self.detector_factory()
        self.det_updates = 0
        self.det_rounds = []
        self.flag = None
        self._log(t, "model_birth", why=why)

    def _intake(self, state: ObservableState) -> None:
        t = state.t
        if self._m_prev is None:
            self._m_prev = state.m
        elif state.m != self._m_prev:
            self._rebirth(t, f"model_change_{self._m_prev}_to_{state.m}")
            self._m_prev = state.m
        fresh = []
        for lab in state.H[self._h_ptr :]:
            loss = lab.loss(lab.model_at_request)
            if loss is None:
                continue
            self.delays.append(lab.release_t - lab.request_t)
            rec = (lab.label_round, lab.model_at_request, float(loss), lab)
            self.labels.append(rec)
            fresh.append(rec)
        self._h_ptr = len(state.H)
        for lr, _ms, loss, _lab in sorted(fresh, key=lambda r: r[0]):
            if self.phase.get(lr, 0) == 0 and lr >= self.birth_t + self.cfg.g:
                self._det_update(lr, loss, t)
        in_canary = self.st in (CANARY1, CANARY2, SWITCHING)
        if (
            self.flag is not None
            and not in_canary
            and t - self.flag["raised"] > self._tau_hat() + self.cfg.W_train
        ):
            self._log(t, "flag_expired", t_hat_d=self.flag["t_d"])
            self.flag = None

    def _det_update(self, lr: int, loss: float, t: int) -> None:
        self.det_updates += 1
        self.det_rounds.append(lr)
        fired = self.det.update(loss)
        if fired and self.det_updates >= self.cfg.detector_warmup:
            w = max(1, min(int(self.det.width), len(self.det_rounds)))
            t_d = max(self.det_rounds[-w], self.birth_t)
            self.detections.append(lr)
            if self.flag is None:
                self.flag = {"t_d": int(t_d), "raised": int(t), "evaluated": False}
                self.last_t_d = int(t_d)
                self._log(t, "detector_flag", frontier=lr, t_hat_d=int(t_d))

    # ------------------------------------------------------------------ accuracy helpers (released labels only)
    def _acc(self, lo: int, hi: int) -> float | None:
        v = [l_ for lr, _ms, l_, _ in self.labels if lo <= lr <= hi and self.phase.get(lr, 0) == 0]
        return 1.0 - float(np.mean(v)) if len(v) >= self.min_window_labels else None

    def _acc_cur(self, t: int) -> float | None:
        f = t - self._tau_hat()
        return self._acc(f - self.cfg.W_cur + 1, f)

    def _acc_pre(self, t_d: int) -> float | None:
        e = t_d - self.cfg.g
        return self._acc(e - self.cfg.W_ref + 1, e)

    def _acc_ref_recent(self, t: int) -> float | None:
        e = t - self._tau_hat() - self.cfg.W_cur
        return self._acc(e - self.cfg.W_ref + 1, e)

    def _labeled_in_window(self, t_d: int, t: int) -> int:
        hi = min(t - 1, t_d + self.cfg.W_train - 1)
        return sum(1 for lr, *_ in self.labels if t_d <= lr <= hi)

    def _ctx(self, state: ObservableState, *, win=0, acc_pre=None, acc_cur=None) -> HookContext:
        return HookContext(
            t=state.t,
            state=self.st,
            tau=self._tau_hat(),
            cfg=self.cfg,
            n_labels_released=len(state.H),
            n_pending=state.b.pending,
            routed_to_new=state.route is not None,
            canary_stage={CANARY1: 1, SWITCHING: 2, CANARY2: 2}.get(self.st, 0),
            labeled_in_window=win,
            t_hat_d=None if self.flag is None else self.flag["t_d"],
            acc_pre=acc_pre,
            acc_cur=acc_cur,
            rho=float(self.env.costs.c_r),
        )

    # ------------------------------------------------------------------ budgets / helpers
    def _can_retrain(self, state: ObservableState) -> bool:
        b, cap = state.b, self.env.budget.retrain_cap
        return (
            b.retrain_busy_until is None
            and b.retrain_cooldown_left <= 1
            and (cap is None or b.retrain_used < cap)
        )

    def _poll_retrain(self, state: ObservableState) -> str:
        """'pending' | 'refused' | 'done' for the retrain issued earlier."""
        b = state.b
        if b.retrain_used <= self._retrain_used0:
            return "refused"
        return "pending" if b.retrain_busy_until is not None else "done"

    def _query(self, state: ObservableState, acts: list[Action]) -> None:
        b = state.b
        if b.label_remaining <= 0:
            return
        if self.env.budget.pending_cap is not None and b.pending >= self.env.budget.pending_cap:
            return
        if self.label_policy.request(self._ctx(state)):
            acts.append(Action("query"))

    def _queue_alert(self, kind: str, key: tuple | None = None, **d) -> None:
        if key is not None:
            if key in self.alerted:
                return
            self.alerted.add(key)
        self.alert_queue.append((kind, d))

    def _emit_alert(self, t: int, acts: list[Action]) -> None:
        if self.alert_queue and "alert" in self.env.allowed_actions:
            kind, d = self.alert_queue.pop(0)
            acts.append(Action("alert"))
            self._log(t, "alert", kind=kind, **d)
        elif self.alert_queue:
            self.alert_queue.clear()


class RARPolicy(_MonitorBase):
    """RAR state machine over the common contract (see module docstring for the mapping)."""

    name = "rar"

    def __init__(
        self,
        *,
        gate2: GateRule | None = None,
        gate3: GateRule | None = None,
        **kw,
    ) -> None:
        super().__init__(**kw)
        self.gate2: GateRule = gate2 or ThetaLGate()
        self.gate3: GateRule = gate3 or ThetaRGate()

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        self.hold: dict | None = None
        self.c: dict = {}
        self.pending_rollback = False
        self.canary_degraded = False
        self.retries = 0

    # ------------------------------------------------------------------ main
    def act(self, state: ObservableState):
        t = state.t
        self._intake(state)
        acts: list[Action] = []
        if self.st == SERVING:
            self._serving(state, acts)
        elif self.st == RETRAINING:
            self._retraining(state, acts)
        elif self.st == CANARY1:
            self._canary1(state, acts)
        elif self.st == SWITCHING:
            self._switching(state, acts)
        elif self.st == CANARY2:
            self._canary2(state, acts)
        if self.st == HOLD:
            self._hold(state, acts)
        self.phase[t] = {CANARY1: 1, SWITCHING: 2, CANARY2: 2}.get(self.st, 0)
        self._emit_alert(t, acts)
        self._query(state, acts)
        return acts or Action("continue")

    # ------------------------------------------------------------------ SERVING
    def _serving(self, state: ObservableState, acts: list[Action]) -> None:
        t = state.t
        if self.flag is None:
            self._maybe_a3(state)
            return
        t_d = self.flag["t_d"]
        a_pre, a_cur = self._acc_pre(t_d), self._acc_cur(t)
        ctx = self._ctx(state, win=self._labeled_in_window(t_d, t), acc_pre=a_pre, acc_cur=a_cur)
        g2 = bool(self.gate2.passes(ctx))
        g3 = bool(self.gate3.passes(ctx)) if g2 else False
        self._log(t, "gates", g2=g2, g3=g3, win=ctx.labeled_in_window, a_pre=a_pre, a_cur=a_cur)
        if g2 and g3:
            slot_free = state.m == INCUMBENT
            cap = self.env.budget.retrain_cap
            if not slot_free or (cap is not None and state.b.retrain_used >= cap):
                self._queue_alert("A_blocked", (t_d, "A_blocked"), t_hat_d=t_d)
                return
            if self._can_retrain(state):
                self._do_retrain(state, acts, "gates_pass")
            return
        self._queue_alert("A1" if not g2 else "A2", (t_d, "A1" if not g2 else "A2"), t_hat_d=t_d)

    def _maybe_a3(self, state: ObservableState) -> None:
        t, cfg = state.t, self.cfg
        if t - self.last_a3 < cfg.W_mon:
            return
        cur, ref = self._acc_cur(t), self._acc_ref_recent(t)
        if cur is not None and ref is not None and ref - cur >= cfg.soft_thr:
            self.last_a3 = t
            self._queue_alert("A3", None, drop=ref - cur)

    def _do_retrain(self, state: ObservableState, acts: list[Action], reason: str) -> None:
        self._retrain_used0 = state.b.retrain_used
        acts.append(Action("retrain"))
        self.flag = None
        self.st = RETRAINING
        self._log(state.t, "retrain_issued", reason=reason)

    # ------------------------------------------------------------------ RETRAINING -> canary
    def _retraining(self, state: ObservableState, acts: list[Action]) -> None:
        t = state.t
        r = self._poll_retrain(state)
        if r == "pending":
            return
        if r == "refused":
            self.st = SERVING
            self._log(t, "retrain_refused")
            return
        if state.m == RETRAINED:  # auto-deployed on completion: stage 1 impossible
            self.canary_degraded = True
            self._start_stage(t, 2)
            self.st = CANARY2
            self._log(t, "probation_no_stage1")
            return
        self._start_stage(t, 1)
        acts.append(Action("route", target=RETRAINED, fraction=self.cfg.p1))
        self.st = CANARY1
        self._log(t, "stage1_start", p1=self.cfg.p1)

    def _start_stage(self, t: int, stage: int) -> None:
        cfg, tau = self.cfg, self._tau_hat()
        nominal = (tau + math.ceil(cfg.W1 / cfg.p1)) if stage == 1 else (tau + cfg.W2)
        self.c = {
            "stage": stage,
            "start": t,
            "timeout": int(cfg.kappa_canary_mult * nominal),
            "interim": False,
            "ref": self._acc(t - cfg.W_ref, t - 1),
        }

    def _stats(self) -> dict[str, Any]:
        c, stage = self.c, self.c["stage"]
        sel = [
            lab
            for lr, ms, _l, lab in self.labels
            if lr >= c["start"] and ms == RETRAINED and self.phase.get(lr) == stage
        ]
        new = [lab.loss(RETRAINED) for lab in sel]
        old = [lab.loss(INCUMBENT) for lab in sel]
        n = len(sel)
        if n == 0:
            return {"n": 0}
        paired = all(o is not None for o in old) and all(v is not None for v in new)
        a_new = 1.0 - float(np.mean([v for v in new if v is not None]))
        if paired:
            a_old = 1.0 - float(np.mean(old))
            n01 = sum(1 for a, b in zip(new, old) if a == 0 and b == 1)
            n10 = sum(1 for a, b in zip(new, old) if a == 1 and b == 0)
        else:
            a_old = c["ref"] if c["ref"] is not None else 0.0
            n01 = n10 = 0
        return {"n": n, "a_new": a_new, "a_old": a_old, "n01": n01, "n10": n10, "paired": paired}

    # ------------------------------------------------------------------ CANARY stages
    def _verdict(self, stage: int) -> tuple[str, dict]:
        """('wait' | 'pass' | R-cause string, stats)."""
        cfg, c = self.cfg, self.c
        s = self._stats()
        W = cfg.W1 if stage == 1 else cfg.W2
        if s["n"] == 0:
            return "wait", s
        n, a_new, a_old = s["n"], s["a_new"], s["a_old"]
        if not c["interim"] and 0.5 * W <= n < W:
            c["interim"] = True
            if a_new < a_old - cfg.interim_margin_mult * cfg.delta:
                return "R1_interim", s
        if n < W:
            return "wait", s
        if a_new < 0.5 and a_new < a_old:
            return "R3", s
        if a_new < a_old - cfg.delta:
            return "R1", s
        return "pass", s

    def _canary1(self, state: ObservableState, acts: list[Action]) -> None:
        t = state.t
        if state.route is None and t > self.c["start"]:  # route was refused or cancelled
            self._abort_stage1(state, acts, "route_lost", clear=False)
            return
        if t - self.c["start"] > self.c["timeout"]:
            self._queue_alert("canary_timeout", None)
            self._abort_stage1(state, acts, "timeout")
            return
        v, s = self._verdict(1)
        if v == "wait":
            return
        if v != "pass":
            self._abort_stage1(state, acts, v, **{k: s[k] for k in ("n", "a_new", "a_old")})
            return
        self._log(t, "stage1_pass", **{k: s[k] for k in ("n", "a_new", "a_old")})
        b, bud = state.b, self.env.budget
        if (bud.switch_cap is not None and b.switch_used >= bud.switch_cap) or (
            bud.rollback_cap is not None and b.rollback_used >= bud.rollback_cap
        ):
            self._abort_stage1(state, acts, "no_switch_or_rollback_budget")
            return
        acts.append(Action("switch", target=RETRAINED))
        self.c["switch_t"] = t
        self.c["switch_tries"] = 1
        self.st = SWITCHING

    def _abort_stage1(self, state, acts, cause, clear=True, **d):
        t = state.t
        if clear:
            acts.append(Action("route", target=RETRAINED, fraction=0.0))
        self._log(t, "stage1_abort", cause=cause, **d)
        self._rebirth(t, "stage1_abort_" + cause)
        self._enter_hold(t, cause)

    def _switching(self, state: ObservableState, acts: list[Action]) -> None:
        t = state.t
        if state.m == RETRAINED:
            switch_t = self.c["switch_t"]
            self._start_stage(t, 2)
            self.c["start"] = switch_t
            self.st = CANARY2
            return
        waited = t - self.c["switch_t"]
        if waited > self.env.clocks.deploy_lag + 3:
            self._log(t, "switch_failed")
            self._rebirth(t, "switch_failed")
            self._enter_hold(t, "switch_failed")
        elif waited > self.env.clocks.deploy_lag:
            acts.append(Action("switch", target=RETRAINED))

    def _canary2(self, state: ObservableState, acts: list[Action]) -> None:
        t, cfg = state.t, self.cfg
        if t - self.c["start"] > self.c["timeout"]:
            self._queue_alert("canary_timeout", None)
            self._fail_stage2(state, acts, "timeout")
            return
        v, s = self._verdict(2)
        if v == "wait":
            return
        if v != "pass":
            self._fail_stage2(state, acts, v, **{k: s[k] for k in ("n", "a_new", "a_old")})
            return
        if s["paired"]:
            d = s["n01"] + s["n10"]
            z = (s["n01"] - s["n10"]) / math.sqrt(d) if d > 0 else 0.0
            ok = z >= cfg.z_commit - 1e-12
        else:
            z, ok = None, s["a_new"] >= s["a_old"]
        info = {"z": z, "unpaired": not s["paired"], "a_new": s["a_new"], "a_old": s["a_old"]}
        if ok:
            self._log(t, "commit", **info)
            self.st = SERVING
            self._rebirth(t, "commit")
            self.c = {}
        else:
            self._fail_stage2(state, acts, "dead_band", **info)

    def _fail_stage2(self, state, acts, cause, **d):
        t = state.t
        self._log(t, "stage2_fail", cause=cause, **d)
        self.pending_rollback = True
        self.retries = 0
        self._rebirth(t, "rollback_" + cause)
        self._enter_hold(t, cause)
        self._maybe_rollback(state, acts)

    def _maybe_rollback(self, state: ObservableState, acts: list[Action]) -> None:
        if not self.pending_rollback:
            return
        if state.m != RETRAINED or state.prev_m is None:
            self.pending_rollback = False
            return
        if self.retries > 5:
            self._log(state.t, "rollback_giveup")
            self.pending_rollback = False
            return
        self.retries += 1
        acts.append(Action("rollback"))

    # ------------------------------------------------------------------ HOLD (Alert-Hold-Soft)
    def _enter_hold(self, t: int, cause: str) -> None:
        self.hold = {"start": t, "left": self.cfg.kappa_short, "cause": cause}
        self.flag = None
        self.st = HOLD
        self._log(t, "hold_enter", cause=cause, duration=self.cfg.kappa_short)

    def _hold(self, state: ObservableState, acts: list[Action]) -> None:
        t, cfg, h = state.t, self.cfg, self.hold
        if h is None:
            self.st = SERVING
            return
        if t == h["start"]:
            return
        self._maybe_rollback(state, acts)
        h["left"] -= 1
        if h["left"] <= 0:
            self._log(t, "hold_exit", reason="expiry")
            self.st, self.hold = SERVING, None
            return
        if (
            t - h["start"] >= cfg.kappa_min
            and self.last_t_d is not None
            and state.m == INCUMBENT
            and not self.pending_rollback
        ):
            anchor = max(self.last_t_d, t - self._tau_hat() - cfg.W_train + 1)
            cur, ref = self._acc_cur(t), self._acc_ref_recent(t)
            ctx = self._ctx(state, win=self._labeled_in_window(anchor, t), acc_pre=ref, acc_cur=cur)
            if (
                cur is not None
                and ref is not None
                and cur < ref - cfg.delta_crit_mult * cfg.theta_R
                and self.gate2.passes(ctx)
                and self._can_retrain(state)
            ):
                self._log(t, "emergency_override", cur=cur, ref=ref)
                self.st, self.hold = SERVING, None
                self._do_retrain(state, acts, "emergency_override")


class BinaryPolicy(_MonitorBase):
    """ADWIN flag -> retrain (immediate deployment). ``cost_aware=True`` is the paper's Cost-Aware Binary."""

    name = "cost_aware_binary"

    def __init__(self, *, cost_aware: bool = True, **kw) -> None:
        super().__init__(**kw)
        self.cost_aware = cost_aware
        self.name = "cost_aware_binary" if cost_aware else "binary"

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        self.switch_wait = 0

    def act(self, state: ObservableState):
        t, env = state.t, self.env
        self._intake(state)
        acts: list[Action] = []
        if self.st == RETRAINING:
            r = self._poll_retrain(state)
            if r == "refused":
                self.st = SERVING
            elif r == "done":
                if state.m != RETRAINED and not env.clocks.deploy_on_complete:
                    acts.append(Action("switch", target=RETRAINED))
                    self.switch_wait += 1
                    if self.switch_wait > env.clocks.deploy_lag + 3:
                        self.st, self.switch_wait = SERVING, 0
                else:
                    self.st, self.switch_wait = SERVING, 0
                    self._rebirth(t, "retrain_deployed")
        if self.st == SERVING and self.flag is not None and not self.flag["evaluated"]:
            self._evaluate_flag(state, acts)
        self.phase[t] = 0
        self._query(state, acts)
        return acts or Action("continue")

    def _evaluate_flag(self, state: ObservableState, acts: list[Action]) -> None:
        t, cfg, env = state.t, self.cfg, self.env
        if not self._can_retrain(state):
            return
        self.flag["evaluated"] = True
        if self.cost_aware:
            a_pre, a_cur = self._acc_pre(self.flag["t_d"]), self._acc_cur(t)
            d_hat = 0.0 if (a_pre is None or a_cur is None) else max(0.0, a_pre - a_cur)
            H = float(np.mean(np.diff(self.detections))) if len(self.detections) >= 2 else 0.0
            H = max(H, float(cfg.W_train))
            cost = float(env.costs.c_r) + (
                0.0 if env.clocks.deploy_on_complete else float(env.costs.c_s)
            )
            ok = d_hat * H >= cost
            self._log(t, "cost_gate", d_hat=d_hat, H=H, cost=cost, passes=ok)
            if not ok:
                self.flag = None
                return
        self._retrain_used0 = state.b.retrain_used
        acts.append(Action("retrain"))
        self.flag = None
        self.st = RETRAINING
        self._log(t, "retrain_issued", reason="binary_flag")


class _RARAdapter:
    name = "rar"
    vocabulary = ("query", "continue", "retrain", "switch", "rollback", "alert", "route")
    claimed_null = "none"
    port_status = "COMMON_CONTRACT_PORT"
    fidelity = "PAPER_RECONSTRUCTION (see module docstring for every simplification)"

    def __init__(self, **kw) -> None:
        self.kw = kw

    def build(self, env: EnvSpec) -> RARPolicy:
        p = RARPolicy(**self.kw)
        p.reset(env)
        return p


class _BinaryAdapter:
    vocabulary = ("query", "continue", "retrain", "switch")
    claimed_null = "none"
    port_status = "COMMON_CONTRACT_PORT"
    fidelity = "PAPER_RECONSTRUCTION"

    def __init__(self, name: str, cost_aware: bool, **kw) -> None:
        self.name, self.cost_aware, self.kw = name, cost_aware, kw

    def build(self, env: EnvSpec) -> BinaryPolicy:
        p = BinaryPolicy(cost_aware=self.cost_aware, **self.kw)
        p.reset(env)
        return p


RARAdapter = _RARAdapter()
CostAwareBinaryAdapter = _BinaryAdapter("cost_aware_binary", True)
BinaryAdapter = _BinaryAdapter("binary", False)

__all__ = [
    "CONTRACT_DEFAULTS",
    "BinaryAdapter",
    "BinaryPolicy",
    "CostAwareBinaryAdapter",
    "RARAdapter",
    "RARPolicy",
    "canary_clocks",
]
