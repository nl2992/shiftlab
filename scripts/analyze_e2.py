"""Registered E2 analysis: H-B1a, H-B1b, H-B2, validity stop rule, power, mechanism check.

``confirm`` evaluates the registered tests. Rows from the development block are analysed only
under the label DEVELOPMENT (descriptive) and never as confirmatory evidence.
``power`` computes the McNemar/non-inferiority/bootstrap sample sizes from development rows.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, binomtest, norm, spearmanr

FWER = 0.025  # one-sided family-wise level used throughout
MARGIN = -0.05  # non-inferiority margin in detection proportion
HORIZON = 2400
BOOT_B = 10_000
BOOT_SEED = 20261028
GATED_PRIMARY = "gated_ht_paced"
ENGINE = "fixed08"
H1_CELLS = {"b1_r0.02": 0.02, "b1_r0.05": 0.05}
H1B_CELL = "b1_r0.20"
H2_CELLS = {"b2_i": "ni", "b2_iii": "ni", "b2_ii": "superior"}


def mcnemar_exact_p(wins: int, losses: int) -> float:
    """One-sided exact McNemar: P(X >= wins) for X ~ Bin(wins + losses, 1/2)."""
    n = wins + losses
    return 1.0 if n == 0 else float(binomtest(wins, n, 0.5, alternative="greater").pvalue)


def holm(pvalues: dict[str, float], alpha: float = FWER) -> dict[str, bool]:
    ordered = sorted(pvalues, key=pvalues.get)
    out = dict.fromkeys(pvalues, False)
    for rank, key in enumerate(ordered):
        if pvalues[key] <= alpha / (len(ordered) - rank):
            out[key] = True
        else:
            break
    return out


def _wilson(k: float, n: int, z: float) -> tuple[float, float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def newcombe_lower(a: int, b: int, c: int, d: int, alpha: float) -> float:
    """Newcombe (1998, method 10) one-sided lower bound for p1 - p2, paired proportions.

    ``a`` both succeed, ``b`` only arm 1, ``c`` only arm 2, ``d`` neither; p1 = (a+b)/n,
    p2 = (a+c)/n. Wilson limits with the continuity-corrected phi correlation adjustment.
    """
    n = a + b + c + d
    z = float(norm.isf(alpha))
    p1, p2 = (a + b) / n, (a + c) / n
    l1, _ = _wilson(a + b, n, z)
    _, u2 = _wilson(a + c, n, z)
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    if denom == 0:
        phi = 0.0
    else:
        diff = a * d - b * c
        numerator = diff - n / 2 if diff > n / 2 else (0.0 if diff >= 0 else diff)
        phi = numerator / np.sqrt(denom)
    return float(
        p1 - p2 - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2))
    )


def ni_pvalue(a: int, b: int, c: int, d: int, margin: float = MARGIN) -> float:
    """Smallest one-sided level at which the Newcombe lower bound exceeds the margin."""
    lo, hi = 1e-14, 0.999
    if newcombe_lower(a, b, c, d, lo) > margin:
        return lo
    if newcombe_lower(a, b, c, d, hi) <= margin:
        return 1.0
    for _ in range(80):
        mid = np.sqrt(lo * hi)
        if newcombe_lower(a, b, c, d, mid) > margin:
            hi = mid
        else:
            lo = mid
    return float(hi)


def paired_table(rows: pd.DataFrame, cell: str, first: str, second: str, engine: str = ENGINE):
    sub = rows[(rows.cell == cell) & (rows.engine == engine) & rows.arm.isin([first, second])]
    wide = sub.pivot(index="seed", columns="arm", values="detected").dropna().astype(bool)
    x, y = wide[first].to_numpy(), wide[second].to_numpy()
    return (
        int((x & y).sum()),
        int((x & ~y).sum()),
        int((~x & y).sum()),
        int((~x & ~y).sum()),
    )


def bootstrap_ratio_upper(num: np.ndarray, den: np.ndarray, seed: int = BOOT_SEED, b: int = BOOT_B):
    num, den = np.asarray(num, float), np.asarray(den, float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(len(num), size=(b, len(num)))
    ratio = num[idx].mean(axis=1) / np.maximum(den[idx].mean(axis=1), 1e-12)
    return float(np.quantile(ratio, 1 - FWER)), float(num.mean() / den.mean())


def validity_stop(rows: pd.DataFrame, alpha_each: float = 0.05 / 8) -> list[dict]:
    """Withdraw any (arm, engine) whose pre-onset alarm count exceeds its exact 0.05 bound."""
    out = []
    for (arm, engine), g in rows.groupby(["arm", "engine"]):
        k, n = int(g.false_alarm_pre_onset.sum()), len(g)
        p = float(binomtest(k, n, 0.05, alternative="greater").pvalue)
        out.append(
            {
                "arm": arm,
                "engine": engine,
                "pre_onset_alarms": k,
                "streams": n,
                "rate": k / n,
                "exact_p_rate_gt_0.05": p,
                "withdrawn": p < alpha_each,
            }
        )
    return out


def mechanism(rows: pd.DataFrame) -> dict:
    """Held-out check: fixed-window label count vs a design-parameter baseline (descriptive)."""
    m = rows[(rows.arm == "gated_ht_fixed") & (rows.engine == ENGINE)].copy()
    m = m[m.cell.str.startswith("mech_")]
    if m.empty:
        return {}
    rate = m.cell.str.extract(r"_r([0-9.]+)$")[0].astype(float)
    delay = np.where(
        m.first_alarm.notna(),
        np.maximum(m.first_alarm - m.onset, 0),
        HORIZON - m.onset,
    )
    m["y"] = np.log1p(delay)
    m["log_rate"] = np.log(rate)
    m["severity"] = m.cell.str.extract(r"_s([0-9.]+)_")[0].astype(float)
    m["log_window"] = np.log1p(m.window_labels)
    held = m.cell.isin(["mech_s1.0_r0.05", "mech_s2.0_r0.05"])
    train, test = m[~held], m[held]
    # Mechanism predictor: the fixed-window label count (plus intercept). Baseline predictor: the
    # nominal design parameters only (log budget rate and severity), no label counts.
    specs = {
        "mechanism_window_labels": ["log_window"],
        "baseline_rate_severity": ["log_rate", "severity"],
    }
    out = {}
    for name, cols in specs.items():
        design = np.column_stack([np.ones(len(train)), train[cols].to_numpy()])
        coef = np.linalg.lstsq(design, train.y.to_numpy(), rcond=None)[0]
        pred = np.column_stack([np.ones(len(test)), test[cols].to_numpy()]) @ coef
        constant = np.ptp(pred) == 0
        out[name] = {
            "heldout_rmse_log1p_delay": float(np.sqrt(np.mean((test.y.to_numpy() - pred) ** 2))),
            "heldout_spearman": None if constant else float(spearmanr(pred, test.y).statistic),
            "coefficients": [float(c) for c in coef],
            "n_train": len(train),
            "n_heldout": len(test),
        }
    out["constant_baseline_rmse"] = float(np.sqrt(np.mean((m[held].y - m[~held].y.mean()) ** 2)))
    return out


def confirm(rows: pd.DataFrame) -> dict:
    result: dict = {}
    p1a = {}
    detail = {}
    for cell in H1_CELLS:
        a, b, c, d = paired_table(rows, cell, GATED_PRIMARY, "uniform_ht")
        p1a[cell] = mcnemar_exact_p(b, c)
        detail[cell] = {
            "both": a,
            "gated_only": b,
            "uniform_only": c,
            "neither": d,
            "p": p1a[cell],
            "n": a + b + c + d,
        }
    reject = holm(p1a)
    result["H-B1a"] = {"cells": detail, "holm_reject": reject, "supported": all(reject.values())}
    cell = rows[(rows.cell == H1B_CELL) & (rows.engine == ENGINE)]
    wide = cell.pivot(index="seed", columns="arm", values="labels_to_alarm_or_horizon").dropna()
    upper, estimate = bootstrap_ratio_upper(wide[GATED_PRIMARY], wide["uniform_ht"])
    result["H-B1b"] = {
        "ratio_of_means": estimate,
        "upper_97.5": upper,
        "supported": upper < 0.5,
        "n": len(wide),
    }
    p2, d2 = {}, {}
    for name, kind in H2_CELLS.items():
        if kind == "ni":  # arm 1 = fixed, arm 2 = paced; p1 - p2 > margin
            a, b, c, d = paired_table(rows, name, "gated_ht_fixed", "gated_ht_paced")
            p2[name] = ni_pvalue(a, b, c, d)
            d2[name] = {
                "test": "non-inferiority fixed vs paced (Newcombe paired)",
                "fixed_minus_paced": (b - c) / (a + b + c + d),
                "lower_97.5": newcombe_lower(a, b, c, d, FWER),
            }
        else:  # paced > fixed
            a, b, c, d = paired_table(rows, name, "gated_ht_paced", "gated_ht_fixed")
            p2[name] = mcnemar_exact_p(b, c)
            d2[name] = {"test": "McNemar paced > fixed", "paced_only": b, "fixed_only": c}
        d2[name].update(both=a, only_first=b, only_second=c, neither=d, p=p2[name])
    reject2 = holm(p2)
    result["H-B2"] = {"cells": d2, "holm_reject": reject2}
    result["validity"] = validity_stop(rows)
    result["mechanism_descriptive"] = mechanism(rows)
    return result


def mcnemar_power(n: int, psi: float, delta: float, alpha: float) -> float:
    """Exact power: discordant count M ~ Bin(n, delta); wins | M ~ Bin(M, psi);
    reject when the exact one-sided p <= alpha."""
    m = np.arange(n + 1)
    pm = binom.pmf(m, n, delta)
    power = 0.0
    for k, w in zip(m, pm, strict=True):
        if w < 1e-14:
            continue
        crit = None
        for wins in range(k + 1):  # smallest wins with p <= alpha
            if mcnemar_exact_p(wins, k - wins) <= alpha:
                crit = wins
                break
        power += w * (0.0 if crit is None else float(binom.sf(crit - 1, k, psi)))
    return power


def smallest_n(power_fn, target=0.9, start=5, stop=60_000) -> int | None:
    n = start
    while n <= stop:
        if power_fn(n) >= target:
            lo, hi = max(start, n // 2), n
            while lo < hi:
                mid = (lo + hi) // 2
                if power_fn(mid) >= target:
                    hi = mid
                else:
                    lo = mid + 1
            return lo
        n = int(n * 1.5) + 1
    return None


def _n_for(psi: float, delta: float, alpha: float) -> int | None:
    return smallest_n(lambda n: mcnemar_power(n, psi, delta, alpha))


def ni_power(table: tuple[int, int, int, int], n: int, alpha: float, reps=400, seed=1) -> float:
    probs = np.array(table, float)
    probs = (probs + 0.5) / (probs.sum() + 2)  # Jeffreys-style smoothing of dev cells
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(reps):
        a, b, c, d = rng.multinomial(n, probs)
        hits += ni_pvalue(int(a), int(b), int(c), int(d)) <= alpha
    return hits / reps


def power_plan(rows: pd.DataFrame, floor: int = 1000) -> dict:
    out: dict = {"floor_per_primary_cell": floor, "formula": "see protocol section 7"}
    z80 = float(norm.isf(0.2))
    for cell in H1_CELLS:
        a, b, c, d = paired_table(rows, cell, GATED_PRIMARY, "uniform_ht")
        n_dev = a + b + c + d
        delta, psi = (b + c) / n_dev, (b / (b + c) if b + c else 0.5)
        dl = _wilson(b + c, n_dev, z80)[0]
        pl = _wilson(b, b + c, z80)[0] if b + c else 0.5
        alpha = FWER / 2  # Bonferroni level for 2 tests, sufficient for Holm
        out[cell] = {
            "dev_table": [a, b, c, d],
            "delta": delta,
            "psi": psi,
            "delta_lower80": dl,
            "psi_lower80": pl,
            "alpha_adj": alpha,
            "n_plugin": _n_for(psi, delta, alpha),
            "n_pessimistic": _n_for(pl, dl, alpha),
        }
    alpha3 = FWER / 3
    for name, kind in H2_CELLS.items():
        if kind == "superior":
            a, b, c, d = paired_table(rows, name, "gated_ht_paced", "gated_ht_fixed")
            n_dev = a + b + c + d
            delta, psi = (b + c) / n_dev, (b / (b + c) if b + c else 0.5)
            dl = _wilson(b + c, n_dev, z80)[0]
            pl = _wilson(b, b + c, z80)[0] if b + c else 0.5
            out[name] = {
                "dev_table": [a, b, c, d],
                "delta": delta,
                "psi": psi,
                "delta_lower80": dl,
                "psi_lower80": pl,
                "alpha_adj": alpha3,
                "n_plugin": _n_for(psi, delta, alpha3),
                "n_pessimistic": _n_for(pl, dl, alpha3),
            }
        else:
            tab = paired_table(rows, name, "gated_ht_fixed", "gated_ht_paced")
            grid = [50, 100, 200, 400, 800, 1600]
            powers = {n: ni_power(tab, n, alpha3) for n in grid}
            ok = [n for n in grid if powers[n] >= 0.9]
            out[name] = {
                "dev_table": list(tab),
                "alpha_adj": alpha3,
                "power_by_n": powers,
                "n_ni": ok[0] if ok else None,
            }
    # H-B1b: bootstrap-of-bootstrap power by resampling development streams.
    cell = rows[(rows.cell == H1B_CELL) & (rows.engine == ENGINE)]
    wide = cell.pivot(index="seed", columns="arm", values="labels_to_alarm_or_horizon").dropna()
    g, u = wide[GATED_PRIMARY].to_numpy(), wide["uniform_ht"].to_numpy()
    rng = np.random.default_rng(7)
    res = {}
    for n in (50, 100, 200, 400, 1000):
        ok = 0
        for _ in range(100):
            i = rng.integers(len(g), size=n)
            ok += (
                bootstrap_ratio_upper(g[i], u[i], seed=int(rng.integers(1 << 30)), b=1000)[0] < 0.5
            )
        res[n] = ok / 100
    out["H-B1b"] = {"power_by_n": res, "dev_ratio": float(g.mean() / u.mean())}
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["confirm", "power"])
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = pd.read_parquet(args.rows)
    manifest = json.loads((args.rows.parent / "manifest.json").read_text(encoding="utf-8"))
    status = (
        "CONFIRMATORY"
        if manifest["block"] == "confirmation"
        else "DEVELOPMENT (descriptive, not confirmatory)"
    )
    body = confirm(rows) if args.mode == "confirm" else power_plan(rows)
    payload = {"status": status, "manifest": manifest, "result": body}
    args.out.write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
    print(json.dumps(body, indent=2, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
