"""Registered E2 analysis: grid selection, H-B1a, H-B1b, H-B2, validity stop rule, mechanism.

Modes:
- ``select-grid``: development-only selection of the burst cells from the e2_dev_grid rows; writes
  the locked design (cells, order, n, multiplicity) that the confirmation reads.
- ``confirm``: the registered tests. Rows from the development block are analysed only under the
  label DEVELOPMENT (descriptive) and never as confirmatory evidence. Incomplete cells, duplicate
  rows, missing arm/engine combinations, NaN statistics and (with a locked design) seed sets that
  differ from the registered ones are rejected with an error.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binom, binomtest, norm, spearmanr

FWER = 0.025  # one-sided family-wise level used throughout
MARGIN = -0.05  # non-inferiority margin in detection proportion (H-B2, H-B1b joint condition)
HORIZON = 2400
BOOT_B = 10_000
BOOT_SEED = 20261028
GATED_PRIMARY = "gated_ht_paced"
ENGINE = "fixed08"
H1_CELLS = {"b1_r0.02": 0.02, "b1_r0.05": 0.05}
H1B_CELL = "b1_r0.20"
# Grid-selection rules (development only, locked before confirmation).
BAND = (0.20, 0.80)  # paced detection band for classes (i) and (iii)
MIN_ONSET_SHARE = 0.95  # share of streams in which the planned harm is material
MAX_PER_CLASS = 2
EXHAUSTION_BANDS = {
    "A_none": ((0.0, 0.2), 0.1),
    "B_partial": ((0.2, 0.8), 0.5),
    "C_full": ((0.8, 1.0), 0.9),
}
FLOOR_N, CEIL_N, CORE_B1_N, MECH_N = 1000, 3000, 1000, 500


def registered_combos(cells) -> dict[str, frozenset]:
    """Registered (arm, engine) set of each cell known to the E2 module."""
    from shiftlab.dive import e2_acquisition_pacing as e2

    out = {}
    for cell in cells:
        spec = e2.CELLS.get(cell)
        if spec is None:
            continue
        engines = ("fixed08",) if spec.role == "grid" else e2.ENGINES
        out[cell] = frozenset((a, e) for a in spec.arms for e in engines)
    return out


def validate_rows(
    rows: pd.DataFrame,
    expected: dict[str, list[int]] | None = None,
    combos: dict[str, frozenset] | None = None,
) -> None:
    """Reject duplicate rows, ragged cells, NaN statistics and unregistered seed sets."""
    keys = ["cell", "seed", "arm", "engine"]
    if rows.duplicated(keys).any():
        raise ValueError("duplicate (cell, seed, arm, engine) rows")
    stats = ["detected", "false_alarm_pre_onset", "labels_to_alarm_or_horizon", "dollars"]
    if rows[stats].isna().any().any():
        raise ValueError("NaN in a registered statistic")
    for cell, g in rows.groupby("cell"):
        combos_by_seed = g.groupby("seed").apply(
            lambda x: frozenset(zip(x.arm, x.engine, strict=True)), include_groups=False
        )
        if combos_by_seed.nunique() != 1:
            raise ValueError(f"cell {cell!r} is incomplete: seeds differ in their arm/engine rows")
        if combos is not None and cell in combos and combos_by_seed.iloc[0] != combos[cell]:
            raise ValueError(f"cell {cell!r}: arm/engine set differs from the registered set")
        if expected is not None and sorted(g.seed.unique()) != sorted(expected.get(cell, [])):
            raise ValueError(f"cell {cell!r}: seeds differ from the registered set")
    if expected is not None and set(expected) != set(rows.cell.unique()):
        raise ValueError("cells differ from the registered set")


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
    """Smallest one-sided level at which the Newcombe lower bound exceeds the margin.

    The lower bound is searched only on alpha in (0, 0.5], i.e. z >= 0, where it is monotone
    (non-increasing in z). At alpha = 0.5 the bound equals the point estimate ``p1 - p2``; if even
    that does not exceed the margin the p-value is reported as 1.0 (any p above 0.5 can never
    reject at a level of at most 0.025). A test passes at level ``alpha`` exactly when this p-value
    is at most ``alpha`` (the decision rule is the registered-level bound compared with the margin).
    """
    lo, hi = 1e-14, 0.5
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
    wide = sub.pivot(index="seed", columns="arm", values="detected")  # raises on duplicates
    if set(wide.columns) != {first, second} or wide.isna().any().any() or wide.empty:
        raise ValueError(f"cell {cell!r}: arms {first!r}/{second!r} are not paired on every seed")
    x, y = wide[first].to_numpy(bool), wide[second].to_numpy(bool)
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


def validity_stop(rows: pd.DataFrame, alpha_each: float | None = None) -> list[dict]:
    """Withdraw any (arm, engine) whose pre-onset alarm count exceeds its exact 0.05 bound."""
    out = []
    groups = list(rows.groupby(["arm", "engine"]))
    alpha_each = alpha_each or 0.05 / len(groups)  # Bonferroni over arm-engine pairs
    for (arm, engine), g in groups:
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
    out["note"] = "retrospective association (post-onset window count), not an online predictor"
    out["constant_baseline_rmse"] = float(np.sqrt(np.mean((m[held].y - m[~held].y.mean()) ** 2)))
    return out


def cell_summary(rows: pd.DataFrame, cell: str, engine: str = ENGINE) -> dict:
    """Per-arm descriptive summary: detection, false alarms, spend, reserve survival."""
    g = rows[(rows.cell == cell) & (rows.engine == engine)]
    out = {}
    for arm, a in g.groupby("arm"):
        out[arm] = {
            "n": len(a),
            "detection": float(a.detected.mean()),
            "false_alarm_pre_onset": float(a.false_alarm_pre_onset.mean()),
            "labels_to_alarm_or_horizon": float(a.labels_to_alarm_or_horizon.mean()),
            "realised_dollars": float(a.dollars.mean()),
            "dollars_pre_onset": float(a.dollars_pre_onset.mean()),
            "dollars_post_onset": float(a.dollars_post_onset.mean()),
            "reserve_used_frac_pre_onset": float(a.reserve_used_frac_pre_onset.mean()),
            "reserve_exhausted": float(a.reserve_exhausted.mean()),
            "reserve_exhausted_before_onset": float(a.reserve_exhausted_before_onset.mean()),
        }
    return out


def confirm(rows: pd.DataFrame, locked: dict, expected: dict[str, list[int]] | None = None):
    validate_rows(rows, expected, registered_combos(rows.cell.unique()))
    result: dict = {}
    p1a, detail = {}, {}
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
            "summary": cell_summary(rows, cell),
        }
    reject = holm(p1a)
    result["H-B1a"] = {
        "framing": "gating ablation (DISCERN replication under this contract); expected spend "
        "is matched, realised spend is reported per arm in each cell summary",
        "cells": detail,
        "holm_reject": reject,
        "supported": all(reject.values()),
    }
    cell = rows[(rows.cell == H1B_CELL) & (rows.engine == ENGINE)]
    wide = cell.pivot(index="seed", columns="arm", values="labels_to_alarm_or_horizon")
    if wide[[GATED_PRIMARY, "uniform_ht"]].isna().any().any():
        raise ValueError("H-B1b: unpaired streams")
    upper, estimate = bootstrap_ratio_upper(wide[GATED_PRIMARY], wide["uniform_ht"])
    a, b, c, d = paired_table(rows, H1B_CELL, GATED_PRIMARY, "uniform_ht")
    detection_lower = newcombe_lower(a, b, c, d, FWER)
    result["H-B1b"] = {
        "quantity": "acquisition expenditure (labels to alarm or horizon, pre-onset included); "
        "not faster detection",
        "ratio_of_means": estimate,
        "upper_97.5": upper,
        "detection_gated_minus_uniform_lower_97.5": detection_lower,
        "joint_condition": f"ratio upper bound < 0.5 AND detection lower bound > {MARGIN}",
        "supported": bool(upper < 0.5 and detection_lower > MARGIN),
        "n": len(wide),
        "summary": cell_summary(rows, H1B_CELL),
    }
    p2, d2 = {}, {}
    for t in locked["h_b2"]:
        name = t["cell"]
        if t["type"] == "ni":  # arm 1 = fixed, arm 2 = paced; p1 - p2 > margin
            a, b, c, d = paired_table(rows, name, "gated_ht_fixed", GATED_PRIMARY)
            p2[name] = ni_pvalue(a, b, c, d)
            d2[name] = {
                "test": "non-inferiority fixed vs paced (Newcombe paired)",
                "fixed_minus_paced": (b - c) / (a + b + c + d),
                "lower_97.5": newcombe_lower(a, b, c, d, FWER),
            }
        else:  # paced > fixed
            a, b, c, d = paired_table(rows, name, GATED_PRIMARY, "gated_ht_fixed")
            p2[name] = mcnemar_exact_p(b, c)
            d2[name] = {"test": "McNemar paced > fixed"}
        d2[name].update(
            both=a,
            only_first=b,
            only_second=c,
            neither=d,
            p=p2[name],
            underpowered=t["underpowered"],
        )
        d2[name]["class"] = t["class"]
        d2[name]["summary"] = cell_summary(rows, name)
    reject2 = holm(p2) if p2 else {}
    result["H-B2"] = {
        "cells": d2,
        "holm_reject": reject2,
        "family_size": len(p2),
        "uninformative_classes": locked["uninformative"],
        "uninformative_note": "no development cell placed paced detection in the band; "
        "registered as UNINFORMATIVE, not support",
    }
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


def ni_power(table: tuple[int, int, int, int], n: int, alpha: float, reps=500, seed=1) -> float:
    probs = np.array(table, float)
    probs = (probs + 0.5) / (probs.sum() + 2)  # Jeffreys-style smoothing of dev cells
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(reps):
        a, b, c, d = rng.multinomial(n, probs)
        hits += ni_pvalue(int(a), int(b), int(c), int(d)) <= alpha
    return hits / reps


def _wilson80(k: int, n: int) -> tuple[float, float]:
    return _wilson(k, n, float(norm.isf(0.2)))


def _ceil100(n: int) -> int:
    return int(-(-n // 100) * 100)


def _size_cell(test_type: str, tab: tuple[int, int, int, int], alpha: float) -> dict:
    """Pessimistic n from 100-stream development discordance (Wilson 80% limits)."""
    a, b, c, d = tab
    total = a + b + c + d
    if test_type == "superior":  # tab = (both, paced only, fixed only, neither)
        dl = _wilson80(b + c, total)[0]
        pl = _wilson80(b, b + c)[0] if b + c else 0.5
        raw = _n_for(pl, dl, alpha) if dl > 0 else None
    else:  # non-inferiority: no true difference, discordance at the Wilson 80% upper limit
        delta = max(_wilson80(b + c, total)[1], 0.02)
        pbar = (a + (b + c) / 2) / total
        half = delta / 2
        base = max(pbar - half, 0.0)
        pessimistic = (round(base * 10_000), round(half * 10_000), round(half * 10_000))
        pessimistic += (10_000 - sum(pessimistic),)
        # Two scenarios, both must reach power 0.9: (1) true difference zero with the Wilson-80%
        # upper discordance; (2) the development table taken at face value (its observed
        # fixed-minus-paced difference, which can be negative).
        raw = next(
            (
                n
                for n in (1000, 1500, 2000, 2500, 3000)
                if ni_power(pessimistic, n, alpha) >= 0.9 and ni_power(tab, n, alpha) >= 0.9
            ),
            None,
        )
    under = raw is None or raw > CEIL_N
    n = CEIL_N if under else min(max(_ceil100(raw), FLOOR_N), CEIL_N)
    return {"n_power": raw, "n": n, "underpowered": bool(under)}


def select_grid(grid: pd.DataFrame, dev: pd.DataFrame) -> dict:
    """Select confirmation burst cells from the development grid and lock the design."""
    validate_rows(grid, None, registered_combos(grid.cell.unique()))
    stats = {}
    for cell, g in grid.groupby("cell"):
        paced = g[g.arm == GATED_PRIMARY]
        fixed = g[g.arm == "gated_ht_fixed"]
        horizon = g[g.arm == "gated_ht_horizon"]
        stats[cell] = {
            "class": cell.split("_")[1],
            "n": len(paced),
            "onset_share": float(paced.onset.notna().mean()),
            "paced_detection": float(paced.detected.mean()),
            "fixed_detection": float(fixed.detected.mean()),
            "horizon_detection": float(horizon.detected.mean()),
            "fixed_exhausted_before_onset": float(fixed.reserve_exhausted_before_onset.mean()),
            "fixed_reserve_used_pre_onset": float(fixed.reserve_used_frac_pre_onset.mean()),
            "paced_reserve_used_pre_onset": float(paced.reserve_used_frac_pre_onset.mean()),
            "pre_onset_false_alarm_paced": float(paced.false_alarm_pre_onset.mean()),
            "fixed_paced_table": list(paired_table(grid, cell, "gated_ht_fixed", GATED_PRIMARY)),
        }
    chosen: list[dict] = []
    uninformative = []
    for tag in ("i", "iii"):
        ok = [
            (abs(v["paced_detection"] - 0.5), name)
            for name, v in stats.items()
            if v["class"] == tag
            and BAND[0] <= v["paced_detection"] <= BAND[1]
            and v["onset_share"] >= MIN_ONSET_SHARE
        ]
        picked = [name for _, name in sorted(ok)[:MAX_PER_CLASS]]
        if not picked:
            uninformative.append(tag)
        chosen += [{"cell": name, "class": tag, "type": "ni"} for name in picked]
    ii = []
    for label, ((lo, hi), centre) in EXHAUSTION_BANDS.items():
        ok = [
            (abs(v["fixed_exhausted_before_onset"] - centre), name)
            for name, v in stats.items()
            if v["class"] == "ii"
            and v["onset_share"] >= MIN_ONSET_SHARE
            and (
                lo <= v["fixed_exhausted_before_onset"] < hi
                or (hi == 1.0 and v["fixed_exhausted_before_onset"] == 1.0)
            )
        ]
        if ok:
            ii.append((label, min(ok)[1]))
    chosen += [
        {"cell": name, "class": "ii", "type": "superior", "band": label} for label, name in ii
    ]
    if not ii:
        uninformative.append("ii")
    alpha = FWER / max(len(chosen), 1)  # Bonferroni level, sufficient for the Holm family
    for t in chosen:
        tab = tuple(stats[t["cell"]]["fixed_paced_table"])
        if t["type"] == "superior":  # (both, paced only, fixed only, neither)
            a, fixed_only, paced_only, d = tab
            tab = (a, paced_only, fixed_only, d)
        t.update(_size_cell(t["type"], tab, alpha))
    order = [*CORE_NAMES, *[t["cell"] for t in chosen]]
    sizes = {name: CORE_B1_N for name in CORE_NAMES if name.startswith("b1_")}
    sizes.update({name: MECH_N for name in CORE_NAMES if name.startswith("mech_")})
    sizes.update({t["cell"]: t["n"] for t in chosen})
    core = {}
    for cell in H1_CELLS:
        a, b, c, d = paired_table(dev, cell, GATED_PRIMARY, "uniform_ht")
        n_dev = a + b + c + d
        dl = _wilson80(b + c, n_dev)[0]
        pl = _wilson80(b, b + c)[0] if b + c else 0.5
        core[cell] = {"dev_table": [a, b, c, d], "n_pessimistic": _n_for(pl, dl, FWER / 2)}
    return {
        "status": "LOCKED_FROM_DEVELOPMENT_GRID (block e2_dev_grid); no confirmation seed used",
        "rules": {
            "band_paced_detection": BAND,
            "min_onset_share": MIN_ONSET_SHARE,
            "max_per_class": MAX_PER_CLASS,
            "class_ii_exhaustion_bands": {k: v[0] for k, v in EXHAUSTION_BANDS.items()},
            "selection_order": "closest to 0.5 paced detection (i, iii); closest to band centre "
            "of fixed pre-onset reserve exhaustion (ii); ties by cell name",
            "floor_n": FLOOR_N,
            "ceil_n": CEIL_N,
            "alpha_family": FWER,
        },
        "order": order,
        "n": sizes,
        "h_b2": chosen,
        "uninformative": uninformative,
        "core_power_dev": core,
        "grid_summary": stats,
    }


CORE_NAMES = (
    "b1_r0.02",
    "b1_r0.05",
    "b1_r0.20",
    "mech_s0.8_r0.02",
    "mech_s0.8_r0.10",
    "mech_s1.5_r0.02",
    "mech_s1.5_r0.10",
    "mech_s1.0_r0.05",
    "mech_s2.0_r0.05",
)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["confirm", "select-grid"])
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--dev-rows", type=Path, default=None, help="select-grid: e2_dev rows")
    parser.add_argument("--locked", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    rows = pd.read_parquet(args.rows)
    if args.mode == "select-grid":
        if args.dev_rows is None:
            parser.error("select-grid needs --dev-rows")
        body = select_grid(rows, pd.read_parquet(args.dev_rows))
        args.out.write_text(json.dumps(body, indent=2, default=float) + "\n", encoding="utf-8")
        print(json.dumps({k: body[k] for k in ("order", "n", "h_b2", "uninformative")}, indent=1))
        return 0
    if args.locked is None:
        parser.error("confirm needs --locked")
    manifest = json.loads((args.rows.parent / "manifest.json").read_text(encoding="utf-8"))
    locked = json.loads(args.locked.read_text(encoding="utf-8"))
    expected = None
    if manifest["block"] == "confirmation":
        from shiftlab.dive import e2_acquisition_pacing as e2

        expected = {
            c: e2.cell_seeds("confirmation", c, locked["n"][c], locked["order"])
            for c in locked["order"]
        }
    status = (
        "CONFIRMATORY"
        if manifest["block"] == "confirmation"
        else "DEVELOPMENT (descriptive, not confirmatory)"
    )
    body = confirm(rows, locked, expected)
    payload = {"status": status, "manifest": manifest, "result": body}
    args.out.write_text(json.dumps(payload, indent=2, default=float), encoding="utf-8")
    print(json.dumps(body, indent=2, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
