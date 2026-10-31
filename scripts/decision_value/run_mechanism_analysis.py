"""Mechanism analysis for the monitoring-to-decision-value programme (DEVELOPMENT, synthetic Setting C).

Subcommands (each = simulate cells with the engine under CRN, then analyse; `analyze` re-analyses a dir):
  th1  P2 switching-cost crossing         (S3 strong, fixed tau, Permanent)
  th2  P3 incumbent-target reversal (H4)  (S3, 5 challenger types x {incumbent, paired}, Permanent)
  th3  P5 Markov precision + ceiling      (S2, Hold(H))
  th4  P6 conversion number, H1, H3       (S1 grid, Hold(L/2))
  analyze --exp th1|th2|th3|th4 --dir DIR
Every cell also yields an H6 comparison (best monitor vs best simple reference).

Monitor set (DECLARED BEFORE any cost result was inspected; all calibrated to P(any alarm by T)=0.05 on
the null, n_cal=6000, seeds 5,000,000 / 5,000,001):
  cusum (k=.02), cusum_k005 (k=.005), cusum_k06 (k=.06), page_hinkley (delta=.005), ph_d03 (delta=.03),
  batch (n_b=50), batch_nb20, batch_nb200, sr_betting, kelly_h2c_inspired.
Development seeds only (< 7,000,000); outputs under outputs/decision_value/development/mech_<exp>_<ts>/.
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import itertools
import json
import sys
import time
from datetime import UTC, datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_value import controllers as C
from shiftlab.decision_value.calibration import null_maxima
from shiftlab.decision_value.contracts import CostContract, FeedbackContract
from shiftlab.decision_value.evaluation import score, simulate
from shiftlab.decision_value.monitors import monitor_factory
from shiftlab.decision_value.oracles import oracle_costs
from shiftlab.decision_value.registry import append_run
from shiftlab.decision_value.statistics import classify_reversal
from shiftlab.decision_value.synthetic import Family

DEV_OUT = ROOT / "outputs" / "decision_value" / "development"
CAL_DIR = DEV_OUT / "_calibration_cache"
N_CAL, CAL_SEED, ALPHA = 6000, 5_000_000, 0.05
MON = {  # label -> (engine monitor name, hyperparameters)
    "cusum": ("cusum", {}),
    "cusum_k005": ("cusum", {"k": 0.005}),
    "cusum_k06": ("cusum", {"k": 0.06}),
    "page_hinkley": ("page_hinkley", {}),
    "ph_d03": ("page_hinkley", {"delta": 0.03}),
    "batch": ("batch", {}),
    "batch_nb20": ("batch", {"n_b": 20}),
    "batch_nb200": ("batch", {"n_b": 200}),
    "sr_betting": ("sr_betting", {}),
    "kelly_h2c_inspired": ("kelly_h2c_inspired", {}),
}
MONS = list(MON)
REFS = {
    "never": "never",
    "always": "always",
    "calendar100": "calendar:100",
    "calendar200": "calendar:200",
    "calendar400": "calendar:400",
}
KEYS = (
    "cost_exp",
    "cost_real",
    "N_s",
    "first_alarm",
    "n_alarms",
    "any_alarm",
    "power_T",
    "power_opp",
    "delay",
    "delay_cens",
    "false_alarm_pre_tau",
    "t_chal_in_opp",
    "harm_before_switch",
    "tau",
)
ORC_KEYS = (
    "never_exp",
    "always_exp",
    "static_exp",
    "dynamic_exp",
    "headroom_exp",
    "headroom_static_exp",
    "clairvoyant_exp",
)
BOOT = 10_000


# ----------------------------------------------------------------------------- utilities
def build_controller(spec, n, T, c_s):
    name, _, arg = spec.partition(":")
    if name == "permanent":
        return C.Permanent(n, T, c_s)
    if name == "hold":
        return C.Hold(n, T, c_s, H=int(arg))
    if name == "never":
        return C.NeverSwitch(n, T, c_s)
    if name == "always":
        return C.AlwaysChallenger(n, T, c_s)
    if name == "calendar":
        return C.CalendarBatch(n, T, c_s, K=int(arg))
    raise SystemExit(f"unknown controller {spec}")


def calib_path(label, target, q, d, p):
    key = json.dumps(
        [MON[label], target, q, d, p["T"], p["p0"], p["delta"], N_CAL, CAL_SEED, ALPHA],
        sort_keys=True,
    )
    return (
        CAL_DIR / f"{label}_{target}_q{q}_d{d}_{hashlib.sha1(key.encode()).hexdigest()[:10]}.json"
    )


def get_threshold(label, target, q, d, fam):
    path = calib_path(label, target, q, d, fam.params)
    if path.exists():
        return json.loads(path.read_text())
    name, hp = MON[label]
    fac = monitor_factory(name, target=target, **hp)
    fb = FeedbackContract(q, d)
    mx = null_maxima(fac, fam, fb, N_CAL, CAL_SEED)
    thr = float(np.quantile(mx, 1 - ALPHA, method="higher"))
    fresh = null_maxima(fac, fam, fb, N_CAL, CAL_SEED + 1)
    info = {
        "threshold": thr,
        "null_rate_cal": float((mx > thr).mean()),
        "null_rate_fresh": float((fresh > thr).mean()),
    }
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(info))
    os.replace(tmp, path)
    return info


def _calib_task(t):
    label, target, q, d, family, params = t
    t0 = time.time()
    get_threshold(label, target, q, d, Family(family, params))
    return time.time() - t0


def prefill(specs, procs):
    tasks = {}
    for s in specs:
        fam = Family(s["family"], s["params"])
        for m in s["monitors"]:
            tasks[str(calib_path(m, s["target"], s["q"], s["d"], fam.params))] = (
                m,
                s["target"],
                s["q"],
                s["d"],
                s["family"],
                s["params"],
            )
    todo = [t for k, t in tasks.items() if not Path(k).exists()]
    print(f"calibration: {len(todo)} of {len(tasks)} thresholds to compute", flush=True)
    t0 = time.time()
    if todo:
        with Pool(procs) as pool:
            for i, _ in enumerate(pool.imap_unordered(_calib_task, todo), 1):
                if i % 10 == 0:
                    print(f"  calib {i}/{len(todo)}", flush=True)
    return time.time() - t0


def put(store, label, rec):
    for k in KEYS:
        store[f"{label}|{k}"] = np.asarray(rec[k])


# ----------------------------------------------------------------------------- cell runner
def run_cell(arg):
    spec, outdir = arg
    t0 = time.time()
    n = spec["n"]
    fam = Family(spec["family"], spec["params"])
    fb, cost = FeedbackContract(spec["q"], spec["d"]), CostContract(0.0, spec["c_s"])
    T = fam.T
    batch, truth = fam.generate(spec["seed"], n, fb)
    orc = oracle_costs(batch, truth, cost)
    store = {f"__orc|{k}": orc[k] for k in ORC_KEYS}
    meta = {"spec": spec, "thresholds": {}, "checks": {}}
    adv = truth.advantage
    if spec.get("permanent_identity"):
        Wsuf = np.cumsum(adv[:, ::-1], axis=1)[:, ::-1]
        meta["checks"]["delta_t_constant_across_episodes"] = bool(np.ptp(adv, axis=0).max() == 0)
        store["__delta_t"] = adv[0]
    if spec["family"] == "s2":
        p = fam.params
        rho = p["rho"]
        lam, pib = 2 * rho - 1, 0.5
        Db = p["Delta"] if p["challenger_bad"] == "useful" else 0.0
        H = int(spec["controller"].split(":")[1])
        S = np.arange(T)
        B_S = np.minimum(H, T - S)
        A_S = (1 - lam**B_S) / (1 - lam)
        rev_S = (S + H <= T - 1).astype(float)
        base_S = B_S * (pib * (Db + p["delta"]) - p["delta"]) - spec["c_s"] * (1 + rev_S)
        slope_S = (Db + p["delta"]) * A_S
        theta_max = pib + (1 - pib) * lam ** (spec["d"] + 1)
        meta["p5"] = {
            "lam": lam,
            "pi_b": pib,
            "Delta_bad": Db,
            "delta": p["delta"],
            "H": H,
            "theta_max": theta_max,
            "G_untrunc_at_ceiling": float(
                H * (pib * (Db + p["delta"]) - p["delta"])
                + (theta_max - pib) * (Db + p["delta"]) * (1 - lam**H) / (1 - lam)
                - 2 * spec["c_s"]
            ),
            "G_untrunc_at_stationary": float(
                H * (pib * (Db + p["delta"]) - p["delta"]) - 2 * spec["c_s"]
            ),
        }
        bad = truth.regime == 1
    for label in spec["monitors"]:
        name, hp = MON[label]
        fac = monitor_factory(name, target=spec["target"], **hp)
        info = get_threshold(label, spec["target"], spec["q"], spec["d"], fam)
        meta["thresholds"][label] = info
        mon = fac(n)
        mon.threshold = info["threshold"]
        ctrl = build_controller(spec["controller"], n, T, cost.c_s)
        sim = simulate(batch, fb, mon, ctrl)
        rec = score(sim, batch, truth, cost)
        put(store, label, rec)
        if spec.get("permanent_identity"):
            fa = rec["first_alarm"]
            idx = np.nan_to_num(fa, nan=0).astype(int)
            store[f"{label}|W_at_S"] = np.where(rec["any_alarm"], Wsuf[np.arange(n), idx], 0.0)
        if spec.get("cs_grid"):
            for c in spec["cs_grid"]:
                store[f"{label}|cost@{c}"] = score(sim, batch, truth, CostContract(0.0, c))[
                    "cost_exp"
                ]
            mon2 = fac(n)
            mon2.threshold = info["threshold"]
            sim2 = simulate(batch, fb, mon2, build_controller(spec["controller"], n, T, 100.0))
            meta["checks"].setdefault("alarm_and_action_invariant_to_c_s", {})[label] = bool(
                np.array_equal(sim.alarm, sim2.alarm) and np.array_equal(sim.actions, sim2.actions)
            )
        if spec["family"] == "s2":
            a = sim.actions.astype(bool)
            prev = np.zeros_like(a)
            prev[:, 1:] = a[:, :-1]
            starts = a & ~prev
            store[f"{label}|n_trig"] = starts.sum(1)
            store[f"{label}|n_bad_trig"] = (starts & bad).sum(1)
            store[f"{label}|sum_base"] = (starts * base_S).sum(1)
            store[f"{label}|sum_slope"] = (starts * slope_S).sum(1)
            store[f"{label}|sum_badc_slope"] = (starts * (bad - pib) * slope_S).sum(1)
    for r, cs in REFS.items():
        ctrl = build_controller(cs, n, T, cost.c_s)
        rec = score(simulate(batch, fb, None, ctrl), batch, truth, cost)
        put(store, r, rec)
    meta["runtime_s"] = time.time() - t0
    cells = Path(outdir) / "cells"
    cells.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cells / f"{spec['id']}.npz", **store)
    (cells / f"{spec['id']}.json").write_text(
        json.dumps(meta, default=lambda o: o.item() if hasattr(o, "item") else str(o), indent=1)
    )
    return spec["id"], meta["runtime_s"]


def simulate_cells(specs, outdir, procs):
    t_cal = prefill(specs, procs)
    t0 = time.time()
    with Pool(procs) as pool:
        for i, (cid, rt) in enumerate(
            pool.imap_unordered(run_cell, [(s, str(outdir)) for s in specs]), 1
        ):
            print(f"  cell {i}/{len(specs)} {cid} {rt:.0f}s", flush=True)
    return t_cal, time.time() - t0


# ----------------------------------------------------------------------------- stats helpers
def boot_means(X, B=BOOT, seed=0, chunk=200):
    n, K = X.shape
    rng = np.random.default_rng(seed)
    out = np.empty((B, K))
    for lo in range(0, B, chunk):
        hi = min(B, lo + chunk)
        out[lo:hi] = X[rng.integers(0, n, size=(hi - lo, n))].mean(axis=1)
    return out


def ci_mean(x, B=BOOT, seed=0):
    x = np.asarray(x, float)
    b = boot_means(x[:, None], B, seed)[:, 0]
    lo, hi = np.quantile(b, [0.025, 0.975])
    return float(x.mean()), float(lo), float(hi)


def fmt(m, lo=None, hi=None, nd=2):
    if lo is None:
        return f"{m:.{nd}f}"
    return f"{m:.{nd}f} [{lo:.{nd}f}, {hi:.{nd}f}]"


def md(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def load_cells(d):
    cells = {}
    for p in sorted((Path(d) / "cells").glob("*.json")):
        z = np.load(p.with_suffix(".npz"))
        cells[p.stem] = {"meta": json.loads(p.read_text()), "z": {k: z[k] for k in z.files}}
    return cells


def get(cell, label, key):
    return cell["z"][f"{label}|{key}"]


def kt(x, y):
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        return float("nan")
    return float(kendalltau(x, y).statistic)


def never_cost(cell):
    return cell["z"]["__orc|never_exp"]


def value(cell, label):  # per-episode expected-cost value vs never-switch (positive good)
    return never_cost(cell) - get(cell, label, "cost_exp")


def h6(cell, labels, seed=0):
    """Best monitor vs best simple reference. Selection on episodes [0, n/2), evaluation on the rest."""
    nv = never_cost(cell)
    n = len(nv)
    sel, tst = np.arange(n) < n // 2, np.arange(n) >= n // 2
    mme = 0.01 * nv.mean()
    cm = {m: get(cell, m, "cost_exp") for m in labels}
    cr = {r: get(cell, r, "cost_exp") for r in REFS}
    bm = min(cm, key=lambda m: cm[m][sel].mean())
    br = min(cr, key=lambda r: cr[r][sel].mean())
    d = cr[br][tst] - cm[bm][tst]
    m, lo, hi = ci_mean(d, seed=seed)
    bm2 = min(cm, key=lambda m: cm[m].mean())
    br2 = min(cr, key=lambda r: cr[r].mean())
    d2 = cr[br2] - cm[bm2]
    m2, lo2, hi2 = ci_mean(d2, seed=seed + 1)
    cls = "monitor" if (m >= mme and lo > 0) else ("reference" if (m <= -mme and hi < 0) else "tie")
    return {
        "best_monitor": bm,
        "best_ref": br,
        "gap_heldout": m,
        "lo": lo,
        "hi": hi,
        "mme": mme,
        "winner": cls,
        "best_monitor_insample": bm2,
        "best_ref_insample": br2,
        "gap_insample": m2,
        "lo_in": lo2,
        "hi_in": hi2,
        "never_cost": float(nv.mean()),
    }


def count_reversals(cell, labels, mme, B=BOOT):
    """Ordered pairs (A over B). Necessary point conditions are screened first (the CI requirements can only
    remove further pairs), then the protocol classifier runs with B bootstrap resamples."""
    out = {"power_T": 0, "power_opp": 0, "delay": 0, "n_pairs": 0, "examples": []}
    cost = {m: get(cell, m, "cost_exp") for m in labels}
    dl = {m: get(cell, m, "delay_cens") for m in labels}
    pw = {k: {m: get(cell, m, k).astype(float) for m in labels} for k in ("power_T", "power_opp")}
    for a, b in itertools.permutations(labels, 2):
        out["n_pairs"] += 1
        if cost[a].mean() - cost[b].mean() < mme:
            continue
        cand = (
            pw["power_T"][a].mean() - pw["power_T"][b].mean() >= 0.05
            or pw["power_opp"][a].mean() - pw["power_opp"][b].mean() >= 0.05
            or (dl[b].mean() > 0 and (dl[a].mean() - dl[b].mean()) / dl[b].mean() <= -0.10)
        )
        if not cand:
            continue
        for k in ("power_T", "power_opp"):
            r = classify_reversal(
                pw[k][a], pw[k][b], dl[a], dl[b], cost[a], cost[b], mme, B=B, seed=0
            )
            if r["reversal"] and "power" in r["detection_via"]:
                out[k] += 1
                if len(out["examples"]) < 6:
                    out["examples"].append(
                        (k, a, b, r["power_diff"]["mean"], r["cost_diff"]["mean"])
                    )
            if k == "power_T" and r["reversal"] and "delay" in r["detection_via"]:
                out["delay"] += 1
    return out


# ----------------------------------------------------------------------------- spec builders
def base_spec(cid, family, params, q, d, c_s, target, controller, seed, n, monitors=None, **kw):
    return {
        "id": cid,
        "family": family,
        "params": params,
        "q": q,
        "d": d,
        "c_s": c_s,
        "target": target,
        "controller": controller,
        "seed": seed,
        "n": n,
        "monitors": list(monitors or MONS),
        **kw,
    }


def specs_th1(n):
    p = {"challenger": "strong", "tau_lo": 1000, "tau_hi": 1000}
    grid = [0, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]  # protocol grid {0..100} + extension
    return [
        base_spec(
            f"th1_set{i}",
            "s3",
            p,
            0.2,
            50,
            0.0,
            "paired",
            "permanent",
            seed,
            n,
            cs_grid=grid,
            permanent_identity=True,
        )
        for i, seed in ((1, 1000), (2, 2000))
    ]


def specs_th2(n):
    return [
        base_spec(
            f"th2_{tg}_{ch}",
            "s3",
            {"challenger": ch},
            0.2,
            50,
            5.0,
            tg,
            "permanent",
            3000,
            n,
            permanent_identity=True,
        )
        for tg in ("incumbent", "paired")
        for ch in ("strong", "weak", "none", "common_shock", "reversing")
    ]


def specs_th3(n):
    out = []
    for rho, d, fb, H in itertools.product(
        (0.98, 0.995, 0.999), (0, 50, 200), ("useful", "useless"), (50, 200)
    ):
        out.append(
            base_spec(
                f"th3_rho{rho}_d{d}_{fb}_H{H}",
                "s2",
                {"rho": rho, "challenger_bad": fb},
                0.2,
                d,
                2.0,
                "paired",
                f"hold:{H}",
                4000,
                n,
            )
        )
    return out


def specs_th4(n):
    out = []
    for L, d, q in itertools.product((100, 400, 1600), (0, 50, 200), (0.1, 0.5)):
        out.append(
            base_spec(
                f"th4_L{L}_d{d}_q{q}",
                "s1",
                {"L": L},
                q,
                d,
                5.0,
                "paired",
                f"hold:{round(L / 2)}",
                6000,
                n,
            )
        )
    return out


# ----------------------------------------------------------------------------- TH-1 analysis
def an_th1(out, B):
    cells = load_cells(out)
    c1, c2 = cells["th1_set1"], cells["th1_set2"]
    spec = c1["meta"]["spec"]
    grid = spec["cs_grid"]
    L = MONS
    res = {"identity": {}, "invariance": {}, "pairs": []}

    def prep(cell):
        nv = never_cost(cell)
        dt = cell["z"]["__delta_t"]
        cols = []
        for m in L:
            cols += [
                get(cell, m, "W_at_S"),
                get(cell, m, "any_alarm").astype(float),
                nv - get(cell, m, "cost@0"),
                nv - get(cell, m, "cost@100"),
            ]
        idmax = 0.0
        cdfmax = 0.0
        for m in L:
            W, sw = get(cell, m, "W_at_S"), get(cell, m, "any_alarm").astype(float)
            fa = get(cell, m, "first_alarm")
            F = np.array([np.mean(np.isfinite(fa) & (fa <= t)) for t in range(len(dt))])
            for c in grid:
                vsim = (nv - get(cell, m, f"cost@{c}")).mean()
                idmax = max(idmax, abs(vsim - (W - c * sw).mean()))
                cdfmax = max(cdfmax, abs(vsim - ((dt * F).sum() - c * F[-1])))
        return np.column_stack(cols), idmax, cdfmax

    X1, id1, cdf1 = prep(c1)
    X2, id2, cdf2 = prep(c2)
    res["identity"] = {
        "max_abs_mean_V_sim_minus_per_episode_formula": [id1, id2],
        "max_abs_mean_V_sim_minus_CDF_formula": [cdf1, cdf2],
    }
    res["invariance"] = {
        s: c["meta"]["checks"]["alarm_and_action_invariant_to_c_s"]
        for s, c in (("set1", c1), ("set2", c2))
    }
    res["delta_t_constant"] = c1["meta"]["checks"]["delta_t_constant_across_episodes"]
    b1, b2 = boot_means(X1, B, 11), boot_means(X2, B, 12)
    m1, m2 = X1.mean(0), X2.mean(0)
    k = len(L)
    iW, isw, iV0, iV100 = ([4 * i + j for i in range(k)] for j in range(4))

    def pred(M, ia, ib):  # works for (K,) means or (B,K)
        return (M[..., iW[ia]] - M[..., iW[ib]]), (M[..., isw[ia]] - M[..., isw[ib]])

    def emp(M, ia, ib):
        dv0 = M[..., iV0[ia]] - M[..., iV0[ib]]
        dv100 = M[..., iV100[ia]] - M[..., iV100[ib]]
        return dv0, (dv0 - dv100) / 100.0

    def interp(
        dv0, g
    ):  # crossing of dV(c)=dv0-c*g over the grid: interpolation if bracketed else linear extrapolation
        y = np.array([dv0 - c * g for c in grid])
        for i in range(len(grid) - 1):
            if y[i] * y[i + 1] < 0:
                return grid[i] + (grid[i + 1] - grid[i]) * y[i] / (y[i] - y[i + 1]), True
        return (dv0 / g if g != 0 else np.nan), False

    for ia, ib in itertools.combinations(range(k), 2):
        D0, g = pred(m1, ia, ib)
        if g == 0 or abs(g) < 1e-12:
            res["pairs"].append(
                {"A": L[ia], "B": L[ib], "g": 0.0, "note": "equal power: no crossing"}
            )
            continue
        if g < 0:
            ia, ib = ib, ia
        D0, g = pred(m1, ia, ib)
        cp1 = D0 / g
        D02, g2 = pred(m2, ia, ib)
        ce_dv0, ce_g = emp(m2, ia, ib)
        ce2, in_grid2 = interp(ce_dv0, ce_g)
        ce1_dv0, ce1_g = emp(m1, ia, ib)
        ce1, in_grid1 = interp(ce1_dv0, ce1_g)
        # bootstrap
        D0b, gb = pred(b1, ia, ib)
        with np.errstate(all="ignore"):
            cp1b = D0b / gb
            e2_dv0b, e2_gb = emp(b2, ia, ib)
            ce2b = e2_dv0b / e2_gb
        q = lambda x: [
            float(v) for v in np.nanquantile(np.where(np.isfinite(x), x, np.nan), [0.025, 0.975])
        ]
        diff = ce2b - cp1b
        res["pairs"].append(
            {
                "A": L[ia],
                "B": L[ib],
                "g_T1": float(g),
                "g_ci": q(gb),
                "D0": float(D0),
                "c_pred_set1": float(cp1),
                "c_pred_ci": q(cp1b),
                "c_emp_set1_interp": float(ce1),
                "c_emp_set1_in_grid": bool(in_grid1),
                "c_pred_set2": float(D02 / g2) if g2 != 0 else float("nan"),
                "c_emp_set2": float(ce2),
                "c_emp_set2_ci": q(ce2b),
                "c_emp_set2_in_grid": bool(in_grid2),
                "emp2_minus_pred1_ci": q(diff),
                "agree_oos": bool(q(diff)[0] <= 0 <= q(diff)[1]),
                "same_set_gap": float(abs(cp1 - ce1)),
            }
        )
    prs = [p for p in res["pairs"] if "c_pred_set1" in p]
    ing = [p for p in prs if 0 < p["c_pred_set1"] <= 1000]
    ing100 = [p for p in ing if p["c_pred_set1"] <= 100]
    res["summary"] = {
        "n_pairs": len(prs),
        "n_equal_power": len(res["pairs"]) - len(prs),
        "n_cross_in_0_100": len(ing100),
        "n_cross_in_0_1000": len(ing),
        "oos_agree_in_0_100": sum(p["agree_oos"] for p in ing100),
        "oos_agree_in_0_1000": sum(p["agree_oos"] for p in ing),
        "n_cross_gt1000": sum(p["c_pred_set1"] > 1000 for p in prs),
        "n_no_cross_neg": sum(p["c_pred_set1"] <= 0 for p in prs),
        "oos_agree_all_cross_pos": sum(p["agree_oos"] for p in prs if p["c_pred_set1"] > 0),
        "n_cross_pos": sum(p["c_pred_set1"] > 0 for p in prs),
        "max_same_set_gap_in_grid": max([p["same_set_gap"] for p in ing], default=None),
    }
    h = {cid: h6(c, MONS) for cid, c in cells.items()}
    res["h6"] = h
    # power table
    pt = []
    for m in L:
        for tag, c in (("set1", c1), ("set2", c2)):
            pass
        pt.append(
            [
                m,
                fmt(get(c1, m, "any_alarm").mean(), nd=3),
                fmt(get(c2, m, "any_alarm").mean(), nd=3),
                fmt(get(c1, m, "delay_cens").mean(), nd=1),
                fmt(get(c1, m, "false_alarm_pre_tau").mean(), nd=3),
                c1["meta"]["thresholds"][m]["null_rate_fresh"],
            ]
        )
    tab = [
        "### TH-1 alarm laws (set 1, tau=1000, d=50, q=0.2)",
        md(
            [
                "monitor",
                "F(T-1) set1",
                "F(T-1) set2",
                "mean delay (cens.)",
                "P(alarm<tau)",
                "fresh-seed null rate",
            ],
            pt,
        ),
        "",
    ]
    rows = []
    for p in sorted(ing, key=lambda p: p["c_pred_set1"]):
        rows.append(
            [
                f"{p['A']} vs {p['B']}",
                fmt(p["g_T1"], nd=3),
                fmt(p["D0"], nd=2),
                fmt(p["c_pred_set1"], *p["c_pred_ci"], nd=1),
                fmt(p["c_emp_set1_interp"], nd=1),
                fmt(p["c_emp_set2"], *p["c_emp_set2_ci"], nd=1),
                "yes" if p["agree_oos"] else "NO",
            ]
        )
    tab += [
        "### TH-1 crossing points (0 < c_s* <= 1000); A = more powerful",
        md(
            [
                "pair (A vs B)",
                "g(T-1)",
                "D_0",
                "predicted c_s* (set1, CDF)",
                "empirical set1",
                "empirical set2 (OOS)",
                "OOS CI agrees",
            ],
            rows,
        ),
        "",
    ]
    tab += [
        "```",
        json.dumps(res["summary"], indent=1),
        json.dumps(res["identity"]),
        json.dumps(res["invariance"]),
        "```",
    ]
    return res, "\n".join(tab)


# ----------------------------------------------------------------------------- TH-2 analysis
def an_th2(out, B):
    cells = load_cells(out)
    res = {"cells": {}, "invariance": {}, "identity": {}}
    tab = []
    chal = ("strong", "weak", "none", "common_shock", "reversing")
    for tg in ("incumbent", "paired"):
        for ch in chal:
            c = cells[f"th2_{tg}_{ch}"]
            nv = never_cost(c)
            mme = 0.01 * nv.mean()
            pw = np.array([get(c, m, "power_T").mean() for m in MONS])
            V = np.array([value(c, m).mean() for m in MONS])
            dly = np.array([get(c, m, "delay_cens").mean() for m in MONS])
            X = np.column_stack(
                [get(c, m, "power_T").astype(float) for m in MONS]
                + [value(c, m) for m in MONS]
                + [get(c, m, "delay_cens") for m in MONS]
            )
            bm = boot_means(X, B, 21)
            k = len(MONS)
            tau_pow = np.array([kt(bm[i, :k], bm[i, k : 2 * k]) for i in range(0, B, 5)])
            tau_dly = np.array([kt(-bm[i, 2 * k :], bm[i, k : 2 * k]) for i in range(0, B, 5)])
            qq = lambda x: [float(v) for v in np.nanquantile(x, [0.025, 0.975])]
            # identity V_i = W_at_S - c_s * any_alarm
            idm = max(
                float(
                    np.abs(value(c, m) - (get(c, m, "W_at_S") - 5.0 * get(c, m, "any_alarm"))).max()
                )
                for m in MONS
            )
            anyf = np.array([get(c, m, "any_alarm").mean() for m in MONS])
            vb = V + 5.0 * anyf  # <= 0 if the fallback is never better (P3a)
            rev = count_reversals(c, MONS, mme, B)
            rows = []
            for i, m in enumerate(MONS):
                v = value(c, m)
                mv, lo, hi = ci_mean(v, B, 31)
                rows.append(
                    [
                        m,
                        fmt(pw[i], nd=3),
                        fmt(dly[i], nd=0),
                        fmt(get(c, m, "cost_exp").mean(), nd=1),
                        fmt(mv, lo, hi, nd=2),
                    ]
                )
            res["cells"][c["meta"]["spec"]["id"]] = {
                "tau_power_vs_V": float(kt(pw, V)),
                "tau_power_vs_V_ci": qq(tau_pow),
                "tau_negdelay_vs_V": float(kt(-dly, V)),
                "tau_negdelay_vs_V_ci": qq(tau_dly),
                "never_cost": float(nv.mean()),
                "V": V.tolist(),
                "power": pw.tolist(),
                "identity_maxabs": idm,
                "reversals": rev,
                "p3a_max_of_V_plus_cs_F": float(vb.max()),
                "best_monitor_V": float(V.max()),
                "h6": h6(c, MONS),
            }
            tab += [
                f"#### target={tg}, challenger={ch} (never-switch cost {nv.mean():.1f}; MME {mme:.2f})",
                md(["monitor", "power_T", "delay (cens.)", "cost", "V vs never [95% CI]"], rows),
                f"Kendall tau(power, V) = {kt(pw, V):.2f} {qq(tau_pow)}; tau(-delay, V) = {kt(-dly, V):.2f} {qq(tau_dly)}; "
                + f"protocol reversals (power_T) = {rev['power_T']}/{rev['n_pairs']} ordered pairs; per-episode identity max|err| = {idm:.2e}",
                "",
            ]
    # P3 invariance
    for m in MONS:
        ref = get(cells["th2_incumbent_strong"], m, "first_alarm")
        same = all(
            np.array_equal(ref, get(cells[f"th2_incumbent_{ch}"], m, "first_alarm"), equal_nan=True)
            for ch in chal
        )
        ref_p = get(cells["th2_paired_strong"], m, "first_alarm")
        difffrac = {
            ch: float(
                np.mean(
                    ~(
                        (ref_p == get(cells[f"th2_paired_{ch}"], m, "first_alarm"))
                        | (
                            np.isnan(ref_p)
                            & np.isnan(get(cells[f"th2_paired_{ch}"], m, "first_alarm"))
                        )
                    )
                )
            )
            for ch in chal
        }
        res["invariance"][m] = {
            "incumbent_alarm_times_identical_across_challengers": bool(same),
            "paired_fraction_episodes_differing_vs_strong": difffrac,
        }
    tab += [
        "#### P3 invariance (first-alarm time per episode, identical seeds)",
        md(
            [
                "monitor",
                "incumbent: identical across 5 challengers",
                "paired: frac. episodes differing vs strong (weak/none/common/rev)",
            ],
            [
                [
                    m,
                    v["incumbent_alarm_times_identical_across_challengers"],
                    " / ".join(
                        f"{v['paired_fraction_episodes_differing_vs_strong'][ch]:.2f}"
                        for ch in chal[1:]
                    ),
                ]
                for m, v in res["invariance"].items()
            ],
        ),
    ]
    return res, "\n".join(tab)


# ----------------------------------------------------------------------------- TH-3 analysis
def an_th3(out, B):
    cells = load_cells(out)
    rows, res = [], {"rows": [], "cells": {}}
    n_tests = n_exceed = n_theta_exceed = 0
    for cid, c in sorted(cells.items()):
        p5 = c["meta"]["p5"]
        nv = never_cost(c)
        cell = {
            "p5": p5,
            "V": {},
            "dynamic_oracle": float((nv - c["z"]["__orc|dynamic_exp"]).mean()),
            "clair": float((nv - c["z"]["__orc|clairvoyant_exp"]).mean()),
            "always": float((nv - get(c, "always", "cost_exp")).mean()),
            "h6": h6(c, MONS),
        }
        for m in MONS:
            v = value(c, m)
            nt, nb = get(c, m, "n_trig").astype(float), get(c, m, "n_bad_trig").astype(float)
            if nt.sum() < 10:
                cell["V"][m] = {
                    "V": float(v.mean()),
                    "n_trig_mean": float(nt.mean()),
                    "skipped": True,
                }
                continue
            th = nb.sum() / nt.sum()
            sb, ss, sbc = get(c, m, "sum_base"), get(c, m, "sum_slope"), get(c, m, "sum_badc_slope")
            pred_ind = sb + sbc
            pred_plug = sb + (th - 0.5) * ss
            ceil = sb + (p5["theta_max"] - 0.5) * ss
            ceil_untr = nt * p5["G_untrunc_at_ceiling"]
            # bootstrap theta-hat (ratio) and excess over ceiling
            X = np.column_stack([nb, nt, v - pred_ind, v - pred_plug, v - ceil, v - ceil_untr, v])
            bm = boot_means(X, 2000, 5)
            th_b = bm[:, 0] / bm[:, 1]
            qq = lambda x: [float(a) for a in np.quantile(x, [0.025, 0.975])]
            e = {
                "V": float(v.mean()),
                "V_ci": qq(bm[:, 6]),
                "n_trig_mean": float(nt.mean()),
                "theta_hat": float(th),
                "theta_ci": qq(th_b),
                "pred_exact": float(pred_ind.mean()),
                "err_exact": float((v - pred_ind).mean()),
                "err_exact_ci": qq(bm[:, 2]),
                "pred_plugin": float(pred_plug.mean()),
                "err_plugin": float((v - pred_plug).mean()),
                "err_plugin_ci": qq(bm[:, 3]),
                "ceiling": float(ceil.mean()),
                "excess_ceiling": float((v - ceil).mean()),
                "excess_ceiling_ci": qq(bm[:, 4]),
                "ceiling_untrunc": float(ceil_untr.mean()),
                "excess_untrunc": float((v - ceil_untr).mean()),
                "excess_untrunc_ci": qq(bm[:, 5]),
            }
            e["exceeds_ceiling"] = bool(e["excess_ceiling_ci"][0] > 0)
            e["theta_exceeds_max"] = bool(e["theta_ci"][0] > p5["theta_max"])
            cell["V"][m] = e
            n_tests += 1
            n_exceed += e["exceeds_ceiling"]
            n_theta_exceed += e["theta_exceeds_max"]
        res["cells"][cid] = cell
        act = {m: v for m, v in cell["V"].items() if not v.get("skipped")}
        bestm = max(cell["V"], key=lambda m: cell["V"][m]["V"])
        rows.append(
            [
                cid.replace("th3_", ""),
                fmt(p5["theta_max"], nd=3),
                fmt(p5["G_untrunc_at_ceiling"], nd=1),
                f"{cell['V'][bestm]['V']:.1f} ({bestm})",
                f"{cell['clair']:.1f}",
                f"{cell['always']:.1f}",
                f"{sum(1 for v in act.values() if v['exceeds_ceiling'])}/{len(act)}",
                f"{np.mean([v['theta_hat'] for v in act.values()]):.3f}" if act else "NA",
            ]
        )
    allv = [
        (cid, m, v)
        for cid, c in res["cells"].items()
        for m, v in c["V"].items()
        if not v.get("skipped")
    ]
    pe = np.array([v["pred_exact"] for _, _, v in allv])
    sv = np.array([v["V"] for _, _, v in allv])
    cover = np.mean([v["err_exact_ci"][0] <= 0 <= v["err_exact_ci"][1] for _, _, v in allv])
    cover_p = np.mean([v["err_plugin_ci"][0] <= 0 <= v["err_plugin_ci"][1] for _, _, v in allv])
    sl = np.polyfit(pe, sv, 1)
    res["summary"] = {
        "n_cell_monitor_tests": n_tests,
        "n_V_exceeds_ceiling": n_exceed,
        "n_theta_hat_ci_above_theta_max": n_theta_exceed,
        "pred_exact_vs_sim_slope_intercept": [float(sl[0]), float(sl[1])],
        "corr": float(np.corrcoef(pe, sv)[0, 1]),
        "frac_err_exact_ci_covers_0": float(cover),
        "frac_err_plugin_ci_covers_0": float(cover_p),
        "mean_abs_err_exact": float(np.mean(np.abs(pe - sv))),
        "max_excess_z_like": max(
            (
                (
                    v["excess_ceiling"]
                    / max((v["excess_ceiling_ci"][1] - v["excess_ceiling_ci"][0]) / 3.92, 1e-9)
                )
                for _, _, v in allv
            )
        ),
    }
    # sign of best monitor value vs theory
    tab = [
        "### TH-3 per-cell summary (best-monitor V vs ceiling; theta_max = pi_b + (1-pi_b) lam^(d+1))",
        md(
            [
                "cell",
                "theta_max",
                "G_H(theta_max) per alarm (untrunc.)",
                "best monitor V (name)",
                "V clairvoyant",
                "V always",
                "monitors with V > ceiling (CI)",
                "mean theta_hat",
            ],
            rows,
        ),
        "",
        "```",
        json.dumps(res["summary"], indent=1),
        "```",
    ]
    return res, "\n".join(tab)


# ----------------------------------------------------------------------------- TH-4 analysis
def kl_trinomial(m0a, m1a, m0b, m1b):
    """KL(P_a || P_b) of x = l0 - l1 in {-1,0,1} with independent Bernoulli(m0), Bernoulli(m1)."""

    def pm(m0, m1):
        return np.array([(1 - m0) * m1, m0 * m1 + (1 - m0) * (1 - m1), m0 * (1 - m1)])

    pa, pb = pm(m0a, m1a), pm(m0b, m1b)
    return float(np.sum(pa * np.log(pa / pb)))


def an_th4(out, B):
    cells = load_cells(out)
    res = {"cells": {}}
    pts = []
    rev_tot = {"power_T": 0, "power_opp": 0, "delay": 0}
    rows_c = []
    for cid, c in sorted(cells.items()):
        sp = c["meta"]["spec"]
        L, d, q = sp["params"]["L"], sp["d"], sp["q"]
        p0, de, Dl = 0.2, 0.05, 0.15
        I = kl_trinomial(p0 + Dl, p0 + de, p0, p0 + de)
        kappa = max(L - d, 0) * q * I / np.log(1 / ALPHA)
        nv = never_cost(c)
        HT = float(c["z"]["__orc|headroom_static_exp"].mean())
        Cs = float(c["z"]["__orc|static_exp"].mean())
        mme = 0.01 * nv.mean()
        mons = {}
        for m in MONS:
            v = value(c, m)
            mv, lo, hi = ci_mean(v, B, 41)
            mons[m] = {
                "V": mv,
                "V_lo": lo,
                "V_hi": hi,
                "captured": (Cs - get(c, m, "cost_exp").mean()) / HT if HT > 0.5 else None,
                "power_T": float(get(c, m, "power_T").mean()),
                "power_opp": float(get(c, m, "power_opp").mean()),
                "delay": float(get(c, m, "delay_cens").mean()),
            }
            pts.append((cid, m, kappa, mons[m]["power_T"], mons[m]["power_opp"], mv, HT))
        rev = count_reversals(c, MONS, mme, B)
        for k in rev_tot:
            rev_tot[k] += rev[k]
        h = h6(c, MONS)
        bm = max(mons, key=lambda m: mons[m]["V"])
        res["cells"][cid] = {
            "L": L,
            "d": d,
            "q": q,
            "kappa": kappa,
            "I": I,
            "H_T": HT,
            "never_cost": float(nv.mean()),
            "mme": mme,
            "monitors": mons,
            "reversals": rev,
            "h6": h,
            "best": bm,
        }
        cap = [v["captured"] for v in mons.values() if v["captured"] is not None]
        rows_c.append(
            [
                cid.replace("th4_", ""),
                f"{kappa:.2f}",
                f"{HT:.1f}",
                f"{mons[bm]['V']:.1f} ({bm})",
                f"{np.median(cap):.2f}" if cap else "NA",
                f"{np.mean([v['power_T'] for v in mons.values()]):.2f}",
                f"{np.mean([v['power_opp'] for v in mons.values()]):.2f}",
                f"{rev['power_T']}/{rev['power_opp']}/{rev['delay']}",
                f"{h['gap_heldout']:.1f} [{h['lo']:.1f},{h['hi']:.1f}] {h['winner']}",
            ]
        )
    arr = np.array([(k, p, po, v, ht) for _, _, k, p, po, v, ht in pts], float)
    kap, pT, pO, V = arr[:, 0], arr[:, 1], arr[:, 2], arr[:, 3]
    stat = {}
    stat["spearman_V_kappa_all_points"] = float(spearmanr(V, kap).statistic)
    stat["spearman_V_powerT_all_points"] = float(spearmanr(V, pT).statistic)
    stat["spearman_V_powerOpp_all_points"] = float(spearmanr(V, pO).statistic)
    # between-cell
    cid_list = sorted(res["cells"])
    mv = np.array([np.mean([res["cells"][c]["monitors"][m]["V"] for m in MONS]) for c in cid_list])
    mbest = np.array([max(res["cells"][c]["monitors"][m]["V"] for m in MONS) for c in cid_list])
    mk = np.array([res["cells"][c]["kappa"] for c in cid_list])
    mp = np.array(
        [np.mean([res["cells"][c]["monitors"][m]["power_T"] for m in MONS]) for c in cid_list]
    )
    mpo = np.array(
        [np.mean([res["cells"][c]["monitors"][m]["power_opp"] for m in MONS]) for c in cid_list]
    )
    mh = np.array([res["cells"][c]["H_T"] for c in cid_list])
    stat["between_cell_spearman_meanV_kappa"] = float(spearmanr(mv, mk).statistic)
    stat["between_cell_spearman_meanV_meanPowerT"] = float(spearmanr(mv, mp).statistic)
    stat["between_cell_spearman_meanV_meanPowerOpp"] = float(spearmanr(mv, mpo).statistic)
    stat["between_cell_spearman_bestV_kappa"] = float(spearmanr(mbest, mk).statistic)
    stat["between_cell_spearman_bestV_headroom"] = float(spearmanr(mbest, mh).statistic)
    stat["between_cell_spearman_bestV_meanPowerT"] = float(spearmanr(mbest, mp).statistic)
    # within-cell rank correlation of V with power_T and power_opp (monitor ranking quality)
    wT, wO = [], []
    for c in cid_list:
        ms = res["cells"][c]["monitors"]
        v = [ms[m]["V"] for m in MONS]
        a, b = (
            spearmanr(v, [ms[m]["power_T"] for m in MONS]).statistic,
            spearmanr(v, [ms[m]["power_opp"] for m in MONS]).statistic,
        )
        if np.isfinite(a):
            wT.append(a)
        if np.isfinite(b):
            wO.append(b)
    stat["within_cell_mean_spearman_V_powerT"] = [float(np.mean(wT)), len(wT)]
    stat["within_cell_mean_spearman_V_powerOpp"] = [float(np.mean(wO)), len(wO)]
    # threshold rules for 1{V>0}
    y = V > 0

    def best_thr(x):
        best = (0, None)
        for t in np.unique(x):
            acc = max(np.mean((x >= t) == y), np.mean((x < t) == y))
            if acc > best[0]:
                best = (acc, float(t))
        return best

    def auc(x):
        from scipy.stats import rankdata

        r = rankdata(x)
        n1, n0 = y.sum(), (~y).sum()
        return float((r[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)) if n1 and n0 else float("nan")

    stat["frac_points_V_positive"] = float(y.mean())
    stat["rule_V_pos_iff_kappa>k"] = {"acc_thr": best_thr(kap), "auc": auc(kap)}
    stat["rule_V_pos_iff_powerT>p"] = {"acc_thr": best_thr(pT), "auc": auc(pT)}
    stat["rule_V_pos_iff_powerOpp>p"] = {"acc_thr": best_thr(pO), "auc": auc(pO)}
    stat["majority_baseline_acc"] = float(max(y.mean(), 1 - y.mean()))
    stat["reversal_counts_total_ordered_pairs"] = {
        **rev_tot,
        "n_ordered_pairs_total": 90 * len(cells),
        "n_cells": len(cells),
    }
    stat["cells_with_any_power_T_reversal"] = int(
        sum(v["reversals"]["power_T"] > 0 for v in res["cells"].values())
    )
    stat["cells_with_any_power_opp_reversal"] = int(
        sum(v["reversals"]["power_opp"] > 0 for v in res["cells"].values())
    )
    stat["h6_winner_counts"] = {
        w: int(sum(v["h6"]["winner"] == w for v in res["cells"].values()))
        for w in ("monitor", "reference", "tie")
    }
    res["stat"] = stat
    tab = [
        "### TH-4 per-cell (kappa = (L-d) q I / log(1/alpha); H_T = static - dynamic expected cost; captured = median over monitors of (C_static - C_P)/H_T)",
        md(
            [
                "cell",
                "kappa",
                "H_T",
                "best monitor V vs never (name)",
                "median captured",
                "mean power_T",
                "mean power_opp",
                "reversals power_T/power_opp/delay (of 90)",
                "H6 gap ref-minus-best-monitor [CI] winner",
            ],
            rows_c,
        ),
        "",
        "```",
        json.dumps(stat, indent=1),
        "```",
    ]
    return res, "\n".join(tab)


ANALYZE = {"th1": an_th1, "th2": an_th2, "th3": an_th3, "th4": an_th4}
SPECS = {"th1": specs_th1, "th2": specs_th2, "th3": specs_th3, "th4": specs_th4}


def h6_table(out):
    cells = load_cells(out)
    rows = []
    for cid, c in sorted(cells.items()):
        h = h6(c, MONS)
        rows.append(
            [
                cid,
                h["best_monitor"],
                h["best_ref"],
                f"{h['never_cost']:.0f}",
                fmt(h["gap_heldout"], h["lo"], h["hi"], nd=2),
                f"{h['mme']:.1f}",
                h["winner"],
                fmt(h["gap_insample"], h["lo_in"], h["hi_in"], nd=2),
            ]
        )
    return md(
        [
            "cell",
            "best monitor (sel. half)",
            "best ref (sel. half)",
            "never cost",
            "gap ref - monitor, held-out half [95% CI]",
            "MME",
            "winner",
            "in-sample gap (optimistic)",
        ],
        rows,
    )


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("cmd", choices=["th1", "th2", "th3", "th4", "analyze"])
    ap.add_argument("--exp", choices=list(ANALYZE))
    ap.add_argument("--dir")
    ap.add_argument("--n", type=int, default=1000)
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--B", type=int, default=BOOT)
    ap.add_argument("--only", default=None, help="substring filter on cell ids (smoke)")
    a = ap.parse_args()
    t0 = time.time()
    if a.cmd == "analyze":
        out, exp = Path(a.dir), a.exp
        t_cal = t_sim = 0.0
    else:
        exp = a.cmd
        specs = SPECS[exp](a.n)
        if a.only:
            specs = [s for s in specs if a.only in s["id"]]
        ts = f"{datetime.now(UTC):%Y%m%dT%H%M%SZ}"
        out = DEV_OUT / f"mech_{exp}_{ts}"
        out.mkdir(parents=True, exist_ok=True)
        t_cal, t_sim = simulate_cells(specs, out, min(a.procs, 4))
    t1 = time.time()
    res, tab = ANALYZE[exp](out, a.B)
    res["h6_table"] = h6_table(out)
    t2 = time.time()
    res["timing_s"] = {"calibration": t_cal, "simulation": t_sim, "analysis": t2 - t1}
    (out / "results.json").write_text(
        json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    )
    (out / "tables.md").write_text(
        tab + "\n\n### H6 (best monitor vs best simple reference)\n" + res["h6_table"] + "\n"
    )
    if a.cmd != "analyze":
        specs_meta = [{k: v for k, v in s.items() if k != "monitors"} for s in specs]
        config = {
            "exp": exp,
            "n": a.n,
            "B": a.B,
            "procs": a.procs,
            "monitors": {m: MON[m] for m in MONS},
            "n_cal": N_CAL,
            "alpha": ALPHA,
            "label": "development, synthetic (Setting C)",
            "cells": specs_meta,
        }
        seeds = {
            "eval": sorted({s["seed"] for s in specs}),
            "calibration": CAL_SEED,
            "calibration_check": CAL_SEED + 1,
        }
        append_run(
            f"mech_{exp}_{out.name.split('_')[-1]}",
            config,
            seeds,
            a.n,
            time.time() - t0,
            [out / "results.json", out / "tables.md", out / "cells"],
        )
    print(f"exp={exp} out={out} sim={t_sim:.0f}s cal={t_cal:.0f}s analysis={t2 - t1:.0f}s")


if __name__ == "__main__":
    main()
