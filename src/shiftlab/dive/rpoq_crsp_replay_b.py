"""CRSP replay S6b: validation-selected residual-variance allocation (ASI-VS).

Implements ``docs/rpoq_s6b_validation_selected_variance_protocol_v1.md``. Reuses the S6
stream, monitor, cohorts and query seeds; only the allocation's variance model differs.
Exploratory: imposed clocks and null, no error-controlled validity on real data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from pathlib import Path

import numpy as np

from shiftlab.dive.rpoq_crsp_replay import (
    BOUND,
    BUDGET_FRACTIONS,
    COHORT_SIZE,
    COLUMNS,
    FEE,
    N_COHORTS,
    QUERY_SEEDS,
    RETURN_CAP,
    SEED,
    VWRETD,
    _bootstrap,
    _features,
    _load_rows,
    _predict,
    _ridge,
    _turnover,
    run_monitor,
)

MODELS = ("lin", "log", "log_abs")


def _sqrt_r(model: str, xs: np.ndarray, resid2: np.ndarray, train: np.ndarray) -> np.ndarray:
    if model == "lin":
        beta = _ridge(xs[train], resid2[train])
        return np.sqrt(np.maximum(_predict(beta, xs), 0.0))
    feats = xs if model == "log" else np.c_[xs, np.abs(xs), xs**2]
    target = np.log(resid2 + 1e-6)
    beta = _ridge(feats[train], target[train])
    sigma2 = float(np.var(target[train] - _predict(beta, feats[train])))
    return np.sqrt(np.exp(_predict(beta, feats) + sigma2 / 2.0))


def _propensity_from_root(root: np.ndarray, val_mean: float, frac: float) -> np.ndarray:
    score = np.maximum(root, 0.1 * val_mean)
    return np.clip(frac * score / val_mean, 0.1 * frac, 1.0)


def _bins(col: np.ndarray, train: np.ndarray, n: int = 8) -> np.ndarray:
    """Bin index from train-split quantile edges (no outcome information)."""
    return np.digitize(col, np.quantile(col[train], np.linspace(0, 1, n + 1)[1:-1]))


def build_cohort_b(table, cohort_permnos: np.ndarray, eval_split: str = "test") -> dict | None:
    permno = table["permno"].to_numpy()
    mask = np.isin(permno, cohort_permnos)
    split = np.asarray(table["split"].to_pylist(), dtype=object)[mask]
    date = np.asarray(table["dlycaldt"].to_pylist(), dtype=object)[mask]
    sub_x = _features(table)[mask]
    sub_y = table["target"].to_numpy()[mask]
    sub_p = permno[mask]
    ok = np.isfinite(sub_y)
    split, date, sub_x, sub_y, sub_p = split[ok], date[ok], sub_x[ok], sub_y[ok], sub_p[ok]
    train = split == "train"
    if train.sum() < 1000 or (split == eval_split).sum() < 1000:
        return None
    med = np.nanmedian(sub_x[train], axis=0)
    xs = np.where(np.isfinite(sub_x), sub_x, med)
    xr = xs.copy()
    xs = (xs - xs[train].mean(0)) / (xs[train].std(0) + 1e-12)
    pred = _predict(_ridge(xs[train], np.clip(sub_y[train], -RETURN_CAP, RETURN_CAP)), xs)
    cand = (pred > 0).astype(np.int8)
    ref = (np.where(np.isfinite(sub_x[:, VWRETD]), sub_x[:, VWRETD], 0.0) > 0).astype(np.int8)
    clipped = np.clip(sub_y, -RETURN_CAP, RETURN_CAP)
    z = np.zeros(len(sub_y))
    for sp in ("train", "validation", "calibration", "test"):
        m = split == sp
        if m.any():
            ct = _turnover(cand[m], sub_p[m], date[m])
            rt = _turnover(ref[m], sub_p[m], date[m])
            z[m] = (-cand[m] * clipped[m] + FEE * ct) - (-ref[m] * clipped[m] + FEE * rt)
    h = np.clip(_predict(_ridge(xs[train], z[train]), xs), -BOUND, BOUND)
    resid2 = (z - h) ** 2
    val, test = split == "validation", split == eval_split
    roots = {m: _sqrt_r(m, xs, resid2, train) for m in MODELS}
    order = np.lexsort((sub_p[test], date[test]))
    idx = np.flatnonzero(test)[order]
    _, date_index = np.unique(date[idx], return_inverse=True)
    out = {
        "z": z[idx],
        "h": h[idx],
        "date_index": date_index,
        "n_dates": int(date_index.max()) + 1,
        "n_events": len(idx),
        "ctx_size": _bins(xr[:, 5], train)[idx],
        "ctx_abs_return": _bins(np.abs(xr[:, 0]), train)[idx],
        "choice": {},
        "root_by_budget": {},
        "val_objective": {},
    }
    for frac in BUDGET_FRACTIONS:
        scores = {}
        for m in MODELS:
            val_mean = float(roots[m][val].mean())
            q_val = _propensity_from_root(roots[m][val], val_mean, frac)
            scores[m] = float(np.mean(resid2[val] / q_val))
        best = min(MODELS, key=lambda k: scores[k])
        out["choice"][frac] = best
        out["val_objective"][frac] = scores
        out["root_by_budget"][frac] = (roots[best][idx], float(roots[best][val].mean()))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True)
    parser.add_argument("--s6-runs", required=True)
    parser.add_argument("--output-dir", default="outputs/rpoq_s6b_crsp_asivs_v1")
    parser.add_argument("--cohorts", type=int, default=N_COHORTS)
    parser.add_argument("--seeds", type=int, default=QUERY_SEEDS)
    args = parser.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    base = _load_rows(Path(args.panel), None, ["permno", "split"])
    permno_all = base["permno"].to_numpy()
    split_all = np.asarray(base["split"].to_pylist(), dtype=object)
    universe = np.unique(permno_all[split_all == "train"])
    chosen = rng.permutation(universe)[: args.cohorts * COHORT_SIZE]
    cohorts = [chosen[i * COHORT_SIZE : (i + 1) * COHORT_SIZE] for i in range(args.cohorts)]
    table = _load_rows(Path(args.panel), chosen, COLUMNS)

    runs, meta = [], []
    for ci, cp in enumerate(cohorts):
        c = build_cohort_b(table, cp)
        if c is None:
            meta.append({"cohort": ci, "skipped": True})
            continue
        meta.append(
            {
                "cohort": ci,
                "choice": {str(k): v for k, v in c["choice"].items()},
                "val_objective": {str(k): v for k, v in c["val_objective"].items()},
            }
        )
        for direction, sign in (("benefit", -1.0), ("harm", 1.0)):
            for frac in BUDGET_FRACTIONS:
                root, val_mean = c["root_by_budget"][frac]
                cc = {**c, "root_r": root, "root_r_val_mean": val_mean}
                for s in range(args.seeds):
                    u = np.random.default_rng(SEED + 1000 * ci + s).random(c["n_events"])
                    res = run_monitor(cc, "neyman", sign, frac, u)
                    runs.append(
                        {
                            "cohort": ci,
                            "direction": direction,
                            "budget_fraction": frac,
                            "rule": "asi_vs",
                            "seed": s,
                            **res,
                        }
                    )
        print(f"cohort {ci} done ({time.time() - t0:.0f}s)", flush=True)

    s6: dict[tuple, dict[int, list[float]]] = {}
    with open(args.s6_runs) as fh:
        for r in csv.DictReader(fh):
            if r["rule"] in ("uniform", "neyman", "oracle") and r["budget_fraction"]:
                key = (r["direction"], float(r["budget_fraction"]), r["rule"])
                s6.setdefault(key, {}).setdefault(int(r["cohort"]), []).append(
                    float(r["log_wealth"])
                )
    brng = np.random.default_rng(SEED + 11)
    summary = []
    for direction in ("benefit", "harm"):
        for frac in BUDGET_FRACTIONS:
            mine: dict[int, list[float]] = {}
            for r in runs:
                if (r["direction"], r["budget_fraction"]) == (direction, frac):
                    mine.setdefault(r["cohort"], []).append(r["log_wealth"])
            cohort_ids = sorted(mine)
            arr = np.array([np.mean(mine[k]) for k in cohort_ids])
            row = {
                "direction": direction,
                "budget_fraction": frac,
                "asi_vs_mean_log_wealth": _bootstrap(arr, brng),
            }
            for other in ("uniform", "neyman", "oracle"):
                o = s6[(direction, frac, other)]
                diff = np.array([np.mean(mine[k]) - np.mean(o[k]) for k in cohort_ids if k in o])
                row[f"diff_vs_{other}"] = _bootstrap(diff, brng)
            summary.append(row)
    picks = {}
    for m in meta:
        for f, v in m.get("choice", {}).items():
            picks.setdefault(f, {}).setdefault(v, 0)
            picks[f][v] += 1
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(
        json.dumps(
            {
                "protocol": "docs/rpoq_s6b_validation_selected_variance_protocol_v1.md",
                "summary": summary,
                "model_selection_counts": picks,
                "cohort_meta": meta,
                "seconds": time.time() - t0,
            },
            indent=2,
        )
    )
    with (out / "runs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    (out / "checksums.sha256").write_text(
        "".join(
            f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n"
            for p in sorted(out.glob("*"))
            if p.name != "checksums.sha256"
        )
    )
    for row in summary:
        print(row)
    print("selection counts", picks)


if __name__ == "__main__":
    main()
