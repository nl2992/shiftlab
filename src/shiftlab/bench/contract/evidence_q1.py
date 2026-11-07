"""Q1 label-outcome evidence identities, built on :mod:`evidence_seam` (reuses ``shiftlab.sota.inrepo.gapmix`` components).

Common setting (applies to every class below unless its docstring says otherwise)
---------------------------------------------------------------------------------
* Filtration ``G_i``: sigma-field of the in-order, identified RELEASED outcomes ``(t_1, Z_1), ..., (t_i, Z_i)``, their gaps
  ``g_k = t_k - t_{k-1}`` and declared selection records. Not the round-level chain. ``Z = 1[d < 0]`` with
  ``d = loss(candidate) - loss(incumbent)`` (so ties count as unfavourable: conservative for the null ``P(Z=1) <= q0``).
  ``q0 = (1 + h) / 2`` with ``h`` the public hurdle ``EnvSpec.hurdle``.
* Out-of-order outcomes (``label_round`` <= an already used one) are DROPPED and counted: the drop rule reads event rounds
  and release order only, so it is value-blind exactly when delays are non-informative (declared, never inferred).
* Predictable-selection requirement: the next observed round ``t_i`` must be ``G_{i-1}``-measurable (calendar, rule on past
  released outcomes) or exogenously randomised with a declared propensity. Under that requirement
  ``P(Z_i = 1 | Z_{i-1}, g_i) = p + (Z_{i-1} - p) rho^{g_i}`` for the stationary two-state chain, and
  ``P(Z_i = 1 | G_{i-1}, g_i) <= q0`` under the conditional null. It is NOT assumed under informative delay/missingness, query
  rules that peek at ``Z_i`` or at a monitor correlated with it, or the Drift2Act host's own selection (undeclared propensity
  and dependence on the current monitor x_t); :meth:`GapEvidence.contract_status` flags those as OUT_OF_CONTRACT.
* Declared nulls. ``cond``: ``P(Z_i = 1 | G_{i-1}, g_i) <= q0`` for every history. ``marg``: the round-level favourable
  indicator is a stationary two-state chain with ``p <= q0`` and persistence ``rho in [0, rho_bar]`` (``rho_bar`` DECLARED,
  never read from simulator truth); the labelled skeleton then has kernel ``P^{g_i}``.
* Anytime validity: every claimed-valid process is a nonnegative supermartingale (or is dominated by one) with start value 1,
  so ``P(sup_i E_i >= 1/alpha) <= alpha`` (Ville) at any stopping time of the released-order filtration.

Building blocks (all deterministic given the outcome stream):
* predictors (``AltGridPred``, ``BucketPred``, ``TemperedPred``, ``DirichletPred``, ``PluginPred``) return
  ``r_i = Q(Z_i = 1 | past, gap)`` from earlier outcomes only. ANY predictable ``r_i`` is a valid numerator/bet.
* ``LRStart`` (marg): ``prod_i Q(Z_i | past)`` divided by the certified null supremum of the exact-gap likelihood
  (``gapmix.certified_null_sup_loglik`` over ``rho in [0, rho_bar]``, ``p <= q0``): a valid test martingale ratio for any predictor.
* ``BetStart`` (cond or marg-envelope): conditional bets against ``Bernoulli(u)``, ``u = q0`` (cond) or the envelope
  ``gapmix.envelope_u(q0, rho_bar, g, prev)`` (marg). Neutral when ``r <= u``.
* Mixtures over restarts use weights fixed in advance (or sub-probability weights fixed at the start event), with unstarted
  components counted at their prior mass, so the mixture is dominated by a supermartingale started at 1.
"""

from __future__ import annotations

import itertools
import json
import math
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import numpy as np
from scipy.special import logsumexp
from scipy.stats import norm

from shiftlab.dive.atlas_dependence_baselines import MarkovLREProcess
from shiftlab.sota.inrepo.gapmix import (
    ALT_P,
    ALT_RHO,
    ENV_BET_FRACS,
    certified_null_sup_loglik,
    envelope_log_factor,
    envelope_u,
    rho_cell_edges,
)

from .evidence_seam import IN_CONTRACT_REGIMES, SELECTION_REGIMES, ReleasedOutcome
from .types import EnvSpec

DEFAULT_RHO_BAR = (
    0.8  # declared dependence ceiling when an identity's configuration has no declared_rho_bar
)
CELL_WIDTH = 0.005  # gapmix default rho cell width of the certified supremum
GAP_BUCKETS = (1, 4, 16)  # buckets {1}, {2-4}, {5-16}, {>16}
BUCKET_MIN_GAP = (1, 2, 5, 17)
_R_LO, _R_HI = 1e-9, 1.0 - 1e-6


def gap_bucket(g: int) -> int:
    return 0 if g <= 1 else 1 if g <= 4 else 2 if g <= 16 else 3


def _clip(r: float) -> float:
    return min(max(float(r), _R_LO), _R_HI)


def _p1(p: float, rho: float, prev: int, g: int) -> float:
    lam = rho**g
    return p * (1.0 - lam) if prev == 0 else p + (1.0 - p) * lam


@dataclass(frozen=True)
class Ctx:
    """Public quantities available to a core at ``bind`` time (nothing evaluator-side)."""

    q0: float
    T: int
    B: int  # label budget cap (public BudgetSpec.label_cap)
    rho_bar: float
    cell_width: float = CELL_WIDTH


# ----------------------------------------------------------------------------- predictors


class AltGridPred:
    """Posterior-weighted mixture of exact-gap alternatives ``(p_a, rho_a)`` (uniform prior): ``r = sum_a w_a P_a^g(prev -> 1)``.

    The running product of its predictions equals the ``ExactGapStart`` numerator ``mean_a prod L_a`` of gapmix (identity of
    mixture likelihood and sequential predictive); tested against gapmix."""

    def __init__(self, q0: float) -> None:
        self.alts = np.array([(p, r) for p in ALT_P for r in ALT_RHO if p > q0])
        self.logw = np.zeros(len(self.alts))

    def _p1(self, prev: int, g: int) -> np.ndarray:
        return np.array([_p1(p, r, prev, g) for p, r in self.alts])

    def predict(self, prev: int, g: int) -> float:
        w = np.exp(self.logw - logsumexp(self.logw))
        return float(w @ self._p1(prev, g))

    def learn(self, prev: int, g: int, z: int) -> None:
        p1 = self._p1(prev, g)
        self.logw += np.log(p1 if z else 1.0 - p1)


class BucketPred:
    """Pooled KT plug-in per (gap bucket, previous state) shrunk to 1/2 by ``smoothing``: ``(1-s) KT + s/2``."""

    def __init__(self, smoothing: float = 0.02) -> None:
        self.s, self.n = smoothing, np.zeros((4, 2, 2))

    def predict(self, prev: int, g: int) -> float:
        n0, n1 = self.n[gap_bucket(g), prev]
        return (1 - self.s) * (n1 + 0.5) / (n0 + n1 + 1.0) + self.s * 0.5

    def learn(self, prev: int, g: int, z: int) -> None:
        self.n[gap_bucket(g), prev, z] += 1.0


class TemperedPred:
    """Adjacent-step KT plug-in tempered towards the marginal KT by ``lam = rho_bar^(g-1)`` (shrunk to 1/2 by ``smoothing``)."""

    def __init__(self, rho_bar: float, smoothing: float = 0.02) -> None:
        self.rho_bar, self.s = rho_bar, smoothing
        self.n, self.m = np.zeros((2, 2)), np.zeros(2)

    def predict(self, prev: int, g: int) -> float:
        n0, n1 = self.n[prev]
        q_adj = (n1 + 0.5) / (n0 + n1 + 1.0)
        q_mar = (self.m[1] + 0.5) / (self.m.sum() + 1.0)
        lam = self.rho_bar ** max(0, g - 1)
        return (1 - self.s) * (lam * q_adj + (1 - lam) * q_mar) + self.s * 0.5

    def learn(self, prev: int, g: int, z: int) -> None:
        self.n[prev, z] += 1.0
        self.m[z] += 1.0


class DirichletPred:
    """Per-row Dirichlet(a, a) predictive mean (gap-agnostic): ``(n1 + a) / (n + 2a)``. ``a = 0.5`` is the KT plug-in."""

    def __init__(self, a: float = 0.5) -> None:
        self.a, self.n = a, np.zeros((2, 2))

    def predict(self, prev: int, g: int) -> float:
        n0, n1 = self.n[prev]
        return (n1 + self.a) / (n0 + n1 + 2 * self.a)

    def learn(self, prev: int, g: int, z: int) -> None:
        self.n[prev, z] += 1.0


def PluginPred() -> DirichletPred:
    return DirichletPred(0.5)


# ----------------------------------------------------------------------------- per-start processes


class _Start:
    """Shared scaffolding: first outcome is only conditioned on; ``gap_source`` selects the gap used by the PREDICTOR only."""

    def __init__(self, gap_source: str = "observed") -> None:
        if gap_source not in ("observed", "expected_plugin"):
            raise ValueError(gap_source)
        self.gap_source = gap_source
        self.prev: int | None = None
        self.prev_ev = 0
        self._gsum, self._gn = 0.0, 0
        self.log_e = 0.0

    def _plug_gap(self) -> int:
        return max(1, round(self._gsum / self._gn)) if self._gn else 1

    def update(self, ev: int, z: int) -> None:
        if self.prev is None:
            self.prev, self.prev_ev = z, ev
            return
        g = ev - self.prev_ev
        gp = g if self.gap_source == "observed" else self._plug_gap()
        self._step(g, gp, self.prev, z)
        self._gsum += g
        self._gn += 1
        self.prev, self.prev_ev = z, ev

    def _step(self, g: int, gp: int, prev: int, z: int) -> None:  # pragma: no cover
        raise NotImplementedError


class LRStart(_Start):
    """Marginal-null likelihood-ratio e-process of one start (generalises ``gapmix.ExactGapStart``).

    Filtration: G_i (common setting). Transition model: stationary two-state chain, skeleton kernel P^{g_i}, DENOMINATOR always
    uses the OBSERVED gap. Stopping: any stopping time of G. Parameter uncertainty: the numerator is a predictable predictor
    (no parameter claim); the denominator is the CERTIFIED supremum of the exact-gap conditional likelihood over
    p <= q0, rho in [0, rho_bar] (cell-wise monotone bound + bisection, slack 1e-9). Target null: marg within the declared class.
    Validity: PROVEN given the declared class and predictable/exogenous gaps, for every predictor and gap_source (the
    numerator may be wrong, it only costs power)."""

    def __init__(
        self, ctx: Ctx, pred, gap_source: str = "observed", rho_bar: float | None = None
    ) -> None:
        super().__init__(gap_source)
        self.q0, self.pred = ctx.q0, pred
        self.edges = rho_cell_edges(ctx.rho_bar if rho_bar is None else rho_bar, ctx.cell_width)
        self.counts: dict[int, np.ndarray] = {}
        self.logq = 0.0

    def _step(self, g, gp, prev, z):
        r = _clip(self.pred.predict(prev, gp))
        self.logq += math.log(r if z else 1.0 - r)
        self.pred.learn(prev, gp, z)
        self.counts.setdefault(g, np.zeros(4))[2 * prev + z] += 1.0
        self.log_e = self.logq - certified_null_sup_loglik(self.counts, self.q0, self.edges)


class BetStart(_Start):
    """Conditional-bet e-process of one start (generalises ``gapmix.EnvelopeStart``); optional gap-bucket wallets.

    Filtration: G_i. Null bound ``u``: cond -> ``u = q0 (+ radius)`` for every history and gap (no dependence parameter);
    marg-envelope -> ``u = gapmix.envelope_u(q0, rho_bar_eff, g, prev) (+ radius)``, the sup over the declared class of
    ``P(Z=1 | prev, g)``. Factor ``(r/u)^Z ((1-r)/(1-u))^(1-Z)`` if ``r > u`` else 1 for the predictor bet and fixed bets
    ``u + b(1-u)``, ``b in ENV_BET_FRACS``; wealth = equal-weight average of the three bets. With ``n_wallets = 4`` the gap
    buckets each get their own wallet (factor 1 on other buckets) averaged with weight 1/4 (a union-bound-style mixture).
    Stopping: any G-stopping time. Parameter uncertainty: none beyond the declared bound ``u`` (radius = extra deterministic
    slack). Validity: PROVEN under the cond null (any predictable gaps) or, for the envelope, under the declared marg class
    with predictable/exogenous gaps; ``r`` is any predictable predictor."""

    def __init__(
        self,
        ctx: Ctx,
        pred,
        null: str,
        gap_source: str = "observed",
        rho_bar: float | None = None,
        radius: float = 0.0,
        additive: bool = True,
        n_wallets: int = 1,
    ) -> None:
        super().__init__(gap_source)
        if null not in ("cond", "marg"):
            raise ValueError(null)
        self.q0, self.pred, self.null, self.radius, self.additive = (
            ctx.q0,
            pred,
            null,
            radius,
            additive,
        )
        self.rho_bar = ctx.rho_bar if rho_bar is None else rho_bar
        self.n_wallets = n_wallets
        self.logw = np.zeros((n_wallets, 1 + len(ENV_BET_FRACS)))

    def _u(self, g: int, prev: int) -> float:
        if self.null == "cond":
            u = self.q0 + (self.radius if self.additive else 0.0)
        elif self.additive:
            gg = BUCKET_MIN_GAP[gap_bucket(g)] if self.n_wallets > 1 else g
            u = envelope_u(self.q0, self.rho_bar, gg, prev) + self.radius
        else:
            u = envelope_u(self.q0, min(0.999, self.rho_bar + self.radius), g, prev)
        return min(u, _R_HI)

    def _step(self, g, gp, prev, z):
        u = self._u(g, prev)
        r = min(_clip(self.pred.predict(prev, gp)), _R_HI)
        rs = [r] + [u + b * (1.0 - u) for b in ENV_BET_FRACS]
        w = gap_bucket(g) if self.n_wallets > 1 else 0
        self.logw[w] += np.array([envelope_log_factor(x, u, z) for x in rs])
        self.pred.learn(prev, gp, z)
        per = logsumexp(self.logw, axis=1) - math.log(self.logw.shape[1])
        self.log_e = float(logsumexp(per) - math.log(self.n_wallets))


class SlackMarkovLR:
    """Repository adjacent-step Markov-LR (``MarkovLREProcess``) with a deterministic threshold slack ``radius * sqrt(n)``.

    Filtration: G_i, but the model IGNORES gaps (treats consecutive released labels as adjacent chain steps). Transition model:
    adjacent two-state chain; valid only when all gaps are equal (a thinned stationary chain is Markov), NOT for varying gaps.
    Stopping: any. Parameter uncertainty: the Markov-LR's own certified supremum. Target null: marg with constant spacing.
    Validity: NOT CLAIMED for varying gaps (control arm)."""

    def __init__(self, ctx: Ctx, radius: float) -> None:
        self.ep, self.radius, self.n = MarkovLREProcess(ctx.q0, 0.1, max(1, ctx.B)), radius, 0
        self.log_e = 0.0

    def update(self, ev: int, z: int) -> None:
        self.ep.update_z(z)
        self.n += 1
        self.log_e = float(self.ep.log_e_value) - self.radius * math.sqrt(self.n)


class SlackBet(BetStart):
    """Cond-null plug-in bet e-process with deterministic slack ``radius * sqrt(n)`` on log e (dominated by the valid ``BetStart``)."""

    def __init__(self, ctx: Ctx, pred, radius: float, gap_source: str = "observed") -> None:
        super().__init__(ctx, pred, "cond", gap_source)
        self.slack, self.n = radius, 0

    def _step(self, g, gp, prev, z):
        super()._step(g, gp, prev, z)
        self.n += 1
        self.log_e -= self.slack * math.sqrt(self.n)


# ----------------------------------------------------------------------------- restart mixtures


class StartMixture:
    """Restart mixture over starts triggered by event round (``('ev', thr)``) or accepted-label index (``('idx', k)``).

    Filtration: G_i. Weights ``pi`` fixed in advance (sum 1). ``gap_weighted``: when start j begins its weight becomes
    ``pi_j / (1 + log2 g)`` with ``g`` the gap at the start event (a G-measurable sub-probability; unstarted components count
    at ``pi_j``), so the process is dominated by a supermartingale started at 1. ``prune``: a started component is permanently
    dropped when its log e falls ``prune`` below the best started component; dropping mass can only LOWER the process
    (never re-allocated), hence validity holds for any pruning rule (but pruning cannot add power).
    Stopping: any G-stopping time. Parameter uncertainty: inherited from the per-start process. Target null: that of the starts."""

    def __init__(
        self,
        make_start: Callable[[], object],
        triggers: Sequence[tuple[str, float]],
        pi: Sequence[float],
        gap_weighted: bool = False,
        prune: float | None = None,
    ) -> None:
        self.triggers = list(triggers)
        self.pi = np.asarray(pi, float)
        if not np.isclose(self.pi.sum(), 1.0):
            raise ValueError("prior weights must sum to 1")
        self.w = self.pi.copy()
        self.starts = [make_start() for _ in self.triggers]
        self.started = [False] * len(self.triggers)
        self.alive = [True] * len(self.triggers)
        self.gap_weighted, self.prune = gap_weighted, prune
        self.n_lab, self.prev_ev = 0, None
        self.log_e = 0.0

    def update(self, ev: int, z: int) -> None:
        gap_here = 1 if self.prev_ev is None else max(1, ev - self.prev_ev)
        for j, (kind, val) in enumerate(self.triggers):
            if not self.started[j] and (
                (kind == "ev" and ev >= val) or (kind == "idx" and self.n_lab >= val)
            ):
                self.started[j] = True
                if self.gap_weighted:
                    self.w[j] = self.pi[j] / (1.0 + math.log2(gap_here))
            if self.started[j] and self.alive[j]:
                self.starts[j].update(ev, z)
        self.n_lab += 1
        self.prev_ev = ev
        comp = np.array([s.log_e for s in self.starts])
        if self.prune is not None:
            live = [j for j in range(len(comp)) if self.started[j] and self.alive[j]]
            if live:
                best = max(comp[j] for j in live)
                for j in live:
                    if comp[j] < best - self.prune:
                        self.alive[j] = False
        lw = np.where(self.alive, np.log(np.maximum(self.w, 1e-300)) + comp, -np.inf)
        self.log_e = float(logsumexp(lw))


class TrailingStarts:
    """Every one of the first ``B`` labels starts a component of weight ``1/B``; only the last ``K`` components are kept.

    Filtration: G_i. Weights 1/B fixed in advance (total <= 1); future starts count at their prior mass ``(B-n)/B``. Dropped
    components lower the value, so the process is dominated by the full mixture (a supermartingale): VALID, at the price of
    dilution by 1/B (control-like). Stopping: any. Parameter uncertainty: inherited. Target null: that of the starts."""

    def __init__(self, make_start: Callable[[], object], K: int, B: int) -> None:
        self.make, self.K, self.B = make_start, max(1, K), max(1, B)
        self.live: list[object] = []
        self.n_started = 0
        self.log_e = 0.0

    def update(self, ev: int, z: int) -> None:
        if self.n_started < self.B:
            self.live.append(self.make())
            self.n_started += 1
        for s in self.live:
            s.update(ev, z)
        self.live = self.live[-self.K :]
        e = sum(math.exp(min(s.log_e, 700.0)) for s in self.live) / self.B
        self.log_e = math.log(e + max(0, self.B - self.n_started) / self.B)


def start_weights(prior: str, n: int) -> tuple[np.ndarray, bool]:
    """(pi, gap_weighted) for start_prior in {uniform, geometric, gap_weighted}."""
    if prior == "geometric":
        w = 0.5 ** np.arange(n)
        return w / w.sum(), False
    return np.full(n, 1.0 / n), prior == "gap_weighted"


def hazard_weights(duration_prior: str, floor: float, n: int) -> np.ndarray:
    """Onset prior over ``n`` start slots from a regime-duration pmf.

    ``geometric``: constant hazard ``h = max(floor, 1/n)`` -> ``pmf_j ∝ (1-h)^j h``. ``semi_markov``: discrete Weibull (shape 2,
    scale n/2: hazard increasing with regime age) mixed with ``min(1, floor*n)`` uniform mass so the hazard never falls below
    the floor. Normalised; fixed before data, hence valid as restart weights."""
    j = np.arange(n)
    if duration_prior == "geometric":
        h = max(floor, 1.0 / n)
        pmf = (1 - h) ** j * h
    else:
        lam, k = max(n / 2.0, 1.0), 2.0
        pmf = np.exp(-((j / lam) ** k)) - np.exp(-(((j + 1) / lam) ** k))
        eps = min(1.0, floor * n)
        pmf = (1 - eps) * pmf / pmf.sum() + eps / n
    return pmf / pmf.sum()


# ----------------------------------------------------------------------------- null-selection cores


class DualCore:
    """Run a cond-null and a marg-null core on the same outcomes; DECIDE with ``decide`` ('cond'|'marg'), report both.

    Filtration G_i. Transition/params: those of the two cores. Stopping: any. Target null: the decision core's null; the other
    stream is reported as labelled stress only (never scored as a validity claim). Validity: PROVEN for the decision null."""

    def __init__(self, cond, marg, decide: str) -> None:
        self.cond, self.marg, self.decide = cond, marg, decide

    def update(self, ev: int, z: int) -> None:
        self.cond.update(ev, z)
        self.marg.update(ev, z)

    @property
    def log_e(self) -> float:
        return (self.cond if self.decide == "cond" else self.marg).log_e

    def report(self) -> dict:
        return {
            "log_e_cond": self.cond.log_e,
            "log_e_marg": self.marg.log_e,
            "decided_with": self.decide,
        }


class MinCore(DualCore):
    """Intersection certificate: ``log e = min(log e_cond, log e_marg)`` (both must cross).

    Filtration G_i. Pointwise <= each valid component, so it is dominated by e_cond (valid under H0cond) and by e_marg (valid
    under H0marg within the declared class). Stopping: any. Target null: either (cond or marg). Valid-conservative reference arm."""

    @property
    def log_e(self) -> float:
        return min(self.cond.log_e, self.marg.log_e)


class RouterCore(DualCore):
    """Pre-specified dependence screen on an independent calibration prefix routes between the cond and the marg core.

    Filtration G_i; the first ``n_cal`` identified in-order outcomes are used ONLY for the screen (one-sided two-proportion z
    test of P(Z=1|prev=1) > P(Z=1|prev=0) at level ``alpha_sel``) and then discarded, so the route is G_{n_cal}-measurable.
    Routed to marg if dependence is detected, else cond. Both cores are fed (for the report), the decision uses the route.
    Stopping: any, after the prefix. Parameter uncertainty: the screen's type-II error is NOT controlled.
    Validity: PROVEN under H0cond within the declared class (both routes are valid there). Under marg-only dependence a missed
    screen routes to the cond core, which is not valid there: validity under H0marg is NOT claimed (flagged, measured only)."""

    def __init__(self, cond, marg, n_cal: int, alpha_sel: float) -> None:
        super().__init__(cond, marg, "cond")
        self.n_cal, self.alpha_sel = n_cal, alpha_sel
        self.prefix: list[int] = []
        self.route: str | None = None

    def _screen(self) -> str:
        z = self.prefix
        n = np.zeros((2, 2))
        for a, b in itertools.pairwise(z):
            n[a, b] += 1
        n0, n1 = n[0].sum(), n[1].sum()
        if n0 == 0 or n1 == 0:
            return "cond"
        p0, p1 = n[0, 1] / n0, n[1, 1] / n1
        pp = (n[0, 1] + n[1, 1]) / (n0 + n1)
        se = math.sqrt(max(pp * (1 - pp) * (1 / n0 + 1 / n1), 1e-12))
        return "marg" if norm.sf((p1 - p0) / se) < self.alpha_sel else "cond"

    def update(self, ev: int, z: int) -> None:
        if self.route is None:
            self.prefix.append(z)
            if len(self.prefix) >= self.n_cal:
                self.route = self._screen()
                self.decide = self.route
            return
        super().update(ev, z)

    @property
    def log_e(self) -> float:
        return 0.0 if self.route is None else super().log_e


# ----------------------------------------------------------------------------- consumer


@dataclass(frozen=True)
class Q1Spec:
    """Registry entry of one implemented (family, variant, null) evidence process."""

    family: str
    variant: str
    null: str
    kind: str
    validity: str  # PROVEN_DECLARED_CLASS | DOMINATED_BY_VALID | NOT_CLAIMED
    filtration: str
    transition_model: str
    stopping: str
    parameter_uncertainty: str
    selection_requirement: str
    deviations: str = ""
    needs_rho_bar: bool = False


class GapEvidence:
    """Consumer of the seam: feeds a core with in-order identified outcomes and exposes e-value/alarm/belief increments."""

    def __init__(
        self,
        spec: Q1Spec,
        build_core: Callable[[Ctx], object],
        *,
        rho_bar: float = DEFAULT_RHO_BAR,
        alpha_level: float | None = None,
        cell_width: float = CELL_WIDTH,
        selection: str = "undeclared",
    ) -> None:
        self.spec, self._build, self.rho_bar = spec, build_core, rho_bar
        self.alpha_level, self.cell_width = alpha_level, cell_width
        self.declare_selection(selection)
        self.target_null = spec.null
        self.core = None
        self._reset_counters()

    def _reset_counters(self) -> None:
        self.n_used = self.n_dropped_ooo = self.n_unidentified = 0
        self._all_declared, self.gaps = True, []
        self.first_alarm: dict | None = None
        self._mark = 0.0

    # ---- lifecycle
    def declare_selection(self, regime: str) -> None:
        if regime not in SELECTION_REGIMES:
            raise ValueError(f"selection regime must be one of {SELECTION_REGIMES}")
        self.selection = regime

    def bind(self, env: EnvSpec) -> None:
        ctx = Ctx(
            (1.0 + env.hurdle) / 2.0,
            env.T,
            max(1, env.budget.label_cap),
            self.rho_bar,
            self.cell_width,
        )
        self.core = self._build(ctx)
        self._reset_counters()

    # ---- evidence
    def observe(self, outcomes: Sequence[ReleasedOutcome]) -> None:
        if self.core is None:
            raise RuntimeError("bind(env) first")
        for o in outcomes:
            if o.z is None:
                self.n_unidentified += 1
                continue
            if o.order == "out_of_order":
                self.n_dropped_ooo += 1
                continue
            self._all_declared &= o.selection.propensity is not None
            self.core.update(o.label_round, o.z)
            self.n_used += 1
            if o.gap is not None:
                self.gaps.append(o.gap)
            if self.first_alarm is None and self.alarm():
                self.first_alarm = {
                    "label_round": o.label_round,
                    "release_round": o.release_round,
                    "n_used": self.n_used,
                }

    @property
    def log_e(self) -> float:
        return 0.0 if self.core is None else float(self.core.log_e)

    def alarm(self, alpha: float | None = None) -> bool:
        a = alpha if alpha is not None else (self.alpha_level or 0.1)
        return self.log_e >= -math.log(self.alpha_level or a)

    def belief_increment(self) -> float:
        cur = self.log_e
        inc, self._mark = cur - self._mark, cur
        return inc

    def report(self) -> dict:
        rep = self.core.report() if hasattr(self.core, "report") else {}
        return {"log_e": self.log_e, "n_used": self.n_used, "n_dropped_ooo": self.n_dropped_ooo,
                "n_unidentified": self.n_unidentified, "first_alarm": self.first_alarm, **rep}  # fmt: skip

    def contract_status(self, stream_spec=None) -> dict:
        """OUT_OF_CONTRACT reasons. ``stream_spec`` (evaluator side, optional) is read by the HARNESS, never by the policy."""
        why = []
        if self.selection not in IN_CONTRACT_REGIMES:
            why.append(f"selection regime {self.selection!r} is not predictable/exogenous")
        if self.n_used and not self._all_declared:
            why.append(
                "released outcomes carry no declared propensity: selection rule unverifiable"
            )
        if self.spec.kind == "slack_markov" and len(set(self.gaps)) > 1:
            why.append("gap-ignorant Markov-LR used with varying gaps")
        if stream_spec is not None:
            if stream_spec.delay.kind == "informative" or stream_spec.missing.kind == "informative":
                why.append("informative delay/missingness: gap g_i carries information about Z_i")
            if (
                self.spec.needs_rho_bar
                and stream_spec.dependence == "markov"
                and stream_spec.rho > self.rho_bar + 1e-12
            ):
                why.append(
                    f"stream rho {stream_spec.rho:g} exceeds declared rho_bar {self.rho_bar:g}"
                )
        return {
            "status": "OUT_OF_CONTRACT" if why else "IN_CONTRACT",
            "reasons": why,
            "validity_claim": self.spec.validity,
        }


# ----------------------------------------------------------------------------- identity -> implementation

COMMON_FILT = "G_i = sigma(in-order identified released outcomes, gaps, selection records); out-of-order outcomes dropped"
SEL_REQ = "next observed round predictable (G_{i-1}-measurable) or exogenously randomised with declared propensity; informative selection OUT_OF_CONTRACT"


def _mixture(ctx: Ctx, make: Callable[[], object], n: int = 4, prior: str = "uniform", basis: str = "ev",
             prune: float | None = None) -> StartMixture:  # fmt: skip
    pi, gw = start_weights(prior, n)
    if basis == "ev":
        trig = [("ev", int(j * ctx.T / n)) for j in range(n)]
    else:
        trig = [("idx", int(j * ctx.B / n)) for j in range(n)]
    return StartMixture(make, trig, pi, gw, prune)


def _lr(ctx, pred, cfg, rho=None):
    return lambda: LRStart(ctx, pred(), cfg.get("gap_source", "observed"), rho)


def _bet(ctx, pred, cfg, null, **kw):
    return lambda: BetStart(ctx, pred(), null, cfg.get("gap_source", "observed"), **kw)


def _per_start(null: str, kind: str, ctx: Ctx, cfg: dict, **kw):
    """(make_start) for predictor ``kind`` under ``null`` (marg -> certified LR, cond -> bet)."""
    rho = cfg.get("declared_rho_bar", ctx.rho_bar)
    s = cfg.get("smoothing", 0.02)
    preds = {
        "altgrid": lambda: AltGridPred(ctx.q0),
        "bucket": lambda: BucketPred(s),
        "tempered": lambda: TemperedPred(rho, s),
        "dirichlet": lambda: DirichletPred(0.5 + cfg.get("smoothing", 0.0)),
        "plugin": lambda: PluginPred(),
    }
    return (
        _lr(ctx, preds[kind], cfg, rho)
        if null == "marg"
        else _bet(ctx, preds[kind], cfg, "cond", **kw)
    )


def _core_factories(cfg: dict, null: str) -> dict[tuple[str, str], Callable[[Ctx], object]]:
    """{(family, variant): ctx -> core} for one configuration."""
    rho = cfg.get("declared_rho_bar")
    rad = cfg.get("envelope_radius", 0.0)
    est = "dirichlet" if cfg.get("estimator") == "dirichlet" else "plugin"
    S = int(cfg.get("max_starts", 16))
    prior = cfg.get("start_prior", "uniform")
    sel_a = cfg.get("selector_alpha", 0.05)

    def four(kind):  # 4 equal event-round starts (the Gap-Mix restart set)
        return lambda c: _mixture(c, _per_start(null, kind, c, cfg))

    def env_bet(c, pred, n_wallets=1, additive=True):
        r = rho if rho is not None else c.rho_bar
        mk = lambda: BetStart(
            c, pred(), "marg", cfg.get("gap_source", "observed"), r, rad, additive, n_wallets
        )
        return mk

    f: dict[tuple[str, str], Callable[[Ctx], object]] = {
        ("actual_gap_evidence", "exact_Pg_kernel"): four("altgrid"),
        ("actual_gap_evidence", "gap_bucketed_kernel"): four("bucket"),
        ("actual_gap_evidence", "gap_tempered_evidence"): four("tempered"),
        ("markov_transition_envelopes", "dirichlet_mixture_evidence"): four("dirichlet"),
    }
    if null == "marg":
        f[("markov_transition_envelopes", "lfd_envelope")] = lambda c: _mixture(
            c,
            env_bet(
                c,
                (lambda: DirichletPred(0.5)) if est == "dirichlet" else PluginPred,
                1,
                additive=False,
            ),
        )
        f[("markov_transition_envelopes", "interval_uncertainty_set")] = lambda c: _mixture(
            c, env_bet(c, lambda: BucketPred(0.02), 4, additive=True)
        )
        f[("markov_transition_envelopes", "plugin_slack_inflation")] = lambda c: SlackMarkovLR(
            c, cfg.get("envelope_radius", 0.0)
        )
    else:
        f[("markov_transition_envelopes", "lfd_envelope")] = lambda c: _mixture(
            c,
            _bet(
                c, (lambda: DirichletPred(0.5)) if est == "dirichlet" else PluginPred, cfg, "cond"
            ),
        )
        f[("markov_transition_envelopes", "interval_uncertainty_set")] = lambda c: _mixture(
            c, _bet(c, lambda: BucketPred(0.02), cfg, "cond", radius=rad, n_wallets=4)
        )
        f[("markov_transition_envelopes", "plugin_slack_inflation")] = lambda c: _mixture(
            c,
            lambda: SlackBet(
                c, PluginPred(), cfg.get("envelope_radius", 0.0), cfg.get("gap_source", "observed")
            ),
        )

    def n_starts(c):
        return max(1, min(S, c.B))

    def coarse(
        c,
    ):  # many exact-LR starts: coarser (still certified, looser) rho cells keep a run inside the CPU budget
        return replace(c, cell_width=max(c.cell_width, 0.02)) if S > 16 else c

    f[("restart_mixture_allocation", "e_cusum_markov_base")] = lambda c: _mixture(
        coarse(c), _per_start(null, "altgrid", coarse(c), cfg), n_starts(c), prior, "idx"
    )
    f[("restart_mixture_allocation", "adaptive_restart_budget")] = lambda c: _mixture(
        c, _cheap_start(null, c, cfg), n_starts(c), prior, "idx", prune=3.0
    )
    f[("restart_mixture_allocation", "e_sr_gap_weighted_starts")] = lambda c: _mixture(
        c, _cheap_start(null, c, cfg), n_starts(c), "gap_weighted", "ev"
    )
    f[("restart_mixture_allocation", "truncated_restart_window")] = lambda c: TrailingStarts(
        _per_start(null, "altgrid", coarse(c), cfg), S, c.B
    )

    def hazard(c):
        n = max(1, min(16, c.B))
        pi = hazard_weights(
            cfg.get("duration_prior", "geometric"), cfg.get("hazard_floor", 0.01), n
        )
        trig = [("ev", int(j * c.T / n)) for j in range(n)]
        return StartMixture(_cheap_start(null, c, cfg), trig, pi)

    for v in ("geometric_hazard_prior", "semi_markov_duration_prior"):
        f[("hazard_regime_duration", v)] = hazard

    def cond_core(c):
        return _mixture(c, _per_start("cond", "altgrid", c, cfg))

    def marg_core(c):
        return _mixture(c, _per_start("marg", "altgrid", c, cfg))

    def n_cal(c):
        return max(8, c.B // 5)

    f[("conditional_marginal_objective_selection", "dual_null_reporting")] = lambda c: DualCore(
        cond_core(c), marg_core(c), null
    )
    f[("conditional_marginal_objective_selection", "min_of_both_certificate")] = lambda c: MinCore(
        cond_core(c), marg_core(c), null
    )
    if cfg.get("selector_rule") == "min_of_both":
        f[("conditional_marginal_objective_selection", "dependence_test_router")] = f[
            ("conditional_marginal_objective_selection", "min_of_both_certificate")
        ]
    else:
        f[("conditional_marginal_objective_selection", "dependence_test_router")] = lambda c: (
            RouterCore(cond_core(c), marg_core(c), n_cal(c), sel_a)
        )
    return f


def _cheap_start(null: str, ctx: Ctx, cfg: dict):
    """Per-start process for many-start mixtures: bet e-process (envelope under marg, conditional under cond), altgrid bets."""
    rho = cfg.get("declared_rho_bar", ctx.rho_bar)
    return lambda: BetStart(ctx, AltGridPred(ctx.q0), null, cfg.get("gap_source", "observed"), rho)


def _spec(fam: str, var: str, null: str) -> Q1Spec:
    """Registry text for one implemented identity."""
    marg_lr = (
        "exact_Pg_kernel",
        "gap_bucketed_kernel",
        "gap_tempered_evidence",
        "dirichlet_mixture_evidence",
        "e_cusum_markov_base",
        "truncated_restart_window",
    )
    env_marg = ("lfd_envelope", "interval_uncertainty_set", "e_sr_gap_weighted_starts", "adaptive_restart_budget", "geometric_hazard_prior", "semi_markov_duration_prior")  # fmt: skip
    if fam == "conditional_marginal_objective_selection":
        kind = {
            "dual_null_reporting": "dual",
            "min_of_both_certificate": "min",
            "dependence_test_router": "router",
        }[var]
    elif null == "cond":
        kind = "cond_bet"
    elif var == "plugin_slack_inflation":
        kind = "slack_markov"
    elif var in marg_lr:
        kind = "marg_lr_certified"
    elif var in env_marg:
        kind = "marg_envelope_bet"
    else:
        raise KeyError((fam, var, null))
    validity, dev, trans = (
        "PROVEN_DECLARED_CLASS",
        "",
        "stationary two-state chain, skeleton kernel P^{g_i}",
    )
    par = "predictor is predictable (no parameter claim); declared rho_bar and q0 bound the null"
    if kind == "cond_bet":
        trans = "none (conditional null only): P(Z_i=1 | G_{i-1}, g_i) <= q0"
        par = "no nuisance parameter; predictor r is any G_{i-1}-measurable bet; gaps may be chosen adaptively from past released outcomes"
    elif kind == "marg_lr_certified":
        par = "certified supremum of the exact-gap likelihood over p<=q0, rho in [0, rho_bar] (declared) as denominator"
    elif kind == "marg_envelope_bet":
        par = "declared envelope u(prev, g) = sup over p<=q0, rho<=rho_bar (radius = extra slack)"
    elif kind == "slack_markov":
        validity, dev = (
            "NOT_CLAIMED",
            "gap-ignorant adjacent-step Markov-LR + sqrt(n) log slack; valid only for constant spacing",
        )
        par = "Markov-LR certified supremum over adjacent chains"
    elif kind in ("dual", "min"):
        validity = "PROVEN_DECLARED_CLASS" if kind == "dual" else "DOMINATED_BY_VALID"
        trans = "cond core: none; marg core: stationary two-state chain with P^{g_i}"
        par = "see the two cores"
    elif kind == "router":
        validity = "PROVEN_DECLARED_CLASS" if null == "cond" else "NOT_CLAIMED"
        trans = "route chosen on an independent calibration prefix; cores as in dual"
        par = "screen type-II error uncontrolled"
        dev = (
            ""
            if null == "cond"
            else "marg target: a missed dependence screen routes to the cond core, invalid under marg-only dependence"
        )
    if var == "plugin_slack_inflation" and null == "cond":
        dev = "dominated by the valid cond plug-in bet; slack = radius*sqrt(n) on log e"
        validity = "DOMINATED_BY_VALID"
    if var in ("lfd_envelope",) and null == "cond":
        dev = "envelope_radius inert under the cond null (no kernel uncertainty to inflate)"
    if var == "interval_uncertainty_set":
        dev = "interval = additive slack on the envelope per gap bucket {1,2-4,5-16,>16}; union bound realised as an equal-weight bucket-wallet mixture"
    if var in ("geometric_hazard_prior", "semi_markov_duration_prior"):
        dev = "hazard enters as restart (onset) weights only; hazard-aware belief transition T^g inside the Drift2Act filter is NOT implemented"
    if var == "adaptive_restart_budget":
        dev = "pruning only lowers the mixture (valid, no re-allocation); hypothesis of power gain from pruning is untestable by construction"
    if var == "e_sr_gap_weighted_starts":
        dev = "per-start process is the cheap envelope/cond bet, not the exact-gap LR"
    if var == "truncated_restart_window":
        dev = "prior mass 1/B per start (B=label cap), trailing window K=max_starts"
    if var in ("lfd_envelope", "interval_uncertainty_set"):
        dev += (
            ("; " if dev else "")
            + "null set is centred on the DECLARED rho_bar, not on the plug-in kernel (a data-centred null set cannot be certified)"
        )
    return Q1Spec(
        fam, var, null, kind, validity, COMMON_FILT, trans,
        "any stopping time of the released-order filtration (Ville)", par, SEL_REQ, dev,
        needs_rho_bar=kind in ("marg_lr_certified", "marg_envelope_bet"),
    )  # fmt: skip


IMPLEMENTED_FAMILIES = (
    "actual_gap_evidence",
    "markov_transition_envelopes",
    "restart_mixture_allocation",
    "conditional_marginal_objective_selection",
    "hazard_regime_duration",
)
_PROBE = _core_factories({}, "marg")
IMPLEMENTED_VARIANTS = tuple(sorted(_PROBE))
BLOCKED_VARIANTS = {
    ("actual_gap_evidence", "full_sup_denominator"): "closed construction (FL-016): do_not_repeat_without a new mechanistic hypothesis",
    ("actual_gap_evidence", "rho_robust_gapmix"): "closed construction (FL-022): do_not_repeat_without a new mechanistic hypothesis",
}  # fmt: skip


class Q1NotImplemented(NotImplementedError):
    pass


def spec_for(identity: dict) -> Q1Spec:
    key = (identity["family"], identity["variant"])
    if key not in IMPLEMENTED_VARIANTS:
        raise Q1NotImplemented(
            BLOCKED_VARIANTS.get(key, f"{key} has no label-outcome implementation")
        )
    return _spec(*key, identity["target_null"])


def is_implemented(identity: dict) -> bool:
    return (
        identity.get("hook") == "d2a.evidence_log_lik"
        and (identity["family"], identity["variant"]) in IMPLEMENTED_VARIANTS
    )


def build_evidence(identity: dict, *, alpha_level: float | None = None, cell_width: float = CELL_WIDTH,
                   selection: str = "undeclared") -> GapEvidence:  # fmt: skip
    """Registry identity -> :class:`GapEvidence` (unbound; ``bind(env)`` before use)."""
    spec = spec_for(identity)
    cfg, null = dict(identity["configuration"]), identity["target_null"]
    fam = _core_factories(cfg, null)[(identity["family"], identity["variant"])]
    if identity["variant"] == "min_of_both_certificate" or (
        identity["variant"] == "dependence_test_router"
        and cfg.get("selector_rule") == "min_of_both"
    ):
        alpha_level = alpha_level or cfg.get(
            "selector_alpha"
        )  # here selector_alpha is the certificate level
    return GapEvidence(
        spec, fam, rho_bar=cfg.get("declared_rho_bar", DEFAULT_RHO_BAR), alpha_level=alpha_level,
        cell_width=cell_width, selection=selection,
    )  # fmt: skip


def registry_entries() -> list[dict]:
    out = []
    for fam, var in IMPLEMENTED_VARIANTS:
        for null in ("cond", "marg"):
            out.append(asdict(_spec(fam, var, null)))
    return out


REGISTRY_PATH = (
    Path(__file__).resolve().parents[4] / "docs" / "d2a_rar" / "registry" / "Q1_EVIDENCE_IMPLS.json"
)


def registry_document() -> dict:
    return {
        "schema": 1,
        "module": "shiftlab.bench.contract.evidence_q1",
        "seam": "shiftlab.bench.contract.evidence_seam",
        "blocked": {f"{a}.{b}": why for (a, b), why in BLOCKED_VARIANTS.items()},
        "common_assumptions": [COMMON_FILT, SEL_REQ],
        "entries": registry_entries(),
    }


def write_registry(path: Path = REGISTRY_PATH) -> Path:
    path.write_text(
        json.dumps(registry_document(), indent=1, sort_keys=True) + "\n", encoding="utf8"
    )
    return path


__all__ = [
    "BLOCKED_VARIANTS",
    "IMPLEMENTED_VARIANTS",
    "Ctx",
    "GapEvidence",
    "Q1NotImplemented",
    "Q1Spec",
    "build_evidence",
    "is_implemented",
    "spec_for",
    "write_registry",
]
