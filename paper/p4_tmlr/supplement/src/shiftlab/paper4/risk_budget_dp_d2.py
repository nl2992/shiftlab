"""Risk-budget DP (RB-DP) for the causal switching game with label delay d = 2.

Implements ``docs/paper4_continuation/rbdp/DELAY2.md`` (risk recursion section 2, Bellman equations
section 3) and certifies every result by exact evaluation of the extracted policy.

Timing (matches ``shiftlab.dive.causal_switching_game`` with delay 2). At decision time t the labels
queried at times <= t - 2 have been released. A label queried at t - 1 (if any) is *pending*: the
null knows it, the learner does not. A query at t asks for Y_t.

Belief-indexing convention (the part DELAY2.md leaves loose):

* No-pending state A(t, beta, n, w): ``beta = P(S_t = 1 | released labels)`` (belief about the
  CURRENT state), n = remaining queries, scalar risk budget w.
* Pending state B(t, mu, n, w0, w1): ``mu = P(S_{t-1} = 1 | released labels)`` (belief about the
  state at the time the pending label Y_{t-1} was queried). The pending label has
  P(Y_{t-1} = 1) = pos(mu); the step cost at t is pos(prop(mu)) (the learner does not know it).
  ``post(mu, z)`` is the Bayes update of S_{t-1} on Y_{t-1} = z, ``prop`` one transition step.
* Transitions. A, no query  -> A(t+1, prop(beta)).         A, query -> B(t+1, mu = beta).
  B, label z, no query -> A(t+1, prop(prop(post(mu, z)))).  B, label z, query -> B(t+1, prop(post(mu, z))).
  (After the label z is released the successor's lagged belief is propagated by the number of steps
  needed to reach S_t resp. S_{t-1}.)
* Risk. Budget pair (w0, w1) = (R(h, z=0), R(h, z=1)). With weights (pi, 1-pi-kq, kq) on
  promote / no-query / query: R(h, z) = pi + wN * R(A-child after z) + wQ * m(R(B-child after z, y=0),
  R(B-child after z, y=1)); the learner's pi, kappa are common to both z. At a no-pending state the
  query child is the pending node B(t+1, beta) and R = pi + wN R(A child) + wQ m(a, b) with
  (a, b) = that node's budget pair.

Grids. Uniform risk grid with step 1/N, N = round(K / alpha); all budgets live on it. Beliefs: either
the exactly reachable set (``belief_grid="reach"``: no interpolation error at all, used when the
reachable set is small) or a uniform grid with linear interpolation in belief (``"uniform"``).

Pending value tables are lower convex hulls over the 2-D grid of min(no-query, query) together with the
promote point (1, 1). The hull is computed with Qhull on the 3-D point cloud (after dropping points that
are not strict vertices of their row/column hull), values are max over the lower-facet planes. A node
policy is read from the facet containing the node's budget (barycentric weights); vertices tagged
promote / no-query / query are merged by tag (budgets averaged, which keeps risk <= budget because m is
convex and cost <= table value because the tables are convex), so each node is a behavioural mixture of
three actions and the risk recursion needs no assumption on what the null sees of private coins.

The executed policy is evaluated exactly on its own forward tree with exact float beliefs
(``cost_exact``, ``risk_causal``, ``risk_iid``); this, not the DP value, certifies the result.
Queries are only allowed at t <= T - 2 (a label queried later is never released in time).
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

import numpy as np
from scipy.spatial import ConvexHull, Delaunay

try:  # scipy >= 1.12 exposes QhullError at top level
    from scipy.spatial import QhullError
except ImportError:  # pragma: no cover
    from scipy.spatial.qhull import QhullError  # type: ignore[no-redef]

_KEY_DIGITS = 11
_SNAP = 1e-10
_EPS = 1e-14


@dataclass(frozen=True)
class RBDP2Config:
    """Cell and grid parameters (floats; delay must be 2)."""

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
    w_step_div: int = 2  # K: N = round(K / alpha)
    n_w_override: int | None = None
    mode: str = "causal"
    delay: int = 2
    belief_grid: str = "auto"  # "auto" | "reach" | "uniform"
    n_beta: int = 101
    max_reach_states: int = 4000
    table_dir: str | None = None  # if set, pending-state tables are kept in .npy files there (memory-mapped)

    def __post_init__(self) -> None:
        if self.delay != 2:
            raise ValueError("this solver is for delay d = 2 only")
        if self.mode not in ("causal", "iid"):
            raise ValueError("mode must be 'causal' or 'iid'")
        if self.T < 1 or not 0 <= self.B <= self.T:
            raise ValueError("require T >= 1 and 0 <= B <= T")
        if not 0 < self.e0 < 0.5 < self.e1 < 1:
            raise ValueError("emissions must straddle 1/2 and lie in (0,1)")
        if not 0 < self.alpha <= 1 or self.c < 0 or self.k < 0:
            raise ValueError("require 0 < alpha <= 1 and nonnegative costs")
        if self.belief_grid not in ("auto", "reach", "uniform"):
            raise ValueError("belief_grid must be auto, reach or uniform")

    @property
    def n_w(self) -> int:
        if self.n_w_override:
            return int(self.n_w_override)
        return max(1, round(self.w_step_div / self.alpha))


# ---- 1-D lower hull (copied from the d = 1 solver, kept independent of it) ------------------


def _vertices_prune(f: np.ndarray) -> np.ndarray:
    rows, width = f.shape
    size = rows * width
    ff = f.reshape(-1)
    prv = np.arange(size, dtype=np.int64) - 1
    nxt = np.arange(size, dtype=np.int64) + 1
    alive = np.ones(size, dtype=bool)
    d = np.diff(f, axis=1)
    bad = np.zeros((rows, width), dtype=bool)
    bad[:, 1:-1] = d[:, :-1] >= d[:, 1:]
    cand = np.flatnonzero(bad.reshape(-1))
    tok = np.zeros(size, dtype=np.int64)
    while cand.size:
        pc = prv[cand]
        qc = nxt[cand]
        col = cand % width
        colp = pc % width
        colq = qc % width
        drop = cand[(ff[cand] - ff[pc]) * (colq - colp) >= (ff[qc] - ff[pc]) * (col - colp)]
        if drop.size == 0:
            break
        alive[drop] = False
        starts = np.sort(drop[alive[prv[drop]]])
        ends = np.sort(drop[alive[nxt[drop]]])
        left = prv[starts]
        right = nxt[ends]
        nxt[left] = right
        prv[right] = left
        near = np.concatenate([left, right])
        tok[near] = np.arange(near.size)
        near = near[tok[near] == np.arange(near.size)]
        cand = near[(near % width != 0) & (near % width != width - 1)]
    return alive.reshape(rows, width)


def _vertices_march(f: np.ndarray, max_steps: int = 48) -> np.ndarray:
    """Strict lower-hull vertex mask per row (gift wrapping, prune fallback)."""
    rows, width = f.shape
    idx = np.arange(width)
    is_v = np.zeros((rows, width), dtype=bool)
    is_v[:, 0] = True
    cur = np.zeros(rows, dtype=np.int64)
    act = np.arange(rows)
    for _ in range(max_steps):
        if act.size == 0:
            return is_v
        c = cur[act]
        fa = f[act]
        fc = fa[np.arange(act.size), c]
        sl = (fa - fc[:, None]) / np.maximum(idx[None, :] - c[:, None], 1)
        sl[idx[None, :] <= c[:, None]] = np.inf
        nx = width - 1 - np.argmin(sl[:, ::-1], axis=1)
        is_v[act, nx] = True
        cur[act] = nx
        act = act[nx < width - 1]
    if act.size:
        is_v[act] = _vertices_prune(f[act])
    return is_v


def _lower_hull(f: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Row-wise lower convex hull of (j, f[:, j]): values and the strict-vertex mask."""
    rows, width = f.shape
    idx = np.arange(width)[None, :]
    is_v = _vertices_march(f)
    pv = np.maximum.accumulate(np.where(is_v, idx, -1), axis=1)
    nv = np.minimum.accumulate(np.where(is_v, idx, width)[:, ::-1], axis=1)[:, ::-1]
    fpv = np.take_along_axis(f, pv, axis=1)
    fnv = np.take_along_axis(f, np.minimum(nv, width - 1), axis=1)
    span = np.maximum(nv - pv, 1)
    hull = np.where(pv == nv, fpv, fpv + (fnv - fpv) * (idx - pv) / span)
    return hull, is_v


# ---- 2-D lower hull ------------------------------------------------------------------------


def _hull2(f: np.ndarray) -> SimpleNamespace:
    """Lower convex hull of the grid function f[i0, i1] (square, (N+1) x (N+1)).

    Returns ``table`` (hull values at every grid point), vertex coordinates ``pts`` (V, 2) in grid
    units, vertex values ``vals`` and the lower facets ``fac`` (F, 3) indexing ``pts``.
    """
    nw = f.shape[0]
    n = nw - 1
    keep = _vertices_march(f) & _vertices_march(f.T).T
    ii, jj = np.nonzero(keep)
    vals = f[ii, jj]
    pts = np.column_stack([ii, jj]).astype(float)
    a_ = (f[n, 0] - f[0, 0]) / n
    b_ = (f[0, n] - f[0, 0]) / n
    plane = f[0, 0] + a_ * ii + b_ * jj
    if np.max(np.abs(vals - plane)) < 1e-11:
        fac = Delaunay(pts).simplices
    else:
        cloud = np.column_stack([ii / n, jj / n, vals])
        try:
            hull = ConvexHull(cloud)
        except QhullError:
            hull = ConvexHull(cloud, qhull_options="QJ")
        fac = hull.simplices[hull.equations[:, 2] < -1e-12]
    p = pts[fac]
    v = vals[fac]
    mat = np.concatenate([p, np.ones((len(fac), 3, 1))], axis=2)
    det = np.linalg.det(mat)
    good = np.abs(det) > 1e-9
    fac, p, v, mat = fac[good], p[good], v[good], mat[good]
    coef = np.linalg.solve(mat, v[:, :, None])[:, :, 0]  # f = A i0 + B i1 + C
    grid_i, grid_j = np.meshgrid(np.arange(nw), np.arange(nw), indexing="ij")
    gi, gj = grid_i.ravel().astype(float), grid_j.ravel().astype(float)
    table = np.full(gi.shape, -np.inf)
    chunk = max(1, int(2e6 // gi.size))
    for s in range(0, len(coef), chunk):
        cc = coef[s : s + chunk]
        table = np.maximum(table, (cc[:, 0:1] * gi + cc[:, 1:2] * gj + cc[:, 2:3]).max(axis=0))
    table = np.minimum(table.reshape(nw, nw), f)
    return SimpleNamespace(table=table, pts=pts, vals=vals, fac=fac)


def _locate_facet(pts: np.ndarray, fac: np.ndarray, x0: float, x1: float) -> tuple[np.ndarray, np.ndarray]:
    """Vertex indices and barycentric weights of the facet containing (x0, x1)."""
    tri = pts[fac]
    v0 = tri[:, 0]
    d1 = tri[:, 1] - v0
    d2 = tri[:, 2] - v0
    det = d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]
    safe = np.where(np.abs(det) < 1e-12, 1.0, det)
    rx = x0 - v0[:, 0]
    ry = x1 - v0[:, 1]
    l1 = (rx * d2[:, 1] - ry * d2[:, 0]) / safe
    l2 = (d1[:, 0] * ry - d1[:, 1] * rx) / safe
    lam = np.stack([1.0 - l1 - l2, l1, l2], axis=1)
    score = np.where(np.abs(det) < 1e-12, -np.inf, lam.min(axis=1))
    best = int(np.argmax(score))
    w = np.clip(lam[best], 0.0, None)
    return fac[best], w / w.sum()


# ---- solver --------------------------------------------------------------------------------


def _lerp(table: np.ndarray, rm: np.ndarray, loc: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
    lo, wt = loc
    r0 = rm[lo]
    r1 = rm[lo + 1]
    r1 = np.where(wt == 0.0, r0, r1)
    r0 = np.where(wt == 1.0, r1, r0)
    if (r0 < 0).any() or (r1 < 0).any():
        raise RuntimeError("belief outside the active set (use belief_grid='uniform')")
    w = wt.reshape((-1,) + (1,) * (table.ndim - 1))
    return table[r0] * (1.0 - w) + table[r1] * w


def _key(b: float) -> float:
    return round(float(b), _KEY_DIGITS)


class _Solver:
    def __init__(self, cfg: RBDP2Config) -> None:
        self.cfg = cfg
        self.T, self.B = cfg.T, cfg.B
        self.N = cfg.n_w
        self.Nw = self.N + 1
        self.beta1 = float(self.prop(np.array([cfg.prior1]))[0])
        self._build_beliefs()
        self.VA: dict[tuple[int, int], np.ndarray] = {}
        self.VB: dict[tuple[int, int], np.ndarray] = {}
        self.GA: dict[tuple[int, int, int], np.ndarray] = {}
        self.GB: dict[tuple[int, int, int], np.ndarray] = {}
        self.n_hull2 = 0

    # ---- belief maps ----------------------------------------------------------------------
    def prop(self, b: np.ndarray) -> np.ndarray:
        c = self.cfg
        return c.t01 * (1.0 - b) + (1.0 - c.t10) * b

    def pos(self, b: np.ndarray) -> np.ndarray:
        c = self.cfg
        return c.e0 + (c.e1 - c.e0) * b

    def post(self, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Bayes update on label 0 and label 1 (same time index)."""
        c = self.cfg
        p1 = self.pos(b)
        return b * (1.0 - c.e1) / (1.0 - p1), b * c.e1 / p1

    def qok(self, t: int, n: int) -> bool:
        return n > 0 and t <= self.T - 2

    def _succ(self, typ: int, t: int, n: int, b: float) -> list[tuple[int, int, float]]:
        out: list[tuple[int, int, float]] = []
        arr = np.array([b])
        if typ == 0:
            out.append((0, n, float(self.prop(arr)[0])))
            if self.qok(t, n):
                out.append((1, n - 1, b))
        else:
            for z in self.post(arr):
                pp = self.prop(z)
                out.append((0, n, float(self.prop(pp)[0])))
                if self.qok(t, n):
                    out.append((1, n - 1, float(pp[0])))
        return out

    def _build_beliefs(self) -> None:
        cfg, T, B = self.cfg, self.T, self.B
        levels: list[dict[tuple[int, int], dict[float, float]]] = [dict() for _ in range(T + 2)]
        levels[1][(0, B)] = {_key(self.beta1): self.beta1}
        total = 1
        reach_ok = cfg.belief_grid != "uniform"
        for t in range(1, T):
            if not reach_ok:
                break
            for (typ, n), d in levels[t].items():
                for b in d.values():
                    for typ2, n2, b2 in self._succ(typ, t, n, b):
                        slot = levels[t + 1].setdefault((typ2, n2), {})
                        if _key(b2) not in slot:
                            slot[_key(b2)] = b2
                            total += 1
            if cfg.belief_grid == "auto" and total > cfg.max_reach_states:
                reach_ok = False
        self.mode_reach = reach_ok
        T1 = T + 1
        if reach_ok:
            reps: dict[float, float] = {0.0: 0.0, 1.0: 1.0}
            for lev in levels:
                for d in lev.values():
                    reps.update({k: v for k, v in d.items() if k not in reps})
            grid = np.array(sorted(reps.values()))
            self.grid = grid
            gidx = {_key(v): i for i, v in enumerate(grid)}
            self.rm = [[[np.full(len(grid), -1, dtype=np.int64) for _ in range(self.B + 1)] for _ in range(2)] for _ in range(T1 + 1)]
            self.rows = [[[np.zeros(0, dtype=np.int64) for _ in range(self.B + 1)] for _ in range(2)] for _ in range(T1 + 1)]
            for t in range(1, T + 1):
                for (typ, n), d in levels[t].items():
                    idx = np.array(sorted(gidx[k] for k in d), dtype=np.int64)
                    self.rows[t][typ][n] = idx
                    self.rm[t][typ][n][idx] = np.arange(len(idx))
        else:
            grid = np.unique(np.concatenate([np.linspace(0.0, 1.0, cfg.n_beta), [self.beta1]]))
            self.grid = grid
            ident = np.arange(len(grid), dtype=np.int64)
            self.rm = [[[ident for _ in range(self.B + 1)] for _ in range(2)] for _ in range(T1 + 1)]
            self.rows = [[[ident for _ in range(self.B + 1)] for _ in range(2)] for _ in range(T1 + 1)]
        self.G = len(self.grid)

    def locate(self, x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        g = self.grid
        lo = np.clip(np.searchsorted(g, x, side="right") - 1, 0, len(g) - 2)
        wt = np.clip((x - g[lo]) / (g[lo + 1] - g[lo]), 0.0, 1.0)
        wt = np.where(np.abs(x - g[lo]) < _SNAP, 0.0, np.where(np.abs(x - g[lo + 1]) < _SNAP, 1.0, wt))
        return lo, wt

    def mapsA(self, b: np.ndarray) -> SimpleNamespace:
        pos = self.pos(b)
        return SimpleNamespace(b=b, pos=pos, loc_prop=self.locate(self.prop(b)), loc_self=self.locate(b))

    def mapsB(self, mu: np.ndarray) -> SimpleNamespace:
        p1 = self.pos(mu)
        post0, post1 = self.post(mu)
        pp = [self.prop(post0), self.prop(post1)]
        pp2 = [self.prop(pp[0]), self.prop(pp[1])]
        return SimpleNamespace(
            mu=mu,
            p=[1.0 - p1, p1],
            posprop=self.pos(self.prop(mu)),
            loc_pp=[self.locate(x) for x in pp],
            loc_pp2=[self.locate(x) for x in pp2],
            pp=pp,
            pp2=pp2,
        )

    # ---- table access (zero beyond the horizon) -------------------------------------------
    def _VA(self, t: int, n: int, loc: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
        if t > self.T:
            return np.zeros((len(loc[0]), self.Nw))
        return _lerp(self.VA[t, n], self.rm[t][0][n], loc)

    def _VB(self, t: int, n: int, loc: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
        return _lerp(self.VB[t, n], self.rm[t][1][n], loc)

    def _GA(self, t: int, a: int, n: int, loc: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
        if t > self.T:
            return np.zeros(len(loc[0]))
        return _lerp(self.GA[t, a, n], self.rm[t][0][n], loc)

    def _GB(self, t: int, a: int, n: int, loc: tuple[np.ndarray, np.ndarray]) -> np.ndarray:
        if t > self.T:
            return np.zeros(len(loc[0]))
        return _lerp(self.GB[t, a, n], self.rm[t][1][n], loc)

    # ---- post-promotion (unconstrained delayed belief DP) ---------------------------------
    def brA(self, t: int, n: int, m: SimpleNamespace) -> list[list[np.ndarray | None]]:
        c = self.cfg.c
        out: list[list[np.ndarray | None]] = []
        for a2 in (0, 1):
            base = m.pos if a2 == 0 else 1.0 - m.pos
            v0 = base + self._GA(t + 1, a2, n, m.loc_prop)
            v1 = base + c + self._GB(t + 1, a2, n - 1, m.loc_self) if self.qok(t, n) else None
            out.append([v0, v1])
        return out

    def brB(self, t: int, n: int, m: SimpleNamespace) -> list[list[np.ndarray | None]]:
        c = self.cfg.c
        out: list[list[np.ndarray | None]] = []
        for a2 in (0, 1):
            base = m.posprop if a2 == 0 else 1.0 - m.posprop
            v0 = base + sum(m.p[z] * self._GA(t + 1, a2, n, m.loc_pp2[z]) for z in (0, 1))
            if self.qok(t, n):
                v1 = base + c + sum(m.p[z] * self._GB(t + 1, a2, n - 1, m.loc_pp[z]) for z in (0, 1))
            else:
                v1 = None
            out.append([v0, v1])
        return out

    @staticmethod
    def _best(br: list[np.ndarray | None]) -> np.ndarray:
        v0, v1 = br
        assert v0 is not None
        return v0 if v1 is None else np.minimum(v0, v1)

    def promote_cost(self, br: list[list[np.ndarray | None]]) -> np.ndarray:
        return self.cfg.k + self._best(br[1])

    def build_post(self) -> None:
        cfg, T = self.cfg, self.T
        for t in range(T, 0, -1):
            for n in range(self.B + 1):
                for typ in (0, 1):
                    rows = self.rows[t][typ][n]
                    if len(rows) == 0:
                        continue
                    b = self.grid[rows]
                    if typ == 0:
                        br = self.brA(t, n, self.mapsA(b))
                    else:
                        br = self.brB(t, n, self.mapsB(b))
                    best = [self._best(br[a2]) for a2 in (0, 1)]
                    for old in (0, 1):
                        val = np.minimum(best[0] + cfg.k * (0 != old), best[1] + cfg.k * (1 != old))
                        (self.GA if typ == 0 else self.GB)[t, old, n] = val

    # ---- pre-promotion Bellman step -------------------------------------------------------
    def split(self, V: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Q[r, j] = min {V[r, a, b] : m(a, b) <= j}, with the argmin a (b = min(N, 2j - a))."""
        N, Nw = self.N, self.Nw
        j = np.arange(Nw)[:, None]
        a = np.arange(Nw)[None, :]
        valid = (a <= j) if self.cfg.mode == "causal" else (2 * j - a >= 0)
        bidx = np.where(valid, np.minimum(N, 2 * j - a), 0)
        rows = V.shape[0]
        Q = np.empty((rows, Nw))
        arg = np.empty((rows, Nw), dtype=np.int64)
        chunk = max(1, int(3e6 // (Nw * Nw)))
        for s in range(0, rows, chunk):
            vals = V[s : s + chunk][:, a, bidx]
            vals = np.where(valid[None], vals, np.inf)
            arg[s : s + chunk] = vals.argmin(axis=2)
            Q[s : s + chunk] = vals.min(axis=2)
        return Q, arg

    def stepA(self, t: int, n: int, b: np.ndarray) -> SimpleNamespace:
        cfg, N = self.cfg, self.N
        m = self.mapsA(b)
        noq = self._VA(t + 1, n, m.loc_prop)
        qflag = np.zeros(noq.shape, dtype=bool)
        arg = np.zeros(noq.shape, dtype=np.int64)
        cmin = noq
        if self.qok(t, n):
            Q, arg = self.split(self._VB(t + 1, n - 1, m.loc_self))
            qc = cfg.c + Q
            qflag = qc < noq
            cmin = np.minimum(noq, qc)
        C = m.pos[:, None] + cmin
        P = self.promote_cost(self.brA(t, n, m))
        f = C.copy()
        promo = P < C[:, N]
        f[:, N] = np.minimum(C[:, N], P)
        return SimpleNamespace(f=f, qflag=qflag, arg=arg, promo=promo, m=m)

    def stepB(self, t: int, n: int, mu: np.ndarray) -> SimpleNamespace:
        cfg, N = self.cfg, self.N
        m = self.mapsB(mu)
        V = [self._VA(t + 1, n, m.loc_pp2[z]) for z in (0, 1)]
        fN = (
            m.posprop[:, None, None]
            + (m.p[0][:, None] * V[0])[:, :, None]
            + (m.p[1][:, None] * V[1])[:, None, :]
        )
        f = fN
        qflag = np.zeros(fN.shape, dtype=bool)
        args = [np.zeros((len(mu), self.Nw), dtype=np.int64) for _ in (0, 1)]
        if self.qok(t, n):
            Qz = []
            for z in (0, 1):
                Qa, args[z] = self.split(self._VB(t + 1, n - 1, m.loc_pp[z]))
                Qz.append(m.p[z][:, None] * Qa)
            fQ = m.posprop[:, None, None] + cfg.c + Qz[0][:, :, None] + Qz[1][:, None, :]
            qflag = fQ < fN
            f = np.minimum(fN, fQ)
        P = self.promote_cost(self.brB(t, n, m))
        f = f.copy()
        promo = P < f[:, N, N]
        f[:, N, N] = np.minimum(f[:, N, N], P)
        return SimpleNamespace(f=f, qflag=qflag, args=args, promo=promo, m=m)

    def _store(self, t: int, n: int, tab: np.ndarray) -> np.ndarray:
        """Keep a pending-state table in memory, or on disk as a read-only memory map if ``table_dir`` is set."""
        d = self.cfg.table_dir
        if not d:
            return tab
        path = os.path.join(d, f"VB_{t}_{n}.npy")
        np.save(path, tab)
        return np.load(path, mmap_mode="r")

    def build_pre(self) -> None:
        for t in range(self.T, 0, -1):
            for n in range(self.B + 1):
                rows = self.rows[t][0][n]
                if len(rows):
                    st = self.stepA(t, n, self.grid[rows])
                    self.VA[t, n] = _lower_hull(st.f)[0]
                rows = self.rows[t][1][n]
                if len(rows):
                    st = self.stepB(t, n, self.grid[rows])
                    tab = np.empty_like(st.f)
                    for r in range(len(rows)):
                        tab[r] = _hull2(st.f[r]).table
                    self.n_hull2 += len(rows)
                    self.VB[t, n] = self._store(t, n, tab)

    def never_promote_cost(self) -> float:
        b = np.array([self.beta1])
        total = 0.0
        for _ in range(self.T):
            total += float(self.pos(b)[0])
            b = self.prop(b)
        return total


# ---- exact policy evaluation ---------------------------------------------------------------


class _Evaluator:
    def __init__(self, s: _Solver) -> None:
        self.s = s
        self.cfg = s.cfg
        self.hA: dict[tuple, SimpleNamespace] = {}
        self.hB: dict[tuple, SimpleNamespace] = {}
        self.memoA: dict[tuple, tuple] = {}
        self.memoB: dict[tuple, tuple] = {}
        self.postA_memo: dict[tuple, float] = {}
        self.postB_memo: dict[tuple, float] = {}

    # post-promotion greedy policy ------------------------------------------------------------
    def _post_choice(self, br: list[list[np.ndarray | None]], a: int) -> tuple[int, int]:
        k = self.cfg.k
        best, bv = (0, 0), math.inf
        for a2 in (0, 1):
            for q in (0, 1):
                v = br[a2][q]
                if v is None:
                    continue
                val = float(v[0]) + k * (a2 != a)
                if val < bv - 1e-15:
                    best, bv = (a2, q), val
        return best

    def postA(self, t: int, a: int, n: int, b: float) -> float:
        if t > self.s.T:
            return 0.0
        key = (t, a, n, _key(b))
        hit = self.postA_memo.get(key)
        if hit is not None:
            return hit
        s, cfg = self.s, self.cfg
        arr = np.array([b])
        m = s.mapsA(arr)
        a2, q = self._post_choice(s.brA(t, n, m), a)
        pos = float(m.pos[0])
        val = (pos if a2 == 0 else 1.0 - pos) + cfg.c * q + cfg.k * (a2 != a)
        if q:
            val += self.postB(t + 1, a2, n - 1, b)
        else:
            val += self.postA(t + 1, a2, n, float(s.prop(arr)[0]))
        self.postA_memo[key] = val
        return val

    def postB(self, t: int, a: int, n: int, mu: float) -> float:
        if t > self.s.T:
            return 0.0
        key = (t, a, n, _key(mu))
        hit = self.postB_memo.get(key)
        if hit is not None:
            return hit
        s, cfg = self.s, self.cfg
        m = s.mapsB(np.array([mu]))
        a2, q = self._post_choice(s.brB(t, n, m), a)
        pp = float(m.posprop[0])
        val = (pp if a2 == 0 else 1.0 - pp) + cfg.c * q + cfg.k * (a2 != a)
        for z in (0, 1):
            pz = float(m.p[z][0])
            if q:
                val += pz * self.postB(t + 1, a2, n - 1, float(m.pp[z][0]))
            else:
                val += pz * self.postA(t + 1, a2, n, float(m.pp2[z][0]))
        self.postB_memo[key] = val
        return val

    def promoteA(self, t: int, n: int, b: float) -> float:
        s, cfg = self.s, self.cfg
        arr = np.array([b])
        m = s.mapsA(arr)
        br = s.brA(t, n, m)[1]
        q = 1 if (br[1] is not None and float(br[1][0]) < float(br[0][0])) else 0  # type: ignore[index]
        pos = float(m.pos[0])
        val = cfg.k + 1.0 - pos + cfg.c * q
        if q:
            val += self.postB(t + 1, 1, n - 1, b)
        else:
            val += self.postA(t + 1, 1, n, float(s.prop(arr)[0]))
        return val

    def promoteB(self, t: int, n: int, mu: float) -> float:
        s, cfg = self.s, self.cfg
        m = s.mapsB(np.array([mu]))
        br = s.brB(t, n, m)[1]
        q = 1 if (br[1] is not None and float(br[1][0]) < float(br[0][0])) else 0  # type: ignore[index]
        pp = float(m.posprop[0])
        val = cfg.k + 1.0 - pp + cfg.c * q
        for z in (0, 1):
            pz = float(m.p[z][0])
            if q:
                val += pz * self.postB(t + 1, 1, n - 1, float(m.pp[z][0]))
            else:
                val += pz * self.postA(t + 1, 1, n, float(m.pp2[z][0]))
        return val

    # pre-promotion ---------------------------------------------------------------------------
    def _hullA(self, t: int, n: int, b: float) -> SimpleNamespace:
        key = (t, n, _key(b))
        hit = self.hA.get(key)
        if hit is None:
            st = self.s.stepA(t, n, np.array([b]))
            _, is_v = _lower_hull(st.f)
            hit = SimpleNamespace(verts=np.flatnonzero(is_v[0]), qflag=st.qflag[0], arg=st.arg[0], promo=bool(st.promo[0]))
            self.hA[key] = hit
        return hit

    def _hullB(self, t: int, n: int, mu: float) -> SimpleNamespace:
        key = (t, n, _key(mu))
        hit = self.hB.get(key)
        if hit is None:
            st = self.s.stepB(t, n, np.array([mu]))
            h = _hull2(st.f[0])
            self.s.n_hull2 += 1
            hit = SimpleNamespace(
                pts=h.pts, fac=h.fac, qflag=st.qflag[0], args=[a[0] for a in st.args], promo=bool(st.promo[0])
            )
            self.hB[key] = hit
        return hit

    def _bounded(self, x: float) -> float:
        return min(max(x, 0.0), float(self.s.N))

    def evalA(self, t: int, n: int, b: float, x: float) -> tuple[float, float, float]:
        """(expected cost-to-go, causal risk-to-go, IID risk-to-go) of the executed policy."""
        if t > self.s.T:
            return 0.0, 0.0, 0.0
        x = self._bounded(x)
        key = (t, n, _key(b), round(x, 9))
        hit = self.memoA.get(key)
        if hit is not None:
            return hit
        s, cfg, N = self.s, self.cfg, self.s.N
        h = self._hullA(t, n, b)
        verts = h.verts
        lo_candidates = verts[verts <= x + 1e-12]
        lo = int(lo_candidates[-1]) if len(lo_candidates) else int(verts[0])
        hi_candidates = verts[verts >= x - 1e-12]
        hi = int(hi_candidates[0]) if len(hi_candidates) else int(verts[-1])
        lam = 0.0 if hi == lo else (x - lo) / (hi - lo)
        wP = wN = wQ = 0.0
        xN = 0.0
        pa = pb = 0.0
        for v, w in ((lo, 1.0 - lam), (hi, lam)):
            if w <= 0:
                continue
            if v == N and h.promo:
                wP += w
            elif bool(h.qflag[v]):
                a = int(h.arg[v])
                bb = min(N, 2 * v - a)
                wQ += w
                pa += w * a
                pb += w * bb
            else:
                wN += w
                xN += w * v
        arr = np.array([b])
        pos = float(s.pos(arr)[0])
        cost = 0.0
        rc = ri = wP
        if wP > _EPS:
            cost += wP * self.promoteA(t, n, b)
        if wN > _EPS:
            c0, rc0, ri0 = self.evalA(t + 1, n, float(s.prop(arr)[0]), xN / wN)
            cost += wN * (pos + c0)
            rc += wN * rc0
            ri += wN * ri0
        if wQ > _EPS:
            cB, rcB, riB = self.evalB(t + 1, n - 1, b, pa / wQ, pb / wQ)
            cost += wQ * (pos + cfg.c + cB)
            rc += wQ * max(rcB[0], 0.5 * (rcB[0] + rcB[1]))
            ri += wQ * 0.5 * (riB[0] + riB[1])
        out = (cost, rc, ri)
        self.memoA[key] = out
        return out

    def evalB(
        self, t: int, n: int, mu: float, x0: float, x1: float
    ) -> tuple[float, tuple[float, float], tuple[float, float]]:
        """(cost-to-go, (R_c(z=0), R_c(z=1)), (R_iid(z=0), R_iid(z=1))) at a pending node."""
        if t > self.s.T:
            return 0.0, (0.0, 0.0), (0.0, 0.0)
        x0, x1 = self._bounded(x0), self._bounded(x1)
        key = (t, n, _key(mu), round(x0, 9), round(x1, 9))
        hit = self.memoB.get(key)
        if hit is not None:
            return hit
        s, cfg, N = self.s, self.cfg, self.s.N
        h = self._hullB(t, n, mu)
        idx, lam = _locate_facet(h.pts, h.fac, x0, x1)
        wP = 0.0
        wN = 0.0
        wQ = 0.0
        xN = [0.0, 0.0]
        qa = [0.0, 0.0]
        qb = [0.0, 0.0]
        for vi, w in zip(idx, lam, strict=True):
            if w <= 0:
                continue
            i0, i1 = int(h.pts[vi, 0]), int(h.pts[vi, 1])
            if i0 == N and i1 == N and h.promo:
                wP += w
            elif bool(h.qflag[i0, i1]):
                wQ += w
                for z, i in ((0, i0), (1, i1)):
                    a = int(h.args[z][i])
                    qa[z] += w * a
                    qb[z] += w * min(N, 2 * i - a)
            else:
                wN += w
                xN[0] += w * i0
                xN[1] += w * i1
        m = s.mapsB(np.array([mu]))
        pz = [float(m.p[0][0]), float(m.p[1][0])]
        pp = float(m.posprop[0])
        cost = 0.0
        if wP > _EPS:
            cost += wP * self.promoteB(t, n, mu)
        cost += (wN + wQ) * pp + wQ * cfg.c
        rc = [wP, wP]
        ri = [wP, wP]
        for z in (0, 1):
            if wN > _EPS:
                c0, rc0, ri0 = self.evalA(t + 1, n, float(m.pp2[z][0]), xN[z] / wN)
                cost += wN * pz[z] * c0
                rc[z] += wN * rc0
                ri[z] += wN * ri0
            if wQ > _EPS:
                cB, rcB, riB = self.evalB(t + 1, n - 1, float(m.pp[z][0]), qa[z] / wQ, qb[z] / wQ)
                cost += wQ * pz[z] * cB
                rc[z] += wQ * max(rcB[0], 0.5 * (rcB[0] + rcB[1]))
                ri[z] += wQ * 0.5 * (riB[0] + riB[1])
        out = (cost, (rc[0], rc[1]), (ri[0], ri[1]))
        self.memoB[key] = out
        return out


def solve(config: RBDP2Config) -> dict[str, Any]:
    """Solve a cell for ``config.mode``; ``U`` is the exact cost of the extracted feasible policy."""
    sys.setrecursionlimit(max(20_000, sys.getrecursionlimit()))
    t0 = time.perf_counter()
    s = _Solver(config)
    t1 = time.perf_counter()
    s.build_post()
    t2 = time.perf_counter()
    s.build_pre()
    t3 = time.perf_counter()
    idx = min(s.N, int(math.floor(config.alpha * s.N + 1e-9)))
    ra = s.rm[1][0][config.B][int(np.argmin(np.abs(s.grid - s.beta1)))]
    dp_value = float(s.VA[1, config.B][ra, idx]) if ra >= 0 else float("nan")
    ev = _Evaluator(s)
    cost, rc, ri = ev.evalA(1, config.B, s.beta1, float(idx))
    t4 = time.perf_counter()
    return {
        "U": cost,
        "cost_exact": cost,
        "dp_value": dp_value,
        "risk_causal": rc,
        "risk_iid": ri,
        "C0": s.never_promote_cost(),
        "mode": config.mode,
        "n_w": s.Nw,
        "n_beta_grid": s.G,
        "belief_grid": "reach" if s.mode_reach else "uniform",
        "n_hull2": s.n_hull2,
        "n_eval_nodes": len(ev.memoA) + len(ev.memoB),
        "time_setup": t1 - t0,
        "time_post": t2 - t1,
        "time_pre": t3 - t2,
        "time_eval": t4 - t3,
        "time_total": t4 - t0,
    }
