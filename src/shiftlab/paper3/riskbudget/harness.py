"""F3 comparison harness (spec 03F section 5): arm specs, per-tape runner, per-regime checkpoints."""

from __future__ import annotations

import copy
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from ..baselines import AlwaysChallenger
from ..joint.harness import make_policy
from ..simulation import (
    CONFIG_DIR,
    SimulationEvaluator,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
)
from .comparators import CusumRollback, StopLossPlugin
from .metrics import harm_summary
from .shield import RiskBudgetShield

T_DEFAULT = 300
RS = (8, 10, 12, 15, 20, 30)
ROOT = Path(__file__).resolve().parents[4]
TUNING = ROOT / "outputs" / "paper3" / "joint" / "tuning"
STRESS_CFG = CONFIG_DIR / "regimes_f3_v1.json"


def tuned(name: str) -> dict:
    spec = json.loads((TUNING / f"{name}.json").read_text())["best_spec"]
    return {"kind": spec["kind"], "params": dict(spec["params"]), "name": name}


def _with(spec: dict, **params) -> dict:
    s = copy.deepcopy(spec)
    s["params"].update(params)
    return s


def all_regimes() -> dict:
    regs = dict(load_regimes())
    stress = load_regimes(str(STRESS_CFG))
    regs.update(stress)
    return regs


def stress_ids() -> list[str]:
    return list(load_regimes(str(STRESS_CFG)).keys())


PI = {
    "f3_pi1": {"pi_menu": (1.0,), "delta": 0.0},
    "f3_pi50": {"pi_menu": (0.5, 1.0), "delta": 0.05, "margin": 2.0},
    "f3_pi25": {"pi_menu": (0.25, 1.0), "delta": 0.05, "margin": 2.0},
}


def build_arms() -> list[dict]:
    wc = tuned("wald_cut")
    arms = [{"name": "never", "type": "policy", "policy": {"kind": "never"}}]
    for n in ("wald_cut", "wald_paced", "cusum", "gate_wald"):
        arms.append({"name": n, "type": "policy", "policy": tuned(n)})
    for g in (0.02, 0.05, 0.1, 0.2):
        arms.append({"name": f"wald_cut_g{g:g}", "type": "policy", "policy": _with(wc, gamma=g)})
    for h in (2, 4, 8, 12):
        arms.append(
            {"name": f"cusum_h{h}", "type": "policy", "policy": _with(tuned("cusum"), h=float(h))}
        )
    for a in (0.01, 0.05, 0.1, 0.2):
        arms.append(
            {"name": f"gate_a{a:g}", "type": "policy", "policy": _with(tuned("gate_wald"), alpha=a)}
        )
    for h in (2, 4, 8):
        arms.append({"name": f"cusum_rb_h{h}", "type": "cusum_rb", "inner": wc, "h": float(h)})
    for R in RS:
        arms.append({"name": f"stoploss_R{R}", "type": "stoploss", "inner": wc, "R": R})
    for var, kw in PI.items():
        for R in RS:
            arms.append(
                {"name": f"{var}_R{R}", "type": "f3", "inner": wc, "R": R, "shield": dict(kw)}
            )
    for R in (12, 20):
        arms.append(
            {
                "name": f"f3_always_R{R}",
                "type": "f3",
                "inner": {"kind": "always"},
                "R": R,
                "shield": dict(PI["f3_pi1"]),
            }
        )
    abl = {
        "nopending": ("f3_pi1", {"use_pending_reserve": False}),
        "norollback": ("f3_pi1", {"use_rollback_reserve": False}),
        "noride": ("f3_pi1", {"ride_out": False}),
        "nolabelres": ("f3_pi1", {"label_reserve_frac": 0.0}),
        "noconf": ("f3_pi25", {"use_conf_width": False}),
    }
    for tag, (var, extra) in abl.items():
        arms.append(
            {
                "name": f"{var}_R12_{tag}",
                "type": "f3",
                "inner": wc,
                "R": 12,
                "shield": {**PI[var], **extra},
            }
        )
    return arms


def make_arm(spec: dict, T: int):
    ty = spec["type"]
    if ty == "policy":
        return make_policy(spec["policy"], T)
    inner_spec = spec["inner"]
    inner = AlwaysChallenger() if inner_spec["kind"] == "always" else make_policy(inner_spec, T)
    if ty == "cusum_rb":
        return CusumRollback(inner, spec["h"])
    if ty == "stoploss":
        return StopLossPlugin(inner, spec["R"])
    if ty == "f3":
        return RiskBudgetShield(inner, spec["R"], **spec["shield"], name=spec["name"])
    raise ValueError(ty)


FIELDS = (
    "J",
    "J_never",
    "n_queries",
    "n_switches",
    "sup_harm",
    "final_harm",
    "max_drawdown_vs_never",
    "global_null_false_promotion",
    "frac_time_deployed",
    "n_forced_rollbacks",
    "n_vetoed_promotions",
    "rode_out",
    "I_max",
)
_REG = None
_ARMS = None


def _init():
    global _REG, _ARMS
    _REG, _ARMS = all_regimes(), build_arms()


def _task(args):
    rid, seed, T = args
    reg = _REG[rid]
    tape, truth = generate_tape(reg, seed, T)
    spec = make_spec(reg, T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    rows = []
    for arm in _ARMS:
        pol = make_arm(arm, T)
        rec = run_policy(pol, tape, spec, seed)
        e = ev.evaluate(rec)
        row = {k: float(e[k]) for k in FIELDS if k in e}
        row.update(harm_summary(tape, rec, spec.costs.k))
        row["frac_time_deployed"] = float(np.mean(rec.a))
        for k in ("n_forced_rollbacks", "n_vetoed_promotions", "rode_out", "I_max"):
            if hasattr(pol, k):
                row[k] = float(getattr(pol, k))
        rows.append(row)
    return rid, seed, rows


def run_regimes(tag_dir: Path, seed_list, workers=8, T=T_DEFAULT, log=print, regimes=None):
    tag_dir.mkdir(parents=True, exist_ok=True)
    arms = build_arms()
    names = [a["name"] for a in arms]
    rids = list(regimes or all_regimes().keys())
    t0 = time.time()
    with Pool(workers, initializer=_init) as pool:
        for rid in rids:
            path = tag_dir / f"{rid}.json"
            if path.exists():
                log(f"skip {rid} (exists)")
                continue
            tasks = [(rid, s, T) for s in seed_list]
            res = {}
            for _, s, rows in pool.imap_unordered(_task, tasks, chunksize=2):
                res[s] = rows
            fields = {}
            for f in FIELDS + ("sup_harm",):
                if f in fields:
                    continue
                fields[f] = [[res[s][i].get(f) for s in seed_list] for i in range(len(names))]
            out = {"regime": rid, "seeds": list(seed_list), "arms": names, "fields": fields}
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(out))
            tmp.rename(path)
            log(f"done {rid}  elapsed {time.time() - t0:.0f}s")
    return time.time() - t0


def load_results(tag_dir: Path):
    """-> (arm names, regime ids, seeds, {field: array (arm, regime, seed) with NaN for missing})"""
    files = {}
    for p in sorted(tag_dir.glob("*.json")):
        d = json.loads(p.read_text())
        files[d["regime"]] = d
    order = [r for r in all_regimes() if r in files]
    d0 = files[order[0]]
    arrs = {
        f: np.array(
            [
                [[np.nan if v is None else v for v in row] for row in files[r]["fields"][f]]
                for r in order
            ],
            float,
        ).transpose(1, 0, 2)
        for f in d0["fields"]
    }
    return d0["arms"], order, d0["seeds"], arrs
