"""wpG: fixed-calendar reduced LP for the symmetric stationary chain (d = 1, c = k = 0).

Learner class: queries at times 1..B (label s released at s+1), pre-promotion action 0, a randomised
stopping time sigma (first promotion) adapted to released labels, unconstrained optimal continuation after
promotion (the exact belief DP with the remaining calendar labels).  Values:
  V_IID^cal(alpha)    = min cost s.t. P_{IID(1/2)}(sigma < inf) <= alpha,
  V_causal^cal(alpha) = min cost s.t. sup_nu P_nu(sigma < inf) <= alpha, nu: adapted p_t in [0, 1/2].
The causal constraint uses the exact recursion R(h) = x(h) + max(R(h0), (R(h0)+R(h1))/2)
(Theorem T1 of GENERAL_B_PREMIUM.md), linearised; the IID one is linear.  Float LP (HiGHS).
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog


def build(T, B, t, e):
    """Return per-node arrays for the label tree with calendar 1..B, horizon T."""
    assert 1 <= B <= T - 1
    rho = 1.0 - 2.0 * t
    # joint forward vectors a[l][idx] = (P(S_l=0, y), P(S_l=1, y)); idx built by appending bits
    emis = np.array([e, 1.0 - e])  # P(Y=1 | S)
    a = {0: None}
    a[1] = np.zeros((2, 2))
    for bit in (0, 1):
        for s in (0, 1):
            a[1][bit, s] = 0.5 * (emis[s] if bit else 1 - emis[s])
    P = np.array([[1 - t, t], [t, 1 - t]])
    for l in range(2, B + 1):
        prev = a[l - 1]
        pred = prev @ P  # P(S_l, y_{<l})
        cur = np.zeros((2 ** l, 2))
        cur[0::2] = pred * (1 - emis)
        cur[1::2] = pred * emis
        a[l] = cur

    def post(l):  # P(S_l=1 | y) and P_A(y)
        if l == 0:
            return np.array([0.5]), np.array([1.0])
        pa = a[l].sum(1)
        return a[l][:, 1] / pa, pa

    lens = [min(s - 1, B) for s in range(1, T + 2)]  # lens[s-1] for s = 1..T+1
    # pi_s(y) = P(S_s = 1 | y), w_s = (1-2e)(2 pi - 1)
    w, PA, PI = {}, {}, {}
    for s in range(1, T + 1):
        l = lens[s - 1]
        pl, pa = post(l)
        lag = s - l if l > 0 else None
        pis = 0.5 + (pl - 0.5) * (rho ** lag) if l > 0 else np.array([0.5])
        PI[s], PA[s] = pis, pa
        w[s] = (1 - 2 * e) * (2 * pis - 1)
    # U_s(y) = max(0, w) + E[U_{s+1}], V_s = w + E[U_{s+1}]
    U = {T + 1: np.zeros(2 ** lens[T])}
    V = {}
    for s in range(T, 0, -1):
        if s <= B:  # label s added
            q1 = e + (1 - 2 * e) * PI[s]
            nxt = U[s + 1]
            EU = (1 - q1) * nxt[0::2] + q1 * nxt[1::2]
        else:
            EU = U[s + 1]
        V[s] = w[s] + EU
        U[s] = np.maximum(0.0, w[s]) + EU
    return dict(T=T, B=B, t=t, e=e, lens=lens, V=V, PA=PA, w=w, U1=float(U[1][0]))


def solve(T, B, t, e, alpha, causal):
    m = build(T, B, t, e)
    lens = m["lens"]
    off, n = {}, 0
    for s in range(1, T + 1):
        off[s] = n
        n += 2 ** lens[s - 1]
    nx = n  # x variables, then cont variables, then R variables (causal)
    nv = 2 * n + (n if causal else 0)
    cobj = np.zeros(nv)
    for s in range(1, T + 1):
        cobj[off[s]: off[s] + 2 ** lens[s - 1]] = -m["PA"][s] * m["V"][s]
    rows, cols, vals, beq = [], [], [], []
    r = 0
    for s in range(1, T + 1):
        L = 2 ** lens[s - 1]
        for i in range(L):
            # x + cont = cont(parent)
            rows += [r, r]
            cols += [off[s] + i, nx + off[s] + i]
            vals += [1.0, 1.0]
            if s == 1:
                beq.append(1.0)
            else:
                par = i // 2 if lens[s - 1] > lens[s - 2] else i
                rows.append(r)
                cols.append(nx + off[s - 1] + par)
                vals.append(-1.0)
                beq.append(0.0)
            r += 1
    Aeq = sp.csr_matrix((vals, (rows, cols)), shape=(r, nv))
    ur, uc, uv, bub = [], [], [], []
    k = 0
    if not causal:
        for s in range(1, T + 1):
            L = 2 ** lens[s - 1]
            for i in range(L):
                ur.append(0)
                uc.append(off[s] + i)
                uv.append(2.0 ** -lens[s - 1])
        bub.append(alpha)
        k = 1
    else:
        Rb = 2 * n
        # R(1) <= alpha
        ur.append(k); uc.append(Rb + off[1]); uv.append(1.0); bub.append(alpha); k += 1
        for s in range(1, T + 1):
            L = 2 ** lens[s - 1]
            newlab = s < T and lens[s] > lens[s - 1]
            for i in range(L):
                me = Rb + off[s] + i
                xi = off[s] + i
                if s == T:
                    ur += [k, k]; uc += [xi, me]; uv += [1.0, -1.0]; bub.append(0.0); k += 1
                elif not newlab:
                    ch = Rb + off[s + 1] + i
                    ur += [k, k, k]; uc += [xi, ch, me]; uv += [1.0, 1.0, -1.0]; bub.append(0.0); k += 1
                else:
                    c0 = Rb + off[s + 1] + 2 * i
                    c1 = c0 + 1
                    ur += [k, k, k]; uc += [xi, c0, me]; uv += [1.0, 1.0, -1.0]; bub.append(0.0); k += 1
                    ur += [k, k, k, k]; uc += [xi, c0, c1, me]; uv += [1.0, 0.5, 0.5, -1.0]; bub.append(0.0); k += 1
    Aub = sp.csr_matrix((uv, (ur, uc)), shape=(k, nv))
    res = linprog(cobj, A_ub=Aub, b_ub=bub, A_eq=Aeq, b_eq=beq, bounds=[(0, None)] * nv,
                  method="highs", options={"primal_feasibility_tolerance": 1e-10,
                                           "dual_feasibility_tolerance": 1e-10})
    if not res.success:
        raise RuntimeError(res.message)
    C0 = T / 2.0
    out = dict(value=C0 + res.fun, voi=-res.fun, C0=C0, full_voi=m["U1"])
    out["x"] = res.x[:n]
    out["off"], out["lens"] = off, lens
    return out


def gamma(T, B, t, e, alpha):
    vi = solve(T, B, t, e, alpha, False)
    vc = solve(T, B, t, e, alpha, True)
    G = vc["value"] - vi["value"]
    return dict(T=T, B=B, t=t, e=e, alpha=alpha, V_IID=vi["value"], V_causal=vc["value"], Gamma=G,
                VOI=vi["voi"], VOI_causal=vc["voi"], rho=G / vi["voi"] if vi["voi"] > 1e-12 else None,
                full_voi=vi["full_voi"])


def test_policy(T, B, e, alpha):
    """t = 1 only.  Causal-safe 'betting' policy of Theorem V: mixture e-process
    E_n = (prod_{odd i<=n} f(Y_i) + prod_{even i<=n} f(Y_i)) / 2, f(1) = 2(1-e), f(0) = 2e;
    promote at the first time s whose released labels have hit max E >= 1/alpha and w_s > 0.
    Returns its exact (float) VOI under A, its worst-case causal risk (recursion), its IID risk, and
    E_A[#{s < sigma : w_s > 0}] (the quantity bounding VOI_full - VOI_test)."""
    m = build(T, B, 1.0, e)
    lens = m["lens"]
    thr = 1.0 / alpha
    # e-process per prefix of length l, hit flag (running max >= thr)
    hit = {0: np.array([False])}
    E1, E0 = {0: np.array([1.0])}, {0: np.array([1.0])}
    for l in range(1, B + 1):
        f = np.array([2 * e, 2 * (1 - e)])
        a1 = np.repeat(E1[l - 1], 2)
        a0 = np.repeat(E0[l - 1], 2)
        bits = np.tile([0, 1], 2 ** (l - 1))
        if l % 2 == 1:
            a1 = a1 * f[bits]
        else:
            a0 = a0 * f[bits]
        E1[l], E0[l] = a1, a0
        hit[l] = np.repeat(hit[l - 1], 2) | ((a1 + a0) / 2 >= thr)
    # stop indicator per node (s, y): hit and w_s > 0 (first such time; earlier stops tracked by 'done')
    voi, risk_iid, wait = 0.0, 0.0, 0.0
    done = {}
    stopx = {}
    for s in range(1, T + 1):
        l = lens[s - 1]
        prev_done = np.zeros(2 ** l, bool) if s == 1 else (
            np.repeat(done[s - 1], 2) if l > lens[s - 2] else done[s - 1])
        st = (~prev_done) & hit[l] & (m["w"][s] > 1e-15)
        stopx[s] = st
        done[s] = prev_done | st
        pa = m["PA"][s]
        voi += float((pa * m["V"][s] * st).sum())
        risk_iid += float((st * 2.0 ** -l).sum())
        wait += float((pa * (~prev_done) * (m["w"][s] > 1e-15)).sum()) - float((pa * st).sum())
    # worst-case causal risk via the recursion
    R = np.zeros(2 ** lens[T - 1])
    for s in range(T, 0, -1):
        l = lens[s - 1]
        if s < T and lens[s] > l:
            r0, r1 = R[0::2], R[1::2]
            R = np.maximum(r0, (r0 + r1) / 2)
        R = np.where(stopx[s], 1.0, R)
    return dict(voi_test=voi, risk_causal=float(R[0]), risk_iid=risk_iid, wait_pos_steps=wait,
                full_voi=m["U1"])
