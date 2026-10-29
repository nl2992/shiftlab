"""CRSP label-allocation headroom replay (RPOQ S6).

Implements ``docs/rpoq_s6_crsp_allocation_headroom_protocol_v1.md``. Exploratory
external-sequence evaluation: clocks, costs and the conditional-mean null are imposed, and
crossings are descriptive. No new method is evaluated here; the oracle rule reads outcomes
and is an upper reference only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pyarrow.compute as pc
import pyarrow.dataset as ds

RETURN_CAP = 0.10
FEE = 5 / 10_000.0
BOUND = 0.20 + 4 * FEE
ALPHA = 0.05
VWRETD = 7
SEED = 20261029
N_COHORTS = 10
COHORT_SIZE = 300
QUERY_SEEDS = 20
BUDGET_FRACTIONS = (0.05, 0.20)
RULES = ("uniform", "neyman", "oracle", "full")
COLUMNS = ["permno", "dlycaldt", "split", "features", "target"]


def _turnover(actions: np.ndarray, permnos: np.ndarray, dates: np.ndarray) -> np.ndarray:
    order = np.lexsort((dates, permnos))
    sp, sa = permnos[order], actions[order].astype(np.float64)
    delta = np.abs(np.diff(sa, prepend=0.0))
    first = np.r_[True, sp[1:] != sp[:-1]]
    delta[first] = sa[first]
    last = np.r_[sp[1:] != sp[:-1], True]
    delta[last] += sa[last]
    out = np.empty(len(actions))
    out[order] = delta
    return out


def _ridge(x: np.ndarray, y: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    xa = np.c_[np.ones(len(x)), x]
    reg = alpha * np.eye(xa.shape[1])
    reg[0, 0] = 0.0
    return np.linalg.solve(xa.T @ xa + reg, xa.T @ y)


def _predict(beta: np.ndarray, x: np.ndarray) -> np.ndarray:
    return np.c_[np.ones(len(x)), x] @ beta


def _load_rows(panel: Path, permnos: np.ndarray | None, columns: list[str]):
    dataset = ds.dataset(panel, format="parquet")
    flt = pc.field("permno").isin(permnos.tolist()) if permnos is not None else None
    return dataset.to_table(columns=columns, filter=flt)


def _features(table) -> np.ndarray:
    col = table["features"].combine_chunks()
    flat = col.values.to_numpy(zero_copy_only=False)
    return flat.reshape(len(col), -1).astype(np.float64)


def build_cohort(table, cohort_permnos: np.ndarray) -> dict | None:
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
    if train.sum() < 1000 or (split == "test").sum() < 1000:
        return None
    med = np.nanmedian(sub_x[train], axis=0)
    xs = np.where(np.isfinite(sub_x), sub_x, med)
    mu, sd = xs[train].mean(0), xs[train].std(0) + 1e-12
    xs = (xs - mu) / sd
    beta = _ridge(xs[train], np.clip(sub_y[train], -RETURN_CAP, RETURN_CAP))
    pred = _predict(beta, xs)
    cand = (pred > 0).astype(np.int8)
    ref = (np.where(np.isfinite(sub_x[:, VWRETD]), sub_x[:, VWRETD], 0.0) > 0).astype(np.int8)
    clipped = np.clip(sub_y, -RETURN_CAP, RETURN_CAP)
    z = np.zeros(len(sub_y))
    for sp in ("train", "validation", "calibration", "test"):
        m = split == sp
        if not m.any():
            continue
        ct = _turnover(cand[m], sub_p[m], date[m])
        rt = _turnover(ref[m], sub_p[m], date[m])
        z[m] = (-cand[m] * clipped[m] + FEE * ct) - (-ref[m] * clipped[m] + FEE * rt)
    h_beta = _ridge(xs[train], z[train])
    h = np.clip(_predict(h_beta, xs), -BOUND, BOUND)
    r_beta = _ridge(xs[train], (z[train] - h[train]) ** 2)
    r_hat = np.maximum(_predict(r_beta, xs), 0.0)
    val = split == "validation"
    test = split == "test"
    order = np.lexsort((sub_p[test], date[test]))
    idx = np.flatnonzero(test)[order]
    dates = date[idx]
    uniq, date_index = np.unique(dates, return_inverse=True)
    return {
        "z": z[idx],
        "h": h[idx],
        "root_r": np.sqrt(r_hat[idx]),
        "root_r_val_mean": float(np.sqrt(r_hat[val]).mean()) if val.any() else float("nan"),
        "date_index": date_index,
        "n_dates": len(uniq),
        "n_events": len(idx),
        "candidate_long_rate": float(cand[idx].mean()),
        "reference_long_rate": float(ref[idx].mean()),
        "mean_excess_cost": float(z[idx].mean()),
    }


def _propensity(rule: str, c: dict, y: np.ndarray, h: np.ndarray, frac: float) -> np.ndarray:
    if rule == "full":
        return np.ones(c["n_events"])
    if rule == "uniform":
        return np.full(c["n_events"], frac)
    if rule == "neyman":
        score = np.maximum(c["root_r"], 0.1 * c["root_r_val_mean"])
        q = frac * score / c["root_r_val_mean"]
    else:  # oracle: reads the outcome, evaluator-only
        score = np.abs(y - h) + 1e-6
        q = frac * score / score.mean()
    return np.clip(q, 0.1 * frac, 1.0)


def run_monitor(c: dict, rule: str, sign: float, frac: float, u: np.ndarray) -> dict:
    y = sign * c["z"]
    h = sign * c["h"]
    q = _propensity(rule, c, y, h, frac)
    n = c["n_events"]
    budget = np.inf if rule == "full" else int(round(frac * n))
    bounds = BOUND * (2.0 / q - 1.0)
    q_raw = u < q
    di = c["date_index"]
    starts = np.r_[0, np.flatnonzero(np.diff(di)) + 1, n]
    spent = 0
    m1 = m2 = 0.0
    count = 0
    log_w = 0.0
    log_thr = np.log(1.0 / ALPHA)
    first_cross = None
    for k in range(len(starts) - 1):
        a, b = starts[k], starts[k + 1]
        qr = q_raw[a:b]
        csum = np.cumsum(qr)
        active = (spent + csum - qr) < budget
        queried = qr & active
        x = np.where(active, h[a:b] + queried * (y[a:b] - h[a:b]) / q[a:b], 0.0)
        mean = m1 / (count + 1)
        second = m2 / (count + 1)
        lam = np.zeros(b - a)
        if second > 0 and mean > 0:
            lam = np.minimum(mean / second, 0.5 / bounds[a:b])
        log_w += float(np.log1p(lam * x).sum())
        spent += int(queried.sum())
        m1 += float(x[active].sum())
        m2 += float((x[active] ** 2).sum())
        count += int(active.sum())
        if first_cross is None and log_w >= log_thr:
            first_cross = k
    return {"log_wealth": log_w, "crossed": first_cross is not None, "first_cross": first_cross, "spent": spent}


def _bootstrap(per_cohort: np.ndarray, rng: np.random.Generator, reps: int = 2000) -> tuple[float, float, float]:
    mean = float(per_cohort.mean())
    idx = rng.integers(0, len(per_cohort), size=(reps, len(per_cohort)))
    boot = per_cohort[idx].mean(axis=1)
    return mean, float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--panel", required=True)
    parser.add_argument("--output-dir", default="outputs/rpoq_s6_crsp_headroom_v1")
    parser.add_argument("--cohorts", type=int, default=N_COHORTS)
    parser.add_argument("--seeds", type=int, default=QUERY_SEEDS)
    args = parser.parse_args()
    t0 = time.time()
    panel = Path(args.panel)
    rng = np.random.default_rng(SEED)
    base = _load_rows(panel, None, ["permno", "split"])
    permno_all = base["permno"].to_numpy()
    split_all = np.asarray(base["split"].to_pylist(), dtype=object)
    universe = np.unique(permno_all[split_all == "train"])
    chosen = rng.permutation(universe)[: args.cohorts * COHORT_SIZE]
    cohorts = [chosen[i * COHORT_SIZE : (i + 1) * COHORT_SIZE] for i in range(args.cohorts)]
    table = _load_rows(panel, chosen, COLUMNS)
    print(f"loaded {table.num_rows} rows for {len(chosen)} permnos in {time.time() - t0:.0f}s", flush=True)

    runs = []
    meta = []
    for ci, cp in enumerate(cohorts):
        c = build_cohort(table, cp)
        if c is None:
            meta.append({"cohort": ci, "skipped": True})
            continue
        meta.append({"cohort": ci, **{k: c[k] for k in ("n_events", "n_dates", "candidate_long_rate", "reference_long_rate", "mean_excess_cost")}})
        for direction, sign in (("benefit", -1.0), ("harm", 1.0)):
            for frac in BUDGET_FRACTIONS:
                for rule in RULES:
                    if rule == "full" and frac != BUDGET_FRACTIONS[0]:
                        continue
                    for s in range(args.seeds):
                        u = np.random.default_rng(SEED + 1000 * ci + s).random(c["n_events"])
                        res = run_monitor(c, rule, sign, frac, u)
                        runs.append({"cohort": ci, "direction": direction, "budget_fraction": None if rule == "full" else frac, "rule": rule, "seed": s, **res})
        print(f"cohort {ci} done ({time.time() - t0:.0f}s)", flush=True)

    summary = []
    brng = np.random.default_rng(SEED + 7)
    keys = sorted({(r["direction"], r["budget_fraction"], r["rule"]) for r in runs}, key=str)
    def per_cohort(direction, frac, rule, field="log_wealth"):
        vals = {}
        for r in runs:
            if (r["direction"], r["budget_fraction"], r["rule"]) == (direction, frac, rule):
                vals.setdefault(r["cohort"], []).append(float(r[field]))
        return {k: float(np.mean(v)) for k, v in vals.items()}
    for direction, frac, rule in keys:
        pcw = per_cohort(direction, frac, rule)
        arr = np.array([pcw[k] for k in sorted(pcw)])
        row = {"direction": direction, "budget_fraction": frac, "rule": rule, "mean_log_wealth": _bootstrap(arr, brng), "crossing_rate": float(np.mean(per_cohort(direction, frac, rule, "crossed") and list(per_cohort(direction, frac, rule, "crossed").values())))}
        if rule != "uniform" and rule != "full":
            base_c = per_cohort(direction, frac, "uniform")
            diff = np.array([pcw[k] - base_c[k] for k in sorted(pcw) if k in base_c])
            row["paired_diff_vs_uniform"] = _bootstrap(diff, brng)
        summary.append(row)

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "protocol": "docs/rpoq_s6_crsp_allocation_headroom_protocol_v1.md",
        "panel_sha256_prefix_note": "panel not hashed here; see dataset_manifest.json version 5211412140dcb86f08f9",
        "seed": SEED,
        "cohort_meta": meta,
        "summary": summary,
        "n_runs": len(runs),
        "seconds": time.time() - t0,
    }
    (out / "results.json").write_text(json.dumps(payload, indent=2))
    import csv

    with (out / "runs.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    digest = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(out.glob("*")) if p.name != "checksums.sha256"}
    (out / "checksums.sha256").write_text("".join(f"{v}  {k}\n" for k, v in digest.items()))
    for row in summary:
        print(row)


if __name__ == "__main__":
    main()
