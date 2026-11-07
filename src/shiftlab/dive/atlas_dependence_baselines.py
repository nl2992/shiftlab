"""Dependence-robust SOTA baselines for the Failure Atlas (Amendment 8, "Added SOTA baselines").

Two gated :class:`~shiftlab.dive.switching_explore.Method` baselines, both on the ``episode_front``
calendar (uniform query calendar, all of alpha spent on episode 0, ``econ_ok`` check, window-mean
rollback, later episodes untested). They differ only in the promotion evidence:

* ``markov_lr_gate``: Markov-likelihood e-process on the released-label skeleton.
* ``thinned_hedged_gate``: the repository started-mixture e-process fed only labels whose query
  round is at least ``G_THIN = 10`` rounds after the last label used for evidence.

Predictability: ``decide`` uses only labels released by round ``t``; the calendar is deterministic.
Nothing here is a novelty or efficacy claim.

Validity argument for ``markov_lr_gate`` (declared null class)
-------------------------------------------------------------
Let ``z_1, z_2, ...`` be the favourable indicators (``z = 1`` iff ``D < 0``; for the harness
streams ``D`` is +1 or -1 so this is exact) of the queried labels in query order, which equals
release order for a constant delay. Null class ``H0``: ``z`` is a homogeneous 2-state Markov chain
with transitions ``a = P(1|0)``, ``b = P(1|1)`` and stationary favourable probability
``pi = a / (1 - b + a) <= q0 = (1 + h) / 2`` (equivalent to ``E[-D] <= h`` in stationarity). The
linear region ``{a (1 - q0) <= q0 (1 - b)}`` is convex.

For a start index ``s`` (fixed before data) and the likelihood conditional on ``z_s``, let
``M_s = sum_k w_k prod_t p_k(z_t | z_{t-1})`` be a fixed-weight mixture over the declared grid of
alternative transition matrices (those with ``pi > q0``) and
``E_s = M_s / sup_{theta in H0} prod_t p_theta(z_t | z_{t-1})``. For the true ``theta* in H0``,
``E_s <= M_s / prod_t p_theta*(...)``, and the right side is a nonnegative martingale with mean 1
(a likelihood ratio of a probability measure against ``theta*``). Hence ``E_s`` is dominated by a
test martingale under every member of ``H0``, so by Ville ``P(sup_n E_s >= 1/alpha) <= alpha``
(generalised-LR / universal-inference form with a fixed, non-data-dependent numerator; the sup is
over the full history, which only shrinks ``E_s``). The final statistic is the fixed uniform
mixture over at most 8 prespecified start positions (label index), again an e-process; a start
contributes 1 until it has seen one transition. The null-set supremum is exact: the unconstrained
MLE if feasible, else the concave 1-D maximum on the boundary line ``a = kappa (1 - b)``,
``kappa = q0 / (1 - q0)``, by vectorised bisection on the derivative.

Approximation flags (not covered by the argument above)
-------------------------------------------------------
1. Skeleton vs round chain. If the round-level chain is a stationary 2-state Markov chain, the
   chain observed at query gaps ``g_k`` has the same stationary ``pi`` and lag-``g_k`` transitions
   ``(pi (1 - rho^g), pi + rho^g (1 - pi))``. With a deterministic (predictable, D-independent)
   calendar of nearly equal gaps (they differ by at most one round) these are treated as one
   homogeneous chain: DECLARED APPROXIMATION "skeleton chain treated as Markov with
   gap-dependent transitions absorbed by the grid". Exact validity for arbitrary gap sequences is
   NOT claimed; inhomogeneous gaps would need a time-varying null set.
2. The null is a stationary Markov skeleton. Non-Markov within-regime dependence is outside the
   class.
3. Non-binary ``D`` is binarised by sign, which changes the null; only D in {-1, +1} is exact.
4. Alternative-grid weights are fixed and uniform, so power is diluted relative to an oracle
   alternative; this is the price of a fixed, valid mixture.

``thinned_hedged_gate`` validity: the repository started-mixture bounded-mean e-process is a valid
e-process for ``E[-D_t - h | F] <= 0``. After thinning, only dependence between *used* labels
matters; validity holds when the retained labels, conditional on their history, have mean at most
the boundary, which is assumed (not proved) once the gap exceeds the chain's mixing time. For a
persistent chain (rho = 0.8) a gap of 10 rounds leaves lag-10 correlation 0.8^10 ~ 0.11, so exact
conditional validity is not claimed. ``g_t = 10`` is fixed before data.
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp, xlogy

from shiftlab.dive.switching_explore import (
    Config,
    Method,
    Released,
    started_gate,
    uniform_calendar,
)

G_THIN = 10
ALT_VALUES = (0.02, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.98)


def _alt_grid(q0: float) -> np.ndarray:
    """Declared grid of alternative transition pairs ``(a, b)`` with stationary probability > q0."""
    g = [(a, b) for a in ALT_VALUES for b in ALT_VALUES if a / (1.0 - b + a) > q0 + 1e-12]
    if not g:
        raise ValueError("empty alternative grid")
    return np.asarray(g, dtype=float)


def _loglik(n: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Conditional log-likelihood from counts ``n = (n00, n01, n10, n11)`` along the last axis."""
    return (
        xlogy(n[..., 1], a)
        + xlogy(n[..., 0], 1.0 - a)
        + xlogy(n[..., 3], b)
        + xlogy(n[..., 2], 1.0 - b)
    )


def null_sup_loglik(n: np.ndarray, q0: float) -> np.ndarray:
    """Sup of the Markov conditional log-likelihood over ``{pi <= q0}``; counts have shape (S, 4)."""
    n = np.asarray(n, dtype=float)
    n0 = n[:, 0] + n[:, 1]
    n1 = n[:, 2] + n[:, 3]
    a_hat = np.divide(n[:, 1], n0, out=np.zeros_like(n0), where=n0 > 0)
    b_hat = np.divide(n[:, 3], n1, out=np.zeros_like(n1), where=n1 > 0)
    feas = a_hat * (1.0 - q0) <= q0 * (1.0 - b_hat) + 1e-12
    ll_free = _loglik(n, a_hat, b_hat)
    kappa = q0 / (1.0 - q0)
    lo = np.full(len(n), max(0.0, 1.0 - 1.0 / kappa))
    hi = np.full(len(n), 1.0 - 1e-12)
    for _ in range(60):  # bisection on the (decreasing) derivative of the concave boundary profile
        mid = 0.5 * (lo + hi)
        am = kappa * (1.0 - mid)
        der = (
            -(n[:, 1] + n[:, 2]) / (1.0 - mid)
            + n[:, 0] * kappa / np.maximum(1.0 - am, 1e-300)
            + n[:, 3] / np.maximum(mid, 1e-300)
        )
        up = der > 0
        lo = np.where(up, mid, lo)
        hi = np.where(up, hi, mid)
    bb = 0.5 * (lo + hi)
    ll_bd = _loglik(n, np.clip(kappa * (1.0 - bb), 0.0, 1.0), bb)
    return np.where(feas, ll_free, ll_bd)


class MarkovLREProcess:
    """Fixed mixture over start labels of (alt-grid mixture LR) / (sup over null Markov chains)."""

    def __init__(self, q0: float, alpha: float, n_labels: int):
        self.q0, self.alpha = float(q0), float(alpha)
        step = max(1, n_labels // 8)  # at most 8 starts: fewer starts = less mixture dilution
        self.starts = np.arange(0, max(1, n_labels), step)
        self.log_w = -np.log(len(self.starts))
        self.grid = _alt_grid(self.q0)
        a, b = self.grid[:, 0], self.grid[:, 1]
        # log p_k(z | prev), keyed (prev, z)
        self.tab = {
            (0, 0): np.log1p(-a),
            (0, 1): np.log(a),
            (1, 0): np.log1p(-b),
            (1, 1): np.log(b),
        }
        self.log_k = -np.log(len(self.grid))
        self.num = np.zeros((len(self.starts), len(self.grid)))
        self.cnt = np.zeros((len(self.starts), 4))
        self.n = 0
        self.prev = -1
        self._alarm_cache_key: tuple[int, float] | None = None
        self._alarm_cache = False

    @property
    def log_e_value(self) -> float:
        started = self.n > self.starts + 1  # at least one transition seen from start s
        if not started.any():
            return 0.0
        den = null_sup_loglik(self.cnt[started], self.q0)
        lm = logsumexp(self.num[started], axis=1) + self.log_k
        comp = np.zeros(len(self.starts))
        comp[started] = lm - den
        return float(logsumexp(comp + self.log_w))

    @property
    def alarm(self) -> bool:
        key = (self.n, self.alpha)
        if self._alarm_cache_key != key:
            self._alarm_cache = self.log_e_value >= -np.log(self.alpha)
            self._alarm_cache_key = key
        return self._alarm_cache

    def update_z(self, z: int) -> None:
        z = int(z)
        if self.n > 0:
            act = np.nonzero(self.n > self.starts)[0]  # starts whose first label precedes this one
            if len(act):
                self.num[act] += self.tab[(self.prev, z)]
                self.cnt[act, 2 * self.prev + z] += 1.0
        self.prev = z
        self.n += 1


class _FrontGated(Method):
    """episode_front machinery (calendar, alpha spending, econ_ok, rollback), pluggable evidence."""

    def _make_ep(self, alpha: float):  # pragma: no cover - overridden
        raise NotImplementedError

    def _feed(self, ev: int, x: float) -> bool:  # pragma: no cover - overridden
        raise NotImplementedError

    def _reset_feed(self) -> None:
        pass

    def _new_episode(self, j: int, start: int) -> None:
        self.j, self.ep_start = j, start
        self.ep = self._make_ep(self.cfg.alpha) if j == 0 else None  # "front" spending
        self.ep_labels: list[float] = []
        self._reset_feed()

    def _init(self) -> None:
        c = self.cfg
        self.cal = uniform_calendar(c.T, c.B, c.d)
        self.m = max(3, c.B // 8)
        self.act = 0
        self.promo_t = 0
        self.post: list[float] = []
        self._new_episode(0, 0)

    def decide(self, t: int, released: Released) -> tuple[int, bool]:
        c = self.cfg
        for ev, x in released:
            if self.act == 0:
                if ev >= self.ep_start and self.ep is not None and self._feed(ev, x):
                    self.ep_labels.append(x)  # labels used as evidence
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


class MarkovLRGate(_FrontGated):
    name = "markov_lr_gate"

    def _make_ep(self, alpha: float):
        return MarkovLREProcess((1.0 + self.cfg.h) / 2.0, alpha, self.cfg.B)

    def _feed(self, ev: int, x: float) -> bool:
        self.ep.update_z(1 if x < 0 else 0)
        return True


class ThinnedHedgedGate(_FrontGated):
    name = "thinned_hedged_gate"

    def _make_ep(self, alpha: float):
        c = self.cfg
        return started_gate(1 + c.h, alpha, min(c.B, c.T // G_THIN + 1))

    def _reset_feed(self) -> None:
        self.last_used = None

    def _feed(self, ev: int, x: float) -> bool:
        if self.last_used is not None and ev - self.last_used < G_THIN:
            return False  # received but ignored for evidence
        self.last_used = ev
        self.ep.update(-x - self.cfg.h)
        return True


DEP_METHODS: dict[str, tuple] = {
    "markov_lr_gate": (
        lambda cfg: MarkovLRGate(),
        True,
        (
            "Markov-likelihood e-process on the queried-label skeleton (audit: strongest "
            "dependence-robust baseline). Fixed-weight mixture over a declared (a,b) grid with "
            "stationary favourable prob > (1+h)/2, divided by the sup over the composite 2-state "
            "Markov null pi <= (1+h)/2 (generalised-LR, dominated by a test martingale per null "
            "member), fixed mixture over <= 8 start labels. APPROXIMATION: skeleton treated as one "
            "homogeneous Markov chain (gaps nearly equal on the uniform calendar); exact validity "
            "for arbitrary gaps not claimed. D binarised by sign. Promotion: episode_front alpha "
            "spending, econ_ok, window-mean rollback."
        ),
    ),
    "thinned_hedged_gate": (
        lambda cfg: ThinnedHedgedGate(),
        True,
        (
            "Repo started-mixture bounded-mean e-process fed only queried labels with query round "
            ">= g_t = 10 after the last label used (Waudby-Smith-Ramdas hedged capital on thinned "
            "queries, adapted). Other labels received but ignored; calendar as episode_front. "
            "Validity assumes lag-10 independence of used labels (not proved; rho=0.8 leaves "
            "0.8^10~0.11 lag correlation). g_t fixed before data."
        ),
    ),
}


def build_dep(name: str, cfg: Config | None = None) -> Method:
    """Instantiate a dependence baseline (``cfg`` accepted for factory symmetry)."""
    if name not in DEP_METHODS:
        raise ValueError(f"unknown dependence baseline {name}")
    return DEP_METHODS[name][0](cfg)


__all__ = [
    "DEP_METHODS",
    "G_THIN",
    "MarkovLREProcess",
    "MarkovLRGate",
    "ThinnedHedgedGate",
    "build_dep",
    "null_sup_loglik",
]
