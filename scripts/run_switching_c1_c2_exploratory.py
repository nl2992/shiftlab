"""EXPLORATORY C1/C2 switching comparison (R4, development only; no efficacy claim).

Protocol: docs/switching_c1_c2_exploratory_protocol_v1.md
Run from the repository root:
    uv run --no-sync python scripts/run_switching_c1_c2_exploratory.py --mode full
    uv run --no-sync python scripts/run_switching_c1_c2_exploratory.py --mode smoke
"""

from __future__ import annotations

import os

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")  # one BLAS thread per worker process

import argparse
import hashlib
import json
import subprocess
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction as F
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from shiftlab.dive.switching_explore import (
    BASELINES,
    C2_RHOS,
    SCENARIOS,
    Config,
    Stream,
    bernoulli_grid_spec,
    block_bootstrap_ci,
    build_method,
    clairvoyant_actions,
    fit_gaussian_hmm,
    gaussian_grid_spec,
    make_bernoulli_stream,
    make_scenario_stream,
    paired_ci,
    run,
    score_actions,
    wilson,
)

ROOT = Path(__file__).resolve().parents[1]
SAFE_BASELINES = (
    "no_switch",
    "episode_geo",
    "episode_equal",
    "episode_front",
    "allonset_edetector",
)
C2_NAMES = tuple(f"c2_rho{r:g}" for r in C2_RHOS)
SYN_METHODS = (*BASELINES, "c1_hmm_cs", *C2_NAMES)
FIELDS = (
    "cost",
    "decision_loss",
    "queries",
    "switches",
    "wasted",
    "promotions",
    "fp_regime",
    "fp_pred",
)
DEV_SEEDS = tuple(range(8))
EVAL_SEEDS = tuple(range(1000, 1030))
SYN_TS = (200, 1000)
SYN_BFRACS = (0.10, 0.25)
SYN_DS = (1, 10)
SYN_COST = {"c": 0.01, "s": 0.1, "h": 0.1, "alpha": 0.1}
SOURCE_FILES = (
    "src/shiftlab/dive/switching_explore.py",
    "scripts/run_switching_c1_c2_exploratory.py",
    "tests/test_switching_explore.py",
    "docs/switching_c1_c2_exploratory_protocol_v1.md",
)


# ------------------------------------------------------------------ synthetic cells


def _record(r) -> dict[str, float]:
    return {
        "cost": r.cost,
        "decision_loss": r.decision_loss,
        "queries": r.queries,
        "switches": r.switches,
        "wasted": r.wasted_queries,
        "promotions": r.promotions,
        "fp_regime": np.nan if r.fp_regime is None else r.fp_regime,
        "fp_pred": np.nan if r.fp_pred is None else r.fp_pred,
    }


def run_cell(task: tuple) -> dict:
    scenario, T, bfrac, d, seeds, methods = task
    B = round(bfrac * T)
    spec = bernoulli_grid_spec()
    out: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for seed in seeds:
        stream = make_scenario_stream(scenario, T, seed)
        cfg = Config(T=T, B=B, d=d, seed=seed, **SYN_COST)
        for name in methods:
            rec = _record(run(stream, build_method(name, spec), cfg))
            for k, v in rec.items():
                out[name][k].append(v)
        # evaluator-only references (no queries)
        for ref, act in (
            ("ref_always_f1", np.ones(T, dtype=int)),
            ("ref_regime_clairvoyant", clairvoyant_actions(stream)),
        ):
            rec = _record(score_actions(stream, cfg, act, np.zeros(T)))
            for k, v in rec.items():
                out[ref][k].append(v)
    return {
        "scenario": scenario,
        "T": T,
        "B": B,
        "d": d,
        "seeds": list(seeds),
        "methods": {m: {k: list(v) for k, v in rec.items()} for m, rec in out.items()},
    }


def cell_tasks(seeds, methods, scenarios, ts):
    return [
        (sc, T, bf, d, seeds, methods)
        for sc in scenarios
        for T in ts
        for bf in SYN_BFRACS
        for d in SYN_DS
    ]


def select_rho(dev_cells: list[dict]) -> tuple[float, dict]:
    """rho* = argmin over C2 variants of mean (cost - no_switch cost)/T across development cells."""
    scores = {}
    for name in C2_NAMES:
        vals = []
        for cell in dev_cells:
            m = cell["methods"]
            vals.append((np.mean(m[name]["cost"]) - np.mean(m["no_switch"]["cost"])) / cell["T"])
        scores[name] = float(np.mean(vals))
    best = min(scores, key=scores.get)
    return float(best[6:]), scores


def summarize_cells(cells: list[dict], c2_name: str) -> dict:
    rows = []
    for cell in cells:
        m = cell["methods"]
        mean_cost = {k: float(np.mean(v["cost"])) for k, v in m.items() if not k.startswith("ref_")}
        best_all = min(BASELINES, key=lambda k: mean_cost[k])
        best_safe = min(SAFE_BASELINES, key=lambda k: mean_cost[k])
        row = {
            "scenario": cell["scenario"],
            "T": cell["T"],
            "B": cell["B"],
            "d": cell["d"],
            "best_baseline": best_all,
            "best_safe_baseline": best_safe,
            "methods": {},
            "contrasts": {},
        }
        n = len(cell["seeds"])
        for k, v in m.items():
            fr = np.asarray(v["fp_regime"], dtype=float)
            fp = np.asarray(v["fp_pred"], dtype=float)
            row["methods"][k] = {
                "cost_mean": float(np.mean(v["cost"])),
                "cost_ci": paired_ci(np.asarray(v["cost"]))[1:],
                "queries": float(np.mean(v["queries"])),
                "switches": float(np.mean(v["switches"])),
                "wasted": float(np.mean(v["wasted"])),
                "decision_loss": float(np.mean(v["decision_loss"])),
                "promotions": float(np.mean(v["promotions"])),
                "fp_regime_any": float(np.mean(fr > 0)) if not np.isnan(fr).any() else None,
                "fp_regime_runs": int(np.sum(fr > 0)) if not np.isnan(fr).any() else None,
                "fp_pred_any": float(np.mean(fp > 0)) if not np.isnan(fp).any() else None,
                "fp_pred_runs": int(np.sum(fp > 0)) if not np.isnan(fp).any() else None,
                "n_runs": n,
            }
        for cand in ("c1_hmm_cs", c2_name):
            for label, ref in (
                ("vs_best_baseline", best_all),
                ("vs_best_safe_baseline", best_safe),
            ):
                diff = np.asarray(m[cand]["cost"]) - np.asarray(m[ref]["cost"])
                mean, lo, hi = paired_ci(diff)
                row["contrasts"][f"{cand}|{label}"] = {
                    "ref": ref,
                    "diff_mean": mean,
                    "ci": [lo, hi],
                    "diff_per_round": mean / cell["T"],
                }
        rows.append(row)
    return {"cells": rows}


def md_table(header: list[str], rows: list[list]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return "\n".join(out)


def aggregate_markdown(rows: list[dict], c2_name: str) -> str:
    cands = ("c1_hmm_cs", c2_name)
    parts = []
    present = [sc for sc in SCENARIOS if any(r["scenario"] == sc for r in rows)]
    # Primary contrast tables
    for label, title in (
        (
            "vs_best_baseline",
            "Primary: net-cost difference vs strongest baseline per cell (all baselines)",
        ),
        (
            "vs_best_safe_baseline",
            "Secondary: vs strongest safety-gated baseline per cell (no_switch, episode_*, allonset)",
        ),
    ):
        tbl = []
        for sc in present:
            sel = [r for r in rows if r["scenario"] == sc]
            line = [sc]
            for cand in cands:
                c = [r["contrasts"][f"{cand}|{label}"] for r in sel]
                dpr = np.mean([x["diff_per_round"] for x in c])
                better = sum(x["ci"][1] < 0 for x in c)
                worse = sum(x["ci"][0] > 0 for x in c)
                line += [f"{dpr:+.4f}", f"{better}/{worse}/{len(c) - better - worse}"]
            tbl.append(line)
        allc = []
        line = ["ALL"]
        for cand in cands:
            c = [r["contrasts"][f"{cand}|{label}"] for r in rows]
            dpr = np.mean([x["diff_per_round"] for x in c])
            better = sum(x["ci"][1] < 0 for x in c)
            worse = sum(x["ci"][0] > 0 for x in c)
            line += [f"{dpr:+.4f}", f"{better}/{worse}/{len(c) - better - worse}"]
        allc.append(line)
        header = ["scenario"] + [
            h
            for cand in cands
            for h in (f"{cand} mean diff/round", f"{cand} better/worse/ns cells")
        ]
        parts.append(
            f"**{title}** (negative = candidate cheaper; 8 cells per scenario)\n\n"
            + md_table(header, tbl + allc)
        )
    # Cost relative to no_switch, per scenario
    methods = [*BASELINES, "c1_hmm_cs", c2_name]
    tbl = []
    for sc in present:
        sel = [r for r in rows if r["scenario"] == sc]
        line = [sc]
        for mname in methods:
            v = np.mean(
                [
                    (r["methods"][mname]["cost_mean"] - r["methods"]["no_switch"]["cost_mean"])
                    / r["T"]
                    for r in sel
                ]
            )
            line.append(f"{v:+.4f}")
        tbl.append(line)
    refs = []
    for ref in ("ref_always_f1", "ref_regime_clairvoyant"):
        refs.append(
            np.mean(
                [
                    (r["methods"][ref]["cost_mean"] - r["methods"]["no_switch"]["cost_mean"])
                    / r["T"]
                    for r in rows
                ]
            )
        )
    parts.append(
        "**Mean cost per round minus no_switch**, averaged over the 8 cells of each scenario (negative = better than never switching)\n\n"
        + md_table(["scenario", *methods], tbl)
        + f"\n\nEvaluator-only references over all cells: always_f1 {refs[0]:+.4f}, regime_clairvoyant {refs[1]:+.4f}."
    )
    # False promotion
    tbl = []
    for sc in present:
        sel = [r for r in rows if r["scenario"] == sc]
        line = [sc]
        for mname in methods:
            k = sum(r["methods"][mname]["fp_regime_runs"] or 0 for r in sel)
            n = sum(r["methods"][mname]["n_runs"] for r in sel)
            kp = (
                sum(r["methods"][mname]["fp_pred_runs"] or 0 for r in sel)
                if sel[0]["methods"][mname]["fp_pred_runs"] is not None
                else None
            )
            p, lo, hi = wilson(k, n)
            cell = f"{p:.3f} [{lo:.3f},{hi:.3f}]"
            if kp is not None:
                cell += f" / {kp / n:.3f}"
            line.append(cell)
        tbl.append(line)
    parts.append(
        "**False-promotion frequency** (fraction of runs with at least one false promotion; regime-based with Wilson 95% interval, "
        "then `/` predictive-mean-based on HMM-drawn cells; pooled over the 8 cells x 30 seeds)\n\n"
        + md_table(["scenario", *methods], tbl)
    )
    # queries / switches
    tbl = []
    for mname in methods:
        q = np.mean([r["methods"][mname]["queries"] / max(r["B"], 1) for r in rows])
        w = np.mean([r["methods"][mname]["switches"] for r in rows])
        wasted = np.mean([r["methods"][mname]["wasted"] for r in rows])
        tbl.append([mname, f"{q:.2f}", f"{w:.2f}", f"{wasted:.2f}"])
    parts.append(
        "**Query use and switches** (mean over all 64 cells)\n\n"
        + md_table(["method", "queries / B", "switches", "queries never released"], tbl)
    )
    # best baseline frequency
    cnt = defaultdict(int)
    for r in rows:
        cnt[r["best_baseline"]] += 1
    parts.append(
        "Strongest baseline by cell count: " + ", ".join(f"{k} {v}" for k, v in sorted(cnt.items()))
    )
    return "\n\n".join(parts)


def extra_markdown(cells: list[dict], c2_name: str) -> str:
    """Secondary descriptive tables: rho sweep, closest separable composition, clairvoyant capture."""
    present = [sc for sc in SCENARIOS if any(c["scenario"] == sc for c in cells)]

    def mc(cell, name):
        return np.asarray(cell["methods"][name]["cost"], dtype=float)

    parts = []
    tbl = []
    for sc in present:
        sel = [c for c in cells if c["scenario"] == sc]
        tbl.append(
            [sc]
            + [
                f"{np.mean([(mc(c, n).mean() - mc(c, 'no_switch').mean()) / c['T'] for c in sel]):+.4f}"
                for n in C2_NAMES
            ]
        )
    parts.append(
        "**C2 rho sweep on evaluation seeds** (cost per round minus no_switch; rho* was chosen on development seeds only)\n\n"
        + md_table(["scenario", *C2_NAMES], tbl)
    )
    tbl = []
    for sc in present:
        sel = [c for c in cells if c["scenario"] == sc]
        line = [sc]
        for cand in ("c1_hmm_cs", c2_name):
            vals, better, worse = [], 0, 0
            for c in sel:
                ref = min(
                    ("episode_geo", "episode_equal", "episode_front"), key=lambda k: mc(c, k).mean()
                )
                mean, lo, hi = paired_ci(mc(c, cand) - mc(c, ref))
                vals.append(mean / c["T"])
                better += hi < 0
                worse += lo > 0
            line += [f"{np.mean(vals):+.4f}", f"{better}/{worse}/{len(sel) - better - worse}"]
        tbl.append(line)
    parts.append(
        "**Candidates vs the best episode-composition baseline per cell** (the separable-composition null of the C2 candidate note; "
        "negative = candidate cheaper)\n\n"
        + md_table(
            [
                "scenario",
                "C1 diff/round",
                "C1 better/worse/ns",
                f"{c2_name} diff/round",
                "C2 better/worse/ns",
            ],
            tbl,
        )
    )
    tbl = []
    caps = (
        "episode_front",
        "episode_geo",
        "periodic_mean",
        "dal_restart",
        "pacing_bernoulli",
        "c1_hmm_cs",
        c2_name,
    )
    for sc in present:
        sel = [c for c in cells if c["scenario"] == sc]
        gaps = [(mc(c, "ref_regime_clairvoyant").mean() - mc(c, "no_switch").mean()) for c in sel]
        if np.mean(gaps) > -0.01 * sel[0]["T"]:
            continue
        line = [sc]
        for n in caps:
            frac = np.mean(
                [
                    (mc(c, n).mean() - mc(c, "no_switch").mean())
                    / (mc(c, "ref_regime_clairvoyant").mean() - mc(c, "no_switch").mean())
                    for c in sel
                ]
            )
            line.append(f"{frac:.2f}")
        tbl.append(line)
    parts.append(
        "**Fraction of the evaluator-only clairvoyant gain captured** (1 = matches a zero-query follower of the true better regime; "
        "negative = worse than never switching; scenarios where the clairvoyant gain is below 1% of T per round are omitted)\n\n"
        + md_table(["scenario", *caps], tbl)
    )
    return "\n\n".join(parts)


# ------------------------------------------------------------------ tiny oracle cells


def tiny_cell(task: tuple) -> dict:
    T, B, d, n_seeds = task
    from shiftlab.dive.causal_switching_game import CausalSwitchingGame, GameConfig
    from shiftlab.dive.delayed_regime_information import RegimeModel

    model = RegimeModel(F(1, 4), F(1, 4), F(1, 50), F(49, 50), F(1, 2))
    t0 = time.time()
    try:
        game = CausalSwitchingGame(
            GameConfig(
                horizon=T,
                budget=B,
                delay=d,
                alpha=F(1, 10),
                query_cost=F(1, 100),
                switch_cost=F(1, 10),
                max_nodes=3_000_000,
            ),
            model,
        )
        rep, _, _ = game.solve()
        oracle = {
            "raw_recovered_cost": float(F(rep["raw_recovered_cost"])),
            "raw_causal_null_risk": float(F(rep["raw_causal_null_risk"])),
            "continue_cost": float(F(rep["continue_cost"])),
            "seconds": round(time.time() - t0, 1),
        }
    except Exception as exc:  # noqa: BLE001 - solver limits are a reportable outcome
        oracle = {"error": f"{type(exc).__name__}: {exc}"}
    spec = bernoulli_grid_spec()
    cost = {"c": 0.01, "s": 0.1, "h": 0.1, "alpha": 0.1}
    res: dict[str, dict] = {}
    names = (*BASELINES, "c1_hmm_cs", *C2_NAMES)
    for name in names:
        alt, nul = [], []
        for seed in range(n_seeds):
            cfg = Config(T=T, B=B, d=d, seed=seed, **cost)
            rng = np.random.default_rng([seed, T, 5150])
            s_alt = make_bernoulli_stream(rng, T, (0.02, 0.98), a=0.25, b=0.25)
            r = run(s_alt, build_method(name, spec), cfg)
            alt.append((r.cost, r.queries, r.switches))
            rng = np.random.default_rng([seed, T, 5151])
            y = (rng.random(T) < 0.5).astype(float)  # causal-null boundary: iid P(Y=1) = 1/2
            s_nul = Stream(y, 1.0 - y)
            rn = run(s_nul, build_method(name, spec), cfg)
            nul.append(rn.promotions > 0)
        a = np.asarray(alt)
        mean, lo, hi = paired_ci(a[:, 0])
        p, plo, phi = wilson(int(np.sum(nul)), n_seeds)
        res[name] = {
            "cost_mean": mean,
            "cost_ci": [lo, hi],
            "queries": float(a[:, 1].mean()),
            "switches": float(a[:, 2].mean()),
            "null_promotion_freq": p,
            "null_promotion_ci": [plo, phi],
        }
    return {"T": T, "B": B, "d": d, "n_seeds": n_seeds, "oracle": oracle, "methods": res}


def tiny_markdown(cells: list[dict]) -> str:
    parts = []
    for c in cells:
        o = c["oracle"]
        head = f"**T={c['T']}, B={c['B']}, d={c['d']}** ({c['n_seeds']} paired seeds). "
        if "error" in o:
            head += f"Oracle failed: {o['error']}."
        else:
            head += (
                f"Oracle (HiGHS, numerical, risk {o['raw_causal_null_risk']:.3f} <= alpha 0.1): cost {o['raw_recovered_cost']:.4f}; "
                f"never switching: {o['continue_cost']:.4f}."
            )
        rows = []
        for k, v in c["methods"].items():
            gap = "" if "error" in o else f"{v['cost_mean'] - o['raw_recovered_cost']:+.4f}"
            rows.append(
                [
                    k,
                    f"{v['cost_mean']:.4f} [{v['cost_ci'][0]:.4f},{v['cost_ci'][1]:.4f}]",
                    gap,
                    f"{v['queries']:.2f}",
                    f"{v['switches']:.2f}",
                    f"{v['null_promotion_freq']:.3f} [{v['null_promotion_ci'][0]:.3f},{v['null_promotion_ci'][1]:.3f}]",
                ]
            )
        parts.append(
            head
            + "\n\n"
            + md_table(
                [
                    "method",
                    "MC cost [95% CI]",
                    "gap to oracle",
                    "queries",
                    "switches",
                    "null promotion freq (iid 1/2)",
                ],
                rows,
            )
        )
    return "\n\n".join(parts)


# ------------------------------------------------------------------ real data


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 22), b""):
            h.update(chunk)
    return h.hexdigest()


def _scale_losses(l0_train, l1_train, *arrs):
    scale = float(np.quantile(np.concatenate([l0_train, l1_train]), 0.99))
    scale = max(scale, 1e-12)
    return scale, [np.clip(a / scale, 0.0, 1.0) for a in arrs]


def load_elec2(t_cap: int) -> dict:
    import pandas as pd
    from scipy.io import arff
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    path = ROOT / "data/raw/elec2/electricity-normalized.arff"
    digest = sha256_file(path)
    recorded = "2d86fbc74c69a5c04bcede0119bce280dd6d8efa0115987edc75b77ccf024d7f2"
    ok = digest == recorded.replace("bcede", "bcde")  # audit doc has one stray character
    raw, _ = arff.loadarff(str(path))
    df = pd.DataFrame(raw)
    N = len(df)
    df = df.iloc[: int(0.8 * N)].reset_index(
        drop=True
    )  # rows after the 80% mark are dropped immediately
    y = (df["class"].str.decode("utf-8") == "UP").to_numpy().astype(int)
    df["day"] = df["day"].str.decode("utf-8").astype(int)
    X = df[
        ["day", "period", "nswprice", "nswdemand", "vicprice", "vicdemand", "transfer"]
    ].to_numpy(float)
    a, b, c = int(0.4 * N), int(0.5 * N), int(0.5 * N)
    sc = StandardScaler().fit(X[:a])
    f0 = LogisticRegression(max_iter=500).fit(sc.transform(X[:a]), y[:a])
    f1 = HistGradientBoostingClassifier(max_iter=100, max_depth=3, random_state=0).fit(X[:a], y[:a])

    def losses(lo, hi):
        l0 = (f0.predict(sc.transform(X[lo:hi])) != y[lo:hi]).astype(float)
        l1 = (f1.predict(X[lo:hi]) != y[lo:hi]).astype(float)
        return l0, l1

    cal0, cal1 = losses(a, b)
    T = min(t_cap, int(0.8 * N) - c)
    r0, r1 = losses(c, c + T)
    return {
        "name": "elec2",
        "loss0": r0,
        "loss1": r1,
        "calib_D": cal1 - cal0,
        "T": T,
        "meta": {
            "path": str(path.relative_to(ROOT)),
            "sha256": digest,
            "sha256_matches_audit_record": ok,
            "rows_total": N,
            "rows_loaded_for_use": len(df),
            "train_rows": [0, a],
            "calibration_rows": [a, b],
            "replay_rows": [c, c + T],
            "note": "file row order, not a verified clock; date/day-of-record not used as time; day-of-week kept as feature",
            "train_mean_loss": [
                float((f0.predict(sc.transform(X[:a])) != y[:a]).mean()),
                float((f1.predict(X[:a]) != y[:a]).mean()),
            ],
            "replay_mean_loss": [float(r0.mean()), float(r1.mean())],
            "loss_scale": 1.0,
        },
    }


def load_eia(t_cap: int) -> dict:
    import pyarrow.parquet as pq
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    ver = "066f854744aea721eae5"
    base = ROOT / "data/processed/eia" / ver
    manifest = json.loads((base / "dataset_manifest.json").read_text(encoding="utf-8"))
    digest = sha256_file(base / "observations.parquet")
    expected = manifest["files"]["observations.parquet"]
    if digest != expected:
        raise RuntimeError("EIA checksum mismatch")
    tbl = pq.read_table(
        base / "observations.parquet", columns=["event_time", "features", "target"]
    ).to_pandas()
    tbl = tbl.sort_values("event_time", kind="stable").reset_index(drop=True)
    N = len(tbl)
    tbl = tbl.iloc[: int(0.8 * N)]
    X = np.vstack(tbl["features"].to_numpy())
    y = tbl["target"].to_numpy(float)
    hour = (tbl["event_time"].to_numpy(float) // 3600) % 24
    Z = np.column_stack([X, np.sin(2 * np.pi * hour / 24), np.cos(2 * np.pi * hour / 24)])
    a, b = int(0.4 * N), int(0.5 * N)
    sc = StandardScaler().fit(Z[:a])
    f1 = Ridge(alpha=1.0).fit(sc.transform(Z[:a]), y[:a])

    def sq(lo, hi):
        return (X[lo:hi, 0] - y[lo:hi]) ** 2, (f1.predict(sc.transform(Z[lo:hi])) - y[lo:hi]) ** 2

    tr0, tr1 = sq(0, a)
    c0, c1 = sq(a, b)
    T = min(t_cap, int(0.8 * N) - b)
    r0, r1 = sq(b, b + T)
    s_, (c0, c1, r0, r1) = _scale_losses(tr0, tr1, c0, c1, r0, r1)
    return {
        "name": "eia_nyis",
        "loss0": r0,
        "loss1": r1,
        "calib_D": c1 - c0,
        "T": T,
        "meta": {
            "path": f"data/processed/eia/{ver}/observations.parquet",
            "sha256": digest,
            "sha256_matches_manifest": True,
            "rows_total": N,
            "rows_loaded_for_use": int(0.8 * N),
            "train_rows": [0, a],
            "calibration_rows": [a, b],
            "replay_rows": [b, b + T],
            "loss_scale_q99_train": s_,
            "replay_mean_loss": [float(r0.mean()), float(r1.mean())],
            "note": "hourly event time is not a publication time; persistence vs ridge",
        },
    }


CRSP_PERMNOS = [10107, 14593, 12490, 11850, 22111, 55976, 47896, 66181, 18163, 22592]


def load_crsp(t_cap: int) -> dict:
    import pyarrow.parquet as pq
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import StandardScaler

    ver = "5211412140dcb86f08f9"
    base = ROOT / "data/processed/crsp_ciz_next_day" / ver
    manifest = json.loads((base / "dataset_manifest.json").read_text(encoding="utf-8"))
    digest = sha256_file(base / "observations.parquet")
    if digest != manifest["files"]["observations.parquet"]:
        raise RuntimeError("CRSP checksum mismatch")
    tbl = pq.read_table(
        base / "observations.parquet",
        columns=["dlycaldt", "permno", "features", "target", "split"],
        filters=[("permno", "in", CRSP_PERMNOS), ("dlycaldt", "<", "2020-01-01")],
    ).to_pandas()
    tbl = tbl[tbl["split"] != "test"].dropna(subset=["target"])
    counts = tbl.groupby("permno").size()
    keep = [p for p in CRSP_PERMNOS if counts.get(p, 0) >= 4800]
    tbl = tbl[tbl["permno"].isin(keep)]
    dates = tbl.groupby("dlycaldt")["permno"].nunique()
    full = dates[dates == len(keep)].index
    tbl = (
        tbl[tbl["dlycaldt"].isin(full)]
        .sort_values(["dlycaldt", "permno"], kind="stable")
        .reset_index(drop=True)
    )
    X = np.vstack(tbl["features"].to_numpy())
    X = np.nan_to_num(X)
    y = tbl["target"].to_numpy(float)
    date_idx = tbl["dlycaldt"].factorize()[0]
    nd = int(date_idx.max()) + 1
    a_d, b_d = int(0.4 * nd), int(0.5 * nd)
    tr = date_idx < a_d
    sc = StandardScaler().fit(X[tr])
    f1 = Ridge(alpha=100.0).fit(sc.transform(X[tr]), y[tr])
    mean0 = float(y[tr].mean())
    se0 = (y - mean0) ** 2
    se1 = (f1.predict(sc.transform(X)) - y) ** 2
    cs0 = np.bincount(date_idx, weights=se0) / len(keep)
    cs1 = np.bincount(date_idx, weights=se1) / len(keep)
    scale, _ = _scale_losses(cs0[:a_d], cs1[:a_d])
    T = min(t_cap, nd - b_d)
    l0, l1 = (np.clip(cs0 / scale, 0, 1), np.clip(cs1 / scale, 0, 1))
    dates_sorted = tbl.drop_duplicates("dlycaldt")["dlycaldt"].to_list()
    return {
        "name": "crsp_subset",
        "loss0": l0[b_d : b_d + T],
        "loss1": l1[b_d : b_d + T],
        "calib_D": (l1 - l0)[a_d:b_d],
        "T": T,
        "meta": {
            "path": f"data/processed/crsp_ciz_next_day/{ver}/observations.parquet",
            "sha256": digest,
            "sha256_matches_manifest": True,
            "permnos_used": keep,
            "dates_used": nd,
            "train_dates": [dates_sorted[0], dates_sorted[a_d - 1]],
            "calibration_dates": [dates_sorted[a_d], dates_sorted[b_d - 1]],
            "replay_dates": [dates_sorted[b_d], dates_sorted[b_d + T - 1]],
            "loss_scale_q99_train": scale,
            "replay_mean_loss": [float(l0[b_d : b_d + T].mean()), float(l1[b_d : b_d + T].mean())],
            "note": "retrospective daily close ordering; only rows with dlycaldt < 2020-01-01 and split != test were read",
        },
    }


REAL_LOADERS = {"elec2": load_elec2, "eia_nyis": load_eia, "crsp_subset": load_crsp}
REAL_COSTS = ((0.005, 0.05), (0.02, 0.2))


def run_real_stream(payload: dict, rho: float) -> dict:
    T = payload["T"]
    stream = Stream(np.asarray(payload["loss0"]), np.asarray(payload["loss1"]))
    fit = fit_gaussian_hmm(np.asarray(payload["calib_D"])[:3000])
    spec = gaussian_grid_spec(fit)
    names = (*BASELINES, "c1_hmm_cs", f"c2_rho{rho:g}")
    rows = []
    for d in SYN_DS:
        for bf in SYN_BFRACS:
            B = round(bf * T)
            for c, s in REAL_COSTS:
                cfg = Config(T=T, B=B, d=d, c=c, s=s, h=0.0, alpha=0.1, seed=0)
                res = {n: run(stream, build_method(n, spec), cfg) for n in names}
                res["ref_always_f1"] = score_actions(
                    stream, cfg, np.ones(T, dtype=int), np.zeros(T)
                )
                best = min(BASELINES, key=lambda k: res[k].cost)
                safe = min(SAFE_BASELINES, key=lambda k: res[k].cost)
                contrasts = {}
                for cand in ("c1_hmm_cs", f"c2_rho{rho:g}"):
                    for lab, ref in (("best", best), ("best_safe", safe)):
                        dif = res[cand].per_round_cost - res[ref].per_round_cost
                        tot, lo, hi = block_bootstrap_ci(dif, block=50, reps=500, seed=1)
                        contrasts[f"{cand}|{lab}"] = {"ref": ref, "diff": tot, "ci": [lo, hi]}
                rows.append(
                    {
                        "stream": payload["name"],
                        "T": T,
                        "B": B,
                        "d": d,
                        "c": c,
                        "s": s,
                        "best_baseline": best,
                        "best_safe_baseline": safe,
                        "methods": {
                            n: {
                                "cost": r.cost,
                                "queries": r.queries,
                                "switches": r.switches,
                                "wasted": r.wasted_queries,
                            }
                            for n, r in res.items()
                        },
                        "contrasts": contrasts,
                    }
                )
    return {
        "stream": payload["name"],
        "meta": payload["meta"],
        "hmm_fit": fit,
        "bank_size": spec.size,
        "calib_D_mean": float(np.mean(payload["calib_D"])),
        "rows": rows,
    }


def real_markdown(blocks: list[dict], c2_name: str) -> str:
    parts = []
    for blk in blocks:
        m = blk["meta"]
        parts.append(
            f"**{blk['stream']}**: T={blk['rows'][0]['T']}, replay mean loss f0/f1 = "
            f"{m['replay_mean_loss'][0]:.4f}/{m['replay_mean_loss'][1]:.4f}; HMM fit "
            f"{{m0 {blk['hmm_fit']['m0']:+.3f}, m1 {blk['hmm_fit']['m1']:+.3f}, sigma {blk['hmm_fit']['sigma']:.3f}, "
            f"a {blk['hmm_fit']['a']:.3f}, b {blk['hmm_fit']['b']:.3f}}}; bank {blk['bank_size']} models."
        )
        tbl = []
        for r in blk["rows"]:
            ms = r["methods"]
            c1c = r["contrasts"]["c1_hmm_cs|best"]
            c2c = r["contrasts"][f"{c2_name}|best"]
            tbl.append(
                [
                    f"d={r['d']} B={r['B']} c={r['c']} s={r['s']}",
                    f"{ms['no_switch']['cost']:.1f}",
                    f"{ms['ref_always_f1']['cost']:.1f}",
                    f"{r['best_baseline']} {ms[r['best_baseline']]['cost']:.1f}",
                    f"{ms['c1_hmm_cs']['cost']:.1f} (q{ms['c1_hmm_cs']['queries']}/s{ms['c1_hmm_cs']['switches']})",
                    f"{c1c['diff']:+.1f} [{c1c['ci'][0]:+.1f},{c1c['ci'][1]:+.1f}]",
                    f"{ms[c2_name]['cost']:.1f} (q{ms[c2_name]['queries']}/s{ms[c2_name]['switches']})",
                    f"{c2c['diff']:+.1f} [{c2c['ci'][0]:+.1f},{c2c['ci'][1]:+.1f}]",
                ]
            )
        parts.append(
            md_table(
                [
                    "setting",
                    "no_switch",
                    "always_f1",
                    "best baseline",
                    "C1",
                    "C1 - best [block-boot 95%]",
                    "C2",
                    "C2 - best [block-boot 95%]",
                ],
                tbl,
            )
        )
    return "\n\n".join(parts)


# ------------------------------------------------------------------ main


def git_state() -> dict:
    def g(*a):
        return subprocess.run(
            ["git", *a], cwd=ROOT, capture_output=True, text=True, check=False
        ).stdout.strip()

    return {"head": g("rev-parse", "HEAD"), "dirty": bool(g("status", "--porcelain"))}


def write_summary(out: Path, results: dict) -> None:
    rho = results["config"]["rho_star"]
    rho_scores = results["config"]["rho_dev_scores"]
    c2_name = f"c2_rho{rho:g}"
    summary = results["synthetic_eval"]
    tiny = results["tiny_oracle"]
    real_blocks = results["real"]
    real_errors = results["real_dropped"]
    md = ["# Auto-generated exploratory tables (do not cite without the protocol)\n"]
    md.append(
        f"rho* (development) = {rho}; dev scores (mean (cost - no_switch)/T over dev cells): "
        + ", ".join(f"{k}: {v:+.4f}" for k, v in rho_scores.items())
    )
    md.append("## Synthetic (evaluation seeds)\n" + aggregate_markdown(summary["cells"], c2_name))
    md.append(
        "### Secondary descriptive tables\n"
        + extra_markdown(results["synthetic_eval_raw"], c2_name)
    )
    md.append("## Tiny cells vs exact two-law reference\n" + tiny_markdown(tiny))
    if real_blocks:
        md.append(
            "## Real development windows (imposed timing/costs)\n"
            + real_markdown(real_blocks, c2_name)
        )
    if real_errors:
        md.append("Dropped real streams: " + json.dumps(real_errors))
    (out / "summary.md").write_text("\n\n".join(md) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["smoke", "full"], default="smoke")
    ap.add_argument("--out", default="outputs/switching_c1_c2_exploratory_v1")
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--skip-real", action="store_true")
    ap.add_argument(
        "--resummarize",
        action="store_true",
        help="rebuild summary.md from an existing results.json",
    )
    args = ap.parse_args()
    smoke = args.mode == "smoke"
    out = ROOT / (args.out + ("_smoke" if smoke else ""))
    out.mkdir(parents=True, exist_ok=True)
    if args.resummarize:
        prev = json.loads((out / "results.json").read_text(encoding="utf-8"))
        write_summary(out, prev)
        return
    t_start = time.time()
    dev_seeds = DEV_SEEDS[:2] if smoke else DEV_SEEDS
    eval_seeds = EVAL_SEEDS[:3] if smoke else EVAL_SEEDS
    scen = tuple(SCENARIOS)[:3] if smoke else tuple(SCENARIOS)
    ts = (200,) if smoke else SYN_TS
    tiny_cfgs = [(6, 3, 1), (6, 3, 2)] if smoke else [(6, 3, 1), (6, 3, 2), (7, 3, 2), (8, 4, 2)]
    n_tiny = 100 if smoke else 5000
    t_cap = 300 if smoke else 3000

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        tiny_f = [pool.submit(tiny_cell, (*c, n_tiny)) for c in tiny_cfgs]
        dev_f = [pool.submit(run_cell, t) for t in cell_tasks(dev_seeds, SYN_METHODS, scen, ts)]
        eval_f = [pool.submit(run_cell, t) for t in cell_tasks(eval_seeds, SYN_METHODS, scen, ts)]
        dev_cells = [f.result() for f in dev_f]
        rho, rho_scores = select_rho(dev_cells)
        c2_name = f"c2_rho{rho:g}"
        print(f"[dev] rho* = {rho} scores {rho_scores}", flush=True)
        eval_cells = [f.result() for f in eval_f]
        tiny = [f.result() for f in tiny_f]
    print(f"[synthetic+tiny done] {time.time() - t_start:.0f}s", flush=True)

    summary = summarize_cells(eval_cells, c2_name)
    dev_summary = summarize_cells(dev_cells, c2_name)

    real_blocks, real_errors = [], {}
    if not args.skip_real:
        for name, loader in REAL_LOADERS.items():
            try:
                payload = loader(t_cap)
                real_blocks.append(run_real_stream(payload, rho))
                print(f"[real] {name} ok T={payload['T']}", flush=True)
            except Exception as exc:  # noqa: BLE001 - dataset dropped, reason recorded
                real_errors[name] = f"{type(exc).__name__}: {exc}"
                print(f"[real] {name} DROPPED: {real_errors[name]}", flush=True)

    sources = {
        f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest()
        for f in SOURCE_FILES
        if (ROOT / f).exists()
    }
    results = {
        "status": "EXPLORATORY_development_only_no_claims",
        "mode": args.mode,
        "git": git_state(),
        "source_sha256": sources,
        "config": {
            "dev_seeds": list(dev_seeds),
            "eval_seeds": list(eval_seeds),
            "scenarios": list(scen),
            "scenario_params": {
                k: {kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in v.items()}
                for k, v in SCENARIOS.items()
            },
            "T": list(ts),
            "B_fracs": list(SYN_BFRACS),
            "d": list(SYN_DS),
            "costs": SYN_COST,
            "c2_rhos": list(C2_RHOS),
            "rho_star": rho,
            "rho_dev_scores": rho_scores,
            "tiny_cells": tiny_cfgs,
            "tiny_seeds": n_tiny,
            "real_T_cap": t_cap,
            "real_costs": REAL_COSTS,
            "crsp_permnos": CRSP_PERMNOS,
        },
        "synthetic_eval": summary,
        "synthetic_eval_raw": eval_cells,
        "synthetic_dev": dev_summary,
        "tiny_oracle": tiny,
        "real": real_blocks,
        "real_dropped": real_errors,
        "elapsed_seconds": time.time() - t_start,
    }
    (out / "results.json").write_text(
        json.dumps(results, indent=1, default=float) + "\n", encoding="utf-8"
    )

    write_summary(out, results)
    print(f"done in {time.time() - t_start:.0f}s -> {out.name}", flush=True)


if __name__ == "__main__":
    main()
