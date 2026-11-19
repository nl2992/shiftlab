"""Two-state Bernoulli-emission HMM by EM (numpy, scaled forward-backward), plus gates G1 and G2.

Model: S_1 ~ stationary law of the chain, S_{t+1} | S_t via (t01, t10), x_t | S_t ~ Bernoulli(e_{S_t}).
EM: E-step with the stationary prior of the current parameters; standard M-step for transitions and emissions
(the dependence of the prior on (t01, t10) is ignored in the M-step). The best restart is then polished by a
bounded L-BFGS-B on the exact stationary-prior log-likelihood and kept only if it improves it.
Probabilities are clipped to [EPS, 1-EPS] inside the algorithm. States are ordered so that e0 < e1.
"""

from __future__ import annotations

import time

import numpy as np
from scipy.optimize import minimize

EPS = 1e-6
SEED = 20261116
N_RESTARTS = 20


def stationary1(t01: float, t10: float) -> float:
    return t01 / (t01 + t10)


def forward(x: np.ndarray, t01: float, t10: float, e0: float, e1: float):
    """Scaled forward pass (scalar arithmetic for speed). Returns (loglik, alpha[n,2], scales[n])."""
    n = len(x)
    pi1 = stationary1(t01, t10)
    a0, a1 = 1 - t01, 1 - t10
    xs = x.tolist()
    al0 = [0.0] * n
    al1 = [0.0] * n
    c = [0.0] * n
    u0 = (1 - pi1) * (e0 if xs[0] else 1 - e0)
    u1 = pi1 * (e1 if xs[0] else 1 - e1)
    s = u0 + u1
    c[0] = s
    p0, p1 = u0 / s, u1 / s
    al0[0], al1[0] = p0, p1
    for t in range(1, n):
        u0 = (p0 * a0 + p1 * t10) * (e0 if xs[t] else 1 - e0)
        u1 = (p0 * t01 + p1 * a1) * (e1 if xs[t] else 1 - e1)
        s = u0 + u1
        c[t] = s
        p0, p1 = u0 / s, u1 / s
        al0[t], al1[t] = p0, p1
    c_arr = np.array(c)
    return float(np.log(c_arr).sum()), np.column_stack([al0, al1]), c_arr


def loglik(x, p) -> float:
    return forward(np.asarray(x, int), *p)[0]


def _estep(x, p):
    t01, t10, e0, e1 = p
    n = len(x)
    ll, alpha, c = forward(x, *p)
    xs = x.tolist()
    a0, a1 = 1 - t01, 1 - t10
    b0 = [1.0] * n
    b1 = [1.0] * n
    q0 = q1 = 1.0
    for t in range(n - 2, -1, -1):
        l0 = (e0 if xs[t + 1] else 1 - e0) * q0
        l1 = (e1 if xs[t + 1] else 1 - e1) * q1
        q0 = (a0 * l0 + t01 * l1) / c[t + 1]
        q1 = (t10 * l0 + a1 * l1) / c[t + 1]
        b0[t], b1[t] = q0, q1
    beta = np.column_stack([b0, b1])
    gamma = alpha * beta
    gamma /= gamma.sum(axis=1, keepdims=True)
    # xi_t(i,j) proportional to alpha_t(i) A(i,j) lik_{t+1}(j) beta_{t+1}(j), vectorised over t
    e = np.array([e0, e1])
    lik_next = np.where(x[1:, None] == 1, e[None, :], 1 - e[None, :]) * beta[1:]
    A = np.array([[a0, t01], [t10, a1]])
    m = alpha[:-1, :, None] * A[None, :, :] * lik_next[:, None, :]
    m /= m.sum(axis=(1, 2), keepdims=True)
    xi = m.sum(axis=0)
    return ll, gamma, xi


def _clip(p):
    return tuple(float(np.clip(v, EPS, 1 - EPS)) for v in p)


def em_one(x, p0, max_iter=1500, tol=1e-9, deadline=None):
    p = _clip(p0)
    prev = -np.inf
    ll = prev
    for _ in range(max_iter):
        ll, gamma, xi = _estep(x, p)
        t01 = xi[0, 1] / max(xi[0].sum(), 1e-300)
        t10 = xi[1, 0] / max(xi[1].sum(), 1e-300)
        g = gamma.sum(axis=0)
        e1v = (gamma[:, 1] * x).sum() / max(g[1], 1e-300)
        e0v = (gamma[:, 0] * x).sum() / max(g[0], 1e-300)
        p = _clip((t01, t10, e0v, e1v))
        if abs(ll - prev) < tol:
            break
        if deadline is not None and time.perf_counter() > deadline:
            break
        prev = ll
    return p, loglik(x, p)


def _polish(x, p):
    f = lambda q: -loglik(x, tuple(q))  # noqa: E731
    r = minimize(f, np.array(p), method="L-BFGS-B", bounds=[(EPS, 1 - EPS)] * 4)
    q = _clip(r.x)
    return q, loglik(x, q)


def _order(p):
    t01, t10, e0, e1 = p
    return (t10, t01, e1, e0) if e0 > e1 else (t01, t10, e0, e1)


def fit_hmm(x, seed: int = SEED, n_restarts: int = N_RESTARTS, deadline: float | None = None) -> dict:
    x = np.asarray(x, int)
    rng = np.random.default_rng(seed)
    best = None
    lls = []
    capped = False
    for _ in range(n_restarts):
        if deadline is not None and lls and time.perf_counter() > deadline:
            capped = True
            break
        p0 = (rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.95), rng.uniform(0.05, 0.5), rng.uniform(0.5, 0.95))
        p, ll = em_one(x, p0, deadline=deadline)
        if deadline is not None and time.perf_counter() > deadline:
            capped = True
        lls.append(ll)
        if best is None or ll > best[1]:
            best = (p, ll)
    p_em, ll_em = best
    p_pol, ll_pol = _polish(x, p_em)
    p, ll = (p_pol, ll_pol) if ll_pol > ll_em else (p_em, ll_em)
    t01, t10, e0, e1 = _order(p)
    return dict(t01=t01, t10=t10, e0=e0, e1=e1, loglik=ll, loglik_em=ll_em, polished=bool(ll_pol > ll_em),
                restart_loglik_min=float(min(lls)), restart_loglik_max=float(max(lls)),
                n_restarts_at_best=int(sum(v > ll_em - 1e-6 for v in lls)),
                n=len(x), stationary1=stationary1(t01, t10), time_cap_hit=capped, n_restarts_done=len(lls))


# ---------------------------------------------------------------- baselines and G1
def ll_iid(x, p1) -> float:
    k = int(np.sum(x))
    return k * np.log(p1) + (len(x) - k) * np.log(1 - p1)


def fit_iid(x) -> float:
    return (np.sum(x) + 0.5) / (len(x) + 1.0)  # add-1/2 smoothing, so no zero probabilities


def fit_markov(x):
    """Add-1/2 smoothed P(x_{t+1}=1 | x_t=s), s=0,1."""
    x = np.asarray(x, int)
    q = []
    for s in (0, 1):
        m = x[:-1] == s
        q.append((np.sum(x[1:][m]) + 0.5) / (m.sum() + 1.0))
    return q


def ll_markov(x, q, prev=None) -> float:
    """Log-lik of x[1:] given x[0] (or of all of x given prev)."""
    x = np.asarray(x, int)
    seq = x if prev is None else np.concatenate([[prev], x])
    s, y = seq[:-1], seq[1:]
    p = np.where(s == 1, q[1], q[0])
    return float(np.sum(np.where(y == 1, np.log(p), np.log(1 - p))))


def gate_g1(x, seed: int = SEED, n_restarts: int = N_RESTARTS, full_fit: dict | None = None,
            deadline: float | None = None) -> dict:
    x = np.asarray(x, int)
    n = len(x)
    h = n // 2
    x1, x2 = x[:h], x[h:]
    n2 = len(x2)
    # split: fit on first half, score second half conditional on the first half
    f1 = fit_hmm(x1, seed, n_restarts, deadline)
    p1 = (f1["t01"], f1["t10"], f1["e0"], f1["e1"])
    ll_full_h1 = loglik(x, p1)
    ll_first_h1 = loglik(x1, p1)
    hmm_test = (ll_full_h1 - ll_first_h1) / n2  # predictive mean log-lik of second half
    iid_test = ll_iid(x2, fit_iid(x1)) / n2
    mk_test = ll_markov(x2, fit_markov(x1), prev=x1[-1]) / n2
    best_base = max(iid_test, mk_test)
    split_margin = hmm_test - best_base
    # BIC on the full series
    ffull = full_fit if full_fit is not None else fit_hmm(x, seed, n_restarts)
    ll_h = ffull["loglik"]
    pi = fit_iid(x)
    ll_i = ll_iid(x, pi)
    q = fit_markov(x)
    # first observation under the chain's stationary law
    st1 = q[0] / (q[0] + 1 - q[1]) if (q[0] + 1 - q[1]) > 0 else 0.5
    ll_m = ll_markov(x, q) + (np.log(st1) if x[0] == 1 else np.log(1 - st1))
    ln = np.log(n)
    bic_h, bic_i, bic_m = -2 * ll_h + 4 * ln, -2 * ll_i + 1 * ln, -2 * ll_m + 2 * ln
    bic_pass = bic_h < min(bic_i, bic_m)
    split_pass = split_margin > 0
    return dict(
        pass_=bool(split_pass or bic_pass), split_pass=bool(split_pass), bic_pass=bool(bic_pass),
        n_first=h, n_second=n2, hmm_test_mean_ll=hmm_test, iid_test_mean_ll=iid_test, markov_test_mean_ll=mk_test,
        split_margin=split_margin, first_half_fit={k: f1[k] for k in ("t01", "t10", "e0", "e1", "time_cap_hit")},
        loglik_hmm=ll_h, loglik_iid=ll_i, loglik_markov=ll_m, bic_hmm=bic_h, bic_iid=bic_i, bic_markov=bic_m,
        bic_margin=min(bic_i, bic_m) - bic_h, full_fit=ffull,
    )


def gate_g2(fit: dict) -> dict:
    e_ok = fit["e0"] < 0.5 < fit["e1"]
    t_ok = all(0.01 <= fit[k] <= 0.99 for k in ("t01", "t10"))
    return dict(pass_=bool(e_ok and t_ok), emissions_straddle_half=bool(e_ok), transitions_in_range=bool(t_ok),
                at_bounds={k: bool(fit[k] <= 2 * EPS or fit[k] >= 1 - 2 * EPS) for k in ("t01", "t10", "e0", "e1")})


def solver_params(fit: dict) -> dict:
    """Parameters passed to the solver: stationary law as prior, emissions clipped to [0.02, 0.98]."""
    return dict(t01=fit["t01"], t10=fit["t10"], e0=float(np.clip(fit["e0"], 0.02, 0.98)),
                e1=float(np.clip(fit["e1"], 0.02, 0.98)), prior1=stationary1(fit["t01"], fit["t10"]))
