"""Experiment Type II: optimised-controller comparison (DEVELOPMENT, synthetic Setting C).

Per cell: tune (monitor x controller x alpha) and a simple-policy family on tuning seeds (base 100000, n=500),
select by mean cost_exp, evaluate selected configs on fresh seeds (base 200000, n=2000). Design: docs/decision_value/11.
Usage: python run_type2_tuning.py run [--procs 4] [--n-tune 500] [--n-eval 2000] [--cells id,id] [--tag smoke]
       python run_type2_tuning.py analyze --dir DIR
"""

from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
import json
import sys
import time
from datetime import UTC, datetime
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from shiftlab.decision_value import controllers as C
from shiftlab.decision_value.calibration import null_maxima
from shiftlab.decision_value.contracts import CostContract, FeedbackContract
from shiftlab.decision_value.evaluation import count_switches, score, simulate
from shiftlab.decision_value.monitors import monitor_factory
from shiftlab.decision_value.oracles import oracle_costs
from shiftlab.decision_value.registry import append_run
from shiftlab.decision_value.statistics import classify_reversal, holm, paired_bootstrap_diff
from shiftlab.decision_value.synthetic import Family

DEV_OUT = ROOT / "outputs" / "decision_value" / "development"
CAL_DIR = DEV_OUT / "_calibration_cache"
N_CAL, CAL_SEED = 6000, 5_000_000
MONITORS = ("cusum", "page_hinkley", "batch", "sr_betting", "kelly_h2c_inspired")
BOOT = 10_000
# suites: "orig" = first Type II run (docs/decision_value/11 sections 1-7); "orig_ext" = same cells/seeds, extended grids;
# "asym" = asymmetric-regime cells (doc 11 section 8), fresh seeds.
EXT = {
    "alphas": (0.01, 0.05, 0.2, 0.5, 0.8, 0.95),
    "holds": (25, 50, 100, 200, 400, 800, 1000, 1600),
    "cal_k": (25, 50, 100, 200, 400, 800, 1000, 1600),
    "margins": (0.0, 0.01, 0.02, 0.05, 0.1),
    "stat_w": (50, 100, 200, 400),
    "stat_m": (0.0, 0.02, 0.05),
}
CFGS = {
    "orig": {
        "alphas": (0.01, 0.05, 0.2, 0.5),
        "holds": (25, 50, 100, 200, 400, 800),
        "cal_k": (25, 50, 100, 200, 400, 800),
        "margins": (0.0, 0.01, 0.02, 0.05),
        "stat_w": (50, 100, 200),
        "stat_m": (0.0, 0.02),
        "tune_base": 100_000,
        "eval_base": 200_000,
        "cal_tag": "",
    },
    "orig_ext": dict(EXT, tune_base=100_000, eval_base=200_000, cal_tag="x"),
    "asym": dict(EXT, tune_base=300_000, eval_base=400_000, cal_tag="x"),
}


def controllers_of(cfg):
    return ["permanent"] + [f"hold:{h}" for h in cfg["holds"]] + ["reverse"]


# ------------------------------------------------------------------ simple controllers with margins
class CalendarMargin(C.Controller):
    name, uses_monitor, acquires = "calendar_m", False, True

    def __init__(self, n, T, c_s=0.0, K=200, m=0.0):
        super().__init__(n, T, c_s)
        self.K, self.m = int(K), float(m)
        self.s0, self.s1, self.cnt = np.zeros(n), np.zeros(n), np.zeros(n)

    def step(self, s, alarm, rel):
        if s > 0 and s % self.K == 0:
            c = np.maximum(self.cnt, 1)
            adv = self.s0 / c - self.s1 / c  # released window-mean advantage of the challenger
            has = self.cnt > 0
            self.a = np.where(
                has & (adv > self.m), 1, np.where(has & (adv < -self.m), 0, self.a)
            ).astype(np.int8)
            self.s0[:] = self.s1[:] = self.cnt[:] = 0.0
        self.s0 += np.where(rel.valid, rel.l0, 0.0)
        self.s1 += np.where(rel.valid, rel.l1, 0.0)
        self.cnt += rel.valid
        return self.a, np.zeros(self.n, bool)


class StaticMargin(C.StaticThreshold):
    def __init__(self, n, T, c_s=0.0, W=100, m=0.0):
        super().__init__(n, T, c_s, W)
        self.m = float(m)

    def step(self, s, alarm, rel):
        v = rel.valid
        idx = np.flatnonzero(v)
        self.buf[idx, self.cnt[idx] % self.W] = (rel.l0 - rel.l1)[idx]
        self.cnt += v
        gap = self.buf.mean(axis=1)
        go = (self.cnt >= self.W) & (gap * (self.T - s) > self.c_s) & (gap > self.m)
        self.a = (self.a.astype(bool) | go).astype(np.int8)
        return self.a, np.zeros(self.n, bool)


def simple_configs(cfg):
    out = ["never", "always"]
    out += [f"calm:{K}:{m}" for K in cfg["cal_k"] for m in cfg["margins"]]
    out += [f"statm:{W}:{m}" for W in cfg["stat_w"] for m in cfg["stat_m"]]
    return out


def build_simple(spec, n, T, c_s):
    p = spec.split(":")
    if p[0] == "never":
        return C.NeverSwitch(n, T, c_s)
    if p[0] == "always":
        return C.AlwaysChallenger(n, T, c_s)
    if p[0] == "calm":
        return CalendarMargin(n, T, c_s, K=int(p[1]), m=float(p[2]))
    if p[0] == "statm":
        return StaticMargin(n, T, c_s, W=int(p[1]), m=float(p[2]))
    raise ValueError(spec)


def build_system(ctrl, n, T, c_s, fac, thr):
    name, _, arg = ctrl.partition(":")
    if name == "permanent":
        return C.Permanent(n, T, c_s)
    if name == "hold":
        return C.Hold(n, T, c_s, H=int(arg))
    if name == "reverse":
        return C.Reverse(n, T, c_s, rev_factory=fac, rev_threshold=thr)
    raise ValueError(ctrl)


# ------------------------------------------------------------------ calibration (null is family-independent)
def cal_path(monitor, q, d, suite="orig"):
    return (
        CAL_DIR
        / f"type2{CFGS[suite]['cal_tag']}_{monitor}_paired_q{q}_d{d}_n{N_CAL}_s{CAL_SEED}.json"
    )


def thresholds(monitor, q, d, suite="orig"):
    ALPHAS = CFGS[suite]["alphas"]
    path = cal_path(monitor, q, d, suite)
    if path.exists():
        return json.loads(path.read_text())
    fac = monitor_factory(monitor, target="paired")
    mx = null_maxima(fac, Family("s1"), FeedbackContract(q, d), N_CAL, CAL_SEED)
    info = {str(a): float(np.quantile(mx, 1 - a, method="higher")) for a in ALPHAS}
    info["null_rate"] = {str(a): float((mx > info[str(a)]).mean()) for a in ALPHAS}
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(info))
    os.replace(tmp, path)
    return info


def _cal_task(t):
    t0 = time.time()
    thresholds(*t)
    return t, time.time() - t0


# ------------------------------------------------------------------ cells
def cell_specs(suite="orig"):
    if suite == "asym":
        out = []
        for B in (100, 400, 1000):
            for pi in (0.1, 0.25):
                for d in (0, 50):
                    out.append(asym_spec(B, pi, d, "useful"))
        out.append(asym_spec(400, 0.1, 0, "useless", control=True))
        for i, s in enumerate(out):
            s["idx"] = i
            s["suite"] = suite
        return out
    out = []
    for rho, d in ((0.995, 0), (0.995, 50), (0.999, 0), (0.999, 50)):
        out.append(
            {
                "id": f"th3_rho{rho}_d{d}_useful",
                "family": "s2",
                "params": {"rho": rho, "challenger_bad": "useful"},
                "q": 0.2,
                "d": d,
                "c_s": 2.0,
            }
        )
    out.append(
        {
            "id": "th3_rho0.999_d0_useless",
            "family": "s2",
            "params": {"rho": 0.999, "challenger_bad": "useless"},
            "q": 0.2,
            "d": 0,
            "c_s": 2.0,
            "control": True,
        }
    )
    for L in (400, 1600):
        for d in (0, 50):
            out.append(
                {
                    "id": f"th4_L{L}_d{d}",
                    "family": "s1",
                    "params": {"L": L},
                    "q": 0.5,
                    "d": d,
                    "c_s": 5.0,
                }
            )
    for ch in ("strong", "weak"):
        out.append(
            {
                "id": f"th2_{ch}",
                "family": "s3",
                "params": {"challenger": ch},
                "q": 0.2,
                "d": 50,
                "c_s": 5.0,
            }
        )
    for i, s in enumerate(out):
        s["idx"] = i
        s["suite"] = suite
    return out


def asym_spec(B, pi, d, fb, control=False):
    rb = 1 - 1 / B
    rg = 1 - pi * (1 - rb) / (1 - pi)
    lam = rg + rb - 1
    theta_max = pi + (1 - pi) * lam ** (
        d + 1
    )  # P5 ceiling: P(bad at decision | bad at release event)
    s = {
        "id": f"asym_B{B}_pi{pi}_d{d}_{fb}",
        "family": "s2",
        "params": {"rho_g": rg, "rho_b": rb, "challenger_bad": fb},
        "q": 0.2,
        "d": d,
        "c_s": 2.0,
        "B": B,
        "pi_b": pi,
        "lam": lam,
        "theta_max": theta_max,
    }
    if control:
        s["control"] = True
    return s


def lean(sim, truth, c_s):
    a = sim.actions.astype(bool)
    return float(
        (np.where(a, truth.mu1, truth.mu0).sum(axis=1) + c_s * count_switches(sim.actions)).mean()
    )


def run_cell(arg):
    spec, outdir, n_tune, n_eval = arg
    cfg = CFGS[spec["suite"]]
    ALPHAS, CONTROLLERS, TUNE_BASE, EVAL_BASE = (
        cfg["alphas"],
        controllers_of(cfg),
        cfg["tune_base"],
        cfg["eval_base"],
    )
    t0 = time.time()
    fam = Family(spec["family"], spec["params"])
    T, c_s = fam.T, spec["c_s"]
    fb, cost = FeedbackContract(spec["q"], spec["d"]), CostContract(0.0, c_s)
    thr = {m: thresholds(m, spec["q"], spec["d"], spec["suite"]) for m in MONITORS}
    # ---- tuning
    batch, truth = fam.generate(TUNE_BASE + spec["idx"], n_tune, fb)
    tune = {}
    for m in MONITORS:
        fac = monitor_factory(m, target="paired")
        for ctrl in CONTROLLERS:
            for a in ALPHAS:
                mon = fac(n_tune)
                mon.threshold = thr[m][str(a)]
                sim = simulate(
                    batch, fb, mon, build_system(ctrl, n_tune, T, c_s, fac, mon.threshold)
                )
                tune[f"{m}|{ctrl}|{a}"] = lean(sim, truth, c_s)
    for sc in simple_configs(cfg):
        tune[f"simple|{sc}"] = lean(
            simulate(batch, fb, None, build_simple(sc, n_tune, T, c_s)), truth, c_s
        )
    never_tune = tune["simple|never"]
    best = {m: min((k for k in tune if k.startswith(m + "|")), key=tune.get) for m in MONITORS}
    best_mon = min(best.values(), key=tune.get)
    best_simple = min((k for k in tune if k.startswith("simple|")), key=tune.get)
    t_tune = time.time() - t0
    # ---- evaluation on fresh seeds
    batch, truth = fam.generate(EVAL_BASE + spec["idx"], n_eval, fb)
    orc = oracle_costs(batch, truth, cost)
    store = {f"__orc|{k}": orc[k] for k in ("never_exp", "always_exp", "static_exp", "dynamic_exp")}
    keys = ("cost_exp", "N_s", "power_T", "power_opp", "delay_cens", "any_alarm")
    for m, k in best.items():
        _, ctrl, a = k.split("|")
        fac = monitor_factory(m, target="paired")
        mon = fac(n_eval)
        mon.threshold = thr[m][a]
        rec = score(
            simulate(batch, fb, mon, build_system(ctrl, n_eval, T, c_s, fac, mon.threshold)),
            batch,
            truth,
            cost,
        )
        for kk in keys:
            store[f"{m}|{kk}"] = np.asarray(rec[kk])
    for tag, sc in (
        ("simple", best_simple.split("|", 1)[1]),
        ("never", "never"),
        ("always", "always"),
    ):
        rec = score(simulate(batch, fb, None, build_simple(sc, n_eval, T, c_s)), batch, truth, cost)
        for kk in ("cost_exp", "N_s"):
            store[f"{tag}|{kk}"] = np.asarray(rec[kk])
    meta = {
        "spec": spec,
        "n_tune": n_tune,
        "n_eval": n_eval,
        "tune_seed": TUNE_BASE + spec["idx"],
        "eval_seed": EVAL_BASE + spec["idx"],
        "tune_cost": tune,
        "best_per_monitor": best,
        "best_monitor": best_mon,
        "best_simple": best_simple,
        "never_tune": never_tune,
        "thresholds": thr,
        "runtime_tune_s": t_tune,
        "runtime_s": time.time() - t0,
    }
    cells = Path(outdir) / "cells"
    cells.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cells / f"{spec['id']}.npz", **store)
    (cells / f"{spec['id']}.json").write_text(json.dumps(meta, indent=1))
    return spec["id"], meta["runtime_s"]


# ------------------------------------------------------------------ analysis
def md(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def kt(x, y):
    return float("nan") if np.ptp(x) == 0 or np.ptp(y) == 0 else float(kendalltau(x, y).statistic)


def ci(d, seed):
    return paired_bootstrap_diff(d, np.zeros_like(d), B=BOOT, seed=seed)


def analyze(outdir):
    outdir = Path(outdir)
    cells = {}
    for p in sorted((outdir / "cells").glob("*.json")):
        z = np.load(p.with_suffix(".npz"))
        cells[p.stem] = (json.loads(p.read_text()), {k: z[k] for k in z.files})
    ids = [i for i, _ in sorted(cells.items(), key=lambda kv: kv[1][0]["spec"]["idx"])]
    res, lines, sys_p = {}, [], []
    for cid in ids:
        meta, z = cells[cid]
        nv = z["__orc|never_exp"]
        mme = 0.01 * nv.mean()
        dyn, sta = z["__orc|dynamic_exp"].mean(), z["__orc|static_exp"].mean()
        head = nv.mean() - dyn
        bm = meta["best_monitor"].split("|")[0]
        cs, cm = z["simple|cost_exp"], z[f"{bm}|cost_exp"]
        r = ci(cs - cm, seed=1)
        sys_p.append(r["p"])
        row = {
            "best_monitor": meta["best_monitor"],
            "best_simple": meta["best_simple"],
            "diff": r,
            "mme": float(mme),
            "never": float(nv.mean()),
            "dynamic": float(dyn),
            "static": float(sta),
            "headroom": float(head),
            "cap_mon": float((nv.mean() - cm.mean()) / head) if head > 0 else None,
            "cap_simple": float((nv.mean() - cs.mean()) / head) if head > 0 else None,
            "Ns_mon": float(z[f"{bm}|N_s"].mean()),
            "Ns_simple": float(z["simple|N_s"].mean()),
            "opt_mon": float(meta["tune_cost"][meta["best_monitor"]] - cm.mean()),
            "opt_simple": float(meta["tune_cost"][meta["best_simple"]] - cs.mean()),
            "always": float(z["always|cost_exp"].mean()),
            "per_monitor": {},
        }
        for m in MONITORS:
            c = z[f"{m}|cost_exp"]
            row["per_monitor"][m] = {
                "config": meta["best_per_monitor"][m],
                "cost": float(c.mean()),
                "diff_vs_simple": ci(cs - c, seed=2),
                "power_T": float(z[f"{m}|power_T"].mean()),
                "delay_cens": float(z[f"{m}|delay_cens"].mean()),
                "Ns": float(z[f"{m}|N_s"].mean()),
                "opt": float(meta["tune_cost"][meta["best_per_monitor"][m]] - c.mean()),
            }
        pw = np.array([row["per_monitor"][m]["power_T"] for m in MONITORS])
        dl = np.array([row["per_monitor"][m]["delay_cens"] for m in MONITORS])
        val = np.array([nv.mean() - row["per_monitor"][m]["cost"] for m in MONITORS])
        row["tau_power_value"], row["tau_delay_value"] = kt(pw, val), kt(-dl, val)
        nrev = 0
        for ia, a in enumerate(MONITORS):
            for ib, b in enumerate(MONITORS):
                if (
                    a == b
                    or z[f"{a}|cost_exp"].mean() - z[f"{b}|cost_exp"].mean() < mme
                    or pw[ia] - pw[ib] < 0.05
                ):
                    continue
                rv = classify_reversal(
                    z[f"{a}|power_T"].astype(float),
                    z[f"{b}|power_T"].astype(float),
                    z[f"{a}|delay_cens"],
                    z[f"{b}|delay_cens"],
                    z[f"{a}|cost_exp"],
                    z[f"{b}|cost_exp"],
                    mme,
                    B=2000,
                    seed=0,
                )
                nrev += int(rv["reversal"] and "power" in rv["detection_via"])
        row["n_reversals_power"] = nrev
        res[cid] = row
    adj = holm(sys_p)
    for cid, a in zip(ids, adj):
        r = res[cid]
        d = r["diff"]
        r["holm_p"] = float(a)
        r["winner"] = (
            "monitor"
            if d["mean"] >= r["mme"] and d["lo"] > 0 and a < 0.05
            else "simple"
            if d["mean"] <= -r["mme"] and d["hi"] < 0 and a < 0.05
            else "tie"
        )
    f2 = lambda x: f"{x:.2f}"
    ci_s = lambda d: f"{d['mean']:.2f} [{d['lo']:.2f}, {d['hi']:.2f}]"
    lines.append(
        "## Per-cell system-level comparison (eval seeds; diff = cost(best simple) - cost(best monitor system), positive = monitor better)\n"
    )
    lines.append(
        md(
            [
                "cell",
                "best monitor system (tuned)",
                "cost",
                "best simple (tuned)",
                "cost",
                "diff [95% CI]",
                "MME",
                "Holm p",
                "winner",
            ],
            [
                [
                    c,
                    res[c]["best_monitor"],
                    f2(res[c]["per_monitor"][res[c]["best_monitor"].split("|")[0]]["cost"]),
                    res[c]["best_simple"].split("|", 1)[1],
                    f2(cells[c][1]["simple|cost_exp"].mean()),
                    ci_s(res[c]["diff"]),
                    f2(res[c]["mme"]),
                    f"{res[c]['holm_p']:.4f}",
                    res[c]["winner"],
                ]
                for c in ids
            ],
        )
    )
    lines.append("\n## Reference costs, headroom capture, switches, selection optimism\n")
    na = lambda v: "NA" if v is None else f"{v:.2f}"
    lines.append(
        md(
            [
                "cell",
                "never",
                "always",
                "static*",
                "dynamic",
                "headroom",
                "captured monitor",
                "captured simple",
                "N_s mon",
                "N_s simple",
                "optimism mon",
                "optimism simple",
            ],
            [
                [
                    c,
                    f2(res[c]["never"]),
                    f2(res[c]["always"]),
                    f2(res[c]["static"]),
                    f2(res[c]["dynamic"]),
                    f2(res[c]["headroom"]),
                    na(res[c]["cap_mon"]),
                    na(res[c]["cap_simple"]),
                    f2(res[c]["Ns_mon"]),
                    f2(res[c]["Ns_simple"]),
                    f2(res[c]["opt_mon"]),
                    f2(res[c]["opt_simple"]),
                ]
                for c in ids
            ],
        )
    )
    lines.append(
        "\n(*static = per-episode hindsight best of never/always, oracle.) Optimism = tuning-seed cost - eval-seed cost of the selected config.\n"
    )
    bt = []
    for c in ids:
        sp, mt = cells[c][0]["spec"], cells[c][0]
        cfg = CFGS[sp["suite"]]
        _, ctrl, al = mt["best_monitor"].split("|")
        flag = []
        if float(al) == max(cfg["alphas"]):
            flag.append("alpha=max")
        if float(al) == min(cfg["alphas"]):
            flag.append("alpha=min")
        if ctrl == f"hold:{max(cfg['holds'])}":
            flag.append("H=max")
        res[c]["boundary"] = flag
        n_mon, n_sim = (
            len(MONITORS) * len(controllers_of(cfg)) * len(cfg["alphas"]),
            len(simple_configs(cfg)),
        )
        bt.append(
            [
                c,
                mt["best_monitor"],
                ",".join(flag) or "interior",
                mt["best_simple"].split("|", 1)[1],
                f"{sp['B']}/{sp['pi_b']}/{sp['theta_max']:.3f}" if "B" in sp else "",
                f"{n_mon} ({n_mon // len(MONITORS)}/monitor) vs {n_sim}",
            ]
        )
    lines.append(
        "\n## Selected configs, grid boundary, P5 ceiling (B = mean bad run, pi_b, theta_max = pi_b + (1-pi_b) lam^(d+1) per alarm), config counts\n"
    )
    lines.append(
        md(
            [
                "cell",
                "best monitor system",
                "boundary",
                "best simple",
                "B/pi_b/theta_max",
                "configs monitor vs simple",
            ],
            bt,
        )
    )
    lines.append("## Per-monitor tuned systems vs best simple (secondary)\n")
    rows = []
    for c in ids:
        for m in MONITORS:
            p = res[c]["per_monitor"][m]
            rows.append(
                [
                    c,
                    m,
                    p["config"].split("|", 1)[1],
                    f2(p["cost"]),
                    ci_s(p["diff_vs_simple"]),
                    f"{p['power_T']:.2f}",
                    f"{p['delay_cens']:.0f}",
                    f2(p["Ns"]),
                    f2(p["opt"]),
                ]
            )
    lines.append(
        md(
            [
                "cell",
                "monitor",
                "tuned (controller|alpha)",
                "cost",
                "simple - monitor [CI]",
                "power_T",
                "delay_cens",
                "N_s",
                "optimism",
            ],
            rows,
        )
    )
    lines.append("\n## H1 under tuning: detection ranking vs tuned cost ranking\n")
    lines.append(
        md(
            [
                "cell",
                "tau(power_T, value)",
                "tau(-delay, value)",
                "protocol reversals (power, of 20 pairs)",
            ],
            [
                [
                    c,
                    f"{res[c]['tau_power_value']:.2f}",
                    f"{res[c]['tau_delay_value']:.2f}",
                    res[c]["n_reversals_power"],
                ]
                for c in ids
            ],
        )
    )
    nc = [c for c in ids if not cells[c][0]["spec"].get("control")]
    wins = {k: sum(res[c]["winner"] == k for c in nc) for k in ("monitor", "simple", "tie")}
    lines.append(
        f"\nNon-control cells ({len(nc)}): monitor wins {wins['monitor']}, simple wins {wins['simple']}, ties {wins['tie']}."
    )
    (outdir / "tables.md").write_text("\n".join(lines), encoding="utf8")
    (outdir / "results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf8")
    print("\n".join(lines))
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze"])
    ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--n-tune", type=int, default=500)
    ap.add_argument("--n-eval", type=int, default=2000)
    ap.add_argument("--cells", default="")
    ap.add_argument("--tag", default="")
    ap.add_argument("--suite", default="orig", choices=list(CFGS))
    ap.add_argument("--dir", default="")
    a = ap.parse_args()
    if a.cmd == "analyze":
        analyze(a.dir)
        return
    ts = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    pre = a.tag + "_" if a.tag else ""
    pre = (a.suite + "_" if a.suite != "orig" else "") + pre
    outdir = DEV_OUT / f"type2_{pre}{ts}"
    specs = [s for s in cell_specs(a.suite) if not a.cells or s["id"] in a.cells.split(",")]
    t0 = time.time()
    cal = sorted({(m, s["q"], s["d"], a.suite) for s in specs for m in MONITORS})
    todo = [t for t in cal if not cal_path(*t).exists()]
    print(f"calibration: {len(todo)} of {len(cal)} to compute", flush=True)
    with Pool(a.procs) as pool:
        for i, (t, dt) in enumerate(pool.imap_unordered(_cal_task, todo), 1):
            print(f"  cal {i}/{len(todo)} {t} {dt:.0f}s", flush=True)
    t_cal = time.time() - t0
    with Pool(a.procs) as pool:
        for i, (cid, rt) in enumerate(
            pool.imap_unordered(run_cell, [(s, str(outdir), a.n_tune, a.n_eval) for s in specs]), 1
        ):
            print(f"  cell {i}/{len(specs)} {cid} {rt:.0f}s", flush=True)
    t_sim = time.time() - t0 - t_cal
    analyze(outdir)
    rt = time.time() - t0
    append_run(
        f"type2_{pre}{ts}",
        {
            "cells": specs,
            "suite": a.suite,
            "cfg": CFGS[a.suite],
            "controllers": controllers_of(CFGS[a.suite]),
            "monitors": MONITORS,
            "simple": simple_configs(CFGS[a.suite]),
            "n_cal": N_CAL,
            "cal_seed": CAL_SEED,
            "boot": BOOT,
            "runtime_calibration_s": t_cal,
            "runtime_simulation_s": t_sim,
            "script": "scripts/decision_value/run_type2_tuning.py",
        },
        {
            "tune_base": CFGS[a.suite]["tune_base"],
            "eval_base": CFGS[a.suite]["eval_base"],
            "cal": CAL_SEED,
        },
        a.n_eval,
        rt,
        [outdir],
    )
    print(f"done {rt:.0f}s (cal {t_cal:.0f}s, sim {t_sim:.0f}s) -> {outdir.name}")


if __name__ == "__main__":
    main()
