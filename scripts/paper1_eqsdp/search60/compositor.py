# ruff: noqa: RUF012
"""Module compositor for the Paper 1 60-module search (docs/paper1_eqsdp/search60/).

``ComposedPolicy`` wraps a frozen parent (EQSDp arm R + cutoff, or the matched Wald + cutoff) and
runs independently switchable modules at fixed hooks. With no modules it mirrors the parent's
``request_labels`` step by step (same arithmetic, same random draws), so it equals ``s2armr_H1100``
(or ``s2wald_*_H1100``) bitwise; this is tested.

Information rule: modules see only ``Ctx``: t, model predictions, remaining budget, pending
(requested, unreleased) labels, released purchased feedback (event_id, t_requested, t_released,
model_losses) and the declared contract (T, B, delay, cutoff). Event and feedback objects are copied
into ``EventView`` / ``FeedbackView`` so ``label``, ``extra``, ``query_probability`` and ``context``
are never reachable.

Hook order inside one event (see COMPOSITION_RULES.md; the simulator fixes release before predict):

    observe(fbs)  : parent evidence update -> m.on_release (hook 2) -> m.on_switch_proposal (hook 4)
    predict(ev)   : m.on_event (hook 1) -> parent.predict -> m.override_deploy (hook 4)
    request_labels: parent paced propensity + cutoff (hook 3) -> m.scale -> draw -> cutoff ->
                    m.floor (A/B/E reopen & forced) -> m.veto (gates) -> reserves (budget cap)
    log           : one record per decision (hook 5)
"""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

HERE = Path(__file__).resolve().parent
PARENT_DIR = HERE.parent
for _p in (PARENT_DIR, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import stage1_policies  # noqa: F401  (puts the simulator on sys.path)
import trace_run  # noqa: F401
from simulator import QueryRequest

EXCLUSIVE_GROUPS = [{"C21", "C24", "C25", "C26", "C29", "C30"}]
PRECEDENCE = {"E": 0, "F": 1, "D": 2, "C": 3, "B": 4, "A": 5}  # switch-hook order (safety first)
NEVER = 10**9


class UnsupportedCombo(Exception):
    status = "UNSUPPORTED_COMBO"


class NotImplementedModule(Exception):
    status = "NOT_IMPLEMENTED"


class EventView(NamedTuple):
    event_id: int
    t: int
    horizon: int
    model_predictions: tuple


class FeedbackView(NamedTuple):
    event_id: int
    t_requested: int
    t_released: int
    model_losses: tuple

    @property
    def d(self) -> int:
        """l0 - l1: +1 challenger (model 1) correct, -1 incumbent model 0 correct."""
        return int(self.model_losses[0]) - int(self.model_losses[1])


@dataclass
class Force:
    """kind 'lift': lift the cutoff for the parent's own paced draw on this event.
    kind 'force': buy now (the module has already drawn, if randomised); prob is recorded."""

    kind: str = "force"
    prob: float = 1.0
    reason: str = ""


@dataclass
class Reserve:
    """``total`` labels held for the window [lo, hi). A purchase at t inside the window draws the
    reserve down; a purchase before the window (t < lo; use lo=NEVER for "armed, not triggered") must
    leave the unused part in the budget. After hi the reserve is released."""

    key: str
    total: int
    lo: int = 0
    hi: int = NEVER


@dataclass
class Proposal:
    t: int
    frm: int
    to: int
    allow: bool = True
    reasons: list = field(default_factory=list)

    def veto(self, why: str):
        self.allow = False
        self.reasons.append(why)


class Ctx:
    """Read-only view of observable state, updated by the compositor."""

    def __init__(self, parent, T, B, delay, stop_h):
        self.parent, self.T, self.B, self.delay = parent, int(T), int(B), int(delay)
        self.stop_h = stop_h
        self.t_close = None if stop_h is None else self.T - int(stop_h) - self.delay + 1
        self.t = 0
        self.preds = (0, 0)
        self.disagree = False
        self.remaining = int(B)
        self.due = 0
        self.last_release_t = -1  # t_released of the last released (informative) label
        self.last_buy_t = -1
        self.n_buys = 0
        self.last_switch_t = -1
        self.last_switch_to = None
        self.pend_t: dict[int, int] = {}  # event_id -> request time, in-flight labels

    # observable evidence of the parent (released labels only)
    @property
    def n(self):
        return self.parent.n

    @property
    def k(self):
        return self.parent.k

    @property
    def deployed(self):
        return self.parent.deployed

    @property
    def pending(self):
        return self.parent.pending

    @property
    def rate(self):
        return self.parent._rate()

    def gain_away(self, level):
        return self.parent._gain_away(level)

    @property
    def closed(self):
        """Parent cutoff closed at this event (label would be released later than T - stop_h)."""
        return self.stop_h is not None and self.t + self.delay > self.T - self.stop_h

    @property
    def releasable(self):
        return self.t + self.delay < self.T

    def evidence(self):
        return f"dep={self.deployed};k={self.k:.2f}/{self.n:.2f};pend={self.pending}"


class Module:
    """Base class. Subclasses set ID, FAMILY, DEFAULTS, SETTINGS (two presets) and override hooks."""

    ID = ""
    FAMILY = ""
    DEFAULTS: dict = {}
    SETTINGS: list = []  # SETTINGS[0], SETTINGS[1]: the two Phase-1 parameter settings

    def __init__(self, params, ctx: Ctx, rng):
        unknown = set(params) - set(self.DEFAULTS)
        if unknown:
            raise ValueError(f"{self.ID}: unknown params {sorted(unknown)}")
        self.params = {**self.DEFAULTS, **params}
        self.ctx, self.rng = ctx, rng

    # hook 1: prediction-only; called once per event from predict(), before the deploy decision
    def on_event(self, ctx):
        pass

    # hook 2: after the parent updated its evidence with this released label
    def on_release(self, ctx, fb: FeedbackView):
        pass

    # hook 3 (acquire)
    def scale(self, ctx):
        """Multiplier on the parent's propensity before its draw (None / 1.0 = no change)."""
        return

    def floor(self, ctx):
        """Return Force(...) to lift the cutoff for the parent's draw or buy now; None = no action.
        Called at every disagreement event with budget left (so counters can advance)."""
        return

    def veto(self, ctx):
        """Return a reason string to suppress a parent/lifted purchase (gate); None = allow."""
        return

    def reserves(self, ctx):
        return []

    def on_purchase(self, ctx, rec: dict):
        """rec: t, by (module ids that caused it), kind ('parent'|'lift'|'force')."""

    # hook 4
    def on_switch_proposal(self, ctx, prop: Proposal):
        pass

    def override_deploy(self, ctx):
        """Return 0/1 to force the deployed model at this event; None = no override."""
        return

    def on_deploy_change(self, ctx, frm, to):
        pass


_REG: dict[str, type] = {}


def register(cls):
    assert cls.ID and cls.ID not in _REG, cls.ID
    _REG[cls.ID] = cls
    return cls


def load_modules():
    """Import modules_A ... modules_F (those that exist) and return the id -> class registry."""
    import importlib

    for fam in "ABCDEF":
        try:
            importlib.import_module(f"modules_{fam}")
        except ModuleNotFoundError as e:
            if e.name != f"modules_{fam}":
                raise
    return _REG


def _norm_modules(spec):
    return [{"id": m} if isinstance(m, str) else dict(m) for m in spec.get("modules", [])]


def validate_spec(spec: dict) -> list:
    """Return the normalised module list or raise UnsupportedCombo / NotImplementedModule."""
    reg = load_modules()
    mods = _norm_modules(spec)
    ids = [m["id"] for m in mods]
    if len(set(ids)) != len(ids):
        raise UnsupportedCombo(f"duplicate module ids in {ids}")
    for g in EXCLUSIVE_GROUPS:
        both = sorted(set(ids) & g)
        if len(both) > 1:
            raise UnsupportedCombo(
                f"{both} are posterior engines of the exclusive group {sorted(g)}: exactly one "
                "posterior engine may run (each would redefine the evidence behind the same switch)"
            )
    for i in ids:
        if i not in reg:
            raise NotImplementedModule(f"{i} has no implementation registered")
    if spec.get("parent", {}).get("kind", "eqsdp") not in ("eqsdp", "wald"):
        raise ValueError("parent.kind must be eqsdp or wald")
    return mods


def config_id(spec: dict) -> str:
    if spec.get("name"):
        return spec["name"]
    h = hashlib.sha256(json.dumps(spec, sort_keys=True, default=str).encode()).hexdigest()[:8]
    ids = "+".join(m["id"] for m in _norm_modules(spec)) or "off"
    pk = spec.get("parent", {}).get("kind", "eqsdp")
    return f"s60{'w' if pk == 'wald' else ''}_{ids}_{h}"


class ComposedPolicy:
    def __init__(self, parent, modules, ctx: Ctx, name, log=0):
        self.parent, self.mods, self.ctx, self.name = parent, modules, ctx, name
        self.mods_sw = sorted(modules, key=lambda m: (PRECEDENCE[m.FAMILY], m.ID))
        self.ids = [m.ID for m in modules]
        self.log_level = int(log)
        self.log: list[dict] = []
        self._used: dict = {}
        self._prev_dep = parent.deployed

    # ---- logging -------------------------------------------------------------------------
    def _rec(self, **kw):
        c = self.ctx
        r = {"t": c.t, "module_ids": self.ids, "due": c.due, "pending": c.pending,
             "remaining": c.remaining, "evidence": c.evidence()}  # fmt: skip
        r.update(kw)
        self.log.append(r)

    # ---- simulator interface ---------------------------------------------------------------
    def predict(self, event):
        c, p = self.ctx, self.parent
        ev = EventView(event.event_id, event.t, event.horizon, tuple(event.model_predictions))
        c.t = int(ev.t)
        c.preds = tuple(int(x) for x in ev.model_predictions)
        c.disagree = bool(c.preds[0] != c.preds[1])
        for m in self.mods:
            m.on_event(c)
        out = p.predict(event)
        for m in self.mods_sw:
            tgt = m.override_deploy(c)
            if tgt is not None:
                if int(tgt) != p.deployed and self.log_level:
                    self._rec(kind="override", module=m.ID, proposal=f"{p.deployed}->{int(tgt)}",
                              action="override_deploy", reason=f"override:{m.ID}")  # fmt: skip
                p.deployed = int(tgt)
                out = p.deployed
                break
        if out != self._prev_dep:
            c.last_switch_t, c.last_switch_to = c.t, out
            for m in self.mods:
                m.on_deploy_change(c, self._prev_dep, out)
            self._prev_dep = out
        return out

    def observe(self, feedback):
        c, p = self.ctx, self.parent
        fbs = sorted(feedback, key=lambda f: f.event_id)
        c.due = len(fbs)
        for fb in fbs:
            before = p.deployed
            p.observe([fb])
            view = FeedbackView(fb.event_id, fb.t_requested, fb.t_released, tuple(fb.model_losses))
            c.pend_t.pop(view.event_id, None)
            c.last_release_t = view.t_released
            for m in self.mods:
                m.on_release(c, view)
            if p.deployed != before:
                prop = Proposal(view.t_released, before, p.deployed)
                for m in self.mods_sw:
                    m.on_switch_proposal(c, prop)
                if not prop.allow:
                    p.deployed = before
                if self.log_level:
                    self._rec(kind="switch", proposal=f"{before}->{prop.to}", t=view.t_released,
                              action="allow" if prop.allow else "veto",
                              reason=";".join(prop.reasons))  # fmt: skip

    def request_labels(self, event, remaining_budget):
        p, c = self.parent, self.ctx
        c.remaining = int(remaining_budget)
        p.rem = int(remaining_budget)
        dis = bool(event.model_predictions[0] != event.model_predictions[1])
        q = p.acq.propensity(event.t, p.virtual_remaining(remaining_budget), dis)
        p.acq.note_event(dis)
        if not dis or remaining_budget <= 0:
            if self.log_level >= 2:
                self._rec(kind="acquire", action="skip", reason="no_disagreement_or_budget",
                          p_parent=0.0, p_final=0.0)  # fmt: skip
            return QueryRequest(requested=False)
        q = min(1.0, q * p.mf)
        if q <= 0.0:
            return QueryRequest(requested=False)
        p_parent, scalers = q, []
        for m in self.mods:
            s = m.scale(c)
            if s is not None and s != 1.0:
                q = min(1.0, q * float(s))
                scalers.append(m.ID)
        take = bool(p.rng.random() < q)  # the parent's draw is always consumed
        closed_blocked = False
        if take and not p.keep(event, remaining_budget):
            take, closed_blocked = False, True
            p.skipped += 1
        # ---- floors: reopen (lift) and forced purchases, combined with OR
        forces = [(m, m.floor(c)) for m in self.mods]
        forces = [(m, f) for m, f in forces if f is not None]
        lifts = [(m, f) for m, f in forces if f.kind == "lift"]
        forced = [(m, f) for m, f in forces if f.kind == "force"]
        kind, by, prob = ("parent" if take else "none"), [], q
        reason = (
            "parent_draw" if take else ("cutoff_closed" if closed_blocked else "parent_draw_no")
        )
        exception = False
        if closed_blocked and lifts and c.releasable:
            take, kind, by, reason, exception = True, "lift", [m.ID for m, _ in lifts], "lift", True
        if forced and c.releasable:
            take, kind, by, exception = True, "force", [m.ID for m, _ in forced], c.closed
            prob = max(f.prob for _, f in forced)
            reason = "force:" + ",".join(f.reason or m.ID for m, f in forced)
        # ---- gates (cannot suppress forced purchases)
        if take and kind in ("parent", "lift"):
            why = [(m.ID, m.veto(c)) for m in self.mods]
            why = [f"{i}:{r}" for i, r in why if r]
            if why:
                take, reason = False, "veto:" + ";".join(why)
        # ---- budget cap (reserves); applies last, to every purchase
        if take and self._held(c.t) > remaining_budget - 1:
            take, reason = False, "cap:reserve"
        if take:
            for m in self.mods:
                for r in m.reserves(c):
                    if r.lo <= c.t < r.hi:
                        self._used[(m.ID, r.key)] = self._used.get((m.ID, r.key), 0) + 1
            p.pending += 1
            c.pend_t[event.event_id] = c.t
            c.last_buy_t, c.n_buys = c.t, c.n_buys + 1
            rec = {"t": c.t, "by": by, "kind": kind}
            for m in self.mods:
                m.on_purchase(c, rec)
        if self.log_level:
            self._rec(kind="acquire", p_parent=p_parent, p_final=prob if take else 0.0,
                      scaled_by=scalers, action="buy" if take else "skip", source=kind if take else "",
                      by=by, cutoff_exception=bool(take and exception), reason=reason,
                      closed=c.closed)  # fmt: skip
        return QueryRequest(requested=take, probability=prob if take else 0.0)

    def _held(self, t):
        held = 0
        for m in self.mods:
            for r in m.reserves(self.ctx):
                if t < r.lo:
                    held += max(0, r.total - self._used.get((m.ID, r.key), 0))
        return held

    def decision_state(self):
        return self.parent.decision_state()

    def state_dict(self):
        return {}

    def load_state_dict(self, s):
        pass


def build_parent(pspec: dict, T, B, cs, cq, delay, r, name):
    from stage1_policies import Stage1C1Stop
    from stage2_policies import Stage2Wald

    kind = pspec.get("kind", "eqsdp")
    cut = pspec.get("cutoff", 1100)
    stop_h = -(10**9) if cut is None else int(cut)  # very negative = inert (never closed)
    if kind == "eqsdp":
        extra = {k: pspec[k] for k in ("lam", "gamma") if k in pspec}
        return Stage1C1Stop(T, B, cs, rng=r("EQSD"), delay=delay, name=name, cq=cq,
                            stop_h=stop_h, **extra)  # fmt: skip
    lam, g = pspec.get("lam", 0.98), pspec.get("gamma", 0.3)
    return Stage2Wald(T, B, cs, rng=r("EQSD"), delay=delay, name=name, cq=cq, lam=lam, gamma=g,
                      stop_h=stop_h)  # fmt: skip


def make_factory(spec: dict, name: str | None = None):
    """Factory with the trace_run registry signature f(T, B, cs, cq, alpha, delay, r)."""
    mods_spec = validate_spec(spec)
    name = name or config_id(spec)
    reg = load_modules()
    pspec = spec.get("parent", {})
    log = spec.get("log", 0)

    def f(T, B, cs, cq, alpha, delay, r):
        parent = build_parent(pspec, T, B, cs, cq, delay, r, name)
        cut = pspec.get("cutoff", 1100)
        ctx = Ctx(parent, T, B, delay, None if cut is None else int(cut))
        mods = []
        for m in mods_spec:
            cls = reg[m["id"]]
            params = dict(m.get("params", {}))
            if m.get("setting") is not None:
                params = {**cls.SETTINGS[int(m["setting"])], **params}
            mods.append(cls(params, ctx, r("S60:" + m["id"])))
        return ComposedPolicy(parent, mods, ctx, name, log=log)

    f.spec = spec
    return f


def register_specs(specs: list[dict]) -> dict:
    """Register specs in the stage-2 DYN registry (per process); returns {config_id: spec}."""
    import stage2_policies as sp2

    out = {}
    for s in specs:
        n = config_id(s)
        sp2.DYN[n] = make_factory(s, n)
        out[n] = s
    return out
