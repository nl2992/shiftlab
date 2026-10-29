"""Lane B C2: Monte Carlo development check of RLS on the narrowed periodic-window family.

DEVELOPMENT SANITY CHECK ONLY. Not confirmatory; nothing here was preregistered beyond the
constants below, which were fixed before the first run (see C2_rls_narrowed_theory.md, section 7).

Family (docs/lane_b_burst_allocation/C2_rls_narrowed_theory.md, section 1):
  * known period L, unknown offset phi ~ Uniform{0..L-1};
  * window j is [phi + j L + eta_j, phi + j L + eta_j + W); the candidate is better there
    (paired-loss mean +Delta) and worse (-Delta) elsewhere;
  * eta_j iid Uniform{-sigma..sigma}: BOUNDED, independent, non-accumulating per-boundary jitter;
  * Z_t in {-1,+1}, P(Z_t=+1) = (1+mu_t)/2; one common paired label per queried round;
  * fixed delay d (query at t is visible at the start of t+d), request-time hard budget B
    (pending labels count), query cost c, switch cost k, A_0 = 0;
  * the first 0 -> 1 switch must be gated by a level-alpha test of the causal null
    "E[Z_t | past] <= 0 for every t".

Arms (identical B, d, c, k, alpha, and identical knowledge of L, W, sigma, Delta):
  rls          exact Bayes posterior over phi (jitter marginalised per window), posterior-guided
               query design restricted to the next L rounds (info gain + pre-certification
               betting value), phase-stratified e-process gate, receding-horizon switch planner
               on the exact posterior predictive.
  mle_uniform  duration-aware MLE forecaster: uniform random query calendar (rate B/T), plug-in
               MLE of phi, same e-process gate with plug-in stakes, same planner on plug-in means.
  mle_active   ablation: plug-in MLE planning/stakes with RLS's query design.
  ts_forecaster textbook targeted design: each round draw a phase from the exact posterior
               (Thompson sampling) and query iff that phase predicts the candidate window; plug-in
               MLE stakes and planning. No information-gain computation, no pacing.
  exp4         Periodic-EXP4-style schedule learner: label-efficient exponential weights over the
               L shifted nominal schedules (importance-weighted paired gains, delayed updates),
               expert resampled once per calendar block, same gate with weight-based stakes.
  reactive     all-onset e-detector mixture gate (Shin-Ramdas-Rinaldo style) on a uniform random
               calendar, then two-sided CUSUM rollback / re-promotion on released labels.
  never        never switch.
  always       switch to the candidate at t=0 and stay (ungated reference: violates the gate).
  oracle       knows phi (not the jitter), deploys the nominal window, buys no labels.

Seeds: registry block lane_b_toy_development (100600000-100699999). Earlier Lane B scripts used
offsets [0,7000) of strides 0-9 (first and corrective checks) and 100690000-100692999 (K_alpha
reference) of that block; the overflow block 100700000-100830999 is never touched. This script
uses only 100696000-100697999 (alternative worlds) and 100698000-100699999 (null worlds), with
common random numbers across all cells and arms. tests/test_lane_b_rls.py checks disjointness.

Run (from the worktree):
  PYTHONIOENCODING=utf-8 PYTHONPATH="$PWD/src" UV_PROJECT_ENVIRONMENT=<main>/.venv \
    uv run --no-sync python scripts/lane_b/rls_exact_small.py [n_seeds] [--out results.json]
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import asdict, dataclass
from multiprocessing import Pool

import numpy as np
from scipy.special import logsumexp
from scipy.stats import beta as beta_dist

# ---------------------------------------------------------------- fixed constants (pre-run)
L = 24
W = 8
S = 20
T = S * L
DELTA = 0.4
ALPHA = 0.05
C_QUERY = 0.01
K_SWITCH = 0.25
STAKE_MAX = 0.9
TAU_IG = 0.003  # minimum query score (nats) for the posterior-guided design
CUSUM_H = 1.5  # reactive rollback threshold (log-likelihood units)
SIGMAS = (0, 1, 2)
DELAYS = (1, 4)
BUDGETS_PRIMARY = (30, 60)
BUDGETS_EXPLORATORY = (120, 240)
N_SEEDS_DEFAULT = 2000

SEED_ALT = 100_696_000
SEED_NULL = 100_698_000
SEED_BLOCK = (100_600_000, 100_699_999)
OVERFLOW_BLOCK = (100_700_000, 100_830_999)
# Inclusive ranges already used inside the block by scripts/lane_b/separation_check.py.
USED_RANGES = (
    [(100_600_000 + 10_000 * k, 100_600_000 + 10_000 * k + 999) for k in range(10)]
    + [(100_605_000 + 10_000 * k, 100_605_000 + 10_000 * k + 999) for k in range(10)]
    + [(100_601_000 + 10_000 * k, 100_601_000 + 10_000 * k + 3_999) for k in range(8)]
    + [(100_690_000, 100_692_999)]
)

ARMS = (
    "rls",
    "mle_uniform",
    "mle_active",
    "ts_forecaster",
    "exp4",
    "reactive",
    "never",
    "always",
    "oracle",
)
LEARNERS = ("rls", "mle_uniform", "mle_active", "ts_forecaster", "exp4", "reactive")
KAPPA = math.log((1 + DELTA) / (1 - DELTA))


# ---------------------------------------------------------------- closed-form helpers
def e_abs(sigma: int) -> float:
    """E|eta| for eta ~ Uniform{-sigma..sigma}."""
    return sigma * (sigma + 1) / (2 * sigma + 1)


def jitter_floor(sigma: int, d: int) -> float:
    """g(sigma,d): minimal expected mismatched rounds at one up-edge for ANY causal policy that
    knows phi, has unlimited budget and noiseless labels (C2 doc, Proposition E1)."""
    J = 2 * sigma + 1
    tot = 0
    for t in range(-sigma, sigma + 1):
        n1 = sum(1 for e in range(-sigma, sigma + 1) if t - d < e <= t)
        n2 = sum(1 for e in range(-sigma, sigma + 1) if e > t)
        tot += min(n1, n2)
    return tot / J


def jitter_floor_bruteforce(sigma: int, d: int) -> float:
    """Same quantity by explicit Bayes decision on the noiseless information set."""
    etas = list(range(-sigma, sigma + 1))
    tot = 0.0
    for t in range(-sigma, sigma + 1):
        # information: for each eta, the learner sees state at rounds <= t-d, i.e. 1{eta <= s}
        groups: dict[tuple, list[int]] = {}
        for e in etas:
            key = tuple(int(e <= s) for s in range(-sigma - 1, t - d + 1))
            groups.setdefault(key, []).append(e)
        for members in groups.values():
            good = sum(1 for e in members if e <= t)
            tot += min(good, len(members) - good)
    return tot / len(etas)


def oracle_period_gain(sigma: int) -> float:
    return DELTA * (W - 2 * e_abs(sigma)) - 2 * K_SWITCH


def kl_bern(p: float, q: float) -> float:
    out = 0.0
    for a, b in ((p, q), (1 - p, 1 - q)):
        if a > 0:
            out += a * math.log(a / b)
    return out


def anytime_power(n: int, lam: float = DELTA, alpha: float = ALPHA, mean: float = DELTA) -> float:
    """P(sup_{m<=n} prod_{i<=m}(1+lam Z_i) >= 1/alpha) for iid Z=+-1 with E Z = mean (exact DP)."""
    p = (1 + mean) / 2
    up, dn, thr = math.log1p(lam), math.log1p(-lam), math.log(1 / alpha)
    alive = {0: 1.0}  # k positives -> prob, among paths not yet crossed
    crossed = 0.0
    for m in range(1, n + 1):
        nxt: dict[int, float] = {}
        for k, pr in alive.items():
            for k2, w in ((k + 1, p), (k, 1 - p)):
                if k2 * up + (m - k2) * dn >= thr - 1e-12:
                    crossed += pr * w
                else:
                    nxt[k2] = nxt.get(k2, 0.0) + pr * w
        alive = nxt
    return crossed


def labels_for_power(power: float, lam: float = DELTA) -> int:
    n = 1
    while anytime_power(n, lam) < power:
        n += 1
    return n


def clopper_pearson_upper(k: int, n: int, level: float = 0.95) -> float:
    return 1.0 if k >= n else float(beta_dist.ppf(level, k + 1, n - k))


# ---------------------------------------------------------------- world
@dataclass(frozen=True)
class Cell:
    sigma: int
    d: int
    B: int
    null: str  # "alt", "zero" (mean 0 everywhere), "neg" (mean -Delta everywhere)


def seed_list(kind: str, n: int) -> np.ndarray:
    base = SEED_ALT if kind == "alt" else SEED_NULL
    if n > 2000:
        raise ValueError("at most 2000 seeds per world type are registered for this script")
    return base + np.arange(n)


def draw_world(seeds: np.ndarray, sigma: int, null: str):
    """Common random numbers: the same seed gives the same phi, jitter uniforms and emission
    uniforms in every cell; eta_j = floor(u_j (2 sigma+1)) - sigma couples jitter across sigma."""
    n = len(seeds)
    J = 2 * sigma + 1
    phi = np.empty(n, dtype=int)
    ueta = np.empty((n, S + 3))
    uz = np.empty((n, T))
    uq = np.empty((n, T))
    uexp = np.empty((n, S + 1))
    for i, sd in enumerate(seeds):
        rng = np.random.default_rng(int(sd))
        phi[i] = rng.integers(L)
        ueta[i] = rng.random(S + 3)
        uz[i] = rng.random(T)
        uq[i] = rng.random(T)
        uexp[i] = rng.random(S + 1)
    eta = np.floor(ueta * J).astype(int) - sigma  # windows j = -1..S+1
    good = np.zeros((n, T), dtype=bool)
    tt = np.arange(T)
    for jj in range(S + 3):
        start = phi + (jj - 1) * L + eta[:, jj]
        good |= (tt[None, :] >= start[:, None]) & (tt[None, :] < start[:, None] + W)
    if null == "alt":
        mu = DELTA * (2 * good - 1.0)
    elif null == "zero":
        mu = np.zeros((n, T))
    elif null == "neg":
        mu = -DELTA * np.ones((n, T))
    else:
        raise ValueError(null)
    z = np.where(uz < (1 + mu) / 2, 1, -1).astype(np.int8)
    return {"phi": phi, "eta": eta, "good": good, "mu": mu, "z": z, "uq": uq, "uexp": uexp}


# ---------------------------------------------------------------- hypothesis tables
class Tables:
    """Hypothesis-side lookup tables (functions of phi', t', eta only; no data)."""

    def __init__(self, sigma: int):
        self.sigma = sigma
        self.J = 2 * sigma + 1
        etas = np.arange(-sigma, sigma + 1)
        tt = np.arange(T + L)
        ph = np.arange(L)
        # window index governing round t under phi': nearest window centre phi'+gL+W/2
        self.g = np.floor_divide(tt[None, :] - ph[:, None] + (L // 2 - W // 2), L)
        u = tt[None, :] - ph[:, None] - self.g * L  # in [W/2-L/2, W/2+L/2)
        self.G = (
            (etas[None, None, :] <= u[:, :, None]) & (u[:, :, None] < etas[None, None, :] + W)
        ).astype(float)
        self.Pin = self.G.mean(-1)  # jitter-marginal P(good at t | phi')
        self.nom = ((tt[None, :] - ph[:, None]) % L) < W  # nominal window of phi'


def hb(p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


class Posterior:
    """Exact posterior over phi with the per-window jitter marginalised: labels governed by the
    same window share eta, so the likelihood is prod_windows mean_eta prod_labels p(z|phi,eta)."""

    def __init__(self, n: int, tab: Tables):
        self.tab = tab
        self.acc = np.zeros((n, L, tab.J))
        self.total = np.zeros((n, L))
        self.cur_g = np.full((n, L), -(10**6), dtype=np.int64)

    def update(self, idx: np.ndarray, s: int, z: np.ndarray) -> None:
        if len(idx) == 0:
            return
        tab = self.tab
        gs = tab.g[:, s]
        lp = np.log((1 + z[:, None, None] * DELTA * (2 * tab.G[None, :, s, :] - 1)) / 2)
        acc = self.acc[idx]
        fold = self.cur_g[idx] != gs[None, :]
        if fold.any():
            lse = logsumexp(acc, axis=-1) - math.log(tab.J)
            self.total[idx] += np.where(fold, lse, 0.0)
            acc = np.where(fold[..., None], 0.0, acc)
            self.cur_g[idx] = np.broadcast_to(gs, fold.shape)
        self.acc[idx] = acc + lp

    def logpost(self) -> np.ndarray:
        return self.total + logsumexp(self.acc, axis=-1) - math.log(self.tab.J)

    def predictive(self, t: int, H: int):
        """pi (n,L) and P(good at t+h | phi', data) (n,L,H), using the within-window eta posterior
        when t+h is governed by the window that already has released labels."""
        tab = self.tab
        lp = self.logpost()
        pi = np.exp(lp - lp.max(1, keepdims=True))
        pi /= pi.sum(1, keepdims=True)
        sl = slice(t, t + H)
        a = self.acc - self.acc.max(-1, keepdims=True)
        w = np.exp(a)
        w /= w.sum(-1, keepdims=True)
        pacc = np.einsum("npj,phj->nph", w, tab.G[:, sl, :], optimize=True)
        same = tab.g[None, :, sl] == self.cur_g[:, :, None]
        P = np.where(same, pacc, tab.Pin[None, :, sl])
        return pi, P


def plan_first_action(mhat: np.ndarray, a_prev: np.ndarray, k: float) -> np.ndarray:
    """Receding-horizon two-state DP: minimise sum_h -a_h mhat_h + k #switches; return a_0."""
    n, H = mhat.shape
    v0 = np.zeros(n)
    v1 = np.zeros(n)
    for h in range(H - 1, 0, -1):
        c0, c1 = v0, -mhat[:, h] + v1
        v0, v1 = np.minimum(c0, c1 + k), np.minimum(c0 + k, c1)
    c0 = v0 + k * (a_prev == 1)
    c1 = -mhat[:, 0] + v1 + k * (a_prev == 0)
    return (c1 < c0).astype(np.int8)


# ---------------------------------------------------------------- simulation
def simulate(arm: str, world: dict, cell: Cell, tab: Tables, return_paths: bool = False) -> dict:
    n = len(world["phi"])
    z, uq, uexp = world["z"], world["uq"], world["uexp"]
    d, B = cell.d, cell.B
    A = np.zeros((n, T), dtype=np.int8)
    if arm == "never":
        return _summarise(A, np.zeros(n, int), np.full(n, T), world, cell)
    if arm == "always":
        A[:] = 1
        return _summarise(A, np.zeros(n, int), np.zeros(n, int), world, cell)
    if arm == "oracle":
        if oracle_period_gain(cell.sigma) > 0:
            A[:] = tab.nom[world["phi"], :T]
        return _summarise(A, np.zeros(n, int), np.zeros(n, int), world, cell)

    q_rate = B / T
    used = np.zeros(n, dtype=int)
    Q = np.zeros((n, T), dtype=bool)
    stake = np.zeros((n, T))
    logw = np.zeros(n)  # phase-stratified e-process (log wealth) on released labels
    promoted = np.zeros(n, dtype=bool)
    promo_t = np.full(n, T)
    a_prev = np.zeros(n, dtype=np.int8)
    thr = math.log(1 / ALPHA)
    post = (
        Posterior(n, tab) if arm in ("rls", "mle_uniform", "mle_active", "ts_forecaster") else None
    )
    if arm == "exp4":
        ew = np.zeros((n, L))
        eta_lr = math.sqrt(2 * q_rate * math.log(L) / T) / 2
        expert = np.zeros(n, dtype=int)
    if arm == "reactive":
        wmix = 1.0 / ((np.arange(B) + 1) * (np.arange(B) + 2))
        comp = np.zeros((n, B))
        nrel = np.zeros(n, dtype=int)
        mode = np.zeros(n, dtype=np.int8)
        s_bad = np.zeros(n)
        s_good = np.zeros(n)
    rows = np.arange(n)
    H = L
    loc_dist = np.full((n, S), L, dtype=int)  # circular |MAP - phi| at the end of each block
    labels_by = np.zeros((n, S), dtype=int)

    for t in range(T):
        # 1. release labels requested at t-d (fixed delay, request order)
        s = t - d
        if s >= 0:
            idx = np.nonzero(Q[:, s])[0]
            if len(idx):
                zs = z[idx, s].astype(float)
                if post is not None:
                    post.update(idx, s, zs)
                if arm == "exp4":
                    ew[idx] += eta_lr * (zs / q_rate)[:, None] * tab.nom[None, :, s]
                if arm == "reactive":
                    act = np.arange(B)[None, :] <= nrel[idx, None]
                    comp[idx] += np.where(act, np.log1p(DELTA * zs)[:, None], 0.0)
                    nrel[idx] += 1
                    pm = promoted[idx]
                    i1 = idx[pm & (mode[idx] == 1)]
                    i0 = idx[pm & (mode[idx] == 0)]
                    s_bad[i1] = np.maximum(0, s_bad[i1] - KAPPA * z[i1, s])
                    s_good[i0] = np.maximum(0, s_good[i0] + KAPPA * z[i0, s])
                    f1 = i1[s_bad[i1] >= CUSUM_H]
                    mode[f1] = 0
                    s_bad[f1] = 0
                    s_good[f1] = 0
                    f0 = i0[s_good[i0] >= CUSUM_H]
                    mode[f0] = 1
                    s_bad[f0] = 0
                    s_good[f0] = 0
                else:
                    logw[idx] += np.log1p(stake[idx, s] * zs)
        # 2. promotion gate on observed evidence
        if arm == "reactive":
            mix = (wmix[None, :] * np.exp(comp)).sum(1)
            newly = ~promoted & (mix >= 1 / ALPHA)
            mode[newly] = 1
        else:
            newly = ~promoted & (logw >= thr - 1e-12)
        promoted |= newly
        promo_t[newly] = t

        # 3. model quantities for this round
        hz = np.arange(H)
        live = (t + hz) < T
        if arm in ("rls", "mle_active"):
            pi, P = post.predictive(t, H)
            pgood = np.einsum("np,nph->nh", pi, P)
            pplus = (1 + DELTA * (2 * P - 1)) / 2
            ig = hb(np.einsum("np,nph->nh", pi, pplus)) - np.einsum("np,nph->nh", pi, hb(pplus))
            mpost = DELTA * (2 * pgood - 1)
        if arm in ("mle_uniform", "mle_active", "ts_forecaster"):
            lpost = post.logpost()
            phat = lpost.argmax(1)
            mplug = DELTA * (2 * tab.Pin[phat][:, t : t + H] - 1)

        # 4. action
        if arm in ("rls", "mle_uniform", "mle_active", "ts_forecaster"):
            mh = (mpost if arm == "rls" else mplug) * live[None, :]
            a = plan_first_action(mh, a_prev, K_SWITCH)
        elif arm == "exp4":
            if t % L == 0:
                p = np.exp(ew - ew.max(1, keepdims=True))
                p /= p.sum(1, keepdims=True)
                expert = (p.cumsum(1) < uexp[:, t // L][:, None]).sum(1).clip(0, L - 1)
            a = tab.nom[expert, t].astype(np.int8)
        else:  # reactive
            a = mode.copy()
        a = np.where(promoted, a, 0).astype(np.int8)
        A[:, t] = a
        a_prev = a

        # 5. query decision for the current round (only the current round can be queried)
        room = used < B
        if arm in ("rls", "mle_active"):
            lam_post = np.clip(mpost[:, 0], 0, STAKE_MAX)
            cv = (1 + mpost) / 2 * np.log1p(np.clip(mpost, 0, STAKE_MAX)) + (
                1 - mpost
            ) / 2 * np.log1p(-np.clip(mpost, 0, STAKE_MAX))
            score = ig + np.where(promoted[:, None], 0.0, cv)
            score = np.where(live[None, :], score, -np.inf)
            remaining_blocks = max((T - t) / L, 1e-9)
            allow = np.ceil((B - used) / remaining_blocks).astype(int).clip(min=1)
            rank = (score[:, 1:] > score[:, :1]).sum(1)
            q = room & (rank < allow) & (score[:, 0] >= TAU_IG)
            lam = lam_post if arm == "rls" else np.clip(mplug[:, 0], 0, STAKE_MAX)
        elif arm == "ts_forecaster":
            pp = np.exp(lpost - lpost.max(1, keepdims=True))
            pp /= pp.sum(1, keepdims=True)
            phs = (pp.cumsum(1) < uq[:, t][:, None]).sum(1).clip(0, L - 1)
            q = room & (tab.Pin[phs, t] > 0.5)
            lam = np.clip(mplug[:, 0], 0, STAKE_MAX)
        else:
            q = room & (uq[:, t] < q_rate)
            if arm == "mle_uniform":
                lam = np.clip(mplug[:, 0], 0, STAKE_MAX)
            elif arm == "exp4":
                p = np.exp(ew - ew.max(1, keepdims=True))
                p /= p.sum(1, keepdims=True)
                pg = (p * tab.nom[None, :, t]).sum(1)
                lam = np.clip(DELTA * (2 * pg - 1), 0, STAKE_MAX)
            else:
                lam = np.zeros(n)
        Q[:, t] = q
        used += q
        stake[rows, t] = np.where(q, lam, 0.0)
        if t % L == L - 1:
            labels_by[:, t // L] = used
            if post is not None:
                dd = np.abs(post.logpost().argmax(1) - world["phi"])
                loc_dist[:, t // L] = np.minimum(dd, L - dd)
    out = _summarise(A, used, promo_t, world, cell)
    if post is not None:
        out["loc_dist"] = loc_dist
        out["labels_by"] = labels_by
    if return_paths:
        out.update(A=A, Q=Q, stake=stake)
    return out


def _summarise(A, used, promo_t, world, cell) -> dict:
    mu, good = world["mu"], world["good"]
    n = A.shape[0]
    prev = np.concatenate([np.zeros((n, 1), dtype=np.int8), A[:, :-1]], axis=1)
    sw = A != prev
    gain = (A * mu).sum(1)
    net_cost = -gain + C_QUERY * used + K_SWITCH * sw.sum(1)
    out = {
        "net_cost": net_cost,
        "used": used.astype(float),
        "promo_t": promo_t.astype(float),
        "switches": sw.sum(1).astype(float),
        "promoted": (promo_t < T).astype(float),
    }
    if cell.null == "alt":
        tt = np.arange(A.shape[1])[None, :]
        post = tt >= promo_t[:, None]
        gprev = np.concatenate([good[:, :1], good[:, :-1]], axis=1)
        bnd = (good != gprev) & (tt >= promo_t[:, None] + 1)
        mism = ((A != good) & post).sum(1)
        nb = bnd.sum(1)
        pb = (DELTA * mism + K_SWITCH * (sw & post).sum(1)) / np.maximum(nb, 1)
        out["per_boundary"] = np.where(nb >= 4, pb, np.nan)
    return out


def run_cell(args):
    cell, n, arms = args
    seeds = seed_list("alt" if cell.null == "alt" else "null", n)
    world = draw_world(seeds, cell.sigma, cell.null)
    tab = Tables(cell.sigma)
    res = {}
    for arm in arms:
        res[arm] = simulate(arm, world, cell, tab)
    summary = {}
    orc = res.get("oracle")
    for arm, r in res.items():
        row = {
            "net_cost": float(r["net_cost"].mean()),
            "net_cost_se": float(r["net_cost"].std(ddof=1) / math.sqrt(n)),
            "promoted": float(r["promoted"].mean()),
            "promoted_k": int(r["promoted"].sum()),
            "promo_period": float(np.nanmean(np.where(r["promoted"] > 0, r["promo_t"] / L, np.nan)))
            if r["promoted"].sum()
            else float("nan"),
            "labels": float(r["used"].mean()),
            "switches": float(r["switches"].mean()),
        }
        if orc is not None:
            ex = r["net_cost"] - orc["net_cost"]
            row["excess"] = float(ex.mean())
            row["excess_se"] = float(ex.std(ddof=1) / math.sqrt(n))
        if "per_boundary" in r:
            pb = r["per_boundary"]
            row["per_boundary"] = float(np.nanmean(pb)) if np.isfinite(pb).any() else float("nan")
            row["per_boundary_n"] = int(np.isfinite(pb).sum())
        if "loc_dist" in r and cell.null == "alt":
            for per in (5, 10, 20):
                row[f"loc_pm_sigma_p{per}"] = float(
                    (r["loc_dist"][:, per - 1] <= cell.sigma).mean()
                )
                row[f"loc_exact_p{per}"] = float((r["loc_dist"][:, per - 1] == 0).mean())
                row[f"labels_by_p{per}"] = float(r["labels_by"][:, per - 1].mean())
        if cell.null != "alt":
            row["fp_upper95"] = clopper_pearson_upper(row["promoted_k"], n)
        summary[arm] = row
    return asdict(cell), summary


def theory_numbers() -> dict:
    """Closed-form quantities quoted in the C2 document."""
    out = {
        "kl_alt_vs_boundary_null": kl_bern((1 + DELTA) / 2, 0.5),
        "bc_star": math.sqrt(1 - DELTA**2),
        "kl_edge": kl_bern((1 + DELTA) / 2, (1 - DELTA) / 2),
        "e_abs": {s: e_abs(s) for s in SIGMAS},
        "g_floor": {f"{s},{d}": jitter_floor(s, d) for s in SIGMAS for d in DELAYS},
        "oracle_period_gain": {s: oracle_period_gain(s) for s in SIGMAS},
        "anytime_power": {nn: anytime_power(nn) for nn in (20, 30, 36, 40, 60, 72, 80, 120)},
        "labels_for_power": {p: labels_for_power(p) for p in (0.5, 0.8, 0.9)},
        "kl_cert_floor": {
            f"{pw}": kl_bern(pw, ALPHA) / kl_bern((1 + DELTA) / 2, 0.5) for pw in (0.5, 0.8, 0.9)
        },
    }
    # Fano floor for exact localisation at sigma = 0 with 95% success: ((1-.05) ln L - ln 2) / C
    cap = math.log(2) - (-(0.7 * math.log(0.7) + 0.3 * math.log(0.3)))
    out["fano_labels_sigma0"] = (0.95 * math.log(L) - math.log(2)) / cap
    # Round-robin tournament (Theorem L1) labels for delta=0.05 at the worst far pair
    n0 = 2 * math.log(L / 0.05) / math.log(1 / (1 - DELTA**2))
    out["round_robin_n0"] = n0
    out["round_robin_labels"] = L * (math.ceil(n0 / 2) + 1)
    return out


def main(argv: list[str]) -> None:
    n = int(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else N_SEEDS_DEFAULT
    out_path = argv[argv.index("--out") + 1] if "--out" in argv else None
    cells = []
    for B in BUDGETS_PRIMARY + BUDGETS_EXPLORATORY:
        for sigma in SIGMAS:
            for d in DELAYS:
                cells.append((Cell(sigma, d, B, "alt"), n, ARMS))
                cells.append((Cell(sigma, d, B, "zero"), n, LEARNERS))
                if B in BUDGETS_PRIMARY:
                    cells.append((Cell(sigma, d, B, "neg"), n, LEARNERS))
    t0 = time.time()
    with Pool(min(len(cells), 12)) as pool:
        results = pool.map(run_cell, cells)
    payload = {
        "constants": {
            "L": L,
            "W": W,
            "S": S,
            "T": T,
            "DELTA": DELTA,
            "ALPHA": ALPHA,
            "C_QUERY": C_QUERY,
            "K_SWITCH": K_SWITCH,
            "STAKE_MAX": STAKE_MAX,
            "TAU_IG": TAU_IG,
            "CUSUM_H": CUSUM_H,
            "n_seeds": n,
            "seeds_alt": [SEED_ALT, SEED_ALT + n - 1],
            "seeds_null": [SEED_NULL, SEED_NULL + n - 1],
        },
        "theory": theory_numbers(),
        "cells": [{"cell": c, "arms": s} for c, s in results],
        "runtime_s": time.time() - t0,
    }
    if out_path:
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=1)
    print(render(payload))


def render(payload: dict) -> str:
    lines = [f"n_seeds={payload['constants']['n_seeds']} runtime={payload['runtime_s']:.0f}s"]
    lines.append(
        "\n### Alternative worlds: net cost vs never-switch (mean, SE); excess vs phi-oracle; P(promoted); labels; per-boundary loss\n"
    )
    lines.append(
        "| B | sigma | d | arm | net cost | SE | excess vs oracle | P(prom) | mean promo period | labels | switches | per-boundary |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for c in payload["cells"]:
        cell = c["cell"]
        if cell["null"] != "alt":
            continue
        for arm in ARMS:
            r = c["arms"][arm]
            lines.append(
                f"| {cell['B']} | {cell['sigma']} | {cell['d']} | {arm} | {r['net_cost']:.2f} | {r['net_cost_se']:.2f} | "
                f"{r.get('excess', float('nan')):.2f} | {r['promoted']:.3f} | {r['promo_period']:.1f} | {r['labels']:.1f} | "
                f"{r['switches']:.1f} | {r.get('per_boundary', float('nan')):.2f} |"
            )
    lines.append(
        "\n### Localisation of phi by posterior arms: P(|MAP-phi|<=sigma)/P(exact) at the end of period 5, 10, 20 (mean labels requested by then)\n"
    )
    lines.append("| B | sigma | d | arm | p5 | p10 | p20 |")
    lines.append("|---|---|---|---|---|---|---|")
    for c in payload["cells"]:
        cell = c["cell"]
        if cell["null"] != "alt":
            continue
        for arm in ("rls", "mle_uniform", "ts_forecaster"):
            r = c["arms"][arm]
            vals = [
                f"{r[f'loc_pm_sigma_p{p}']:.2f}/{r[f'loc_exact_p{p}']:.2f} ({r[f'labels_by_p{p}']:.0f})"
                for p in (5, 10, 20)
            ]
            lines.append(
                f"| {cell['B']} | {cell['sigma']} | {cell['d']} | {arm} | "
                + " | ".join(vals)
                + " |"
            )
    lines.append("\n### Null worlds: false-promotion rate (count/n, Clopper-Pearson 95% upper)\n")
    lines.append("| B | sigma | d | null | " + " | ".join(LEARNERS) + " |")
    lines.append("|---|---|---|---|" + "---|" * len(LEARNERS))
    for c in payload["cells"]:
        cell = c["cell"]
        if cell["null"] == "alt":
            continue
        vals = []
        for arm in LEARNERS:
            r = c["arms"][arm]
            vals.append(f"{r['promoted']:.4f} ({r['fp_upper95']:.4f})")
        lines.append(
            f"| {cell['B']} | {cell['sigma']} | {cell['d']} | {cell['null']} | "
            + " | ".join(vals)
            + " |"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    main(sys.argv)
