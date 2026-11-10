"""Reduced DP with a change hazard: two hidden regimes, lagged HMM filter, belief grid.

Model. Regime z_s in {lo, hi} flips independently with probability h per step (symmetric chain, initial
distribution 1/2-1/2). In regime z the challenger is correct on a step with probability p_z
(p_lo < p_hi). Everything else is as in reduced_dp.py (every step a disagreement, delay d, hard budget B,
price cq, switch cost cs, reversible deployment, one label decision per step).

Belief state. A label bought at step s is released at the start of step s + d and tells about z_s only.
Let g = P(z_{t-d} = hi | labels released so far) at step t (before the label of step t - d is released).
Releasing that label updates g by Bayes; the belief about the CURRENT regime is the d-step propagation
pi_now = 1/2 + (g - 1/2) (1 - 2h)^d; the next step's lagged belief is the one-step propagation of g.
This is an exact filter (a label informs only its own issue step), so the only approximation is the
linear interpolation of the value function on the g-grid (G + 1 points; checked by refining G and, at
h = 0, against the independent (k, n) solver of reduced_dp.py).

State (dep, g, u, q): u = labels bought so far (budget used), q = d-bit queue of in-flight purchases.
"""

from __future__ import annotations

import numpy as np


def _interp_matrix(points: np.ndarray, G: int) -> np.ndarray:
    """M with (M @ v)[i] = linear interpolation of v (on grid j/G) at points[i]."""
    pts = np.clip(points, 0.0, 1.0) * G
    lo = np.minimum(np.floor(pts).astype(int), G - 1)
    w = pts - lo
    M = np.zeros((len(points), G + 1))
    M[np.arange(len(points)), lo] = 1 - w
    M[np.arange(len(points)), lo + 1] = w
    return M


def solve_hazard(
    T=160, B=24, d=8, cs=2.0, cq=0.05, h=0.02, p_lo=0.35, p_hi=0.65, G=100, want_gap_inputs=False
):
    Q, QR = 1 << d, 1 << (d - 1)
    g = np.linspace(0, 1, G + 1)
    pi_now = 0.5 + (g - 0.5) * (1 - 2 * h) ** d
    m_now = pi_now * p_hi + (1 - pi_now) * p_lo
    Lm = np.stack([m_now, 1 - m_now])  # (2, G+1)
    f_next = 0.5 + (g - 0.5) * (1 - 2 * h)
    Mf = _interp_matrix(f_next, G)
    m_g = g * p_hi + (1 - g) * p_lo
    with np.errstate(divide="ignore", invalid="ignore"):
        g1 = np.where(m_g > 0, g * p_hi / m_g, g)
        g0 = np.where(m_g < 1, g * (1 - p_hi) / (1 - m_g), g)
    M1, M0 = _interp_matrix(g1, G), _interp_matrix(g0, G)
    qr = np.arange(QR)
    i0, i1 = qr << 1, (qr << 1) | 1
    q_all = np.arange(Q)
    oldest = (q_all >> (d - 1)) & 1
    qr_of_q = q_all & (QR - 1)
    pop_r = np.array([x.bit_count() for x in qr])
    u_ax = np.arange(B + 2)

    V = np.zeros((2, G + 1, B + 2, Q))
    for t in range(T - 1, -1, -1):
        Vi = np.einsum("ij,djuq->diuq", Mf, V)  # V_{t+1} at the propagated belief
        c0 = Vi[:, :, : B + 1, :][..., i0]  # (2, G+1, B+1, QR), no purchase
        c1 = np.zeros_like(c0) + np.inf
        c1[:, :, :B, :] = Vi[:, :, 1 : B + 1, :][..., i1] + cq  # purchase (u -> u + 1)
        feas = (
            (u_ax[: B + 1][:, None] < B)
            & (u_ax[: B + 1][:, None] >= pop_r[None, :])
            & (t + d <= T - 1)
        )
        cont = np.where(feas[None, None] & (c1 < c0), c1, c0)
        Gv = Lm[:, :, None, None] + cont  # (2, G+1, B+1, QR) value if deployed model = axis 0
        W = np.minimum(Gv, cs + Gv[::-1])
        # release: pre-release value
        Vnew = np.zeros_like(V)
        W_full = np.zeros((2, G + 1, B + 2, QR))
        W_full[:, :, : B + 1, :] = W
        W1 = np.einsum("ij,djuq->diuq", M1, W_full)
        W0 = np.einsum("ij,djuq->diuq", M0, W_full)
        Wrel = m_g[None, :, None, None] * W1 + (1 - m_g)[None, :, None, None] * W0
        for qq in range(Q):
            Vnew[:, :, :, qq] = Wrel[..., qr_of_q[qq]] if oldest[qq] else W_full[..., qr_of_q[qq]]
        V = Vnew
    return float(V[0, G // 2, 0, 0])


def oracle_hazard(T, cs, h, p_lo, p_hi, n=20000, seed=0):
    """Perfect-information benchmark: regime path known, labels not needed, switch whenever it pays.

    Computed by a DP over (dep, z) with exact regime knowledge (cost of an unavoidable switch cs).
    """
    rng = np.random.default_rng(seed)
    tot = 0.0
    for _ in range(n):
        z = rng.random() < 0.5
        zs = np.empty(T, bool)
        for t in range(T):
            zs[t] = z
            if rng.random() < h:
                z = not z
        pc = np.where(zs, p_hi, p_lo)
        l0, l1 = pc, 1 - pc  # expected loss of incumbent / challenger
        # offline optimal path with switching cost (two-state DP, start on model 0)
        a, b = l0[0], cs + l1[0]
        for t in range(1, T):
            a, b = min(a, b + cs) + l0[t], min(b, a + cs) + l1[t]
        tot += min(a, b)
    return tot / n


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
    import reduced_dp as R

    # cross-check at h = 0 against the independent (k, n) solver with a two-point prior
    T, B, d, cs = 60, 8, 3, 3.0
    inst = R.Inst(T=T, B=B, d=d, cs=cs, prior=("points", (0.35, 0.65), (0.5, 0.5)))
    v_kn = R.solve_optimal(inst)[0]
    for G in (100, 200):
        v_h = solve_hazard(T=T, B=B, d=d, cs=cs, h=0.0, G=G)
        print(f"h=0 check G={G}: hazard-DP {v_h:.5f}  (k,n)-DP {v_kn:.5f}  diff {v_h - v_kn:+.5f}")
