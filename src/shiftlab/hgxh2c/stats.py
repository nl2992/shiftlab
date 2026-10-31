"""Statistics for the HG x H2c protocol (docs/hgxh2c/PROTOCOL.md).

Sign convention: gain = J_base - J_cand (cost), positive favours the candidate.
"""

import numpy as np
import pandas as pd
from scipy.stats import beta

COLUMNS = [
    "method_id", "cell_id", "family", "seed", "partition",
    "tau",  # change time, -1 if null world
    "alarm_B", "alarm_C", "alarm_J",  # int step, -1 if no alarm
    "n_queries", "J_cost", "excess_cost_before_alarm",
    "null_B", "null_C",  # bool: that track's null holds in this world
    "runtime_s",
]  # fmt: skip
NULL_GUARANTEED = ("null_stationary", "null_boundary")  # null_ar is stress only
EMPIRICAL_ALARM = ("cusum", "ph", "page_hinkley")  # not anytime-valid


def clopper_pearson(k, n, conf=0.95):
    a = 1 - conf
    lo = 0.0 if k == 0 else float(beta.ppf(a / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a / 2, k + 1, n - k))
    return lo, hi


def paired_cluster_bootstrap(df, a_col, b_col, cluster="cell_id", unit="seed", n_boot=4000, seed=0):
    """Candidate a vs baseline b: gain = b - a. Cells resampled, then seeds within each cell.

    The statistic is the equal-weight mean over cells of the per-cell mean gain.
    p_one_sided tests H0: mean gain <= 0.
    """
    X = (
        (df[b_col] - df[a_col])
        .groupby([df[cluster], df[unit]])
        .mean()
        .unstack(unit)
        .to_numpy(float)
    )
    C, S = X.shape
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    step = max(1, int(2e7 // (C * S)))
    for i in range(0, n_boot, step):
        m = min(step, n_boot - i)
        cells = rng.integers(0, C, (m, C))
        seeds = rng.integers(0, S, (m, C, S))
        out[i : i + m] = np.nanmean(X[cells[:, :, None], seeds], axis=2).mean(axis=1)
    mean = float(np.nanmean(X, axis=1).mean())
    lo, hi = np.quantile(out, [0.025, 0.975])
    return {
        "mean": mean,
        "lo": float(lo),
        "hi": float(hi),
        "p_one_sided": float((1 + (out <= 0).sum()) / (n_boot + 1)),
    }


def holm(pvals):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m, run, out = len(items), 0.0, {}
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def intersection_union(results, alpha=0.05):
    """results: {baseline: dict with p_one_sided or p}. Pass iff every baseline is beaten."""
    ps = [r.get("p_one_sided", r.get("p")) for r in results.values()]
    p = max(ps)
    return {"pass_": bool(p < alpha), "p": float(p)}


def summarise(df, T, alpha=0.05, window=800):
    """Per (method_id, cell_id) table. Misses count as delay T - tau; alarms before tau are not detections."""
    d = df.copy()
    d["null_J"] = d["null_B"] & d["null_C"]
    cols = {}
    for t in "BCJ":
        null, alarm = d[f"null_{t}"].astype(bool), d[f"alarm_{t}"]
        harm = ~null & (d["tau"] >= 0)
        hit = harm & (alarm >= d["tau"]) & (alarm <= d["tau"] + window)
        cols[f"harm_{t}"] = harm
        cols[f"hit_{t}"] = hit
        cols[f"dly_{t}"] = np.where(
            harm, np.where(alarm >= d["tau"], alarm - d["tau"], T - d["tau"]), 0
        )
        cols[f"dly_{t}"] = np.where(harm & ~(alarm >= d["tau"]), T - d["tau"], cols[f"dly_{t}"])
        cols[f"null_{t}"] = null
        cols[f"fa_{t}"] = null & (alarm >= 0)
    g = pd.concat(
        [
            d[["method_id", "cell_id", "family", "J_cost", "n_queries"]],
            pd.DataFrame(cols, index=d.index),
        ],
        axis=1,
    )
    s = g.groupby(["method_id", "cell_id"]).agg(
        family=("family", "first"), n=("J_cost", "size"), J_cost=("J_cost", "mean"), labels=("n_queries", "mean"),
        **{f"{k}_{t}": (f"{k}_{t}", "sum") for t in "BCJ" for k in ("harm", "hit", "dly", "null", "fa")},
    ).reset_index()  # fmt: skip
    for t in "BCJ":
        h, nn = s[f"harm_{t}"].replace(0, np.nan), s[f"null_{t}"].replace(0, np.nan)
        s[f"power_{t}"] = s[f"hit_{t}"] / h
        s[f"delay_{t}"] = s[f"dly_{t}"] / h
        s[f"far_{t}"] = s[f"fa_{t}"] / nn
        ci = [
            clopper_pearson(int(k), int(m), 1 - alpha) if m > 0 else (np.nan, np.nan)
            for k, m in zip(s[f"fa_{t}"], s[f"null_{t}"])
        ]
        s[f"far_lo_{t}"], s[f"far_hi_{t}"] = [c[0] for c in ci], [c[1] for c in ci]
    return s.drop(columns=[f"{k}_{t}" for t in "BCJ" for k in ("harm", "hit", "dly", "null", "fa")])


def _flag(m, empirical):
    m = m.lower()
    return any(m.startswith(e) or f"_{e}" in m for e in empirical)


def _registry():
    from shiftlab.hgxh2c.baselines import REGISTRY

    return {k: {"track": v[1], "fidelity": v[2], "notes": v[3]} for k, v in REGISTRY.items()}


def frontier(
    summary,
    metrics=("J_cost", "power", "delay"),
    alpha=0.05,
    empirical=EMPIRICAL_ALARM,
    tracks="BCJ",
    registry=None,
):
    """Non-dominated methods per (track, cell) on harm cells (J_cost lower, power higher, delay lower).

    registry: {method_id: {track, fidelity, notes}} (default: hgxh2c.baselines.REGISTRY). Track T admits only
    methods registered for T, scored on track-T power/delay/FAR. DIFFERENT_NULL and INVALID_OR_UNSUPPORTED
    methods never enter; they are listed under "references". A method is excluded for a track if its FAR
    Clopper-Pearson lower bound exceeds alpha in a guaranteed null family (NULL_GUARANTEED).
    Empirical-alarm methods stay eligible but flagged.
    Returns {"frontier": {"T|cell": [ids]}, "excluded": {"T": [ids]}, "flagged": [ids], "references": [ids]}.
    """
    reg = registry or _registry()
    refs = sorted(
        m
        for m, r in reg.items()
        if "DIFFERENT_NULL" in r["notes"] or r["fidelity"] == "INVALID_OR_UNSUPPORTED"
    )
    out = {
        "frontier": {},
        "excluded": {},
        "flagged": sorted({m for m in summary.method_id.unique() if _flag(m, empirical)}),
        "references": refs,
    }
    sign = {"J_cost": 1.0, "power": -1.0, "delay": 1.0}
    for t in tracks:
        elig = {m for m, r in reg.items() if r["track"] == t} - set(refs)
        sm = summary[summary.method_id.isin(elig)]
        nulls = sm[sm.family.isin(NULL_GUARANTEED)]
        bad = set(nulls.loc[nulls[f"far_lo_{t}"] > alpha, "method_id"])
        out["excluded"][t] = sorted(bad)
        harm = sm[
            ~sm.family.isin(NULL_GUARANTEED) & ~sm.method_id.isin(bad) & sm[f"power_{t}"].notna()
        ]
        for cell, h in harm.groupby("cell_id"):
            M = np.column_stack(
                [sign[m] * h[m if m == "J_cost" else f"{m}_{t}"].to_numpy(float) for m in metrics]
            )
            M = np.nan_to_num(M, nan=np.inf)
            keep = [
                not any((M[j] <= M[i]).all() and (M[j] < M[i]).any() for j in range(len(M)) if j != i)
                for i in range(len(M))
            ]  # fmt: skip
            out["frontier"][f"{t}|{cell}"] = h.method_id[keep].tolist()
    return out
