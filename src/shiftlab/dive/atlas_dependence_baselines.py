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


class GapEnvelopeEProcess:
    """Started betting process for a bounded-persistence one-sided transition envelope.

    Under the declared null, the favourable-indicator probability is at most ``q0`` initially.
    After a previous favourable observation and an event gap ``g``, it is at most
    ``q0 + (1-q0)*rho_bar**g``; after an unfavourable observation it is at most ``q0``.
    Each fixed alternative ``r`` bets only when ``r`` exceeds this predictable upper bound.
    """

    ALT_GRID = np.arange(0.60, 0.951, 0.05)

    def __init__(self, q0: float, alpha: float, rho_bar: float):
        if not 0 < q0 < 1 or not 0 < alpha < 1 or not 0 <= rho_bar < 1:
            raise ValueError("q0/alpha must be in (0,1) and rho_bar in [0,1)")
        if np.any(self.ALT_GRID <= q0) or np.any(self.ALT_GRID >= 1):
            raise ValueError("alternative grid must lie strictly between q0 and 1")
        self.q0, self.alpha, self.rho_bar = float(q0), float(alpha), float(rho_bar)
        self.grid = self.ALT_GRID.copy()
        self.log_wealth = np.full(len(self.grid), -np.inf)
        self.n = 0
        self.prev: int | None = None
        self.prev_event: int | None = None

    @property
    def log_e_value(self) -> float:
        if self.n == 0:
            return -np.inf
        return float(logsumexp(self.log_wealth) - np.log(len(self.grid)))

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update_z(self, z: int, event: int) -> None:
        z, event = int(z), int(event)
        if z not in (0, 1):
            raise ValueError("z must be binary")
        if self.prev_event is not None and event <= self.prev_event:
            raise ValueError("query events must arrive in strictly increasing order")
        gap = None if self.prev_event is None else event - self.prev_event
        if self.prev == 1 and gap is not None:
            u = self.q0 + (1.0 - self.q0) * self.rho_bar**gap
        else:
            u = self.q0

        active = self.grid > u
        log_factor = np.zeros_like(self.grid)
        if np.any(active):
            if z:
                log_factor[active] = np.log(self.grid[active]) - np.log(u)
            else:
                log_factor[active] = np.log1p(-self.grid[active]) - np.log1p(-u)

        self.n += 1
        log_start_weight = -np.log(self.n * (self.n + 1.0))
        self.log_wealth = np.logaddexp(self.log_wealth, log_start_weight) + log_factor
        self.prev, self.prev_event = z, event


class GapMarkovSUIProcess:
    """Exact-gap sequential universal inference for a stationary refresh-or-hold null.

    Each candidate start conditions on its first observed label. Subsequent conditional
    likelihoods use the actual event gap. The null likelihood denominator is bounded above
    by maximizing each transition factor at the corners of a rectangular (p, rho) cell,
    then taking the largest cell product. This is conservative for every shared null
    parameter pair; it is not a grid-point plug-in. No log-likelihood flooring is used.

    The fixed finite start prior spans prespecified sparse positions in the known calendar. A
    dormant start contributes its unit initial capital until its first label is observed.
    """

    ALT_RHO = np.asarray([0.0, 0.5, 0.8, 0.95, 0.98])

    def __init__(
        self,
        q0: float,
        alpha: float,
        n_labels: int,
        n_p: int = 100,
        n_rho: int = 200,
        max_starts: int = 8,
    ):
        if not 0 < q0 < 1 or not 0 < alpha < 1 or n_labels < 1:
            raise ValueError("invalid q0, alpha, or start count")
        self.q0, self.alpha = float(q0), float(alpha)
        self.n_labels = int(n_labels)
        self.starts = np.unique(
            np.linspace(0, self.n_labels - 1, min(self.n_labels, max_starts), dtype=int)
        )
        self.p_edges = np.linspace(0.0, self.q0, n_p + 1)
        # Include both endpoints. A geometric mesh resolves persistence close to one.
        rr = np.geomspace(1e-5, 1.0, n_rho - 1)
        self.r_edges = np.unique(np.r_[0.0, rr, 1.0])
        self.n_null_cells = (len(self.r_edges) - 1, len(self.p_edges) - 1)
        base_p = np.unique(np.r_[np.linspace(self.q0 + (1.0 - self.q0) / 100, 0.95, 9), 0.99])
        base_p = base_p[(base_p > self.q0) & (base_p < 1.0)]
        if not len(base_p):
            raise ValueError("no alternative stationary means above q0")
        self.alt_p = np.tile(base_p, len(self.ALT_RHO))
        self.alt_r = np.repeat(self.ALT_RHO, len(base_p))
        self.log_num = np.zeros((len(self.starts), len(self.alt_p)))
        self.log_den_cells = np.zeros((len(self.starts), *self.n_null_cells))
        self.z: list[int] = []
        self.events: list[int] = []
        self._log_e = 0.0

    @staticmethod
    def _log_prob(prob: np.ndarray) -> np.ndarray:
        with np.errstate(divide="ignore"):
            return np.log(prob)

    def _transition(self, prev: int, hit: int, gap: int) -> tuple[np.ndarray, np.ndarray]:
        # Cellwise supremum occurs at a corner: each refresh-or-hold transition factor is
        # monotone separately in p and rho on the cell.
        corners = []
        for p in (self.p_edges[:-1][None, :], self.p_edges[1:][None, :]):
            for rho in (self.r_edges[:-1, None], self.r_edges[1:, None]):
                a = rho**gap
                prob1 = a * prev + (1.0 - a) * p
                corners.append(prob1 if hit else 1.0 - prob1)
        null_upper_log = self._log_prob(np.maximum.reduce(corners))
        alt_a = self.alt_r**gap
        alt_prob1 = alt_a * prev + (1.0 - alt_a) * self.alt_p
        alt_log = self._log_prob(alt_prob1 if hit else 1.0 - alt_prob1)
        return null_upper_log, alt_log

    @property
    def log_e_value(self) -> float:
        return self._log_e

    @property
    def alarm(self) -> bool:
        return self.log_e_value >= -np.log(self.alpha)

    def update_z(self, z: int, event: int) -> None:
        z, event = int(z), int(event)
        if z not in (0, 1):
            raise ValueError("z must be binary")
        if self.events and event <= self.events[-1]:
            raise ValueError("query events must be strictly increasing")
        i = len(self.z)
        if i >= self.n_labels:
            raise ValueError("more labels than the frozen start prior supports")
        if i:
            gap = event - self.events[-1]
            nu, an = self._transition(self.z[-1], z, gap)
            # Only prespecified starts before this transition are active; each conditions
            # on its own first label and uses only later transitions.
            active_idx = np.flatnonzero(self.starts < i)
            self.log_den_cells[active_idx] += nu
            self.log_num[active_idx] += an
        self.z.append(z)
        self.events.append(event)
        active_idx = np.flatnonzero(self.starts < i)
        terms = np.full(len(self.starts), -np.inf)
        if len(active_idx):
            log_ratios = logsumexp(self.log_num[active_idx], axis=1) - np.max(
                self.log_den_cells[active_idx], axis=(1, 2)
            )
            terms[active_idx] = log_ratios - np.log(len(self.starts))
        terms[self.starts >= i] = -np.log(len(self.starts))
        self._log_e = float(logsumexp(terms))


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


class GapMarkovSUIGate(_FrontGated):
    """Fixed-calendar Atlas gate using exact observed gaps under a stationary Markov null."""

    name = "gap_markov_sui"

    def _make_ep(self, alpha: float):
        q0 = (1.0 + self.cfg.h) / 2.0
        return GapMarkovSUIProcess(q0, alpha, max(1, len(self.cal)), n_p=24, n_rho=48)

    def _feed(self, ev: int, x: float) -> bool:
        self.ep.update_z(1 if x < 0 else 0, ev)
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


class GapEnvelopeGate(_FrontGated):
    """Fixed-calendar gate using the actual query gap and a declared persistence bound."""

    def __init__(self, rho_bar: float):
        self.rho_bar = float(rho_bar)
        self.name = f"gap_envelope_rho{self.rho_bar:g}"

    def _make_ep(self, alpha: float):
        q0 = (1.0 + self.cfg.h) / 2.0
        return GapEnvelopeEProcess(q0, alpha, self.rho_bar)

    def _feed(self, ev: int, x: float) -> bool:
        self.ep.update_z(1 if x < 0 else 0, ev)
        return True


DEP_METHODS: dict[str, tuple] = {
    "gap_markov_sui": (
        lambda cfg: GapMarkovSUIGate(),
        True,
        (
            "Exact-gap sequential universal inference for a stationary refresh-or-hold Markov "
            "null with stationary favourable probability p <= (1+h)/2. Conditions each finite "
            "start on its first observed label; fixed alternative mixture over p>(1+h)/2 and "
            "rho values; conservative rectangular-cell upper bound for the composite null "
            "likelihood. Fixed calendar and constant release delay. This is a transfer of known "
            "universal-inference machinery, not a novelty claim; no guarantee for changing p_t."
        ),
    ),
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
    "gap_envelope_rho08": (
        lambda cfg: GapEnvelopeGate(0.8),
        True,
        (
            "Started mixture of one-sided Bernoulli e-factors with the observed query gap in a "
            "conditional Markov envelope; valid for binary D under the declared transition "
            "contract p_t <= (1+h)/2 and rho <= .8. Fixed uniform calendar, fixed delays."
        ),
    ),
    "gap_envelope_rho95": (
        lambda cfg: GapEnvelopeGate(0.95),
        True,
        (
            "Started mixture of one-sided Bernoulli e-factors with the observed query gap in a "
            "conditional Markov envelope; valid for binary D under the declared transition "
            "contract p_t <= (1+h)/2 and rho <= .95. Fixed uniform calendar, fixed delays."
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
    "GapEnvelopeEProcess",
    "GapEnvelopeGate",
    "GapMarkovSUIGate",
    "GapMarkovSUIProcess",
    "MarkovLREProcess",
    "MarkovLRGate",
    "ThinnedHedgedGate",
    "build_dep",
    "null_sup_loglik",
]
