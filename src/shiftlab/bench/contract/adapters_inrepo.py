"""COMMON_CONTRACT_PORT adapters for the in-repo ShiftLab comparators (WP1e).

NEW file; does not touch the other contract modules. Code of the methods lives in
``shiftlab.sota.inrepo`` (ported unchanged from other refs, see that package's file headers) and in
``shiftlab.dive`` (base). Provenance, outputs, nulls and regression evidence:
``docs/d2a_rar/baselines/INREPO_PORTS.md``.

Atlas-harness methods (Gap-Mix, PAVE, delay-gated PAVE, FreshCheck, DSS/straddle, Markov-LR,
gap-10 thinning, episode_front, E_rb, two-phase, Page-CUSUM default, ...) are
``shiftlab.dive.switching_explore.Method`` objects: ``step(t, released) -> (action in {0,1}, query)``
with ``released = ((event_round, D), ...)``, ``D = loss(candidate) - loss(incumbent)`` of a queried
round. ``AtlasMethodPolicy`` drives one through ``ObservableState``:

Fidelity notes (every simplification relative to the native Atlas harness; these are the whole list):
  F1  ``obs_mode='shadow'`` is required (the paired gain must be identifiable from one label).
  F2  The Atlas ``Config`` needs a constant label delay ``d``; the contract policy cannot know the
      stream's delay distribution, so ``declared_delay`` is a public constructor argument (default
      10) used only for the method's calendar / ``t + d <= T`` rule / DSS delay switch / PAVE
      capacity. If the stream's real delays differ, the method runs mis-specified and that is part
      of the comparison (nothing is read from the stream).
  F3  Atlas switch cost ``s`` := ``costs.c_s`` and query cost ``c`` := ``costs.c_q``; the hurdle is
      ``env.hurdle`` and ``alpha = 0.1`` unless overridden. Rollback is charged ``c_b`` (Atlas charged
      ``s`` for any action change); alerts/retrains/abstain are never used.
  F4  Query actions carry ``propensity=1.0``: every one of these rules is a deterministic function of
      the released history and public config (no randomisation).
  F5  The Atlas methods assume labels are released after exactly ``d`` rounds, in order, none lost.
      Under out-of-order, random-delay or missing labels, ``pending_events`` bookkeeping (DSS pending
      cap 2) can stall acquisition; this is a native limitation, reported not repaired.
  F6  If the contract refuses/limits a query the method already decided (label cap, pending cap),
      the adapter revokes it (``used``, ``pending_events``, ``last_query`` restored) and counts it in
      ``n_revoked``; PAVE/FreshCheck credit-pacing counters are NOT restored. If a model change is
      refused (cooldown), the method believes it acted; the adapter re-issues the change on the next
      round while ``method.act != state.m``.
  F7  ``D`` is not binarised by the adapter; Markov-LR binarises by sign internally (native).
  F8  Models 0/1 only; retrained model 2 never used.
"""

from __future__ import annotations

from dataclasses import dataclass

from shiftlab.dive.switching_explore import Config
from shiftlab.sota.inrepo import atlas_methods
from shiftlab.sota.inrepo.rmm import HorizonWeightedPacer, MixtureSRDetector

from .policies import BasePolicy
from .types import CANDIDATE, INCUMBENT, Action, EnvSpec, ObservableState

PORT_STATUS = "COMMON_CONTRACT_PORT"
_VOCAB = ("query", "continue", "switch", "rollback")
_NULL_MAP = {
    "cond": "cond",
    "marg": "marg",
    "abs_risk": "abs_risk",
    "absolute_risk": "abs_risk",
    "none": "none",
    "econ": "none",
}


class AtlasMethodPolicy(BasePolicy):
    """Drive an Atlas ``Method`` from ``ObservableState`` (see module docstring F1-F8)."""

    def __init__(self, name: str, factory, declared_delay: int = 10, alpha: float = 0.1) -> None:
        self.name, self._factory = name, factory
        self.declared_delay, self.alpha = int(declared_delay), float(alpha)
        self.n_revoked = 0

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        if env.obs_mode != "shadow":
            raise NotImplementedError(
                "in-repo Atlas methods need obs_mode='shadow' (paired gain per label)"
            )
        B = min(env.budget.label_cap, env.T)
        self.cfg = Config(
            T=env.T,
            B=B,
            d=self.declared_delay,
            c=float(env.costs.c_q),
            s=float(env.costs.c_s),
            h=float(env.hurdle),
            alpha=self.alpha,
        )
        self.m = self._factory()
        self.m.start(self.cfg)
        self._seen, self.n_revoked = 0, 0

    def act(self, state: ObservableState):
        new = state.H[self._seen :]
        self._seen = len(state.H)
        rel = []
        for lab in new:
            g = lab.gain()
            if g is not None:
                rel.append((lab.label_round or lab.request_t, -float(g)))
        rel.sort(key=lambda r: r[0])
        used0, last0 = self.m.used, self.m.last_query
        action, query = self.m.step(state.t, tuple(rel))
        out: list[Action] = []
        if action == 1 and state.m == INCUMBENT:
            out.append(Action("switch", target=CANDIDATE))
        elif action == 0 and state.m == CANDIDATE:
            out.append(
                Action("rollback")
                if state.prev_m is not None
                else Action("switch", target=INCUMBENT)
            )
        if query:
            blocked = state.b.label_remaining <= 0 or (
                self.env.budget.pending_cap is not None
                and state.b.pending >= self.env.budget.pending_cap
            )
            if blocked:
                self.m.used, self.m.last_query = used0, last0
                self.m.pending_events.discard(state.t)
                self.n_revoked += 1
            else:
                out.append(Action("query", propensity=1.0))
        return out or Action("continue")


class RMMDetectorPolicy(BasePolicy):
    """RMM detector (``MixtureSRDetector`` + ``HorizonWeightedPacer``, ported unchanged) alone.

    Native RMM wraps a base certificate policy and restarts it on every switch; that wrapper needs the
    sprint event simulator and is NOT ported (PARTIAL). Here the base never acts, so every promotion
    comes from the detector at ``alpha_det = alpha*alpha_split / 2^j`` (j-th promotion) and every
    rollback at ``alpha_rb = alpha``. Outcomes are x = sign(gain) (0 skipped), signed so +1 = the
    non-deployed model was right, entered in REQUEST order once released (native ordering; a never-released
    head label blocks the queue exactly as in the source). Each round counts as a 'disagreement' for the pacer;
    queries are randomised with ``state.u[0] < q`` and carry ``propensity=q`` (the source's RMM is randomised).
    """

    name = "rmm_detector"

    def __init__(
        self,
        alpha: float = 0.1,
        alpha_split: float = 0.5,
        gap: int = 10,
        pace_k: float = 1.0,
        p_min: float = 0.05,
    ) -> None:
        self.alpha, self.alpha_split, self.gap, self.pace_k, self.p_min = (
            alpha,
            alpha_split,
            gap,
            pace_k,
            p_min,
        )

    def reset(self, env: EnvSpec) -> None:
        super().reset(env)
        if env.obs_mode != "shadow":
            raise NotImplementedError("rmm_detector needs obs_mode='shadow'")
        self.B = env.budget.label_cap
        self.acq = HorizonWeightedPacer(env.T, self.B, p_min=self.p_min, k=self.pace_k)
        self.alpha_det, self.alpha_rb = self.alpha * self.alpha_split, self.alpha
        self.deployed, self.n_prom = INCUMBENT, 0
        self.order: list[int] = []
        self.queue: dict[int, int] = {}
        self._seen = 0
        self.det = self._new_det()

    def _new_det(self) -> MixtureSRDetector:
        a = self.alpha_det / (2.0**self.n_prom) if self.deployed == INCUMBENT else self.alpha_rb
        return MixtureSRDetector(a, self.B, self.gap)

    def act(self, state: ObservableState):
        if state.m != self.deployed:  # a refused/lagged change: follow the model actually in force
            self.deployed = state.m if state.m in (INCUMBENT, CANDIDATE) else self.deployed
            self.det, self.order, self.queue = self._new_det(), [], {}
        for lab in state.H[self._seen :]:
            g = lab.gain()
            if g is not None and g != 0:
                self.queue[lab.request_t] = 1 if g > 0 else -1
        self._seen = len(state.H)
        alarm = False
        while self.order and self.order[0] in self.queue:
            d = self.queue.pop(self.order.pop(0))
            if self.det.update(d if self.deployed == INCUMBENT else -d):
                alarm = True
                break
        out: list[Action] = []
        if alarm:
            if self.deployed == INCUMBENT:
                self.n_prom += 1
                out.append(Action("switch", target=CANDIDATE))
                self.deployed = CANDIDATE
            else:
                out.append(
                    Action("rollback")
                    if state.prev_m is not None
                    else Action("switch", target=INCUMBENT)
                )
                self.deployed = INCUMBENT
            self.det, self.order, self.queue = self._new_det(), [], {}
        q = self.acq.propensity(state.t, state.b.label_remaining, True)
        self.acq.note_event(True)
        pend_ok = (
            self.env.budget.pending_cap is None or state.b.pending < self.env.budget.pending_cap
        )
        if state.b.label_remaining > 0 and pend_ok and q > 0.0 and state.u and state.u[0] < q:
            self.order.append(state.t)
            out.append(Action("query", propensity=q))
        return out or Action("continue")


@dataclass
class InRepoAdapter:
    """``NativeAdapter``-compatible record (name / vocabulary / claimed_null / port_status / build)."""

    name: str
    claimed_null: str
    registry_id: str
    outputs: tuple[str, ...]
    source: str
    build_fn: object
    vocabulary: tuple[str, ...] = _VOCAB
    port_status: str = PORT_STATUS
    fidelity: str = "see module docstring F1-F8"

    def build(self, env: EnvSpec, **kw) -> BasePolicy:
        return self.build_fn(**kw)


def _atlas_adapters() -> dict[str, InRepoAdapter]:
    out = {}
    for n in atlas_methods.NAMES:
        inf = atlas_methods.info(n)
        out[n] = InRepoAdapter(
            name=n,
            claimed_null=_NULL_MAP[inf.null],
            registry_id=inf.registry_id,
            outputs=inf.outputs,
            source=inf.source,
            build_fn=lambda n=n, declared_delay=10, alpha=0.1: AtlasMethodPolicy(
                n, lambda: atlas_methods.build(n), declared_delay, alpha
            ),
        )
    out["rmm_detector"] = InRepoAdapter(
        name="rmm_detector",
        claimed_null="cond",
        registry_id="rmm",
        outputs=("promotion", "rollback", "label_allocation"),
        source="origin/codex/sprint2-leaderboards scripts/failure_atlas_v2/restart_monitor.py (detector+pacer only)",
        build_fn=lambda **kw: RMMDetectorPolicy(**kw),
        fidelity="PARTIAL: detector and pacer ported unchanged; wrapped base policy + restart NOT ported",
    )
    return out


ADAPTERS = _atlas_adapters()


class _NotPorted:
    """Documented non-ports: ``build`` raises with the reason (kept importable so a runner can enumerate)."""

    vocabulary: tuple[str, ...] = ()
    port_status = "NOT_PORTED_TO_COMMON_CONTRACT"

    def __init__(self, name: str, claimed_null: str, registry_id: str, reason: str) -> None:
        self.name, self.claimed_null, self.registry_id, self.reason = (
            name,
            claimed_null,
            registry_id,
            reason,
        )

    def build(self, env: EnvSpec) -> BasePolicy:
        raise NotImplementedError(f"{self.name}: {self.reason}")


NOT_PORTED = {
    "h2c": _NotPorted(
        "h2c",
        "cond",
        "h2c",
        "H2c/HG (shiftlab.hgxh2c.baselines.h2c/hg; importable) bet on prediction-powered Brier and cost increments "
        "(StreamEvent.proxy / theta / pmax from a proxy predictor and a source calibration). Suite B exposes neither a "
        "proxy predictor nor a source-risk calibration; labels-only H2c would be a different method.",
    ),
    "pprm": _NotPorted(
        "pprm",
        "abs_risk",
        "pprm",
        "PPRM (shiftlab.dive.pprm_risk_monitor; importable) needs an unlabelled batch with proxy losses per round and a "
        "labelled source-risk upper bound; neither is in ObservableState. It also monitors one model's absolute running "
        "risk, not the paired incumbent/candidate gain.",
    ),
    "e_rb_sprint": _NotPorted(
        "e_rb_sprint",
        "cond",
        "e_rb",
        "The original (origin/codex/sprint2-leaderboards scripts/sota_sprint/fam_e.py _rb -> fam_b.RecoveryMonitor) runs on "
        "the sprint event/disagreement simulator with certificate hosts; the detector logic is available as the 'erb' "
        "entry (gave-r erb_port), a documented adaptation.",
    ),
}
