"""Algorithm 1 of Sethi et al., "Asymptotically Optimal Sequential Testing with Markovian Data" (ICML 2026, PMLR 306).

PAPER_RECONSTRUCTION from the PDF (main text + App. B.3, B.5, G). No third-party code was run or copied.

Exact quantities (Alg. 1 lines 14-18; Lemma B.6):
    beta_t = sum_x log( e * (1 + N_x/(m-1)) )
    eps_t  = log(1/alpha) + (m-1) * beta_t
    L_t    = inf_{P in null} sum_{x: N_x>0} N_x KL( Qhat_t(x,.) || P(x,.) )
    reject at the first t with L_t >= eps_t.
alpha-correctness (Thm 4.1, Lemma B.6): for every P in the null and every initial law, with respect to the
natural filtration of (X_0, X_1, ...) observed at EVERY step. Nothing here covers missing / irregular /
informatively sampled observations, nor any statement about loss or harm.

Implementation choices NOT in the paper (each is conservative or a pure speed-up):
* The inner infimum is bounded through its Lagrangian dual, so any dual-feasible point is a valid LOWER bound
  L_lo <= L_t. We reject only if L_lo >= eps_t: an inexact solver can delay rejection, never inflate the
  false-alarm rate. A feasible null kernel gives an upper bound U_t >= L_t; if U_t < eps_t the solver is skipped.
* ``check_every`` evaluates the stopping rule on a subset of times: still alpha-correct, only delays rejection.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.optimize import minimize


def beta_t(counts_x: np.ndarray, m: int) -> float:
    """beta_t = sum_x log(e (1 + N_x/(m-1)))  (Alg. 1 line 14)."""
    return float(np.sum(1.0 + np.log1p(np.asarray(counts_x, float) / (m - 1))))


def boundary(counts_x: np.ndarray, m: int, alpha: float) -> float:
    """eps_t = log(1/alpha) + (m-1) beta_t  (Alg. 1 line 15)."""
    return math.log(1.0 / alpha) + (m - 1) * beta_t(counts_x, m)


def _kl_rows_sum(N: np.ndarray, P: np.ndarray) -> float:
    """sum_x N_x KL(Qhat_x || P_x) = sum_xy N_xy log(Qhat_xy / P_xy), with 0 log 0 = 0."""
    Nx = N.sum(1, keepdims=True)
    q = N / np.where(Nx > 0, Nx, 1.0)
    pos = N > 0
    return float(np.sum(N[pos] * (np.log(q[pos]) - np.log(np.maximum(P[pos], 1e-300)))))


class NullClass:
    """A declared compact null set of transition matrices.

    ``bounds(N, eps)`` returns (lower, upper) with lower <= inf_P sum N_xy log(Qhat_xy/P_xy) <= upper.
    If upper < eps the implementation may return a trivial lower bound (rejection impossible)."""

    def bounds(
        self, N: np.ndarray, eps: float = math.inf
    ) -> tuple[float, float]:  # pragma: no cover
        raise NotImplementedError


@dataclass
class StationaryNull(NullClass):
    """{P : rows stochastic, pi P = pi}: kernels leaving a target law invariant (the paper's MCMC use, Sec 5.1)."""

    pi: np.ndarray

    def __post_init__(self) -> None:
        self.pi = np.asarray(self.pi, float)
        self.pi = self.pi / self.pi.sum()
        if (self.pi <= 0).any():
            raise ValueError("pi must be strictly positive")

    def bounds(self, N: np.ndarray, eps: float = math.inf) -> tuple[float, float]:
        m = len(self.pi)
        upper = _kl_rows_sum(N, np.tile(self.pi, (m, 1)))  # P = 1 pi^T is feasible
        if upper < eps:
            return 0.0, upper
        return min(self._dual(N), upper), upper

    def _dual(self, N: np.ndarray) -> float:
        """Lagrangian dual lower bound.

        Primal: min -sum N_xy log P_xy  s.t. sum_y P_xy = 1, sum_x pi_x P_xy = pi_y.
        Dual: a_xy = mu_x + pi_x lam_y (> 0 where N_xy > 0, >= 0 elsewhere),
              g = sum_{N>0} (N - N log(N/a)) - sum mu - sum lam pi;  inf L >= sum N log Qhat + g.
        """
        m, pi = len(self.pi), self.pi
        Nx = N.sum(1)
        pos = N > 0
        q = N / np.where(Nx[:, None] > 0, Nx[:, None], 1.0)
        const = float(np.sum(N[pos] * np.log(q[pos])))
        logN = np.zeros_like(N)
        logN[pos] = np.log(N[pos])

        def unpack(z):
            return z[:m], np.append(z[m:], 0.0)  # lam_m fixed to 0 (gauge freedom)

        def a_of(z):
            mu, lam = unpack(z)
            return mu[:, None] + pi[:, None] * lam[None, :]

        def negg(z):
            a = a_of(z)
            if (a[pos] <= 1e-12).any():
                return 1e12
            mu, lam = unpack(z)
            g = np.sum(N[pos] - N[pos] * (logN[pos] - np.log(a[pos]))) - mu.sum() - lam @ pi
            return -float(g)

        def grad(z):
            a = a_of(z)
            r = np.where(pos, N / np.maximum(a, 1e-12), 0.0)
            return -np.concatenate([r.sum(1) - 1.0, ((pi[:, None] * r).sum(0) - pi)[:-1]])

        z0 = np.concatenate([np.where(Nx > 0, Nx, 1.0), np.zeros(m - 1)])
        A = np.zeros((m * m, 2 * m - 1))
        for x in range(m):
            for y in range(m):
                A[x * m + y, x] = 1.0
                if y < m - 1:
                    A[x * m + y, m + y] = pi[x]
        cons = [{"type": "ineq", "fun": lambda z: A @ z - 1e-9, "jac": lambda z: A}]
        best = -negg(z0)  # z0 is dual feasible (a = N_x > 0 on rows with data)
        try:
            res = minimize(
                negg,
                z0,
                jac=grad,
                constraints=cons,
                method="SLSQP",
                options={"maxiter": 200, "ftol": 1e-10},
            )
            if (A @ res.x >= 1e-12).all():
                best = max(best, -negg(res.x))
        except Exception:  # noqa: BLE001, S110 - a solver failure only delays rejection
            pass
        return const + best


@dataclass
class ConvexHullNull(NullClass):
    """{ sum_k w_k P_k : w in simplex } for declared kernels P_k. Frank-Wolfe with a duality-gap lower bound."""

    kernels: list

    def __post_init__(self) -> None:
        self.K = np.stack([np.asarray(k, float) for k in self.kernels])

    def bounds(self, N: np.ndarray, eps: float = math.inf, iters: int = 300) -> tuple[float, float]:
        K = len(self.K)
        w = np.full(K, 1.0 / K)
        lo, up = -math.inf, math.inf
        for k in range(iters):
            P = np.tensordot(w, self.K, 1)
            f = _kl_rows_sum(N, P)
            up = min(up, f)
            if up < eps:
                return 0.0, up
            G = np.where(N > 0, -N / np.maximum(P, 1e-300), 0.0)
            g = np.array([np.sum(G * self.K[j]) for j in range(K)])
            j = int(np.argmin(g))
            gap = float(g @ w - g[j])  # f(w) - f* <= gap by convexity
            lo = max(lo, f - gap)
            if lo >= eps or gap < 1e-9:
                break
            e = np.zeros(K)
            e[j] = 1.0
            w = (1 - 2.0 / (k + 2.0)) * w + (2.0 / (k + 2.0)) * e
        return max(lo, 0.0), up


@dataclass
class FiniteUnionNull(NullClass):
    """Finite union of convex components: inf = min over components (paper Sec 4.1)."""

    components: list

    def bounds(self, N: np.ndarray, eps: float = math.inf) -> tuple[float, float]:
        bs = [c.bounds(N, eps) for c in self.components]
        return min(b[0] for b in bs), min(b[1] for b in bs)


@dataclass
class SequentialMarkovTest:
    """Streaming Algorithm 1. ``update(x)`` consumes the next state of a finite chain observed at every step."""

    m: int
    alpha: float
    null: NullClass
    check_every: int = 1
    N: np.ndarray = field(init=False)
    prev: int | None = field(init=False, default=None)
    t: int = field(init=False, default=0)
    rejected_at: int | None = field(init=False, default=None)
    last_lower: float = field(init=False, default=0.0)
    last_eps: float = field(init=False, default=math.inf)

    def __post_init__(self) -> None:
        self.N = np.zeros((self.m, self.m))

    def update(self, x: int) -> bool:
        """Observe X_t = x (the first call is X_0). Returns True once H0 has been rejected."""
        if self.rejected_at is not None:
            return True
        if self.prev is None:
            self.prev = int(x)
            return False
        self.t += 1
        self.N[self.prev, int(x)] += 1
        self.prev = int(x)
        if self.t % self.check_every:
            return False
        eps = boundary(self.N.sum(1), self.m, self.alpha)
        lo, _ = self.null.bounds(self.N, eps)
        self.last_lower, self.last_eps = lo, eps
        if lo >= eps:
            self.rejected_at = self.t
            return True
        return False

    def log_evidence(self) -> float:
        """log M_t = L_lo - (m-1) beta_t at the last check (Remark 4.2: M_t is bounded by a nonnegative
        supermartingale, i.e. an e-process; the dual lower bound keeps this conservative).
        Rejection is equivalent to log_evidence >= log(1/alpha)."""
        return self.last_lower - (self.last_eps - math.log(1.0 / self.alpha))
