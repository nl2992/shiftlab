"""Real-data audit + development-window dynamic-headroom screen (Agent C, decision-value programme).

Usage (single process, CPU, < 10 min):
  python -I scripts/decision_value/audit_real_data.py --data-root <shift-research-starter/data> \
      --tasks opsd monash_elec binance elec2 eia
Writes only under outputs/decision_value/real_data/dev/<task>/ (gitignored).

LEAKAGE RULES (enforced in code):
  * OPSD: only rows with utc_timestamp < 2019-12-31T23:00 are read (nrows cap + assertion). 2020 is reserved.
  * Monash electricity_hourly: only the first 17,544 values (2012-01-01..2013-12-31) of each series are parsed.
  * Binance: only ETHUSDT-1h-2025-01..2025-12 zips are opened; 2026 zips are never opened.
  * Elec2: only the first 36,250 data rows (80%) are parsed; later rows are never read.
  * EIA: processed CISO/ERCO rows with label time < 2025-07-01 only (all EIA windows are exposed anyway).
Headroom quantities are hindsight upper bounds on any online policy (no label delay on the switch decision,
no query cost). Loss units are declared per task; switching costs are imposed sensitivity values.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler

COSTS = (0.0, 1.0, 5.0, 20.0)
N_PERM = 100


# ---------------------------------------------------------------- hindsight switching DP
def dyn_cost(l0, l1, cs, path=False):
    """Min total loss over state sequences s_t in {0,1}; start in state 0; cost cs per change."""
    v0, v1 = 0.0, cs
    bp0, bp1 = [], []
    for a, b in zip(l0, l1):
        f0, f1 = v1 + cs < v0, v0 + cs < v1
        n0 = (v1 + cs if f0 else v0) + a
        n1 = (v0 + cs if f1 else v1) + b
        if path:
            bp0.append(f0)
            bp1.append(f1)
        v0, v1 = n0, n1
    best = min(v0, v1)
    if not path:
        return best, None
    s = 0 if v0 <= v1 else 1
    seq = [s]
    for t in range(len(l0) - 1, 0, -1):
        sw = (bp0 if s == 0 else bp1)[t]
        s = 1 - s if sw else s
        seq.append(s)
    seq = seq[::-1]
    n_sw = int(seq[0] != 0) + sum(seq[i] != seq[i - 1] for i in range(1, len(seq)))
    return best, int(n_sw)


def headroom(l0, l1, rng):
    l0, l1 = np.asarray(l0, float), np.asarray(l1, float)
    d = l0 - l1
    out = {
        "T": len(l0),
        "mean_loss_incumbent": float(l0.mean()),
        "mean_loss_challenger": float(l1.mean()),
        "challenger_gain_pct": float(100 * (l0.sum() - l1.sum()) / l0.sum()),
        "frac_steps_challenger_better": float((d > 0).mean()),
        "lag1_autocorr_of_loss_diff": float(np.corrcoef(d[:-1], d[1:])[0, 1])
        if len(d) > 2
        else None,
        "by_switch_cost": {},
    }
    perms = [rng.permutation(len(l0)) for _ in range(N_PERM)]
    for cs in COSTS:
        static = min(l0.sum(), l1.sum() + cs)
        dyn, nsw = dyn_cost(l0, l1, cs, path=True)
        H = static - dyn
        Hp = np.array([min(l0.sum(), l1.sum() + cs) - dyn_cost(l0[p], l1[p], cs)[0] for p in perms])
        out["by_switch_cost"][str(cs)] = {
            "static_best_cost": float(static),
            "static_best": "challenger" if l1.sum() + cs < l0.sum() else "incumbent",
            "dynamic_best_cost": float(dyn),
            "H_T": float(H),
            "H_T_pct_of_static": float(100 * H / static),
            "optimal_path_switches": nsw,
            "H_T_time_shuffled_median": float(np.median(Hp)),
            "H_T_time_shuffled_p95": float(np.quantile(Hp, 0.95)),
            "H_T_excess_over_shuffled_p95": float(H - np.quantile(Hp, 0.95)),
        }
    return out


# ---------------------------------------------------------------- hourly day-ahead ridge pipeline
def build_features(y: pd.Series, tz):
    idx = pd.date_range(y.index.min(), y.index.max(), freq="h")
    y = y.reindex(idx)
    loc = idx.tz_localize("UTC").tz_convert(tz) if tz else idx
    how = (loc.dayofweek * 24 + loc.hour).to_numpy()
    X = np.zeros((len(idx), 174))
    X[np.arange(len(idx)), how] = 1
    doy = loc.dayofyear.to_numpy() / 365.25 * 2 * np.pi
    for k in (1, 2):
        X[:, 168 + 2 * (k - 1)] = np.sin(k * doy)
        X[:, 169 + 2 * (k - 1)] = np.cos(k * doy)
    X[:, 172] = y.shift(48).to_numpy()  # same hour D-2 (released before the D-1 decision)
    X[:, 173] = y.shift(168).to_numpy()  # same hour D-7
    day = np.array([d.toordinal() for d in loc.date])
    return idx, y.to_numpy(), X, day


def day_ahead_task(
    name, y, tz, fit, val_end, dev, delays=(2, 7), window=365, ext=None, outdir=None, rng=None
):
    idx, yv, X, day = build_features(y, tz)
    M = float(
        np.nanmean(yv[(idx >= fit[0]) & (idx <= pd.Timestamp(fit[1]) + pd.Timedelta(hours=23))])
    )
    Xs, ys = X.copy(), yv / M
    Xs[:, 172:174] /= M
    ok = np.isfinite(Xs).all(1) & np.isfinite(ys)
    d_ord = lambda s: pd.Timestamp(s).toordinal()
    fit_m = ok & (day >= d_ord(fit[0])) & (day <= d_ord(fit[1]))
    val_m = ok & (day > d_ord(fit[1])) & (day <= d_ord(val_end))
    best = None
    for a in (0.1, 1.0, 10.0, 100.0):
        e = np.abs(Ridge(alpha=a).fit(Xs[fit_m], ys[fit_m]).predict(Xs[val_m]) - ys[val_m]).mean()
        best = (e, a) if best is None or e < best[0] else best
    alpha = best[1]
    f0 = Ridge(alpha=alpha).fit(Xs[fit_m], ys[fit_m])  # frozen incumbent
    extv = ext.reindex(idx).to_numpy() / M if ext is not None else None
    L = {
        k: []
        for k in ["frozen_ridge"]
        + [f"sliding_ridge_d{d}" for d in delays]
        + (["external_forecast"] if ext is not None else [])
    }
    kept = []
    for D in range(d_ord(dev[0]), d_ord(dev[1]) + 1):
        te = np.where(day == D)[0]
        te = te[ok[te] & (np.isfinite(extv[te]) if extv is not None else True)]
        if len(te) < 20:
            continue
        kept.append(D)
        L["frozen_ridge"].append(100 * np.abs(f0.predict(Xs[te]) - ys[te]).mean())
        for d in delays:
            tr = np.where(ok & (day <= D - d) & (day > D - d - window))[0]
            m = Ridge(alpha=alpha).fit(Xs[tr], ys[tr])
            L[f"sliding_ridge_d{d}"].append(100 * np.abs(m.predict(Xs[te]) - ys[te]).mean())
        if extv is not None:
            L["external_forecast"].append(100 * np.abs(extv[te] - ys[te]).mean())
    L = {k: np.array(v) for k, v in L.items()}
    pairs = [("frozen_ridge", f"sliding_ridge_d{d}") for d in delays]
    if ext is not None:
        pairs += [
            ("frozen_ridge", "external_forecast"),
            ("external_forecast", f"sliding_ridge_d{delays[0]}"),
        ]
    res = {
        "task": name,
        "loss_unit": "percent of fit-window mean load; daily mean absolute error",
        "ridge_alpha": alpha,
        "fit": list(fit),
        "validation_end": val_end,
        "dev": list(dev),
        "n_dev_days_kept": len(kept),
        "label_delay_days_sliding_refit": list(delays),
        "refit_window_days": window,
        "pairs": {},
    }
    for a, b in pairs:
        res["pairs"][f"{a}__vs__{b}"] = headroom(L[a], L[b], rng)
    if outdir:
        outdir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({"day_ordinal": kept, **L}).to_csv(outdir / "per_step_losses.csv", index=False)
        (outdir / "summary.json").write_text(json.dumps(res, indent=1))
    return res


# ---------------------------------------------------------------- task loaders
def task_opsd(root, out, rng):
    p = root / "raw/opsd/2020-10-06/hourly.csv"
    hold = pd.Timestamp("2019-12-31T23:00:00")
    df = pd.read_csv(
        p,
        usecols=[
            "utc_timestamp",
            "DE_load_actual_entsoe_transparency",
            "DE_load_forecast_entsoe_transparency",
        ],
        nrows=43824,
    )
    df["t"] = pd.to_datetime(df["utc_timestamp"], utc=True).dt.tz_localize(None)
    assert df["t"].max() < hold, "holdout leak"
    df = df.set_index("t")
    return day_ahead_task(
        "opsd_de_load",
        df["DE_load_actual_entsoe_transparency"],
        "Europe/Berlin",
        ("2015-01-01", "2016-12-31"),
        "2017-12-31",
        ("2018-01-01", "2019-12-31"),
        ext=df["DE_load_forecast_entsoe_transparency"],
        outdir=out / "opsd_de_load",
        rng=rng,
    )


def task_monash_elec(root, out, rng):
    z = zipfile.ZipFile(root / "raw/monash/4656140/electricity_hourly_dataset.zip")
    name = next(n for n in z.namelist() if n.endswith(".tsf"))
    N = 24 * (366 + 365)  # 2012-01-01 .. 2013-12-31 only
    tot, n_series, started = np.zeros(N), 0, False
    for line in io.TextIOWrapper(z.open(name), encoding="utf8"):
        if line.startswith("@data"):
            started = True
            continue
        if not started or not line.strip():
            continue
        parts = line.split(":", 2)
        assert parts[1].startswith("2012-01-01"), parts[1]
        tot += np.array(parts[2].split(",", N)[:N], dtype=float)
        n_series += 1
    y = pd.Series(tot, index=pd.date_range("2012-01-01", periods=N, freq="h"))
    r = day_ahead_task(
        "monash_electricity_hourly_aggregate",
        y,
        None,
        ("2012-01-01", "2012-12-31"),
        "2013-03-31",
        ("2013-04-01", "2013-12-31"),
        outdir=out / "monash_electricity_hourly",
        rng=rng,
    )
    r["n_series_aggregated"] = n_series
    return r


def task_eia(root, out, rng):
    d = root / "processed/eia/e47bdef8b208f8e7d788"
    f = pd.read_parquet(
        d / "observations.parquet", columns=["domain_id", "label_event_time", "target"]
    )
    res = {}
    for dom in ("CISO", "ERCO"):
        g = f[f.domain_id == dom]
        y = pd.Series(
            g.target.to_numpy(float),
            index=pd.to_datetime(g.label_event_time.to_numpy(float), unit="s"),
        )
        y = y[~y.index.duplicated()].sort_index()
        y = y[y.index < pd.Timestamp("2025-07-01")]
        res[dom] = day_ahead_task(
            f"eia_{dom}_demand",
            y,
            None,
            ("2023-01-08", "2023-12-31"),
            "2024-06-30",
            ("2024-07-01", "2025-06-30"),
            delays=(2,),
            outdir=out / f"eia_{dom}",
            rng=rng,
        )
    return res


def task_binance(root, out, rng, delay_bars=1, refit_every=24, win=720):
    rows = []
    for m in range(1, 13):  # 2025 only; 2026 zips are never opened
        zp = root / f"raw/binance/ETHUSDT-1h-2025-{m:02d}.zip"
        chk = (root / f"raw/binance/ETHUSDT-1h-2025-{m:02d}.CHECKSUM").read_text().split()[0]
        assert hashlib.sha256(zp.read_bytes()).hexdigest() == chk, f"checksum {zp}"
        z = zipfile.ZipFile(zp)
        rows.append(
            pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 4], names=["o", "c"])
        )
    k = pd.concat(rows, ignore_index=True)
    ts = pd.to_datetime(
        k.o.astype("int64") // 1000, unit="ms"
    )  # 2025 files carry microsecond epochs
    assert (np.diff(ts.values).astype("timedelta64[h]").astype(int) == 1).all(), "gap/dup in bars"
    r = np.log(k.c.values[1:] / k.c.values[:-1])
    ts = ts[1:].reset_index(drop=True)
    n = len(r)
    F = np.column_stack(
        [np.roll(r, s) for s in range(6)]
        + [
            pd.Series(r).rolling(24).std().to_numpy(),
            np.sin(2 * np.pi * ts.dt.hour / 24),
            np.cos(2 * np.pi * ts.dt.hour / 24),
        ]
    )
    yv = (np.append(r[1:], np.nan) > 0).astype(
        int
    )  # direction of next bar; decision at close of bar t
    dev_start = int(ts.searchsorted(pd.Timestamp("2025-07-01")))
    tr0 = np.arange(30, dev_start - 1)
    sc = StandardScaler().fit(F[tr0])
    Fs = sc.transform(np.nan_to_num(F))
    f0 = LogisticRegression(C=1.0, max_iter=500).fit(Fs[tr0], yv[tr0])
    l0, l1, m1 = [], [], None
    for t in range(dev_start, n - 1):
        if (t - dev_start) % refit_every == 0:
            hi = t - delay_bars  # label of decision s is known at close of bar s+1
            m1 = LogisticRegression(C=1.0, max_iter=500).fit(
                Fs[max(30, hi - win) : hi], yv[max(30, hi - win) : hi]
            )
        l0.append(float(f0.predict(Fs[t : t + 1])[0] != yv[t]))
        l1.append(float(m1.predict(Fs[t : t + 1])[0] != yv[t]))
    res = {
        "task": "binance_ethusdt_1h_direction",
        "loss_unit": "0/1 direction error per bar",
        "fit": ["2025-01-01", "2025-06-30"],
        "dev": ["2025-07-01", "2025-12-31"],
        "n_dev_bars": len(l0),
        "label_delay_bars": delay_bars,
        "refit_every_bars": refit_every,
        "refit_window_bars": win,
        "pairs": {"frozen_logit__vs__sliding_logit": headroom(l0, l1, rng)},
    }
    o = out / "binance_ethusdt_1h"
    o.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"frozen": l0, "sliding": l1}).to_csv(o / "per_step_losses.csv", index=False)
    (o / "summary.json").write_text(json.dumps(res, indent=1))
    return res


def task_elec2(
    root, out, rng, fit_end=18124, dev=(25656, 36250), refit_every=48, win=2000, delay=48
):
    lines, started = [], False
    with open(root / "raw/elec2/electricity-normalized.arff", encoding="utf8") as fh:
        for ln in fh:
            if started:
                lines.append(ln)
                if len(lines) == dev[1]:
                    break  # never read past row 36,250 (80% of the stream)
            elif ln.strip().lower() == "@data":
                started = True
    cols = [
        "date",
        "day",
        "period",
        "nswprice",
        "nswdemand",
        "vicprice",
        "vicdemand",
        "transfer",
        "class",
    ]
    df = pd.read_csv(io.StringIO("".join(lines)), header=None, names=cols)
    X = df[["period", "nswprice", "nswdemand", "vicprice", "vicdemand", "transfer"]].to_numpy(float)
    y = (df["class"] == "UP").astype(int).to_numpy()
    Xs = StandardScaler().fit(X[:fit_end]).transform(X)
    f0 = LogisticRegression(max_iter=500).fit(Xs[:fit_end], y[:fit_end])
    l0, l1, m1 = [], [], None
    for t in range(dev[0], dev[1]):
        if (t - dev[0]) % refit_every == 0:
            hi = t - delay
            m1 = LogisticRegression(max_iter=500).fit(
                Xs[max(0, hi - win) : hi], y[max(0, hi - win) : hi]
            )
        l0.append(float(f0.predict(Xs[t : t + 1])[0] != y[t]))
        l1.append(float(m1.predict(Xs[t : t + 1])[0] != y[t]))
    res = {
        "task": "elec2_row_order",
        "loss_unit": "0/1 error per row",
        "fit_rows": [0, fit_end - 1],
        "dev_rows": [dev[0], dev[1] - 1],
        "reserved_rows_NOT_READ": [dev[1], 45311],
        "note": "row order is not a verified clock; label delay 48 rows is imposed",
        "pairs": {"frozen_logit__vs__sliding_logit": headroom(l0, l1, rng)},
    }
    o = out / "elec2_row_order"
    o.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"frozen": l0, "sliding": l1}).to_csv(o / "per_step_losses.csv", index=False)
    (o / "summary.json").write_text(json.dumps(res, indent=1))
    return res


TASKS = {
    "opsd": task_opsd,
    "monash_elec": task_monash_elec,
    "binance": task_binance,
    "elec2": task_elec2,
    "eia": task_eia,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--out", default="outputs/decision_value/real_data/dev")
    ap.add_argument("--tasks", nargs="+", default=list(TASKS))
    a = ap.parse_args()
    root, out = Path(a.data_root), Path(a.out)
    allres = {}
    for t in a.tasks:
        allres[t] = TASKS[t](root, out, np.random.default_rng(20261030))
        print("done", t, file=sys.stderr)
    out.mkdir(parents=True, exist_ok=True)
    (out / "all_dev_headroom_summary.json").write_text(json.dumps(allres, indent=1))
    print(json.dumps({k: "ok" for k in allres}))


if __name__ == "__main__":
    main()
