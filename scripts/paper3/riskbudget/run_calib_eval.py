"""Evaluate the calibrated comparators (config f3_calibrated_comparators_v1.json).

usage: run_calib_eval.py sim|real [--workers N]
sim : 30 regimes, T = 300, fresh dev seeds seeds_for("dev", 1000, 81000); arms never, wald_cut,
      f3_pi1_R{12,20,30}, f3v2d_R{20,30} (frozen specs), stoploss_cal_R*, cusumrb_cal_R*.
      -> outputs/paper3/riskbudget/calib_eval/<regime>.json
real: THIRD LOOK at the real streams; comparators calibrated on simulation only. Same episodes and
      policy seeds seeds_for("dev", 20, 60000) as the first real run; new arms only (plus never as a
      consistency check): stoploss_cal_h{6,14,24}, cusumrb_cal_h{6,14,24} with R = 10 + h and the
      (c, h_c) calibrated at the simulation R with the same headroom (h6->R12, h14->R20, h24->R30).
      -> outputs/paper3/riskbudget/real_calib/<condition>/<stream>.json
No tuning on the real streams.
"""

import argparse
import datetime
import json
import sys
import time
from multiprocessing import Pool

import numpy as np
from calibrate_comparators import OUT_CFG, make_cal_arm

from shiftlab.paper3.riskbudget.harness import FIELDS, ROOT, all_regimes
from shiftlab.paper3.riskbudget.harness_v2 import DIAG, make_arm_v2
from shiftlab.paper3.riskbudget.metrics import harm_summary
from shiftlab.paper3.riskbudget.real_streams import (
    CONDITIONS,
    ROW_FIELDS,
    STREAMS,
    R_of,
    corruption_rng,
    delay_of,
    load_stream,
    make_real_spec,
    make_real_tape,
)
from shiftlab.paper3.simulation import (
    CONFIG_DIR,
    SimulationEvaluator,
    generate_tape,
    make_spec,
    run_policy,
    seeds_for,
)

ARMS_FILE = CONFIG_DIR / "f3_confirmation_arms_v1.json"
OUT = ROOT / "outputs" / "paper3" / "riskbudget"
LEDGER = ROOT / "papers/paper3_cost_aware_adaptation/2026_programme/ledger/riskbudget.jsonl"
T_SIM, SIM_N, SIM_START = 300, 1000, 81000
T_REAL, REAL_N, REAL_START = 2000, 20, 60000
H_TO_R = {6: 12, 14: 20, 24: 30}
SIM_FROZEN = (
    "never",
    "wald_cut",
    "f3_pi1_R12",
    "f3_pi1_R20",
    "f3_pi1_R30",
    "f3v2d_R20",
    "f3v2d_R30",
)


def calib():
    return json.loads(OUT_CFG.read_text())["calibration"]


def sim_arms():
    src = {a["name"]: a for a in json.loads(ARMS_FILE.read_text())["arms"]}
    arms = [src[n] for n in SIM_FROZEN]
    cal = calib()
    for R in (12, 20, 30):
        arms.append({"name": f"stoploss_cal_R{R}", "type": "stoploss_cal", "R": R,
                     "c": cal[f"R{R}"]["stoploss_cal"]["chosen"]})  # fmt: skip
    for R in (12, 20, 30):
        arms.append({"name": f"cusumrb_cal_R{R}", "type": "cusumrb_cal", "R": R,
                     "h": cal[f"R{R}"]["cusumrb_cal"]["chosen"]})  # fmt: skip
    return arms


def real_arms():
    cal = calib()
    arms = [{"name": "never", "type": "policy", "policy": {"kind": "never"}}]
    for h, R in H_TO_R.items():
        arms.append({"name": f"stoploss_cal_h{h}", "type": "stoploss_cal", "R": R_of(h),
                     "c": cal[f"R{R}"]["stoploss_cal"]["chosen"], "sim_R": R})  # fmt: skip
    for h, R in H_TO_R.items():
        arms.append({"name": f"cusumrb_cal_h{h}", "type": "cusumrb_cal", "R": R_of(h),
                     "h": cal[f"R{R}"]["cusumrb_cal"]["chosen"], "sim_R": R})  # fmt: skip
    return arms


def make_any(arm, T):
    if arm["type"] == "stoploss_cal":
        return make_cal_arm("stoploss_cal", arm["R"], arm["c"], T)
    if arm["type"] == "cusumrb_cal":
        return make_cal_arm("cusumrb_cal", arm["R"], arm["h"], T)
    return make_arm_v2(arm, T)


_S = {}


def _init(mode):
    _S["mode"] = mode
    _S["arms"] = sim_arms() if mode == "sim" else real_arms()
    if mode == "sim":
        _S["reg"] = all_regimes()


def _sim_task(args):
    rid, seed = args
    reg = _S["reg"][rid]
    tape, truth = generate_tape(reg, seed, T_SIM)
    spec = make_spec(reg, T_SIM)
    ev = SimulationEvaluator(tape, truth, spec.costs)
    rows = []
    for arm in _S["arms"]:
        pol = make_any(arm, T_SIM)
        rec = run_policy(pol, tape, spec, seed)
        e = ev.evaluate(rec)
        row = {k: float(e[k]) for k in FIELDS if k in e}
        row.update(harm_summary(tape, rec, spec.costs.k))
        row["frac_time_deployed"] = float(np.mean(rec.a))
        for k in DIAG:
            if hasattr(pol, k):
                row[k] = float(getattr(pol, k))
        rows.append(row)
    return seed, rows


_DATA: dict = {}


def _real_task(args):
    cond, stream, ep = args
    if stream not in _DATA:
        _DATA[stream] = load_stream(stream)
    l0, l1 = _DATA[stream]
    delay = delay_of(stream)
    tape = make_real_tape(l0[ep], l1[ep], delay, cond, corruption_rng(stream, ep, cond))
    spec = make_real_spec(delay, cond)
    seeds = seeds_for("dev", REAL_N, REAL_START)
    out = []
    for arm in _S["arms"]:
        per = []
        for s in seeds:
            pol = make_any(arm, T_REAL)
            rec = run_policy(pol, tape, spec, s)
            row = {
                "J": rec.J,
                "J_never": float(tape.ell[:, 0].sum()),
                "n_queries": float(rec.ledger["n_queries"]),
                "n_switches": float(rec.ledger["n_switches"]),
                "frac_time_deployed": float(np.mean(rec.a)),
                **harm_summary(tape, rec, spec.costs.k),
            }
            for k in DIAG:
                if hasattr(pol, k):
                    row[k] = float(getattr(pol, k))
            per.append(row)
        out.append(per)
    return cond, stream, ep, out


def ledger(stage, config, t0):
    rec = {
        "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
        "workstream": "F3_riskbudget",
        "stage": stage,
        "config": config,
        "wall_clock_s": time.time() - t0,
    }
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")


def run_sim(workers):
    out = OUT / "calib_eval"
    if out.exists():
        sys.exit(f"{out} exists")
    out.mkdir(parents=True)
    arms = sim_arms()
    names = [a["name"] for a in arms]
    seeds = seeds_for("dev", SIM_N, SIM_START)
    keys = sorted(set(FIELDS) | set(DIAG) | {"sup_harm", "final_harm", "frac_time_deployed"})
    t0 = time.time()
    with Pool(workers, initializer=_init, initargs=("sim",), maxtasksperchild=500) as pool:
        for rid in all_regimes():
            res = dict(pool.imap_unordered(_sim_task, [(rid, s) for s in seeds], chunksize=2))
            fields = {
                f: [[res[s][i].get(f) for s in seeds] for i in range(len(names))] for f in keys
            }
            (out / f"{rid}.json").write_text(
                json.dumps({"regime": rid, "seeds": seeds, "arms": names, "fields": fields})
            )
            print(f"done {rid} {time.time() - t0:.0f}s", flush=True)
    ledger("calib_eval_sim", {"seeds": [seeds[0], seeds[-1]], "n": len(seeds), "T": T_SIM,
                              "arms": arms}, t0)  # fmt: skip


def run_real(workers):
    out = OUT / "real_calib"
    if out.exists():
        sys.exit(f"{out} exists")
    arms = real_arms()
    names = [a["name"] for a in arms]
    seeds = seeds_for("dev", REAL_N, REAL_START)
    tasks, n_ep = [], {}
    for s in STREAMS:
        n_ep[s] = len(np.load(STREAMS[s][0] / f"{s}.npz")["l0"])
    tasks = [(c, s, e) for c in CONDITIONS for s in STREAMS for e in range(n_ep[s])]
    res: dict = {}
    t0 = time.time()
    with Pool(workers, initializer=_init, initargs=("real",), maxtasksperchild=40) as pool:
        for i, (c, s, e, rows) in enumerate(pool.imap_unordered(_real_task, tasks, chunksize=1)):
            res[(c, s, e)] = rows
            if (i + 1) % 20 == 0:
                print(f"{i + 1}/{len(tasks)} {time.time() - t0:.0f}s", flush=True)
            if all((c, s, ee) in res for ee in range(n_ep[s])):
                n = n_ep[s]
                fields = {
                    f: [
                        [
                            [res[(c, s, ee)][ai][si].get(f) for si in range(len(seeds))]
                            for ee in range(n)
                        ]
                        for ai in range(len(names))
                    ]
                    for f in ROW_FIELDS
                }
                d = out / c
                d.mkdir(parents=True, exist_ok=True)
                body = {"stream": s, "condition": c, "delay": delay_of(s), "n_episodes": n,
                        "seeds": seeds, "arms": names, "arm_specs": arms, "fields": fields}  # fmt: skip
                (d / f"{s}.json").write_text(json.dumps(body))
                for ee in range(n):
                    del res[(c, s, ee)]
    ledger(
        "calib_eval_real_third_look",
        {"label": "THIRD LOOK at the real streams; comparators calibrated on simulation only",
         "n_episodes": sum(n_ep.values()), "seeds": [seeds[0], seeds[-1]], "T": T_REAL,
         "arms": arms},
        t0,
    )  # fmt: skip


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("sim", "real"))
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.workers > 6:
        sys.exit("at most 6 workers")
    (run_sim if a.mode == "sim" else run_real)(a.workers)
