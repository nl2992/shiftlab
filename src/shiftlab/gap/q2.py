"""Q2 / S09: sequential replacement certification among K competing models (synthetic only).

Model 0 is the incumbent. Model k predicts with logit x.W + s_k(t) (x.v_k): s_k is its misspecification scale
(0 = Bayes). A candidate's *true current gap* is g_k(t) = E[loss_0 - loss_k] under the stationary label law
(positive = candidate better). Rankings can reverse over time by switching a candidate's scale.
Both models' losses are deterministic functions of (x, y), so a single label identifies the paired difference.
Error is judged against the true gap *at the certification time*: promoting a candidate whose current gap is
<= 0 is an incorrect promotion.
"""

from __future__ import annotations

import resource
import time
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

from shiftlab.sota_search import generators as g

FN, FP, TAU = g.FN_COST, g.FP_COST, g.TAU
GAP_TARGET = {"zero": 0.0, "tiny": 0.02, "moderate": 0.06, "large": 0.15}
GAP_WORSE = -0.10
S_INC = 1.5


@dataclass(frozen=True)
class Q2World:
    K: int = 5
    gap: str = "moderate"
    ranking: str = "stationary"  # stationary | one_reversal | recurrent
    T: int = 2000

    @property
    def name(self) -> str:
        return f"Q2|K{self.K}|{self.gap}|{self.ranking}|T{self.T}"


def _dirs(K: int) -> np.ndarray:
    v = np.random.default_rng(12345).standard_normal((K, g.D))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


@lru_cache(maxsize=512)
def scale_for_gap(k: int, K: int, target: float) -> float:
    """Misspecification scale of model k whose expected decision cost is ``target`` below the incumbent's (bisection)."""
    lo, hi = 0.0, 6.0
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if _gap_value(k, K, float(S_INC), float(round(mid, 6))) > target:
            lo = mid  # gap too large -> model too good -> increase its scale
        else:
            hi = mid
    return round(0.5 * (lo + hi), 6)


def scales(w: Q2World) -> np.ndarray:
    """(K, T) misspecification scales; row 0 is the incumbent. Candidate 1 is the one that can be better."""
    T = w.T
    s = np.zeros((w.K, T))
    s[0] = S_INC
    t = np.arange(T)
    good = scale_for_gap(1, w.K, GAP_TARGET[w.gap])
    bad = scale_for_gap(1, w.K, GAP_WORSE)
    cand1 = np.full(T, good)
    if w.ranking == "one_reversal":
        cand1 = np.where(t < T // 2, good, bad)
    elif w.ranking == "recurrent":
        cand1 = np.where(((t // max(T // 4, 1)) % 2) == 0, good, bad)
    s[1] = cand1
    for k in range(2, w.K):
        s[k] = scale_for_gap(k, w.K, 0.0 if k % 2 == 0 else GAP_WORSE)
    return s


@lru_cache(maxsize=512)
def _gap_value(k: int, K: int, s0: float, sk: float) -> float:
    rng = np.random.default_rng(777)
    n = 120_000
    x = rng.standard_normal((n, g.D))
    y = (rng.random(n) < g.sigmoid(x @ g.W_SRC)).astype(float)
    V = _dirs(K)

    def cost(s, v):
        act = (g.sigmoid(x @ g.W_SRC + s * (x @ v)) >= TAU).astype(float)
        return g.decision_cost(act, y).mean()

    return float(cost(s0, V[0]) - cost(sk, V[k]))


def true_gaps(w: Q2World) -> np.ndarray:
    """(K-1, T) true current gaps of each candidate versus the incumbent."""
    s = scales(w)
    out = np.zeros((w.K - 1, w.T))
    for k in range(1, w.K):
        for sv in np.unique(s[k]):
            out[k - 1, s[k] == sv] = _gap_value(k, w.K, float(S_INC), float(round(sv, 6)))
    return out


def make(w: Q2World, S: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    T, K = w.T, w.K
    x = rng.standard_normal((S, T, g.D))
    base = x @ g.W_SRC
    y = (rng.random((S, T)) < g.sigmoid(base)).astype(float)
    sc = scales(w)
    V = _dirs(K)
    proj = np.einsum("std,kd->stk", x, V)
    logit = base[..., None] + proj * sc.T[None]
    p = g.sigmoid(logit)  # (S,T,K)
    act = (p >= TAU).astype(float)
    loss = act * (1 - y)[..., None] * FP + (1 - act) * y[..., None] * FN
    L1 = act * 0 + (1 - act) * FN  # loss if y = 1
    L0 = act * FP  # loss if y = 0
    d = loss[..., :1] - loss[..., 1:]  # (S,T,Kc) incumbent minus candidate
    prox = p[..., 1:] * (L1[..., :1] - L1[..., 1:]) + (1 - p[..., 1:]) * (L0[..., :1] - L0[..., 1:])
    dis = (act[..., :1] != act[..., 1:]).astype(float)
    return {
        "d": d,
        "loss": loss,
        "proxy": prox,
        "dis": dis,
        "gap": true_gaps(w),
        "y": y,
        "act": act,
        "world": w,
    }


def _stitch(n, rng_b, a):
    n = np.maximum(n, 1.0)
    return rng_b * np.sqrt(np.log(np.pi**2 * n**2 / (3 * a)) / (2 * n))


# name -> (evidence rule, query allocation, hard-budget pacing)
CONFIG = {
    "paired_e": ("one", "uniform", False),  # per-candidate test, no multiplicity correction
    "paired_e_bonf": ("bonf", "uniform", False),
    "paired_cs": ("cs", "uniform", False),
    "pp_paired": ("pp", "uniform", False),
    "seqmcs": ("seqmcs", "uniform", False),
    "indep_labels": ("bonf", "indep", False),  # labels not shared across candidates
    "cams": (
        "bonf",
        "cams",
        False,
    ),  # disagreement-focused contextual querying (CAMS-style baseline)
    "S09a_ctxvar": ("bonf", "ctxvar", False),
    "S09a_ctxvar_shared": ("shared", "ctxvar", False),
    "S09b_disc": ("disc", "uniform", False),
    "S09b_disc_cams": ("disc", "cams", False),
    "S09c_shared": ("shared", "uniform", False),
    "S09c_shared_cams": ("shared", "cams", False),
    "S09d_budget": ("bonf", "cams", True),
    "S09e_alloc": ("alpha_alloc", "uniform", False),
    "S09e_alloc_cams": ("alpha_alloc", "cams", False),
}
METHODS = tuple(CONFIG)


def run(
    st: dict, method: str, frac: float = 0.10, delay: int = 5, alpha: float = 0.05, qseed: int = 0
) -> dict:
    """Run one certification method on S independent streams. Labels resolve ``delay`` steps after the query."""
    t_start = time.perf_counter()
    w: Q2World = st["world"]
    d = st["d"]
    S, T, Kc = d.shape
    K = w.K
    U = np.random.default_rng(55_000 + qseed).random((S, T, Kc))
    M = FN
    EV, AL, PACE = CONFIG[method]
    gam = 0.99 if EV == "disc" else 1.0
    use_pp = EV == "pp"
    thr = np.log(1 / alpha) if EV in ("one", "shared") else np.log(Kc / alpha)
    NB = T + delay + 2
    BX, BX2, BN, LF = (np.zeros((NB, S, Kc)) for _ in range(4))
    c1, c2, cn = np.zeros((S, Kc)), np.zeros((S, Kc)), np.zeros((S, Kc))
    logW = np.zeros((S, Kc))
    logG = np.zeros(S)  # S09c global wealth
    LG = np.zeros((NB, S))
    cross = np.full((S, Kc), T, dtype=np.int64)
    spent = np.zeros(S, dtype=np.int64)
    lab_cross = np.zeros((S, Kc))
    vsum, vcnt = np.zeros((Kc + 1, S)), np.zeros((Kc + 1, S))
    ew = np.full(S, 0.3)
    B = round(frac * T)
    pilot = 100 if EV == "alpha_alloc" else 0
    pil_sum, pil_cnt = np.zeros((S, Kc)), np.zeros((S, Kc))
    alpha_w = np.full((S, Kc), 1.0 / Kc)
    ar = np.arange(S)
    seq = EV == "seqmcs"
    if seq:
        pairs = [(a, b) for a in range(K) for b in range(a + 1, K)]
        ia, ib = np.array([p[0] for p in pairs]), np.array([p[1] for p in pairs])
        NP = len(pairs)
        BXp, LFp = (
            np.zeros((NB, S, NP, 2), dtype=np.float32),
            np.zeros((NB, S, NP, 2), dtype=np.float32),
        )
        c1p, c2p, cnp = (np.zeros((S, NP, 2)) for _ in range(3))
        logP = np.zeros((S, NP, 2))
        elim = np.zeros((S, K), dtype=bool)
        cum_loss = np.zeros((S, K))
        cert_t, prom, n_el = np.full(S, T, dtype=np.int64), np.full(S, -1), np.zeros(S)
        thr_pair = np.log(K * (K - 1) / alpha)
    for t in range(T):
        if t > 0:
            a = t - 1
            if gam < 1:
                c1, c2, cn = (
                    gam ** BN[a] * c1 + BX[a],
                    gam ** BN[a] * c2 + BX2[a],
                    gam ** BN[a] * cn + BN[a],
                )
            else:
                c1, c2, cn = c1 + BX[a], c2 + BX2[a], cn + BN[a]
            if seq:
                c1p, c2p, cnp = c1p + BXp[a], c2p + BXp[a].astype(float) ** 2, cnp + (BXp[a] != 0)
        disc = st["dis"][:, t, :]
        nd = disc.sum(1).astype(int)
        anyd = (nd > 0).astype(float)
        # ---- shared (or independent) query decision; q_t is a function of covariates and resolved labels
        if AL == "cams":
            q = np.clip(frac * (0.1 + anyd) / np.maximum(ew, 1e-6), 0.01, 1.0)
            q = np.where(
                anyd > 0, np.maximum(q, frac), q
            )  # disagreement events are queried at >= frac
            q_cap = np.maximum(
                np.clip(frac * 1.1 / np.maximum(ew, 1e-6), 0.01, 1.0), frac
            )  # q on any disagreement event
            ew = 0.995 * ew + 0.005 * (0.1 + anyd)
        elif AL == "ctxvar":
            # never query when every candidate agrees with the incumbent (the increment is identically 0 there);
            # among disagreement events, propensity ~ sqrt(estimated variance of the increment), floor frac
            sb = np.sqrt(np.maximum((vsum[nd, ar] + 5.0) / (vcnt[nd, ar] + 5.0), 1e-9))
            ew = 0.995 * ew + 0.005 * np.where(nd > 0, sb, 0.0)
            q = np.where(nd > 0, np.clip(frac * sb / np.maximum(ew, 1e-9), frac, 1.0), 0.0)
        else:
            q = np.full(S, frac)
        if AL != "cams":
            q_cap = np.full(S, frac / Kc if AL == "indep" else frac)
        if PACE:  # hard budget B: spending rate multiplier in [1/2, 2] tracks remaining budget / remaining horizon
            rem = np.maximum(B - spent, 0)
            mult = np.clip(rem / max(T - t, 1) / frac, 0.5, 2.0)
            q = np.where(spent < B, np.clip(q * mult, 0.0, 1.0), 0.0)
            q_cap = np.clip(q_cap * mult, 1e-3, 1.0)
        if EV == "alpha_alloc" and t == pilot:
            gh = pil_sum / np.maximum(pil_cnt, 1)
            z = np.exp((gh - gh.max(1, keepdims=True)) / 0.5)
            alpha_w = 0.5 * z / z.sum(1, keepdims=True) + 0.5 / Kc
        if AL == "indep":
            qk = np.full((S, Kc), frac / Kc)
            Qk = U[:, t, :] < qk
            spent = spent + Qk.sum(1)
            Qs = None
        else:
            Qs = (U[:, t, 0] < q) & (q > 0)
            spent = spent + Qs
            Qk = np.repeat(Qs[:, None], Kc, 1)
            qk = np.repeat(np.where(q > 0, q, 1.0)[:, None], Kc, 1)
            if AL == "ctxvar":  # agreement events: X = 0 exactly, inactive
                pass
        dt = d[:, t, :]
        hk = st["proxy"][:, t, :]
        X = hk + (Qk / qk) * (dt - hk) if use_pp else (Qk / qk) * dt
        if PACE:
            X = np.where((q > 0)[:, None], X, 0.0)
        # ---- predictable bet; the cap uses the declared lower bound of the increment, never the current covariates
        mean, second = c1 / (cn + 1.0), c2 / (cn + 1.0)
        lam = np.where(second > 0, np.maximum(mean, 0.0) / np.maximum(second, 1e-12), 0.0)
        # Increments are identically 0 whenever candidate k agrees with the incumbent (d = proxy = 0), and the marginal null
        # implies E[d | disagree] <= 0, so the cap needs only the inclusion probability on disagreement events, q_cap,
        # which is a function of the past alone (never of the other candidates' agreement pattern).
        xmin = (M * (2.0 / q_cap - 1.0) if use_pp else M / q_cap)[:, None]
        lam = np.minimum(lam, 0.5 / xmin)
        if EV == "disc":
            lam = lam * (mean > 0)
        logf = np.log1p(lam * X)
        arr = t + delay
        BX[arr] += X
        BX2[arr] += X * X
        BN[arr] += 1.0
        start = pilot
        if t < start:
            pil_sum += X
            pil_cnt += 1.0
        else:
            LF[arr] += logf
        if EV == "shared" and t >= start:
            ev = np.exp(np.clip(logW - logW.max(1, keepdims=True), -30, 0) / 2.0)
            wa = ev / ev.sum(1, keepdims=True)
            LG[arr] += np.log(np.maximum((wa * (1.0 + lam * X)).sum(1), 1e-12))
        if AL == "ctxvar" and Qs is not None:
            wq = np.where(Qs, 1.0 / np.maximum(q, 1e-9), 0.0)
            resid = (dt - (hk if use_pp else 0.0)) ** 2
            vsum[nd, ar] += wq * resid.mean(1)
            vcnt[nd, ar] += wq
        logW = logW + LF[t]
        logG = logG + LG[t]
        if seq:
            Lt = st["loss"][:, t, :]
            dp = np.stack(
                [Lt[:, ib] - Lt[:, ia], Lt[:, ia] - Lt[:, ib]], -1
            )  # >0: first (second) of the pair better
            Xp = (Qs / np.maximum(q, 1e-9))[:, None, None] * dp
            m_, s2_ = c1p / (cnp + 1), c2p / (cnp + 1)
            lamp = np.minimum(
                np.where(s2_ > 0, np.maximum(m_, 0) / np.maximum(s2_, 1e-12), 0.0), 0.5 / (M / frac)
            )
            BXp[arr] += Xp
            LFp[arr] += np.log1p(lamp * Xp)
            logP = logP + LFp[t]
            cum_loss += np.where(Qs[:, None], Lt / np.maximum(q, 1e-9)[:, None], 0.0)
            better = logP >= thr_pair
            for pi_, (a_, b_) in enumerate(pairs):
                elim[:, b_] |= better[:, pi_, 0]
                elim[:, a_] |= better[:, pi_, 1]
            newc = elim[:, 0] & (cert_t == T)
            if newc.any():
                prom = np.where(newc, np.where(elim, np.inf, cum_loss).argmin(1), prom)
                cert_t = np.where(newc, t, cert_t)
                n_el = np.where(newc, elim.sum(1), n_el)
        else:
            thr_k = np.log(1.0 / (alpha * alpha_w)) if EV == "alpha_alloc" else thr
            hit = (logW >= thr_k) & (cross == T)
            if EV == "cs":
                nn = np.maximum(cn, 1.0)
                hit = (
                    c1 / nn
                    - (2 * M / frac)
                    * np.sqrt(np.log(np.pi**2 * nn**2 / (3 * alpha / Kc)) / (2 * nn))
                    > 0
                ) & (cross == T)
            if EV == "disc":
                hit &= mean > 0
            if EV == "shared":
                hit = (logG >= thr)[:, None] & (cross == T) & (logW == logW.max(1, keepdims=True))
            cross = np.where(hit, t, cross)
            lab_cross = np.where(hit, spent[:, None], lab_cross)
    wall = time.perf_counter() - t_start
    gaps = st["gap"]
    out = {
        "runtime_s": wall,
        "peak_rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0,
        "labels_total": spent,
    }
    if seq:
        pc = np.where(prom >= 1, prom - 1, 0)
        cert = (cert_t < T) & (prom >= 1)
        ga = gaps[pc, np.minimum(cert_t, T - 1)]
        out.update(
            cert_t=cert_t,
            certified=cert,
            gap_at=np.where(cert, ga, np.nan),
            n_elim=n_el,
            false_reject_any=cert & (ga <= 1e-9),
            labels_at_cert=spent,
        )
        return out
    tau = cross.min(1)
    first = cross.argmin(1)
    cert = tau < T
    gk = np.take_along_axis(
        np.broadcast_to(gaps[None], (S, Kc, T)), np.minimum(cross, T - 1)[:, :, None], 2
    )[:, :, 0]
    out.update(
        cert_t=tau,
        certified=cert,
        gap_at=np.where(cert, gaps[first, np.minimum(tau, T - 1)], np.nan),
        false_reject_any=((cross < T) & (gk <= 1e-9)).any(1),
        labels_at_cert=np.where(cert, lab_cross[ar, first], spent),
        n_elim=np.zeros(S),
    )
    return out


def score(res: dict, st: dict) -> dict:
    """Per-seed certification outcomes against the true current gaps."""
    gaps = st["gap"]
    T = gaps.shape[1]
    cert = res["certified"]
    ga = res["gap_at"]
    best_at = gaps.max(0)[np.minimum(res["cert_t"], T - 1)]
    incorrect = cert & (ga <= 1e-9)
    correct = cert & (ga > 1e-9) & (ga >= 0.5 * best_at)
    return {
        "certified": cert,
        "incorrect": incorrect,
        "correct": correct,
        "false_reject_any": res["false_reject_any"],
        "cert_t": res["cert_t"],
        "labels_at_cert": res["labels_at_cert"],
        "n_elim": res["n_elim"],
        "gap_at": ga,
        "best_gap_exists": bool((gaps.max(0) > 1e-9).any()),
    }
