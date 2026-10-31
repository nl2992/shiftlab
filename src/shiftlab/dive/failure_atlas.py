"""Failure Atlas v1 (R4 exploratory discovery; no novelty/theorem/efficacy claim).

Protocol: docs/failure_atlas_v1_protocol.md (Amendments 1 and 2). Family 1 = late or transient
candidate advantage on the delayed budgeted switching contract of ``switching_explore``; family 2 =
recurrent regimes (2-state Markov chain, initial state off). Methods (baselines and references)
only ever see ``(t, released labels)`` through ``switching_explore.run``; the regime path lives in
the evaluator-only ``Truth``.
"""

from __future__ import annotations

import bisect
import itertools
import math
import zlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from functools import cache

import numpy as np

from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess
from shiftlab.dive.switching_explore import (
    AllOnsetEDetector,
    Config,
    EpisodeComposition,
    Method,
    Stream,
    bernoulli_grid_spec,
    build_method,
    clairvoyant_actions,
    make_bernoulli_stream,
    paired_ci,
    run,
    score_actions,
    started_gate,
    uniform_calendar,
    wilson,
)

# ----------------------------------------------------------------------------- axes

T_DEFAULT = 1000
ONSETS = (0.1, 0.3, 0.6, 0.8)
DURATIONS = (0.15, 0.3, 0.6, 1.0)  # 1.0 = to the end of the horizon
EFFECTS: dict[str, tuple[float, float]] = {  # (P(Y=1) off, P(Y=1) on)
    "strong": (0.1, 0.9),
    "medium": (0.3, 0.7),
    "weak": (0.4, 0.6),
}
OFF_TYPES = ("neutral", "harmful")
DELAYS = (1, 10, 50)
BUDGET_FRACS = (0.05, 0.1, 0.25)
SWITCH_COSTS = (0.05, 0.1, 0.5)
JITTER = 0.05

EASIEST: dict[str, object] = {
    "onset": 0.1,
    "duration": 1.0,
    "effect": "strong",
    "d": 1,
    "budget_frac": 0.25,
    "s": 0.05,
}
AXES = tuple(EASIEST)

SAFETY_GATED = (
    "episode_geo",
    "episode_equal",
    "episode_front",
    "allonset_edetector",
    "c2_rho0.75",
    "c1_hmm_cs",
)
UNGATED = ("periodic_mean", "dal_restart", "pacing_bernoulli")
FLOOR = "no_switch"
ALL_METHODS = (FLOOR, *UNGATED, *SAFETY_GATED)
REFERENCES = ("ref_law", "ref_family", "ref_valid", "ref_regime_clairvoyant")
NULL_REFS = ("ref_family", "ref_valid")  # references evaluated on null twins

MATERIAL = 0.01  # per-round cost units
FP_SLACK = 0.05  # reference null-twin false-promotion allowance above alpha
KAPPA_GRID = (0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01)
KAPPA_DEFAULT = 0.1


# ----------------------------------------------------------------------------- cells


@dataclass(frozen=True)
class CellSpec:
    onset: float
    duration: float
    effect: str
    off_type: str
    d: int
    budget_frac: float
    s: float
    T: int = T_DEFAULT
    c: float = 0.01
    h: float = 0.1
    alpha: float = 0.1
    null: bool = False

    family = 1  # not a dataclass field
    axes = AXES
    easiest_levels = EASIEST

    @property
    def B(self) -> int:
        return round(self.budget_frac * self.T)

    @property
    def p_pair(self) -> tuple[float, float]:
        """(P(Y=1) off, P(Y=1) on)."""
        off, on = EFFECTS[self.effect]
        return (0.5 if self.off_type == "neutral" else off, on)

    @property
    def cell_id(self) -> str:
        base = (
            f"on{self.onset:g}_L{self.duration:g}_{self.effect}_{self.off_type}"
            f"_d{self.d}_b{self.budget_frac:g}_s{self.s:g}"
        )
        if self.T != T_DEFAULT:
            base += f"_T{self.T}"
        return base + ("_NULL" if self.null else "")

    @property
    def stable_index(self) -> int:
        return zlib.crc32(self.cell_id.encode("utf-8"))

    def config(self, seed: int = 0) -> Config:
        return Config(
            T=self.T,
            B=self.B,
            d=self.d,
            c=self.c,
            s=self.s,
            h=self.h,
            alpha=self.alpha,
            seed=int(seed),
        )

    def null_twin(self) -> CellSpec:
        """Same d, B, s, effect, costs; candidate never favourable, off state harmful.

        Onset and duration are irrelevant for a never-on path, so the twin is canonicalised to
        the first onset/duration level (twins of cells that differ only there are identical and
        share one evaluation).
        """
        return replace(
            self,
            onset=ONSETS[0],
            duration=DURATIONS[0],
            off_type="harmful",
            null=True,
        )

    def easiest(self, axis: str) -> CellSpec:
        if axis not in EASIEST:
            raise ValueError(f"unknown axis {axis!r}; choose from {AXES}")
        return replace(self, **{axis: EASIEST[axis]})


def all_cells(T: int = T_DEFAULT) -> list[CellSpec]:
    return [
        CellSpec(on, du, ef, off, d, bf, s, T=T)
        for on, du, ef, off, d, bf, s in itertools.product(
            ONSETS, DURATIONS, EFFECTS, OFF_TYPES, DELAYS, BUDGET_FRACS, SWITCH_COSTS
        )
    ]


def neighbours(cell):
    """Cells that differ from ``cell`` by one level on exactly one axis (grid neighbours)."""
    if cell.family == 2:
        levels = {
            "rate": RATES2,
            "effect": tuple(EFFECTS),
            "off_type": OFF_TYPES,
            "d": DELAYS,
            "budget_frac": BUDGET_FRACS,
            "s": SWITCH_COSTS,
        }
    else:
        levels = {
            "onset": ONSETS,
            "duration": DURATIONS,
            "effect": tuple(EFFECTS),
            "off_type": OFF_TYPES,
            "d": DELAYS,
            "budget_frac": BUDGET_FRACS,
            "s": SWITCH_COSTS,
        }
    out = []
    for axis, lv in levels.items():
        i = lv.index(getattr(cell, axis))
        for j in (i - 1, i + 1):
            if 0 <= j < len(lv):
                out.append(replace(cell, **{axis: lv[j]}))
    return out


def _onset_round(cell: CellSpec, jitter: float) -> int:
    return int(np.clip(round((cell.onset + jitter) * cell.T), 1, cell.T - 1))


def _end_round(cell: CellSpec, tau: int) -> int:
    if cell.duration >= 1.0:
        return cell.T
    return min(cell.T, tau + round(cell.duration * cell.T))


def make_family1_stream(cell: CellSpec, seed: int) -> Stream:
    """Scripted regime path with onset jitter; the oracle path is evaluator-only (``Truth``)."""
    rng = np.random.default_rng([int(seed), cell.stable_index])
    jitter = float(rng.uniform(-JITTER, JITTER))  # always drawn so twins stay aligned
    path = np.zeros(cell.T, dtype=int)
    if not cell.null:
        tau = _onset_round(cell, jitter)
        path[tau : _end_round(cell, tau)] = 1
    return make_bernoulli_stream(rng, cell.T, cell.p_pair, path=path)


# ----------------------------------------------------------------------------- family 2
# Amendment 2, item 4: recurrent regimes. The regime path is a symmetric 2-state Markov chain
# (``a = b = rate``) whose initial state (round 1) is off; the candidate is favourable in "on".

RATES2 = (0.002, 0.005, 0.02)
FAMILY2_TAG = (
    20002  # family tag in the rng seed sequence: family-2 streams never reuse family-1 draws
)
EASIEST2: dict[str, object] = {
    "rate": 0.002,
    "effect": "strong",
    "d": 1,
    "budget_frac": 0.25,
    "s": 0.05,
}
AXES2 = tuple(EASIEST2)


@dataclass(frozen=True)
class Family2CellSpec:
    rate: float
    effect: str
    off_type: str
    d: int
    budget_frac: float
    s: float
    T: int = T_DEFAULT
    c: float = 0.01
    h: float = 0.1
    alpha: float = 0.1
    null: bool = False

    family = 2
    axes = AXES2
    easiest_levels = EASIEST2

    @property
    def B(self) -> int:
        return round(self.budget_frac * self.T)

    @property
    def p_pair(self) -> tuple[float, float]:
        off, on = EFFECTS[self.effect]
        return (0.5 if self.off_type == "neutral" else off, on)

    @property
    def cell_id(self) -> str:
        base = (
            f"f2_r{self.rate:g}_{self.effect}_{self.off_type}"
            f"_d{self.d}_b{self.budget_frac:g}_s{self.s:g}"
        )
        if self.T != T_DEFAULT:
            base += f"_T{self.T}"
        return base + ("_NULL" if self.null else "")

    @property
    def stable_index(self) -> int:
        return zlib.crc32(self.cell_id.encode("utf-8"))

    def config(self, seed: int = 0) -> Config:
        return Config(
            T=self.T,
            B=self.B,
            d=self.d,
            c=self.c,
            s=self.s,
            h=self.h,
            alpha=self.alpha,
            seed=int(seed),
        )

    def null_twin(self) -> Family2CellSpec:
        """Same d, B, s, effect, costs; the candidate is never on and the off state is harmful."""
        return replace(self, rate=RATES2[0], off_type="harmful", null=True)

    def easiest(self, axis: str) -> Family2CellSpec:
        if axis not in EASIEST2:
            raise ValueError(f"unknown axis {axis!r}; choose from {AXES2}")
        return replace(self, **{axis: EASIEST2[axis]})


def all_cells2(T: int = T_DEFAULT) -> list[Family2CellSpec]:
    return [
        Family2CellSpec(r, ef, off, d, bf, s, T=T)
        for r, ef, off, d, bf, s in itertools.product(
            RATES2, EFFECTS, OFF_TYPES, DELAYS, BUDGET_FRACS, SWITCH_COSTS
        )
    ]


def make_family2_stream(cell: Family2CellSpec, seed: int) -> Stream:
    """Markov regime path with initial state off (round 1); the null twin never turns on.

    The flip uniforms are always drawn (the twin consumes the same number of draws); the twin has its
    own cell id and therefore its own draws.
    """
    rng = np.random.default_rng([int(seed), FAMILY2_TAG, cell.stable_index])
    u = rng.random(cell.T)
    path = np.zeros(cell.T, dtype=int)
    if not cell.null:
        state = 0
        for t in range(1, cell.T):
            if u[t] < cell.rate:
                state = 1 - state
            path[t] = state
    return make_bernoulli_stream(rng, cell.T, cell.p_pair, path=path)


def make_stream(cell, seed: int) -> Stream:
    return make_family2_stream(cell, seed) if cell.family == 2 else make_family1_stream(cell, seed)


# ----------------------------------------------------------------------------- seeds

SEED_RANGES = {
    "discovery": (0, 10**5),
    "development": (10**5, 2 * 10**5),
    "mechanism": (2 * 10**5, 3 * 10**5),
    "confirmation": (9 * 10**5, 10**6),
}


class ConfirmationSeedsLocked(RuntimeError):
    """Confirmation seeds were requested without an explicit, frozen-manifest override."""


def seeds(stage: str, n: int, offset: int = 0, allow_confirmation: bool = False) -> tuple[int, ...]:
    if stage not in SEED_RANGES:
        raise ValueError(f"unknown stage {stage!r}")
    if stage == "confirmation" and not allow_confirmation:
        raise ConfirmationSeedsLocked("confirmation seeds are locked for a frozen manifest")
    lo, hi = SEED_RANGES[stage]
    if offset < 0 or n < 0 or lo + offset + n > hi:
        raise ValueError(f"seed request outside the {stage} partition")
    return tuple(range(lo + offset, lo + offset + n))


def guard_seeds(sd: Sequence[int], allow_confirmation: bool = False) -> None:
    lo, hi = SEED_RANGES["confirmation"]
    if not allow_confirmation and any(lo <= int(x) < hi for x in sd):
        raise ConfirmationSeedsLocked("confirmation-range seed passed without allow_confirmation")


# ----------------------------------------------------------------------------- references


def family_hypotheses(T: int) -> np.ndarray:
    """Rows ``(tau, end, p_off, p_on)``: full family grid plus null members (tau == end == T)."""
    taus = sorted({int(np.clip(round(k * T / 50), 1, T - 1)) for k in range(1, 50)})
    rows = []
    for tau in taus:
        for du in DURATIONS:
            end = T if du >= 1.0 else min(T, tau + round(du * T))
            for off_p, on_p in EFFECTS.values():
                for off in OFF_TYPES:
                    rows.append((tau, end, 0.5 if off == "neutral" else off_p, on_p))
    for off_p, on_p in EFFECTS.values():
        for off in OFF_TYPES:
            rows.append((T, T, 0.5 if off == "neutral" else off_p, on_p))  # null members
    # duplicates arise when durations are truncated at T; keep the prior uniform over distinct paths
    return np.unique(np.asarray(rows, dtype=float), axis=0)


def law_hypotheses(cell: CellSpec, n_jitter: int = 11) -> np.ndarray:
    """The cell's own law: onset-jitter grid with the cell's duration, effect and off type."""
    off_p, on_p = cell.p_pair
    taus = sorted({_onset_round(cell, j) for j in np.linspace(-JITTER, JITTER, n_jitter)})
    rows = [(tau, _end_round(cell, tau), off_p, on_p) for tau in taus]
    return np.asarray(rows, dtype=float)


class _Tables:
    """Per-hypothesis round tables, shape (T, H): log-lik, instant benefit, favourable-now flag."""

    def __init__(self, hyp: np.ndarray, T: int, h: float):
        tau, end, p_off, p_on = (hyp[:, i] for i in range(4))
        t0 = np.arange(T)[:, None]
        on = (t0 >= tau[None, :]) & (t0 < end[None, :])
        P = np.where(on, p_on[None, :], p_off[None, :])
        self.log_p1 = np.log(P).astype(np.float32)  # float32 tables keep per-worker memory small
        self.log_p0 = np.log1p(-P).astype(np.float32)
        benefit = 2.0 * P - 1.0  # E[-D_u | hypothesis]
        self.benefit = benefit.astype(np.float32)
        self.fav = (P > (1.0 + h) / 2.0).astype(np.float32)  # regime_mean < -h


_TABLE_CACHE: dict[tuple, _Tables] = {}


def _tables(hyp: np.ndarray, T: int, h: float) -> _Tables:
    key = (hyp.tobytes(), T, round(h, 9))
    tb = _TABLE_CACHE.get(key)
    if tb is None:
        if len(_TABLE_CACHE) > 6:
            _TABLE_CACHE.clear()
        tb = _TABLE_CACHE[key] = _Tables(hyp, T, h)
    return tb


class FilterReference(Method):
    """Exact Bayesian filter over scripted-path hypotheses, using released D values only.

    Plan value (Amendment 1): with ``m_v = E_post[benefit_v]`` and ``cum_u = sum_{v=t}^{u} m_v``,
    promoting at ``t`` and reverting after round ``u`` is worth ``cum_u - 2 s`` (a promote-then-revert
    plan), and the value of promoting is the maximum over ``u in [t, T]``. Promote (from 0) when
    that maximum exceeds ``margin``, the posterior expected current benefit is positive, and
    ``P(candidate favourable now) >= 1 - kappa``. Demote (from 1) when reverting now beats every
    stay-then-revert plan by more than ``margin``: every revert round ``u < T`` has ``cum_u <
    -margin`` and staying to the end has ``cum_T < -(s + margin)``. Queries: uniform calendar of
    ``B`` rounds in ``[1, T - d]``.
    """

    def __init__(
        self,
        hypotheses: np.ndarray,
        prior: np.ndarray | None = None,
        promote_margin: float = 0.0,
        query: str = "uniform",
        kappa: float = 1.0,
        name: str = "ref_filter",
    ):
        if query != "uniform":
            raise ValueError("only the uniform calendar is implemented")
        self.hyp = np.asarray(hypotheses, dtype=float)
        if prior is None:
            prior = np.full(len(self.hyp), 1.0 / len(self.hyp))
        prior = np.asarray(prior, dtype=float)
        if prior.shape != (len(self.hyp),) or np.any(prior < 0) or prior.sum() <= 0:
            raise ValueError("bad prior")
        self.prior = prior / prior.sum()
        self.margin = float(promote_margin)
        self.kappa = float(kappa)
        self.name = name

    def _init(self) -> None:
        c = self.cfg
        self.tb = _tables(self.hyp, c.T, c.h)
        with np.errstate(divide="ignore"):
            self.logw = np.log(self.prior)
        self.post = self.prior.copy()
        self._refresh_mben()
        self.dirty = False
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.act = 0

    def _refresh_mben(self) -> None:
        self.mben = (self.tb.benefit @ self.post.astype(np.float32)).astype(float)  # (T,)

    def plan_values(self, t: int) -> np.ndarray:
        """``cum_u`` for u = t..T under the current posterior (no switch costs)."""
        return np.cumsum(self.mben[t - 1 :])

    def decide(self, t: int, released):
        c, tb = self.cfg, self.tb
        for ev, x in released:
            self.logw = self.logw + (tb.log_p1[ev - 1] if x < 0 else tb.log_p0[ev - 1])
            self.dirty = True
        if self.dirty:
            w = np.exp(self.logw - self.logw.max())
            self.post = w / w.sum()
            self._refresh_mben()
            self.dirty = False
        cum = self.plan_values(t)
        if self.act == 0:
            if (
                float(cum.max()) - 2.0 * c.s > self.margin
                and float(self.mben[t - 1]) > 0.0
                and float(self.post @ tb.fav[t - 1]) >= 1.0 - self.kappa
            ):
                self.act = 1
        else:
            stay_to_end_bad = float(cum[-1]) < -(c.s + self.margin)
            early_revert_bad = len(cum) == 1 or float(cum[:-1].max()) < -self.margin
            if stay_to_end_bad and early_revert_bad:
                self.act = 0
        return self.act, t in self.cal


def family2_hypotheses() -> np.ndarray:
    """Rows ``(rate, p_off, p_on)``: rate in RATES2 x effect x off type, plus null members (rate 0)."""
    rows = []
    for rate in (*RATES2, 0.0):  # rate 0.0 = the candidate is never on
        for off_p, on_p in EFFECTS.values():
            for off in OFF_TYPES:
                rows.append((rate, 0.5 if off == "neutral" else off_p, on_p))
    return np.unique(np.asarray(rows, dtype=float), axis=0)


class HMMFilterReference(Method):
    """Exact forward filter over a finite family of symmetric 2-state Markov regime laws.

    Hypotheses are rows ``(rate, p_off, p_on)``; the regime starts off at round 1 and flips with
    probability ``rate`` per round (``a = b``). Released labels (queried rounds only, after the delay)
    update the joint posterior over (hypothesis, state) exactly, with unqueried rounds marginalised.
    Plan value (Amendment 1, adapted to the HMM): ``m_u = E_post[benefit_u | released]`` is the
    predictive benefit of round ``u`` from the filtered state; promoting at ``t`` and reverting after
    ``u`` is worth ``cum_u - 2 s``. Promote / demote rules, ``kappa`` gate and queries are those of
    :class:`FilterReference`.
    """

    def __init__(
        self,
        hypotheses: np.ndarray,
        prior: np.ndarray | None = None,
        promote_margin: float = 0.0,
        kappa: float = 1.0,
        name: str = "ref_hmm_filter",
    ):
        self.hyp = np.asarray(hypotheses, dtype=float)
        if self.hyp.ndim != 2 or self.hyp.shape[1] != 3:
            raise ValueError("hypotheses must have rows (rate, p_off, p_on)")
        if prior is None:
            prior = np.full(len(self.hyp), 1.0 / len(self.hyp))
        prior = np.asarray(prior, dtype=float)
        if prior.shape != (len(self.hyp),) or np.any(prior < 0) or prior.sum() <= 0:
            raise ValueError("bad prior")
        self.prior = prior / prior.sum()
        self.margin = float(promote_margin)
        self.kappa = float(kappa)
        self.name = name

    def _init(self) -> None:
        c = self.cfg
        self.rate, self.p_off, self.p_on = (self.hyp[:, i] for i in range(3))
        self.lam = 1.0 - 2.0 * self.rate
        thr = (1.0 + c.h) / 2.0
        self.fav_on = (self.p_on > thr).astype(float)
        self.fav_off = (self.p_off > thr).astype(float)
        with np.errstate(divide="ignore"):
            self.logw = np.log(self.prior)
        self.p1 = np.zeros(len(self.hyp))  # P(S = on | released, h) at event ``last_ev``
        self.last_ev = 1  # the regime is off at round 1 (known to the family, not data)
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.act = 0
        self._refresh()

    def _refresh(self) -> None:
        c = self.cfg
        w = np.exp(self.logw - self.logw.max())
        self.post = w / w.sum()
        u = np.arange(self.last_ev, c.T + 1)
        q = 0.5 + (self.p1[:, None] - 0.5) * self.lam[:, None] ** (u[None, :] - self.last_ev)
        P = self.p_off[:, None] + (self.p_on - self.p_off)[:, None] * q
        self.mben = self.post @ (2.0 * P - 1.0)  # index t - last_ev <-> round t
        self.pfav = self.post @ (q * self.fav_on[:, None] + (1.0 - q) * self.fav_off[:, None])

    def _update(self, ev: int, x: float) -> None:
        q = 0.5 + (self.p1 - 0.5) * self.lam ** (ev - self.last_ev)
        if x < 0:
            l_off, l_on = self.p_off, self.p_on
        else:
            l_off, l_on = 1.0 - self.p_off, 1.0 - self.p_on
        lik = (1.0 - q) * l_off + q * l_on
        self.logw = self.logw + np.log(lik)
        self.p1 = q * l_on / lik
        self.last_ev = ev

    def plan_values(self, t: int) -> np.ndarray:
        return np.cumsum(self.mben[t - self.last_ev :])

    def decide(self, t: int, released):
        c = self.cfg
        if released:
            for ev, x in released:
                self._update(ev, x)
            self._refresh()
        i = t - self.last_ev
        cum = np.cumsum(self.mben[i:])
        if self.act == 0:
            if (
                float(cum.max()) - 2.0 * c.s > self.margin
                and float(self.mben[i]) > 0.0
                and float(self.pfav[i]) >= 1.0 - self.kappa
            ):
                self.act = 1
        else:
            stay_to_end_bad = float(cum[-1]) < -(c.s + self.margin)
            early_revert_bad = len(cum) == 1 or float(cum[:-1].max()) < -self.margin
            if stay_to_end_bad and early_revert_bad:
                self.act = 0
        return self.act, t in self.cal


def law2_hypotheses(cell: Family2CellSpec) -> np.ndarray:
    """The cell's own law: the generating (rate, effect, off type); nothing else is known."""
    off_p, on_p = cell.p_pair
    return np.asarray([(cell.rate, off_p, on_p)], dtype=float)


def build_ref_law(cell):
    if cell.family == 2:
        return HMMFilterReference(law2_hypotheses(cell), name="ref_law")
    return FilterReference(law_hypotheses(cell), name="ref_law")


def build_ref_family(T: int, kappa: float, family: int = 1):
    if family == 2:
        return HMMFilterReference(family2_hypotheses(), kappa=kappa, name="ref_family")
    return FilterReference(family_hypotheses(T), kappa=kappa, name="ref_family")


def build_ref_family_for(cell, kappa: float):
    return build_ref_family(cell.T, kappa, cell.family)


# ----------------------------------------------------------------------------- R_valid
# Amendment 2, item 1. A valid gated method that receives the declared family prior only as
# mixture weights fixed before data. It never sees truth.


@cache
def _kelly_cached(p_on: float, h: float) -> float:
    return kelly_stake(p_on, h)


def family_kelly_stakes(h: float) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Distinct Kelly stakes of the family's effect levels against the boundary null, equal weights."""
    st = sorted({round(_kelly_cached(on_p, h), 6) for _, on_p in EFFECTS.values()})
    return tuple(st), tuple(1.0 / len(st) for _ in st)


def set_stake_mixture(proc: VectorizedStartedMixtureEProcess, stakes, weights):
    """Install a fixed stake mixture on an unused e-process instance (before any data)."""
    st, w = np.asarray(stakes, dtype=float), np.asarray(weights, dtype=float)
    if (
        proc.time != 0
        or st.ndim != 1
        or not len(st)
        or np.any(st < 0)
        or np.any(st >= 1)
        or w.shape != st.shape
        or np.any(w <= 0)
        or not np.isclose(w.sum(), 1.0)
    ):
        raise ValueError("stake mixture must be fixed before data, in [0,1), with positive weights")
    proc.stakes, proc.stake_weights = st, w
    proc.log_stake_weights = np.log(w)
    proc.log_wealth = np.zeros((len(proc.starts), len(st)), dtype=float)
    return proc


def family1_start_design(cfg: Config) -> tuple[tuple[int, ...], tuple[float, ...]]:
    """Family-1 onset prior (4 levels x uniform jitter) mapped to label indices by the uniform calendar."""
    cal = sorted(uniform_calendar(cfg.T, cfg.B, cfg.d))
    counts: dict[int, int] = {}
    jit = np.linspace(-JITTER, JITTER, 21)
    for level in ONSETS:
        for j in jit:
            tau = int(np.clip(round((level + float(j)) * cfg.T), 1, cfg.T - 1))
            k = bisect.bisect_left(cal, tau)  # calendar labels strictly before the onset round
            k = min(k, max(0, cfg.B - 1))
            counts[k] = counts.get(k, 0) + 1
    starts = tuple(sorted(counts))
    tot = float(sum(counts.values()))
    return starts, tuple(counts[k] / tot for k in starts)


def valid_gate(cfg: Config, starts, weights, alpha: float | None = None):
    proc = VectorizedStartedMixtureEProcess(
        bound=1.0 + cfg.h,
        alpha=cfg.alpha if alpha is None else alpha,
        starts=tuple(int(x) for x in starts),
        weights=tuple(float(x) for x in weights),
    )
    return set_stake_mixture(proc, *family_kelly_stakes(cfg.h))


class RValidFamily1(EpisodeComposition):
    """``episode_front`` decision rule (alpha on episode 0, economic check, rollback) with the family prior.

    Start weights = family onset prior mapped through the uniform calendar; stake weights = mixture
    of the Kelly stakes of the family effect levels. Both are fixed from the config alone.
    """

    def __init__(self):
        super().__init__("front")
        self.name = "ref_valid"

    def _new_episode(self, j: int, start: int) -> None:
        super()._new_episode(j, start)  # alpha_j = alpha for j == 0, none afterwards (front)
        if j == 0:
            self.ep = valid_gate(self.cfg, *family1_start_design(self.cfg))


class RValidFamily2(Method):
    """Per-episode started gate with family-Kelly stakes plus a Page-CUSUM rollback (family 2).

    Episode ``j`` runs a started-mixture e-process at level ``alpha 2^-(j+1)`` (union bound over
    episodes), the repository uniform start grid, and the family-Kelly stake mixture. Promotion needs
    an alarm and the economic check; after promotion a one-sided Page CUSUM on ``D + h`` (reference
    ``-h``, threshold ``cusum_threshold``) triggers rollback and a fresh episode. Queries: uniform
    calendar. Validity across episodes is a research target, as for the repository baselines.
    """

    name = "ref_valid"

    def __init__(self, cusum_threshold: float = 2.0):
        self.cusum_threshold = float(cusum_threshold)

    def _new_episode(self, j: int, start: int) -> None:
        c = self.cfg
        self.j, self.ep_start, self.ep_labels = j, start, []
        base = started_gate(1.0 + c.h, c.alpha * 2.0 ** -(j + 1), c.B)
        self.ep = valid_gate(c, base.starts, base.weights, alpha=base.alpha)

    def _init(self) -> None:
        c = self.cfg
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.act, self.promo_t, self.cus = 0, 0, 0.0
        self._new_episode(0, 0)

    def decide(self, t: int, released):
        c = self.cfg
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start:
                    self.ep.update(-x - c.h)
                    self.ep_labels.append(x)
            elif ev >= self.promo_t:
                self.cus = max(0.0, self.cus + x + c.h)
        if self.act == 0:
            if self.ep.alarm and self.ep_labels:
                ben = -float(np.mean(self.ep_labels[-10:]))
                if self.econ_ok(t, ben):
                    self.act, self.promo_t, self.cus = 1, t, 0.0
        elif self.cus >= self.cusum_threshold:
            self.act, self.cus = 0, 0.0
            self._new_episode(self.j + 1, t)
        return self.act, t in self.cal


def build_ref_valid(cell) -> Method:
    return RValidFamily2() if cell.family == 2 else RValidFamily1()


# ----------------------------------------------------------------------------- R6 baselines (lazy)

_R6_CACHE: tuple[dict, str | None] | None = None
R6_PLACEHOLDERS = {  # R6 registry name -> BASELINE_REGISTRY placeholder it supersedes
    "gong_zhang_paid_obs": "gong_zhang_delayed",
    "qiu_delayed_movement": "qiu_et_al_delayed",
    "ryabchenko_capacity": "ryabchenko_delayed_wrapper",
    "online_fwer_spending": "online_fwer_comparator",
}


def r6_methods() -> dict:
    """``{name: (factory(cfg) -> Method, gated, notes)}`` from ``atlas_r6_baselines``, or ``{}``."""
    global _R6_CACHE
    if _R6_CACHE is None:
        try:
            from shiftlab.dive.atlas_r6_baselines import R6_METHODS

            _R6_CACHE = (dict(R6_METHODS), None)
        except Exception as exc:  # noqa: BLE001 - a missing or broken R6 module is a logged skip
            _R6_CACHE = ({}, f"R6 baselines skipped: {type(exc).__name__}: {exc}")
    return _R6_CACHE[0]


def r6_status() -> str:
    r6_methods()
    assert _R6_CACHE is not None
    return _R6_CACHE[1] or f"R6 baselines loaded: {', '.join(_R6_CACHE[0])}"


def gated_methods() -> tuple[str, ...]:
    return (*SAFETY_GATED, *(k for k, v in r6_methods().items() if v[1]))


def ungated_methods() -> tuple[str, ...]:
    return (*UNGATED, *(k for k, v in r6_methods().items() if not v[1]))


def all_method_names() -> tuple[str, ...]:
    return (FLOOR, *ungated_methods(), *gated_methods())


def make_method(name: str, spec, cfg: Config) -> Method:
    r6 = r6_methods()
    if name in r6:
        return r6[name][0](cfg)
    return build_method(name, spec)


def baseline_registry() -> list[dict]:
    """``BASELINE_REGISTRY`` with the R6 placeholders updated to ``implemented`` when R6 loads."""
    reg = [dict(r) for r in BASELINE_REGISTRY]
    for name, (_, gated, notes) in r6_methods().items():
        entry = {
            "name": name,
            "status": "implemented",
            "guarantee": "gated (false-promotion control; see source audit)"
            if gated
            else "none (ungated)",
            "role": "safety-gated" if gated else "ungated",
            "notes": notes,
        }
        old = R6_PLACEHOLDERS.get(name)
        idx = next((i for i, r in enumerate(reg) if r["name"] == old), None)
        if idx is None:
            reg.append(entry)
        else:
            reg[idx] = entry
    return reg


# ----------------------------------------------------------------------------- evaluation


def _rec(r) -> dict:
    return {
        "cost": r.cost,
        "fp": int((r.fp_regime or 0) > 0),
        "queries": r.queries,
        "switches": r.switches,
        "promotions": r.promotions,
    }


def _empty() -> dict[str, list]:
    return {"cost": [], "fp": [], "queries": [], "switches": [], "promotions": []}


_NULL_CACHE: dict[tuple, dict] = {}


def evaluate_cell(
    cell,
    seed_list: Sequence[int],
    methods: Sequence[str] | None = None,
    refs: Sequence[str] | None = None,
    *,
    kappa: float = KAPPA_DEFAULT,
    with_null: bool = True,
    null_result: dict | None = None,
    extra_methods: dict[str, Callable[[], Method]] | None = None,
    allow_confirmation: bool = False,
) -> dict:
    """Run methods and references on ``cell``. Costs are per round (cost / T), paired by seed.

    ``extra_methods`` maps name -> factory (used by the mechanism stages). The null twin result
    (methods + ``ref_family``) is attached under ``"null"`` when ``with_null`` is true.
    """
    guard_seeds(seed_list, allow_confirmation)
    methods = tuple(all_method_names() if methods is None else methods)
    refs = tuple(REFERENCES if refs is None else refs)
    spec = bernoulli_grid_spec()
    ref_obj: dict[str, Method] = {}
    if "ref_law" in refs and not cell.null:
        ref_obj["ref_law"] = build_ref_law(cell)
    if "ref_family" in refs:
        ref_obj["ref_family"] = build_ref_family_for(cell, kappa)
    if "ref_valid" in refs:
        ref_obj["ref_valid"] = build_ref_valid(cell)
    out: dict[str, dict[str, list]] = {}
    for sd in seed_list:
        stream = make_stream(cell, sd)
        cfg = cell.config(sd)
        runs = {m: run(stream, make_method(m, spec, cfg), cfg) for m in methods}
        for name, fac in (extra_methods or {}).items():
            runs[name] = run(stream, fac(), cfg)
        for name, ref in ref_obj.items():
            runs[name] = run(stream, ref, cfg)
        if "ref_regime_clairvoyant" in refs:
            runs["ref_regime_clairvoyant"] = score_actions(
                stream, cfg, clairvoyant_actions(stream), np.zeros(cell.T)
            )
        for name, r in runs.items():
            rec = _rec(r)
            slot = out.setdefault(name, _empty())
            for k, v in rec.items():
                slot[k].append(v / cell.T if k == "cost" else v)
    res = {
        "cell_id": cell.cell_id,
        "T": cell.T,
        "B": cell.B,
        "alpha": cell.alpha,
        "kappa": kappa,
        "seeds": [int(x) for x in seed_list],
        "methods": out,
        "null": None,
    }
    if with_null and not cell.null:
        if null_result is None:
            twin = cell.null_twin()
            key = (
                twin.cell_id,
                tuple(seed_list),
                kappa,
                methods,
                tuple(sorted(extra_methods or {})),
            )
            null_result = _NULL_CACHE.get(key)
            if null_result is None:
                null_result = evaluate_cell(
                    twin,
                    seed_list,
                    methods,
                    NULL_REFS,
                    kappa=kappa,
                    with_null=False,
                    extra_methods=extra_methods,
                    allow_confirmation=allow_confirmation,
                )
                if len(_NULL_CACHE) > 400:
                    _NULL_CACHE.clear()
                _NULL_CACHE[key] = null_result
        res["null"] = null_result
    return res


# ----------------------------------------------------------------------------- calibration


def null_fp_by_kappa(task: tuple) -> dict[float, int]:
    """Worker: null-twin false-promotion count of ``ref_family`` for each kappa."""
    twin, seed_list, grid = task
    spec_streams = [(sd, make_stream(twin, sd)) for sd in seed_list]
    counts: dict[float, int] = {}
    for kappa in grid:
        ref = build_ref_family_for(twin, kappa)
        k = 0
        for sd, stream in spec_streams:
            k += int((run(stream, ref, twin.config(sd)).fp_regime or 0) > 0)
        counts[kappa] = k
    return counts


def calibrate_family_kappa(
    cells: Sequence,
    seed_list: Sequence[int],
    grid: Sequence[float] = KAPPA_GRID,
    alpha: float = 0.1,
    mapper: Callable = map,
) -> tuple[float, dict]:
    """Largest kappa (most permissive) whose pooled null-twin any-FP rate is <= alpha."""
    guard_seeds(seed_list)
    twins = {c.null_twin().cell_id: c.null_twin() for c in cells}
    tasks = [(tw, tuple(seed_list), tuple(grid)) for tw in twins.values()]
    per = list(mapper(null_fp_by_kappa, tasks))
    n = len(tasks) * len(seed_list)
    table = {}
    for kappa in grid:
        k = sum(p[kappa] for p in per)
        table[kappa] = {"k": k, "n": n, "rate": k / n if n else float("nan")}
    chosen = None
    for kappa in sorted(grid, reverse=True):
        if n and table[kappa]["rate"] <= alpha:
            chosen = kappa
            break
    calibrated = chosen is not None
    return (chosen if calibrated else min(grid)), {
        "table": table,
        "calibrated": calibrated,
        "n_twins": len(twins),
    }


# ----------------------------------------------------------------------------- classification


def classify_cell(
    result: dict,
    material: float = MATERIAL,
    fp_slack: float = FP_SLACK,
    safety_gated: Sequence[str] | None = None,
    floor: str = FLOOR,
) -> dict:
    """Apply the locked failure definition (per-round cost, paired by seed), Amendment 2 version.

    ``no_switch`` is included among the baselines that define ``best_safe`` and must be beaten
    (the conservative direction). ``safety_gated`` defaults to :func:`gated_methods` (including R6
    gated baselines that were evaluated). Label precedence: info_limited, reference_unsafe,
    shared_failure, cost_of_validity, prior_gap, headroom_not_shared, no_headroom.

    * ``shared_failure``: material headroom against R_family (R_family null FP ok), every gated baseline
      loses to R_family by more than ``material`` (lower CI), and (Amendment 2) ``best_safe - R_valid``
      has a lower CI bound above ``material``.
    * ``cost_of_validity``: material headroom against R_family but none against R_valid. Recorded, not
      pursued.
    * ``prior_gap``: R_valid beats every gated (prior-free) baseline (each lower CI above ``material``),
      but the R_family-based shared-failure test is not met. The ``prior_gap`` flag is also set on
      shared failures where it holds: the advantage there rests on declared prior knowledge.

    When ``ref_valid`` is absent from the result (archives from earlier cycles), the R_valid
    conditions are skipped and the Amendment 1 classes are reproduced.
    """
    m = result["methods"]
    alpha = result.get("alpha", 0.1)
    if safety_gated is None:
        safety_gated = gated_methods()

    def cost(k: str) -> np.ndarray:
        return np.asarray(m[k]["cost"], dtype=float)

    gated = [k for k in (*safety_gated, floor) if k in m]
    fam, law = cost("ref_family"), cost("ref_law")
    best_safe = min(gated, key=lambda k: float(cost(k).mean()))
    h_mean, h_lo, h_hi = paired_ci(cost(best_safe) - fam)
    gaps = {k: paired_ci(cost(k) - fam) for k in gated}
    il_mean, il_lo, il_hi = paired_ci(cost(floor) - law)
    info_limited = bool(il_hi < material)

    has_valid = "ref_valid" in m
    if has_valid:
        valid = cost("ref_valid")
        hv_mean, hv_lo, hv_hi = paired_ci(cost(best_safe) - valid)
        valid_gaps = {k: paired_ci(cost(k) - valid) for k in gated}
        headroom_valid = bool(hv_lo > material)
        prior_gap_flag = bool(all(g[1] > material for g in valid_gaps.values()))
    else:
        hv_mean = hv_lo = hv_hi = float("nan")
        valid_gaps = {}
        headroom_valid = True  # no R_valid information: do not restrict (earlier-cycle behaviour)
        prior_gap_flag = False

    null = result.get("null")
    if null is not None and "ref_family" in null["methods"]:
        fp = np.asarray(null["methods"]["ref_family"]["fp"])
        fp_rate, fp_lo, fp_hi = wilson(int(fp.sum()), len(fp))
        fp_ok = bool(fp_rate <= alpha + fp_slack)
    else:
        fp_rate = fp_lo = fp_hi = float("nan")
        fp_ok = False
    v_rate = v_lo = v_hi = float("nan")
    if null is not None and "ref_valid" in null["methods"]:
        vfp = np.asarray(null["methods"]["ref_valid"]["fp"])
        v_rate, v_lo, v_hi = wilson(int(vfp.sum()), len(vfp))
    headroom = bool(h_lo > material)
    material_headroom = headroom and fp_ok
    shared_family = bool(material_headroom and all(g[1] > material for g in gaps.values()))
    shared = bool(shared_family and headroom_valid)

    if info_limited:
        label = "info_limited"
    elif not fp_ok:
        label = "reference_unsafe"
    elif shared:
        label = "shared_failure"
    elif has_valid and material_headroom and not headroom_valid:
        label = "cost_of_validity"
    elif prior_gap_flag:
        label = "prior_gap"
    elif headroom:
        label = "headroom_not_shared"
    else:
        label = "no_headroom"
    return {
        "cell_id": result["cell_id"],
        "label": label,
        "best_safe": best_safe,
        "H": h_mean,
        "H_ci": [h_lo, h_hi],
        "H_valid": hv_mean,
        "H_valid_ci": [hv_lo, hv_hi],
        "gaps": {k: {"mean": g[0], "lo": g[1], "hi": g[2]} for k, g in gaps.items()},
        "valid_gaps": {k: {"mean": g[0], "lo": g[1], "hi": g[2]} for k, g in valid_gaps.items()},
        "material_headroom": material_headroom,
        "headroom_valid": headroom_valid if has_valid else None,
        "shared_failure": shared,
        "shared_vs_family_only": shared_family,
        "prior_gap": prior_gap_flag,
        "info_limited": info_limited,
        "info_gap": {"mean": il_mean, "lo": il_lo, "hi": il_hi},
        "ref_family_null_fp": {"rate": fp_rate, "wilson": [fp_lo, fp_hi], "ok": fp_ok},
        "ref_valid_null_fp": {"rate": v_rate, "wilson": [v_lo, v_hi]},
        "severity": h_mean if shared else 0.0,
        "mean_cost": {k: float(np.mean(v["cost"])) for k, v in m.items()},
    }


def isolate(
    cell,
    seed_list: Sequence[int],
    kappa: float = KAPPA_DEFAULT,
    axes: Sequence[str] | None = None,
    methods: Sequence[str] | None = None,
    mapper: Callable = map,
) -> dict:
    """Move one axis at a time to its easiest level; record which moves remove the failure.

    A move removes the failure when the headroom lower CI bound is no longer above the
    materiality threshold (protocol stage 4). Axes already at the easiest level are skipped.
    """
    axes = cell.axes if axes is None else axes
    todo = [(ax, cell.easiest(ax)) for ax in axes if getattr(cell, ax) != cell.easiest_levels[ax]]
    tasks = [(mc, tuple(seed_list), kappa, methods) for _, mc in todo]
    out = {}
    for (ax, mc), cls in zip(todo, mapper(_isolate_task, tasks), strict=True):
        cls["removes_failure"] = bool(not cls["H_ci"][0] > MATERIAL)  # headroom CI gone
        cls["moved_cell"] = mc.cell_id
        out[ax] = cls
    return out


def _isolate_task(task: tuple) -> dict:
    mc, seed_list, kappa, methods = task
    return classify_cell(evaluate_cell(mc, seed_list, methods, kappa=kappa))


def evaluate_plain_task(task: tuple) -> dict:
    """Worker: (cell, seeds, kappa, methods) -> result without the null twin attached."""
    cell, seed_list, kappa, methods = task
    return evaluate_cell(cell, seed_list, methods, kappa=kappa, with_null=False)


def evaluate_null_task(task: tuple) -> dict:
    """Worker: evaluate a null twin (methods + ref_family)."""
    twin, seed_list, kappa, methods = task
    return evaluate_cell(twin, seed_list, methods, NULL_REFS, kappa=kappa, with_null=False)


# ----------------------------------------------------------------------------- diagnostics
# Amendment 1, item 2. Evaluator-side and descriptive only. The ``diag_oracle_*`` methods below
# receive truth through their constructor and exist only inside ``diagnose_cell``: they are not
# in ``ALL_METHODS``, ``build_method`` or the candidate registry.

DIAG_VARIANTS = ("known_onset", "known_stake", "known_both")
DIAG_STAKES = tuple(float(x) for x in VectorizedStartedMixtureEProcess.DEFAULT_STAKES)


def _growth(stake: float, p_on: float, h: float) -> float:
    """E log(1 + stake * X / (1+h)) for X = -D - h, with P(D = -1) = p_on."""
    b = 1.0 + h
    return p_on * math.log1p(stake * (1.0 - h) / b) + (1.0 - p_on) * math.log1p(-stake)


def kelly_stake(p_on: float, h: float) -> float:
    """Growth-optimal fixed stake in (0, 1) for the on-state (evaluator-side)."""
    grid = np.linspace(0.0, 0.995, 1992)
    vals = [_growth(float(x), p_on, h) for x in grid]
    return float(grid[int(np.argmax(vals))])


def _with_stakes(
    proc: VectorizedStartedMixtureEProcess, stakes
) -> VectorizedStartedMixtureEProcess:
    proc.stakes = np.asarray(stakes, dtype=float)
    proc.stake_weights = np.full(len(proc.stakes), 1.0 / len(proc.stakes))
    proc.log_stake_weights = np.log(proc.stake_weights)
    proc.log_wealth = np.zeros((len(proc.starts), len(proc.stakes)), dtype=float)
    return proc


class DiagOracleGate(EpisodeComposition):
    """Evaluator-only: ``episode_front`` decision rule with an oracle-ablated started mixture.

    ``onset_label``: label index of the first post-onset label (single start) or ``None`` for the
    repository start grid. ``stake``: single known stake or ``None`` for the default grid.
    """

    def __init__(self, variant: str, onset_label: int | None, stake: float | None):
        super().__init__("front")
        if variant not in DIAG_VARIANTS:
            raise ValueError(variant)
        self.name = f"diag_oracle_{variant}"
        self.onset_label, self.stake = onset_label, stake

    def _new_episode(self, j: int, start: int) -> None:
        self.j, self.ep_start, self.ep_labels = j, start, []
        if j > 0:
            self.ep = None
            return
        c = self.cfg
        step = max(1, c.B // 32)
        starts = (
            tuple(range(0, max(1, c.B), step))
            if self.onset_label is None
            else (int(self.onset_label),)
        )
        proc = VectorizedStartedMixtureEProcess(bound=1.0 + c.h, alpha=c.alpha, starts=starts)
        self.ep = proc if self.stake is None else _with_stakes(proc, [self.stake])


def first_onset_round(stream: Stream) -> int | None:
    reg = stream.truth.regime if stream.truth is not None else None
    if reg is None or not np.any(reg):
        return None
    return int(np.flatnonzero(reg)[0]) + 1


def _final_log_e(m: Method) -> float:
    if isinstance(m, AllOnsetEDetector):
        w = (m.n - min(m.k, m.n)) / m.n + m.v / m.n
        return float(math.log(w)) if w > 0 else float("-inf")
    ep = getattr(m, "_ep0", None)  # episode-0 gate evidence (kept by ``_track_first_episode``)
    return float(ep.log_e_value) if ep is not None and hasattr(ep, "log_e_value") else float("nan")


def _track_first_episode(m: Method) -> Method:
    """Keep a reference to the episode-0 evidence object (later episodes replace ``m.ep``)."""
    orig = m._new_episode

    def wrapped(j, start):
        orig(j, start)
        if j == 0:
            m._ep0 = m.ep

    m._new_episode = wrapped
    return m


def analytic_label_requirement(name: str, cell: CellSpec) -> dict:
    """``(log(1/alpha_ep) + log #starts + log #stakes) / g*`` for an e-process baseline.

    ``g*`` is the per-label log growth of the best fixed stake on the repository stake grid in the
    favourable state. ``None`` entries for methods that are not started-mixture e-processes.
    """
    B, a, h = cell.B, cell.alpha, cell.h
    p_on = cell.p_pair[1]
    g_best = max(_growth(x, p_on, h) for x in DIAG_STAKES)

    def n_start(n: int) -> int:
        return len(range(0, max(1, n), max(1, n // 32)))

    if name in ("episode_geo", "episode_equal", "episode_front"):
        a_ep = {"geo": a / 2, "equal": a / (B + 1), "front": a}[name.split("_", 1)[1]]
        logs, g = math.log(1 / a_ep) + math.log(n_start(B)) + math.log(len(DIAG_STAKES)), g_best
    elif name == "c2_rho0.75":
        n = int(0.75 * B)
        logs = math.log(2 / a) + math.log(n_start(n)) + math.log(len(DIAG_STAKES))
        g = g_best
    elif name == "allonset_edetector":
        n = len(uniform_calendar(cell.T, B, cell.d))
        g = _growth(0.5, p_on, h)  # one fixed normalised stake 0.5
        logs = math.log(1 / a) + math.log(max(1, n))
    else:
        return {"log_terms": None, "growth": None, "labels": None}
    return {"log_terms": logs, "growth": g, "labels": logs / g if g > 0 else float("inf")}


def _mean_ci(x) -> dict:
    m, lo, hi = paired_ci(np.asarray(x, dtype=float))
    return {"mean": m, "lo": lo, "hi": hi}


def diagnose_cell(
    cell: CellSpec,
    seed_list: Sequence[int],
    kappa: float = KAPPA_DEFAULT,
    allow_confirmation: bool = False,
) -> dict:
    """Per-baseline diagnostics and the oracle-ablation decomposition of the gap to R_family.

    For each gated baseline (and ``no_switch``): labels released from the favourable state,
    time to first promotion, final log e-value of the gate evidence (value frozen at promotion if
    the gate promoted), and the analytic label requirement. The three ``diag_oracle_*`` variants
    run the ``episode_front`` decision rule (e-process gate + economic check, same alpha) with
    onset and/or stake given by the evaluator. Costs are per round, paired by seed.
    """
    guard_seeds(seed_list, allow_confirmation)
    if cell.null:
        raise ValueError("diagnostics are defined for non-null cells")
    spec = bernoulli_grid_spec()
    gated = (*SAFETY_GATED, FLOOR)
    stake = kelly_stake(cell.p_pair[1], cell.h)
    cal = sorted(uniform_calendar(cell.T, cell.B, cell.d))
    rec: dict[str, dict[str, list]] = {}
    ref_law, ref_fam = build_ref_law(cell), build_ref_family(cell.T, kappa)

    def put(name, r, m=None, ev=None):
        slot = rec.setdefault(
            name, {"cost": [], "labels_after": [], "first_promo": [], "log_e": [], "promoted": []}
        )
        slot["cost"].append(r.cost / cell.T)
        if m is not None and ev is not None:
            slot["labels_after"].append(int(sum(1 for e, _ in m.labels if ev[e - 1])))
        else:
            slot["labels_after"].append(float("nan"))
        idx = np.flatnonzero(r.actions)
        slot["first_promo"].append(int(idx[0]) + 1 if len(idx) else -1)
        slot["promoted"].append(int(len(idx) > 0))
        slot["log_e"].append(_final_log_e(m) if m is not None else float("nan"))

    for sd in seed_list:
        stream = make_family1_stream(cell, sd)
        cfg = cell.config(sd)
        on = np.asarray(stream.truth.regime, dtype=bool)
        tau = first_onset_round(stream)
        k0 = sum(
            1 for x in cal if tau is not None and x < tau
        )  # label index of first post-onset label
        k0 = min(k0, max(0, cell.B - 1))
        for name in gated:
            m = build_method(name, spec)
            if hasattr(m, "_new_episode"):
                _track_first_episode(m)
            put(name, run(stream, m, cfg), m, on)
        for variant, ol, stk in (
            ("known_onset", k0, None),
            ("known_stake", None, stake),
            ("known_both", k0, stake),
        ):
            m = _track_first_episode(DiagOracleGate(variant, ol, stk))
            put(m.name, run(stream, m, cfg), m, on)
        put("ref_family", run(stream, ref_fam, cfg))
        put("ref_law", run(stream, ref_law, cfg))
    cost = {k: np.asarray(v["cost"]) for k, v in rec.items()}
    best_safe = min(gated, key=lambda k: float(cost[k].mean()))
    front, fam = cost["episode_front"], cost["ref_family"]
    onset_part = front - cost["diag_oracle_known_onset"]
    stake_part = front - cost["diag_oracle_known_stake"]
    both_part = front - cost["diag_oracle_known_both"]
    parts = {
        "gap_best_safe_vs_family": _mean_ci(cost[best_safe] - fam),
        "best_safe_minus_front": _mean_ci(cost[best_safe] - front),
        "onset_uncertainty": _mean_ci(onset_part),
        "stake_mismatch": _mean_ci(stake_part),
        "interaction": _mean_ci(both_part - onset_part - stake_part),
        "residual_known_both_minus_family": _mean_ci(cost["diag_oracle_known_both"] - fam),
    }
    per = {}
    for k, v in rec.items():
        fp = np.asarray(v["first_promo"])
        pr = fp[fp > 0]
        le = np.asarray(v["log_e"], dtype=float)
        la = np.asarray(v["labels_after"], dtype=float)
        per[k] = {
            "mean_cost": float(np.mean(v["cost"])),
            "labels_after_onset": float(np.nanmean(la)) if np.any(~np.isnan(la)) else None,
            "frac_promoted": float(np.mean(v["promoted"])),
            "mean_first_promotion_round": float(pr.mean()) if len(pr) else None,
            "mean_final_log_e": float(np.nanmean(le)) if np.any(~np.isnan(le)) else None,
            "analytic": analytic_label_requirement(k, cell),
        }
    return {
        "cell_id": cell.cell_id,
        "seeds": [int(x) for x in seed_list],
        "kappa": kappa,
        "kelly_stake": stake,
        "best_safe": best_safe,
        "per_method": per,
        "parts": parts,
        "log_threshold": math.log(1.0 / cell.alpha),
    }


def diagnose_task(task: tuple) -> dict:
    cell, seed_list, kappa = task
    out = diagnose_cell(cell, seed_list, kappa)
    out["_runs"] = len(seed_list) * (len(SAFETY_GATED) + 1 + len(DIAG_VARIANTS) + 2)
    return out


# ----------------------------------------------------------------------------- registry

BASELINE_REGISTRY: list[dict] = [
    {
        "name": "no_switch",
        "status": "implemented",
        "guarantee": "none needed (never promotes)",
        "role": "floor",
        "notes": "zero false promotion by construction",
    },
    {
        "name": "periodic_mean",
        "status": "implemented",
        "guarantee": "none",
        "role": "ungated",
        "notes": "periodic window-mean re-evaluation on a uniform calendar",
    },
    {
        "name": "episode_geo / episode_equal / episode_front",
        "status": "implemented",
        "guarantee": "per-episode bounded-mean started-mixture e-process with alpha spending",
        "role": "safety-gated",
        "notes": "validity under repeated episodes is a research target, not established here",
    },
    {
        "name": "allonset_edetector",
        "status": "implemented",
        "guarantee": "all-onset mixture e-detector threshold 1/alpha; promotes once",
        "role": "safety-gated",
        "notes": "no rollback",
    },
    {
        "name": "dal_restart",
        "status": "implemented",
        "guarantee": "none (CUSUM-triggered query bursts)",
        "role": "ungated",
        "notes": "detect-then-re-evaluate",
    },
    {
        "name": "pacing_bernoulli",
        "status": "implemented",
        "guarantee": "none (EWMA threshold, Bernoulli query pacing)",
        "role": "ungated",
        "notes": "budget respected only through the harness guard",
    },
    {
        "name": "c2_rho0.75",
        "status": "implemented",
        "guarantee": "rho*B to alpha-spent e-process gate; remainder to CUSUM rollback",
        "role": "safety-gated",
        "notes": "exploratory C2 candidate used as a benchmark anchor, not a target",
    },
    {
        "name": "c1_hmm_cs",
        "status": "implemented",
        "guarantee": "delayed-HMM likelihood-ratio confidence-set gate over a declared bank",
        "role": "safety-gated",
        "notes": "exploratory C1 candidate; bank misspecification not covered",
    },
    {
        "name": "gong_zhang_delayed",
        "status": "missing",
        "guarantee": "R6 baseline: delayed-feedback sequential testing wrapper",
        "role": "safety-gated (when added)",
        "notes": "not in harness; every atlas entry carries this limitation",
    },
    {
        "name": "qiu_et_al_delayed",
        "status": "missing",
        "guarantee": "R6 baseline: delayed-label monitoring wrapper",
        "role": "safety-gated (when added)",
        "notes": "not in harness",
    },
    {
        "name": "ryabchenko_delayed_wrapper",
        "status": "wrapper-needed",
        "guarantee": "R6 baseline: sequential testing under delayed feedback",
        "role": "safety-gated (when added)",
        "notes": "requires a delayed-feedback wrapper around the base test; missing",
    },
    {
        "name": "online_fwer_comparator",
        "status": "missing",
        "guarantee": "online FWER control across repeated promotion episodes",
        "role": "safety-gated (when added)",
        "notes": "would replace ad hoc alpha spending in episode_*",
    },
    {
        "name": "hard_budget_pacing_comparator",
        "status": "missing",
        "guarantee": "none (budget-feasible pacing comparator)",
        "role": "ungated (when added)",
        "notes": "strong hard-budget pacing baseline absent",
    },
]

__all__ = [
    "ALL_METHODS",
    "BASELINE_REGISTRY",
    "KAPPA_GRID",
    "SAFETY_GATED",
    "UNGATED",
    "CellSpec",
    "ConfirmationSeedsLocked",
    "Family2CellSpec",
    "FilterReference",
    "HMMFilterReference",
    "RValidFamily1",
    "RValidFamily2",
    "all_cells",
    "all_cells2",
    "all_method_names",
    "baseline_registry",
    "build_ref_valid",
    "calibrate_family_kappa",
    "classify_cell",
    "diagnose_cell",
    "evaluate_cell",
    "family2_hypotheses",
    "family_hypotheses",
    "gated_methods",
    "isolate",
    "law_hypotheses",
    "make_family1_stream",
    "make_family2_stream",
    "make_stream",
    "neighbours",
    "r6_methods",
    "seeds",
    "ungated_methods",
]
