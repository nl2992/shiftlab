"""Gap-Mix+: evidence-adaptive query governor for Gap-Mix (methods-recovery, C3 development stage).

Registered in ``docs/methods_recovery/00_PREREG_GAPMIX_PLUS.md``.  Evidence engine, promotion rule,
econ check, rollback monitor and hard budget clamp are the unchanged GAVE-R shell
(``shiftlab.gaver.integrated.GaverMethod``).  Only the *pre-promotion request rule* is replaced.

Predictability / observation contract
-------------------------------------
The request at round ``t`` is a function of ``(t, cfg, own past requests, released labels, evidence
state built from released labels)``.  Nothing from ``Truth`` or from unreleased ``D`` is read.
``decide`` asserts that every released label satisfies ``event + d <= t`` (a *guard*: feeding it a
label from the future raises ``PredictabilityViolation``).  Pending labels are used only to count
the pipeline (``P_t``); they are never evidence.  Because query times are ``F_{t-1}``-predictable,
Gap-Mix's exact-gap null supermartingale argument applies as declared (rho_bar = 0.8); that is
checked empirically on the null grid, not assumed.

Derivation of the expected log-wealth gain per label at gap ``D``
-----------------------------------------------------------------
Gap-Mix (``gapmix.ExactGapStart``) multiplies, per new label at gap ``g`` after the previous
queried label with state ``z``, the factor

    N_t / sup_{theta in H0} L_t(theta),
    N_t = mean_k prod_i P_k^{g_i}(z_i' | z_i)  (alternative grid k = (p_k, rho_k)),
    L_t(theta) = prod_i P_theta^{g_i}(z_i' | z_i)

where the exact-gap kernel of the declared two-state chain with stationary favourable mass ``p``
and persistence ``rho`` is, with ``lam = rho**g``,

    P^g(1 | 0) = p (1 - lam),     P^g(1 | 1) = p + (1 - p) lam.

*Step 1 (plug-in alternative).*  The numerator is a mixture over the grid, whose posterior weights
are ``w_k propto exp(num_k)`` (``ExactGapStart.num``), computed from released labels only.  Under
alternative ``k`` the numerator log-likelihood grows by the expected one-step log-density
``E_k log P_k^g(z'|z)``.

*Step 2 (denominator).*  The denominator is the (certified upper bound of the) maximised null
likelihood.  For a long run of gap-``g`` labels generated under ``k`` the maximised null
log-likelihood grows at ``E_k log P_{theta*}^g`` with ``theta* = argmin_{theta in H0} KL``, so the
log-wealth per label converges to the Kullback-Leibler rate

    r_k(g) = min_{p <= q0, rho' in [0, rho_bar]}  sum_z pi_k(z)  KL( P_k^g(.|z) || P_{(p,rho')}^g(.|z) ),

with ``pi_k = (1 - p_k, p_k)`` the stationary law of ``k`` and ``q0 = (1 + h)/2``.  (Entries are
evaluated on a fine ``(p, rho')`` grid: a lower bound on the minimum is not needed because the rate
only ranks gaps and scales a threshold.)  The plug-in expected gain per label at gap ``D`` is

    r(D) = sum_k w_k r_k(min(D, G_MAX)).

``r`` is increasing in ``D`` and saturates at the iid rate: a label queried ``D`` rounds after the
previous query carries more new information the larger ``D`` is (the contraction ``rho**D`` of the
Markov dependence), which is exactly what a gap-blind governor ignores.  Labels in the pipeline are
scored at the same rate (approximation, documented).  The first label of a start carries no
evidence (conditioned on); it is always requested.

Decision rule (at most 3 free parameters ``theta = (kappa, phi, omega)``)
------------------------------------------------------------------------
Before promotion, with ``a = log(1/alpha_j)``, ``E_t = max(0, log E)`` the current Gap-Mix
log-evidence, ``need = a - E_t`` its distance to the promotion threshold, ``Delta_t = t - last
request``, ``B_t`` the remaining budget, ``P_t`` the pending count, ``H_t = T - d - t + 1`` and
``g_c = ceil(H_t / B_t)`` the budget-feasible calendar gap:

    need_eff = max(0, need - omega * P_t * r(Delta_t))          (pipeline credit)
    request  iff  r(Delta_t) >= kappa * need_eff / B_t          (rate >= required average per label)
              or  Delta_t >= phi * g_c                          (pacing floor)
    except    need_eff = 0 -> do not request (pipeline expected to finish);
              need <= 0    -> defer to the shell rule (alarm already up).

The request is also subject to the shell's spend-pace cap ``ceil(0.1 B) + floor(2 B t / T)``
(inherited, as in PAVE), ``used < B`` and ``t + d <= T``.  After promotion the unchanged shell rule
(DSS straddle / uniform calendar) monitors for reversal.

Ablation 4a (``mode="frozen"``): identical code and parameters, but the evidence terms are frozen
to their prior values: ``E_t = 0`` (so ``need = a``) and uniform alternative weights ``w_k``.
Everything else (``Delta_t``, ``B_t``, ``T - t``, ``P_t``, ``d``) is kept.

Arm 5 (``mode="pace"``): simple fixed pacing; request iff ``Delta_t >= G`` with ``G`` constant or
``G = max(1, round(f * ceil((T - d)/B)))``; same shell, cap, alarm deferral and post-promotion rule.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.special import logsumexp, xlogy

from shiftlab.dive import atlas_components as comp
from shiftlab.gaver import gapmix as gm
from shiftlab.gaver.integrated import RHO_BAR, GaverMethod

G_MAX = 64


class PredictabilityViolation(AssertionError):
    """A label that is not yet released at round ``t`` reached the governor."""


# ----------------------------------------------------------------------------- rate model


@lru_cache(maxsize=8)
def rate_table(q0: float, rho_bar: float) -> tuple[np.ndarray, np.ndarray]:
    """``(alts, rate)`` with ``rate[k, g-1] = r_k(g)`` in nats per label, ``g = 1..G_MAX``."""
    alts = np.array([(p, r) for p in gm.ALT_P for r in gm.ALT_RHO if p > q0])
    ps = np.linspace(0.02, q0, 40)
    rs = np.linspace(0.0, rho_bar, 33)
    pn, rn = np.meshgrid(ps, rs, indexing="ij")
    pn, rn = pn.ravel(), rn.ravel()
    rate = np.zeros((len(alts), G_MAX))
    for gi in range(G_MAX):
        g = gi + 1
        lam_n = rn**g
        qn = np.stack([pn * (1.0 - lam_n), pn + (1.0 - pn) * lam_n])  # Q(1|0), Q(1|1)
        for k, (pa, ra) in enumerate(alts):
            lam = ra**g
            pa1 = np.array([pa * (1.0 - lam), pa + (1.0 - pa) * lam])
            pi = np.array([1.0 - pa, pa])
            kl = np.zeros(len(pn))
            for s in (0, 1):
                kl += pi[s] * (
                    xlogy(pa1[s], pa1[s] / qn[s])
                    + xlogy(1.0 - pa1[s], (1.0 - pa1[s]) / (1.0 - qn[s]))
                )
            rate[k, gi] = float(kl.min())
    return alts, rate


def expected_gain(gap: int, weights: np.ndarray | None, q0: float, rho_bar: float) -> float:
    """Plug-in expected Gap-Mix log-wealth gain (nats) of one label at gap ``gap``."""
    _alts, rate = rate_table(q0, rho_bar)
    col = rate[:, min(max(int(gap), 1), G_MAX) - 1]
    if weights is None:
        return float(col.mean())
    return float(weights @ col)


# ----------------------------------------------------------------------------- QSG-envelope evidence


def _load_qsg():
    d = Path(__file__).resolve().parents[3] / "scripts" / "failure_atlas_v2_flq"
    if str(d) not in sys.path:
        sys.path.insert(0, str(d))
    import qsg

    return qsg


class QSGEvidence:
    """QSG-envelope evidence (``qsg.EnvelopeMixture``) in the DSS shell, null level moved to q0.

    ``qsg.EnvelopeMixture`` tests ``p <= 1/2``; the harness hurdle null is ``p <= q0 = (1+h)/2``.
    The only change is ``u = q0 + (1-q0) rho_bar**g`` after a favourable outcome and ``q0``
    otherwise (components with ``p' <= u`` are neutral).  QSG's own acquisition (front-loading) and
    rollback are *not* used: this is the evidence process only.
    """

    def __init__(self, method, alpha: float):
        qsg = _load_qsg()
        cfg = method.cfg
        self.method, self.alpha = method, alpha
        q0 = (1.0 + cfg.h) / 2.0
        rho_bar = method.rho_bar

        class _Env(qsg.EnvelopeMixture):
            def update_at(self, z, t):
                self.k += 1
                w = 1.0 / (self.k * (self.k + 1))
                u = q0
                if self.prev is not None and self.prev[0] == 1:
                    u = q0 + (1.0 - q0) * rho_bar ** max(t - self.prev[1], 1)
                lr = np.ones_like(self.grid)
                act = self.grid > u
                g = self.grid[act]
                lr[act] = (g / u) if z else ((1.0 - g) / (1.0 - u))
                self.S = (self.S + w) * lr
                self.prev = (z, t)
                return self.value

        self.inner = _Env(+1, rho_bar)

    def update(self, x: float) -> None:
        ev = self.method._evq.popleft()
        self.inner.update_at(1 if x < 0 else 0, ev)

    @property
    def log_e_value(self) -> float:
        return float(np.log(max(self.inner.value, 1e-300)))

    @property
    def proc(self):
        return self

    @property
    def alarm(self) -> bool:
        return self.inner.value >= 1.0 / self.alpha


class QSGMethod(GaverMethod):
    """DSS shell + QSG-envelope evidence + the existing (DSS) acquisition."""

    def __init__(self, rho_bar: float = RHO_BAR):
        super().__init__("env", "dss", rho_bar)
        self.evidence, self.name = "qsg", "gmp:qsg:dss"

    def _new_episode(self, j: int, start: int) -> None:
        comp.ComposedMethod._new_episode(self, j, start)
        self.ep = QSGEvidence(self, self._alpha_j(j))


# ----------------------------------------------------------------------------- the governor


@dataclass(frozen=True)
class GMParams:
    """Free parameters of Gap-Mix+ (``kappa, phi, omega``) or of fixed pacing (``gap`` / ``frac``)."""

    kappa: float = 1.0
    phi: float = 1.0
    omega: float = 1.0
    gap: int | None = None  # Arm 5: constant gap ...
    frac: float | None = None  # ... or fraction of the initial calendar gap ceil((T-d)/B)

    def key(self) -> str:
        if self.gap is not None or self.frac is not None:
            return f"G{self.gap}" if self.gap is not None else f"f{self.frac:g}"
        return f"k{self.kappa:g}_p{self.phi:g}_w{self.omega:g}"


MODES = ("plus", "frozen", "pace")
EVIDENCES_OK = ("gapmix", "mlr")


class GapMixPlusMethod(GaverMethod):
    """Gap-Mix (or Markov-LR) evidence in the GAVE-R shell with the Gap-Mix+ pre-promotion governor."""

    def __init__(
        self,
        evidence: str = "gapmix",
        mode: str = "plus",
        params: GMParams | None = None,
        rho_bar: float = RHO_BAR,
    ):
        if mode not in MODES or evidence not in EVIDENCES_OK:
            raise ValueError((evidence, mode))
        super().__init__(evidence, "dss", rho_bar)
        self.mode, self.gp = mode, params or GMParams()
        self.name = f"gmp:{evidence}:{mode}:{self.gp.key()}"
        self.audit: list[dict] = []
        self.keep_audit = False

    # -- shell hooks ---------------------------------------------------------------------
    def _init(self) -> None:
        super()._init()
        self.pave_on = False
        self._uni0, self._cal0 = self.dss_uniform, self.cal  # shell's own post-promotion rule
        self.dss_uniform, self.cal = False, frozenset()

    def decide(self, t: int, released):
        for ev, _ in released:  # predictability guard
            if ev + self.cfg.d > t:
                raise PredictabilityViolation(f"label of event {ev} not released at t={t}")
        return super().decide(t, released)

    # -- evidence terms (the only part ablation 4a freezes) ------------------------------
    def evidence_terms(self) -> tuple[float, np.ndarray | None]:
        """``(E_t, alt weights)`` from released labels; the prior ``(0, None)`` for mode ``frozen``."""
        if self.mode == "frozen":
            return 0.0, None
        if self.evidence == "mlr":
            return max(0.0, float(self.ep.proc.log_e_value)), None
        inner = self.ep.inner
        e_t = max(0.0, float(inner.log_e_value))
        best, bl = None, -math.inf
        for st in inner.starts:
            if st.prev is not None and st.log_e > bl:
                best, bl = st, st.log_e
        if best is None:
            return e_t, None
        w = np.exp(best.num - logsumexp(best.num))
        return e_t, w

    # -- request rule --------------------------------------------------------------------
    def _shell(self, t: int) -> bool:
        self.dss_uniform, self.cal = self._uni0, self._cal0
        try:
            return comp.ComposedMethod._query(self, t)
        finally:
            self.dss_uniform, self.cal = False, frozenset()

    def _query(self, t: int) -> bool:
        c = self.cfg
        if self.act == 1:  # deployed: unchanged shell monitoring rule
            return self._shell(t)
        if self.burst_left > 0 and len(self.pending_events) < 2 and self.can_query(t):
            self.burst_left -= 1
            return True
        if not self.can_query(t):
            return False
        cap = max(1, math.ceil(self._p("acquisition", "burst_frac") * c.B)) + math.floor(
            2 * c.B * t / c.T
        )
        if self.used >= cap:
            return False
        if self.used == 0:
            return True
        delta = t - self.last_query
        a = -math.log(self._alpha_j(self.j))
        if self.mode != "frozen" and self.ep.alarm:  # evidence already above threshold
            return self._shell(t)
        if self.mode == "pace":
            if self.ep.alarm:
                return self._shell(t)
            g0 = math.ceil((c.T - c.d) / max(c.B, 1))
            gp = self.gp.gap if self.gp.gap is not None else max(1, round(self.gp.frac * g0))
            return delta >= gp
        b_rem = c.B - self.used
        h_rem = max(1, c.T - c.d - t + 1)
        g_c = max(1, math.ceil(h_rem / b_rem))
        e_t, w = self.evidence_terms()
        need = a - e_t
        if need <= 0:
            return self._shell(t)
        q0 = (1.0 + c.h) / 2.0
        r = expected_gain(delta, w, q0, self.rho_bar)
        need_eff = max(0.0, need - self.gp.omega * len(self.pending_events) * r)
        if need_eff <= 0.0:
            go = False
        else:
            go = bool(r >= self.gp.kappa * need_eff / b_rem or delta >= self.gp.phi * g_c)
        if self.keep_audit:
            self.audit.append(
                {"t": t, "r": r, "need": need, "need_eff": need_eff, "delta": delta, "go": go}
            )
        return go


def build(name: str, params: dict | None = None):
    """``gmp:<evidence>:<mode>`` -> method (``gmp:qsg:dss`` -> QSG-envelope evidence)."""
    _, ev, mode = name.split(":")[:3]
    if ev == "qsg":
        return QSGMethod()
    return GapMixPlusMethod(ev, mode, GMParams(**(params or {})))


__all__ = [
    "GMParams",
    "GapMixPlusMethod",
    "PredictabilityViolation",
    "QSGMethod",
    "build",
    "expected_gain",
    "rate_table",
]
