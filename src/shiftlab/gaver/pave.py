"""PAVE: pending-aware value-of-label governor (GAVE-R WP2).

PAVE replaces only the *request rule* of the frozen cycle-7 DSS candidate (spec ``5b5c77b635e5``).
Evidence engine, promotion rule and rollback monitor are inherited unchanged from
``atlas_components.ComposedMethod``; this class overrides ``_query``.

Observation contract (inherits the harness contract in docs/gaver/01_HARNESS_MAP.md)
-----------------------------------------------------------------------------------
* The request at round t is a deterministic function of ``F_t``: t, config (T, B, d, c, s, h, alpha),
  own past requests, released labels, evidence state.  No ``Truth``/onset/duration/rho/effect.
* Pending labels are counted (number and age) for acquisition only; they are never evidence.
* Budget is charged at request; ``Method.step`` still clamps ``used < B`` and ``t + d <= T``.

Working model (fixed before evaluation; two scalars kappa and q tuned on development streams)
-----------------------------------------------------------------------------------------
The benefit of the candidate over the incumbent, ``mu = E[-D]`` in [-1, 1], has a Normal belief
with mean ``n*ben/(n+n0)`` (``ben`` = the engine's own recent-window mean; ``n0`` pseudo-labels of
prior mean 0) and variance ``sigma^2/(min(n, m)+n0)``, ``sigma^2 = max(0.05, 1-mean^2)``.  The
belief drifts: its variance grows by ``q`` per round (staleness) and every label arriving at round
``a`` applies a Kalman update.  Acting on the belief at round ``s`` has expected opportunity loss
``sqrt(V) * L(|m-theta_s|/sqrt(V))``, ``L(z)=phi(z)-z(1-Phi(z))``, against the threshold
``theta_s = h + s_cost/R_s`` (undeployed: switch iff mu exceeds it) or ``h - s_cost/R_s``
(deployed), with ``R_s = T-s+1``.  Before promotion the regret is multiplied by the reachability
``clip(inc*(rollout labels + pending + released)/log-wealth-needed, 0, 1)`` (``inc`` a frozen
per-label log-wealth rate), because a label can only matter if the e-process can still reach
``1/alpha_j``.  This is a heuristic value model with no validity role: validity rests on the
unchanged evidence engine and on the request being a predictable function of ``F_t``.

Governor.  A rollout is a first request after ``shift`` rounds, then labels on a calendar of gap
``g_f`` until the effective budget runs out; ``g_f`` is the current calendar gap
``g = ceil(H/B_rem)`` or a burst gap ``g//4`` (best of the two is used).  Its value is minus the
regret summed over the remaining rounds (coarse round grid) minus ``c`` per label.  Candidates are
shifts ``0, g, 2g``.  Request iff ``V_0 - max(V_1, V_2) > kappa * (V_0 - V_none)/K_0`` (the gain
from requesting now exceeds ``kappa`` times the average value of a label; ``V_none`` is the
no-more-labels rollout), pending capacity allows it, and the DSS spend-pace cap
``ceil(0.1B) + floor(2Bt/T)`` is respected (inherited unchanged, so this is a *when within pace*
rule, not an unconstrained spender).

Switchable parts (WP2.4 factorial):
* ``pending``: on = pending labels enter the sample size of the posterior (their information is
  coming) and capacity is ``ceil(d*B_rem/H_rem)`` instead of the fixed 2.
* ``deadline``: on = value uses the post-arrival horizon ``R = T-a+1``; off = ``R = T-t+1``
  (delay and calendar shifts do not cost value), so the rollout candidates tie except for
  pacing/budget.
* ``reserve``: on = a frozen ``reserve_frac`` of B is withheld before promotion and released
  once the candidate is deployed (rollback monitoring).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.special import erfc as _erfc

from shiftlab.dive import atlas_components as comp

N0 = 2.0  # prior pseudo-labels (frozen)
INC = 0.1  # per-label log-wealth rate for reachability (frozen)
SQ2PI = math.sqrt(2.0 * math.pi)


def _phi(z: np.ndarray) -> np.ndarray:
    return np.exp(-0.5 * z * z) / SQ2PI


def _sf(z: np.ndarray) -> np.ndarray:
    return 0.5 * _erfc(z / math.sqrt(2.0))


@dataclass(frozen=True)
class PaveParams:
    pending: bool = True
    deadline: bool = True
    reserve: bool = True
    kappa: float = 0.05
    reserve_frac: float = 0.2
    q: float = 0.002
    burst: bool = True


class PaveMethod(comp.ComposedMethod):
    """DSS evidence/decision engine (unchanged) with the PAVE request governor."""

    def __init__(self, params: PaveParams | None = None):
        super().__init__(comp.dss_spec(4, True))
        self.pp = params or PaveParams()
        self.name = (
            f"pave_p{int(self.pp.pending)}d{int(self.pp.deadline)}r{int(self.pp.reserve)}"
            f"_k{self.pp.kappa:g}"
        )
        self.audit: list[dict] = []
        self.keep_audit = False

    def _init(self) -> None:
        super()._init()
        self.dss_uniform = False  # the governor owns the request rule in every cell
        self.cal = frozenset()
        self.reserve_n = math.ceil(self.pp.reserve_frac * self.cfg.B) if self.pp.reserve else 0

    # ------------------------------------------------------------------ helpers
    def _b_eff(self) -> int:
        rem = self.cfg.B - self.used
        if self.act == 0:
            rem -= self.reserve_n
        return max(0, rem)

    def pending_capacity(self, t: int) -> int:
        if not self.pp.pending:
            return int(self._p("acquisition", "pending_cap"))
        h_rem = max(1, self.cfg.T - self.cfg.d - t + 1)
        return max(1, math.ceil(self.cfg.d * max(0, self.cfg.B - self.used) / h_rem))

    def _posterior(self) -> tuple[float, int, float]:
        xs = self.ep_labels if self.act == 0 else self.post
        ben = self._ben(xs, self.m)
        n = len(xs)
        m = 0.0 if ben is None else n * float(ben) / (n + N0)
        return m, n, max(0.05, 1.0 - m * m)

    def _rollout(
        self, t: int, shift: int, g: int, b_eff: int, m, n_obs, sigma2, none: bool = False
    ) -> tuple[float, int]:
        """Value of a rollout = -(expected decision regret summed over rounds t+1..T) - c*K.

        Regret per round under posterior variance V is ``sqrt(V) * L(|m-theta|/sqrt(V))``
        (expected opportunity loss of acting on the current belief).  V grows by ``q`` per round
        (drift) and is cut by each label at its arrival; labels follow a calendar of gap ``g``.
        """
        c = self.cfg
        h_rem = c.T - c.d - t - shift
        if h_rem < 0:
            return -math.inf, 0
        k_max = min(b_eff, h_rem // g + 1)
        if k_max <= 0 and not none:
            return -math.inf, 0
        k_max = max(k_max, 1) if not none else 0
        dl = c.d if self.pp.deadline else 0
        arrive = t + shift + np.arange(max(k_max, 1)) * g + dl
        if none:
            arrive = np.array([10**9])
        n_pend = len(self.pending_events) if self.pp.pending else 0
        e_last = max(self.labels[-1][0] if self.labels else 0, self.ep_start)
        if self.act == 1:
            e_last = max(e_last, self.promo_t)
        if n_pend:  # their information arrives before the rollout's first label
            e_last = max(e_last, max(self.pending_events) + c.d)
        q = self.pp.q
        v_base = sigma2 / (min(n_obs + n_pend, self.m) + N0)
        stride = max(1, (c.T - t) // 150)  # coarse round grid for speed; weights below
        s_idx = np.arange(t + 1, c.T + 1, stride)
        # variance process: last update time and its post-update variance
        qg = q * g
        v_ss = 0.5 * (qg + math.sqrt(qg * qg + 4.0 * qg * sigma2))
        v_ss_post = v_ss * sigma2 / (v_ss + sigma2)
        a0 = int(arrive[0])
        v_pre0 = v_base + q * max(0, a0 - e_last)
        v_post0 = v_pre0 * sigma2 / (v_pre0 + sigma2)
        idx = np.searchsorted(arrive, s_idx, side="right") - 1  # last arrival <= s
        t_since = np.where(idx >= 0, s_idx - arrive[np.maximum(idx, 0)], s_idx - e_last)
        base = np.where(idx < 0, v_base, np.where(idx == 0, v_post0, v_ss_post))
        V = np.maximum(base + q * np.maximum(t_since, 0), 1e-9)
        R_s = (c.T - s_idx + 1) if self.pp.deadline else np.full(len(s_idx), c.T - t + 1)
        sign = 1.0 if self.act == 0 else -1.0
        theta = c.h + sign * c.s / np.maximum(R_s, 1)
        sd = np.sqrt(V)
        z = np.abs(m - theta) / sd
        rho = sd * (_phi(z) - z * _sf(z))
        scale = 1.0
        if self.act == 0 and not none:
            need = max(0.0, math.log(1.0 / self._alpha_j(self.j)) - self._logE())
            if need > 0:
                scale = float(np.clip(INC * (k_max + n_pend + n_obs) / need, 0.0, 1.0))
        regret = float(np.sum(rho)) * stride * scale
        return -regret - c.c * k_max, k_max

    def _logE(self) -> float:
        proc = getattr(self.ep, "proc", None)
        try:
            return max(0.0, float(proc.log_e_value))
        except Exception:  # noqa: BLE001 - heuristic input only
            return 0.0

    # ------------------------------------------------------------------ governor
    def _query(self, t: int) -> bool:
        c = self.cfg
        if self.burst_left > 0 and len(self.pending_events) < 2 and self.can_query(t):
            self.burst_left -= 1
            return True
        if not self.can_query(t):
            return False
        if len(self.pending_events) >= self.pending_capacity(t):
            return False
        b_eff = self._b_eff()
        if b_eff <= 0:
            return False
        cap = max(1, math.ceil(self._p("acquisition", "burst_frac") * c.B)) + math.floor(
            2 * c.B * t / c.T
        )
        if self.used >= cap:  # spend-pace cap inherited unchanged from DSS
            return False
        h_rem = max(1, c.T - c.d - t + 1)
        g = max(1, math.ceil(h_rem / b_eff))
        m, n_obs, sigma2 = self._posterior()
        # follow-up spacing options after the first request: current calendar gap or a burst
        gs = (g, max(1, g // 4)) if self.pp.burst else (g,)

        def best(shift: int) -> tuple[float, int]:
            return max(self._rollout(t, shift, gf, b_eff, m, n_obs, sigma2) for gf in gs)

        v0, k0 = best(0)
        v1, _ = best(g)
        v2, _ = best(2 * g)
        gain = v0 - max(v1, v2)
        v_none, _ = self._rollout(t, 0, g, b_eff, m, n_obs, sigma2, none=True)
        lam = self.pp.kappa * max(v0 - v_none, 0.0) / max(k0, 1)  # avg value of a label
        go = bool(k0 > 0 and gain > lam)  # V_j already net of c per label
        if self.keep_audit:
            self.audit.append(
                {
                    "t": t,
                    "v0": v0,
                    "v1": v1,
                    "v2": v2,
                    "gain": gain,
                    "lam": lam,
                    "go": go,
                    "used": self.used,
                    "pending": len(self.pending_events),
                    "act": self.act,
                }
            )
        return go
