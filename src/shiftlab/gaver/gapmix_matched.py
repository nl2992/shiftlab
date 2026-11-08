"""Matched-assumption comparators for Gap-Mix (docs/methods_recovery/51_GAPMIX_MATCHED.md).

Both evidence processes use exactly the declared null class of Gap-Mix: the round-level favourable
indicator is a stationary two-state chain with ``p <= q0`` and persistence ``rho in [0, rho_bar]``
(``rho_bar = 0.8``), observed at known event-round gaps ``g`` through ``P(Z'=1 | z) = p + (z - p) rho^g``.
They plug into the Gap-Mix harness unchanged (``update(ev, x)``, ``alarm``, ``log_e_value``,
``n_used``) through ``shiftlab.gaver.gapmix.GapGate``. Gap-Mix itself is not modified.

``mlr_rb0.8``  Existing gap-blind Markov LR (``MarkovLREProcess``, 8 label-index starts, same alternative
    grid and numerator) whose null supremum runs over the homogeneous chains
    ``{pi <= q0, lambda = 1 - a - b in [0, rho_bar ** g_min]}`` instead of all 2-state chains, where
    ``g_min`` is the smallest gap of the (data-independent) uniform calendar. The supremum is the
    certified upper bound of ``gapmix.certified_null_sup_loglik`` (here with a single gap class and
    ``lambda`` cells). VALIDITY: the universal-inference argument (``M / sup_{H0'} L <= M / L(theta*)``)
    needs the true conditional law to be a member of the homogeneous class. That holds only if every gap
    is the same constant ``g``. The uniform calendar has gaps ``g`` and ``g + 1``, so the true skeleton is
    inhomogeneous (``lambda_k in {rho^g, rho^(g+1)}``) and NOT covered; the gap-blind restricted process
    is therefore NOT PROVEN VALID here. It is run as an empirical comparator and flagged.

``ui_gap_allstarts``  Universal-inference e-detector (Wasserman, Ramdas, Balakrishnan 2020; Shin, Ramdas,
    Rinaldo 2023 e-detectors). For a start at label index ``s``: numerator ``prod_k q_k(z_k | z_{k-1})`` with
    ``q_k`` the exact gap-``g_k`` transition of a PREDICTABLE plug-in alternative ``theta_hat_{k-1}`` (grid
    MAP estimate of ``(p, rho)`` from the labels of this start before observation ``k``, projected onto the
    alternative region ``p in [0.60, 0.95]``, ``rho in [0, 0.90]``, with two pseudo-transitions at
    ``theta_0 = (0.75, 0.4)``); denominator: the same certified hindsight supremum over ``H0`` as Gap-Mix
    (``rho <= rho_bar``, exact ``P^g``). Starts at every ``k``-th label index (``k = max(1, B // 50)``, so
    about 50 starts), each conditioning on its first label. The e-detector is the equal-weight average of the
    per-start e-processes (each equal to 1 before its start) with a FIXED number of starts, alarm at
    ``1/alpha``. VALIDITY (given the declared null, deterministic/predictable gaps): for the true
    ``theta* in H0``, ``e_s <= M_s / L_s(theta*)`` and ``M_s = prod q_k`` with predictable ``q_k`` makes
    ``M_s / L_s(theta*)`` a nonnegative martingale (chain rule, no iid needed), so each start and the fixed
    average are e-processes and Ville's inequality gives type I error ``<= alpha`` over the horizon. The
    raw Shiryaev-Roberts SUM with threshold ``1/alpha`` controls ARL, not horizon false-alarm probability;
    the normalised average is the finite-horizon-valid form (same convention as Gap-Mix's restart mixture).
"""

from __future__ import annotations

import numpy as np
from scipy.special import logsumexp, xlogy

from shiftlab.dive.atlas_dependence_baselines import MarkovLREProcess
from shiftlab.dive.switching_explore import uniform_calendar
from shiftlab.gaver import gapmix as gm

EPS_SLACK = gm.EPS_SLACK
Q0_DEFAULT = 0.55
UI_P_GRID = np.round(np.arange(0.60, 0.9501, 0.025), 4)
UI_RHO_GRID = np.round(np.arange(0.0, 0.9001, 0.05), 4)
UI_THETA0 = (0.75, 0.4)
UI_MAX_GAP_CLASSES = 12
LAM_CELL_WIDTH = 0.005


# ------------------------------------------------------------------ batched certified supremum


def certified_sup_batch(counts: np.ndarray, gaps, q0: float, edges: np.ndarray) -> np.ndarray:
    """Row-wise ``gapmix.certified_null_sup_loglik``. ``counts`` has shape (S, G, 4), ``gaps`` length G.

    Rows with no transitions return 0.0 (as the scalar version does). Same cell-endpoint bound,
    same bisection and slack, so the output equals the scalar function row by row.
    """
    counts = np.asarray(counts, dtype=float)
    gaps = np.asarray(gaps, dtype=float)
    s_rows = counts.shape[0]
    lo_e, hi_e = edges[:-1], edges[1:]
    keep = [g for g in range(counts.shape[1]) if counts[:, g, :].sum() > 0]
    if not keep:
        return np.zeros(s_rows)
    lam_lo = [lo_e ** gaps[g] for g in keep]
    lam_hi = [hi_e ** gaps[g] for g in keep]
    cn = [counts[:, g, :] for g in keep]
    c = len(lo_e)

    def obj(p):
        tot = 0.0
        for n, ll, lh in zip(cn, lam_lo, lam_hi, strict=True):
            tot = (
                tot
                + xlogy(n[:, 0:1], 1.0 - p * (1.0 - lh))
                + xlogy(n[:, 1:2], p * (1.0 - ll))
                + xlogy(n[:, 2:3], (1.0 - p) * (1.0 - ll))
                + xlogy(n[:, 3:4], p + (1.0 - p) * lh)
            )
        return tot

    def deriv(p):
        d = 0.0
        for n, ll, lh in zip(cn, lam_lo, lam_hi, strict=True):
            d = (
                d
                - n[:, 0:1] * (1.0 - lh) / np.maximum(1.0 - p * (1.0 - lh), 1e-300)
                + n[:, 1:2] / np.maximum(p, 1e-300)
                - n[:, 2:3] / np.maximum(1.0 - p, 1e-300)
                + n[:, 3:4] * (1.0 - lh) / np.maximum(p + (1.0 - p) * lh, 1e-300)
            )
        return d

    cap = np.full((s_rows, c), q0)
    at_cap = deriv(cap) >= 0.0
    lo = np.zeros((s_rows, c))
    hi = cap.copy()
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        up = deriv(mid) > 0.0
        lo = np.where(up, mid, lo)
        hi = np.where(up, hi, mid)
    p_star = np.where(at_cap, q0, 0.5 * (lo + hi))
    best = np.maximum(obj(p_star), obj(cap))
    out = best.max(axis=1) + EPS_SLACK
    return np.where(counts.sum(axis=(1, 2)) > 0, out, 0.0)


def lam_edges(lam_max: float, width: float = LAM_CELL_WIDTH) -> np.ndarray:
    n = max(1, int(np.ceil(lam_max / width)))
    return np.linspace(0.0, lam_max, n + 1)


# ------------------------------------------------------------------ (a) restricted gap-blind LR


class MarkovLRRestricted(MarkovLREProcess):
    """``MarkovLREProcess`` with the null supremum restricted to ``lambda in [0, lam_max]``."""

    def __init__(self, q0: float, alpha: float, n_labels: int, lam_max: float):
        super().__init__(q0, alpha, n_labels)
        self.lam_max = float(lam_max)
        self.edges = lam_edges(self.lam_max)

    @property
    def log_e_value(self) -> float:
        started = self.n > self.starts + 1
        if not started.any():
            return 0.0
        den = certified_sup_batch(self.cnt[started][:, None, :], [1], self.q0, self.edges)
        lm = logsumexp(self.num[started], axis=1) + self.log_k
        comp = np.zeros(len(self.starts))
        comp[started] = lm - den
        return float(logsumexp(comp + self.log_w))


class MLRRestrictedEvidence:
    """Harness wrapper: ``mlr_default8`` starts/alternatives, null restricted to ``rho <= rho_bar``."""

    def __init__(self, cfg, alpha, rho_bar: float):
        q0 = (1.0 + cfg.h) / 2.0
        cal = sorted(uniform_calendar(cfg.T, cfg.B, cfg.d))
        g_min = int(np.min(np.diff(cal))) if len(cal) > 1 else 1
        self.g_min, self.lam_max = g_min, float(rho_bar**g_min)
        self.ep = MarkovLRRestricted(q0, alpha, cfg.B, self.lam_max)
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


# ------------------------------------------------------------------ (b) UI e-detector, all starts


def gap_table(p: np.ndarray, rho: np.ndarray, g: int) -> np.ndarray:
    """log P^g(z | prev) for entries (prev,z) = 00, 01, 10, 11 at each theta; shape (n_theta, 4)."""
    lam = rho**g
    pr = np.stack(
        [
            1.0 - p * (1.0 - lam),
            p * (1.0 - lam),
            (1.0 - p) * (1.0 - lam),
            p + (1.0 - p) * lam,
        ],
        axis=1,
    )
    return np.log(np.clip(pr, 1e-300, 1.0))


class UIGapAllStarts:
    """Universal-inference all-starts e-detector with a predictable plug-in Markov alternative."""

    def __init__(
        self, q0: float, rho_bar: float, alpha: float, n_labels: int, k: int | None = None
    ):
        self.q0, self.alpha = float(q0), float(alpha)
        self.edges = gm.rho_cell_edges(rho_bar)
        k = max(1, n_labels // 50) if k is None else int(k)
        self.k = k
        self.starts = np.arange(0, max(1, n_labels), k)
        s = len(self.starts)
        pg, rg = np.meshgrid(UI_P_GRID, UI_RHO_GRID, indexing="ij")
        self.th_p, self.th_r = pg.ravel(), rg.ravel()
        self.counts = np.zeros((s, UI_MAX_GAP_CLASSES, 4))
        self.gaps: list[int] = []
        self.ltab: list[np.ndarray] = []
        self.prior_ll: np.ndarray | None = None
        self.th_idx = np.zeros(s, dtype=int)
        self.num = np.zeros(s)
        self.den = np.zeros(s)
        self.n_seen = 0
        self.prev = -1
        self.prev_ev = 0
        self._log_e = 0.0

    # --- helpers
    def _class(self, g: int) -> int:
        if g in self.gaps:
            return self.gaps.index(g)
        if len(self.gaps) >= UI_MAX_GAP_CLASSES:
            raise ValueError("too many distinct gaps")
        self.gaps.append(g)
        self.ltab.append(gap_table(self.th_p, self.th_r, g))
        if self.prior_ll is None:  # two pseudo-transitions at theta_0, first gap class
            p0, r0 = UI_THETA0
            lam = r0**g
            pseudo = np.array(
                [1 - p0 * (1 - lam), p0 * (1 - lam), (1 - p0) * (1 - lam), p0 + (1 - p0) * lam]
            )
            self.prior_ll = self.ltab[0] @ pseudo
            self.th_idx[:] = int(np.argmax(self.prior_ll))
        return len(self.gaps) - 1

    def predictive_p1(self, s_idx: int, g: int, prev: int) -> float:
        """Plug-in ``P(Z=1 | prev, gap g)`` of start ``s_idx`` (depends on past labels only)."""
        th = self.th_idx[s_idx]
        p, lam = self.th_p[th], self.th_r[th] ** g
        return float(p * (1.0 - lam) if prev == 0 else p + (1.0 - p) * lam)

    # --- API
    def update(self, ev: int, x: float) -> bool:
        z = 1 if x < 0 else 0
        if self.n_seen == 0:
            self.prev, self.prev_ev, self.n_seen = z, ev, 1
            return True
        g = ev - self.prev_ev
        c = self._class(g)
        m = int(np.searchsorted(self.starts, self.n_seen - 1, side="right"))
        if m > 0:
            th = self.th_idx[:m]
            lam = self.th_r[th] ** g
            pa = self.th_p[th]
            p1 = pa * (1.0 - lam) if self.prev == 0 else pa + (1.0 - pa) * lam
            self.num[:m] += np.log(p1 if z else 1.0 - p1)
            self.counts[:m, c, 2 * self.prev + z] += 1.0
            ng = len(self.gaps)
            ll = np.zeros((m, len(self.th_p)))
            for cc in range(ng):
                ll += self.counts[:m, cc, :] @ self.ltab[cc].T
            self.th_idx[:m] = np.argmax(ll + self.prior_ll[None, :], axis=1)
            self.den[:m] = certified_sup_batch(self.counts[:m, :ng], self.gaps, self.q0, self.edges)
            comp = np.zeros(len(self.starts))
            comp[:m] = self.num[:m] - self.den[:m]
            self._log_e = float(logsumexp(comp) - np.log(len(self.starts)))
        self.prev, self.prev_ev = z, ev
        self.n_seen += 1
        return True

    @property
    def log_e_value(self) -> float:
        return self._log_e

    @property
    def alarm(self) -> bool:
        return self._log_e >= -np.log(self.alpha)


class UIEvidence:
    """Harness wrapper around ``UIGapAllStarts`` (adds ``n_used``)."""

    def __init__(self, cfg, alpha, rho_bar: float, k: int | None = None):
        q0 = (1.0 + cfg.h) / 2.0
        self.ep = UIGapAllStarts(q0, rho_bar, alpha, cfg.B, k)
        self.n_used = 0

    def update(self, ev: int, x: float) -> bool:
        self.ep.update(ev, x)
        self.n_used += 1
        return True

    @property
    def log_e_value(self) -> float:
        return self.ep.log_e_value

    @property
    def alarm(self) -> bool:
        return self.ep.alarm


# ------------------------------------------------------------------ registry

MATCHED_RHO_BAR = 0.8
MATCHED_ARMS = ("exact0.8_s4", "mlr_default8", "mlr_rb0.8", "ui_gap_allstarts", "thin10_s4")
NEW_EVIDENCE = {
    "mlr_rb0.8": lambda c, a: MLRRestrictedEvidence(c, a, MATCHED_RHO_BAR),
    "ui_gap_allstarts": lambda c, a: UIEvidence(c, a, MATCHED_RHO_BAR),
}


def build_gate(name: str) -> gm.GapGate:
    if name in NEW_EVIDENCE:
        return gm.GapGate(name, NEW_EVIDENCE[name])
    return gm.build_gate(name)


__all__ = [
    "MATCHED_ARMS",
    "MLRRestrictedEvidence",
    "MarkovLRRestricted",
    "UIEvidence",
    "UIGapAllStarts",
    "build_gate",
    "certified_sup_batch",
    "lam_edges",
]
