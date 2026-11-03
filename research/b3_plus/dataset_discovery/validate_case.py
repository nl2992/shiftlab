"""Phase 8 lightweight validation of a SUCCESS case. Never re-selects the model pair.

The pair is re-derived deterministically from rows [0, 60%) by the same ``select_pair`` call the
screening used, so reproducing it is itself the first validation check. The locked-window losses
are cached, then re-evaluated under (a) the registered seeds, (b) a disjoint seed batch, and
(c) sensitivity configurations. The registry and the screening status files are never written.

    uv run python research/b3_plus/dataset_discovery/validate_case.py openml_ldpa uci_occupancy
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[2] / "scripts/promising_directions"))

import construct_model_pairs as cmp  # noqa: E402
import dataset_sources as ds  # noqa: E402
import registry as reg  # noqa: E402
import screen_candidate as sc  # noqa: E402
import validate_stream as vs  # noqa: E402

import b3_plus_experiments as exp  # noqa: E402
from b3_plus_policy import run_plus_policies  # noqa: E402

base = exp.base
b1 = base.b1
T_EP = sc.T_EP
VARIANTS = ("P0", "P1", "P2", "P3b", "P6", "P7s")


def prepare(dataset_id: str, cache: Path) -> dict:
    """Locked-window per-episode losses for the frozen pair. Cached after the first call."""
    meta_p = cache / f"{dataset_id}_meta.json"
    npz_p = cache / f"{dataset_id}_losses.npz"
    if npz_p.exists() and meta_p.exists():
        z = np.load(npz_p)
        return {**json.loads(meta_p.read_text()), "starts": z["starts"], "l0": z["l0"], "l1": z["l1"]}
    registry = reg.load(reg.REGISTRY_PATH)
    entry = reg.get(registry, dataset_id)
    delay = reg.declared_delay(entry)
    raw = ds.load(dataset_id, openml_did=entry.get("openml_did"), opts=entry.get("load_options"))
    report = vs.validate(raw, entry)
    order = report.pop("_order", None)
    if not report["ok"]:
        raise RuntimeError(f"{dataset_id} no longer validates: {report['reason']}")
    n = raw.n
    w = cmp.windows(n)
    y_all = np.asarray(raw.y)[order]
    x_all = vs.take(raw.X, order)
    y01, _ = cmp.binarise(y_all, w["n30"])
    x60 = x_all[: w["n60"]] if isinstance(x_all, np.ndarray) else x_all.iloc[: w["n60"]]
    sel = cmp.select_pair(x60, y01[: w["n60"]], w, T_EP, sc.CS)
    if not sel["passes_headroom"]:
        raise RuntimeError(f"{dataset_id} pair no longer passes the dev precheck")
    starts = cmp.episode_starts(n)
    eps = cmp.locked_episode_losses(sel, x_all, y01, starts, T_EP)
    l0 = np.stack([e[1] for e in eps]).astype(np.int8)
    l1 = np.stack([e[2] for e in eps]).astype(np.int8)
    meta = {
        "dataset_id": dataset_id,
        "delay": int(delay),
        "base_err": float(sel["inc_err_dev"]),
        "chosen_pair": sel["chosen"],
        "inc_err_dev": float(sel["inc_err_dev"]),
        "n": int(n),
        "K": int(len(starts)),
    }
    cache.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(npz_p, starts=np.asarray(starts), l0=l0, l1=l1)
    meta_p.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {**meta, "starts": np.asarray(starts), "l0": l0, "l1": l1}


def evaluate(prep: dict, *, seed_base: int, n_seeds: int, budget: int, cs: float, cq: float) -> dict:
    """Per-episode stats for every variant under one configuration."""
    p = b1.Params(T=T_EP, delay=prep["delay"], base_err=prep["base_err"], eps=0.05)
    rows, checks = [], {"max_queries": 0, "min_promo_time": np.inf, "budget": budget}
    for i in range(prep["K"]):
        l0, l1 = prep["l0"][i], prep["l1"][i]
        u = np.stack(
            [
                np.random.default_rng(np.random.SeedSequence([seed_base, i, j])).random(T_EP)
                for j in range(n_seeds)
            ],
            axis=1,
        )
        res = base.run_baselines(l0, l1, u, budget, cs, cq, p, sc.BASE_NAMES)
        a0 = np.repeat(np.asarray(l0, dtype=np.int8)[:, None], n_seeds, axis=1)
        a1 = np.repeat(np.asarray(l1, dtype=np.int8)[:, None], n_seeds, axis=1)
        out = run_plus_policies(a0, a1, u, budget, cs, cq, p, [exp._plus_params("P7s")])
        res["P7s"] = out["P7s"]
        row = {}
        for v in VARIANTS:
            s = exp.summarise_variant(res[v], cq, cs)
            row[v] = s
            checks["max_queries"] = max(checks["max_queries"], int(np.max(res[v]["queries"])))
            tp = np.asarray(res[v]["t_prom"], dtype=float)
            if np.isfinite(tp).any():
                checks["min_promo_time"] = min(checks["min_promo_time"], float(np.nanmin(tp)))
        rows.append(row)
    checks["budget_respected"] = checks["max_queries"] <= budget
    checks["promotion_after_first_release"] = (
        not np.isfinite(checks["min_promo_time"]) or checks["min_promo_time"] >= prep["delay"]
    )
    if not np.isfinite(checks["min_promo_time"]):
        checks["min_promo_time"] = None
    return {"rows": rows, "checks": checks}


def paired(ev: dict, K: int, ref: str = "P3b", seed: int = 3) -> dict:
    rng = np.random.default_rng(seed)
    mc = {v: np.array([r[v]["mean_cost"] for r in ev["rows"]]) for v in VARIANTS}
    lab = {v: np.array([r[v]["mean_labels"] for r in ev["rows"]]) for v in VARIANTS}
    if K >= 5:
        lvl = "episode"
        D = {v: mc[v] - mc[ref] for v in VARIANTS}
    else:
        lvl = "seed"
        cs_ = {v: np.array([r[v]["cost_seeds"] for r in ev["rows"]]).mean(0) for v in VARIANTS}
        D = {v: cs_[v] - cs_[ref] for v in VARIANTS}
    out = {"bootstrap_level": lvl, "low_power": K < 5, "K": K, "variants": {}}
    for v in VARIANTS:
        d = D[v]
        idx = rng.integers(0, len(d), (2000, len(d)))
        m = d[idx].mean(1)
        out["variants"][v] = {
            "mean_cost": float(mc[v].mean()),
            "mean_labels": float(lab[v].mean()),
            f"vs_{ref}": float(d.mean()),
            "ci": [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))],
            "per_episode_diff": [round(float(x), 4) for x in (mc[v] - mc[ref])],
        }
    return out


CONFIGS = {
    "V0_registered_seeds": dict(seed_base=20261101, budget=200, cs=5.0, cq=0.05),
    "V1_disjoint_seeds": dict(seed_base=20261103, budget=200, cs=5.0, cq=0.05),
    "V2_switch_cost_20": dict(seed_base=20261101, budget=200, cs=20.0, cq=0.05),
    "V3_budget_400": dict(seed_base=20261101, budget=400, cs=5.0, cq=0.05),
}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("datasets", nargs="+")
    ap.add_argument("--n-seeds", type=int, default=100)
    ap.add_argument("--configs", default=",".join(CONFIGS))
    a = ap.parse_args(argv)
    cache = reg.OUT_ROOT.parent / "_validation_cache"
    for dsid in a.datasets:
        prep = prepare(dsid, cache)
        outd = reg.OUT_ROOT / dsid / "validation"
        outd.mkdir(parents=True, exist_ok=True)
        allr = {"dataset_id": dsid, "delay": prep["delay"], "K": prep["K"],
                "chosen_pair": prep["chosen_pair"], "n_seeds": a.n_seeds, "configs": {}}
        print(f"\n######## {dsid}  K={prep['K']}  delay={prep['delay']}  pair={prep['chosen_pair']}")
        for name in a.configs.split(","):
            ev = evaluate(prep, n_seeds=a.n_seeds, **CONFIGS[name])
            res = paired(ev, prep["K"])
            res["checks"] = ev["checks"]
            res["config"] = CONFIGS[name]
            allr["configs"][name] = res
            w = res["variants"]
            flag = "WIN " if w["P7s"]["ci"][1] < 0 else ("LOSS" if w["P7s"]["ci"][0] > 0 else "  = ")
            print(f"  {name:22s} P0={w['P0']['mean_cost']:8.2f} P3b={w['P3b']['mean_cost']:8.2f} "
                  f"P6={w['P6']['mean_cost']:8.2f} P7s={w['P7s']['mean_cost']:8.2f} "
                  f"lab {w['P3b']['mean_labels']:6.1f}->{w['P7s']['mean_labels']:6.1f} "
                  f"vsP3b={w['P7s']['vs_P3b']:+7.3f} "
                  f"[{w['P7s']['ci'][0]:+7.3f},{w['P7s']['ci'][1]:+7.3f}] {flag} "
                  f"budget_ok={ev['checks']['budget_respected']}")
        (outd / "validation.json").write_text(json.dumps(allr, indent=2), encoding="utf-8")
        print(f"  -> {outd / 'validation.json'}")


if __name__ == "__main__":
    main()
