"""Gap-Mix rho-robust variants (GAVE-R WP1b). Imports ``gapmix.py``; does not modify it.

Declared null (as WP1, with the dependence cap raised): stationary two-state round chain,
``p <= q0``, ``rho in [0, RHO_MAX]`` with ``RHO_MAX = 0.99``, deterministic calendar, constant
delay, conditioning on each restart start's first label. See docs/gaver/11_GAPMIX_RHO_RESULTS.md
section 0 for the validity arguments; the short form follows.

* ``RhoStart`` shares one numerator and one count table per restart start and computes the
  certified null supremum once per cell of ``rho`` (width 0.005, 198 cells up to 0.99). The
  denominator for any ``rho_bar`` is the max over the first ``rho_bar/0.005`` cells, which equals
  ``gapmix.certified_null_sup_loglik`` for that ``rho_bar`` (tested).
* ``RhoCS`` is an anytime-valid upper confidence sequence for ``rho``: per (gap, previous state)
  group the successors are i.i.d. Bernoulli, ``a_1,g - a_0,g = rho^g``; Clopper-Pearson bounds are
  spent over n with ``1/(n(n+1))`` and over gaps with ``1/(j(j+1))``.
* ``cs_sup`` (B2): denominator sup over ``[0, ub_t]``; on the CS event ``G`` this is >= the sup over
  ``[0, rho*]`` so the statistic is <= a test martingale. ``gate`` (A-gated): fixed-weight mixture
  over a ladder of fixed ``rho_bar_k`` read out only for ``rho_bar_k >= ub_t``. ``env_cs`` (B1):
  envelope factor with predictable plug-in ``rho_bar = ub_{t-1}``. All three spend
  ``CS_FRAC * alpha`` on the CS and test at ``(1-CS_FRAC) * alpha``. ``mix`` (no CS) is the plain
  mixture, INVALID under rho above its smallest rung, kept as a negative control.

NOT proven: closed-loop validity, informative delay, non-stationary or non-Markov nulls; the CS is
conservative; the stationarity assumption is also used by the CS.
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp, xlogy
from scipy.stats import beta

from shiftlab.gaver import gapmix as gm

CELL_W = 0.005
RHO_MAX = 0.99
N_CELLS = round(RHO_MAX / CELL_W)  # 198
EDGES = CELL_W * np.arange(N_CELLS + 1)
CS_FRAC = 0.2
BISECT_ITERS = 50
LADDER = (0.5, 0.8, 0.95, 0.99)
W_EQ = (0.25, 0.25, 0.25, 0.25)
W_08 = (0.15, 0.5, 0.2, 0.15)
LADDER_FINE = (0.5, 0.65, 0.8, 0.9, 0.95, 0.99)
W_FINE = (1.0 / 6,) * 6


def n_cells_for(rho_bar: float) -> int:
    """Number of 0.005-cells needed to cover ``[0, rho_bar]`` (never fewer than 1)."""
    return int(np.clip(np.ceil(rho_bar / CELL_W - 1e-9), 1, N_CELLS))


# ----------------------------------------------------------------------------- shared cell sup


def cell_best_loglik(counts: dict[int, np.ndarray], q0: float) -> np.ndarray:
    """Per-rho-cell certified upper bound of the exact-gap log-likelihood (p <= q0 maximised).

    Same certification as ``gapmix.certified_null_sup_loglik`` (endpoint-monotone transition
    probabilities, concave in p, bisection), vectorised over gaps and the 198 cells; the slack
    ``EPS_SLACK`` is added by the caller after taking the max over cells.
    """
    gs = [g for g, n in counts.items() if n.sum() > 0]
    if not gs:
        return np.zeros(N_CELLS)
    g = np.array(gs, float)[:, None]
    n = np.array([counts[k] for k in gs])
    n0, n1, n2, n3 = (n[:, i : i + 1] for i in range(4))
    lo, hi = EDGES[None, :-1] ** g, EDGES[None, 1:] ** g
    a, b = 1.0 - hi, 1.0 - lo

    def obj(p):
        p = p[None, :]
        return (
            xlogy(n0, 1.0 - p * a)
            + xlogy(n1, p * b)
            + xlogy(n2, (1.0 - p) * b)
            + xlogy(n3, p + (1.0 - p) * hi)
        ).sum(0)

    def deriv(p):
        p = p[None, :]
        return (
            -n0 * a / np.maximum(1.0 - p * a, 1e-300)
            + n1 / np.maximum(p, 1e-300)
            - n2 / np.maximum(1.0 - p, 1e-300)
            + n3 * a / np.maximum(p + (1.0 - p) * hi, 1e-300)
        ).sum(0)

    q0v = np.full(N_CELLS, q0)
    at_cap = deriv(q0v) >= 0.0
    lo_p, hi_p = np.zeros(N_CELLS), q0v.copy()
    for _ in range(BISECT_ITERS):
        mid = 0.5 * (lo_p + hi_p)
        up = deriv(mid) > 0.0
        lo_p = np.where(up, mid, lo_p)
        hi_p = np.where(up, hi_p, mid)
    p_star = np.where(at_cap, q0, 0.5 * (lo_p + hi_p))
    return np.maximum(obj(p_star), obj(q0v))


class RhoStart:
    """One restart start: exact-gap numerator mixture + per-cell certified null bound."""

    def __init__(self, q0: float, alt_p=gm.ALT_P, alt_rho=gm.ALT_RHO):
        self.q0 = q0
        self.alts = np.array([(p, r) for p in alt_p for r in alt_rho if p > q0])
        self.num = np.zeros(len(self.alts))
        self.counts: dict[int, np.ndarray] = {}
        self.prev: int | None = None
        self.prev_ev = 0
        self.best = np.zeros(N_CELLS)
        self.started = False  # at least one transition

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
        self.best = cell_best_loglik(self.counts, self.q0)
        self.started = True

    @property
    def log_m(self) -> float:
        return float(logsumexp(self.num) - np.log(len(self.alts)))

    def log_e(self, n_cells: int) -> float:
        """``log(M / D)`` with D the certified sup over the first ``n_cells`` cells of rho."""
        if not self.started:
            return 0.0
        return self.log_m - (float(np.max(self.best[:n_cells])) + gm.EPS_SLACK)


class Snap:
    """Frozen view of a ``RhoStart`` after some number of labels (same ``log_e`` interface)."""

    def __init__(self, log_m: float, best: np.ndarray, started: bool):
        self.log_m, self.best, self.started = log_m, best, started

    def log_e(self, n_cells: int) -> float:
        if not self.started:
            return 0.0
        return self.log_m - (float(np.max(self.best[:n_cells])) + gm.EPS_SLACK)


class StartPool:
    """Per-stream cache of ``RhoStart`` trajectories shared by every method run on that stream.

    The labels fed to the evidence depend only on the (deterministic) calendar and the stream, not
    on the method, so all methods see identical (event, z) sequences until they stop feeding at a
    promotion. Caching the per-label snapshots makes the numbers identical to a private
    computation (checked by an assertion on the (event, z) pair at every cached step).
    """

    def __init__(self, q0: float, n_starts: int):
        self.starts = [RhoStart(q0) for _ in range(n_starts)]
        self.cache: list[list] = [[] for _ in range(n_starts)]  # entries: ((ev, z), Snap)

    def step(self, i: int, m: int, ev: int, z: int) -> Snap:
        c = self.cache[i]
        if m < len(c):
            if c[m][0] != (ev, z):
                raise RuntimeError("StartPool reused across different label sequences")
            return c[m][1]
        if m != len(c):
            raise RuntimeError("StartPool step out of order")
        st = self.starts[i]
        st.update(ev, z)
        snap = Snap(st.log_m if st.started else 0.0, st.best, st.started)
        c.append(((ev, z), snap))
        return snap


# ----------------------------------------------------------------------------- confidence sequence


class RhoCS:
    """Anytime-valid upper bound on rho from released labels (valid under the declared null)."""

    def __init__(self, delta: float):
        self.delta = delta
        self.cnt: dict[tuple[int, int], list[int]] = {}  # (gap, prev) -> [n, k successes]
        self.gap_rank: dict[int, int] = {}
        self.prev: int | None = None
        self.prev_ev = 0
        self.ub = RHO_MAX

    def update(self, ev: int, z: int) -> None:
        if self.prev is None:
            self.prev, self.prev_ev = z, ev
            return
        g = ev - self.prev_ev
        self.gap_rank.setdefault(g, len(self.gap_rank) + 1)
        c = self.cnt.setdefault((g, self.prev), [0, 0])
        c[0] += 1
        c[1] += z
        self.prev, self.prev_ev = z, ev
        self._refresh(g)

    def _bound(self, g: int, s: int, upper: bool) -> float:
        n, k = self.cnt.get((g, s), (0, 0))
        if n == 0:
            return 1.0 if upper else 0.0
        j = self.gap_rank[g]
        eps = self.delta / (j * (j + 1)) / (2.0 * n * (n + 1))
        if upper:
            return 1.0 if k >= n else float(beta.ppf(1.0 - eps, k + 1, n - k))
        return 0.0 if k <= 0 else float(beta.ppf(eps, k, n - k + 1))

    def _refresh(self, g: int) -> None:
        lam_ub = min(1.0, max(0.0, self._bound(g, 1, True) - self._bound(g, 0, False)))
        self.ub = min(self.ub, lam_ub ** (1.0 / g), RHO_MAX)


# ----------------------------------------------------------------------------- evidence


class EnvCSStart(gm.EnvelopeStart):
    """Envelope start whose ``rho_bar`` is replaced each step by a predictable CS bound."""

    def update(self, ev: int, z: int, rho_bar: float | None = None) -> None:
        if rho_bar is not None:
            self.rho_bar = rho_bar
        super().update(ev, z)


class RhoEvidence:
    """Restart mixture (``s4``) with the rho handling selected by ``mode``.

    mode ``mix``    : fixed weights over rungs, no CS (single rung = plain exact-gap Gap-Mix)
    mode ``gate``   : as ``mix`` but rungs below ``ub_t`` are excluded from the read-out (CS)
    mode ``cs_sup`` : denominator sup over ``[0, ub_t]`` (CS)
    mode ``env_cs`` : envelope factor with plug-in ``rho_bar = ub`` before the current label (CS)
    """

    def __init__(self, cfg, alpha: float, mode: str, rungs=LADDER, weights=W_EQ, pool=None):
        if mode not in {"mix", "gate", "cs_sup", "env_cs"}:
            raise ValueError(mode)
        self.mode, self.rungs = mode, tuple(rungs)
        self.logw = np.log(np.asarray(weights, float))
        self.ncell = [n_cells_for(r) for r in self.rungs]
        q0 = (1.0 + cfg.h) / 2.0
        self.q0 = q0
        self.thresholds = gm.restart_thresholds(cfg.T, True)
        if mode == "env_cs":
            self.starts = [EnvCSStart(q0, RHO_MAX) for _ in self.thresholds]
        else:
            self.pool = pool or StartPool(q0, len(self.thresholds))
            self.starts = [Snap(0.0, np.zeros(N_CELLS), False) for _ in self.thresholds]
            self.step_count = [0] * len(self.thresholds)
        self.uses_cs = mode != "mix"
        self.cs = RhoCS(CS_FRAC * alpha) if self.uses_cs else None
        self.alpha_test = alpha * (1.0 - CS_FRAC) if self.uses_cs else alpha
        self.n_used = 0
        self._log_e = 0.0

    @property
    def ub(self) -> float:
        return self.cs.ub if self.cs is not None else RHO_MAX

    def _start_log_e(self, st) -> float:
        if self.mode == "env_cs":
            return st.log_e
        if self.mode == "cs_sup":
            return st.log_e(n_cells_for(self.ub))
        keep = np.ones(len(self.rungs), bool)
        if self.mode == "gate":
            keep = np.array([r >= self.ub - 1e-12 for r in self.rungs])
            keep[-1] = True  # the top rung is the declared class cap
        comps = [self.logw[i] + st.log_e(self.ncell[i]) for i in range(len(keep)) if keep[i]]
        return float(logsumexp(comps))

    def update(self, ev: int, x: float) -> bool:
        z = 1 if x < 0 else 0
        for i, thr in enumerate(self.thresholds):
            if ev >= thr:
                if self.mode == "env_cs":
                    self.starts[i].update(ev, z, self.cs.ub)  # ub from labels strictly before
                else:
                    self.starts[i] = self.pool.step(i, self.step_count[i], ev, z)
                    self.step_count[i] += 1
        if self.cs is not None:
            self.cs.update(ev, z)
        self.n_used += 1
        comp = np.array([self._start_log_e(s) for s in self.starts])
        self._log_e = float(logsumexp(comp) - np.log(len(comp)))
        return True

    @property
    def log_e_value(self) -> float:
        return self._log_e

    @property
    def alarm(self) -> bool:
        return self._log_e >= -np.log(self.alpha_test)


def _single(rb: float):
    return lambda c, a, pool=None: RhoEvidence(c, a, "mix", (rb,), (1.0,), pool=pool)


def _registry() -> dict:
    reg = {
        "exact0.8_s4": _single(0.8),  # fast re-implementation of the WP1 reference (tested equal)
        "exact0.95_s4": _single(0.95),
        "exact0.99_s4": _single(0.99),  # variant C
        "exactcs_s4": lambda c, a, pool=None: RhoEvidence(c, a, "cs_sup", pool=pool),  # variant B2
        "gate_eq_s4": lambda c, a, pool=None: RhoEvidence(
            c, a, "gate", LADDER, W_EQ, pool=pool
        ),  # A-gated
        "gate_w_s4": lambda c, a, pool=None: RhoEvidence(c, a, "gate", LADDER, W_08, pool=pool),
        "gate_fine_eq_s4": lambda c, a, pool=None: RhoEvidence(
            c, a, "gate", LADDER_FINE, W_FINE, pool=pool
        ),
        "envcs_s4": lambda c, a, pool=None: RhoEvidence(c, a, "env_cs"),  # variant B1
        "mixnaive_eq_s4": lambda c, a, pool=None: RhoEvidence(
            c, a, "mix", LADDER, W_EQ, pool=pool
        ),  # NEG control
        "mixnaive_w_s4": lambda c, a, pool=None: RhoEvidence(
            c, a, "mix", LADDER, W_08, pool=pool
        ),  # NEG control
    }
    return reg


EVIDENCE_RHO = _registry()
REFERENCE_WP1 = ("mlr_default8",)  # served by gapmix.EVIDENCE
METHOD_NAMES = tuple(EVIDENCE_RHO) + REFERENCE_WP1


def new_pool(T: int = 1000, h: float = 0.1) -> StartPool:
    return StartPool((1.0 + h) / 2.0, len(gm.restart_thresholds(T, True)))


def build_gate(name: str, pool: StartPool | None = None) -> gm.GapGate:
    """``pool`` (optional): per-stream shared cache; must only be reused on the same stream."""
    if name in EVIDENCE_RHO:
        f = EVIDENCE_RHO[name]
        return gm.GapGate(name, lambda c, a: f(c, a, pool))
    if name in REFERENCE_WP1:
        return gm.build_gate(name)
    raise ValueError(f"unknown WP1b method {name}")


__all__ = [
    "EVIDENCE_RHO",
    "METHOD_NAMES",
    "RhoCS",
    "RhoEvidence",
    "RhoStart",
    "StartPool",
    "build_gate",
    "cell_best_loglik",
    "n_cells_for",
    "new_pool",
]
