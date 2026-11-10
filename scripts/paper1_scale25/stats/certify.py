"""Per-dataset lower bounds for the relative cost reduction r_d under chronological dependence.

Definitions (per dataset d; episodes k = 1..n are consecutive non-overlapping chunks of one stream):
    b_k  reference net cost of episode k (seed-averaged, any common scale, e.g. 100*net/T)
    a_k  new-method net cost of episode k (same scale)
    D_k = b_k - a_k
    r_d = 100 * E[D] / E[b]         (percent reduction of mean net cost, positive = new is better)

Estimator: r_hat = 100 * mean(D) / mean(b).

Block-Fieller bound (`fieller_lower`; the PRIMARY bound `primary_lower` is the minimum over two prespecified block lengths): cluster-robust Fieller bound.
    Partition the n episodes into n_B contiguous non-overlapping blocks (sizes m or m+1, n_B = n // m,
    m = block_length(n) = max(2, ceil(n**(1/3)))). For rho in R let z_k(rho) = D_k - rho*b_k. The
    block-cluster variance of mean(z) is V(rho) = n_B/(n_B-1) * sum_j (Z_j - n_j*zbar)^2 / n^2, and
    t(rho) = zbar(rho)/sqrt(V(rho)). The one-sided (1-alpha) lower bound is the smallest rho with
    t(rho) <= t_{1-alpha, n_B-1}; this is a quadratic in rho (Fieller), solved in closed form. If the
    denominator is not significantly positive (b-bar^2 <= c^2 V_bb) the bound is -inf.

Validity: asymptotically valid under strong mixing of (D_k, b_k) with blocks long enough that block sums are
approximately independent; finite-sample t_{n_B-1} reference is a conservative-in-practice small-sample
correction. Simulation (sim_coverage.py) checks coverage; there is no distribution-free guarantee.

Other methods (comparison only): `fieller_lower(..., crit="normal")`, `mbb_lower` (studentised circular
block bootstrap; needs B >> 1/alpha, so it is unusable below alpha ~ 1e-3 at B = 20000).
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

ALPHA_TOTAL = 0.05


def alpha_i(i: int, total: float = ALPHA_TOTAL) -> float:
    """Level for chronological attempt index i >= 1: total / (i (i+1)); sums to `total` over all i."""
    if int(i) != i or i < 1:
        raise ValueError("attempt index must be an integer >= 1")
    return total / (i * (i + 1))


def block_length(n: int, min_block: int = 2) -> int:
    """Prespecified block length depending on n only: max(2, ceil(n^(1/3)))."""
    return max(min_block, math.ceil(n ** (1.0 / 3.0)))


def _blocks(n: int, m: int):
    n_b = n // m
    if n_b < 3:
        raise ValueError(f"need at least 3 blocks (n={n}, block length={m})")
    return np.array_split(np.arange(n), n_b)


def _cluster_moments(A, B, m):
    """Cluster-robust moments of (D, b) for 2-D arrays (R x n). Returns dict of (R,) arrays."""
    A, B = np.atleast_2d(A), np.atleast_2d(B)
    n = B.shape[1]
    D = B - A
    blocks = _blocks(n, m)
    n_b = len(blocks)
    sb = np.stack([B[:, ix].sum(1) for ix in blocks], 1)
    sd = np.stack([D[:, ix].sum(1) for ix in blocks], 1)
    nj = np.array([len(ix) for ix in blocks], float)
    bbar, dbar = B.mean(1), D.mean(1)
    eb = sb - nj * bbar[:, None]
    ed = sd - nj * dbar[:, None]
    k = n_b / (n_b - 1) / n**2
    return {
        "n": n,
        "n_b": n_b,
        "bbar": bbar,
        "dbar": dbar,
        "Vbb": k * (eb * eb).sum(1),
        "VDD": k * (ed * ed).sum(1),
        "VDb": k * (ed * eb).sum(1),
    }


def block_lengths(n: int) -> tuple:
    """Prespecified block lengths of the PRIMARY bound: cube-root and square-root rules (deduplicated)."""
    return tuple(sorted({block_length(n), max(2, math.ceil(math.sqrt(n)))}))


def crit_value(alpha: float, df: int, crit: str = "t") -> float:
    return float(stats.t.isf(alpha, df) if crit == "t" else stats.norm.isf(alpha))


def fieller_lower_batch(A, B, alpha: float, m: int | None = None, crit: str = "t"):
    """Vectorised Fieller lower bound (percent) for each row of A, B. Returns (L, r_hat, se) in percent."""
    A, B = np.atleast_2d(np.asarray(A, float)), np.atleast_2d(np.asarray(B, float))
    m = block_length(B.shape[1]) if m is None else m
    q = _cluster_moments(A, B, m)
    c = crit_value(alpha, q["n_b"] - 1, crit)
    bb, dd = q["bbar"], q["dbar"]
    aq = bb**2 - c**2 * q["Vbb"]
    bq = dd * bb - c**2 * q["VDb"]
    cq = dd**2 - c**2 * q["VDD"]
    disc = np.maximum(bq**2 - aq * cq, 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        low = np.where(aq > 0, (bq - np.sqrt(disc)) / aq, -np.inf)
    rho = dd / bb
    v = q["VDD"] - 2 * rho * q["VDb"] + rho**2 * q["Vbb"]
    se = 100 * np.sqrt(np.maximum(v, 0)) / np.abs(bb)
    return 100 * low, 100 * rho, se


def fieller_lower(a, b, alpha: float, m: int | None = None, crit: str = "t") -> dict:
    """Lower (1-alpha) bound for r_d (percent) from one dataset's episode series (chronological order)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("a and b must be 1-D arrays of equal length")
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("non-finite episode values")
    m = block_length(len(b)) if m is None else m
    L, r, se = fieller_lower_batch(a[None], b[None], alpha, m, crit)
    return {
        "L": float(L[0]),
        "r_hat": float(r[0]),
        "se": float(se[0]),
        "alpha": alpha,
        "n": len(b),
        "block_len": m,
        "n_blocks": len(b) // m,
        "crit": crit,
    }


def primary_lower_batch(A, B, alpha: float):
    """PRIMARY bound: the minimum of the block-Fieller bounds over `block_lengths(n)`.

    A minimum of valid lower bounds covers at least as often as each of them (its miss event is contained in
    each one's miss event), so the primary bound is at least as well calibrated as the best single block
    length and protects against under-estimated dependence. Returns (L, r_hat, se, binding_block_length)."""
    A, B = np.atleast_2d(np.asarray(A, float)), np.atleast_2d(np.asarray(B, float))
    best = None
    for m in block_lengths(B.shape[1]):
        L, r, se = fieller_lower_batch(A, B, alpha, m)
        if best is None:
            best = (L, r, se, np.full(len(L), m))
        else:
            take = L < best[0]
            best = (
                np.where(take, L, best[0]),
                r,
                np.where(take, se, best[2]),
                np.where(take, m, best[3]),
            )
    return best


def primary_lower(a, b, alpha: float) -> dict:
    """PRIMARY per-dataset lower (1-alpha) bound for r_d in percent (see `primary_lower_batch`)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("a and b must be 1-D arrays of equal length")
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("non-finite episode values")
    L, r, se, m = primary_lower_batch(a[None], b[None], alpha)
    return {
        "L": float(L[0]),
        "r_hat": float(r[0]),
        "se": float(se[0]),
        "alpha": alpha,
        "n": len(b),
        "block_len": int(m[0]),
        "n_blocks": len(b) // int(m[0]),
        "crit": "t",
        "block_set": block_lengths(len(b)),
    }


def mbb_lower(a, b, alpha: float, B: int = 20000, m: int | None = None, seed: int = 0) -> dict:
    """Studentised circular block bootstrap (percentile-t) lower bound; requires B*alpha >= ~20."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = len(b)
    m = block_length(n) if m is None else m
    rng = np.random.default_rng(seed)
    nblk = math.ceil(n / m)
    starts = rng.integers(0, n, size=(B, nblk))
    idx = ((starts[:, :, None] + np.arange(m)[None, None, :]) % n).reshape(B, -1)[:, :n]
    A_, B_ = a[idx], b[idx]
    # studentise each resample with its own non-overlapping blocks (they are the sampled blocks)
    _, r_star, se_star = fieller_lower_batch(A_, B_, 0.5, m)
    _, r_hat, se_hat = fieller_lower_batch(a[None], b[None], 0.5, m)
    t_star = (r_star - r_hat[0]) / np.maximum(se_star, 1e-12)
    qv = float(np.quantile(t_star, 1 - alpha))
    return {
        "L": float(r_hat[0] - qv * se_hat[0]),
        "r_hat": float(r_hat[0]),
        "se": float(se_hat[0]),
        "alpha": alpha,
        "n": n,
        "block_len": m,
        "boot_B": B,
    }


def paired_series(records, cand: str, ref: str, stream: str, scale_T: float | None = 2000.0):
    """Seed-averaged, episode-ordered (a, b) arrays for one stream from a records DataFrame.

    `records` has columns stream, ep, seed, config_id, net. Averages over seeds per (ep, config), requires
    both policies on every episode, returns 100*net/T arrays sorted by ep.
    """
    d = records[records.stream == stream]
    m = d.groupby(["ep", "config_id"]).net.mean().unstack("config_id").sort_index()
    if cand not in m or ref not in m or m[[cand, ref]].isna().any().any():
        raise ValueError("candidate or reference missing on some episode")
    s = 100.0 / scale_T if scale_T else 1.0
    return m[cand].to_numpy() * s, m[ref].to_numpy() * s
