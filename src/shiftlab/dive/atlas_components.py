"""Typed composition engine for the failure-atlas mechanism search (stage 5).

Exploratory development code (R4). Nothing here is a novelty, theorem or efficacy claim.
A candidate is a :class:`CandidateSpec` that picks one component from each of four slots

* ACQUISITION: ``uniform``, ``bernoulli_pacing``, ``reserve_pacing``, ``straddle``;
* EVIDENCE:    ``started_mixture_eprocess``, ``horizon_cusum``, ``window_mean`` and (Amendment 1)
               ``started_kelly``, ``weighted_starts``, ``wide_stakes``;
* MEMORY:      ``none``, ``discount``, ``restart_on_rollback``;
* DECISION:    ``certificate_econ``, ``hysteresis``, ``rollback_monitor``.

``validate_spec`` applies typing/compatibility rules and rejects (never silently repairs)
invalid combinations. ``build_candidate`` returns a :class:`ComposedMethod`, a
``switching_explore.Method`` that runs through ``switching_explore.run`` unchanged.

Validity argument for ``is_safety_gated`` (what is and is not established)
-------------------------------------------------------------------------
Null used: every regime has ``E[-D_t | information available when t was queried] <= h``
(for example ``null_harm``), where ``D`` is the paired loss difference, observed only for
queried rounds and only after the delay ``d``. Labels enter the evidence in event order.

1. Evidence is a bounded-increment test supermartingale (started mixture of fixed stakes
   and fixed starts, or the finite-horizon CUSUM e-detector of ``horizon_edetectors``)
   applied to ``-D - h``. Under the null its increments have conditional mean ``<= 0``.
   The query rule (every acquisition component) depends only on released labels, the
   round index and an independent RNG, so which rounds enter the evidence is predictable.
   This is an assumption on selection, not something the code verifies.
2. Promotion requires evidence to alarm; the other decision conditions (economic check,
   hysteresis streaks) are extra conjuncts that can only remove promotions, so they never
   weaken the false-promotion bound.
3. Repeated promotion episodes. After a rollback a fresh evidence object starts from the
   rollback time (a stopping time) with level ``alpha_j = alpha * 2^-(j+1)``, so by a union
   bound over episodes the probability that any episode alarms under the null is at most
   ``alpha``. If the decision component never rolls back there is one episode and the full
   ``alpha`` is used.
4. Heuristic pieces: the ``horizon_cusum`` threshold is a fixed finite-horizon bound
   (horizon = label budget B), not an anytime-valid level; the union-bound argument relies
   on the null holding conditionally at every episode start; and nothing proves validity
   against alternatives, delayed-regime dependence, or adaptive queries that react to
   unreleased information. Empirical false-promotion rates are sanity checks only.
5. New evidence components (Amendment 1). ``started_kelly`` is the repository
   ``MultiTimescaleStartedKellyEProcess`` (stakes predictable, in [0, 0.5], fixed start and
   half-life weights). ``weighted_starts`` is a ``VectorizedStartedMixtureEProcess`` whose start
   weights are fixed before data from the declared family onset levels (0.1/0.3/0.6/0.8 of T),
   converted to label indices through the acquisition schedule's data-independent expected label
   count, with a uniform floor of 25%. ``wide_stakes`` is the same mixture with a stake grid that
   also contains 0.9 and 0.95 (set on the instance; the class default is untouched). All stakes
   are in [0, 1) and all mixture weights are fixed before data, so each is a valid e-process under
   the same null; the family-informed weights are a declared prior and validity does not depend
   on them. The schedule approximation for ``straddle`` (data dependent) is the uniform pace.
7. ``triggered_kelly`` (Amendment 3, development only) is a fixed-weight (equal) average of 12
   wealth processes on ``X = -D - h`` (bound ``1 + h``), one per trigger length ``r`` in {1,2,3,4}
   and stake ``lambda`` in {0.3, 0.6, 0.9}. Component ``(r, lambda)`` bets ``lambda`` when the last
   ``r`` released labels of the episode were all favourable (``X > 0``) and nothing otherwise. The
   stake depends on the past only, lies in [0, 1), and the weights are fixed before data, so each
   wealth is a nonnegative supermartingale under ``E[X_t | F_{t-1}] <= 0`` and their (equal-weight)
   average is an e-process; there is no start mixture. Same heuristic caveats as item 4. Predictable
   plug-in betting is established; no novelty is claimed.
6. ``discount`` memory is only admitted on non-evidence statistics (economic benefit
   estimate, hysteresis window). Discounting the evidence itself breaks the supermartingale
   argument and is rejected when the evidence is an e-process/e-detector. ``window_mean``
   evidence carries no validity guarantee and is never safety-gated.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, replace
from typing import Any

import numpy as np
from scipy.special import logsumexp

from shiftlab.dive.eprocess import (
    MultiTimescaleStartedKellyEProcess,
    VectorizedStartedMixtureEProcess,
)
from shiftlab.dive.horizon_edetectors import HorizonCalibratedEDetector
from shiftlab.dive.switching_explore import (
    Method,
    Released,
    started_gate,
    uniform_calendar,
)

SLOTS = ("acquisition", "evidence", "memory", "decision")


@dataclass(frozen=True)
class ParamSpec:
    default: Any
    lo: float | None = None
    hi: float | None = None
    kind: str = "float"  # float | int | str
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class ComponentInfo:
    name: str
    params: dict[str, ParamSpec] = field(default_factory=dict)
    doc: str = ""


def _c(name: str, doc: str, **params: ParamSpec) -> ComponentInfo:
    return ComponentInfo(name, dict(params), doc)


REGISTRY: dict[str, dict[str, ComponentInfo]] = {
    "acquisition": {
        c.name: c
        for c in (
            _c("uniform", "Calendar of B nearly equally spaced releasable rounds (B/T pace)."),
            _c("bernoulli_pacing", "Query each round independently with probability B/T."),
            _c(
                "reserve_pacing",
                "Allowance = (remaining budget - decaying reserve)/remaining rounds.",
                reserve_frac=ParamSpec(0.2, 0.05, 0.9),
            ),
            _c(
                "straddle",
                "Query while evidence is undecided; pacing cap and pending cap.",
                margin=ParamSpec(0.15, 0.01, 0.5),
                burst_frac=ParamSpec(0.1, 0.0, 0.5),
                pending_cap=ParamSpec(2, 1, 2, "int"),
                keepalive_mult=ParamSpec(4.0, 1.0, 16.0),
            ),
        )
    },
    "evidence": {
        c.name: c
        for c in (
            _c("started_mixture_eprocess", "Repository started-mixture e-process (gated)."),
            _c("horizon_cusum", "Finite-horizon CUSUM e-detector, horizon = B (gated)."),
            _c(
                "window_mean",
                "Mean of last max(3,B/8) labels above h + margin (NOT safety-gated).",
                margin=ParamSpec(0.1, 0.0, 0.5),
            ),
            _c(
                "started_kelly",
                "Repository multi-timescale started e-process with predictable discounted Kelly "
                "stakes (gated).",
            ),
            _c(
                "weighted_starts",
                "Started mixture with start weights fixed from the declared family onset levels "
                "plus a uniform floor (gated).",
            ),
            _c(
                "wide_stakes",
                "Started mixture whose stake grid extends to 0.9 and 0.95 (gated).",
            ),
            _c(
                "triggered_kelly",
                "Equal-weight average of history-triggered bettors, r in {1..4} x lambda in "
                "{0.3,0.6,0.9}, no start mixture (gated; Amendment 3).",
            ),
        )
    },
    "memory": {
        c.name: c
        for c in (
            _c("none", "Episode-local statistics; fresh evidence episode after rollback."),
            _c(
                "discount",
                "Exponentially discounted non-evidence statistics.",
                gamma=ParamSpec(0.9, 0.5, 0.99),
                scope=ParamSpec("stats", kind="str", choices=("stats", "evidence")),
            ),
            _c(
                "restart_on_rollback",
                "After rollback, spend a re-evaluation burst of queries.",
                burst_frac=ParamSpec(0.1, 0.01, 0.5),
            ),
        )
    },
    "decision": {
        c.name: c
        for c in (
            _c(
                "certificate_econ",
                "Promote when evidence rejects AND econ check passes; no rollback.",
                econ_mult=ParamSpec(1.0, 0.25, 10.0),
            ),
            _c(
                "hysteresis",
                "Promote after k consecutive confirmations; roll back after k failing windows.",
                k=ParamSpec(2, 1, 10, "int"),
                econ_mult=ParamSpec(1.0, 0.25, 10.0),
            ),
            _c(
                "rollback_monitor",
                "certificate_econ promotion; Page CUSUM on D after promotion (threshold kappa).",
                kappa=ParamSpec(2.0, 0.1, 20.0),
                econ_mult=ParamSpec(1.0, 0.25, 10.0),
            ),
        )
    },
}

DEFAULTS = {
    "acquisition": "uniform",
    "evidence": "started_mixture_eprocess",
    "memory": "none",
    "decision": "certificate_econ",
}
E_EVIDENCE = frozenset(
    {
        "started_mixture_eprocess",
        "horizon_cusum",
        "started_kelly",
        "weighted_starts",
        "wide_stakes",
        "triggered_kelly",
    }
)
TRIGGER_LENGTHS = (1, 2, 3, 4)
TRIGGER_STAKES = (0.3, 0.6, 0.9)
ONSET_LEVELS = (0.1, 0.3, 0.6, 0.8)  # declared family onset levels (fractions of T)
ONSET_JITTER = 0.05
START_FLOOR = 0.25  # uniform floor of the start weights (>= 0.2 required)
WIDE_STAKES = (0.05, 0.1, 0.2, 0.4, 0.8, 0.9, 0.95)
ROLLBACK_DECISIONS = frozenset({"hysteresis", "rollback_monitor"})
FOCUS_KEY = "g.focus"


def _norm_value(spec: ParamSpec, v: Any) -> Any:
    if spec.kind == "int":
        return int(v)
    if spec.kind == "str":
        return str(v)
    return float(v)


@dataclass(frozen=True)
class CandidateSpec:
    acquisition: str
    evidence: str
    memory: str
    decision: str
    params: Any = ()  # dict or tuple of (key, value); normalised to a sorted tuple
    hypothesis: str = ""

    def __post_init__(self) -> None:
        raw = dict(self.params)
        for slot in SLOTS:
            info = REGISTRY[slot].get(getattr(self, slot))
            if info is None:
                continue
            for pname, ps in info.params.items():
                raw.setdefault(f"{slot}.{pname}", ps.default)
        norm = {}
        for key, v in raw.items():
            slot, _, pname = key.partition(".")
            info = REGISTRY.get(slot, {}).get(getattr(self, slot, None)) if slot in SLOTS else None
            ps = info.params.get(pname) if info else None
            try:
                norm[key] = _norm_value(ps, v) if ps else v
            except (TypeError, ValueError):
                norm[key] = v  # left for validate_spec to reject
        object.__setattr__(self, "params", tuple(sorted(norm.items())))

    def get(self, slot: str, name: str) -> Any:
        return dict(self.params)[f"{slot}.{name}"]

    @property
    def focus(self) -> str | None:
        return dict(self.params).get(FOCUS_KEY)

    @property
    def spec_id(self) -> str:
        """Stable hash of components and params (the hypothesis text is excluded)."""
        payload = json.dumps(
            [self.acquisition, self.evidence, self.memory, self.decision, list(self.params)],
            sort_keys=True,
            default=repr,
        )
        return hashlib.sha1(payload.encode()).hexdigest()[:12]

    @property
    def is_safety_gated(self) -> bool:
        """True iff promotion passes through an e-process/e-detector with episode alpha-spending.

        See the module docstring: heuristic validity, not a proven guarantee. Discounting
        applied to the evidence (rejected by ``validate_spec``) would void the property.
        """
        pd = dict(self.params)
        discounted_evidence = (
            self.memory == "discount" and pd.get("memory.scope", "stats") == "evidence"
        )
        return self.evidence in E_EVIDENCE and not discounted_evidence


def default_spec() -> CandidateSpec:
    """Close to the strongest gated baseline: C2 style (uniform + e-process + rollback CUSUM)."""
    return CandidateSpec(
        "uniform",
        "started_mixture_eprocess",
        "none",
        "rollback_monitor",
        {"decision.kappa": 2.0},
        "Baseline: uniform spending, alpha-spent started-mixture gate, Page-CUSUM rollback.",
    )


def validate_spec(spec: CandidateSpec) -> tuple[bool, list[str]]:
    """Typing and compatibility rules. Returns ``(ok, reasons)``; invalid specs are never repaired."""
    why: list[str] = []
    for slot in SLOTS:
        if getattr(spec, slot) not in REGISTRY[slot]:
            why.append(f"unknown {slot} component {getattr(spec, slot)!r}")
    if why:
        return False, why
    if not spec.hypothesis.strip():
        why.append("missing mechanistic hypothesis")
    for key, v in spec.params:
        slot, _, pname = key.partition(".")
        if slot == "g":
            if pname != "focus" or v not in SLOTS:
                why.append(f"bad global param {key}={v!r}")
            continue
        if slot not in SLOTS:
            why.append(f"unknown param key {key!r}")
            continue
        comp = getattr(spec, slot)
        ps = REGISTRY[slot][comp].params.get(pname)
        if ps is None:
            why.append(f"param {key!r} not accepted by {slot} component {comp!r}")
            continue
        if ps.kind == "str":
            if v not in ps.choices:
                why.append(f"{key}={v!r} not in {ps.choices}")
        elif not isinstance(v, (int, float)) or not math.isfinite(v):
            why.append(f"{key}={v!r} is not a finite number")
        elif (ps.lo is not None and v < ps.lo) or (ps.hi is not None and v > ps.hi):
            why.append(f"{key}={v} outside [{ps.lo}, {ps.hi}]")
    if why:
        return False, why
    if spec.memory == "restart_on_rollback" and spec.decision not in ROLLBACK_DECISIONS:
        why.append(
            "restart_on_rollback needs a decision that can roll back "
            "(hysteresis or rollback_monitor); certificate_econ never rolls back"
        )
    if (
        spec.memory == "discount"
        and spec.get("memory", "scope") == "evidence"
        and spec.evidence in E_EVIDENCE
    ):
        why.append(
            "discounting the evidence itself breaks the supermartingale validity argument; "
            "discount may only act on non-evidence statistics (memory.scope='stats')"
        )
    if (
        spec.memory == "discount"
        and spec.get("memory", "scope") == "evidence"
        and spec.evidence not in E_EVIDENCE
        and spec.evidence != "window_mean"
    ):
        why.append("discount scope 'evidence' has no evidence object to act on")
    return (not why), why


def ablation_of(spec: CandidateSpec, slot: str) -> CandidateSpec:
    """Same spec with ``slot`` replaced by its default component (params reset to defaults).

    Raises if the slot already holds the default component with default params. The result
    is not silently repaired: callers should run ``validate_spec`` on it.
    """
    if slot not in SLOTS:
        raise ValueError(f"unknown slot {slot!r}")
    kept = {k: v for k, v in spec.params if not k.startswith(slot + ".")}
    new = replace(
        spec,
        params=kept,
        hypothesis=f"Ablation of {slot} ({getattr(spec, slot)} -> {DEFAULTS[slot]}): "
        + spec.hypothesis,
        **{slot: DEFAULTS[slot]},
    )
    if differing_slots(new, spec) == ():
        raise ValueError(f"{slot} already default in {spec.spec_id}")
    return new


def differing_slots(a: CandidateSpec, b: CandidateSpec) -> tuple[str, ...]:
    """Slots whose component name or slot-prefixed params differ (``g.*`` params ignored)."""
    pa, pb = dict(a.params), dict(b.params)
    out = []
    for slot in SLOTS:
        sa = {k: v for k, v in pa.items() if k.startswith(slot + ".")}
        sb = {k: v for k, v in pb.items() if k.startswith(slot + ".")}
        if getattr(a, slot) != getattr(b, slot) or sa != sb:
            out.append(slot)
    return tuple(out)


# ----------------------------------------------------------------------------- the method


def with_stakes(proc: VectorizedStartedMixtureEProcess, stakes) -> VectorizedStartedMixtureEProcess:
    """Set a stake grid on this instance (uniform stake weights, fixed before data)."""
    st = np.asarray(stakes, dtype=float)
    if st.ndim != 1 or not len(st) or np.any(st < 0) or np.any(st >= 1):
        raise ValueError("stakes must lie in [0, 1)")
    proc.stakes = st
    proc.stake_weights = np.full(len(st), 1.0 / len(st))
    proc.log_stake_weights = np.log(proc.stake_weights)
    proc.log_wealth = np.zeros((len(proc.starts), len(st)), dtype=float)
    return proc


def wide_stakes_gate(bound: float, alpha: float, n_labels: int) -> VectorizedStartedMixtureEProcess:
    """``started_gate`` with the stake grid extended to 0.9 and 0.95 (instance-level change)."""
    return with_stakes(started_gate(bound, alpha, n_labels), WIDE_STAKES)


def expected_queries_by_round(acquisition: str, cfg, reserve_frac: float = 0.2) -> np.ndarray:
    """Data-independent expected cumulative number of queries issued through round t (index t-1).

    ``uniform``: the calendar. ``bernoulli_pacing``: B/T per releasable round. ``reserve_pacing``:
    the deterministic credit recursion of the method. ``straddle`` is data dependent, so the
    uniform pace B t / (T - d) is used as its declared approximation.
    """
    T, B, d = cfg.T, cfg.B, cfg.d
    if acquisition == "uniform":
        cal = uniform_calendar(T, B, d)
        return np.cumsum([1.0 if t in cal else 0.0 for t in range(1, T + 1)])
    if acquisition == "bernoulli_pacing":
        per = np.array([B / T if t + d <= T else 0.0 for t in range(1, T + 1)])
        return np.minimum(np.cumsum(per), B)
    if acquisition == "reserve_pacing":
        out, used, credit = np.zeros(T), 0, 0.0
        for t in range(1, T + 1):
            rr = T - d - t + 1
            if rr > 0 and used < B:
                reserve_now = reserve_frac * B * rr / max(1, T - d)
                credit += max(0.0, (B - used) - reserve_now) / rr
                if credit >= 1.0:
                    credit -= 1.0
                    used += 1
            out[t - 1] = used
        return out
    return np.minimum(B * np.arange(1, T + 1) / max(1, T - d), B)  # straddle: uniform pace


def weighted_start_design(
    acquisition: str,
    cfg,
    reserve_frac: float = 0.2,
    levels: tuple[float, ...] = ONSET_LEVELS,
    jitter: float = ONSET_JITTER,
    floor: float = START_FLOOR,
) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Fixed (before data) start positions and weights for ``weighted_starts``.

    Start positions are label indices: the repository grid plus the label index at which each
    declared onset level (fraction of T) falls under the acquisition schedule's expected label
    count. A mass ``1 - floor`` is split equally over the levels and, within a level, over the
    starts within ``jitter * B`` labels of it; ``floor`` is spread uniformly over all starts.
    """
    if not 0.2 <= floor < 1.0:
        raise ValueError("uniform floor must be at least 0.2 and below 1")
    B = cfg.B
    cum = expected_queries_by_round(acquisition, cfg, reserve_frac)
    centers = []
    for f in levels:
        r = int(np.clip(round(f * cfg.T), 1, cfg.T))
        k = cum[r - 2] if r >= 2 else 0.0  # queries issued strictly before the onset round
        centers.append(int(np.clip(round(float(k)), 0, max(0, B - 1))))
    step = max(1, B // 32)
    starts = tuple(sorted(set(range(0, max(1, B), step)) | set(centers)))
    w = np.full(len(starts), floor / len(starts))
    arr = np.asarray(starts)
    for k in centers:
        near = np.abs(arr - k) <= jitter * B
        near[int(np.flatnonzero(arr == k)[0])] = True
        w[near] += (1.0 - floor) / len(centers) / near.sum()
    w = w / w.sum()
    return starts, tuple(float(x) for x in w)


class TriggeredKellyEProcess:
    """Equal-weight average of history-triggered bettors on ``X in [-bound, bound]``.

    Component ``(r, lam)`` stakes ``lam`` iff the last ``r`` observed ``X`` of this process were all
    positive (stake is a function of the past only) and ``0`` otherwise; wealth is multiplied by
    ``1 + stake * X / bound``. The reported e-value is the equal-weight *average* of the wealths.
    """

    def __init__(self, *, bound: float, alpha: float):
        if not np.isfinite(bound) or bound <= 0 or not 0 < alpha < 1:
            raise ValueError("bound must be positive and alpha in (0, 1)")
        self.bound, self.alpha = float(bound), float(alpha)
        self.r = np.repeat(np.asarray(TRIGGER_LENGTHS), len(TRIGGER_STAKES))
        self.lam = np.tile(np.asarray(TRIGGER_STAKES, dtype=float), len(TRIGGER_LENGTHS))
        self.log_w = np.zeros(len(self.r))
        self.streak = 0  # number of consecutive favourable (X > 0) observations so far
        self.time = 0

    @property
    def log_e_value(self) -> float:
        return float(logsumexp(self.log_w) - math.log(len(self.log_w)))

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -math.log(self.alpha)

    def update(self, value: float) -> float:
        if not np.isfinite(value) or abs(value) > self.bound + 1e-12:
            raise ValueError("observed value is outside the declared bounded range")
        stake = np.where(self.streak >= self.r, self.lam, 0.0)  # decided before seeing ``value``
        self.log_w = self.log_w + np.log1p(stake * (value / self.bound))
        self.streak = self.streak + 1 if value > 0 else 0
        self.time += 1
        return self.log_e_value


class _Evidence:
    """Uniform wrapper: ``update(x)`` consumes D, tests E[-D] > h; ``alarm`` flag."""

    def __init__(
        self,
        kind: str,
        cfg,
        alpha_j: float,
        m: int,
        margin: float,
        design: tuple[tuple[int, ...], tuple[float, ...]] | None = None,
    ):
        self.kind, self.cfg, self.m, self.margin = kind, cfg, m, margin
        self.xs: list[float] = []
        self.proc = None
        bound = 1.0 + cfg.h
        if kind == "started_mixture_eprocess":
            self.proc = started_gate(bound, alpha_j, cfg.B)
        elif kind == "started_kelly":
            step = max(1, cfg.B // 32)
            self.proc = MultiTimescaleStartedKellyEProcess(
                bound=bound, alpha=alpha_j, starts=tuple(range(0, max(1, cfg.B), step))
            )
        elif kind == "weighted_starts":
            if design is None:
                self.proc = started_gate(bound, alpha_j, cfg.B)  # later episodes: uniform starts
            else:
                self.proc = VectorizedStartedMixtureEProcess(
                    bound=bound, alpha=alpha_j, starts=design[0], weights=design[1]
                )
        elif kind == "wide_stakes":
            self.proc = wide_stakes_gate(bound, alpha_j, cfg.B)
        elif kind == "triggered_kelly":
            self.proc = TriggeredKellyEProcess(bound=bound, alpha=alpha_j)
        elif kind == "horizon_cusum":
            self.proc = HorizonCalibratedEDetector(
                bound=bound, horizon=max(1, cfg.B), alpha=alpha_j, kind="cusum"
            )

    def update(self, x: float) -> None:
        self.xs.append(x)
        if self.proc is None:
            return
        if self.kind == "horizon_cusum" and self.proc.n_updates >= self.proc.horizon:
            return
        self.proc.update(-x - self.cfg.h)

    @property
    def alarm(self) -> bool:
        if self.proc is not None:
            return bool(self.proc.alarm)
        if len(self.xs) < self.m:
            return False
        return -float(np.mean(self.xs[-self.m :])) > self.cfg.h + self.margin


class ComposedMethod(Method):
    """Runs a validated :class:`CandidateSpec` as a ``switching_explore.Method``."""

    def __init__(self, spec: CandidateSpec):
        ok, why = validate_spec(spec)
        if not ok:
            raise ValueError(f"invalid spec {spec.spec_id}: {'; '.join(why)}")
        self.spec = spec
        self.name = f"atlas_{spec.spec_id}"

    # parameters ---------------------------------------------------------------------
    def _p(self, slot: str, name: str) -> Any:
        return self.spec.get(slot, name)

    def _alpha_j(self, j: int) -> float:
        a = self.cfg.alpha
        return a * 2.0 ** -(j + 1) if self.spec.decision in ROLLBACK_DECISIONS else a

    def _new_episode(self, j: int, start: int) -> None:
        self.j, self.ep_start = j, start
        self.ep = _Evidence(
            self.spec.evidence,
            self.cfg,
            self._alpha_j(j),
            self.m,
            self._p("evidence", "margin") if self.spec.evidence == "window_mean" else 0.0,
            design=self.design if j == 0 else None,
        )
        self.ep_labels: list[float] = []

    def _init(self) -> None:
        c, s = self.cfg, self.spec
        self.m = max(3, c.B // 8)
        self.act = 0
        self.promo_t = 0
        self.post: list[float] = []
        self.cus = 0.0
        self.ref = 0.0
        self.streak = 0
        self.rb_streak = 0
        self.burst_left = 0
        self.credit = 0.0
        self.cal = uniform_calendar(c.T, c.B, c.d) if s.acquisition == "uniform" else frozenset()
        self.rng = np.random.default_rng([c.seed, 778])
        self.design = None
        if s.evidence == "weighted_starts":  # fixed from the config and the schedule, not data
            rf = (
                self._p("acquisition", "reserve_frac") if s.acquisition == "reserve_pacing" else 0.2
            )
            self.design = weighted_start_design(s.acquisition, c, rf)
        if s.acquisition == "straddle":
            self.keepalive = max(
                c.d + 1, math.ceil(self._p("acquisition", "keepalive_mult") * c.T / max(c.B, 1))
            )
        self._new_episode(0, 0)

    # statistics (non-evidence; the only place discounting acts) ---------------------
    def _ben(self, xs: list[float], n: int) -> float | None:
        if not xs:
            return None
        if self.spec.memory == "discount":
            g = self._p("memory", "gamma")
            w = g ** np.arange(len(xs) - 1, -1, -1)
            return -float(np.sum(w * np.asarray(xs)) / np.sum(w))
        return -float(np.mean(xs[-n:]))

    def _econ(self, t: int, ben: float) -> bool:
        mult = self._p("decision", "econ_mult")
        return (self.cfg.T - t + 1) * ben > mult * self.cfg.s

    # decision -----------------------------------------------------------------------
    def decide(self, t: int, released: Released) -> tuple[int, bool]:
        c, s = self.cfg, self.spec
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start:
                    self.ep.update(x)
                    self.ep_labels.append(x)
            elif ev >= self.promo_t:
                self.post.append(x)
                self.cus = max(0.0, self.cus + x - self.ref)
        k = self._p("decision", "k") if s.decision == "hysteresis" else 1
        if self.act == 0:
            ben = self._ben(self.ep_labels, 10)
            cond = bool(self.ep.alarm and ben is not None and self._econ(t, ben))
            if released:
                self.streak = self.streak + 1 if cond else 0
            if cond and (k == 1 or self.streak >= k):
                self.act, self.promo_t, self.post, self.cus = 1, t, [], 0.0
                self.ref = (-float(ben) - c.h) / 2.0
                self.rb_streak = 0
        else:
            rollback = False
            if s.decision == "rollback_monitor":
                rollback = self.cus >= self._p("decision", "kappa")
            elif s.decision == "hysteresis":
                if released:
                    pb = self._ben(self.post, self.m)
                    bad = len(self.post) >= 3 and pb is not None and pb <= c.h
                    self.rb_streak = self.rb_streak + 1 if bad else 0
                rollback = self.rb_streak >= k
            if rollback:
                self.act, self.cus, self.streak, self.rb_streak = 0, 0.0, 0, 0
                self._new_episode(self.j + 1, t)
                if s.memory == "restart_on_rollback":
                    self.burst_left = max(1, math.ceil(self._p("memory", "burst_frac") * c.B))
        return self.act, self._query(t)

    # acquisition --------------------------------------------------------------------
    def _query(self, t: int) -> bool:
        c, s = self.cfg, self.spec
        if self.burst_left > 0 and len(self.pending_events) < 2 and self.can_query(t):
            self.burst_left -= 1
            return True
        if s.acquisition == "uniform":
            return t in self.cal
        if s.acquisition == "bernoulli_pacing":
            return bool(self.rng.random() < c.B / c.T)
        rr = c.T - c.d - t + 1
        if s.acquisition == "reserve_pacing":
            if rr <= 0:
                return False
            reserve_now = self._p("acquisition", "reserve_frac") * c.B * rr / max(1, c.T - c.d)
            eff = max(0.0, (c.B - self.used) - reserve_now)
            self.credit += eff / rr
            if self.credit >= 1.0:
                self.credit -= 1.0
                return True
            return False
        # straddle
        margin = self._p("acquisition", "margin")
        if self.act == 0:
            ben = self._ben(self.ep_labels, self.m)
            if ben is None:
                undecided = True
            elif self.ep.alarm:
                undecided = False
            else:
                undecided = ben > c.h - margin
        else:
            ben = self._ben(self.post, self.m)
            undecided = ben is None or ben < c.h + margin
        keep = t - self.last_query >= self.keepalive
        cap = max(1, math.ceil(self._p("acquisition", "burst_frac") * c.B)) + math.floor(
            2 * c.B * t / c.T
        )
        return bool(
            (undecided or keep)
            and self.used < cap
            and len(self.pending_events) < self._p("acquisition", "pending_cap")
        )


def build_candidate(spec: CandidateSpec) -> ComposedMethod:
    return ComposedMethod(spec)


# ----------------------------------------------------------------------------- proposals


def _mk(
    focus: str,
    hyp: str,
    acq="uniform",
    evi="started_mixture_eprocess",
    mem="none",
    dec="rollback_monitor",
    **params: Any,
) -> CandidateSpec:
    p = {"decision.kappa": 2.0} if dec == "rollback_monitor" else {}
    p.update({k.replace("__", "."): v for k, v in params.items()})
    p[FOCUS_KEY] = focus
    return CandidateSpec(acq, evi, mem, dec, p, hyp)


def _evidence_specs() -> list[CandidateSpec]:
    """Amendment 1 evidence components, combined with acquisition and decision variants."""
    E = "evidence"
    return [
        _mk(
            E,
            "Uniform start weights waste mass on starts far from any plausible onset; fixed "
            "weights around the declared onset levels cut the log(#starts) price of a late onset.",
            evi="weighted_starts",
        ),
        _mk(
            E,
            "Predictable discounted Kelly stakes track the effect size, avoiding the stake-grid "
            "dilution of the fixed-stake mixture.",
            evi="started_kelly",
        ),
        _mk(
            E,
            "Stakes up to 0.95 give near-Kelly growth for strong effects, which the 0.8 cap "
            "gives up.",
            evi="wide_stakes",
        ),
        _mk(
            E,
            "Onset-informed start weights plus a decaying reserve keep labels for a late onset "
            "and place start mass where the reserve will be spent.",
            acq="reserve_pacing",
            evi="weighted_starts",
            acquisition__reserve_frac=0.2,
        ),
        _mk(
            E,
            "Onset-informed start weights with undecided-only straddle queries.",
            acq="straddle",
            evi="weighted_starts",
        ),
        _mk(
            E,
            "Kelly stakes with straddle queries concentrate labels where the bet is undecided.",
            acq="straddle",
            evi="started_kelly",
        ),
        _mk(
            E,
            "Kelly stakes with a decaying reserve keep budget for the late regime.",
            acq="reserve_pacing",
            evi="started_kelly",
            acquisition__reserve_frac=0.2,
        ),
        _mk(
            E,
            "Wide stakes with a decaying reserve: near-Kelly growth on the labels that arrive "
            "after a late onset.",
            acq="reserve_pacing",
            evi="wide_stakes",
            acquisition__reserve_frac=0.2,
        ),
        _mk(
            E,
            "Onset-informed starts with k=2 hysteresis separate a real regime from a single "
            "lucky streak.",
            evi="weighted_starts",
            dec="hysteresis",
            decision__k=2,
        ),
        _mk(
            E,
            "Kelly stakes with k=2 hysteresis.",
            evi="started_kelly",
            dec="hysteresis",
            decision__k=2,
        ),
        _mk(
            E,
            "Wide stakes with k=2 hysteresis.",
            evi="wide_stakes",
            dec="hysteresis",
            decision__k=2,
        ),
        _mk(
            E,
            "Onset-informed starts promote as soon as evidence rejects when the economic margin "
            "is halved and there is no rollback.",
            evi="weighted_starts",
            dec="certificate_econ",
            decision__econ_mult=0.5,
        ),
    ]


def _triggered_specs() -> list[CandidateSpec]:
    """Amendment 3: proposed for every axis; the ablation partner swaps in the started mixture."""
    E = "evidence"
    return [
        _mk(
            E,
            "Adapting the stake quickly from the last r released labels avoids paying the "
            "start-multiplicity penalty when pre-onset data are informative (harmful off state); "
            "predicts gains in harmful-off cells and none in neutral-off cells.",
            evi="triggered_kelly",
        ),
        _mk(
            E,
            "History-triggered bettor with k=2 hysteresis (as above, harder to fool by one run).",
            evi="triggered_kelly",
            dec="hysteresis",
            decision__k=2,
        ),
    ]


def _axis_specs(axis: str) -> list[CandidateSpec]:
    A, E, M, D = "acquisition", "evidence", "memory", "decision"
    if axis == "rate":
        return [
            _mk(
                M,
                "Recurrent regimes: a re-evaluation burst after each rollback restores information "
                "at the moment the old evidence is discarded.",
                mem="restart_on_rollback",
            ),
            _mk(
                D,
                "A tighter Page-CUSUM rollback (kappa=1.5) leaves an off phase sooner under fast "
                "switching.",
                dec="rollback_monitor",
                decision__kappa=1.5,
            ),
            _mk(
                D,
                "A looser rollback (kappa=3) avoids reverting on noise during slow regimes.",
                dec="rollback_monitor",
                decision__kappa=3.0,
            ),
            _mk(
                M,
                "Restart burst with a decaying reserve keeps budget for the next on phase.",
                acq="reserve_pacing",
                mem="restart_on_rollback",
                acquisition__reserve_frac=0.2,
            ),
            _mk(
                E,
                "A history-triggered bettor with rollback restarts quickly in each episode.",
                evi="triggered_kelly",
                mem="restart_on_rollback",
            ),
        ]
    if axis == "d":
        return [
            _mk(
                A,
                "Under delay uniform spending queries rounds whose labels arrive too late to matter; "
                "front-loaded straddle queries (pending cap 2) buy information while evidence is undecided.",
                acq="straddle",
                acquisition__burst_frac=0.3,
            ),
            _mk(
                A,
                "Querying only while the promotion/rollback call is undecided avoids paying for "
                "labels that arrive after the decision is already clear.",
                acq="straddle",
            ),
            _mk(
                E,
                "A CUSUM e-detector re-opens a start at every label and recovers faster from stale "
                "pre-onset labels, which delay makes more frequent.",
                acq="straddle",
                evi="horizon_cusum",
            ),
            _mk(
                A,
                "A decaying reserve keeps budget for rounds after the delay window instead of "
                "spending it on labels that cannot be released in time.",
                acq="reserve_pacing",
                acquisition__reserve_frac=0.2,
            ),
            _mk(
                D,
                "Delayed labels make the rollback monitor see stale evidence; requiring k consecutive "
                "confirmations avoids flip-flop on stale labels.",
                dec="hysteresis",
                decision__k=2,
            ),
            _mk(
                E,
                "Window-mean evidence reacts without waiting for an e-process to accumulate under "
                "delay (contrast only, not safety-gated).",
                acq="straddle",
                evi="window_mean",
            ),
        ]
    if axis == "budget_frac":
        return [
            _mk(
                A,
                "Keeping 20% of budget in a decaying reserve prevents early exhaustion before a "
                "later onset.",
                acq="reserve_pacing",
                acquisition__reserve_frac=0.2,
            ),
            _mk(
                A,
                "A 40% reserve protects late-onset detection when the budget is scarce.",
                acq="reserve_pacing",
                acquisition__reserve_frac=0.4,
            ),
            _mk(
                M,
                "With a scarce budget a post-rollback re-evaluation burst taken from the reserve "
                "restores information at the moment the old evidence is discarded.",
                acq="reserve_pacing",
                mem="restart_on_rollback",
                acquisition__reserve_frac=0.4,
            ),
            _mk(
                A,
                "Spending only while undecided (burst 0.2) saves scarce queries for undecided phases.",
                acq="straddle",
                acquisition__burst_frac=0.2,
            ),
            _mk(
                E,
                "With few labels a CUSUM e-detector with horizon B uses each label more "
                "aggressively than the started mixture.",
                acq="straddle",
                evi="horizon_cusum",
            ),
            _mk(
                A,
                "Pacing capped at pending 1 avoids spending the scarce budget on overlapping "
                "in-flight queries.",
                acq="straddle",
                acquisition__pending_cap=1,
            ),
        ]
    if axis == "s":
        return [
            _mk(
                D,
                "Requiring k=2 consecutive confirmations before switching cuts costly flip-flops.",
                dec="hysteresis",
                decision__k=2,
            ),
            _mk(
                D,
                "k=3 confirmations further reduces switching under high switch cost.",
                dec="hysteresis",
                decision__k=3,
            ),
            _mk(
                D,
                "Doubling the economic margin stops promotions whose remaining-horizon gain barely "
                "covers the switch cost.",
                dec="certificate_econ",
                decision__econ_mult=2.0,
            ),
            _mk(
                D,
                "Tripling the economic margin trades promotions for fewer wasted switches.",
                dec="certificate_econ",
                decision__econ_mult=3.0,
            ),
            _mk(
                D,
                "A looser rollback threshold (kappa=3) avoids rollback churn that costs switches.",
                dec="rollback_monitor",
                decision__kappa=3.0,
            ),
            _mk(
                D,
                "Hysteresis combined with straddle queries confirms only when undecided.",
                acq="straddle",
                dec="hysteresis",
                decision__k=2,
                decision__econ_mult=1.5,
            ),
        ]
    if axis == "effect":
        return [
            _mk(
                E,
                "For strong effects a CUSUM e-detector crosses its horizon threshold sooner than the "
                "started mixture.",
                evi="horizon_cusum",
            ),
            _mk(
                E,
                "CUSUM evidence plus straddle queries concentrates labels where the effect is "
                "visible.",
                acq="straddle",
                evi="horizon_cusum",
            ),
            _mk(
                A,
                "For weak effects, spending queries while undecided accumulates evidence where the "
                "mixture is close to threshold.",
                acq="straddle",
            ),
            _mk(
                E,
                "A window-mean test reacts to moderate effects the e-process cannot yet certify "
                "(contrast only, not safety-gated).",
                evi="window_mean",
            ),
            _mk(
                E,
                "CUSUM evidence with rollback hysteresis separates a real effect from noise.",
                evi="horizon_cusum",
                dec="hysteresis",
                decision__k=2,
            ),
        ]
    if axis == "onset":
        return [*_evidence_specs(), *_duration_onset_specs()]
    if axis == "duration":
        return _duration_onset_specs()
    return [
        _mk(
            "acquisition", "Querying while undecided adapts spend to the evidence.", acq="straddle"
        ),
        _mk(
            "evidence",
            "CUSUM e-detector may detect faster than the started mixture.",
            evi="horizon_cusum",
        ),
        _mk(
            "acquisition",
            "A decaying 20% reserve guards against early budget exhaustion.",
            acq="reserve_pacing",
            acquisition__reserve_frac=0.2,
        ),
        _mk(
            "memory",
            "A post-rollback burst restores information after regime change.",
            mem="restart_on_rollback",
        ),
        *_evidence_specs(),
    ]


def _duration_onset_specs() -> list[CandidateSpec]:
    A, _E, M, D = "acquisition", "evidence", "memory", "decision"
    return [
        _mk(
            M,
            "A re-evaluation burst after rollback recovers information when a new regime starts "
            "later than the uniform calendar would sample it.",
            mem="restart_on_rollback",
        ),
        _mk(
            M,
            "Restart burst plus decaying reserve keeps budget for the next onset.",
            acq="reserve_pacing",
            mem="restart_on_rollback",
            acquisition__reserve_frac=0.2,
        ),
        _mk(
            D,
            "A tighter rollback threshold (kappa=1.5) reverts sooner when a short-lived regime "
            "ends.",
            dec="rollback_monitor",
            decision__kappa=1.5,
        ),
        _mk(
            D,
            "A looser rollback threshold (kappa=3) avoids reverting on noise during long regimes.",
            dec="rollback_monitor",
            decision__kappa=3.0,
        ),
        _mk(
            A,
            "A 40% decaying reserve preserves budget for onsets late in the horizon.",
            acq="reserve_pacing",
            acquisition__reserve_frac=0.4,
        ),
        _mk(
            M,
            "Discounted benefit statistics forget stale labels when regimes are short "
            "(evidence untouched).",
            mem="discount",
            memory__gamma=0.9,
        ),
        _mk(
            M,
            "Straddle queries plus restart bursts concentrate labels near transitions.",
            acq="straddle",
            mem="restart_on_rollback",
        ),
        _mk(
            M,
            "CUSUM evidence restarts quickly after a rollback.",
            evi="horizon_cusum",
            mem="restart_on_rollback",
            memory__burst_frac=0.2,
        ),
    ]


def propose_candidates(mechanism_axis: str, max_n: int = 40) -> list[CandidateSpec]:
    """Failure-conditioned proposals for an isolated axis, each followed by its ablation partner.

    Axes: 'd', 'budget_frac', 's', 'effect', 'duration', 'onset', 'rate'; anything else gets a
    small default set. Specs are deduplicated by ``spec_id``; invalid ones are kept so the
    archive records the rejection (callers filter with ``validate_spec``).
    """
    out: list[CandidateSpec] = []
    seen: set[str] = set()

    def add(sp: CandidateSpec) -> None:
        if sp.spec_id not in seen:
            seen.add(sp.spec_id)
            out.append(sp)

    for sp in [*_triggered_specs(), *_axis_specs(mechanism_axis)]:
        if len(out) >= max_n:
            break
        add(sp)
        if sp.focus is not None and len(out) < max_n:
            add(ablation_of(sp, sp.focus))
    return out[:max_n]


__all__ = [
    "DEFAULTS",
    "REGISTRY",
    "SLOTS",
    "WIDE_STAKES",
    "CandidateSpec",
    "ComposedMethod",
    "TriggeredKellyEProcess",
    "ablation_of",
    "build_candidate",
    "default_spec",
    "differing_slots",
    "propose_candidates",
    "validate_spec",
    "weighted_start_design",
    "wide_stakes_gate",
    "with_stakes",
]
