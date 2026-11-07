# PORTED UNCHANGED (COMMON_CONTRACT_PORT tier component) -- WP1e, d2a_rar branch.
# Source: origin/research/gave-r-2026-11-06@03289d1d (file last changed in d636765e), path: src/shiftlab/gaver/gapmix.py
# Only edit vs source: 'shiftlab.gaver' import paths -> 'shiftlab.sota.inrepo'. See tests/d2a_rar/test_inrepo_ports.py
# (test_port_source_identical) which re-extracts the source with git show and diffs it.
"""Gap-Mix: gap-aware evidence for uniformly acquired, delayed labels (GAVE-R WP1).

Two new evidence processes plus a frozen restart mixture, written as pluggable evidence for the
Atlas ``episode_front`` gate (calendar, alpha spending, ``econ_ok``, window-mean rollback).

Observation contract (shared by every class here)
-------------------------------------------------
* Evidence sees only released labels ``(event_round, D)`` in event order. With a constant delay
  release order equals query order, and the event rounds are fixed by a deterministic calendar,
  so the gap ``g = ev_k - ev_{k-1}`` is predictable (it is not value-dependent).
* ``Z = 1[D < 0]`` (favourable). Declared null ``H0``: the round-level favourable indicator is a
  stationary two-state chain with ``p <= q0 = (1+h)/2`` and persistence ``rho in [0, rho_bar]``
  (``rho_bar`` is *declared*, never read from simulator truth). The labelled skeleton is then
  Markov with ``P(Z_k=1 | z) = p + (z - p) rho^g`` for gap ``g``.
* The first label of each restart start is conditioned on and used as ``prev``.

Validity status
---------------
PROVEN (elementary, given the declared null and the conditioning above):

* ``EnvelopeStart``: each factor is ``1`` or ``(r/u)^Z ((1-r)/(1-u))^(1-Z)`` with ``r`` computed from
  earlier labels and ``u`` the upper bound of ``P(Z=1 | past)`` over ``H0``; hence a nonnegative
  supermartingale per component, and fixed convex mixtures of components and of restart starts
  are e-processes. This covers the one-step conditional bound only; the full pipeline (value
  dependent requests, informative delay) is outside the declared contract.
* ``ExactGapStart``: numerator = fixed mixture of exact-gap Markov likelihoods
  (alternative ``(p_a, rho_a)`` grid, ``P^g`` transitions); denominator ``D`` is a certified upper
  bound of ``sup_{(p, rho) in H0}`` of the exact-gap conditional likelihood, so
  ``M / D <= M / L(theta*)`` which is a test martingale under every ``theta*`` in ``H0``.
  Certification: ``rho`` is cut into cells; inside a cell each of the four transition
  probabilities is monotone in ``lambda = rho^g`` so the per-term endpoint maximum bounds the cell;
  with those fixed ``lambda``'s the log-likelihood is concave in ``p`` and is maximised by bisection
  (slack ``1e-9`` added). The bound is >= the true supremum; its looseness (conservatism, lost
  power) is not proven and is measured in the tests/results.
* The restart mixture is a fixed equal-weight average of per-start e-processes (each equals 1 until
  its start), hence an e-process; alpha is spent once on the mixture.

NOT proven: closed-loop validity when requests depend on past values, informative delay, other
nulls (non-Markov, non-stationary, ``rho > rho_bar``), and any claim about the Atlas gate beyond the
evidence level (econ_ok and rollback are as in the existing baselines).
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp, xlogy

from shiftlab.dive.atlas_dependence_baselines import MarkovLREProcess, _FrontGated
from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess

EPS_SLACK = 1e-9
ALT_P = (0.65, 0.75, 0.85, 0.95)
ALT_RHO = (0.0, 0.4, 0.7, 0.9)
ENV_BET_FRACS = (0.5, 0.9)


# ----------------------------------------------------------------------------- envelope


def envelope_u(q0: float, rho_bar: float, gap: int, prev: int) -> float:
    """Upper bound of ``P(Z=1 | previous observed state, gap)`` over the declared null."""
    return q0 + (1.0 - q0) * rho_bar**gap if prev == 1 else q0


def envelope_log_factor(r: float, u: float, z: int) -> float:
    """Neutral if ``r <= u`` else the conditional bet on ``Z`` against Bernoulli(u)."""
    if r <= u:
        return 0.0
    return float(np.log(r / u) if z else np.log((1.0 - r) / (1.0 - u)))


def envelope_expectation(v: float, r: float, u: float) -> float:
    """``E[f]`` when ``P(Z=1)=v`` (exact, for tests)."""
    if r <= u:
        return 1.0
    return v * (r / u) + (1.0 - v) * ((1.0 - r) / (1.0 - u))


class EnvelopeStart:
    """One start of the conservative envelope e-process (plug-in bet + fixed bet fractions)."""

    def __init__(self, q0: float, rho_bar: float):
        self.q0, self.rho_bar = q0, rho_bar
        self.n_comp = 1 + len(ENV_BET_FRACS)
        self.logw = np.zeros(self.n_comp)
        self.prev: int | None = None
        self.prev_ev = 0
        self.cnt = np.zeros((2, 2))
        self.n_trans = 0

    def update(self, ev: int, z: int) -> None:
        if self.prev is None:
            self.prev, self.prev_ev = z, ev
            return
        u = envelope_u(self.q0, self.rho_bar, ev - self.prev_ev, self.prev)
        n0, n1 = self.cnt[self.prev]
        plug = min((n1 + 0.5) / (n0 + n1 + 1.0), 1.0 - 1e-6)  # prequential, past labels only
        rs = [plug] + [u + b * (1.0 - u) for b in ENV_BET_FRACS]
        self.logw += np.array([envelope_log_factor(r, u, z) for r in rs])
        self.cnt[self.prev, z] += 1.0
        self.prev, self.prev_ev = z, ev
        self.n_trans += 1

    @property
    def log_e(self) -> float:
        return float(logsumexp(self.logw) - np.log(self.n_comp))


# ----------------------------------------------------------------------------- exact gap


def rho_cell_edges(rho_bar: float, width: float = 0.005) -> np.ndarray:
    n = max(1, int(np.ceil(rho_bar / width)))
    return np.linspace(0.0, rho_bar, n + 1)


def exact_loglik(counts: dict[int, np.ndarray], p: float, rho: float) -> float:
    """Exact-gap conditional log-likelihood at a point (reference for tests)."""
    tot = 0.0
    for g, n in counts.items():
        lam = rho**g
        tot += (
            xlogy(n[0], 1.0 - p * (1.0 - lam))
            + xlogy(n[1], p * (1.0 - lam))
            + xlogy(n[2], (1.0 - p) * (1.0 - lam))
            + xlogy(n[3], p + (1.0 - p) * lam)
        )
    return float(tot)


def certified_null_sup_loglik(counts: dict[int, np.ndarray], q0: float, edges: np.ndarray) -> float:
    """Certified upper bound of ``sup_{p<=q0, rho in [0, edges[-1]]}`` exact-gap log-likelihood.

    ``counts[g] = (n00, n01, n10, n11)`` of ``prev -> z`` transitions at gap ``g``.
    """
    lo_e, hi_e = edges[:-1], edges[1:]
    terms = []
    for g, n in counts.items():
        if n.sum() <= 0:
            continue
        lam_lo, lam_hi = lo_e**g, hi_e**g
        terms.append((n, lam_lo, lam_hi))
    if not terms:
        return 0.0

    def obj(p):
        tot = 0.0
        for n, ll, lh in terms:
            tot = (
                tot
                + xlogy(n[0], 1.0 - p * (1.0 - lh))
                + xlogy(n[1], p * (1.0 - ll))
                + xlogy(n[2], (1.0 - p) * (1.0 - ll))
                + xlogy(n[3], p + (1.0 - p) * lh)
            )
        return tot

    def deriv(p):
        d = 0.0
        for n, ll, lh in terms:
            d = (
                d
                - n[0] * (1.0 - lh) / np.maximum(1.0 - p * (1.0 - lh), 1e-300)
                + n[1] / np.maximum(p, 1e-300)
                - n[2] / np.maximum(1.0 - p, 1e-300)
                + n[3] * (1.0 - lh) / np.maximum(p + (1.0 - p) * lh, 1e-300)
            )
        return d

    c = len(lo_e)
    lo = np.zeros(c)
    hi = np.full(c, q0)
    at_cap = deriv(np.full(c, q0)) >= 0.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        up = deriv(mid) > 0.0
        lo = np.where(up, mid, lo)
        hi = np.where(up, hi, mid)
    p_star = np.where(at_cap, q0, 0.5 * (lo + hi))
    best = np.maximum(obj(p_star), obj(np.full(c, q0)))
    return float(np.max(best)) + EPS_SLACK


class ExactGapStart:
    """One start of the exact-gap Markov LR: alt-grid mixture / certified null supremum."""

    def __init__(self, q0: float, rho_bar: float, alt_p=ALT_P, alt_rho=ALT_RHO):
        self.q0 = q0
        self.edges = rho_cell_edges(rho_bar)
        self.alts = np.array([(p, r) for p in alt_p for r in alt_rho if p > q0])
        self.num = np.zeros(len(self.alts))
        self.counts: dict[int, np.ndarray] = {}
        self.prev: int | None = None
        self.prev_ev = 0
        self._log_e = 0.0

    def update(self, ev: int, z: int) -> None:
        if self.prev is None:
            self.prev, self.prev_ev = z, ev
            return
        g = ev - self.prev_ev
        lam = self.alts[:, 1] ** g
        pa = self.alts[:, 0]
        p1 = pa * (1.0 - lam) if self.prev == 0 else pa + (1.0 - pa) * lam
        self.num += np.log(p1 if z else 1.0 - p1)
        self.counts.setdefault(g, np.zeros(4))[2 * self.prev + z] += 1.0
        self.prev, self.prev_ev = z, ev
        den = certified_null_sup_loglik(self.counts, self.q0, self.edges)
        self._log_e = float(logsumexp(self.num) - np.log(len(self.alts)) - den)

    @property
    def log_e(self) -> float:
        return self._log_e


# ----------------------------------------------------------------------------- evidence wrappers


class RestartMixture:
    """Equal-weight fixed mixture of per-start e-processes with event-round thresholds."""

    def __init__(self, make_start, thresholds, alpha: float):
        self.thresholds = tuple(thresholds)
        self.starts = [make_start() for _ in self.thresholds]
        self.alpha = alpha
        self.n_used = 0
        self._log_e = 0.0

    def update(self, ev: int, x: float) -> bool:
        z = 1 if x < 0 else 0
        for thr, st in zip(self.thresholds, self.starts, strict=True):
            if ev >= thr:
                st.update(ev, z)
        self.n_used += 1
        comp = np.array([s.log_e for s in self.starts])
        self._log_e = float(logsumexp(comp) - np.log(len(comp)))
        return True

    @property
    def log_e_value(self) -> float:
        return self._log_e

    @property
    def alarm(self) -> bool:
        return self._log_e >= -np.log(self.alpha)


def restart_thresholds(T: int, mixture: bool) -> tuple[int, ...]:
    return tuple(int(f * T) for f in (0.0, 0.25, 0.5, 0.75)) if mixture else (0,)


def envelope_evidence(cfg, alpha, rho_bar: float, mixture: bool):
    q0 = (1.0 + cfg.h) / 2.0
    return RestartMixture(
        lambda: EnvelopeStart(q0, rho_bar), restart_thresholds(cfg.T, mixture), alpha
    )


def exact_evidence(cfg, alpha, rho_bar: float, mixture: bool):
    q0 = (1.0 + cfg.h) / 2.0
    return RestartMixture(
        lambda: ExactGapStart(q0, rho_bar), restart_thresholds(cfg.T, mixture), alpha
    )


def label_starts(n_labels: int, mixture: bool) -> tuple[int, ...]:
    if not mixture:
        return (0,)
    return tuple(sorted({int(f * n_labels) for f in (0.0, 0.25, 0.5, 0.75)}))


class IIDEvidence:
    """Repository bounded-mean started-mixture e-process, optional gap-``g`` thinning."""

    def __init__(self, cfg, alpha, mixture: bool, thin_gap: int | None = None, n_starts32=False):
        n_lab = cfg.B if thin_gap is None else min(cfg.B, cfg.T // thin_gap + 1)
        if n_starts32:
            step = max(1, n_lab // 32)
            starts = tuple(range(0, max(1, n_lab), step))
        else:
            starts = label_starts(n_lab, mixture)
        self.ep = VectorizedStartedMixtureEProcess(bound=1.0 + cfg.h, alpha=alpha, starts=starts)
        self.h, self.thin_gap, self.last_used = cfg.h, thin_gap, None
        self.n_used = 0

    def update(self, ev: int, x: float) -> bool:
        if self.thin_gap and self.last_used is not None and ev - self.last_used < self.thin_gap:
            return False
        self.last_used = ev
        self.ep.update(-x - self.h)
        self.n_used += 1
        return True

    @property
    def log_e_value(self) -> float:
        return self.ep.log_e_value

    @property
    def alarm(self) -> bool:
        return self.ep.alarm


class ExistingMarkovLR:
    """Existing Atlas Markov LR with a selectable start set (``default`` keeps its 8 starts)."""

    def __init__(self, cfg, alpha, variant: str):
        q0 = (1.0 + cfg.h) / 2.0
        self.ep = MarkovLREProcess(q0, alpha, cfg.B)
        if variant != "default":
            self.ep.starts = np.array(label_starts(cfg.B, variant == "s4"))
            self.ep.log_w = -np.log(len(self.ep.starts))
            self.ep.num = np.zeros((len(self.ep.starts), len(self.ep.grid)))
            self.ep.cnt = np.zeros((len(self.ep.starts), 4))
        self.n_used = 0

    def update(self, ev: int, x: float) -> bool:
        self.ep.update_z(1 if x < 0 else 0)
        self.n_used += 1
        return True

    @property
    def log_e_value(self) -> float:
        return self.ep.log_e_value

    @property
    def alarm(self) -> bool:
        return self.ep.alarm


# ----------------------------------------------------------------------------- gate + registry


class GapGate(_FrontGated):
    """``episode_front`` gate with pluggable evidence; records evidence-level alarm time."""

    def __init__(self, name: str, factory):
        self.name = name
        self._factory = factory

    def _make_ep(self, alpha: float):
        return self._factory(self.cfg, alpha)

    def _init(self) -> None:
        self.first_alarm_ev: int | None = None  # event round of first evidence alarm
        self.n_used = 0  # labels fed to the evidence
        super()._init()

    def _feed(self, ev: int, x: float) -> bool:
        used = self.ep.update(ev, x)
        self.n_used += int(used)
        if used and self.first_alarm_ev is None and self.ep.alarm:
            self.first_alarm_ev = ev
        return used


def _registry() -> dict:
    reg = {}
    for tag, mix in (("s1", False), ("s4", True)):
        reg[f"iid_{tag}"] = lambda c, a, m=mix: IIDEvidence(c, a, m)
        for g in (4, 10):
            reg[f"thin{g}_{tag}"] = lambda c, a, m=mix, g=g: IIDEvidence(c, a, m, thin_gap=g)
        reg[f"mlr_{tag}"] = lambda c, a, t=tag: ExistingMarkovLR(c, a, t)
        for rb in (0.8, 0.95):
            reg[f"env{rb:g}_{tag}"] = lambda c, a, m=mix, rb=rb: envelope_evidence(c, a, rb, m)
            reg[f"exact{rb:g}_{tag}"] = lambda c, a, m=mix, rb=rb: exact_evidence(c, a, rb, m)
    reg["iid_repo32"] = lambda c, a: IIDEvidence(c, a, True, n_starts32=True)
    reg["mlr_default8"] = lambda c, a: ExistingMarkovLR(c, a, "default")
    return reg


EVIDENCE = _registry()
METHOD_NAMES = tuple(EVIDENCE)


def build_gate(name: str) -> GapGate:
    if name not in EVIDENCE:
        raise ValueError(f"unknown gap-mix method {name}")
    return GapGate(name, EVIDENCE[name])


__all__ = [
    "EVIDENCE",
    "METHOD_NAMES",
    "EnvelopeStart",
    "ExactGapStart",
    "GapGate",
    "RestartMixture",
    "build_gate",
    "certified_null_sup_loglik",
    "envelope_expectation",
    "envelope_log_factor",
    "envelope_u",
    "exact_loglik",
    "rho_cell_edges",
]
