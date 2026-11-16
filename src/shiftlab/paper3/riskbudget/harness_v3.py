"""F3 v3 (spec 03F section 7): label-scarce family, candidates, arm lists, per-family runner.

v3 is RiskBudgetShieldV2 with a lower pacing floor and a mixture grid extended to V = 4096; the
validity argument of 03F 6.1-6.3 is unchanged. New code only; v1/v2 files are untouched.
"""

from __future__ import annotations

import copy
import itertools
import json
import time
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from ..simulation import (
    CONFIG_DIR,
    SimulationEvaluator,
    generate_tape,
    load_regimes,
    make_spec,
    run_policy,
)
from .harness import ROOT, all_regimes
from .harness_v2 import DIAG, FIELDS_V2, make_arm_v2
from .metrics import harm_summary

SCARCE_CFG = CONFIG_DIR / "regimes_f3_scarce_v1.json"
FROZEN_V3 = CONFIG_DIR / "f3_v3_frozen.json"
ARMS_FILE = CONFIG_DIR / "f3_confirmation_arms_v1.json"
T_SC, K_SC = 2000, 5.0
V_TARGETS_V3 = (4.0, 16.0, 64.0, 256.0, 1024.0, 4096.0)
HS_SEL = (50,)
OUT = ROOT / "outputs" / "paper3" / "riskbudget"
FIELDS_OUT = FIELDS_V2 + ("sup_harm", "final_harm")


def scarce_regimes() -> dict:
    return load_regimes(str(SCARCE_CFG))


def R_of(h: float, k: float = K_SC) -> float:
    return 2 * k + h


def _src() -> dict:
    return {a["name"]: a for a in json.loads(ARMS_FILE.read_text())["arms"]}


# ------------------------------------------------------------------------------------------
# v3 specs
# ------------------------------------------------------------------------------------------
def candidate_grid() -> list[dict]:
    """The 12 shield-parameter candidates of section 7 (shield kwargs, without R / window)."""
    out = []
    for pm, lr, bm in itertools.product((0.05, 0.1, 0.25), (0.1, 0.25), (None, 8.0)):
        out.append(
            {
                "pi_min": pm,
                "label_reserve_frac": lr,
                "blind_margin": bm,
                "v_targets": list(V_TARGETS_V3),
                "delta": 0.05,
                "paced": True,
                "ride_out": True,
            }
        )
    return out


def cand_name(c: dict) -> str:
    bm = "none" if c["blind_margin"] is None else f"{c['blind_margin']:g}"
    return f"v3c_pm{c['pi_min']:g}_lr{c['label_reserve_frac']:g}_bm{bm}"


def v3_arm(shield: dict, R: float, name: str) -> dict:
    inner = _src()["wald_cut"]["policy"]
    return {"name": name, "type": "f3v2", "inner": inner, "R": R, "shield": copy.deepcopy(shield)}


def load_frozen_v3() -> dict:
    return json.loads(FROZEN_V3.read_text())["shield"]


def _frozen_arm(name: str, newname: str | None = None, R: float | None = None) -> dict:
    a = copy.deepcopy(_src()[name])
    if newname:
        a["name"] = newname
    if R is not None:
        a["R"] = R
    return a


def comparator_arms(hs, k: float = K_SC) -> list[dict]:
    """never, wald_cut, cusum, gate_wald, cusum_rb_h8 and stoploss / f3_pi1 / f3v2d at each h."""
    arms = [_frozen_arm(n) for n in ("never", "wald_cut", "cusum", "gate_wald", "cusum_rb_h8")]
    for h in hs:
        for tmpl, tag in (
            ("stoploss_R20", "stoploss"),
            ("f3_pi1_R20", "f3_pi1"),
            ("f3v2d_R20", "f3v2d"),
        ):
            arms.append(_frozen_arm(tmpl, f"{tag}_h{h}", R_of(h, k)))
    return arms


def selection_arms() -> list[dict]:
    arms = comparator_arms(HS_SEL)
    arms = [a for a in arms if a["name"] != "never"]
    arms.insert(0, _frozen_arm("never"))
    for c in candidate_grid():
        arms.append(v3_arm(c, R_of(50), cand_name(c)))
    return arms


def scarce_eval_arms() -> list[dict]:
    arms = comparator_arms((14, 50, 100))
    sh = load_frozen_v3()
    for h in (6, 14, 24, 50, 100):
        arms.append(v3_arm(sh, R_of(h), f"v3_h{h}"))
    return arms


def orig30_arms() -> list[dict]:
    arms = [_frozen_arm(n) for n in ("never", "wald_cut")]
    for R in (12, 20, 30):
        arms.append(_frozen_arm(f"f3_pi1_R{R}"))
    for R in (20, 30):
        arms.append(_frozen_arm(f"f3v2d_R{R}"))
    sh = load_frozen_v3()
    for R in (12, 20, 30):
        arms.append(v3_arm(sh, R, f"v3_R{R}"))
    return arms


# ------------------------------------------------------------------------------------------
# runner
# ------------------------------------------------------------------------------------------
_REG: dict = {}
_ARMS: list = []
_T = 0


def _init(which: str, arms: list, T: int):
    global _REG, _ARMS, _T
    _REG = scarce_regimes() if which == "scarce" else all_regimes()
    _ARMS, _T = arms, T


def _task(args):
    rid, seed = args
    reg = _REG[rid]
    tape, truth = generate_tape(reg, seed, _T)
    spec = make_spec(reg, _T)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    rows = []
    for arm in _ARMS:
        pol = make_arm_v2(arm, _T)
        rec = run_policy(pol, tape, spec, seed)
        e = ev.evaluate(rec)
        row = {k: float(e[k]) for k in FIELDS_V2 if k in e}
        row.update(harm_summary(tape, rec, spec.costs.k))
        row["frac_time_deployed"] = float(np.mean(rec.a))
        for k in DIAG:
            if hasattr(pol, k):
                row[k] = float(getattr(pol, k))
        rows.append(row)
    return rid, seed, rows


def run_family(
    which: str, arms: list, seed_list, out_dir: Path, T: int, workers: int = 6, log=print
) -> float:
    if workers > 6:
        raise ValueError("at most 6 workers")
    out_dir.mkdir(parents=True, exist_ok=True)
    names = [a["name"] for a in arms]
    (out_dir / "_arms.spec").write_text(json.dumps(arms, default=float, indent=1))
    rids = list(scarce_regimes() if which == "scarce" else all_regimes())
    t0 = time.time()
    with Pool(workers, initializer=_init, initargs=(which, arms, T), maxtasksperchild=400) as pool:
        for rid in rids:
            path = out_dir / f"{rid}.json"
            if path.exists():
                log(f"skip {rid} (exists)")
                continue
            res = {}
            for _, s, rows in pool.imap_unordered(_task, [(rid, s) for s in seed_list], 2):
                res[s] = rows
            fields = {
                f: [[res[s][i].get(f) for s in seed_list] for i in range(len(names))]
                for f in FIELDS_OUT
            }
            out = {"regime": rid, "seeds": list(seed_list), "arms": names, "fields": fields}
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(out))
            tmp.rename(path)
            log(f"done {rid}  elapsed {time.time() - t0:.0f}s")
    return time.time() - t0


def load_family(out_dir: Path, which: str):
    """-> (arm names, regime ids, seeds, {field: array (arm, regime, seed), NaN for missing})"""
    order = list(scarce_regimes() if which == "scarce" else all_regimes())
    files = {r: json.loads((out_dir / f"{r}.json").read_text()) for r in order}
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
