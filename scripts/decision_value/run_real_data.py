"""Real-data development replay of the monitoring-to-decision-value engine (Agent C, phase 2).

DEVELOPMENT ONLY.  Reserved windows are never read (OPSD >= 2019-12-31T23:00 UTC; Monash 2014; Binance 2026):
loaders below cap the rows/values they parse exactly as in scripts/decision_value/audit_real_data.py.

  python scripts/decision_value/run_real_data.py --data-root <shift-research-starter/data> [--smoke]
  python scripts/decision_value/run_real_data.py --analyze-only <run_dir>

Order of operations inside one run (also the order in which things are fixed):
  1. load validation- and development-window paired losses (raw units);
  2. fit the scaling on the VALIDATION window only; compute the deployable diagnostics (recipe in
     shiftlab.decision_value.data_adapters) from the validation window only and write diagnostics.json;
  3. calibrate monitor thresholds on the declared stationary null built from the validation window;
  4. replay on the dev window (modes actual / roll / bootS / bootL), costs on RAW losses.
Switching/label costs and delays are imposed sensitivity values; labels are free (c_q = 0).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import sys
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_value import controllers as C
from shiftlab.decision_value import data_adapters as DA
from shiftlab.decision_value.contracts import FeedbackContract
from shiftlab.decision_value.evaluation import simulate
from shiftlab.decision_value.monitors import monitor_factory
from shiftlab.decision_value.oracles import dp_two_state
from shiftlab.decision_value.registry import append_run

SEED = 20261030
ALPHA = 0.05
COSTS = (0.0, 1.0, 5.0, 20.0)
DELAYS = (1, 7)
QS = (0.25, 1.0)
HOLDS = (7, 30)
MONITORS = ("cusum", "page_hinkley", "batch", "sr_betting", "kelly_h2c_inspired")
INC_MONITORS = ("cusum", "sr_betting", "kelly_h2c_inspired")
# Declared monitor hyper-parameters (scaled-input units; sd of the scaled paired step is about 0.25 by construction)
HP = {
    "cusum": {"k": 0.05},
    "page_hinkley": {"delta": 0.025},
    "batch": {"n_b": 14},
    "sr_betting": {},
    "kelly_h2c_inspired": {},
}
CAL_BLOCK_REFS = {
    "calendar14": ("calendar", 14),
    "calendar28": ("calendar", 28),
    "static28": ("static", 28),
}

PAIRS = [
    {
        "key": "opsd_frozen_vs_sliding",
        "task": "opsd",
        "a": "frozen_ridge",
        "b": "sliding_ridge_d2",
        "role": "headline",
    },
    {
        "key": "opsd_frozen_vs_tso",
        "task": "opsd",
        "a": "frozen_ridge",
        "b": "external_forecast",
        "role": "headline",
    },
    {
        "key": "opsd_tso_vs_sliding",
        "task": "opsd",
        "a": "external_forecast",
        "b": "sliding_ridge_d2",
        "role": "headline",
    },
    {
        "key": "monash_frozen_vs_sliding",
        "task": "monash",
        "a": "frozen_ridge",
        "b": "sliding_ridge_d2",
        "role": "control",
    },
    {
        "key": "binance_frozen_vs_sliding",
        "task": "binance",
        "a": "frozen",
        "b": "sliding",
        "role": "null_control",
    },
]
GRAN = {  # per-task granularity and episode geometry (steps)
    "opsd": {"step": "day", "H": 365, "roll_step": 7, "b_null": 7, "bS": 7, "bL": 28, "cal": 30},
    "monash": {"step": "day", "H": 180, "roll_step": 7, "b_null": 7, "bS": 7, "bL": 28, "cal": 30},
    "binance": {
        "step": "hour",
        "H": 2000,
        "roll_step": 168,
        "b_null": 24,
        "bS": 24,
        "bL": 168,
        "cal": 168,
    },
}


# ================================================================ data loading (dev + validation only)
def load_audit():
    spec = importlib.util.spec_from_file_location(
        "audit_real_data", ROOT / "scripts/decision_value/audit_real_data.py"
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.headroom = lambda *a, **k: {}  # losses only; headroom already computed in phase 1
    return m


def _read_losses(d: Path):
    return pd.read_csv(d / "per_step_losses.csv")


def load_opsd(audit, root, cache):
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
    y, ext = df["DE_load_actual_entsoe_transparency"], df["DE_load_forecast_entsoe_transparency"]
    fit = ("2015-01-01", "2016-12-31")
    out = {}
    for tag, win in (("val", ("2017-01-01", "2017-12-31")), ("dev", ("2018-01-01", "2019-12-31"))):
        audit.day_ahead_task(
            f"opsd_{tag}",
            y,
            "Europe/Berlin",
            fit,
            "2017-12-31",
            win,
            delays=(2,),
            ext=ext,
            outdir=cache / f"opsd_{tag}",
            rng=None,
        )
        out[tag] = _read_losses(cache / f"opsd_{tag}")
    return out, {"data_file": str(p), "rows_read": 43824, "max_utc_read": str(df.index.max())}


def load_monash(audit, root, cache):
    z = zipfile.ZipFile(root / "raw/monash/4656140/electricity_hourly_dataset.zip")
    name = next(n for n in z.namelist() if n.endswith(".tsf"))
    N = 24 * (366 + 365)
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
    assert y.index.max() < pd.Timestamp("2014-01-01")
    fit = ("2012-01-01", "2012-12-31")
    out = {}
    for tag, win in (("val", ("2013-01-01", "2013-03-31")), ("dev", ("2013-04-01", "2013-12-31"))):
        audit.day_ahead_task(
            f"monash_{tag}",
            y,
            None,
            fit,
            "2013-03-31",
            win,
            delays=(2,),
            outdir=cache / f"monash_{tag}",
            rng=None,
        )
        out[tag] = _read_losses(cache / f"monash_{tag}")
    return out, {"n_series_aggregated": n_series, "values_parsed_per_series": N}


def load_binance(root, cache, delay_bars=1, refit_every=24, win=720):
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

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
    ts = pd.to_datetime(k.o.astype("int64") // 1000, unit="ms")
    assert (np.diff(ts.values).astype("timedelta64[h]").astype(int) == 1).all()
    assert ts.max() < pd.Timestamp("2026-01-01")
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
    yv = (np.append(r[1:], np.nan) > 0).astype(int)
    jul = int(ts.searchsorted(pd.Timestamp("2025-07-01")))
    apr = int(ts.searchsorted(pd.Timestamp("2025-04-01")))

    def pair(dev_start, stop):
        tr0 = np.arange(30, dev_start - 1)
        sc = StandardScaler().fit(F[tr0])
        Fs = sc.transform(np.nan_to_num(F))
        f0 = LogisticRegression(C=1.0, max_iter=500).fit(Fs[tr0], yv[tr0])
        l0, l1, m1 = [], [], None
        for t in range(dev_start, stop):
            if (t - dev_start) % refit_every == 0:
                hi = t - delay_bars
                m1 = LogisticRegression(C=1.0, max_iter=500).fit(
                    Fs[max(30, hi - win) : hi], yv[max(30, hi - win) : hi]
                )
            l0.append(float(f0.predict(Fs[t : t + 1])[0] != yv[t]))
            l1.append(float(m1.predict(Fs[t : t + 1])[0] != yv[t]))
        return pd.DataFrame(
            {"ts": ts[dev_start:stop].astype(str).to_numpy(), "frozen": l0, "sliding": l1}
        )

    # pseudo-validation: same pair specification shifted back one quarter (frozen on Jan-Mar, evaluated Apr-Jun)
    val = pair(apr, jul - 1)
    dev = pair(jul, n - 1)
    return {"val": val, "dev": dev}, {
        "val_window": "2025-04-01..2025-06-30 (frozen trained Jan-Mar)",
        "dev_window": "2025-07-01..2025-12-31",
        "max_ts_loaded": str(ts.max()),
    }


# ================================================================ replay machinery
def make_controller(spec, n, T, c_s, fac, thr):
    name, _, arg = spec.partition(":")
    if name == "permanent":
        return C.Permanent(n, T, c_s)
    if name == "hold":
        return C.Hold(n, T, c_s, H=int(arg))
    if name == "reverse":
        return C.Reverse(n, T, c_s, rev_factory=fac, rev_threshold=thr)
    if name == "calendar":
        return C.CalendarBatch(n, T, c_s, K=int(arg))
    if name == "static":
        return C.StaticThreshold(n, T, c_s, W=int(arg))
    raise ValueError(spec)


def block_ci(v: np.ndarray, block: int, B: int = 1000, seed: int = 1):
    n = len(v)
    if n < 3:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    idx = DA.block_indices(rng, n, n, B, min(block, n))
    m = v[idx].mean(axis=1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def episode_rows(base, es, Lsum, Ns, first_alarm, orc, extra_ci_block=None):
    """One row per c_s for a (cell, method)."""
    rows = []
    n, T = es.n, es.T
    never = es.raw0.sum(axis=1)
    for cs in COSTS:
        cost = Lsum + cs * Ns
        V = never - cost
        r = dict(
            base,
            c_s=cs,
            n_ep=n,
            cost_mean=float(cost.mean()),
            N_s_mean=float(Ns.mean()),
            never_mean=float(never.mean()),
            dyn_mean=orc["dyn"][cs],
            static_mean=orc["static"][cs],
            V_mean=float(V.mean()),
            V_sd=float(V.std(ddof=1)) if n > 1 else np.nan,
            V_q025=float(np.quantile(V, 0.025)),
            V_q975=float(np.quantile(V, 0.975)),
            p_V_pos=float((V > 0).mean()),
            V_ci_lo=np.nan,
            V_ci_hi=np.nan,
        )
        if extra_ci_block:
            r["V_ci_lo"], r["V_ci_hi"] = block_ci(V, extra_ci_block)
        if first_alarm is not None:
            fa = np.where(np.isnan(first_alarm), T, first_alarm)
            r.update(
                power=float((~np.isnan(first_alarm)).mean()), first_alarm_cens_mean=float(fa.mean())
            )
        rows.append(r)
    return rows


def oracles(es):
    out = {"dyn": {}, "static": {}}
    never, always = es.raw0.sum(axis=1), es.raw1.sum(axis=1)
    for cs in COSTS:
        out["dyn"][cs] = float(dp_two_state(es.raw0, es.raw1, cs).mean())
        out["static"][cs] = float(np.minimum(never, always + cs).mean())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root")
    ap.add_argument("--out-root", default=str(ROOT / "outputs/decision_value/real_data/dev"))
    ap.add_argument("--pairs", nargs="+", default=[p["key"] for p in PAIRS])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--n-cal", type=int, default=2000)
    ap.add_argument("--n-masks", type=int, default=100)
    ap.add_argument("--n-boot", type=int, default=100)
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--analyze-only", default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument(
        "--merge", nargs="+", default=None, help="OUT_DIR PART_DIR... : merge part runs and analyse"
    )
    a = ap.parse_args(argv)
    if a.merge:
        merge(Path(a.merge[0]), [Path(x) for x in a.merge[1:]])
        return
    if a.analyze_only:
        analyze(Path(a.analyze_only))
        return
    if a.smoke:
        a.n_cal, a.n_masks, a.n_boot = 150, 6, 6
    t0 = time.time()
    root = Path(a.data_root)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = a.run_id or f"replay_{ts}"
    out = Path(a.run_dir) if a.run_dir else Path(a.out_root) / run_id
    out.mkdir(parents=True, exist_ok=True)
    cache = out / "losses"
    audit = load_audit()
    want = [p for p in PAIRS if p["key"] in a.pairs]
    tasks = {p["task"] for p in want}
    data, prov = {}, {}
    if "opsd" in tasks:
        data["opsd"], prov["opsd"] = load_opsd(audit, root, cache)
    if "monash" in tasks:
        data["monash"], prov["monash"] = load_monash(audit, root, cache)
    if "binance" in tasks:
        data["binance"], prov["binance"] = load_binance(root, cache)

    pairs = []
    for p in want:
        d = data[p["task"]]
        g = GRAN[p["task"]]
        if p["task"] == "binance":
            labels = d["dev"]["ts"].tolist()
        else:
            labels = [str(datetime.fromordinal(int(o)).date()) for o in d["dev"]["day_ordinal"]]
        pairs.append(
            DA.PairSeries(
                name=p["key"],
                role=p["role"],
                incumbent=p["a"],
                challenger=p["b"],
                loss_unit="percent of fit-window mean load, daily MAE"
                if p["task"] != "binance"
                else "0/1 direction error",
                step=g["step"],
                val0=d["val"][p["a"]].to_numpy(float),
                val1=d["val"][p["b"]].to_numpy(float),
                dev0=d["dev"][p["a"]].to_numpy(float),
                dev1=d["dev"][p["b"]].to_numpy(float),
                dev_labels=labels,
                meta={"task": p["task"], **g},
            )
        )

    # ---- step 2: scaling + deployable diagnostics from the validation window only (before any replay)
    scaling, diag = {}, {}
    for pr in pairs:
        sp = DA.fit_scaling(pr.val0, pr.val1)
        scaling[pr.name] = {**sp.to_dict(), "incumbent_cap_B": DA.fit_incumbent_cap(pr.val0)}
        diag[pr.name] = DA.deployable_diagnostics(pr.val0, pr.val1)
    (out / "scaling.json").write_text(json.dumps(scaling, indent=1))
    (out / "diagnostics.json").write_text(json.dumps(diag, indent=1))
    print("diagnostics written", file=sys.stderr)

    rows, ident, calib, detect, setinfo = [], [], [], {}, {}
    n_episodes = 0
    for pi, pr in enumerate(pairs):
        g = pr.meta
        Binc = scaling[pr.name]["incumbent_cap_B"]
        sp = DA.ScaleSpec(**{k: v for k, v in scaling[pr.name].items() if k != "incumbent_cap_B"})
        v0, v1, _ = DA.apply_scaling(pr.val0, pr.val1, sp)
        vi, _ = DA.apply_incumbent_scaling(pr.val0, Binc)
        s0, s1, nclip = DA.apply_scaling(pr.dev0, pr.dev1, sp)
        si, nclip_inc = DA.apply_incumbent_scaling(pr.dev0, Binc)
        T = len(pr.dev0)
        H = g["H"]
        assert np.abs(s0 - s1).max() <= 1 + 1e-9
        setinfo[pr.name] = {
            "T_dev": T,
            "dev_start": pr.dev_labels[0],
            "dev_end": pr.dev_labels[-1],
            "n_val": len(pr.val0),
            "n_dev_paired_clipped_steps": nclip,
            "n_dev_incumbent_clipped_steps": nclip_inc,
            "mean_raw_loss_inc": float(pr.dev0.mean()),
            "mean_raw_loss_chal": float(pr.dev1.mean()),
        }
        targets = [("paired", MONITORS), ("incumbent", INC_MONITORS)]
        thr = {}
        for target, mons in targets:
            for mon in mons:
                fac = monitor_factory(mon, target, g["cal"], **HP[mon])
                for d in DELAYS:
                    for q in QS:
                        th, fr = DA.calibrate_horizons(
                            fac,
                            vi if target == "incumbent" else v0,
                            v1,
                            target,
                            q,
                            d,
                            sorted({T, H}),
                            g["b_null"],
                            ALPHA,
                            a.n_cal,
                            chunk=min(500, a.n_cal),
                            n_fresh=min(500, a.n_cal),
                        )
                        for h in th:
                            thr[(target, mon, d, q, h)] = th[h]
                            calib.append(
                                {
                                    "pair": pr.name,
                                    "target": target,
                                    "monitor": mon,
                                    "d": d,
                                    "q": q,
                                    "horizon": h,
                                    "threshold": th[h],
                                    "fresh_null_alarm_rate": fr[h],
                                }
                            )
        print(f"[{pr.name}] calibrated ({time.time() - t0:.0f}s)", file=sys.stderr)

        sets = {}

        def get_set(mode, q, *, pr=pr, s0=s0, s1=s1, si=si, pi=pi, H=H, g=g, sets=sets):
            key = (mode, q if mode == "actual" else None)
            if key not in sets:
                if mode == "actual":
                    es = DA.actual_set(pr.dev0, pr.dev1, s0, s1, 1 if q == 1.0 else a.n_masks, si)
                elif mode == "roll":
                    es = DA.roll_set(pr.dev0, pr.dev1, s0, s1, H, g["roll_step"], si)
                else:
                    b = g["bS"] if mode == "bootS" else g["bL"]
                    es = DA.boot_set(
                        pr.dev0,
                        pr.dev1,
                        s0,
                        s1,
                        b,
                        a.n_boot,
                        [SEED, pi, 7 if mode == "bootS" else 8],
                        si,
                    )
                sets[key] = (es, oracles(es))
            return sets[key]

        for mi, mode in enumerate(("actual", "roll", "bootS", "bootL")):
            for qi, q in enumerate(QS):
                es, orc = get_set(mode, q)
                n_episodes += es.n
                Tm = es.T
                batch = DA.episode_batch(es, q, [SEED, pi, mi, qi])
                batch_inc = DA.episode_batch(es, q, [SEED, pi, mi, qi], "incumbent")
                ci_block = -(-H // g["roll_step"]) if mode == "roll" else None
                setinfo.setdefault(pr.name, {})[f"{mode}_n"] = es.n
                for d in DELAYS:
                    fb = FeedbackContract(q, d)
                    base0 = {"pair": pr.name, "mode": mode, "q": q, "d": d}
                    # reference methods (monitor-free)
                    for cs in COSTS:
                        pass
                    never = es.raw0.sum(axis=1)
                    rows += episode_rows(
                        dict(base0, target="-", monitor="-", controller="never"),
                        es,
                        never,
                        np.zeros(es.n),
                        None,
                        orc,
                        ci_block,
                    )
                    rows += episode_rows(
                        dict(base0, target="-", monitor="-", controller="always"),
                        es,
                        es.raw1.sum(axis=1),
                        np.ones(es.n),
                        None,
                        orc,
                        ci_block,
                    )
                    for rname, (kind, arg) in CAL_BLOCK_REFS.items():
                        if kind == "calendar":
                            ctrl = make_controller(f"calendar:{arg}", es.n, Tm, 0.0, None, np.inf)
                            sim = simulate(batch, fb, None, ctrl)
                            Ls, Ns = DA.cost_parts(sim.actions, es.raw0, es.raw1)
                            rows += episode_rows(
                                dict(base0, target="-", monitor="-", controller=rname),
                                es,
                                Ls,
                                Ns,
                                None,
                                orc,
                                ci_block,
                            )
                        else:  # static economic rule depends on c_s -> one sim per c_s
                            for cs in COSTS:
                                ctrl = make_controller(f"static:{arg}", es.n, Tm, cs, None, np.inf)
                                sim = simulate(batch, fb, None, ctrl)
                                Ls, Ns = DA.cost_parts(sim.actions, es.raw0, es.raw1)
                                rr = episode_rows(
                                    dict(base0, target="-", monitor="-", controller=rname),
                                    es,
                                    Ls,
                                    Ns,
                                    None,
                                    orc,
                                    ci_block,
                                )
                                rows += [r for r in rr if r["c_s"] == cs]
                    # monitored methods
                    for target, mons in targets:
                        ctrls = ["permanent", "hold:7", "hold:30"] + (
                            ["reverse"] if target == "paired" else []
                        )
                        if target == "incumbent":
                            ctrls = ["permanent", "hold:7"]
                        for mon in mons:
                            fac = monitor_factory(mon, target, g["cal"], **HP[mon])
                            th = thr[(target, mon, d, q, Tm)]
                            for cspec in ctrls:
                                m = fac(es.n)
                                m.threshold = th
                                facp = monitor_factory(mon, "paired", g["cal"], **HP[mon])
                                ctrl = make_controller(cspec, es.n, Tm, 0.0, facp, th)
                                sim = simulate(
                                    batch if target == "paired" else batch_inc, fb, m, ctrl
                                )
                                Ls, Ns = DA.cost_parts(sim.actions, es.raw0, es.raw1)
                                al = sim.alarm
                                fa = np.where(al.any(axis=1), al.argmax(axis=1), np.nan)
                                cname = cspec.replace(":", "")
                                rows += episode_rows(
                                    dict(base0, target=target, monitor=mon, controller=cname),
                                    es,
                                    Ls,
                                    Ns,
                                    fa,
                                    orc,
                                    ci_block,
                                )
                                # identity check (exact)
                                kind = {
                                    "permanent": "permanent",
                                    "hold": "hold",
                                    "reverse": "reverse",
                                }[cspec.split(":")[0]]
                                Hh = int(cspec.split(":")[1]) if ":" in cspec else 0
                                if kind == "permanent" or mode in ("actual", "roll"):
                                    for cs in COSTS:
                                        Vid = DA.identity_value(
                                            kind, al, sim.actions, es.raw0, es.raw1, cs, Hh
                                        )
                                        Vdir = es.raw0.sum(axis=1) - (Ls + cs * Ns)
                                        ident.append(
                                            {
                                                "pair": pr.name,
                                                "mode": mode,
                                                "target": target,
                                                "monitor": mon,
                                                "controller": cname,
                                                "d": d,
                                                "q": q,
                                                "c_s": cs,
                                                "max_abs_err": float(np.abs(Vid - Vdir).max()),
                                            }
                                        )
                                if mode == "actual" and q == 1.0:
                                    key = f"{pr.name}|{target}|{mon}|{cname}|d{d}"
                                    if kind == "permanent":
                                        detect[key] = {
                                            "first_alarm": pr.dev_labels[int(fa[0])]
                                            if not np.isnan(fa[0])
                                            else None,
                                            "first_alarm_step": None
                                            if np.isnan(fa[0])
                                            else int(fa[0]),
                                            "n_alarm_steps_raw_stream": int(al[0].sum()),
                                        }
                                    elif kind == "hold":
                                        trig = np.flatnonzero(DA.hold_triggers(al, Hh)[0])
                                        detect[key] = {
                                            "n_triggers": len(trig),
                                            "trigger_dates": [pr.dev_labels[i] for i in trig[:12]],
                                        }
                                    else:
                                        sw = np.flatnonzero(
                                            np.diff(np.concatenate([[0], sim.actions[0]]))
                                        )
                                        detect[key] = {
                                            "n_switches": len(sw),
                                            "switch_dates": [pr.dev_labels[i] for i in sw[:12]],
                                        }
                print(
                    f"[{pr.name}] mode={mode} q={q} done ({time.time() - t0:.0f}s)", file=sys.stderr
                )
        # per-pair incremental save
        pd.DataFrame(rows).to_csv(out / "cells.csv.gz", index=False)

    df = pd.DataFrame(rows)
    df.to_csv(out / "cells.csv.gz", index=False)
    pd.DataFrame(ident).to_csv(out / "identity_check.csv", index=False)
    pd.DataFrame(calib).to_csv(out / "calibration.csv", index=False)
    (out / "detection_actual.json").write_text(json.dumps(detect, indent=1))
    (out / "set_info.json").write_text(json.dumps(setinfo, indent=1))
    for pr in pairs:  # raw per-step dev losses for audit trail
        pd.DataFrame({"label": pr.dev_labels, "l0": pr.dev0, "l1": pr.dev1}).to_csv(
            out / f"dev_losses_{pr.name}.csv", index=False
        )
    cfg = dict(
        vars(a),
        costs=COSTS,
        delays=DELAYS,
        qs=QS,
        holds=HOLDS,
        monitors=MONITORS,
        hp=HP,
        alpha=ALPHA,
        scale_c=DA.SCALE_C,
        gran=GRAN,
        pairs=[p["key"] for p in want],
        provenance=prov,
        label="development replay",
        reserved_windows_read=False,
    )
    (out / "config.json").write_text(json.dumps(cfg, indent=1, default=str))
    runtime = time.time() - t0
    append_run(
        run_id,
        cfg,
        {"eval": SEED, "calibration": 5_100_000, "calibration_check": 5_200_000},
        n_episodes,
        runtime,
        [out / "cells.csv.gz", out / "identity_check.csv", out / "diagnostics.json"],
    )
    print(f"run_id={run_id} runtime={runtime:.0f}s", file=sys.stderr)
    analyze(out)


def merge(out: Path, parts):
    out.mkdir(parents=True, exist_ok=True)
    for f in ("cells.csv.gz", "identity_check.csv", "calibration.csv"):
        pd.concat([pd.read_csv(p / f) for p in parts], ignore_index=True).to_csv(
            out / f, index=False
        )
    for f in ("detection_actual.json", "set_info.json", "scaling.json", "diagnostics.json"):
        m = {}
        for p in parts:
            m.update(json.loads((p / f).read_text()))
        (out / f).write_text(json.dumps(m, indent=1))
    cfgs = [json.loads((p / "config.json").read_text()) for p in parts]
    (out / "config.json").write_text(
        json.dumps({"merged_parts": [str(p) for p in parts], "part_configs": cfgs}, indent=1)
    )
    for p in parts:
        for f in p.glob("dev_losses_*.csv"):
            (out / f.name).write_bytes(f.read_bytes())
    analyze(out)


# ================================================================ analysis tables
def md(df: pd.DataFrame, floatfmt="{:.2f}") -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        lines.append(
            "| "
            + " | ".join(
                floatfmt.format(v)
                if isinstance(v, (float, np.floating)) and np.isfinite(v)
                else ("" if isinstance(v, float) else str(v))
                for v in r
            )
            + " |"
        )
    return "\n".join(lines)


def analyze(out: Path):
    df = pd.read_csv(out / "cells.csv.gz")
    ident = pd.read_csv(out / "identity_check.csv")
    cal = pd.read_csv(out / "calibration.csv")
    diag = json.loads((out / "diagnostics.json").read_text())
    scaling = json.loads((out / "scaling.json").read_text())
    setinfo = json.loads((out / "set_info.json").read_text())
    df["V"] = df.never_mean - df.cost_mean
    df["H_T"] = df.never_mean - df.dyn_mean
    df["V_over_H"] = df.V / df.H_T.where(df.H_T > 1e-12)
    keys = ["pair", "mode", "q", "d", "c_s"]
    refs = df[df.controller.isin(["never", "always", "calendar14", "calendar28", "static28"])]
    best_ref = refs.groupby(keys).cost_mean.min().rename("bestref_cost")
    best_ref_name = refs.loc[refs.groupby(keys).cost_mean.idxmin(), keys + ["controller"]].rename(
        columns={"controller": "bestref"}
    )
    df = df.merge(best_ref.reset_index(), on=keys).merge(best_ref_name, on=keys)
    df["V_vs_bestref"] = df.bestref_cost - df.cost_mean
    df.to_csv(out / "cells_with_derived.csv.gz", index=False)
    T = []
    T.append("# Tables (auto-generated by run_real_data.py --analyze-only)\n")
    T.append(
        "## Scaling (validation window only)\n"
        + md(pd.DataFrame(scaling).T.reset_index().rename(columns={"index": "pair"}), "{:.4g}")
    )
    T.append(
        "\n## Dev windows\n"
        + md(pd.DataFrame(setinfo).T.reset_index().rename(columns={"index": "pair"}), "{:.4g}")
    )
    # diagnostics
    rows = []
    for p, dg in diag.items():
        r = dg["recipe"]
        row = {
            "pair": p,
            "Delta_hat": dg["Delta_hat"],
            "sigma_hat": dg["sigma_hat"],
            "t_NW": dg["t_stat_NW"],
            "acf1": dg["acf_lag1"],
            "acf7": dg["acf_lag7"],
            "acf28": dg["acf_lag28"],
            "half_life": dg["half_life_steps"],
            "n_runs": r["n_runs"],
            "L_hat": r["L_hat"],
            "Delta_opp": r["Delta_opp"],
            "I_hat": r["I_hat"],
            "I_perm_p95": dg["perm_null"]["I_hat_p95"],
            "L_perm_p95": dg["perm_null"]["L_hat_p95"],
        }
        for k, v in dg["kappa_hat"].items():
            row[f"kappa_{k}"] = v["kappa_hat"]
            row[f"kp95_{k}"] = v["perm_p95"]
        rows.append(row)
    dgd = pd.DataFrame(rows)
    T.append("\n## Deployable diagnostics (validation window only)\n" + md(dgd, "{:.3g}"))
    # reference + oracle table at actual series, q=1 (d irrelevant for never/always/oracles)
    act = df[(df["mode"] == "actual") & (df.q == 1.0) & (df.d == 1)]
    rt = (
        act[act.controller.isin(["never", "always", "calendar14", "calendar28", "static28"])]
        .pivot_table(index=["pair", "controller"], columns="c_s", values="cost_mean")
        .reset_index()
    )
    orc = (
        act[act.controller == "never"]
        .groupby(["pair", "c_s"])
        .agg(dyn=("dyn_mean", "first"), stat=("static_mean", "first"))
        .reset_index()
    )
    T.append(
        "\n## References on the actual dev series (q=1, d=1), cost by c_s\n" + md(rt, "{:.1f}")
    )
    T.append(
        "\n## Hindsight oracles on realised losses\n"
        + md(
            orc.pivot_table(index="pair", columns="c_s", values=["dyn", "stat"]).reset_index(),
            "{:.1f}",
        )
    )
    # V tables actual series
    for d, q in ((1, 1.0), (7, 0.25)):
        for p in df.pair.unique():
            sub = df[
                (df.pair == p)
                & (df["mode"] == "actual")
                & (df.d == d)
                & (df.q == q)
                & (df.monitor != "-")
            ]
            pv = sub.pivot_table(
                index=["target", "monitor", "controller"], columns="c_s", values="V"
            ).reset_index()
            T.append(
                f"\n## V vs never, actual series, {p}, d={d}, q={q} (mean over {int(sub.n_ep.iloc[0])} masks)\n"
                + md(pv, "{:.1f}")
            )
    # identity
    idt = ident.groupby(["pair", "controller"]).max_abs_err.max().reset_index()
    T.append(
        "\n## Identity check: max |V_identity - V_direct| over all checked cells\n"
        + md(idt, "{:.2e}")
    )
    # calibration
    cs = (
        cal.groupby(["pair", "target", "monitor"])
        .agg(
            thr_min=("threshold", "min"),
            thr_max=("threshold", "max"),
            fresh_rate_mean=("fresh_null_alarm_rate", "mean"),
            fresh_rate_max=("fresh_null_alarm_rate", "max"),
        )
        .reset_index()
    )
    T.append("\n## Calibration (fresh-seed null alarm rate, target 0.05)\n" + md(cs, "{:.3f}"))
    (out / "tables.md").write_text("\n".join(T), encoding="utf8")
    # ranking agreement
    rk = []
    for (p, mode, q, d, c), g in df[
        (df.target == "paired") & (df.controller == "permanent")
    ].groupby(["pair", "mode", "q", "d", "c_s"]):
        if len(g) < 3:
            continue
        det_score = -g.first_alarm_cens_mean.to_numpy()  # earlier first alarm = better detection
        pw = g.power.to_numpy()
        v = g.V.to_numpy()
        from scipy.stats import spearmanr

        r1 = (
            spearmanr(det_score, v).statistic if np.ptp(det_score) > 0 and np.ptp(v) > 0 else np.nan
        )
        r2 = spearmanr(pw, v).statistic if np.ptp(pw) > 0 and np.ptp(v) > 0 else np.nan
        rk.append(
            {
                "pair": p,
                "mode": mode,
                "q": q,
                "d": d,
                "c_s": c,
                "rho_delay_vs_V": r1,
                "rho_power_vs_V": r2,
                "top_det_is_top_V": bool(
                    g.monitor.iloc[int(np.argmax(det_score))] == g.monitor.iloc[int(np.argmax(v))]
                ),
                "most_powerful_worse_than_least": bool(
                    v[int(np.argmax(pw))] < v[int(np.argmin(pw))]
                ),
            }
        )
    rk = pd.DataFrame(rk)
    rk.to_csv(out / "ranking_agreement.csv", index=False)
    summ = (
        rk.groupby(["pair", "mode"])
        .agg(
            rho_delay=("rho_delay_vs_V", "mean"),
            rho_power=("rho_power_vs_V", "mean"),
            top_agree=("top_det_is_top_V", "mean"),
            power_rev=("most_powerful_worse_than_least", "mean"),
            n=("c_s", "size"),
        )
        .reset_index()
    )
    (out / "tables.md").write_text(
        (out / "tables.md").read_text(encoding="utf8")
        + "\n\n## Ranking agreement (permanent, paired target)\n"
        + md(summ, "{:.2f}"),
        encoding="utf8",
    )
    summ.to_csv(out / "ranking_agreement_summary.csv", index=False)
    print("analysis written", file=sys.stderr)


if __name__ == "__main__":
    main()
