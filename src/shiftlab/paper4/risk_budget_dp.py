"""Risk-budget dynamic programming (RB-DP) for the causal switching game, delay d = 1.

State before acting (not yet promoted): (t, beta, n, w) with beta = P(S_t = 1 | released labels),
n = remaining query budget, w = worst-case probability of ever promoting from here on.

Two grid programs are solved with the same Bellman step:

* "upper": every risk budget lives on the w grid; the extracted policy is evaluated *exactly* on
  its own forward tree (exact float beliefs), which certifies U >= V* independently of grid error.
* "lower": linear beta interpolation (V is concave in beta) plus optimistic rounding in w.

Decisions are not stored per grid cell. The executed policy re-runs the upper Bellman step at the
exact belief, against the stored next-stage grid tables, so the DP and the executed policy share
one code path.
"""

from __future__ import annotations

import math
import sys
import time
from dataclasses import dataclass
from typing import Any

import numpy as np

_KEY_DIGITS = 12


@dataclass(frozen=True)
class RBDPConfig:
    """Cell and grid parameters (floats; delay must be 1)."""

    T: int
    B: int
    t01: float
    t10: float
    e0: float
    e1: float
    prior1: float = 0.5
    c: float = 0.0
    k: float = 0.0
    alpha: float = 0.1
    n_beta: int = 401
    w_step_div: int = 20
    mode: str = "causal"
    delay: int = 1
    n_extra_max: int = 250
    reach_labels: int = 3
    reach_gap_cap: int = 6

    def __post_init__(self) -> None:
        if self.delay != 1:
            raise ValueError("RB-DP is implemented for delay d = 1 only")
        if self.mode not in ("causal", "iid"):
            raise ValueError("mode must be 'causal' or 'iid'")
        if self.T < 1 or not 0 <= self.B <= self.T:
            raise ValueError("require T >= 1 and 0 <= B <= T")
        if not 0 < self.e0 < 0.5 < self.e1 < 1:
            raise ValueError("emissions must straddle 1/2 and lie in (0,1)")
        if not (0 <= self.t01 <= 1 and 0 <= self.t10 <= 1 and 0 <= self.prior1 <= 1):
            raise ValueError("transition and prior probabilities must be in [0,1]")
        if not 0 < self.alpha <= 1 or self.c < 0 or self.k < 0:
            raise ValueError("require 0 < alpha <= 1 and nonnegative costs")
        if self.n_beta < 3 or self.w_step_div < 1:
            raise ValueError("n_beta >= 3 and w_step_div >= 1 required")

    @property
    def n_w(self) -> int:
        """Number of w-grid cells N (grid step 1/N, N = round(K / alpha) so that 1 is on the grid).

        If alpha * N is not an integer, alpha is not on the grid: the upper program starts at
        floor(alpha * N) and the lower program at ceil(alpha * N).
        """
        return max(1, round(self.w_step_div / self.alpha))


def _lower_hull(f: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Row-wise lower convex hull of points (j, f[:, j]).

    Returns hull values and, per j, the previous/next hull vertex indices (equal at vertices).
    The hull is the exact value of randomising between two budgets (risk is linear in mixing).
    """
    rows, width = f.shape
    r = np.arange(rows)
    stack = np.zeros((rows, width), dtype=np.int64)
    sp = np.zeros(rows, dtype=np.int64)
    for j in range(width):
        fj = f[:, j]
        while True:
            ok = sp >= 2
            if not ok.any():
                break
            ia = stack[r, np.maximum(sp - 2, 0)]
            im = stack[r, np.maximum(sp - 1, 0)]
            fa = f[r, ia]
            fm = f[r, im]
            pop = ok & ((fm - fa) * (j - ia) >= (fj - fa) * (im - ia))
            if not pop.any():
                break
            sp -= pop
        stack[r, sp] = j
        sp += 1
    idx = np.arange(width)[None, :]
    is_v = np.zeros((rows, width), dtype=bool)
    live = idx < sp[:, None]
    rr = np.broadcast_to(r[:, None], stack.shape)
    is_v[rr[live], stack[live]] = True
    pv = np.maximum.accumulate(np.where(is_v, idx, -1), axis=1)
    nv = np.minimum.accumulate(np.where(is_v, idx, width)[:, ::-1], axis=1)[:, ::-1]
    fpv = np.take_along_axis(f, pv, axis=1)
    fnv = np.take_along_axis(f, np.minimum(nv, width - 1), axis=1)
    span = np.maximum(nv - pv, 1)
    hull = np.where(pv == nv, fpv, fpv + (fnv - fpv) * (idx - pv) / span)
    return hull, pv, nv


class _Maps:
    """Belief maps for an array of beliefs: positive prob, label probs, next-belief interpolation."""

    __slots__ = ("b", "pos", "p0", "p1", "nq", "y0", "y1", "bn", "b0", "b1")

    def __init__(self, solver: _Solver, b: np.ndarray) -> None:
        cfg = solver.cfg
        self.b = b
        self.pos = cfg.e0 + (cfg.e1 - cfg.e0) * b
        self.p1 = self.pos
        self.p0 = 1.0 - self.pos
        prop = solver.propagate
        self.bn = prop(b)
        self.b1 = prop(b * cfg.e1 / self.p1)
        self.b0 = prop(b * (1.0 - cfg.e1) / self.p0)
        self.nq = solver.locate(self.bn)
        self.y0 = solver.locate(self.b0)
        self.y1 = solver.locate(self.b1)

    def slice(self, s: slice) -> _Maps:
        out = object.__new__(_Maps)
        for name in self.__slots__:
            val = getattr(self, name)
            setattr(out, name, (val[0][s], val[1][s]) if isinstance(val, tuple) else val[s])
        return out


def _lerp_rows(table: np.ndarray, loc: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    lo, wt = loc
    if table.ndim == 1:
        return table[lo] * (1.0 - wt) + table[lo + 1] * wt
    return table[lo] * (1.0 - wt)[:, None] + table[lo + 1] * wt[:, None]


class _Solver:
    def __init__(self, cfg: RBDPConfig) -> None:
        self.cfg = cfg
        self.N = cfg.n_w
        self.Nw = self.N + 1
        self.g = np.arange(self.Nw) / self.N
        self.beta1 = self.propagate(np.array([cfg.prior1]))[0]
        self.grid = self._build_beta_grid()
        self.G = len(self.grid)
        self.gmaps = _Maps(self, self.grid)
        self._build_w_tables()
        self.J: list[list[np.ndarray]] = []
        self.P: list[list[np.ndarray]] = []
        self.Vup: list[list[np.ndarray]] = []
        self.chunk = max(1, int(3e6 // (self.Nw * self.Nw)))

    # ---- beliefs --------------------------------------------------------------------------
    def propagate(self, b: np.ndarray) -> np.ndarray:
        cfg = self.cfg
        return cfg.t01 * (1.0 - b) + (1.0 - cfg.t10) * b

    def locate(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        grid = self.grid
        lo = np.clip(np.searchsorted(grid, x, side="right") - 1, 0, len(grid) - 2)
        wt = np.clip((x - grid[lo]) / (grid[lo + 1] - grid[lo]), 0.0, 1.0)
        return lo, wt

    def _reachable(self) -> list[float]:
        cfg = self.cfg
        e0, e1 = cfg.e0, cfg.e1
        found: list[tuple[float, float]] = []
        frontier = [(float(self.beta1), 1.0)]
        for _ in range(cfg.reach_labels):
            nxt: list[tuple[float, float]] = []
            for b, w in frontier:
                x = b
                for _gap in range(cfg.reach_gap_cap + 1):
                    found.append((x, w))
                    pos = e0 + (e1 - e0) * x
                    for p, post in ((1 - pos, x * (1 - e1) / (1 - pos)), (pos, x * e1 / pos)):
                        nxt.append((float(self.propagate(np.array([post]))[0]), w * p))
                    x = float(self.propagate(np.array([x]))[0])
            frontier = nxt
        found.extend(frontier)
        found.sort(key=lambda item: -item[1])
        return [b for b, _ in found]

    def _build_beta_grid(self) -> np.ndarray:
        cfg = self.cfg
        uniform = np.linspace(0.0, 1.0, cfg.n_beta)
        pts = [float(self.beta1)]
        tol = 1e-9
        taken = np.sort(np.concatenate([uniform, [self.beta1]]))
        extras: list[float] = []
        for b in pts + self._reachable():
            if len(extras) >= cfg.n_extra_max:
                break
            if not 0.0 <= b <= 1.0:
                continue
            j = np.searchsorted(taken, b)
            near = [taken[i] for i in (j - 1, j) if 0 <= i < len(taken)]
            if all(abs(b - v) > tol for v in near):
                taken = np.insert(taken, j, b)
                extras.append(b)
        # beta1 must be a grid point exactly
        if np.min(np.abs(taken - self.beta1)) > 0:
            taken = np.sort(np.append(taken, self.beta1))
        return taken

    # ---- w tables -------------------------------------------------------------------------
    def _build_w_tables(self) -> None:
        N, Nw = self.N, self.Nw
        j = np.arange(Nw)[:, None]
        self.split: dict[bool, tuple[np.ndarray, np.ndarray]] = {}
        for lower in (False, True):
            extra = 1 if lower else 0
            i = np.arange(Nw)[None, :]
            if self.cfg.mode == "causal":
                valid = i <= j
            else:
                valid = (2 * j + extra - i) >= 0
            i1 = np.clip(np.minimum(N, 2 * j + extra - i), 0, N)
            self.split[lower] = (i1, np.where(valid, 0.0, np.inf))

    # ---- post-promotion value J and promotion cost P --------------------------------------
    def _branch_values(
        self, n: int, mp: _Maps, Jnext: list[np.ndarray]
    ) -> list[list[np.ndarray | None]]:
        cfg = self.cfg
        out: list[list[np.ndarray | None]] = []
        for a2 in (0, 1):
            base = mp.pos if a2 == 0 else 1.0 - mp.pos
            row: list[np.ndarray | None] = []
            row.append(base + _lerp_rows(Jnext[n][a2], mp.nq))
            if n > 0:
                cont = mp.p0 * _lerp_rows(Jnext[n - 1][a2], mp.y0)
                cont = cont + mp.p1 * _lerp_rows(Jnext[n - 1][a2], mp.y1)
                row.append(base + cfg.c + cont)
            else:
                row.append(None)
            out.append(row)
        return out

    def _promote_cost(
        self, n: int, mp: _Maps, Jnext: list[np.ndarray]
    ) -> tuple[np.ndarray, np.ndarray]:
        br = self._branch_values(n, mp, Jnext)[1]
        v0, v1 = br
        if v1 is None:
            return self.cfg.k + v0, np.zeros(len(v0), dtype=bool)
        return self.cfg.k + np.minimum(v0, v1), v1 < v0

    def _build_post(self) -> None:
        cfg = self.cfg
        T, B = cfg.T, cfg.B
        zero = [np.zeros((2, self.G)) for _ in range(B + 1)]
        self.J = [[] for _ in range(T + 2)]
        self.P = [[] for _ in range(T + 2)]
        self.J[T + 1] = zero
        for t in range(T, 0, -1):
            Jn = self.J[t + 1]
            Jt: list[np.ndarray] = []
            Pt: list[np.ndarray] = []
            for n in range(B + 1):
                br = self._branch_values(n, self.gmaps, Jn)
                cand = np.full((2, 2, self.G), np.inf)  # [a_prev, a2]
                for a2 in (0, 1):
                    best = br[a2][0]
                    assert best is not None
                    if br[a2][1] is not None:
                        best = np.minimum(best, br[a2][1])
                    for a_prev in (0, 1):
                        cand[a_prev, a2] = best + cfg.k * (a2 != a_prev)
                Jt.append(cand.min(axis=1))
                Pt.append(self._promote_cost(n, self.gmaps, Jn)[0])
            self.J[t] = Jt
            self.P[t] = Pt

    # ---- pre-promotion Bellman step -------------------------------------------------------
    def _step(
        self,
        n: int,
        mp: _Maps,
        P: np.ndarray,
        Vn: np.ndarray,
        Vm: np.ndarray | None,
        lower: bool,
        decisions: bool = False,
    ) -> tuple[np.ndarray, dict[str, np.ndarray] | None]:
        cfg = self.cfg
        i1, pen = self.split[lower]
        Vnq = _lerp_rows(Vn, mp.nq)
        Qc = None
        w0arg = None
        if n > 0 and Vm is not None:
            V0 = _lerp_rows(Vm, mp.y0)
            V1 = _lerp_rows(Vm, mp.y1)
            val = mp.p0[:, None, None] * V0[:, None, :] + mp.p1[:, None, None] * V1[:, i1]
            val += pen
            Qc = cfg.c + val.min(axis=2)
            if decisions:
                w0arg = val.argmin(axis=2)
            cmin = np.minimum(Vnq, Qc)
        else:
            cmin = Vnq
        C = mp.pos[:, None] + cmin
        N = self.N
        f = np.empty_like(C)
        if lower:
            f[:, :N] = C[:, 1:]  # true C(w'') >= C_low(ceil(w'')): left endpoints of cells
        else:
            f[:, :N] = C[:, :N]
        f[:, N] = np.minimum(C[:, N], P)
        V, pv, nv = _lower_hull(f)
        dec = None
        if decisions:
            dec = {"pv": pv, "nv": nv, "promote_n": P < C[:, N]}
            if Qc is not None and w0arg is not None:
                dec["q"] = Qc < Vnq
                dec["w0"] = w0arg
        return V, dec

    def _run_dp(self, lower: bool) -> np.ndarray:
        cfg = self.cfg
        T, B = cfg.T, cfg.B
        Vnext = [np.zeros((self.G, self.Nw)) for _ in range(B + 1)]
        if not lower:
            self.Vup = [[] for _ in range(T + 2)]
            self.Vup[T + 1] = Vnext
        for t in range(T, 0, -1):
            Vcur: list[np.ndarray] = []
            for n in range(B + 1):
                out = np.empty((self.G, self.Nw))
                for a in range(0, self.G, self.chunk):
                    s = slice(a, min(self.G, a + self.chunk))
                    out[s], _ = self._step(
                        n,
                        self.gmaps.slice(s),
                        self.P[t][n][s],
                        Vnext[n],
                        Vnext[n - 1] if n else None,
                        lower,
                    )
                Vcur.append(out)
            Vnext = Vcur
            if not lower:
                self.Vup[t] = Vcur
        return Vnext[B]

    def root_value(self, V: np.ndarray, idx: int) -> float:
        loc = self.locate(np.array([self.beta1]))
        return float(_lerp_rows(V[:, idx : idx + 1], loc)[0, 0])

    def root_indices(self) -> tuple[int, int]:
        x = self.cfg.alpha * self.N
        return min(self.N, int(math.floor(x + 1e-9))), min(self.N, int(math.ceil(x - 1e-9)))

    def never_promote_cost(self) -> float:
        b = np.array([self.beta1])
        total = 0.0
        for _ in range(self.cfg.T):
            total += float(self.cfg.e0 + (self.cfg.e1 - self.cfg.e0) * b[0])
            b = self.propagate(b)
        return total


class _Evaluator:
    """Exact evaluation of the upper-DP policy on its own forward tree."""

    def __init__(self, solver: _Solver) -> None:
        self.s = solver
        self.cfg = solver.cfg
        self.dec_cache: dict[tuple[int, int, float], dict[str, Any]] = {}
        self.post_cache: dict[tuple[int, int, int, float], float] = {}
        self.pre_cache: dict[tuple[int, int, int, float], tuple[float, float, float]] = {}

    # post-promotion greedy policy on exact beliefs -------------------------------------------
    def _post_choice(self, t: int, a: int, n: int, mp: _Maps) -> tuple[int, int]:
        cfg = self.cfg
        s = self.s
        if t == cfg.T:
            vals = {}
            for a2 in (0, 1):
                vals[a2, 0] = (mp.pos[0] if a2 == 0 else 1 - mp.pos[0]) + cfg.k * (a2 != a)
            return min(vals, key=lambda key: vals[key])  # type: ignore[return-value]
        br = s._branch_values(n, mp, s.J[t + 1])
        best = None
        best_val = math.inf
        for a2 in (0, 1):
            for q in (0, 1):
                v = br[a2][q]
                if v is None:
                    continue
                val = float(v[0]) + cfg.k * (a2 != a)
                if val < best_val:
                    best_val, best = val, (a2, q)
        assert best is not None
        return best

    def post(self, t: int, a: int, n: int, b: float) -> float:
        cfg = self.cfg
        if t > cfg.T:
            return 0.0
        key = (t, a, n, round(b, _KEY_DIGITS))
        hit = self.post_cache.get(key)
        if hit is not None:
            return hit
        mp = _Maps(self.s, np.array([b]))
        a2, q = self._post_choice(t, a, n, mp)
        pos = float(mp.pos[0])
        val = (pos if a2 == 0 else 1.0 - pos) + cfg.c * q + cfg.k * (a2 != a)
        if t < cfg.T:
            if q:
                val += float(mp.p0[0]) * self.post(t + 1, a2, n - 1, float(mp.b0[0]))
                val += float(mp.p1[0]) * self.post(t + 1, a2, n - 1, float(mp.b1[0]))
            else:
                val += self.post(t + 1, a2, n, float(mp.bn[0]))
        self.post_cache[key] = val
        return val

    # pre-promotion ---------------------------------------------------------------------------
    def _decide(self, t: int, n: int, b: float) -> dict[str, Any]:
        key = (t, n, round(b, _KEY_DIGITS))
        hit = self.dec_cache.get(key)
        if hit is not None:
            return hit
        s = self.s
        mp = _Maps(s, np.array([b]))
        P, pq = s._promote_cost(n, mp, s.J[t + 1])
        _, dec = s._step(
            n,
            mp,
            P,
            s.Vup[t + 1][n],
            s.Vup[t + 1][n - 1] if n else None,
            False,
            decisions=True,
        )
        assert dec is not None
        out = {
            "mp": mp,
            "pq": bool(pq[0]),
            "pv": dec["pv"][0],
            "nv": dec["nv"][0],
            "promote_n": bool(dec["promote_n"][0]),
            "q": dec["q"][0] if "q" in dec else None,
            "w0": dec["w0"][0] if "w0" in dec else None,
        }
        self.dec_cache[key] = out
        return out

    def _promote_exact(self, t: int, n: int, dec: dict[str, Any]) -> float:
        cfg = self.cfg
        mp: _Maps = dec["mp"]
        q = 1 if dec["pq"] else 0
        val = cfg.k + 1.0 - float(mp.pos[0]) + cfg.c * q
        if t < cfg.T:
            if q:
                val += float(mp.p0[0]) * self.post(t + 1, 1, n - 1, float(mp.b0[0]))
                val += float(mp.p1[0]) * self.post(t + 1, 1, n - 1, float(mp.b1[0]))
            else:
                val += self.post(t + 1, 1, n, float(mp.bn[0]))
        return val

    def pre(self, t: int, n: int, j: int, b: float) -> tuple[float, float, float]:
        """Return (expected cost-to-go, worst-case causal risk, IID risk) of the executed policy.

        Budget j is realised by randomising between the two adjacent hull vertices; the risk of
        the mixture is the mixture of the vertex risks (exact if the null sees the coin,
        otherwise an upper bound on the true worst case).
        """
        if t > self.cfg.T:
            return 0.0, 0.0, 0.0
        key = (t, n, j, round(b, _KEY_DIGITS))
        hit = self.pre_cache.get(key)
        if hit is not None:
            return hit
        dec = self._decide(t, n, b)
        va, vb = int(dec["pv"][j]), int(dec["nv"][j])
        if va == vb:
            out = self._vertex(t, n, va, b, dec)
        else:
            lam = (j - va) / (vb - va)
            xa = self._vertex(t, n, va, b, dec)
            xb = self._vertex(t, n, vb, b, dec)
            out = tuple((1.0 - lam) * u + lam * v for u, v in zip(xa, xb, strict=True))
            out = (out[0], out[1], out[2])
        self.pre_cache[key] = out
        return out

    def _vertex(
        self, t: int, n: int, v: int, b: float, dec: dict[str, Any]
    ) -> tuple[float, float, float]:
        cfg = self.cfg
        N = self.s.N
        mp: _Maps = dec["mp"]
        if v == N and dec["promote_n"]:
            return self._promote_exact(t, n, dec), 1.0, 1.0
        pos = float(mp.pos[0])
        if dec["q"] is not None and bool(dec["q"][v]):
            i0 = int(dec["w0"][v])
            i1 = min(N, 2 * v - i0)
            p0, p1 = float(mp.p0[0]), float(mp.p1[0])
            c0, r0c, r0i = self.pre(t + 1, n - 1, i0, float(mp.b0[0]))
            c1, r1c, r1i = self.pre(t + 1, n - 1, i1, float(mp.b1[0]))
            cost = pos + cfg.c + p0 * c0 + p1 * c1
            return cost, max(r0c, 0.5 * (r0c + r1c)), 0.5 * (r0i + r1i)
        c0, r0c, r0i = self.pre(t + 1, n, v, float(mp.bn[0]))
        return pos + c0, r0c, r0i


def evaluate_policy(solver: _Solver) -> dict[str, float]:
    """Execute the stored upper-DP policy from the root and evaluate it exactly."""
    sys.setrecursionlimit(max(10_000, sys.getrecursionlimit()))
    ev = _Evaluator(solver)
    lo_idx, _ = solver.root_indices()
    cost, rc, ri = ev.pre(1, solver.cfg.B, lo_idx, float(solver.beta1))
    return {
        "cost_exact": cost,
        "risk_causal": rc,
        "risk_iid": ri,
        "n_pre_nodes": len(ev.pre_cache),
        "n_post_nodes": len(ev.post_cache),
    }


def solve(config: RBDPConfig) -> dict[str, Any]:
    """Solve a cell: certified-style sandwich ``L <= V* <= U`` for ``config.mode``."""
    t0 = time.perf_counter()
    solver = _Solver(config)
    t1 = time.perf_counter()
    solver._build_post()
    t2 = time.perf_counter()
    lower_tab = solver._run_dp(lower=True)
    t3 = time.perf_counter()
    solver._run_dp(lower=False)
    t4 = time.perf_counter()
    lo_idx, hi_idx = solver.root_indices()
    L = solver.root_value(lower_tab, hi_idx)
    dp_up = solver.root_value(solver.Vup[1][config.B], lo_idx)
    ev = evaluate_policy(solver)
    t5 = time.perf_counter()
    return {
        "L": L,
        "U": ev["cost_exact"],
        "dp_upper_value": dp_up,
        "risk_causal": ev["risk_causal"],
        "risk_iid": ev["risk_iid"],
        "C0": solver.never_promote_cost(),
        "mode": config.mode,
        "n_beta_grid": solver.G,
        "n_w": solver.Nw,
        "n_pre_nodes": ev["n_pre_nodes"],
        "n_post_nodes": ev["n_post_nodes"],
        "time_setup": t1 - t0,
        "time_post": t2 - t1,
        "time_lower": t3 - t2,
        "time_upper": t4 - t3,
        "time_eval": t5 - t4,
        "time_total": t5 - t0,
    }
