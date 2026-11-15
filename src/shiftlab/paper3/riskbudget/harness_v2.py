"""F3 v2 comparison harness (spec 03F section 6): arms, tuning space, per-tape runners.

v1 arm definitions in ``harness.py`` are untouched; this module adds the ``f3v2`` arm type and
the v2 arm list. Frozen tuned configs are read from ``outputs/paper3/riskbudget/tuning_v2``.
"""

from __future__ import annotations

import copy
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from ..joint.harness import STOPS, make_policy
from ..simulation import (
    SimulationEvaluator,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
)
from .harness import FIELDS, ROOT, all_regimes, make_arm, tuned
from .metrics import harm_summary
from .shield_v2 import RiskBudgetShieldV2

T_DEFAULT = 300
RS_V2 = (8, 10, 12, 15, 20, 30, 45)
TUNE_DIR = ROOT / "outputs" / "paper3" / "riskbudget" / "tuning_v2"
DELTA = 0.05
FIELDS_V2 = FIELDS + ("n_blind", "n_sampled", "n_pi1", "mean_pi")
DIAG = (
    "n_forced_rollbacks",
    "n_vetoed_promotions",
    "rode_out",
    "I_max",
    "n_blind",
    "n_sampled",
    "n_pi1",
    "mean_pi",
)


# ------------------------------------------------------------------------------------------
# configs
# ------------------------------------------------------------------------------------------
def _wald(lam, gamma, stop) -> dict:
    return {
        "kind": "wald",
        "params": {"lam": lam, "gamma": gamma, "acq": "paced", "stop": stop},
        "name": "wald_cut",
    }


def default_v2_config() -> dict:
    """Config 0: tuned wald_cut inner + documented shield defaults."""
    p = tuned("wald_cut")["params"]
    return {
        "inner": {"lam": p["lam"], "gamma": p["gamma"], "stop": p["stop"]},
        "shield": {
            "label_reserve_frac": 0.25,
            "pi_min": 0.5,
            "blind_margin": None,
            "default_window": 10,
        },
    }


def default_v1_config() -> dict:
    p = tuned("wald_cut")["params"]
    return {
        "inner": {"lam": p["lam"], "gamma": p["gamma"], "stop": p["stop"]},
        "shield": {"label_reserve_frac": 0.25},
    }


def sample_v2_configs(n: int, seed: int = 0) -> list[dict]:
    r = np.random.default_rng([seed, sum(map(ord, "f3v2"))])
    cfgs = [default_v2_config()]
    for _ in range(n - 1):
        cfgs.append(
            {
                "inner": {
                    "lam": float(r.uniform(0.9, 0.999)),
                    "gamma": float(r.uniform(0.05, 0.5)),
                    "stop": STOPS[int(r.integers(len(STOPS)))],
                },
                "shield": {
                    "label_reserve_frac": float(r.uniform(0.0, 0.5)),
                    "pi_min": [0.25, 0.5, 1.0][int(r.integers(3))],
                    "blind_margin": [None, 4.0, 8.0, 16.0][int(r.integers(4))],
                    "default_window": [5, 10, 20][int(r.integers(3))],
                },
            }
        )
    return cfgs


def sample_v1_configs(n: int, seed: int = 0) -> list[dict]:
    r = np.random.default_rng([seed, sum(map(ord, "f3v1"))])
    cfgs = [default_v1_config()]
    for _ in range(n - 1):
        cfgs.append(
            {
                "inner": {
                    "lam": float(r.uniform(0.9, 0.999)),
                    "gamma": float(r.uniform(0.05, 0.5)),
                    "stop": STOPS[int(r.integers(len(STOPS)))],
                },
                "shield": {"label_reserve_frac": float(r.uniform(0.0, 0.5))},
            }
        )
    return cfgs


def v2_arm(cfg: dict, R: float, name: str, **shield_override) -> dict:
    sh = {"delta": DELTA, **cfg["shield"], **shield_override}
    i = cfg["inner"]
    return {
        "name": name,
        "type": "f3v2",
        "inner": _wald(i["lam"], i["gamma"], i["stop"]),
        "R": R,
        "shield": sh,
    }


def v1_arm(cfg: dict, R: float, name: str) -> dict:
    i = cfg["inner"]
    return {
        "name": name,
        "type": "f3",
        "inner": _wald(i["lam"], i["gamma"], i["stop"]),
        "R": R,
        "shield": {"pi_menu": (1.0,), "delta": 0.0, **cfg["shield"]},
    }


def load_tuned(name: str) -> dict:
    d = json.loads((TUNE_DIR / f"{name}.json").read_text())
    return d["configs"][d["best"]]


# ------------------------------------------------------------------------------------------
# arms
# ------------------------------------------------------------------------------------------
def build_arms_v2() -> list[dict]:
    wc = tuned("wald_cut")
    arms = [{"name": "never", "type": "policy", "policy": {"kind": "never"}}]
    for n in ("wald_cut", "cusum", "gate_wald"):
        arms.append({"name": n, "type": "policy", "policy": tuned(n)})
    for h in (2, 4, 8):
        arms.append({"name": f"cusum_rb_h{h}", "type": "cusum_rb", "inner": wc, "h": float(h)})
    for R in (8, 12, 20, 30):
        arms.append({"name": f"stoploss_R{R}", "type": "stoploss", "inner": wc, "R": R})
    c1, c2d = default_v1_config(), default_v2_config()
    for R in (8, 12, 20, 30):
        arms.append(v1_arm(c1, R, f"f3_pi1_R{R}"))
    c1t = load_tuned("f3v1_tuned")
    for R in (8, 12, 20, 30):
        arms.append(v1_arm(c1t, R, f"f3v1t_R{R}"))
    for R in (8, 12, 20, 30):
        arms.append(v2_arm(c2d, R, f"f3v2d_R{R}"))
    c2 = load_tuned("f3v2")
    for R in RS_V2:
        arms.append(v2_arm(c2, R, f"f3v2_R{R}"))
    # ablations at R=20 on the tuned config (c2) and on the sampling default (c2d)
    for tag, cfg in (("f3v2_R20", c2), ("f3v2d_R20", c2d)):
        arms.append(v2_arm(cfg, 20, f"{tag}_pi1fixed", paced=False, pi_min=1.0))
        arms.append(v2_arm(cfg, 20, f"{tag}_noride", ride_out=False))
        if cfg["shield"]["blind_margin"] is None:
            arms.append(v2_arm(cfg, 20, f"{tag}_blind8", blind_margin=8.0))
        else:
            arms.append(v2_arm(cfg, 20, f"{tag}_noblind", blind_margin=None))
        for pm in (0.25, 0.5):
            if pm != cfg["shield"]["pi_min"]:
                arms.append(v2_arm(cfg, 20, f"{tag}_pimin{pm:g}", pi_min=pm))
    return arms


def make_arm_v2(spec: dict, T: int):
    if spec["type"] == "f3v2":
        inner = make_policy(spec["inner"], T)
        return RiskBudgetShieldV2(inner, spec["R"], **spec["shield"], name=spec["name"])
    return make_arm(spec, T)


# ------------------------------------------------------------------------------------------
# dev_v2 runner (all 30 regimes, many seeds)
# ------------------------------------------------------------------------------------------
_REG = None
_ARMS = None


def _init():
    global _REG, _ARMS
    _REG, _ARMS = all_regimes(), build_arms_v2()


def _task(args):
    rid, seed, T = args
    reg = _REG[rid]
    tape, truth = generate_tape(reg, seed, T)
    spec = make_spec(reg, T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    rows = []
    for arm in _ARMS:
        pol = make_arm_v2(arm, T)
        rec = run_policy(pol, tape, spec, seed)
        e = ev.evaluate(rec)
        row = {k: float(e[k]) for k in FIELDS if k in e}
        row.update(harm_summary(tape, rec, spec.costs.k))
        row["frac_time_deployed"] = float(np.mean(rec.a))
        for k in DIAG:
            if hasattr(pol, k):
                row[k] = float(getattr(pol, k))
        rows.append(row)
    return rid, seed, rows


def run_regimes_v2(tag_dir: Path, seed_list, workers=8, T=T_DEFAULT, log=print, regimes=None):
    tag_dir.mkdir(parents=True, exist_ok=True)
    arms = build_arms_v2()
    names = [a["name"] for a in arms]
    (tag_dir / "_arms.spec").write_text(json.dumps(arms, default=float, indent=1))
    rids = list(regimes or all_regimes().keys())
    t0 = time.time()
    with Pool(workers, initializer=_init) as pool:
        for rid in rids:
            path = tag_dir / f"{rid}.json"
            if path.exists():
                log(f"skip {rid} (exists)")
                continue
            res = {}
            for _, s, rows in pool.imap_unordered(
                _task, [(rid, s, T) for s in seed_list], chunksize=2
            ):
                res[s] = rows
            fields = {}
            for f in FIELDS_V2 + ("sup_harm", "final_harm"):
                if f in fields:
                    continue
                fields[f] = [[res[s][i].get(f) for s in seed_list] for i in range(len(names))]
            out = {"regime": rid, "seeds": list(seed_list), "arms": names, "fields": fields}
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(out))
            tmp.rename(path)
            log(f"done {rid}  elapsed {time.time() - t0:.0f}s")
    return time.time() - t0


# ------------------------------------------------------------------------------------------
# tuning runner (24 original regimes, tuning seeds): arms are (spec) dicts
# ------------------------------------------------------------------------------------------
_TREG = None
_TARMS = None


def _tinit(arms):
    global _TREG, _TARMS
    _TREG, _TARMS = load_regimes(), arms


def _ttask(args):
    rid, seed, T = args
    reg = _TREG[rid]
    tape, truth = generate_tape(reg, seed, T)
    spec = make_spec(reg, T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    out = []
    for arm in _TARMS:
        t0 = time.time()
        pol = make_arm_v2(arm, T)
        rec = run_policy(pol, tape, spec, seed)
        e = ev.evaluate(rec)
        hs = harm_summary(tape, rec, spec.costs.k)
        out.append(
            {
                "J": float(e["J"]),
                "J_never": float(e["J_never"]),
                "n_queries": float(e["n_queries"]),
                "sup_harm": hs["sup_harm"],
                "n_sampled": float(getattr(pol, "n_sampled", 0)),
                "sec": time.time() - t0,
            }
        )
    return rid, seed, out


def tune_arms(arms, rids, seed_list, workers=8, T=T_DEFAULT, log=print):
    """-> dict of arrays (n_arm, n_regime, n_seed) for J, J_never, n_queries, sup_harm, sec."""
    keys = ("J", "J_never", "n_queries", "sup_harm", "n_sampled", "sec")
    ri, si = {r: i for i, r in enumerate(rids)}, {s: i for i, s in enumerate(seed_list)}
    A = {k: np.full((len(arms), len(rids), len(seed_list)), np.nan) for k in keys}
    tasks = [(r, s, T) for r in rids for s in seed_list]
    t0 = time.time()
    with Pool(workers, initializer=_tinit, initargs=(arms,)) as pool:
        for n, (rid, s, out) in enumerate(pool.imap_unordered(_ttask, tasks, chunksize=1)):
            for i, row in enumerate(out):
                for k in keys:
                    A[k][i, ri[rid], si[s]] = row[k]
            if (n + 1) % max(len(tasks) // 6, 1) == 0:
                log(f"  {n + 1}/{len(tasks)} tapes, {time.time() - t0:.0f}s")
    return A


def tuning_score(A) -> np.ndarray:
    """Mean over regimes of mean-J / mean-J_never per arm (same objective as the baselines)."""
    return (A["J"].mean(2) / A["J_never"][0].mean(1)[None, :]).mean(1)


def deep(x):
    return copy.deepcopy(x)
