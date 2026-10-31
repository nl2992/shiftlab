"""FROZEN confirmation script for the monitoring-to-decision-value programme (protocol 12, v1).

Subcommands
  step0         development only: re-tune the simple family (extended margins) on dev tuning seeds and
                write docs/decision_value/manifests/confirmation_selected_configs.json
  synthetic     Part S (confirmation seeds 7_000_000 + 10_000*cell_index, n = 2000), one shot
  real          Part R (reserved windows, one shot)
  write-hashes  write docs/decision_value/manifests/confirmation_hashes.json (after the script is final)
Add --dry-run to `synthetic` / `real` for a development-seed / development-window smoke test (no hash
check, outputs under outputs/decision_value/development/, never touches seeds >= 7_000_000 or reserved
windows).

On start, `synthetic` and `real` (non-dry) verify the sha256 of the protocol, the dev real-data results,
the selected-config JSON and this script (plus the engine sources they import) against the hash manifest
and refuse to run on any difference; they also refuse a second run of the same part once results exist.

Pre-declared interpretations of protocol Part R (fixed here, before the reserved windows are opened):
  * pass rule: primary endpoint point estimate > MME AND the percentile CI lower bound > 0 for BOTH block
    lengths (7 d and 28 d; Binance 168 h / 672 h); controls: the maximum V-vs-never over the 5 monitors x 4
    controllers (paired target, c_s = 5, d = 1, q = 1) must be <= 1% of the control's never-switch cost.
  * bootstrap = moving-block resampling of the reserved-window joint paired losses (10,000 series), monitor
    system replayed on each resample with the actual-series calibrated threshold; CI = percentiles of the
    endpoint over resamples (understates persistence; the endpoint point estimate is the actual series).
  * the 4 pre-declared secondary comparisons for Holm are the 4 non-primary pairs; endpoint = best of
    {never, always, calendar28} cost minus CUSUM+Hold(7) cost (c_s=5, d=1, q=1), block-7 bootstrap.
  * Binance: the frozen model is the phase-1 model (fit 2025-01..06, refit-free); sliding refit schedule as
    phase 1, anchored at the first bar of the reserved window.
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import hashlib
import importlib.util
import io
import json
import sys
import time
import zipfile
from datetime import UTC, datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_value import controllers as C
from shiftlab.decision_value import data_adapters as DA
from shiftlab.decision_value.contracts import CostContract, EpisodeBatch, FeedbackContract
from shiftlab.decision_value.evaluation import score, simulate
from shiftlab.decision_value.monitors import monitor_factory
from shiftlab.decision_value.oracles import oracle_costs
from shiftlab.decision_value.registry import append_run
from shiftlab.decision_value.statistics import classify_reversal, holm
from shiftlab.decision_value.synthetic import Family

DOCS = ROOT / "docs" / "decision_value"
MAN = DOCS / "manifests"
PROTO = DOCS / "12_CONFIRMATION_PROTOCOL.md"
DEVREAL = DOCS / "10_REAL_DATA_DEV_RESULTS.md"
SEL = MAN / "confirmation_selected_configs.json"
HASHES = MAN / "confirmation_hashes.json"
SELF = Path(__file__).resolve()
DEV_OUT = ROOT / "outputs" / "decision_value" / "development"
CONF_OUT = ROOT / "outputs" / "decision_value" / "confirmation"
ASYM_RUN = DEV_OUT / "type2_asym_20261031T021545Z"
DEV_REPLAY = ROOT / "outputs" / "decision_value" / "real_data" / "dev" / "replay_20261030T231500Z"
DEFAULT_DATA = ROOT.parent / "shift-research-starter" / "data"

HASHED = [  # relative to ROOT; first four are the files named in the protocol
    "docs/decision_value/12_CONFIRMATION_PROTOCOL.md",
    "docs/decision_value/10_REAL_DATA_DEV_RESULTS.md",
    "docs/decision_value/manifests/confirmation_selected_configs.json",
    "scripts/decision_value/run_confirmation.py",
    "scripts/decision_value/run_real_data.py",
    "scripts/decision_value/run_type2_tuning.py",
    "scripts/decision_value/audit_real_data.py",
    *[
        f"src/shiftlab/decision_value/{n}.py"
        for n in (
            "__init__",
            "calibration",
            "contracts",
            "controllers",
            "data_adapters",
            "evaluation",
            "feedback",
            "monitors",
            "oracles",
            "registry",
            "statistics",
            "synthetic",
        )
    ],
]
CONF_SEED_BASE, CONF_SEED_STEP, N_CONF = 7_000_000, 10_000, 2000
DRY_SEED_BASE = 600_000
BOOT = 10_000
MARGINS8 = (0.0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3)

_MODS = {}


def sha256(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load(name: str, rel: str):
    if name not in _MODS:
        spec = importlib.util.spec_from_file_location(name, ROOT / rel)
        m = importlib.util.module_from_spec(spec)
        sys.modules[name] = m
        spec.loader.exec_module(m)
        _MODS[name] = m
    return _MODS[name]


def RTS():
    return _load("run_type2_tuning", "scripts/decision_value/run_type2_tuning.py")


def RR():
    return _load("run_real_data", "scripts/decision_value/run_real_data.py")


def verify_hashes():
    if not HASHES.exists():
        raise SystemExit(f"refusing to run: hash manifest {HASHES} missing")
    man = json.loads(HASHES.read_text())["files"]
    bad = [r for r in HASHED if man.get(r) != sha256(ROOT / r)]
    if bad:
        raise SystemExit(f"refusing to run: sha256 mismatch for {bad}")
    return man


def guard_oneshot(part: str):
    done = list(CONF_OUT.glob(f"*/DONE_{part}"))
    if done:
        raise SystemExit(f"refusing to run: confirmation part {part} already executed ({done[0]})")


def md(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


# ======================================================================== step 0 (development only)
def step0_cfg():
    rts = RTS()
    return dict(
        rts.EXT,
        margins=MARGINS8,
        stat_m=MARGINS8,
        tune_base=300_000,
        eval_base=400_000,
        cal_tag="x",
    )


def _step0_cell(spec):
    rts = RTS()
    cfg = step0_cfg()
    fam = Family(spec["family"], spec["params"])
    T, c_s = fam.T, spec["c_s"]
    fb = FeedbackContract(spec["q"], spec["d"])
    batch, truth = fam.generate(300_000 + spec["idx"], 500, fb)
    costs = {}
    for sc in rts.simple_configs(cfg):
        costs[sc] = rts.lean(
            simulate(batch, fb, None, rts.build_simple(sc, 500, T, c_s)), truth, c_s
        )
    return spec["id"], costs


def step0(procs: int):
    rts = RTS()
    specs = rts.cell_specs("asym")
    t0 = time.time()
    with Pool(procs) as pool:
        res = dict(pool.map(_step0_cell, specs))
    out = {
        "protocol": "docs/decision_value/12_CONFIRMATION_PROTOCOL.md (Step 0)",
        "created_utc": datetime.now(UTC).isoformat(),
        "monitor_selection_source": str(ASYM_RUN.relative_to(ROOT)),
        "tuning": {
            "seed_base": 300_000,
            "n_tune": 500,
            "selection": "min mean cost_exp on tuning seeds",
        },
        "simple_grid": {
            "never_always": True,
            "calendar_K": list(rts.EXT["cal_k"]),
            "calendar_margins": list(MARGINS8),
            "static_W": list(rts.EXT["stat_w"]),
            "static_margins": list(MARGINS8),
            "n_configs": len(rts.simple_configs(step0_cfg())),
        },
        "confirmation": {
            "seed_rule": "7_000_000 + 10_000 * cell_index",
            "n": N_CONF,
            "calibration_seed": rts.CAL_SEED,
            "n_cal": rts.N_CAL,
        },
        "cells": [],
    }
    for spec in specs:
        dev = json.loads((ASYM_RUN / "cells" / f"{spec['id']}.json").read_text())
        assert dev["spec"]["id"] == spec["id"] and dev["tune_seed"] == 300_000 + spec["idx"]
        costs = res[spec["id"]]
        assert abs(costs["never"] - dev["never_tune"]) < 1e-9, "step0 reproduces dev never cost"
        best = min(costs, key=costs.get)
        m, ctrl, a = dev["best_monitor"].split("|")
        old = dev["best_simple"].split("|", 1)[1]
        assert abs(costs[old] - dev["tune_cost"][dev["best_simple"]]) < 1e-9, (old, costs[old])
        p = best.split(":")
        simple = {"spec": best, "type": p[0]}
        if p[0] == "calm":
            simple.update(K=int(p[1]), margin=float(p[2]))
        elif p[0] == "statm":
            simple.update(W=int(p[1]), margin=float(p[2]))
        out["cells"].append(
            {
                "cell_index": spec["idx"],
                "cell_id": spec["id"],
                "control": bool(spec.get("control", False)),
                "spec": spec,
                "confirmation_seed": CONF_SEED_BASE + CONF_SEED_STEP * spec["idx"],
                "monitor": {
                    "spec": dev["best_monitor"],
                    "monitor": m,
                    "controller": ctrl,
                    "alpha": float(a),
                    "threshold": dev["thresholds"][m][a],
                    "dev_tune_cost": dev["tune_cost"][dev["best_monitor"]],
                },
                "simple": dict(
                    simple,
                    dev_tune_cost=costs[best],
                    previous_dev_selection=old,
                    previous_dev_tune_cost=costs[old],
                ),
                "dev_tune_cost_never": costs["never"],
                "simple_dev_tune_costs_all": costs,
            }
        )
    SEL.write_text(json.dumps(out, indent=1))
    print(f"wrote {SEL} in {time.time() - t0:.0f}s")
    for c in out["cells"]:
        print(
            c["cell_id"],
            c["monitor"]["spec"],
            f"{c['monitor']['dev_tune_cost']:.2f}",
            c["simple"]["spec"],
            f"{c['simple']['dev_tune_cost']:.2f}",
            "(was",
            c["simple"]["previous_dev_selection"],
            f"{c['simple']['previous_dev_tune_cost']:.2f})",
        )


# ======================================================================== Part S
def _s_cell(arg):
    rec, seed, n = arg
    rts = RTS()
    spec = rec["spec"]
    fam = Family(spec["family"], spec["params"])
    T, c_s = fam.T, spec["c_s"]
    fb, cost = FeedbackContract(spec["q"], spec["d"]), CostContract(0.0, c_s)
    t0 = time.time()
    batch, truth = fam.generate(seed, n, fb)
    orc = oracle_costs(batch, truth, cost)
    m, ctrl, a = (
        rec["monitor"]["monitor"],
        rec["monitor"]["controller"],
        str(rec["monitor"]["alpha"]),
    )
    thr = rts.thresholds(m, spec["q"], spec["d"], "asym")[a]
    assert abs(thr - rec["monitor"]["threshold"]) < 1e-9, (
        "recalibrated threshold differs from frozen"
    )
    fac = monitor_factory(m, target="paired")
    mon = fac(n)
    mon.threshold = thr
    rm = score(
        simulate(batch, fb, mon, rts.build_system(ctrl, n, T, c_s, fac, thr)), batch, truth, cost
    )
    store = {f"orc_{k}": orc[k] for k in ("never_exp", "always_exp", "static_exp", "dynamic_exp")}
    store["mon_cost"], store["mon_Ns"] = rm["cost_exp"], rm["N_s"]
    for tag, sc in (("simple", rec["simple"]["spec"]), ("never", "never"), ("always", "always")):
        r = score(simulate(batch, fb, None, rts.build_simple(sc, n, T, c_s)), batch, truth, cost)
        store[f"{tag}_cost"], store[f"{tag}_Ns"] = r["cost_exp"], r["N_s"]
    return rec["cell_id"], store, time.time() - t0


def _boot_means(arrs, B, seed, chunk=1000):
    n = len(arrs[0])
    rng = np.random.default_rng(seed)
    out = [np.empty(B) for _ in arrs]
    for lo in range(0, B, chunk):
        hi = min(B, lo + chunk)
        idx = rng.integers(0, n, size=(hi - lo, n))
        for o, a in zip(out, arrs):
            o[lo:hi] = a[idx].mean(axis=1)
    return out


def _two_sided(point, boot):
    lo, hi = np.quantile(boot, [0.025, 0.975])
    p = min(1.0, 2 * min((boot <= 0).mean(), (boot >= 0).mean()) + 1.0 / (len(boot) + 1))
    return {"mean": float(point), "lo": float(lo), "hi": float(hi), "p": float(p)}


def _one_sided_gt0(point, boot):
    return {
        "mean": float(point),
        "lb95_onesided": float(np.quantile(boot, 0.05)),
        "p_onesided": float((np.sum(boot <= 0) + 1) / (len(boot) + 1)),
    }


def synthetic(dry: bool, procs: int):
    if not dry:
        verify_hashes()
        guard_oneshot("synthetic")
    sel = json.loads(SEL.read_text())
    cells = sel["cells"]
    n = 200 if dry else N_CONF
    B = 1000 if dry else BOOT
    base = DRY_SEED_BASE if dry else CONF_SEED_BASE
    seeds = {c["cell_id"]: base + CONF_SEED_STEP * c["cell_index"] for c in cells}
    if not dry:
        assert all(
            s == CONF_SEED_BASE + CONF_SEED_STEP * c["cell_index"]
            for c, s in zip(cells, seeds.values())
        )
    else:
        assert max(seeds.values()) < 7_000_000
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{'dryrun_' if dry else ''}confirm_synthetic_{ts}"
    out = (DEV_OUT if dry else CONF_OUT) / run_id
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    store = {}
    with Pool(procs) as pool:
        for i, (cid, st, rt) in enumerate(
            pool.imap_unordered(_s_cell, [(c, seeds[c["cell_id"]], n) for c in cells]), 1
        ):
            store[cid] = st
            print(f"  cell {i}/{len(cells)} done ({rt:.0f}s)", flush=True)
    np.savez_compressed(
        out / "episodes.npz", **{f"{k}|{kk}": v for k, s in store.items() for kk, v in s.items()}
    )
    # ---- bootstrap: per-cell independent seed blocks
    by_id = {c["cell_id"]: c for c in cells}
    boots, info = {}, {}
    for c in cells:
        st = store[c["cell_id"]]
        diff = st["simple_cost"] - st["mon_cost"]
        val = st["never_cost"] - st["mon_cost"]
        bd, bv = _boot_means([diff, val], B, 20_261_031 + c["cell_index"])
        boots[c["cell_id"]] = (bd, bv)
        nv = st["never_cost"].mean()
        dyn = st["orc_dynamic_exp"].mean()
        head = nv - dyn
        info[c["cell_id"]] = {
            "diff": float(diff.mean()),
            "value_mon_vs_never": float(val.mean()),
            "mme": float(0.01 * nv),
            "never": float(nv),
            "always": float(st["always_cost"].mean()),
            "dynamic": float(dyn),
            "headroom": float(head),
            "cost_monitor": float(st["mon_cost"].mean()),
            "cost_simple": float(st["simple_cost"].mean()),
            "cap_mon": float((nv - st["mon_cost"].mean()) / head) if head > 1e-9 else None,
            "cap_simple": float((nv - st["simple_cost"].mean()) / head) if head > 1e-9 else None,
            "Ns_mon": float(st["mon_Ns"].mean()),
            "Ns_simple": float(st["simple_Ns"].mean()),
            "alpha": by_id[c["cell_id"]]["monitor"]["alpha"],
            "monitor": by_id[c["cell_id"]]["monitor"]["spec"],
            "simple": by_id[c["cell_id"]]["simple"]["spec"],
            "diff_ci": _two_sided(diff.mean(), bd),
        }
    useful = [c for c in cells if not c["control"]]
    idx_of = {(c["spec"]["B"], c["spec"]["pi_b"], c["spec"]["d"]): c["cell_id"] for c in useful}
    # CF-S1
    s1_ids = [idx_of[(Bm, pi, 0)] for Bm in (400, 1000) for pi in (0.1, 0.25)]
    s1_boot = np.mean([boots[i][0] for i in s1_ids], axis=0)
    s1_pt = float(np.mean([info[i]["diff"] for i in s1_ids]))
    s1_mme = float(np.mean([info[i]["mme"] for i in s1_ids]))
    s1 = _one_sided_gt0(s1_pt, s1_boot)
    s1.update(cells=s1_ids, mean_mme=s1_mme)
    # CF-S2
    pairs = [(Bm, pi) for Bm in (100, 400, 1000) for pi in (0.1, 0.25)]
    s2_boot = np.mean(
        [boots[idx_of[(Bm, pi, 0)]][0] - boots[idx_of[(Bm, pi, 50)]][0] for Bm, pi in pairs], axis=0
    )
    s2_pt = float(
        np.mean(
            [
                info[idx_of[(Bm, pi, 0)]]["diff"] - info[idx_of[(Bm, pi, 50)]]["diff"]
                for Bm, pi in pairs
            ]
        )
    )
    s2 = _one_sided_gt0(s2_pt, s2_boot)
    s2["pairs"] = [list(p) for p in pairs]
    s2["per_pair_erosion"] = {
        f"B{Bm}_pi{pi}": info[idx_of[(Bm, pi, 0)]]["diff"] - info[idx_of[(Bm, pi, 50)]]["diff"]
        for Bm, pi in pairs
    }
    hp = holm([s1["p_onesided"], s2["p_onesided"]])
    s1["holm_p"], s2["holm_p"] = float(hp[0]), float(hp[1])
    s1["pass"] = bool(s1["lb95_onesided"] > 0 and s1_pt >= s1_mme and hp[0] < 0.05)
    s2["pass"] = bool(s2["lb95_onesided"] > 0 and hp[1] < 0.05)
    # CF-S3
    ctrl = next(c for c in cells if c["control"])
    cid = ctrl["cell_id"]
    s3 = _two_sided(info[cid]["value_mon_vs_never"], boots[cid][1])
    s3.update(mme=info[cid]["mme"], cell=cid)
    s3["pass"] = bool(s3["hi"] <= s3["mme"])
    # secondary: per-cell diffs, Holm across the 12 useful cells
    ph = holm([info[c["cell_id"]]["diff_ci"]["p"] for c in useful])
    for c, a in zip(useful, ph):
        info[c["cell_id"]]["holm_p_12"] = float(a)
    results = {
        "run_id": run_id,
        "dry_run": dry,
        "seeds": seeds,
        "n": n,
        "B_boot": B,
        "CF_S1": s1,
        "CF_S2": s2,
        "CF_S3": s3,
        "partS_valid": s3["pass"],
        "cells": info,
    }
    (out / "results.json").write_text(json.dumps(results, indent=1))
    rt = time.time() - t0
    t = ["# Part S tables (auto-generated)\n"]
    f2 = lambda x: "NA" if x is None else f"{x:.2f}"
    t.append(
        "## Primary endpoints\n"
        + md(
            [
                "endpoint",
                "estimate",
                "one-sided 95% LB / two-sided CI",
                "threshold",
                "p (1-sided)",
                "Holm p",
                "pass",
            ],
            [
                [
                    "CF-S1",
                    f2(s1_pt),
                    f2(s1["lb95_onesided"]),
                    f"LB>0 and est>={s1_mme:.2f} (mean MME)",
                    f"{s1['p_onesided']:.4f}",
                    f"{s1['holm_p']:.4f}",
                    s1["pass"],
                ],
                [
                    "CF-S2",
                    f2(s2_pt),
                    f2(s2["lb95_onesided"]),
                    "LB>0",
                    f"{s2['p_onesided']:.4f}",
                    f"{s2['holm_p']:.4f}",
                    s2["pass"],
                ],
                [
                    "CF-S3 (control, value vs never)",
                    f2(s3["mean"]),
                    f"[{s3['lo']:.2f}, {s3['hi']:.2f}]",
                    f"upper<={s3['mme']:.2f}",
                    "-",
                    "-",
                    s3["pass"],
                ],
            ],
        )
    )
    rows = []
    for c in cells:
        i = info[c["cell_id"]]
        d = i["diff_ci"]
        rows.append(
            [
                c["cell_id"],
                i["monitor"],
                i["simple"],
                f2(i["cost_monitor"]),
                f2(i["cost_simple"]),
                f"{d['mean']:.2f} [{d['lo']:.2f}, {d['hi']:.2f}]",
                f2(i["mme"]),
                f"{i.get('holm_p_12', float('nan')):.4f}" if not c["control"] else "(control)",
                f2(i["cap_mon"]),
                f2(i["cap_simple"]),
                f2(i["Ns_mon"]),
                f2(i["Ns_simple"]),
                i["alpha"],
            ]
        )
    t.append(
        "\n## Secondary: per-cell diff = cost(simple) - cost(monitor system) (positive favours monitor)\n"
        + md(
            [
                "cell",
                "monitor system",
                "simple",
                "cost mon",
                "cost simple",
                "diff [95% CI]",
                "MME",
                "Holm p (12 cells)",
                "headroom captured mon",
                "captured simple",
                "N_s mon",
                "N_s simple",
                "alpha",
            ],
            rows,
        )
    )
    t.append(
        "\n## Reference costs\n"
        + md(
            ["cell", "never", "always", "dynamic oracle", "headroom"],
            [
                [
                    c["cell_id"],
                    f2(info[c["cell_id"]]["never"]),
                    f2(info[c["cell_id"]]["always"]),
                    f2(info[c["cell_id"]]["dynamic"]),
                    f2(info[c["cell_id"]]["headroom"]),
                ]
                for c in cells
            ],
        )
    )
    t.append(
        "\n## Delay erosion per (B, pi_b): diff(d=0) - diff(d=50)\n"
        + md(["pair", "erosion"], [[k, f2(v)] for k, v in s2["per_pair_erosion"].items()])
    )
    (out / "tables.md").write_text("\n".join(t), encoding="utf8")
    (out / ("DONE_dry" if dry else "DONE_synthetic")).write_text("done")
    append_run(
        run_id,
        {
            "part": "S",
            "dry_run": dry,
            "protocol_sha256": sha256(PROTO),
            "selected_configs_sha256": sha256(SEL),
            "script_sha256": sha256(SELF),
            "n": n,
            "B_boot": B,
            "cells": [c["cell_id"] for c in cells],
            "script": "scripts/decision_value/run_confirmation.py",
        },
        {"seed_base": base, "seed_step": CONF_SEED_STEP, "cal": 5_000_000},
        n,
        rt,
        [out],
        confirmation=not dry,
    )
    print("\n".join(t))
    print(f"done {rt:.0f}s -> {out}")


# ======================================================================== Part R: loaders
def load_opsd_w(audit, root, cache, win, nrows):
    p = root / "raw/opsd/2020-10-06/hourly.csv"
    df = pd.read_csv(
        p,
        usecols=[
            "utc_timestamp",
            "DE_load_actual_entsoe_transparency",
            "DE_load_forecast_entsoe_transparency",
        ],
        nrows=nrows,
    )
    df["t"] = pd.to_datetime(df["utc_timestamp"], utc=True).dt.tz_localize(None)
    if nrows is not None:
        assert df["t"].max() < pd.Timestamp("2019-12-31T23:00:00"), "holdout leak (dry run)"
    df = df.set_index("t")
    y, ext = df["DE_load_actual_entsoe_transparency"], df["DE_load_forecast_entsoe_transparency"]
    fit = ("2015-01-01", "2016-12-31")
    out = {}
    for tag, w in (("val", ("2017-01-01", "2017-12-31")), ("dev", win)):
        audit.day_ahead_task(
            f"opsd_{tag}",
            y,
            "Europe/Berlin",
            fit,
            "2017-12-31",
            w,
            delays=(2,),
            ext=ext,
            outdir=cache / f"opsd_{tag}",
            rng=None,
        )
        out[tag] = pd.read_csv(cache / f"opsd_{tag}" / "per_step_losses.csv")
    alpha = json.loads((cache / "opsd_dev" / "summary.json").read_text())["ridge_alpha"]
    return out, {"ridge_alpha": alpha, "rows_read": len(df), "max_utc_read": str(df.index.max())}


def load_monash_w(audit, root, cache, win, years):
    z = zipfile.ZipFile(root / "raw/monash/4656140/electricity_hourly_dataset.zip")
    name = next(n for n in z.namelist() if n.endswith(".tsf"))
    N = 24 * years
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
    fit = ("2012-01-01", "2012-12-31")
    out = {}
    for tag, w in (("val", ("2013-01-01", "2013-03-31")), ("dev", win)):
        audit.day_ahead_task(
            f"monash_{tag}",
            y,
            None,
            fit,
            "2013-03-31",
            w,
            delays=(2,),
            outdir=cache / f"monash_{tag}",
            rng=None,
        )
        out[tag] = pd.read_csv(cache / f"monash_{tag}" / "per_step_losses.csv")
    return out, {"n_series_aggregated": n_series, "values_parsed_per_series": N}


def load_binance_w(root, months, eval_start, eval_stop_excl, delay_bars=1, refit_every=24, win=720):
    """Same pair specification as run_real_data.load_binance. months: list of (year, month).
    Frozen model: fit on bars [30, 2025-07-01) (phase-1 model), refit-free. Validation (pseudo): frozen on
    Jan-Mar 2025, evaluated Apr-Jun 2025. Evaluation window: [eval_start, eval_stop_excl)."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    rows = []
    for yr, m in months:
        zp = root / f"raw/binance/ETHUSDT-1h-{yr}-{m:02d}.zip"
        chk = (root / f"raw/binance/ETHUSDT-1h-{yr}-{m:02d}.CHECKSUM").read_text().split()[0]
        assert hashlib.sha256(zp.read_bytes()).hexdigest() == chk, f"checksum {zp}"
        z = zipfile.ZipFile(zp)
        rows.append(
            pd.read_csv(z.open(z.namelist()[0]), header=None, usecols=[0, 4], names=["o", "c"])
        )
    k = pd.concat(rows, ignore_index=True)
    o = k.o.astype("int64")
    o = o.where(o < 10**14, o // 1000)  # microsecond epochs (2025+) -> ms; ms stays
    ts = pd.to_datetime(o, unit="ms")
    assert (np.diff(ts.values).astype("timedelta64[h]").astype(int) == 1).all(), "gap/dup in bars"
    assert ts.max() < pd.Timestamp(eval_stop_excl), "bars beyond declared window"
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
    ev0 = int(ts.searchsorted(pd.Timestamp(eval_start)))

    def pair(train_end, start, stop):
        tr0 = np.arange(30, train_end - 1)
        sc = StandardScaler().fit(F[tr0])
        Fs = sc.transform(np.nan_to_num(F))
        f0 = LogisticRegression(C=1.0, max_iter=500).fit(Fs[tr0], yv[tr0])
        l0, l1, m1 = [], [], None
        for t in range(start, stop):
            if (t - start) % refit_every == 0:
                hi = t - delay_bars
                m1 = LogisticRegression(C=1.0, max_iter=500).fit(
                    Fs[max(30, hi - win) : hi], yv[max(30, hi - win) : hi]
                )
            l0.append(float(f0.predict(Fs[t : t + 1])[0] != yv[t]))
            l1.append(float(m1.predict(Fs[t : t + 1])[0] != yv[t]))
        return pd.DataFrame(
            {"ts": ts[start:stop].astype(str).to_numpy(), "frozen": l0, "sliding": l1}
        )

    val = pair(apr, apr, jul - 1)
    dev = pair(jul, ev0, n - 1)
    return {"val": val, "dev": dev}, {
        "max_ts_loaded": str(ts.max()),
        "eval_first_bar": str(ts[ev0]),
        "n_bars_eval": len(dev),
    }


def load_all(root: Path, dry: bool, cache: Path):
    rr = RR()
    audit = rr.load_audit()
    if dry:
        o_win, o_rows = ("2018-01-01", "2019-12-31"), 43824
        m_win, m_years = ("2013-04-01", "2013-12-31"), 366 + 365
        b_months, b_start, b_stop = [(2025, m) for m in range(1, 13)], "2025-07-01", "2026-01-01"
    else:
        o_win, o_rows = ("2020-01-01", "2020-09-30"), None
        m_win, m_years = ("2014-01-01", "2014-12-31"), 366 + 365 + 365
        b_months = [(2025, m) for m in range(1, 13)] + [(2026, m) for m in range(1, 10)]
        b_start, b_stop = "2026-01-01", "2026-10-01"
    data, prov = {}, {}
    data["opsd"], prov["opsd"] = load_opsd_w(audit, root, cache, o_win, o_rows)
    data["monash"], prov["monash"] = load_monash_w(audit, root, cache, m_win, m_years)
    data["binance"], prov["binance"] = load_binance_w(root, b_months, b_start, b_stop)
    if dry:  # the loaders reproduce the run_real_data development loaders exactly
        c2 = cache / "_ref"
        ref = {}
        ref["opsd"], _ = rr.load_opsd(audit, root, c2)
        ref["monash"], _ = rr.load_monash(audit, root, c2)
        ref["binance"], _ = rr.load_binance(root, c2)
        for t in data:
            for w in ("val", "dev"):
                a, b = data[t][w], ref[t][w]
                assert list(a.columns) == list(b.columns) and len(a) == len(b), (t, w)
                for col in a.columns:
                    if col != "ts":
                        assert np.allclose(
                            a[col].to_numpy(float), b[col].to_numpy(float), atol=1e-12
                        ), (t, w, col)
        prov["loader_equals_dev_loader"] = True
    else:  # frozen-model / specification consistency with phase 1
        dev_alpha = json.loads(
            (DEV_REPLAY / "partA" / "losses" / "opsd_dev" / "summary.json").read_text()
        )["ridge_alpha"]
        assert prov["opsd"]["ridge_alpha"] == dev_alpha, "ridge penalty differs from phase 1"
    return data, prov


# ======================================================================== Part R: worker
MONS = ("cusum", "page_hinkley", "batch", "sr_betting", "kelly_h2c_inspired")
CTRLS = ("permanent", "hold:7", "hold:30", "reverse")
PRIMARY_PAIR = "opsd_tso_vs_sliding"
N_REV = 2000


def _cost_of(sim, es, c_s):
    Ls, Ns = DA.cost_parts(sim.actions, es.raw0, es.raw1)
    return Ls + c_s * Ns


def _bootstrap_pair(P, thr_c, unit, n_boot, n_rev):
    """Moving-block bootstrap of the reserved-window joint paired losses; CUSUM+Hold(7), c_s=5, d=1, q=1."""
    rr = RR()
    raw0, raw1, s0, s1 = P["raw0"], P["raw1"], P["s0"], P["s1"]
    T = len(raw0)
    cal = rr.GRAN[P["task"]]["cal"]
    cs = 5.0
    fb = FeedbackContract(1.0, 1)
    res = {}
    for bi, blk in enumerate((7 * unit, 28 * unit)):
        rng = np.random.default_rng([rr.SEED, 900 + P["pidx"], bi])
        E_prim, E_sec, V_never, extra = [], [], [], {}
        for lo in range(0, n_boot, 1000):
            n = min(1000, n_boot - lo)
            idx = DA.block_indices(rng, T, T, n, blk)
            es = DA.EpisodeSet(raw0[idx], raw1[idx], s0[idx], s1[idx], "boot", {})
            batch = EpisodeBatch(es.s0, es.s1, np.ones((n, T), bool))
            fac = monitor_factory("cusum", "paired", cal, **rr.HP["cusum"])
            m = fac(n)
            m.threshold = thr_c
            mon = _cost_of(simulate(batch, fb, m, C.Hold(n, T, 0.0, H=7)), es, cs)
            never = es.raw0.sum(axis=1)
            always = es.raw1.sum(axis=1) + cs
            cal28 = _cost_of(simulate(batch, fb, None, C.CalendarBatch(n, T, 0.0, K=28)), es, cs)
            E_prim.append(np.minimum(never, cal28) - mon)
            E_sec.append(np.minimum(np.minimum(never, always), cal28) - mon)
            V_never.append(never - mon)
            if (
                bi == 0 and lo < n_rev
            ):  # all five monitors on the first block-7 resamples (reversal classes)
                for mname in MONS:
                    f2 = monitor_factory(mname, "paired", cal, **rr.HP[mname])
                    m2 = f2(n)
                    m2.threshold = P["thr"][(mname, 1, 1.0)]
                    sim = simulate(batch, fb, m2, C.Hold(n, T, 0.0, H=7))
                    al = sim.alarm
                    fa = np.where(al.any(axis=1), al.argmax(axis=1), T)
                    ex = extra.setdefault(mname, {"cost": [], "pow": [], "delay": []})
                    ex["cost"].append(_cost_of(sim, es, cs))
                    ex["pow"].append(al.any(axis=1).astype(float))
                    ex["delay"].append(fa.astype(float))
        out = {}
        for tag, arr in (
            ("E_primary_def", E_prim),
            ("E_secondary_def", E_sec),
            ("V_vs_never", V_never),
        ):
            a = np.concatenate(arr)
            lo_, hi_ = np.quantile(a, [0.025, 0.975])
            p = min(1.0, 2 * min((a <= 0).mean(), (a >= 0).mean()) + 1.0 / (len(a) + 1))
            out[tag] = {
                "boot_mean": float(a.mean()),
                "lo": float(lo_),
                "hi": float(hi_),
                "p": float(p),
                "frac_pos": float((a > 0).mean()),
            }
        if extra:
            ex = {k: {kk: np.concatenate(vv) for kk, vv in v.items()} for k, v in extra.items()}
            mme = 0.01 * float(raw0.sum())
            revs, tot = [], 0
            for a in MONS:
                for b in MONS:
                    if a == b:
                        continue
                    tot += 1
                    rv = classify_reversal(
                        ex[a]["pow"],
                        ex[b]["pow"],
                        ex[a]["delay"],
                        ex[b]["delay"],
                        ex[a]["cost"],
                        ex[b]["cost"],
                        mme,
                        B=2000,
                        seed=0,
                    )
                    if rv["reversal"]:
                        revs.append(f"{a} over {b} via {','.join(rv['detection_via'])}")
            out["reversal_classification"] = {
                "n_ordered_pairs": tot,
                "n_reversals": len(revs),
                "reversals": revs,
                "n_boot_series": len(ex["cusum"]["cost"]),
                "mme_used": mme,
            }
        out["block"] = blk
        res[f"block{blk}"] = out
    return res


def pair_task(arg):
    P, n_cal, n_masks, n_boot, n_rev = arg
    rr = RR()
    t0 = time.time()
    g = rr.GRAN[P["task"]]
    sp = DA.fit_scaling(P["val0"], P["val1"])
    v0, v1, _ = DA.apply_scaling(P["val0"], P["val1"], sp)
    s0, s1, nclip = DA.apply_scaling(P["dev0"], P["dev1"], sp)
    P = dict(P, raw0=P["dev0"], raw1=P["dev1"], s0=s0, s1=s1)
    T = len(s0)
    thr, calib = {}, []
    for mname in MONS:
        fac = monitor_factory(mname, "paired", g["cal"], **rr.HP[mname])
        for d in rr.DELAYS:
            for q in rr.QS:
                th, fr = DA.calibrate_horizons(
                    fac,
                    v0,
                    v1,
                    "paired",
                    q,
                    d,
                    [T],
                    g["b_null"],
                    rr.ALPHA,
                    n_cal,
                    chunk=min(500, n_cal),
                    n_fresh=min(500, n_cal),
                )
                thr[(mname, d, q)] = th[T]
                calib.append(
                    {
                        "pair": P["key"],
                        "monitor": mname,
                        "d": d,
                        "q": q,
                        "horizon": T,
                        "threshold": th[T],
                        "fresh_null_alarm_rate": fr[T],
                    }
                )
    P["thr"] = thr
    rows, detect = [], {}
    for qi, q in enumerate(rr.QS):
        es = DA.actual_set(P["dev0"], P["dev1"], s0, s1, 1 if q == 1.0 else n_masks)
        orc = rr.oracles(es)
        batch = DA.episode_batch(es, q, [rr.SEED, P["pidx"], 0, qi])
        for d in rr.DELAYS:
            fb = FeedbackContract(q, d)
            base0 = {"pair": P["key"], "mode": "actual", "q": q, "d": d}
            rows += rr.episode_rows(
                dict(base0, target="-", monitor="-", controller="never"),
                es,
                es.raw0.sum(axis=1),
                np.zeros(es.n),
                None,
                orc,
            )
            rows += rr.episode_rows(
                dict(base0, target="-", monitor="-", controller="always"),
                es,
                es.raw1.sum(axis=1),
                np.ones(es.n),
                None,
                orc,
            )
            for rname, (kind, arg_) in rr.CAL_BLOCK_REFS.items():
                if kind == "calendar":
                    ctrl = rr.make_controller(f"calendar:{arg_}", es.n, T, 0.0, None, np.inf)
                    Ls, Ns = DA.cost_parts(
                        simulate(batch, fb, None, ctrl).actions, es.raw0, es.raw1
                    )
                    rows += rr.episode_rows(
                        dict(base0, target="-", monitor="-", controller=rname),
                        es,
                        Ls,
                        Ns,
                        None,
                        orc,
                    )
                else:
                    for cs in rr.COSTS:
                        ctrl = rr.make_controller(f"static:{arg_}", es.n, T, cs, None, np.inf)
                        Ls, Ns = DA.cost_parts(
                            simulate(batch, fb, None, ctrl).actions, es.raw0, es.raw1
                        )
                        rr_ = rr.episode_rows(
                            dict(base0, target="-", monitor="-", controller=rname),
                            es,
                            Ls,
                            Ns,
                            None,
                            orc,
                        )
                        rows += [r for r in rr_ if r["c_s"] == cs]
            for mname in MONS:
                fac = monitor_factory(mname, "paired", g["cal"], **rr.HP[mname])
                th = thr[(mname, d, q)]
                for cspec in CTRLS:
                    m = fac(es.n)
                    m.threshold = th
                    ctrl = rr.make_controller(cspec, es.n, T, 0.0, fac, th)
                    sim = simulate(batch, fb, m, ctrl)
                    Ls, Ns = DA.cost_parts(sim.actions, es.raw0, es.raw1)
                    al = sim.alarm
                    fa = np.where(al.any(axis=1), al.argmax(axis=1), np.nan)
                    cname = cspec.replace(":", "")
                    rows += rr.episode_rows(
                        dict(base0, target="paired", monitor=mname, controller=cname),
                        es,
                        Ls,
                        Ns,
                        fa,
                        orc,
                    )
                    if q == 1.0 and d == 1 and cspec in ("permanent", "hold:7"):
                        lab = P["labels"]
                        key = f"{mname}|{cname}"
                        if cspec == "permanent":
                            detect[key] = {
                                "first_alarm": lab[int(fa[0])] if not np.isnan(fa[0]) else None,
                                "n_alarm_steps": int(al[0].sum()),
                            }
                        else:
                            trig = np.flatnonzero(DA.hold_triggers(al, 7)[0])
                            sw = np.flatnonzero(np.diff(np.concatenate([[0], sim.actions[0]])))
                            detect[key] = {
                                "n_triggers": len(trig),
                                "trigger_dates": [lab[i] for i in trig[:20]],
                                "n_switches": len(sw),
                            }
    boot = _bootstrap_pair(
        P, thr[("cusum", 1, 1.0)], 24 if g["step"] == "hour" else 1, n_boot, n_rev
    )
    info = {
        "T": T,
        "first_label": P["labels"][0],
        "last_label": P["labels"][-1],
        "n_val": len(P["val0"]),
        "scaling": sp.to_dict(),
        "n_clipped_eval_steps": nclip,
        "mean_raw_loss_inc": float(P["dev0"].mean()),
        "mean_raw_loss_chal": float(P["dev1"].mean()),
        "runtime_s": time.time() - t0,
    }
    return P["key"], rows, calib, detect, boot, info


# ======================================================================== Part R: driver + analysis
def real(dry: bool, procs: int, data_root: str, pairs_sel, n_cal, n_masks, n_boot, compare_dev):
    if not dry:
        verify_hashes()
        guard_oneshot("real")
    rr = RR()
    root = Path(data_root)
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"{'dryrun_' if dry else ''}confirm_real_{ts}"
    out = (DEV_OUT if dry else CONF_OUT) / run_id
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    data, prov = load_all(root, dry, out / "losses")
    (out / "provenance.json").write_text(json.dumps(prov, indent=1, default=str))
    want = [p for p in rr.PAIRS if (not pairs_sel or p["key"] in pairs_sel)]
    tasks = []
    for pi, p in enumerate(rr.PAIRS):
        if p not in want:
            continue
        d = data[p["task"]]
        labels = (
            d["dev"]["ts"].tolist()
            if p["task"] == "binance"
            else [str(datetime.fromordinal(int(o)).date()) for o in d["dev"]["day_ordinal"]]
        )
        P = {
            "key": p["key"],
            "task": p["task"],
            "role": p["role"],
            "pidx": pi,
            "val0": d["val"][p["a"]].to_numpy(float),
            "val1": d["val"][p["b"]].to_numpy(float),
            "dev0": d["dev"][p["a"]].to_numpy(float),
            "dev1": d["dev"][p["b"]].to_numpy(float),
            "labels": labels,
        }
        tasks.append((P, n_cal, n_masks, n_boot, min(N_REV, n_boot)))
    rows, calib, detect, boot, info = [], [], {}, {}, {}
    with Pool(min(procs, len(tasks))) as pool:
        for key, r, c, dt, bt, inf in pool.imap_unordered(pair_task, tasks):
            rows += r
            calib += c
            detect[key], boot[key], info[key] = dt, bt, inf
            print(f"  pair {key} done ({inf['runtime_s']:.0f}s)", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(out / "cells.csv.gz", index=False)
    pd.DataFrame(calib).to_csv(out / "calibration.csv", index=False)
    (out / "detection_actual.json").write_text(json.dumps(detect, indent=1))
    (out / "bootstrap.json").write_text(json.dumps(boot, indent=1))
    (out / "pair_info.json").write_text(json.dumps(info, indent=1))
    res, tables = analyze_real(df, boot, info, dry)
    if compare_dev:
        res["dev_comparison"] = _compare_dev(df)
    (out / "results.json").write_text(json.dumps(res, indent=1, default=float))
    (out / "tables.md").write_text(tables, encoding="utf8")
    (out / ("DONE_dry" if dry else "DONE_real")).write_text("done")
    rt = time.time() - t0
    append_run(
        run_id,
        {
            "part": "R",
            "dry_run": dry,
            "protocol_sha256": sha256(PROTO),
            "dev_results_sha256": sha256(DEVREAL),
            "selected_configs_sha256": sha256(SEL),
            "script_sha256": sha256(SELF),
            "pairs": [p["key"] for p in want],
            "n_cal": n_cal,
            "n_masks": n_masks,
            "n_boot": n_boot,
            "provenance": prov,
            "script": "scripts/decision_value/run_confirmation.py",
        },
        {
            "eval": rr.SEED,
            "calibration": 5_100_000,
            "calibration_check": 5_200_000,
            "bootstrap": [rr.SEED, 900],
        },
        int(df.n_ep.sum()),
        rt,
        [out / "cells.csv.gz", out / "results.json"],
        confirmation=not dry,
    )
    print(tables)
    print(json.dumps(res.get("verdict", {}), indent=1))
    print(f"done {rt:.0f}s -> {out}")


def _compare_dev(df):
    dev = pd.read_csv(DEV_REPLAY / "cells.csv.gz")
    keys = ["pair", "mode", "q", "d", "c_s", "target", "monitor", "controller"]
    m = df[df.q == 1.0].merge(dev[dev.q == 1.0], on=keys, suffixes=("", "_dev"))
    return {
        "n_matched": len(m),
        "max_abs_cost_diff": float((m.cost_mean - m.cost_mean_dev).abs().max()) if len(m) else None,
    }


def analyze_real(df, boot, info, dry):
    df = df.copy()
    df["V"] = df.never_mean - df.cost_mean

    def cost(pair, ctrl, mon="-", **kw):
        s = df[
            (df.pair == pair)
            & (df.controller == ctrl)
            & (df.monitor == mon)
            & (df.q == kw.get("q", 1.0))
            & (df.d == kw.get("d", 1))
            & (df.c_s == kw.get("c_s", 5.0))
        ]
        assert len(s) == 1, (pair, ctrl, mon, kw, len(s))
        return float(s.cost_mean.iloc[0])

    res = {"dry_run": dry, "pairs": {}}
    for pair in df.pair.unique():
        never, always, cal28 = cost(pair, "never"), cost(pair, "always"), cost(pair, "calendar28")
        mon = cost(pair, "hold7", "cusum")
        dyn = float(
            df[
                (df.pair == pair)
                & (df.controller == "never")
                & (df.q == 1.0)
                & (df.d == 1)
                & (df.c_s == 5.0)
            ].dyn_mean.iloc[0]
        )
        v = df[
            (df.pair == pair)
            & (df.target == "paired")
            & (df.q == 1.0)
            & (df.d == 1)
            & (df.c_s == 5.0)
        ]
        mme = 0.01 * never
        b7, b28 = [boot[pair][k] for k in sorted(boot[pair], key=lambda s: int(s[5:]))]
        res["pairs"][pair] = {
            "never": never,
            "always": always,
            "calendar28": cal28,
            "static28": cost(pair, "static28"),
            "cusum_hold7": mon,
            "dynamic_oracle": dyn,
            "headroom": never - dyn,
            "MME": mme,
            "E_primary_def": min(never, cal28) - mon,
            "E_secondary_def": min(never, always, cal28) - mon,
            "V_cusum_hold7_vs_never": never - mon,
            "frac_headroom_captured_cusum_hold7": (never - mon) / (never - dyn)
            if never - dyn > 1e-9
            else None,
            "max_V_vs_never_20cells_cs5": float(v.V.max()),
            "argmax_cell_cs5": f"{v.loc[v.V.idxmax(), 'monitor']}|{v.loc[v.V.idxmax(), 'controller']}",
            "max_V_vs_never_by_cs": {
                str(c): float(
                    df[
                        (df.pair == pair)
                        & (df.target == "paired")
                        & (df.q == 1.0)
                        & (df.d == 1)
                        & (df.c_s == c)
                    ].V.max()
                )
                for c in (0.0, 1.0, 5.0, 20.0)
            },
            "bootstrap": {"block7": b7, "block28": b28},
        }
    verdict = {}
    if PRIMARY_PAIR in res["pairs"]:
        p = res["pairs"][PRIMARY_PAIR]
        E, mme = p["E_primary_def"], p["MME"]
        lo7, lo28 = (
            p["bootstrap"]["block7"]["E_primary_def"]["lo"],
            p["bootstrap"]["block28"]["E_primary_def"]["lo"],
        )
        prim_pass = bool(E > mme and lo7 > 0 and lo28 > 0)
        verdict["primary"] = {
            "E": E,
            "MME": mme,
            "CI_lo_block7": lo7,
            "CI_hi_block7": p["bootstrap"]["block7"]["E_primary_def"]["hi"],
            "CI_lo_block28": lo28,
            "CI_hi_block28": p["bootstrap"]["block28"]["E_primary_def"]["hi"],
            "pass": prim_pass,
        }
        ctr = {}
        for ck in ("monash_frozen_vs_sliding", "binance_frozen_vs_sliding"):
            if ck in res["pairs"]:
                c = res["pairs"][ck]
                ctr[ck] = {
                    "max_V": c["max_V_vs_never_20cells_cs5"],
                    "MME": c["MME"],
                    "pass": bool(c["max_V_vs_never_20cells_cs5"] <= c["MME"]),
                    "argmax": c["argmax_cell_cs5"],
                }
        verdict["controls"] = ctr
        verdict["part_R_pass"] = bool(
            prim_pass and len(ctr) == 2 and all(x["pass"] for x in ctr.values())
        )
        sec4 = [k for k in res["pairs"] if k != PRIMARY_PAIR]
        ps = [res["pairs"][k]["bootstrap"]["block7"]["E_secondary_def"]["p"] for k in sec4]
        ph = holm(ps) if ps else []
        verdict["secondary_holm_block7"] = {
            k: {
                "E_secondary_def": res["pairs"][k]["E_secondary_def"],
                "p_boot": a,
                "holm_p": float(b),
            }
            for k, a, b in zip(sec4, ps, ph)
        }
    res["verdict"] = verdict
    # ---- tables
    f1 = lambda x: (
        "NA" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.1f}"
    )
    T = ["# Part R tables (auto-generated)\n"]
    if verdict:
        pv = verdict["primary"]
        T.append(
            "## Primary endpoint (OPSD TSO vs sliding; CUSUM+Hold7 minus better of never/calendar28; c_s=5, d=1, q=1)\n"
            + md(
                ["E (loss units)", "MME", "CI block 7 d", "CI block 28 d", "pass"],
                [
                    [
                        f1(pv["E"]),
                        f1(pv["MME"]),
                        f"[{f1(pv['CI_lo_block7'])}, {f1(pv['CI_hi_block7'])}]",
                        f"[{f1(pv['CI_lo_block28'])}, {f1(pv['CI_hi_block28'])}]",
                        pv["pass"],
                    ]
                ],
            )
        )
        T.append(
            "\n## Controls (max V vs never over 5 monitors x 4 controllers; c_s=5, d=1, q=1)\n"
            + md(
                ["control", "max V", "MME", "argmax cell", "pass"],
                [
                    [k, f1(v["max_V"]), f1(v["MME"]), v["argmax"], v["pass"]]
                    for k, v in verdict["controls"].items()
                ],
            )
        )
        T.append(f"\n**Part R pass: {verdict['part_R_pass']}**")
    T.append(
        "\n## Pair summary (c_s=5, d=1, q=1, actual series)\n"
        + md(
            [
                "pair",
                "T",
                "never",
                "always",
                "calendar28",
                "static28",
                "CUSUM+Hold7",
                "dynamic oracle",
                "headroom",
                "MME",
                "E (never/cal28 ref)",
                "E (never/always/cal28 ref)",
                "V vs never",
                "frac headroom",
                "max V (20 cells) c_s=0/1/5/20",
            ],
            [
                [
                    k,
                    info[k]["T"],
                    f1(v["never"]),
                    f1(v["always"]),
                    f1(v["calendar28"]),
                    f1(v["static28"]),
                    f1(v["cusum_hold7"]),
                    f1(v["dynamic_oracle"]),
                    f1(v["headroom"]),
                    f1(v["MME"]),
                    f1(v["E_primary_def"]),
                    f1(v["E_secondary_def"]),
                    f1(v["V_cusum_hold7_vs_never"]),
                    "NA"
                    if v["frac_headroom_captured_cusum_hold7"] is None
                    else f"{v['frac_headroom_captured_cusum_hold7']:.3f}",
                    " / ".join(
                        f1(v["max_V_vs_never_by_cs"][c]) for c in ("0.0", "1.0", "5.0", "20.0")
                    ),
                ]
                for k, v in res["pairs"].items()
            ],
        )
    )
    bt = []
    for k, v in res["pairs"].items():
        for bk in ("block7", "block28"):
            b = v["bootstrap"][bk]
            bt.append(
                [
                    k,
                    bk,
                    f1(b["E_primary_def"]["boot_mean"]),
                    f"[{f1(b['E_primary_def']['lo'])}, {f1(b['E_primary_def']['hi'])}]",
                    f"[{f1(b['E_secondary_def']['lo'])}, {f1(b['E_secondary_def']['hi'])}]",
                    f"{b['E_secondary_def']['p']:.4f}",
                    f"{b['E_primary_def']['frac_pos']:.3f}",
                ]
            )
    T.append(
        "\n## Block bootstrap of the endpoint (resamples per config; understates persistence)\n"
        + md(
            [
                "pair",
                "block",
                "boot mean E (primary def)",
                "CI E (never/cal28 ref)",
                "CI E (never/always/cal28 ref)",
                "p (2-sided, secondary def)",
                "frac resamples E>0",
            ],
            bt,
        )
    )
    if verdict:
        T.append(
            "\n## Secondary comparisons, Holm across the 4 non-primary pairs (block 7)\n"
            + md(
                ["pair", "E (never/always/cal28 ref)", "boot p", "Holm p"],
                [
                    [k, f1(v["E_secondary_def"]), f"{v['p_boot']:.4f}", f"{v['holm_p']:.4f}"]
                    for k, v in verdict["secondary_holm_block7"].items()
                ],
            )
        )
    for pair in res["pairs"]:
        s = df[
            (df.pair == pair)
            & (df.target == "paired")
            & (df.q == 1.0)
            & (df.d == 1)
            & (df.c_s == 5.0)
        ]
        pv = s.pivot_table(index="monitor", columns="controller", values="V").reset_index()
        T.append(
            f"\n## V vs never, {pair}, c_s=5, d=1, q=1 (5 monitors x 4 controllers)\n"
            + md(
                list(pv.columns),
                [[f1(x) if not isinstance(x, str) else x for x in r] for r in pv.to_numpy()],
            )
        )
        det = s[s.controller == "permanent"][["monitor", "first_alarm_cens_mean", "power"]]
        T.append(
            "\nfirst alarm step (censored at T) / alarmed: "
            + "; ".join(
                f"{r.monitor}: {r.first_alarm_cens_mean:.0f}/{int(r.power)}"
                for r in det.itertuples()
            )
        )
    for pair in res["pairs"]:
        g = df[(df.pair == pair) & (df.monitor == "cusum") & (df.controller == "hold7")]
        ref = (
            df[(df.pair == pair) & (df.controller.isin(["never", "calendar28"]))]
            .groupby(["q", "d", "c_s", "controller"])
            .cost_mean.first()
            .unstack()
        )
        gg = g.set_index(["q", "d", "c_s"]).cost_mean
        sens = [
            [q, d, c, f1(float(ref.loc[(q, d, c)].min() - gg.loc[(q, d, c)]))]
            for (q, d, c) in gg.index
        ]
        T.append(
            f"\n## Sensitivity, {pair}: E = better of never/calendar28 minus CUSUM+Hold7\n"
            + md(["q", "d", "c_s", "E"], sens)
        )
    rv = [
        (k, v["bootstrap"]["block7"].get("reversal_classification"))
        for k, v in res["pairs"].items()
    ]
    for k, r_ in rv:
        if r_:
            T.append(
                f"\n## Reversal classification ({k}, block-7 bootstrap, {r_['n_boot_series']} series): {r_['n_reversals']} of {r_['n_ordered_pairs']} ordered monitor pairs\n"
                + "\n".join(f"- {x}" for x in r_["reversals"])
            )
    return res, "\n".join(T)


# ======================================================================== main
def write_hashes():
    MAN.mkdir(parents=True, exist_ok=True)
    out = {
        "created_utc": datetime.now(UTC).isoformat(),
        "files": {r: sha256(ROOT / r) for r in HASHED},
    }
    HASHES.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["files"], indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["step0", "synthetic", "real", "write-hashes"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--data-root", default=str(DEFAULT_DATA))
    ap.add_argument("--pairs", nargs="*", default=None, help="dry-run only")
    ap.add_argument("--n-cal", type=int, default=2000)
    ap.add_argument("--n-masks", type=int, default=100)
    ap.add_argument("--n-boot", type=int, default=BOOT)
    ap.add_argument("--compare-dev", action="store_true", help="dry-run only")
    a = ap.parse_args()
    if a.cmd == "step0":
        step0(a.procs)
    elif a.cmd == "write-hashes":
        write_hashes()
    elif a.cmd == "synthetic":
        synthetic(a.dry_run, a.procs)
    else:
        if not a.dry_run and (
            a.pairs or a.n_cal != 2000 or a.n_masks != 100 or a.n_boot != BOOT or a.compare_dev
        ):
            raise SystemExit("non-default options are allowed only with --dry-run")
        real(a.dry_run, a.procs, a.data_root, a.pairs, a.n_cal, a.n_masks, a.n_boot, a.compare_dev)


if __name__ == "__main__":
    main()
