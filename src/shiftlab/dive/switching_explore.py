"""Exploratory shared harness for C1/C2 switching prototypes (R4: development only).

Protocol: docs/switching_c1_c2_exploratory_protocol_v1.md. Nothing here is a novelty,
theorem or efficacy claim. Event order inside round ``t``: labels due at ``t`` are
released, the method picks ``(action, query)`` from released information only, then the
outcome is realized. The paired difference ``D_t = loss1_t - loss0_t`` is shown to a method
only if it queried round ``t`` and only at round ``t + d``. Budget is counted at request
time (pending queries included) and a request over budget raises ``BudgetExceeded``.
Oracle truth lives only in :class:`Truth`, which is never passed to a method.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from scipy.special import logsumexp

from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess

Released = tuple[tuple[int, float], ...]  # ((event_round, D), ...) in event order


class BudgetExceeded(RuntimeError):
    """A method requested more queries than the hard budget allows."""


@dataclass(frozen=True)
class Config:
    T: int
    B: int
    d: int
    c: float = 0.01
    s: float = 0.1
    h: float = 0.1
    alpha: float = 0.1
    seed: int = 0

    def __post_init__(self) -> None:
        if any(type(v) is not int for v in (self.T, self.B, self.d)):
            raise ValueError("T, B, d must be integers")
        if self.T < 1 or not 0 <= self.B <= self.T or self.d < 1:
            raise ValueError("require T >= 1, 0 <= B <= T, d >= 1")
        if min(self.c, self.s, self.h) < 0 or not 0 < self.alpha < 1:
            raise ValueError("costs and hurdle must be nonnegative and alpha in (0,1)")


# ----------------------------------------------------------------------------- HMM bank


@dataclass(frozen=True)
class BankSpec:
    """A finite family of 2-state recurrent HMMs. State 1 is candidate-favourable.

    ``a = P(0 -> 1)``, ``b = P(1 -> 0)``. ``kind='bernoulli'`` emits ``D = 1 - 2Y`` with
    ``P(Y=1 | state) = p``; ``kind='gaussian'`` emits N(means, sigma^2).
    """

    kind: str
    a: np.ndarray
    b: np.ndarray
    means: np.ndarray  # (M, 2) mean of D in each state
    p: np.ndarray | None = None  # (M, 2) for bernoulli
    sigma: np.ndarray | None = None  # (M,) for gaussian

    @property
    def size(self) -> int:
        return len(self.a)


def bernoulli_grid_spec(
    rates: Sequence[float] = (0.01, 0.03, 0.1, 0.25),
    pairs: Sequence[tuple[float, float]] = (
        (0.02, 0.98),
        (0.1, 0.9),
        (0.3, 0.7),
        (0.5, 0.5),
        (0.3, 0.3),
        (0.1, 0.1),
    ),
) -> BankSpec:
    a, b, p = [], [], []
    for ra in rates:
        for rb in rates:
            for pair in pairs:
                a.append(ra)
                b.append(rb)
                p.append(pair)
    p_arr = np.asarray(p, dtype=float)
    return BankSpec("bernoulli", np.asarray(a), np.asarray(b), 1.0 - 2.0 * p_arr, p=p_arr)


class HMMBank:
    """Online HMM filter over a finite family, in event order with pending marginalized.

    ``update(event, D)`` incorporates one released label. Labels are released in event order
    (fixed delay), so the likelihood is the HMM likelihood of the released subsequence; pending
    and unqueried outcomes are never inserted.
    """

    def __init__(self, spec: BankSpec, prior1: float = 0.5):
        self.spec = spec
        self.pi = spec.a / (spec.a + spec.b)
        self.lam = 1.0 - spec.a - spec.b
        if np.any(self.lam < 0):
            raise ValueError("require a + b <= 1")
        self.prior1 = prior1
        self.reset()

    def reset(self) -> None:
        m = self.spec.size
        self.p1 = np.full(m, self.prior1)
        self.event = 0
        self.log_l = np.zeros(m)
        self._set_cache: np.ndarray | None = None

    def _prop(self, p1: np.ndarray, k: int) -> np.ndarray:
        return self.pi + (p1 - self.pi) * self.lam**k

    def _loglik(self, d: float) -> np.ndarray:
        sp = self.spec
        if sp.kind == "bernoulli":
            assert sp.p is not None
            p = sp.p
            return np.log(p) if d < 0 else np.log1p(-p)
        assert sp.sigma is not None
        z = (d - sp.means) / sp.sigma[:, None]
        return -0.5 * z * z - np.log(sp.sigma)[:, None]

    def update(self, event: int, d: float) -> None:
        if event <= self.event:
            raise ValueError("labels must be supplied in strictly increasing event order")
        q = self._prop(self.p1, event - self.event)  # P(S_event = 1 | released before)
        ll = self._loglik(d)
        top = np.maximum(ll[:, 0], ll[:, 1])
        e0, e1 = np.exp(ll[:, 0] - top), np.exp(ll[:, 1] - top)
        lik = (1.0 - q) * e0 + q * e1
        self.log_l = self.log_l + top + np.log(lik)
        self.p1 = q * e1 / lik
        self.event = event
        self._set_cache = None

    def confidence_set(self, alpha: float) -> np.ndarray:
        """Time-uniform likelihood-ratio set with a uniform-prior mixture numerator."""
        if self._set_cache is None:
            m = self.spec.size
            log_mix = logsumexp(self.log_l - math.log(m))
            self._set_cache = (log_mix - self.log_l) < math.log(1.0 / alpha)
        return self._set_cache

    def mean_at(self, t: int) -> np.ndarray:
        p = self._prop(self.p1, t - self.event)
        m = self.spec.means
        return m[:, 0] * (1 - p) + m[:, 1] * p

    def remaining_mean_sum(self, t: int, horizon: int) -> np.ndarray:
        """Sum over rounds t..horizon of E[D_u | released], without further labels."""
        k_rounds = horizon - t + 1
        p_t = self._prop(self.p1, t - self.event)
        gap = 1.0 - self.lam
        geometric = np.where(
            gap > 1e-12, (1.0 - self.lam**k_rounds) / np.maximum(gap, 1e-12), k_rounds
        )
        sum_p = k_rounds * self.pi + (p_t - self.pi) * geometric
        m = self.spec.means
        return m[:, 0] * k_rounds + (m[:, 1] - m[:, 0]) * sum_p


# ----------------------------------------------------------------------------- streams


@dataclass(frozen=True)
class HMMTruth:
    a: float
    b: float
    p: tuple[float, float]
    prior1: float = 0.5


@dataclass
class Truth:
    """Evaluator-side oracle information. Never passed to a method."""

    regime_mean: np.ndarray  # E[D_t | regime at t]
    regime: np.ndarray | None = None
    hmm: HMMTruth | None = None


@dataclass
class Stream:
    loss0: np.ndarray
    loss1: np.ndarray
    truth: Truth | None = None

    @property
    def T(self) -> int:
        return len(self.loss0)

    @property
    def D(self) -> np.ndarray:
        return np.clip(self.loss1 - self.loss0, -1.0, 1.0)


def make_bernoulli_stream(
    rng: np.random.Generator,
    T: int,
    p: tuple[float, float],
    *,
    a: float = 0.03,
    b: float = 0.03,
    path: np.ndarray | None = None,
    prior1: float = 0.5,
) -> Stream:
    """Regime path (HMM draw, or scripted), then ``Y_t ~ Bern(p[S_t])``; ``l0 = Y``, ``l1 = 1 - Y``."""
    if path is None:
        s = np.empty(T, dtype=int)
        prev = int(rng.random() < prior1)
        u = rng.random(T)
        for t in range(T):
            flip = a if prev == 0 else b
            prev = 1 - prev if u[t] < flip else prev
            s[t] = prev
        hmm: HMMTruth | None = HMMTruth(a, b, p, prior1)
    else:
        s = np.asarray(path, dtype=int)
        hmm = None
    pv = np.asarray(p, dtype=float)
    y = (rng.random(T) < pv[s]).astype(float)
    return Stream(y, 1.0 - y, Truth(1.0 - 2.0 * pv[s], s, hmm))


# ----------------------------------------------------------------------------- harness


@dataclass
class RunResult:
    cost: float
    decision_loss: float
    query_cost: float
    switch_cost: float
    queries: int
    switches: int
    wasted_queries: int
    promotions: int
    fp_regime: int | None
    fp_pred: int | None
    actions: np.ndarray = field(repr=False)
    query_mask: np.ndarray = field(repr=False)
    per_round_cost: np.ndarray = field(repr=False)


def true_predictive_mean(
    spec: HMMTruth, released_by_round: list[Released], horizon: int
) -> np.ndarray:
    """Evaluator-side filtered E_theta*[D_t | released] using the true parameters."""
    bank = HMMBank(
        BankSpec(
            "bernoulli",
            np.array([spec.a]),
            np.array([spec.b]),
            1.0 - 2.0 * np.array([spec.p]),
            p=np.array([spec.p]),
        ),
        prior1=spec.prior1,
    )
    out = np.empty(horizon)
    for t in range(1, horizon + 1):
        for ev, d in released_by_round[t - 1]:
            bank.update(ev, d)
        out[t - 1] = bank.mean_at(t)[0]
    return out


def score_actions(
    stream: Stream,
    cfg: Config,
    actions: np.ndarray,
    query_mask: np.ndarray,
    released_by_round: list[Released] | None = None,
) -> RunResult:
    prev = np.concatenate(([0], actions[:-1]))
    switch = actions != prev
    loss = np.where(actions == 1, stream.loss1, stream.loss0)
    per_round = loss + cfg.c * query_mask + cfg.s * switch
    promo = (actions == 1) & (prev == 0)
    fp_regime = fp_pred = None
    if stream.truth is not None:
        fp_regime = int(np.sum(promo & (stream.truth.regime_mean >= -cfg.h)))
        if stream.truth.hmm is not None and released_by_round is not None:
            pm = true_predictive_mean(stream.truth.hmm, released_by_round, cfg.T)
            fp_pred = int(np.sum(promo & (pm >= -cfg.h)))
    nq = int(query_mask.sum())
    wasted = int(np.sum(query_mask[max(0, cfg.T - cfg.d) :]))
    return RunResult(
        cost=float(per_round.sum()),
        decision_loss=float(loss.sum()),
        query_cost=cfg.c * nq,
        switch_cost=cfg.s * int(switch.sum()),
        queries=nq,
        switches=int(switch.sum()),
        wasted_queries=wasted,
        promotions=int(promo.sum()),
        fp_regime=fp_regime,
        fp_pred=fp_pred,
        actions=actions.copy(),
        query_mask=query_mask.copy(),
        per_round_cost=per_round,
    )


def run(stream: Stream, method: Method, cfg: Config) -> RunResult:
    """Play one stream. The method sees only ``(t, released labels)``; never the stream/truth."""
    if stream.T != cfg.T:
        raise ValueError("stream length must equal cfg.T")
    D = stream.D
    pending: dict[int, list[tuple[int, float]]] = {}
    actions = np.zeros(cfg.T, dtype=int)
    qmask = np.zeros(cfg.T, dtype=float)
    released_log: list[Released] = []
    used = 0
    method.start(cfg)
    for t in range(1, cfg.T + 1):
        due: Released = tuple(pending.pop(t, ()))
        released_log.append(due)
        action, query = method.step(t, due)
        if action not in (0, 1):
            raise ValueError("action must be 0 or 1")
        if query:
            if used >= cfg.B:
                raise BudgetExceeded(f"query {used + 1} requested with B={cfg.B} at round {t}")
            used += 1
            qmask[t - 1] = 1.0
            if t + cfg.d <= cfg.T:
                pending.setdefault(t + cfg.d, []).append((t, float(D[t - 1])))
        actions[t - 1] = action
    return score_actions(stream, cfg, actions, qmask, released_log)


# ----------------------------------------------------------------------------- methods


def uniform_calendar(T: int, B: int, d: int) -> frozenset[int]:
    """Up to B distinct, nearly equally spaced rounds in [1, T - d] (all releasable)."""
    last = T - d
    n = min(B, max(last, 0))
    if n <= 0:
        return frozenset()
    return frozenset(max(1, math.ceil(j * last / n)) for j in range(1, n + 1))


class Method:
    """Base class. Subclasses implement ``decide``; the budget guard lives in ``step``."""

    name = "base"

    def start(self, cfg: Config) -> None:
        self.cfg = cfg
        self.used = 0
        self.prev = 0
        self.pending_events: set[int] = set()
        self.last_query = 0
        self.labels: list[tuple[int, float]] = []
        self._init()

    def _init(self) -> None:  # pragma: no cover - overridden
        pass

    def decide(self, t: int, released: Released) -> tuple[int, bool]:  # pragma: no cover
        raise NotImplementedError

    def can_query(self, t: int) -> bool:
        return self.used < self.cfg.B and t + self.cfg.d <= self.cfg.T

    def step(self, t: int, released: Released) -> tuple[int, bool]:
        for ev, x in released:
            self.pending_events.discard(ev)
            self.labels.append((ev, x))
        action, query = self.decide(t, released)
        query = bool(query) and self.can_query(t)
        if query:
            self.used += 1
            self.pending_events.add(t)
            self.last_query = t
        self.prev = int(action)
        return int(action), query

    # helpers ------------------------------------------------------------------------
    def window_mean(self, m: int) -> float | None:
        if not self.labels:
            return None
        return float(np.mean([x for _, x in self.labels[-m:]]))

    def econ_ok(self, t: int, benefit: float) -> bool:
        return (self.cfg.T - t + 1) * benefit > self.cfg.s


def started_gate(bound: float, alpha: float, n_labels: int) -> VectorizedStartedMixtureEProcess:
    """Repository started-mixture e-process: at most 32 prespecified start positions (label index).

    Starts are fixed before data, so the fixed mixture stays a valid e-process for the conditional-mean
    null while allowing recovery after a long unfavourable phase (a plain product would stay crushed).
    """
    step = max(1, n_labels // 32)
    return VectorizedStartedMixtureEProcess(
        bound=bound, alpha=alpha, starts=tuple(range(0, max(1, n_labels), step))
    )


class NoSwitch(Method):
    name = "no_switch"

    def decide(self, t, released):
        return 0, False


class PeriodicMean(Method):
    name = "periodic_mean"

    def _init(self):
        c = self.cfg
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.period = max(c.d + 1, c.T // 20)
        self.m = max(3, c.B // 8)
        self.act = 0

    def decide(self, t, released):
        if (t - 1) % self.period == 0:
            mean = self.window_mean(self.m)
            if mean is not None:
                self.act = int(mean < 0)
        return self.act, t in self.cal


class EpisodeComposition(Method):
    """Fixed calendar + per-episode bounded-mean e-process with alpha spending (adaptation)."""

    def __init__(self, spending: str):
        if spending not in ("geo", "equal", "front"):
            raise ValueError(spending)
        self.spending = spending
        self.name = f"episode_{spending}"

    def _alpha_j(self, j: int) -> float:
        a, B = self.cfg.alpha, self.cfg.B
        if self.spending == "geo":
            return a * 2.0 ** -(j + 1)
        if self.spending == "equal":
            return a / (B + 1) if j <= B else 0.0
        return a if j == 0 else 0.0

    def _new_episode(self, j: int, start: int) -> None:
        self.j = j
        self.ep_start = start
        aj = self._alpha_j(j)
        self.ep = started_gate(1 + self.cfg.h, aj, self.cfg.B) if aj > 0 else None
        self.ep_labels: list[float] = []

    def _init(self):
        c = self.cfg
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.m = max(3, c.B // 8)
        self.act = 0
        self.promo_t = 0
        self.post: list[float] = []
        self._new_episode(0, 0)

    def decide(self, t, released):
        c = self.cfg
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start and self.ep is not None:
                    self.ep.update(-x - c.h)
                    self.ep_labels.append(x)
            elif ev >= self.promo_t:
                self.post.append(x)
        if self.act == 0:
            if self.ep is not None and self.ep.alarm and self.ep_labels:
                ben = -float(np.mean(self.ep_labels[-10:]))
                if self.econ_ok(t, ben):
                    self.act, self.promo_t, self.post = 1, t, []
        elif len(self.post) >= 3 and -float(np.mean(self.post[-self.m :])) <= c.h:
            self.act = 0
            self._new_episode(self.j + 1, t)
        return self.act, t in self.cal


class AllOnsetEDetector(Method):
    name = "allonset_edetector"

    def _init(self):
        c = self.cfg
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.n = max(1, len(self.cal))
        self.v = 0.0
        self.k = 0
        self.lam = 0.5 / (1 + c.h)
        self.m = max(3, c.B // 8)
        self.act = 0

    def decide(self, t, released):
        c = self.cfg
        for _ev, x in released:
            self.v = (self.v + 1.0) * (1.0 + self.lam * (-x - c.h))
            self.k += 1
        if self.act == 0 and self.k:
            w = (self.n - min(self.k, self.n)) / self.n + self.v / self.n
            mean = self.window_mean(self.m)
            if w >= 1.0 / c.alpha and mean is not None and self.econ_ok(t, -mean):
                self.act = 1  # promote once, never roll back
        return self.act, t in self.cal


class DALRestart(Method):
    """Detect-then-re-evaluate adaptation: uniform background + CUSUM-triggered query bursts."""

    name = "dal_restart"

    def _init(self):
        c = self.cfg
        self.bg_n = math.ceil(c.B / 2)
        self.pool = c.B - self.bg_n
        self.pool_used = 0
        self.bg_cal = uniform_calendar(c.T, self.bg_n, c.d)
        self.n_b = max(3, math.ceil(c.B / 10))
        self.act = 0
        self.phase = "burst"
        self.burst_events: set[int] = set()
        self.burst_labels: list[float] = []
        self.burst_req = 0
        self.mon_start = 0
        self.ref = 0.0
        self.sp = self.sm = 0.0

    def decide(self, t, released):
        c = self.cfg
        alarm = False
        for ev, x in released:
            if ev in self.burst_events:
                self.burst_labels.append(x)
            elif self.phase == "monitor" and ev >= self.mon_start:
                z = x - self.ref
                self.sp = max(0.0, self.sp + z - 0.25)
                self.sm = max(0.0, self.sm - z - 0.25)
                alarm = alarm or max(self.sp, self.sm) >= 3.0
        if self.phase == "burst":
            done = len(self.burst_labels) == self.burst_req and (
                self.burst_req >= self.n_b or self.pool_used >= self.pool
            )
            if done:
                if self.burst_labels:
                    mean = float(np.mean(self.burst_labels))
                    self.act = int(-mean > c.h and self.econ_ok(t, -mean))
                    self.ref = mean
                self.phase, self.mon_start = "monitor", t
                self.sp = self.sm = 0.0
                self.burst_events, self.burst_labels, self.burst_req = set(), [], 0
        elif alarm:
            self.phase, self.burst_events, self.burst_labels, self.burst_req = "burst", set(), [], 0
        want = False
        if self.phase == "burst" and self.burst_req < self.n_b and self.pool_used < self.pool:
            if t + c.d <= c.T:
                want = True
                self.burst_events.add(t)
                self.burst_req += 1
                self.pool_used += 1
        elif t in self.bg_cal:
            want = True
        return self.act, want


class PacingBernoulli(Method):
    name = "pacing_bernoulli"

    def _init(self):
        self.rng = np.random.default_rng([self.cfg.seed, 777])
        self.ewma: float | None = None
        self.act = 0

    def decide(self, t, released):
        c = self.cfg
        for _ev, x in released:
            self.ewma = x if self.ewma is None else 0.9 * self.ewma + 0.1 * x
        if self.ewma is not None:
            ben = -self.ewma
            if self.act == 0 and ben > c.h and self.econ_ok(t, ben):
                self.act = 1
            elif self.act == 1 and ben <= c.h:
                self.act = 0
        return self.act, bool(self.rng.random() < c.B / c.T)


class C1HMMConfidenceGate(Method):
    """C1: delayed-HMM predictive confidence-set gate with a straddle/keep-alive query rule."""

    name = "c1_hmm_cs"

    def __init__(self, spec: BankSpec, pending_cap: int = 2, burst_frac: float = 0.0):
        self.spec = spec
        self.pending_cap = pending_cap
        self.burst_frac = burst_frac

    def _init(self):
        self.bank = HMMBank(self.spec)
        c = self.cfg
        self.keepalive = max(c.d + 1, math.ceil(4 * c.T / max(c.B, 1)))

    def decide(self, t, released):
        c = self.cfg
        for ev, x in released:
            self.bank.update(ev, x)
        ben = -self.bank.mean_at(t)
        inset = self.bank.confidence_set(c.alpha)
        lo, hi = float(ben[inset].min()), float(ben[inset].max())
        act = self.prev
        if act == 0:
            if lo > c.h:
                g_lo = float((-self.bank.remaining_mean_sum(t, c.T))[inset].min())
                if g_lo > c.s:
                    act = 1
        elif hi <= c.h:
            act = 0
        straddle = lo <= c.h < hi
        keep = t - self.last_query >= self.keepalive
        paced = self.used < max(1, math.ceil(self.burst_frac * c.B)) + math.floor(2 * c.B * t / c.T)
        query = (straddle or keep) and paced and len(self.pending_events) < self.pending_cap
        return act, query


class C2ReversalBudgetSplit(Method):
    """C2: rho*B to an alpha-spent e-process promotion gate, the rest to a CUSUM rollback monitor."""

    def __init__(self, rho: float, cusum_threshold: float = 2.0):
        if not 0 < rho < 1:
            raise ValueError("rho must be in (0,1)")
        self.rho = rho
        self.kappa = cusum_threshold
        self.name = f"c2_rho{rho:g}"

    def _new_episode(self, j: int, start: int) -> None:
        self.j, self.ep_start = j, start
        self.ep = started_gate(1 + self.cfg.h, self.cfg.alpha * 2.0 ** -(j + 1), self.gate_n)
        self.ep_labels: list[float] = []

    def _init(self):
        c = self.cfg
        self.gate_n = int(self.rho * c.B)
        self.mon_n = c.B - self.gate_n
        self.gate_used = self.mon_used = 0
        self.credit = {0: 0.0, 1: 0.0}
        self.act = 0
        self.promo_t = 0
        self.cus = 0.0
        self.ref = 0.0
        self._new_episode(0, 0)

    def decide(self, t, released):
        c = self.cfg
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start:
                    self.ep.update(-x - c.h)
                    self.ep_labels.append(x)
            elif ev >= self.promo_t:
                self.cus = max(0.0, self.cus + x - self.ref)
        if self.act == 0:
            if self.ep.alarm and self.ep_labels:
                mean = float(np.mean(self.ep_labels[-10:]))
                if self.econ_ok(t, -mean):
                    self.act, self.promo_t, self.cus = 1, t, 0.0
                    self.ref = (mean - c.h) / 2.0
        elif self.cus >= self.kappa:
            self.act, self.cus = 0, 0.0
            self._new_episode(self.j + 1, t)
        # uniformly paced spend from the pool belonging to the current phase
        pool = self.gate_n if self.act == 0 else self.mon_n
        used = self.gate_used if self.act == 0 else self.mon_used
        query = False
        if pool - used > 0 and t + c.d <= c.T:
            self.credit[self.act] += (pool - used) / max(1, c.T - c.d - t + 1)
            if self.credit[self.act] >= 1.0:
                self.credit[self.act] -= 1.0
                query = True
                if self.act == 0:
                    self.gate_used += 1
                else:
                    self.mon_used += 1
        return self.act, query


def build_method(name: str, spec: BankSpec | None = None) -> Method:
    if name == "no_switch":
        return NoSwitch()
    if name == "periodic_mean":
        return PeriodicMean()
    if name.startswith("episode_"):
        return EpisodeComposition(name.split("_", 1)[1])
    if name == "allonset_edetector":
        return AllOnsetEDetector()
    if name == "dal_restart":
        return DALRestart()
    if name == "pacing_bernoulli":
        return PacingBernoulli()
    if name == "c1_hmm_cs":
        if spec is None:
            raise ValueError("C1 needs a BankSpec")
        return C1HMMConfidenceGate(spec, burst_frac=0.1)
    if name.startswith("c2_rho"):
        return C2ReversalBudgetSplit(float(name[6:]))
    raise ValueError(f"unknown method {name}")


BASELINES = (
    "no_switch",
    "periodic_mean",
    "episode_geo",
    "episode_equal",
    "episode_front",
    "allonset_edetector",
    "dal_restart",
    "pacing_bernoulli",
)
C2_RHOS = (0.25, 0.5, 0.75)
CANDIDATES = ("c1_hmm_cs",) + tuple(f"c2_rho{r:g}" for r in C2_RHOS)


# ----------------------------------------------------------------------------- scenarios

SCENARIOS: dict[str, dict] = {
    "persistent_std": {"kind": "hmm", "a": 0.03, "b": 0.03, "p": (0.1, 0.9)},
    "fast_std": {"kind": "hmm", "a": 0.25, "b": 0.25, "p": (0.1, 0.9)},
    "persistent_weak": {"kind": "hmm", "a": 0.03, "b": 0.03, "p": (0.3, 0.7)},
    "null_boundary": {"kind": "hmm", "a": 0.03, "b": 0.03, "p": (0.5, 0.5)},
    "null_harm": {"kind": "hmm", "a": 0.03, "b": 0.03, "p": (0.3, 0.3)},
    "late_onset": {"kind": "script", "breaks": ((0.6, 1),), "p": (0.1, 0.9)},
    "reversal": {"kind": "script", "breaks": ((0.2, 1), (0.55, 0)), "p": (0.1, 0.9)},
    "offgrid_hmm": {"kind": "hmm", "a": 0.05, "b": 0.05, "p": (0.15, 0.85)},
}


def make_scenario_stream(name: str, T: int, seed: int) -> Stream:
    sc = SCENARIOS[name]
    idx = list(SCENARIOS).index(name)
    rng = np.random.default_rng([seed, T, idx])
    if sc["kind"] == "hmm":
        return make_bernoulli_stream(rng, T, sc["p"], a=sc["a"], b=sc["b"])
    path = np.zeros(T, dtype=int)
    for frac, state in sc["breaks"]:
        path[int(frac * T) :] = state
    return make_bernoulli_stream(rng, T, sc["p"], path=path)


def clairvoyant_actions(stream: Stream) -> np.ndarray:
    """Evaluator-only reference: follow the truly better regime (zero queries)."""
    assert stream.truth is not None
    return (stream.truth.regime_mean < 0).astype(int)


# ----------------------------------------------------------------------------- statistics


def paired_ci(x: np.ndarray, level: float = 0.95) -> tuple[float, float, float]:
    """Mean and paired-t interval over independent seeds."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    mean = float(x.mean())
    if n < 2:
        return mean, float("nan"), float("nan")
    se = float(x.std(ddof=1) / math.sqrt(n))
    half = float(stats.t.ppf(0.5 + level / 2, n - 1)) * se
    return mean, mean - half, mean + half


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    ph = k / n
    den = 1 + z * z / n
    centre = (ph + z * z / (2 * n)) / den
    half = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return ph, max(0.0, centre - half), min(1.0, centre + half)


def block_bootstrap_ci(
    diff: np.ndarray, block: int = 50, reps: int = 500, seed: int = 0
) -> tuple[float, float, float]:
    """Moving-block bootstrap interval for the SUM of a per-round paired cost difference."""
    x = np.asarray(diff, dtype=float)
    n = len(x)
    block = max(1, min(block, n))
    rng = np.random.default_rng(seed)
    n_blocks = math.ceil(n / block)
    csum = np.concatenate(([0.0], np.cumsum(x)))
    starts_max = n - block
    sums = np.empty(reps)
    for r in range(reps):
        st = rng.integers(0, starts_max + 1, size=n_blocks)
        total = (csum[st + block] - csum[st]).sum()
        sums[r] = total * (n / (n_blocks * block))
    return float(x.sum()), float(np.quantile(sums, 0.025)), float(np.quantile(sums, 0.975))


# ----------------------------------------------------------------------------- EM (real data)


def fit_gaussian_hmm(d: np.ndarray, iters: int = 40) -> dict[str, float]:
    """2-state Gaussian HMM by scaled Baum-Welch on calibration-block D. State 1 = lower mean."""
    x = np.asarray(d, dtype=float)
    n = len(x)
    mu = np.array([np.quantile(x, 0.75), np.quantile(x, 0.25)])
    sd = max(float(x.std()), 1e-6)
    sig = np.array([sd, sd])
    A = np.array([[0.95, 0.05], [0.05, 0.95]])
    for _ in range(iters):
        z = (x[:, None] - mu[None, :]) / sig[None, :]
        B = np.exp(-0.5 * z * z) / sig[None, :] + 1e-300
        alpha = np.empty((n, 2))
        scale = np.empty(n)
        a0 = 0.5 * B[0]
        scale[0] = a0.sum()
        alpha[0] = a0 / scale[0]
        for t in range(1, n):
            v = (alpha[t - 1] @ A) * B[t]
            scale[t] = v.sum()
            alpha[t] = v / scale[t]
        beta = np.ones((n, 2))
        for t in range(n - 2, -1, -1):
            beta[t] = (A @ (B[t + 1] * beta[t + 1])) / scale[t + 1]
        gamma = alpha * beta
        gamma /= gamma.sum(1, keepdims=True)
        xi = (alpha[:-1, :, None] * A[None] * (B[1:, None, :] * beta[1:, None, :])) / scale[
            1:, None, None
        ]
        A = xi.sum(0) / np.maximum(xi.sum((0, 2))[:, None], 1e-12)
        A = np.clip(A, 1e-3, 1 - 1e-3)
        A /= A.sum(1, keepdims=True)
        w = gamma.sum(0) + 1e-12
        mu = (gamma * x[:, None]).sum(0) / w
        sig = np.sqrt(np.maximum((gamma * (x[:, None] - mu[None]) ** 2).sum(0) / w, 1e-8))
        sig = np.maximum(sig, 0.2 * sd)
    order = np.argsort(mu)  # state 1 = lower mean (candidate favourable)
    hi, lo = int(order[1]), int(order[0])
    return {
        "m0": float(mu[hi]),
        "m1": float(mu[lo]),
        "sigma": float(np.sqrt(0.5 * (sig[hi] ** 2 + sig[lo] ** 2))),
        "a": float(A[hi, lo]),
        "b": float(A[lo, hi]),
        "mu_bar": float(x.mean()),
    }


def gaussian_grid_spec(fit: dict[str, float]) -> BankSpec:
    """Declared real-data family: fitted means scaled around two centers, noise and rate perturbations."""
    mean_pairs = []
    for center in (fit["mu_bar"], 0.0):
        for k in (0.5, 1.0, 1.5):
            mean_pairs.append(
                (center + k * (fit["m0"] - center), center + k * (fit["m1"] - center))
            )
    mean_pairs += [(fit["mu_bar"], fit["mu_bar"]), (0.0, 0.0)]
    a, b, means, sig = [], [], [], []
    for mp in mean_pairs:
        for sf in (0.8, 1.0, 1.25):
            for ra in (0.5, 1.0, 2.0):
                for rb in (0.5, 1.0, 2.0):
                    a.append(float(np.clip(fit["a"] * ra, 0.002, 0.5)))
                    b.append(float(np.clip(fit["b"] * rb, 0.002, 0.5)))
                    means.append(mp)
                    sig.append(fit["sigma"] * sf)
    return BankSpec(
        "gaussian", np.asarray(a), np.asarray(b), np.asarray(means), sigma=np.asarray(sig)
    )


__all__ = [
    "BASELINES",
    "C2_RHOS",
    "CANDIDATES",
    "SCENARIOS",
    "BankSpec",
    "BudgetExceeded",
    "Config",
    "HMMBank",
    "Method",
    "RunResult",
    "Stream",
    "Truth",
    "bernoulli_grid_spec",
    "block_bootstrap_ci",
    "build_method",
    "clairvoyant_actions",
    "fit_gaussian_hmm",
    "gaussian_grid_spec",
    "make_bernoulli_stream",
    "make_scenario_stream",
    "paired_ci",
    "run",
    "score_actions",
    "wilson",
]
