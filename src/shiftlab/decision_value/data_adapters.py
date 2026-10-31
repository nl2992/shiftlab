"""Setting-A adapters: real paired loss series -> ``EpisodeBatch`` objects (development windows only).

A *pair* is two models scored on the same realised outcomes (incumbent ``l0``, challenger ``l1``), so
both action losses are identified (Setting A). This module contains no data loading: callers supply
validation-window and development-window paired losses (the reserved windows are never passed in).

Train-only scaling
------------------
Monitors need bounded inputs (``|l0 - l1| <= 1``). The scale is fitted on the validation-window paired
differences only:  ``s = 1 / (c * sd(l0 - l1))`` with ``c = 4``; ``l1s = s*l1`` and
``l0s = l1s + clip(s*(l0 - l1), -1, 1)`` (clipping only touches the monitor input; costs are always
evaluated on the *raw* losses). The spec and the number of clipped dev steps are recorded.

Where the variance comes from (one real series cannot give independent replications)
-----------------------------------------------------------------------------------
* ``actual``  : the realised dev series, ``n_q`` independent query masks (q < 1). Captures query
  (acquisition) randomness only; for q = 1 it is a single deterministic episode.
* ``roll``    : rolling origins (start offsets every ``step`` steps, horizon ``H`` < T). Captures temporal
  sampling of the series, but episodes overlap heavily (effective n ~ T/H), so intervals use a
  moving-block bootstrap over the origin sequence.
* ``boot``    : moving-block bootstrap of the *joint* paired losses (block ``b``). Synthetic series of
  length T with the within-block dependence of the dev window; regimes longer than ``b`` are broken, so
  it understates persistence (and therefore monitor value). Robustness check, not an estimate of the
  dev-window value.

Thresholds are calibrated on a declared *unconditional stationary null* built from the validation
window (block bootstrap of the validation paired differences recentred to mean 0 for the paired target;
block bootstrap of validation incumbent losses for the incumbent target). This is NOT the conditional
excess-cost null of the research charter: it is marginal, assumes stationarity within the validation
window and the validation window's dependence, and is not claimed valid under adaptation.

Deployable diagnostics recipe (fixed BEFORE any dev outcome is replayed; validation window only)
-------------------------------------------------------------------------------------------------
D_t = l0_t - l1_t (raw units), n = len(D).
 1. Delta_hat = mean(D); sigma_hat = sd(D); NW_se = Newey-West (lag 7) standard error of the mean.
 2. rho_k = sample ACF at lags 1, 7, 14, 28; half-life h = ln(0.5)/ln(rho_1) if 0 < rho_1 < 1 else 0.
 3. Smoothed advantage m_t = centred rolling mean of D (window w = 7, min_periods 4).
    Opportunity runs = maximal runs of consecutive steps with m_t > sigma_hat / sqrt(w)  (1 s.e. of an
    iid w-mean).  L_hat = mean run length in steps (0 if no runs).  Delta_opp = mean of D over the steps
    inside runs.  I_hat = Delta_opp^2 / (2 sigma_hat^2)  (Gaussian equal-variance KL per labelled event).
 4. kappa_hat(d, q) = max(L_hat - d, 0) * q * I_hat / ln(1/alpha), alpha = 0.05.
 5. Reference distribution: the same statistics on 200 uniform time-permutations of D (destroys
    persistence, keeps marginals); report the observed value's percentile and the permutation p95.
Selection bias note: runs are chosen where m_t is high, so Delta_opp is inflated for pure noise; the
permutation reference quantifies that inflation and kappa_hat should only be read relative to it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np

from .contracts import EpisodeBatch
from .evaluation import count_switches
from .feedback import LabelQueue, make_mask
from .monitors import Target

SCALE_C = 4.0
ALPHA = 0.05


# ------------------------------------------------------------------ data containers
@dataclass
class PairSeries:
    name: str
    role: str  # headline | control | null_control
    incumbent: str
    challenger: str
    loss_unit: str
    step: str  # 'day' | 'hour'
    val0: np.ndarray
    val1: np.ndarray
    dev0: np.ndarray
    dev1: np.ndarray
    dev_labels: list = field(default_factory=list)  # one label per dev step (ISO string)
    meta: dict = field(default_factory=dict)
    setting: str = "A"


@dataclass(frozen=True)
class ScaleSpec:
    s: float
    c: float
    sigma_val: float
    mean_val: float
    n_val: int

    def to_dict(self):
        return asdict(self)


def fit_scaling(val0, val1, c: float = SCALE_C) -> ScaleSpec:
    d = np.asarray(val0, float) - np.asarray(val1, float)
    sd = float(d.std(ddof=1))
    if not np.isfinite(sd) or sd <= 0:
        raise ValueError("validation paired differences have zero variance")
    return ScaleSpec(s=1.0 / (c * sd), c=c, sigma_val=sd, mean_val=float(d.mean()), n_val=len(d))


def apply_scaling(l0, l1, spec: ScaleSpec):
    """Return (l0s, l1s, n_clipped). Monitor input only; never used for cost."""
    l0, l1 = np.asarray(l0, float), np.asarray(l1, float)
    l1s = spec.s * l1
    raw = spec.s * (l0 - l1)
    dif = np.clip(raw, -1.0, 1.0)
    return l1s + dif, l1s, int((np.abs(raw) > 1.0).sum())


def fit_incumbent_cap(val0, mult: float = 1.25) -> float:
    """Cap B for the incumbent-risk target (validation window only): l0 / B clipped to [0, 1] keeps
    x = l0 - r0 within [-1, 1]. The paired scaling cannot be used there because s*l0 can exceed 1."""
    return float(mult * np.max(np.asarray(val0, float)))


def apply_incumbent_scaling(l0, B: float):
    """Returns (clipped scaled incumbent loss in [0,1], n_clipped)."""
    z = np.asarray(l0, float) / B
    return np.minimum(z, 1.0), int((z > 1.0).sum())


# ------------------------------------------------------------------ episode sets
@dataclass
class EpisodeSet:
    raw0: np.ndarray  # (n, T) raw incumbent loss (cost units)
    raw1: np.ndarray
    s0: np.ndarray  # scaled (monitor input, paired target)
    s1: np.ndarray
    kind: str  # actual | roll | boot
    info: dict = field(default_factory=dict)
    si: np.ndarray | None = None  # incumbent-target scaled incumbent loss, same indexing as s0

    @property
    def n(self):
        return self.raw0.shape[0]

    @property
    def T(self):
        return self.raw0.shape[1]


def block_indices(rng, T_src: int, T_out: int, n: int, b: int) -> np.ndarray:
    """Moving-block bootstrap indices (n, T_out): blocks of length b start uniformly in [0, T_src-b]."""
    b = min(int(b), T_src)
    nb = -(-T_out // b)
    starts = rng.integers(0, T_src - b + 1, size=(n, nb))
    idx = (starts[:, :, None] + np.arange(b)[None, None, :]).reshape(n, nb * b)
    return idx[:, :T_out]


def actual_set(pair_raw0, pair_raw1, s0, s1, n: int, si=None) -> EpisodeSet:
    tile = lambda a: np.tile(np.asarray(a, float)[None, :], (n, 1))
    return EpisodeSet(
        tile(pair_raw0),
        tile(pair_raw1),
        tile(s0),
        tile(s1),
        "actual",
        {"n_masks": n},
        None if si is None else tile(si),
    )


def roll_set(raw0, raw1, s0, s1, H: int, step: int, si=None) -> EpisodeSet:
    T = len(raw0)
    offs = np.arange(0, T - H + 1, step)
    g = lambda a: np.stack([np.asarray(a, float)[o : o + H] for o in offs])
    return EpisodeSet(
        g(raw0),
        g(raw1),
        g(s0),
        g(s1),
        "roll",
        {"offsets": offs.tolist(), "H": H, "step": step},
        None if si is None else g(si),
    )


def boot_set(raw0, raw1, s0, s1, b: int, n: int, seed, si=None) -> EpisodeSet:
    rng = np.random.default_rng(seed)
    T = len(raw0)
    idx = block_indices(rng, T, T, n, b)
    g = lambda a: np.asarray(a, float)[idx]
    return EpisodeSet(
        g(raw0), g(raw1), g(s0), g(s1), "boot", {"block": b, "n": n}, None if si is None else g(si)
    )


def episode_batch(es: EpisodeSet, q: float, seed, target: str = "paired") -> EpisodeBatch:
    """Operational batch. For the incumbent target the monitor sees the incumbent-scaled loss (l1 is carried
    along but unused by incumbent monitors and by the Permanent/Hold controllers)."""
    rng = np.random.default_rng(seed)
    l0 = es.si if (target == "incumbent" and es.si is not None) else es.s0
    return EpisodeBatch(l0, es.s1, make_mask(rng, es.n, es.T, q))


# ------------------------------------------------------------------ null / calibration
def null_batch(val_s0, val_s1, target: str, n: int, T: int, b: int, q: float, seed) -> EpisodeBatch:
    """Declared stationary null from the validation window. paired: block-resample the validation paired
    difference recentred to mean 0 (E x = 0 on the boundary of H0: E x <= 0); incumbent: block-resample
    validation incumbent losses (the monitor's own reference risk r0 is estimated inside each episode)."""
    rng = np.random.default_rng(seed)
    idx = block_indices(rng, len(val_s0), T, n, b)
    if target == "paired":
        dv = np.asarray(val_s0, float) - np.asarray(val_s1, float)
        dv = dv - dv.mean()
        l1 = np.asarray(val_s1, float)[idx]
        l0 = l1 + dv[idx]
    else:
        l0, l1 = np.asarray(val_s0, float)[idx], np.asarray(val_s1, float)[idx]
    return EpisodeBatch(l0, l1, make_mask(rng, n, T, q))


def null_maxima_horizons(factory, batch: EpisodeBatch, d: int, horizons) -> dict:
    """Per-episode max of the monitor statistic over the first h steps, for each h in ``horizons``
    (same procedure as calibration.null_maxima, which only supports a single horizon)."""
    n = batch.n
    mon = factory(n)
    queue, target = LabelQueue(batch, d), Target(mon.target, n, mon.cal)
    hs = sorted({int(h) for h in horizons})
    mx, out = np.full(n, -np.inf), {}
    for s in range(max(hs)):
        x, v = target.transform(queue.at(s))
        mon.update(x, v)
        mx = np.maximum(mx, mon.statistic)
        if s + 1 in hs:
            out[s + 1] = mx.copy()
    return out


def calibrate_horizons(
    factory,
    val_s0,
    val_s1,
    target,
    q,
    d,
    horizons,
    b,
    alpha=ALPHA,
    n_cal=2000,
    chunk=500,
    seed=5_100_000,
    fresh_seed=5_200_000,
    n_fresh=500,
):
    """Thresholds per horizon (1-alpha 'higher' quantile of the null max) and the fresh-seed null alarm rate."""
    Tmax = max(horizons)
    acc = {h: [] for h in horizons}
    for c in range(-(-n_cal // chunk)):
        nb = null_batch(
            val_s0, val_s1, target, min(chunk, n_cal - c * chunk), Tmax, b, q, [seed, c]
        )
        m = null_maxima_horizons(factory, nb, d, horizons)
        for h in horizons:
            acc[h].append(m[h])
    thr = {
        h: float(np.quantile(np.concatenate(acc[h]), 1 - alpha, method="higher")) for h in horizons
    }
    nb = null_batch(val_s0, val_s1, target, n_fresh, Tmax, b, q, [fresh_seed])
    fm = null_maxima_horizons(factory, nb, d, horizons)
    fresh = {h: float((fm[h] > thr[h]).mean()) for h in horizons}
    return thr, fresh


# ------------------------------------------------------------------ cost parts and identities
def cost_parts(actions: np.ndarray, raw0: np.ndarray, raw1: np.ndarray):
    """(sum of realised raw loss of the deployed action, number of switches) per episode."""
    a = actions.astype(bool)
    return np.where(a, raw1, raw0).sum(axis=1), count_switches(actions)


def hold_triggers(alarm: np.ndarray, H: int) -> np.ndarray:
    """Replay of the Hold(H) trigger logic from the alarm stream alone (pause during hold, no trigger at the
    reverting step). Independent re-implementation used for the identity check."""
    n, T = alarm.shape
    until = np.full(n, -1)
    trig = np.zeros((n, T), bool)
    for s in range(T):
        t = alarm[:, s] & ~(s < until) & ~(until == s)
        trig[:, s] = t
        until = np.where(t, s + H, until)
    return trig


def identity_value(
    kind: str, alarm: np.ndarray, actions: np.ndarray, raw0, raw1, c_s: float, H: int = 0
):
    """Realised-loss version of P1 (permanent) / P4 (hold) / interval form (reverse) in the engine's
    0-indexed convention (alarm at decision step s acts at step s):
      permanent: V = sum_{t>=S} D_t - c_s 1{S<=T-1},  S = first alarm step
      hold(H)  : V = sum over trigger alarms s of [ sum_{t=s}^{min(s+H,T)-1} D_t - c_s (1 + 1{s+H<=T-1}) ]
      reverse  : V = sum_{t: a_t=1} D_t - c_s * (#changes), from the switch times of ``actions``
    with D = raw0 - raw1.  Returns V (n,)."""
    D = np.asarray(raw0, float) - np.asarray(raw1, float)
    n, T = D.shape
    C = np.concatenate([np.zeros((n, 1)), np.cumsum(D, axis=1)], axis=1)  # C[:, k] = sum_{t<k} D
    if kind == "permanent":
        has = alarm.any(axis=1)
        S = np.where(has, alarm.argmax(axis=1), T)
        return (C[:, T] - C[np.arange(n), S]) - c_s * has
    if kind == "hold":
        trig = hold_triggers(alarm, H)
        s_idx = np.arange(T)[None, :]
        end = np.minimum(s_idx + H, T)
        block = np.take_along_axis(C, np.broadcast_to(end, (n, T)), axis=1) - C[:, :T]
        nsw = 1 + (s_idx + H <= T - 1)
        return (trig * (block - c_s * nsw)).sum(axis=1)
    if kind == "reverse":
        a = actions.astype(np.int64)
        ns = count_switches(actions)
        return (a * D).sum(axis=1) - c_s * ns
    raise ValueError(kind)


# ------------------------------------------------------------------ deployable diagnostics
def _acf(x: np.ndarray, k: int) -> float:
    x = x - x.mean()
    den = float((x * x).sum())
    return float((x[:-k] * x[k:]).sum() / den) if den > 0 and len(x) > k else float("nan")


def _nw_se(x: np.ndarray, lag: int = 7) -> float:
    x = x - x.mean()
    n = len(x)
    g0 = float((x * x).sum() / n)
    s = g0
    for k in range(1, min(lag, n - 1) + 1):
        s += 2 * (1 - k / (lag + 1)) * float((x[:-k] * x[k:]).sum() / n)
    return float(np.sqrt(max(s, 0.0) / n))


def _runs(D: np.ndarray, w: int):
    n = len(D)
    kern = np.ones(w)
    num = np.convolve(D, kern, mode="same")
    cnt = np.convolve(np.ones(n), kern, mode="same")
    m = num / cnt
    ok = cnt >= (w + 1) // 2
    sig = D.std(ddof=1)
    flag = ok & (m > sig / np.sqrt(w))
    lens, inside = [], []
    i = 0
    while i < n:
        if flag[i]:
            j = i
            while j < n and flag[j]:
                j += 1
            lens.append(j - i)
            inside.extend(range(i, j))
            i = j
        else:
            i += 1
    return lens, np.array(inside, int)


def _recipe_core(D: np.ndarray, w: int = 7):
    sig = float(D.std(ddof=1))
    lens, inside = _runs(D, w)
    if len(lens) == 0:
        return {"L_hat": 0.0, "n_runs": 0, "frac_in_runs": 0.0, "Delta_opp": 0.0, "I_hat": 0.0}
    dopp = float(D[inside].mean())
    return {
        "L_hat": float(np.mean(lens)),
        "n_runs": len(lens),
        "frac_in_runs": float(len(inside) / len(D)),
        "Delta_opp": dopp,
        "I_hat": dopp**2 / (2 * sig**2),
    }


def kappa_hat(L_hat: float, I_hat: float, d: int, q: float, alpha: float = ALPHA) -> float:
    return max(L_hat - d, 0.0) * q * I_hat / np.log(1.0 / alpha)


def deployable_diagnostics(
    val0,
    val1,
    d_grid=(1, 7),
    q_grid=(0.25, 1.0),
    w: int = 7,
    n_perm: int = 200,
    seed: int = 20261030,
) -> dict:
    D = np.asarray(val0, float) - np.asarray(val1, float)
    sig = float(D.std(ddof=1))
    rho = {f"acf_lag{k}": _acf(D, k) for k in (1, 7, 14, 28)}
    r1 = rho["acf_lag1"]
    half = float(np.log(0.5) / np.log(r1)) if 0 < r1 < 1 else 0.0
    core = _recipe_core(D, w)
    out = {
        "n_val": len(D),
        "Delta_hat": float(D.mean()),
        "sigma_hat": sig,
        "NW_se": _nw_se(D),
        "t_stat_NW": float(D.mean() / _nw_se(D)),
        "Delta_hat_in_sigma": float(D.mean() / sig),
        **rho,
        "half_life_steps": half,
        "recipe": core,
        "recipe_params": {"w": w, "alpha": ALPHA, "n_perm": n_perm},
    }
    rng = np.random.default_rng(seed)
    perm = [_recipe_core(rng.permutation(D), w) for _ in range(n_perm)]
    out["perm_null"] = {
        "L_hat_p95": float(np.quantile([p["L_hat"] for p in perm], 0.95)),
        "I_hat_p95": float(np.quantile([p["I_hat"] for p in perm], 0.95)),
        "L_hat_pct_rank": float(np.mean([p["L_hat"] <= core["L_hat"] for p in perm])),
        "I_hat_pct_rank": float(np.mean([p["I_hat"] <= core["I_hat"] for p in perm])),
    }
    out["kappa_hat"] = {}
    for d in d_grid:
        for q in q_grid:
            k = kappa_hat(core["L_hat"], core["I_hat"], d, q)
            kp = np.array([kappa_hat(p["L_hat"], p["I_hat"], d, q) for p in perm])
            out["kappa_hat"][f"d{d}_q{q}"] = {
                "kappa_hat": float(k),
                "perm_p95": float(np.quantile(kp, 0.95)),
                "pct_rank_vs_perm": float((kp <= k).mean()),
            }
    return out
