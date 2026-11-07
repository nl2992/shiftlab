"""COMMON_CONTRACT_PORT core for ASI: a streaming, delayed-label IPW monitor with a betting confidence sequence.

STATUS: ASI-inspired port, NOT a result of Zrnic & Candes (2024). What is from the papers and what is ours:

From ASI (arXiv 2403.03208): the increment Delta_t = f_t(X_t) + (Y_t - f_t(X_t)) xi_t / pi_t(X_t) with f_t, pi_t
F_{t-1}-measurable has E[Delta_t | F_{t-1}] = E[Y_t | F_{t-1}] (Sec 6); App. C says that for bounded increments
with a common conditional mean "betting-based methods" (Waudby-Smith & Ramdas, Orabona & Jun) give non-asymptotic
CIs / time-uniform CSs, and that bounded increments follow from pi_t >= pi_min > 0 (their mixing with the uniform rule).

From Waudby-Smith & Ramdas (arXiv 2010.09686, Thm 2 / Eqs. 13-15, read): the predictable plug-in empirical-Bernstein
process M_t(m) = exp( sum_i lam_i (X_i - m) - v_i psi_E(lam_i) ), v_i = 4 (X_i - muhat_{i-1})^2,
psi_E(l) = (-log(1-l) - l)/4, lam_t = min( sqrt(2 log(2/alpha) / (sig2_{t-1} t log(1+t))), c ), X_i in [0,1],
is a test supermartingale when E[X_i | past] = m, and the two-sided CS is sum lam_i X_i / sum lam_i +- (log(2/alpha) + sum v_i psi_E(lam_i)) / sum lam_i.

OURS (derived here, not stated in either paper; validated only by Monte Carlo in tests/d2a_rar/test_asi.py):
  * one-sided use: if E[X_i | past] <= m for all i (a CONDITIONAL null), M_t(m) is still a nonnegative supermartingale
    (the Fan-et-al. inequality behind WSR Thm 2 needs only E[X_i - m | past] <= 0 for lam_i >= 0), so rejecting when
    M_t(m) >= 1/alpha is an anytime-valid level-alpha test of H0_cond: E[d_t | past] <= h;
  * the affine rescaling of Delta_t into [0, 1] using bounds implied by pi_min;
  * in-order consumption of increments under label delay (an increment is used only when rounds <= t are resolved).
Assumptions needed: d_t in [d_lo, d_hi]; pi_t >= pi_min fixed (logged) at request time; xi_t drawn from the declared
propensity independently of d_t given the past; f_t, pi_t depend only on information released before the request.
Non-stationary drift: the CS is for a CONSTANT conditional mean; under drift only the one-sided conditional-null test
(m = hurdle) keeps its meaning. The rescaling makes the evidence conservative: increments span a range ~ 1/pi_min.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def psi_e(lam: float) -> float:
    return (-math.log1p(-lam) - lam) / 4.0


class PrPlEB:
    """Predictable plug-in empirical-Bernstein betting process for [0,1] observations (WSR 2010.09686, Thm 2)."""

    def __init__(self, alpha: float, c: float = 0.5) -> None:
        self.alpha, self.c = alpha, c
        self.t = 0
        self.s_x = 0.0  # sum x_i
        self.s_sq = 0.0  # sum (x_i - muhat_i)^2
        self.mu_prev, self.sig2_prev = 0.5, 0.25  # muhat_0, sigma2hat_0
        self.sum_lam = 0.0
        self.sum_lam_x = 0.0
        self.sum_vpsi = 0.0
        self.lams: list[float] = []
        self.xs: list[float] = []

    def next_lambda(self) -> float:
        t = self.t + 1
        return min(
            math.sqrt(2.0 * math.log(2.0 / self.alpha) / (self.sig2_prev * t * math.log1p(t))),
            self.c,
        )

    def update(self, x: float) -> None:
        if not -1e-12 <= x <= 1 + 1e-12:
            raise ValueError(f"observation {x} outside [0,1]; rescale first")
        lam = self.next_lambda()
        v = 4.0 * (x - self.mu_prev) ** 2
        self.sum_lam += lam
        self.sum_lam_x += lam * x
        self.sum_vpsi += v * psi_e(lam)
        self.lams.append(lam)
        self.xs.append(x)
        self.t += 1
        self.s_x += x
        self.mu_prev = (0.5 + self.s_x) / (self.t + 1)
        self.s_sq += (x - self.mu_prev) ** 2
        self.sig2_prev = (0.25 + self.s_sq) / (self.t + 1)

    def log_m(self, m: float) -> float:
        """log M_t(m) = sum lam_i (x_i - m) - sum v_i psi_E(lam_i)."""
        return self.sum_lam_x - m * self.sum_lam - self.sum_vpsi

    def cs(self) -> tuple[float, float]:
        """Two-sided (1 - alpha) time-uniform CS for the common conditional mean (WSR Thm 2), intersected with [0,1]."""
        if self.sum_lam == 0:
            return 0.0, 1.0
        mid = self.sum_lam_x / self.sum_lam
        w = (math.log(2.0 / self.alpha) + self.sum_vpsi) / self.sum_lam
        return max(0.0, mid - w), min(1.0, mid + w)


@dataclass
class StreamingASI:
    """Delayed-label IPW monitor. Round-indexed protocol:

    ``register(t, f, pi, queried)`` at request time (f_t and pi_t are frozen here);
    ``resolve(t, d)`` when the label of round t is released (queried rounds only);
    increments are consumed in round order once all earlier rounds are resolved.
    The target d_t must lie in [d_lo, d_hi]. ``hurdle`` is the null value h of H0_cond: E[d_t | past] <= h.
    """

    d_lo: float
    d_hi: float
    pi_min: float
    alpha: float = 0.05
    hurdle: float = 0.0
    c: float = 0.5
    proc: PrPlEB = field(init=False)
    _reg: dict = field(default_factory=dict, init=False)
    _next: int = field(default=1, init=False)
    n_consumed: int = field(default=0, init=False)
    max_log_evidence: float = field(default=-math.inf, init=False)

    def __post_init__(self) -> None:
        w = self.d_hi - self.d_lo
        self.lo = self.d_hi - w / self.pi_min  # smallest possible IPW increment
        self.hi = self.d_lo + w / self.pi_min  # largest
        self.proc = PrPlEB(self.alpha, self.c)

    def _scale(self, x: float) -> float:
        return (x - self.lo) / (self.hi - self.lo)

    def register(self, t: int, f: float, pi: float, queried: bool) -> None:
        if pi < self.pi_min - 1e-12 or pi > 1.0:
            raise ValueError(f"pi={pi} violates pi_min={self.pi_min}")
        f = min(max(f, self.d_lo), self.d_hi)
        self._reg[t] = [
            f,
            pi,
            queried,
            None if queried else f,
        ]  # unqueried: Delta_t = f_t immediately
        self._advance()

    def resolve(self, t: int, d: float) -> None:
        f, pi, queried, _ = self._reg[t]
        if not queried:
            raise ValueError("round was not queried")
        d = min(max(d, self.d_lo), self.d_hi)
        self._reg[t][3] = f + (d - f) / pi
        self._advance()

    def _advance(self) -> None:
        while self._next in self._reg and self._reg[self._next][3] is not None:
            delta = self._reg.pop(self._next)[3]
            self.proc.update(min(max(self._scale(delta), 0.0), 1.0))
            self._next += 1
            self.n_consumed += 1
            self.max_log_evidence = max(self.max_log_evidence, self.log_evidence())

    # ---- readouts (all in the original d-scale)
    def estimate(self) -> float:
        if self.proc.sum_lam == 0:
            return float("nan")
        return self.lo + (self.hi - self.lo) * self.proc.sum_lam_x / self.proc.sum_lam

    def log_evidence(self) -> float:
        """log M_t(h) for H0_cond: E[d_t | past] <= h (valid one-sided, see module docstring)."""
        return self.proc.log_m(self._scale(self.hurdle))

    def alarm(self) -> bool:
        """Ever-crossed (Ville): once M_t(h) >= 1/alpha the alarm stays on; level alpha under H0_cond."""
        return self.max_log_evidence >= math.log(1.0 / self.alpha)

    def cs(self) -> tuple[float, float]:
        a, b = self.proc.cs()
        return self.lo + (self.hi - self.lo) * a, self.lo + (self.hi - self.lo) * b
