"""Q1 detectors on synthetic streams. Every detector returns a running statistic (S, T); larger = more evidence.

Provenance labels (VERIFIED_REPRODUCTION, FAITHFUL_ADAPTATION, SOURCE_INSPIRED_BASELINE, LOCAL_HEURISTIC,
ORACLE_ONLY) are in ``META``. None is a verified reproduction: no primary source could be read in this
environment, so source-named methods are SOURCE_INSPIRED_BASELINE at best.

Feedback contract (shared by every label-using detector): each event's label is queried with probability
``frac`` (uniform) via a common random mask, and becomes usable ``delay`` steps later. Unlabeled
detectors (MMD, C2ST, BBSD) see features/predictions only, with no delay.
"""

from __future__ import annotations

import numpy as np

from shiftlab.sota_search import generators as g

ALPHA = 0.05
REF_N = 200
META = {
    "mmd": (
        "SOURCE_INSPIRED_BASELINE",
        "empirical",
        "Gretton et al. 2012; windowed unbiased RBF MMD^2, threshold from null simulation",
    ),
    "c2st": (
        "LOCAL_HEURISTIC",
        "empirical",
        "Lopez-Paz and Oquab 2017 idea with an LDA classifier and a held-out t statistic",
    ),
    "bbsd": (
        "SOURCE_INSPIRED_BASELINE",
        "empirical",
        "Rabanser et al. 2019 idea: KS test on model scores, no multiplicity correction needed (one score)",
    ),
    "cusum": ("SOURCE_INSPIRED_BASELINE", "empirical", "one-sided CUSUM on labeled decision costs"),
    "page_hinkley": (
        "SOURCE_INSPIRED_BASELINE",
        "empirical",
        "Page-Hinkley on labeled decision costs",
    ),
    "twowin": (
        "LOCAL_HEURISTIC",
        "empirical",
        "ADWIN-like two-window mean comparison on labeled costs",
    ),
    "pr_cs": (
        "SOURCE_INSPIRED_BASELINE",
        "theory",
        "Podkopaev-Ramdas style labeled-risk confidence sequence vs nominal risk (stitched Hoeffding)",
    ),
    "pprm": (
        "SOURCE_INSPIRED_BASELINE",
        "theory",
        "PPRM-style prediction-powered predictive-risk (Brier) betting e-process",
    ),
    "watch": (
        "SOURCE_INSPIRED_BASELINE",
        "theory",
        "unweighted conformal test martingale (WATCH without covariate weighting)",
    ),
    "pp_cost": (
        "LOCAL_HEURISTIC",
        "theory",
        "prediction-powered betting e-process on decision cost (Candidate S01 core)",
    ),
}


def shift_time(a, d, fill=0.0):
    """Value of event s becomes available at s + d."""
    if d == 0:
        return a
    out = np.full_like(a, fill, dtype=float)
    out[:, d:] = a[:, :-d]
    return out


def label_mask(sim, frac, seed):
    S, T = sim["y"].shape
    return np.random.default_rng(seed).random((S, T)) < frac


_SOURCE_CACHE: dict = {}


def source_moments(kind: str):
    """Nominal (source) mean/std of decision cost and Brier loss, from a large independent source stream."""
    if kind not in _SOURCE_CACHE:
        s = g.simulate(g.World(T=4000), 100, 999)
        _SOURCE_CACHE[kind] = {
            k: (float(s[k].mean()), float(s[k].std())) for k in ("loss", "brier")
        }
    return _SOURCE_CACHE[kind]


def _pairwise_rbf(a, b, gamma):
    d2 = (a**2).sum(-1)[:, :, None] + (b**2).sum(-1)[:, None, :] - 2 * a @ b.transpose(0, 2, 1)
    return np.exp(-gamma * np.maximum(d2, 0.0))


def mmd(sim, win=100, stride=20, **_):
    x = sim["x"].astype(float)
    S, T, _d = x.shape
    ref = x[:, :REF_N]
    med = np.median(((ref[:, :100, None, :] - ref[:, None, :100, :]) ** 2).sum(-1))
    gamma = 1.0 / (2.0 * med + 1e-12)
    kref = _pairwise_rbf(ref, ref, gamma)
    ref_term = (kref.sum((1, 2)) - np.trace(kref, axis1=1, axis2=2)) / (REF_N * (REF_N - 1))
    idx = list(range(REF_N + win, T + 1, stride))
    vals = []
    for t in idx:
        cur = x[:, t - win : t]
        kcc = _pairwise_rbf(cur, cur, gamma)
        kcr = _pairwise_rbf(cur, ref, gamma)
        vals.append(
            ref_term
            + (kcc.sum((1, 2)) - np.trace(kcc, axis1=1, axis2=2)) / (win * (win - 1))
            - 2 * kcr.mean((1, 2))
        )
    vals = np.stack(vals, 1)
    out = np.full((S, T), -np.inf)
    for j, t in enumerate(idx):
        out[:, min(t, T - 1) :] = vals[:, [j]]
    return out


def c2st(sim, win=100, stride=20, **_):
    x = sim["x"].astype(float)
    S, T, D = x.shape
    ref = x[:, :REF_N]
    idx = list(range(REF_N + win, T + 1, stride))
    out = np.full((S, T), -np.inf)
    h = win // 2
    for t in idx:
        cur = x[:, t - win : t]
        tr_r, te_r, tr_c, te_c = ref[:, :h], ref[:, h : 2 * h], cur[:, :h], cur[:, h:]
        mu_r, mu_c = tr_r.mean(1), tr_c.mean(1)
        centered = np.concatenate([tr_r - mu_r[:, None], tr_c - mu_c[:, None]], 1)
        cov = np.einsum("sni,snj->sij", centered, centered) / (2 * h - 2) + 1e-6 * np.eye(D)
        w = np.linalg.solve(cov, (mu_c - mu_r)[:, :, None])[:, :, 0]
        zr, zc = (te_r * w[:, None]).sum(-1), (te_c * w[:, None]).sum(-1)
        se = np.sqrt(zr.var(1) / h + zc.var(1) / h) + 1e-12
        out[:, min(t, T - 1) :] = ((zc.mean(1) - zr.mean(1)) / se)[:, None]
    return out


def bbsd(sim, win=100, stride=20, **_):
    p = sim["p"]
    S, T = p.shape
    ref = np.sort(p[:, :REF_N], 1)
    idx = list(range(REF_N + win, T + 1, stride))
    out = np.full((S, T), -np.inf)
    for t in idx:
        cur = np.sort(p[:, t - win : t], 1)
        vals = np.empty(S)
        for s in range(S):
            grid = np.concatenate([ref[s], cur[s]])
            vals[s] = np.abs(
                np.searchsorted(ref[s], grid, "right") / REF_N
                - np.searchsorted(cur[s], grid, "right") / win
            ).max()
        out[:, min(t, T - 1) :] = vals[:, None]
    return out


def _labeled_obs(sim, frac, delay, lseed, key="loss"):
    q = label_mask(sim, frac, lseed)
    v = sim[key] * q
    return shift_time(v, delay), shift_time(q.astype(float), delay)


def cusum(sim, frac=0.1, delay=5, lseed=0, slack=0.5, **_):
    obs, avail = _labeled_obs(sim, frac, delay, lseed)
    mu, sd = source_moments("c")["loss"]
    S, T = obs.shape
    st, out = np.zeros(S), np.zeros((S, T))
    for t in range(T):
        st = np.where(avail[:, t] > 0, np.maximum(0.0, st + (obs[:, t] - mu) / sd - slack), st)
        out[:, t] = st
    return out


def page_hinkley(sim, frac=0.1, delay=5, lseed=0, delta=0.1, **_):
    obs, avail = _labeled_obs(sim, frac, delay, lseed)
    mu, sd = source_moments("c")["loss"]
    S, T = obs.shape
    m, mmin, out = np.zeros(S), np.zeros(S), np.zeros((S, T))
    for t in range(T):
        upd = avail[:, t] > 0
        m = np.where(upd, m + (obs[:, t] - mu) / sd - delta, m)
        mmin = np.minimum(mmin, m)
        out[:, t] = m - mmin
    return out


def twowin(sim, frac=0.1, delay=5, lseed=0, w=60, **_):
    obs, avail = _labeled_obs(sim, frac, delay, lseed)
    mu, sd = source_moments("c")["loss"]
    cs, cn = np.cumsum(obs, 1), np.cumsum(avail, 1)
    T = obs.shape[1]
    # mean of the labels seen in the last 'recent' samples is approximated by a fixed time window of length w/frac
    span = int(w / frac)
    lo = np.clip(np.arange(T) - span, 0, None)
    recent_s = cs - cs[:, lo]
    recent_n = np.maximum(cn - cn[:, lo], 1)
    out = (recent_s / recent_n - mu) / (sd / np.sqrt(recent_n))
    out[:, : span + 1] = 0.0
    return out


def hoeffding_width(n, bound):
    n = np.maximum(n, 1.0)
    return bound * np.sqrt(np.log(np.pi**2 * n**2 / (3 * ALPHA)) / (2 * n))


def pr_cs(sim, frac=0.1, delay=5, lseed=0, tol=0.0, **_):
    obs, avail = _labeled_obs(sim, frac, delay, lseed)
    mu, _ = source_moments("c")["loss"]
    n = np.cumsum(avail, 1)
    mean = np.cumsum(obs, 1) / np.maximum(n, 1)
    stat = mean - mu - tol - hoeffding_width(n, g.FN_COST)
    return np.where(n > 0, stat, -np.inf)


def _pp_increment(sim, q_mask, q, risk):
    """Prediction-powered per-event increment X_s = Rhat + Q/q (R - Rhat) - r0 for risk 'cost' or 'brier'."""
    p, y = sim["p"], sim["y"]
    act = (p >= g.TAU).astype(float)
    if risk == "cost":
        proxy = act * (1 - p) * g.FP_COST + (1 - act) * p * g.FN_COST
        r, bound_m = sim["loss"], g.FN_COST
    else:
        proxy = p * (1 - p)
        r, bound_m = sim["brier"], 1.0
    r0 = source_moments("c")["loss" if risk == "cost" else "brier"][0]
    x = proxy + (q_mask / q) * (r - proxy) - r0
    return x, bound_m


def pp_eprocess(sim, frac=0.1, delay=5, lseed=0, tol=0.0, risk="cost", q=None, mask=None, **_):
    """Betting e-process on the prediction-powered excess-risk increment; log-wealth (S, T)."""
    S, T = sim["y"].shape
    qv = np.full((S, T), frac) if q is None else q
    qm = (label_mask(sim, frac, lseed) if mask is None else mask).astype(float)
    x, bm = _pp_increment(sim, qm, qv, risk)
    x = x - tol
    bound = bm * (2.0 / qv - 1.0) + bm
    c1 = shift_time(np.cumsum(x, 1), delay + 1)
    c2 = shift_time(np.cumsum(x**2, 1), delay + 1)
    n = np.maximum(np.arange(T)[None, :] - delay, 0).astype(float)
    mean, second = c1 / (n + 1), c2 / (n + 1)
    lam = np.minimum(
        np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), 0.5 / bound
    )
    log_inc = np.log1p(lam * x)
    return np.cumsum(shift_time(log_inc, delay), 1)


def pprm(sim, **kw):
    return pp_eprocess(sim, risk="brier", **kw)


def pp_cost(sim, **kw):
    return pp_eprocess(sim, risk="cost", **kw)


_CAL = {}


def _cal_scores(n=500):
    if n not in _CAL:
        s = g.simulate(g.World(T=n), 1, 4242)
        _CAL[n] = np.abs(s["y"][0] - s["p"][0])
    return _CAL[n]


def watch(sim, frac=0.1, delay=5, lseed=0, **_):
    """Unweighted conformal test martingale on labeled |y - p| scores (mixture over power calibrators)."""
    cal = np.sort(_cal_scores())
    score = np.abs(sim["y"] - sim["p"])
    rng = np.random.default_rng(lseed + 17)
    ge = (len(cal) - np.searchsorted(cal, score, "left")).astype(float)
    ties = (len(cal) - np.searchsorted(cal, score, "right")).astype(float)
    pval = (ties + rng.random(score.shape) * (ge - ties + 1)) / (len(cal) + 1)
    pval = np.clip(pval, 1e-6, 1.0)
    q = label_mask(sim, frac, lseed)
    eps = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
    logm = np.log(eps[None, None, :]) + (eps[None, None, :] - 1) * np.log(pval)[:, :, None]
    logm = np.where(q[:, :, None], logm, 0.0)
    if delay:
        shifted = np.zeros_like(logm)
        shifted[:, delay:, :] = logm[:, :-delay, :]
        logm = shifted
    cum = np.cumsum(logm, 1)
    mx = cum.max(2)
    return mx + np.log(np.exp(cum - mx[:, :, None]).mean(2))


DETECTORS = {
    "mmd": mmd,
    "c2st": c2st,
    "bbsd": bbsd,
    "cusum": cusum,
    "page_hinkley": page_hinkley,
    "twowin": twowin,
    "pr_cs": pr_cs,
    "pprm": pprm,
    "watch": watch,
    "pp_cost": pp_cost,
}
THEORY_THRESHOLD = {
    "pr_cs": 0.0,
    "pprm": float(np.log(1 / ALPHA)),
    "watch": float(np.log(1 / ALPHA)),
    "pp_cost": float(np.log(1 / ALPHA)),
}


def first_cross(stat, thr):
    hit = stat >= thr
    anyhit = hit.any(1)
    return np.where(anyhit, hit.argmax(1), stat.shape[1])
