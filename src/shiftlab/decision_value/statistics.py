"""Paired bootstrap over independent episodes, Holm correction, protocol reversal classifier."""

from __future__ import annotations

import numpy as np


def _resample_means(arrs, B: int, seed: int, chunk: int = 1000):
    """Yield bootstrap means of each array in ``arrs`` using shared episode resamples."""
    n = len(arrs[0])
    rng = np.random.default_rng(seed)
    out = [np.empty(B) for _ in arrs]
    for lo in range(0, B, chunk):
        hi = min(B, lo + chunk)
        idx = rng.integers(0, n, size=(hi - lo, n))
        for o, a in zip(out, arrs):
            o[lo:hi] = a[idx].mean(axis=1)
    return out


def _summ(point, boot, alpha):
    lo, hi = np.quantile(boot, [alpha / 2, 1 - alpha / 2])
    p = min(1.0, 2 * min((boot <= 0).mean(), (boot >= 0).mean()) + 1.0 / (len(boot) + 1))
    return {"mean": float(point), "lo": float(lo), "hi": float(hi), "p": float(p)}


def paired_bootstrap_diff(a, b, B: int = 10_000, seed: int = 0, alpha: float = 0.05) -> dict:
    """Mean of per-episode difference a-b with percentile CI and two-sided bootstrap p."""
    d = np.asarray(a, float) - np.asarray(b, float)
    (bm,) = _resample_means([d], B, seed)
    return _summ(d.mean(), bm, alpha)


def relative_diff(a, b, denom, B: int = 10_000, seed: int = 0, alpha: float = 0.05) -> dict:
    """(mean(a)-mean(b)) / mean(denom); denominator is stated by the caller (e.g. never-switch cost)."""
    a, b, den = (np.asarray(v, float) for v in (a, b, denom))
    ba, bb, bd = _resample_means([a, b, den], B, seed)
    return _summ((a.mean() - b.mean()) / den.mean(), (ba - bb) / bd, alpha)


def holm(pvals) -> np.ndarray:
    """Holm-Bonferroni adjusted p-values (step-down, monotone)."""
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj


def classify_reversal(
    power_a, power_b, delay_a, delay_b, cost_a, cost_b, mme: float, B: int = 10_000, seed: int = 0
) -> dict:
    """Protocol definition for monitor A over B (per-episode paired arrays on common episodes).

    detection advantage: power_a - power_b >= 0.05 with CI excluding 0, OR delay_a at least 10% lower than
    delay_b (relative to mean delay_b) with CI excluding 0; cost disadvantage: mean(cost_a - cost_b) >= mme
    with CI excluding 0.  reversal = detection advantage AND cost disadvantage.
    """
    pw = paired_bootstrap_diff(power_a, power_b, B, seed)
    dl = relative_diff(delay_a, delay_b, delay_b, B, seed + 1)
    cs = paired_bootstrap_diff(cost_a, cost_b, B, seed + 2)
    det_power = pw["mean"] >= 0.05 and pw["lo"] > 0
    det_delay = dl["mean"] <= -0.10 and dl["hi"] < 0
    cost_dis = cs["mean"] >= mme and cs["lo"] > 0
    return {
        "power_diff": pw,
        "delay_rel_diff": dl,
        "cost_diff": cs,
        "detection_advantage": bool(det_power or det_delay),
        "detection_via": [k for k, v in (("power", det_power), ("delay", det_delay)) if v],
        "cost_disadvantage": bool(cost_dis),
        "reversal": bool((det_power or det_delay) and cost_dis),
    }
