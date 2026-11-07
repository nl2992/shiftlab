"""Hindsight-gate headroom bound for track-A economic gating.

Protocol (locked before running): docs/sota_fidelity/econ_gate_bound_protocol.md.

    uv run --extra drift python scripts/sota_fidelity/econ_gate_bound.py run --out DIR --workers 9
    uv run python scripts/sota_fidelity/econ_gate_bound.py analyze --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/failure_atlas_v2_flq", ROOT / "scripts/sota_sprint",
           ROOT / "scripts/promising_directions/sota/competitors", ROOT / "scripts/sota_fidelity"):
    sys.path.insert(0, str(_p))

SEED_BASE, SEEDS = 2026120801, 100
PRIMARY = ["F3_reversal_800", "W_reversal_700", "S_reversal_400", "V_reversal_1000"]
REGIMES = PRIMARY + ["F3_reversal_1200"]
BASES = ["esr_rmmbets_fullalpha", "two_sided_esr_label_clock", "rmm:LRMD_k1"]
PRIMARY_BASE = BASES[0]
NEVER = "CONTROL_never_switch"
MARGIN = 10.0  # decision threshold in cost units (protocol)


def best_veto_gate(desired: np.ndarray, cost: np.ndarray, cs: float):
    """Minimum-cost deployed path a that may change only where `desired` changes, and only to it.

    desired: (T,) 0/1 model the base policy deploys; cost: (T, 2) per-round cost of each model.
    Starts on model 0. Returns (prediction cost + cs * switches, path, n_switches).
    """
    T = len(desired)
    prev = np.r_[0, desired[:-1]]
    props = np.flatnonzero(desired != prev)
    bounds = np.r_[0, props, T]
    seg = [cost[bounds[i]:bounds[i + 1]].sum(axis=0) for i in range(len(bounds) - 1)]
    INF = float("inf")
    val = [seg[0][0], INF]  # cost so far, by current deployed model
    back = []
    for j, tau in enumerate(props):
        d = int(desired[tau])
        new, arg = [INF, INF], [0, 1]
        for a in (0, 1):
            if val[a] == INF:
                continue
            # keep a
            if val[a] < new[a]:
                new[a], arg[a] = val[a], a
            # accept the proposal (a switch only if a differs from it)
            if a != d and val[a] + cs < new[d]:
                new[d], arg[d] = val[a] + cs, a
        back.append(arg)
        val = [new[m] + seg[j + 1][m] if new[m] < INF else INF for m in (0, 1)]
    m = int(np.argmin(val))
    best = float(val[m])
    # recover path
    states = [m]
    for arg in reversed(back):
        m = arg[m]
        states.append(m)
    states = states[::-1]  # state on each segment
    path = np.repeat(states, np.diff(bounds))
    return best, path, int(np.sum(np.diff(np.r_[0, path]) != 0))


def _job(args):
    import screen
    from bench import CONTRACT, parse_regime
    from simulator import run_episode
    from smoke_shin_esr import build_extra
    from suite import build_suite, stream_from_losses

    name, seed = args
    extra = build_extra()
    R, _ = parse_regime(name)
    losses = R.sample(np.random.default_rng(np.random.SeedSequence([SEED_BASE, screen._h(R.name), seed])))
    gain, delay = R.truth_gain(), R.delay
    cs, cq, B = CONTRACT["cs"], CONTRACT["cq"], CONTRACT["budget"]
    j_never = float(losses[:, 0].sum())
    exp_cost = np.stack([np.zeros(len(gain)), -gain], axis=1)  # expected cost relative to model 0
    rows = []
    for pol in build_suite(losses.shape[0], B, cs, cq, CONTRACT["alpha"], delay, seed,
                           SEED_BASE + screen._h(name) % 1000, names=[NEVER] + BASES, extra=extra):
        preds, labels = stream_from_losses(losses, np.random.default_rng([SEED_BASE, screen._h(name), seed, 7]))
        res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=B,
                          label_price=cq, switch_cost=cs, trace=True)
        dep = np.fromiter((r["deployed_model"] for r in res.records), int, len(res.records))
        lab = cq * res.requested_labels
        g_real, path, nsw = best_veto_gate(dep, losses.astype(float), cs)
        g_exp, path_e, nsw_e = best_veto_gate(dep, exp_cost, cs)
        own_exp = float(exp_cost[np.arange(len(dep)), dep].sum() + cs * np.sum(np.diff(np.r_[0, dep]) != 0))
        props = np.flatnonzero(dep != np.r_[0, dep[:-1]])
        acc = path[props] == dep[props]
        rows.append({
            "regime": name, "seed": seed, "policy": pol.name, "net": res.net_cost,
            "labels": res.requested_labels, "switches": res.deployment_switches,
            "j_never": j_never, "path_check": float(losses[np.arange(len(dep)), dep].sum() - res.prediction_loss),
            "j_gate": g_real + lab, "gate_switches": nsw,
            "veto_prom": int(np.sum(~acc & (dep[props] == 1))), "veto_roll": int(np.sum(~acc & (dep[props] == 0))),
            "n_prop": len(props),
            # truth-informed: expected cost relative to never switching (never = 0)
            "exp_rel_base": own_exp + lab, "exp_rel_gate": g_exp + lab,
        })
    return rows


def run(out: Path, workers: int):
    jobs = [(r, s) for r in REGIMES for s in range(SEEDS)]
    out.mkdir(parents=True, exist_ok=True)
    with Pool(workers) as pool, (out / "records.jsonl").open("w") as f:
        for i, rows in enumerate(pool.imap_unordered(_job, jobs, chunksize=4)):
            for r in rows:
                f.write(json.dumps(r, default=float) + "\n")
            if i % 100 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=ROOT).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                                cwd=ROOT).stdout.strip())
    (out / "manifest.json").write_text(json.dumps(
        {"seed_base": SEED_BASE, "seeds": SEEDS, "regimes": REGIMES, "bases": BASES,
         "git_head": sha, "worktree_dirty": dirty, "n_jobs": len(jobs)}, indent=1))


def _tci(x):
    from scipy import stats
    x = np.asarray(x, float)
    n = len(x)
    m, se = x.mean(), x.std(ddof=1) / math.sqrt(n)
    q = stats.t.ppf(0.975, n - 1)
    return {"mean": float(m), "ci95": [float(m - q * se), float(m + q * se)], "n": n}


def analyze(out: Path):
    import pandas as pd

    df = pd.read_json(out / "records.jsonl", lines=True)
    assert (df.path_check.abs() < 1e-9).all(), "deployed path does not reproduce the simulator's loss"
    nev = df[df.policy == NEVER].set_index(["regime", "seed"])
    assert np.allclose(nev.net, nev.j_never), "never-switch net cost != realised incumbent loss"
    res = {"per_regime": {}}
    for (reg, pol), g in df[df.policy != NEVER].groupby(["regime", "policy"]):
        g = g.set_index("seed").sort_index()
        res["per_regime"][f"{reg}|{pol}"] = {
            "H_headroom_vs_never": _tci(g.j_never - g.j_gate),
            "H_loose_no_labels": _tci(g.j_never - (g.j_gate - 0.05 * g.labels)),
            "G_gate_saving_vs_base": _tci(g.net - g.j_gate),
            "base_minus_never": _tci(g.net - g.j_never),
            "H_truth_informed": _tci(-g.exp_rel_gate),
            "base_minus_never_truth": _tci(g.exp_rel_base),
            "mean_net_base": float(g.net.mean()), "mean_net_gate": float(g.j_gate.mean()),
            "mean_net_never": float(g.j_never.mean()),
            "mean_proposals": float(g.n_prop.mean()), "mean_veto_prom": float(g.veto_prom.mean()),
            "mean_veto_roll": float(g.veto_roll.mean()), "mean_labels": float(g.labels.mean()),
        }
    pr = {r: res["per_regime"][f"{r}|{PRIMARY_BASE}"] for r in PRIMARY}
    n_stop = sum(v["H_headroom_vs_never"]["ci95"][1] < MARGIN for v in pr.values())
    n_go = sum(v["H_headroom_vs_never"]["ci95"][0] > MARGIN
               and v["H_truth_informed"]["mean"] > 0 for v in pr.values())
    verdict = "STOP" if n_stop >= 3 else ("CONTINUE" if n_go >= 2 else "INCONCLUSIVE")
    res["decision"] = {"base": PRIMARY_BASE, "margin": MARGIN, "n_regimes_upper_below_margin": n_stop,
                       "n_regimes_lower_above_margin_and_truth_positive": n_go, "verdict": verdict}
    res["manifest"] = json.loads((out / "manifest.json").read_text())
    (ROOT / "docs/sota_fidelity/econ_gate_bound_results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["decision"], indent=1))
    for k, v in res["per_regime"].items():
        h, t = v["H_headroom_vs_never"], v["H_truth_informed"]
        print(f"{k:50s} H={h['mean']:7.2f} [{h['ci95'][0]:7.2f},{h['ci95'][1]:7.2f}]  "
              f"Htruth={t['mean']:7.2f}  gate-save={v['G_gate_saving_vs_base']['mean']:6.2f}  "
              f"base-never={v['base_minus_never']['mean']:6.2f}  vetoP={v['mean_veto_prom']:.2f} "
              f"vetoR={v['mean_veto_roll']:.2f} props={v['mean_proposals']:.2f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run", "analyze"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    run(a.out, a.workers) if a.cmd == "run" else analyze(a.out)


if __name__ == "__main__":
    main()
