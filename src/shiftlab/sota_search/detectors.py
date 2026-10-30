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


def _family(sim):
    return sim["world"].family


def source_moments(kind: str):
    """Nominal (source) mean/std of decision cost and Brier loss, from a large independent source stream."""
    if kind not in _SOURCE_CACHE:
        s = g.simulate(g.World(T=4000, family=kind), 100, 999)
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
    mu, sd = source_moments(_family(sim))["loss"]
    S, T = obs.shape
    st, out = np.zeros(S), np.zeros((S, T))
    for t in range(T):
        st = np.where(avail[:, t] > 0, np.maximum(0.0, st + (obs[:, t] - mu) / sd - slack), st)
        out[:, t] = st
    return out


def page_hinkley(sim, frac=0.1, delay=5, lseed=0, delta=0.1, **_):
    obs, avail = _labeled_obs(sim, frac, delay, lseed)
    mu, sd = source_moments(_family(sim))["loss"]
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
    mu, sd = source_moments(_family(sim))["loss"]
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
    mu, _ = source_moments(_family(sim))["loss"]
    n = np.cumsum(avail, 1)
    mean = np.cumsum(obs, 1) / np.maximum(n, 1)
    stat = mean - mu - tol - hoeffding_width(n, g.FN_COST)
    return np.where(n > 0, stat, -np.inf)


def _pp_increment(sim, q_mask, q, risk):
    """Prediction-powered per-event increment X_s = Rhat + Q/q (R - Rhat) - r0 for risk 'cost' or 'brier'."""
    p = sim["p"]
    act = (p >= g.TAU).astype(float)
    if risk == "cost":
        proxy = act * (1 - p) * g.FP_COST + (1 - act) * p * g.FN_COST
        r, bound_m = sim["loss"], g.FN_COST
    else:
        proxy = p * (1 - p)
        r, bound_m = sim["brier"], 1.0
    r0 = source_moments(_family(sim))["loss" if risk == "cost" else "brier"][0]
    x = proxy + (q_mask / q) * (r - proxy) - r0
    return x, bound_m


def _pp_parts(sim, frac, lseed, risk, q, mask, tol, uniform_cap=False):
    S, T = sim["y"].shape
    qv = np.full((S, T), frac) if q is None else q
    qm = (label_mask(sim, frac, lseed) if mask is None else mask).astype(float)
    p = sim["p"]
    act = (p >= g.TAU).astype(float)
    if risk == "cost":
        proxy = act * (1 - p) * g.FP_COST + (1 - act) * p * g.FN_COST
        r, m = sim["loss"], g.FN_COST
    else:
        proxy, r, m = p * (1 - p), sim["brier"], 1.0
    r0 = source_moments(_family(sim))["loss" if risk == "cost" else "brier"][0]
    x = proxy + (qm / qv) * (r - proxy) - r0 - tol
    loose = m * (2.0 / qv - 1.0) + m  # symmetric worst-case range (initial implementation)
    # one-sided exact minimum of the increment: label queried with zero loss (R=0), predictable from proxy and q
    tight = proxy * (1.0 / qv - 1.0) + r0 + tol
    if uniform_cap:
        # context-free support bound (proxy <= 1/4 for Brier, <= 5/6 for decision cost): the bet then depends on
        # the resolved past only, which is what the marginal-null supermartingale argument needs (doc 02)
        tight = (0.25 if risk == "brier" else 5.0 / 6.0) * (1.0 / qv - 1.0) + r0 + tol
    return x, qv, loose, tight


def pp_eprocess(
    sim,
    frac=0.1,
    delay=5,
    lseed=0,
    tol=0.0,
    risk="cost",
    q=None,
    mask=None,
    tight=False,
    cap=0.5,
    uniform_cap=False,
    **_,
):
    """Betting e-process on the prediction-powered excess-risk increment; log-wealth (S, T).

    ``tight=False`` caps the bet by a symmetric worst-case range (the initial, over-conservative
    implementation); ``tight=True`` caps it by the exact one-sided minimum of the increment, which keeps
    ``1 + lam*X >= 1 - cap > 0`` and therefore the same validity argument.
    """
    x, _qv, loose, tight_b = _pp_parts(sim, frac, lseed, risk, q, mask, tol, uniform_cap)
    bound = tight_b if tight else loose
    T = x.shape[1]
    c1 = shift_time(np.cumsum(x, 1), delay + 1)
    c2 = shift_time(np.cumsum(x**2, 1), delay + 1)
    n = np.maximum(np.arange(T)[None, :] - delay, 0).astype(float)
    mean, second = c1 / (n + 1), c2 / (n + 1)
    lam = np.minimum(
        np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), cap / bound
    )
    log_inc = np.log1p(lam * x)
    return np.cumsum(shift_time(log_inc, delay), 1)


def sr_edetector(
    sim, frac=0.1, delay=5, lseed=0, tol=0.0, risk="cost", q=None, mask=None, cap=0.5, **_
):
    """Shiryaev-Roberts style e-detector: R_t = (1 + R_{t-1}) * f_t with tight-capped betting factors."""
    x, _qv, _loose, tight_b = _pp_parts(sim, frac, lseed, risk, q, mask, tol)
    T = x.shape[1]
    c1 = shift_time(np.cumsum(x, 1), delay + 1)
    c2 = shift_time(np.cumsum(x**2, 1), delay + 1)
    n = np.maximum(np.arange(T)[None, :] - delay, 0).astype(float)
    mean, second = c1 / (n + 1), c2 / (n + 1)
    lam = np.minimum(
        np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), cap / tight_b
    )
    f = shift_time(1.0 + lam * x, delay, fill=1.0)
    out = np.zeros_like(f)
    r = np.zeros(f.shape[0])
    for t in range(T):
        r = (1.0 + r) * f[:, t]
        out[:, t] = r
    return out


def _ewm_cumsum(x, gamma):
    """Discounted running sum c_t = gamma * c_{t-1} + x_t (gamma = 1 is the plain cumulative sum)."""
    if gamma >= 1.0:
        return np.cumsum(x, 1)
    out = np.empty_like(x, dtype=float)
    c = np.zeros(x.shape[0])
    for t in range(x.shape[1]):
        c = gamma * c + x[:, t]
        out[:, t] = c
    return out


_W_BAR: dict = {}


def boundary_weight(p, h, floor):
    logit = np.log(np.clip(p, 1e-9, 1 - 1e-9) / (1 - np.clip(p, 1e-9, 1 - 1e-9)))
    return np.exp(-0.5 * ((logit - np.log(g.TAU / (1 - g.TAU))) / h) ** 2) + floor


def _boundary_q(sim, frac, h, floor):
    key = (h, floor, _family(sim))
    if key not in _W_BAR:
        src = g.simulate(g.World(T=4000, family=_family(sim)), 50, 31337)
        _W_BAR[key] = float(boundary_weight(src["p"], h, floor).mean())
    return np.clip(frac * boundary_weight(sim["p"], h, floor) / _W_BAR[key], 0.02, 1.0)


def pp_fix(
    sim,
    frac=0.1,
    delay=5,
    lseed=0,
    tol=0.0,
    risk="brier",
    gamma=1.0,
    gate_w=None,
    alloc=None,
    cap=0.5,
    uniform_cap=False,
    **_,
):
    """Tight-capped prediction-powered e-process with optional fixes (see docs 09_*).

    gamma < 1: discounted predictable Kelly bet (DK). gate_w: set the bet to zero unless the discounted
    mean decision-cost increment (same labels) is positive (HG). alloc = (h, floor): query probability
    concentrated near the decision boundary with a matching propensity (BD). With gamma = 1, no gate and
    no allocation this is exactly ``pp_eprocess(..., tight=True)``. Every change acts on the predictable
    bet or query probability only, so the one-sided cap keeps 1 + lam * X >= 1 - cap > 0.
    """
    S, T = sim["y"].shape
    if alloc is None:
        qv, qm = np.full((S, T), frac), None
    else:
        qv = _boundary_q(sim, frac, *alloc)
        qm = (np.random.default_rng(lseed).random((S, T)) < qv).astype(float)
    x, qv, _loose, tight_b = _pp_parts(
        sim, frac, lseed, risk, qv if alloc is not None else None, qm, tol, uniform_cap
    )
    mask = qm if qm is not None else label_mask(sim, frac, lseed).astype(float)
    sim["_labels"] = np.cumsum(mask, 1)
    ones = np.ones_like(x)
    c1 = shift_time(_ewm_cumsum(x, gamma), delay + 1)
    c2 = shift_time(_ewm_cumsum(x**2, gamma), delay + 1)
    n = shift_time(_ewm_cumsum(ones, gamma), delay + 1)
    mean, second = c1 / (n + 1), c2 / (n + 1)
    lam = np.minimum(
        np.where(second > 0, np.maximum(mean, 0) / np.maximum(second, 1e-12), 0.0), cap / tight_b
    )
    if gate_w is not None:
        xc, _q, _l, _t = _pp_parts(
            sim, frac, lseed, "cost", qv if alloc is not None else None, qm, tol
        )
        gg = 1.0 - 1.0 / gate_w
        gmean = shift_time(_ewm_cumsum(xc, gg), delay + 1) / (
            shift_time(_ewm_cumsum(ones, gg), delay + 1) + 1
        )
        lam = lam * (gmean > 0)
    return np.cumsum(shift_time(np.log1p(lam * x), delay), 1)


def fix_brier(sim, **kw):
    return pp_fix(sim, risk="brier", **kw)


def fix_cost(sim, **kw):
    return pp_fix(sim, risk="cost", **kw)


def pprm(sim, **kw):
    return pp_eprocess(sim, risk="brier", **kw)


def pp_cost(sim, **kw):
    return pp_eprocess(sim, risk="cost", **kw)


def pprm_tight(sim, **kw):
    return pp_eprocess(sim, risk="brier", tight=True, **kw)


def pp_cost_tight(sim, **kw):
    return pp_eprocess(sim, risk="cost", tight=True, **kw)


def sr_cost_tight(sim, **kw):
    return sr_edetector(sim, risk="cost", **kw)


def sr_brier_tight(sim, **kw):
    return sr_edetector(sim, risk="brier", **kw)


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


def pp_mixture(sim, frac=0.1, delay=5, lseed=0, tol=0.0, risk="brier", k=8, cap=0.5, **_):
    """Equal-weight mixture over ``k`` fixed bets on the uniform-cap PP increment (LOCAL_HEURISTIC adaptation of
    the standard mixture-of-bets e-process; valid under the marginal null because every bet is a constant)."""
    x, _q, _l, bound = _pp_parts(sim, frac, lseed, risk, None, None, tol, uniform_cap=True)
    lams = cap / bound[..., None] * (np.arange(1, k + 1) / k)
    logs = np.cumsum(
        shift_time(np.log1p(lams * x[..., None]).transpose(2, 0, 1).reshape(-1, x.shape[1]), delay),
        1,
    )
    logs = logs.reshape(k, *x.shape)
    m = logs.max(0)
    return m + np.log(np.exp(logs - m).mean(0))


def pp_ons(sim, frac=0.1, delay=5, lseed=0, tol=0.0, risk="brier", cap=0.5, **_):
    """Online-Newton-step betting on the uniform-cap PP increment (Cutkosky-Orabona style step; SOURCE_INSPIRED).

    The bet used for step s is fixed before X_s and updated only with labels resolved by s (index <= s - delay).
    """
    x, _q, _l, bound = _pp_parts(sim, frac, lseed, risk, None, None, tol, uniform_cap=True)
    S, T = x.shape
    hi = cap / bound
    lam = np.zeros((S, T))
    cur = np.zeros(S)
    a = np.ones(S)
    logw = np.zeros((S, T))
    acc = np.zeros(S)
    c = 2.0 / (2.0 - np.log(3.0))
    for s in range(T):
        lam[:, s] = cur
        r = s - delay
        if r >= 0:
            z = x[:, r] / (1.0 + lam[:, r] * x[:, r])
            acc = acc + np.log1p(lam[:, r] * x[:, r])
            a = a + z * z
            cur = np.clip(cur + c * z / a, 0.0, hi[:, min(s + 1, T - 1)])
        logw[:, s] = acc
    return logw


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
    "pprm_tight": pprm_tight,
    "pp_cost_tight": pp_cost_tight,
    "sr_cost_tight": sr_cost_tight,
    "sr_brier_tight": sr_brier_tight,
    "fix_brier": fix_brier,
    "fix_cost": fix_cost,
    "pp_mixture": pp_mixture,
    "pp_ons": pp_ons,
}
THEORY_THRESHOLD = {
    "pr_cs": 0.0,
    "pprm": float(np.log(1 / ALPHA)),
    "watch": float(np.log(1 / ALPHA)),
    "pp_cost": float(np.log(1 / ALPHA)),
    "pprm_tight": float(np.log(1 / ALPHA)),
    "pp_cost_tight": float(np.log(1 / ALPHA)),
    "fix_brier": float(np.log(1 / ALPHA)),
    "fix_cost": float(np.log(1 / ALPHA)),
    "pp_mixture": float(np.log(1 / ALPHA)),
    "pp_ons": float(np.log(1 / ALPHA)),
}


def first_cross(stat, thr):
    hit = stat >= thr
    anyhit = hit.any(1)
    return np.where(anyhit, hit.argmax(1), stat.shape[1])
