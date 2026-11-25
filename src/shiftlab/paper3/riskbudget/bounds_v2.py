"""Lemma 1' (exact coin mixture), spec 03F section 6.2.

For x in [-1, 1] and coin q ~ Bernoulli(pi): E exp(lam x (1 - q/pi)) is convex in x, hence at most
exp(psi(lam, pi)) with
    psi = ln max( pi e^{-lam(1/pi-1)} + (1-pi) e^{lam},  pi e^{lam(1/pi-1)} + (1-pi) e^{-lam} ).
exp(lam M_t - Psi_t(lam)) is then a supermartingale, and a union over a small lam grid gives, with
probability >= 1 - delta for all t, M_t <= D_t = min_lam [ln(m/delta) + Psi_t(lam)] / lam.

Two pathwise facts are added (both keep the bound valid): M_t <= sum_s max(1, 1/pi_s - 1) always
(xi_s <= 1 if x_s > 0 and xi_s <= 1/pi_s - 1 if x_s < 0), so D_t is capped by that sum; this
removes the ln(m/delta) overhead when only a handful of sampled rounds have been added.
"""

from __future__ import annotations

import numpy as np

V_TARGETS = (4.0, 16.0, 64.0, 256.0, 1024.0)


class CoinMixture:
    def __init__(
        self,
        delta: float,
        lams=None,
        lam_max: float = 2.0,
        use_cap: bool = True,
        v_targets=None,
        scale: float = 1.0,
        mix_m: int | None = None,
    ):
        if not 0.0 < delta < 1.0:
            raise ValueError("delta must be in (0, 1)")
        self.delta, self.use_cap = float(delta), use_cap
        self.scale = float(scale)  # DIAGNOSTIC ONLY: scale != 1 voids the guarantee
        if lams is None:
            vt = np.asarray(V_TARGETS if v_targets is None else v_targets, float)
            L = np.log(len(vt) / delta)
            lams = np.minimum(np.sqrt(2.0 * L / vt), lam_max)
        self.mix_m = mix_m
        if mix_m:  # dense log-grid, exact method of mixtures (sum, not max): valid by Ville on the averaged supermartingale
            vt = np.geomspace(2.0, 4096.0, int(mix_m))
            lams = np.minimum(np.sqrt(2.0 * np.log(mix_m / delta) / vt), lam_max)
        self.lams = np.asarray(lams, float)
        if np.any(self.lams <= 0):
            raise ValueError("lams must be positive")
        self._c = np.log(len(self.lams) / delta) / self.lams
        self.Psi = np.zeros(len(self.lams))
        self.cap = 0.0

    # ------------------------------------------------------------------ pieces
    def psi(self, pi: float) -> np.ndarray:
        """Vector psi(lam_j, pi) via log-sum-exp (zero at pi = 1)."""
        if not 0.0 < pi <= 1.0:
            raise ValueError("pi must be in (0, 1]")
        if pi >= 1.0:
            return np.zeros(len(self.lams))
        lp, lq, r = np.log(pi), np.log1p(-pi), 1.0 / pi - 1.0
        a1 = np.logaddexp(lp - self.lams * r, lq + self.lams)
        a2 = np.logaddexp(lp + self.lams * r, lq - self.lams)
        return np.maximum(np.maximum(a1, a2), 0.0)

    @staticmethod
    def cap_of(pi: float) -> float:
        return 0.0 if pi >= 1.0 else max(1.0, 1.0 / pi - 1.0)

    def add(self, pi: float) -> None:
        self.Psi = self.Psi + self.psi(pi)
        self.cap += self.cap_of(pi)

    def reset(self) -> None:
        self.Psi = np.zeros(len(self.lams))
        self.cap = 0.0

    # ------------------------------------------------------------------ width
    def D_with(self, extra_psi=None, extra_cap: float | None = None) -> float:
        """Width if ``extra_psi`` (a psi vector, e.g. of rounds about to be settled) were added.

        ``extra_cap`` is the matching pathwise cap; if omitted and extra_psi is nonzero the cap is
        dropped (conservative: larger D)."""
        P = self.Psi if extra_psi is None else self.Psi + np.asarray(extra_psi, float)
        if not np.any(P > 0.0):
            return 0.0
        d = float(np.min(self._c + P / self.lams))
        if self.mix_m:
            d = self._solve_mixture(P, d)
        if self.use_cap:
            if extra_psi is not None and np.any(np.asarray(extra_psi) > 0) and extra_cap is None:
                return d * self.scale
            d = min(d, self.cap + (extra_cap or 0.0))
        return d * self.scale

    def _solve_mixture(self, P, hi: float) -> float:
        """Smallest d with (1/m) sum_j exp(lam_j d - P_j) >= 1/delta (<= the union bound ``hi``)."""
        target = -np.log(self.delta)
        lo = 0.0
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            v = np.logaddexp.reduce(self.lams * mid - P) - np.log(len(self.lams))
            if v >= target:
                hi = mid
            else:
                lo = mid
        return hi

    def D(self) -> float:
        return self.D_with()

    def D_mix(self) -> float:
        """Mixture width without the pathwise cap (for width comparisons)."""
        if not np.any(self.Psi > 0.0):
            return 0.0
        return float(np.min(self._c + self.Psi / self.lams))
