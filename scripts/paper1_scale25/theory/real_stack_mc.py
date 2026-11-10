"""Monte Carlo of the REAL search60 stack (compositor + EQSDp/Wald parent + E48 + F60) on the reduced model.

The same generative model as reduced_dp.py / hazard_dp.py (every step a disagreement; delay d, budget B,
price cq, switch cost cs), run through the repository simulator with the repository's own policy classes,
so no controller is re-implemented here. Used to (i) check the table-based controllers of reduced_dp.py
against the real code in the stationary model, and (ii) evaluate the real controllers where E48/F60 are
designed to act: a regime-change (hazard) environment, compared with the exact hazard DP optimum.

Output rows: docs/paper1_scale25/theory/real_stack_mc.csv
"""

from __future__ import annotations

import csv
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
S60 = ROOT / "scripts/paper1_eqsdp/search60"
for p in (
    S60,
    S60.parent,
    ROOT / "scripts/qsg_methods_search",
    ROOT / "scripts/failure_atlas_v2_flq",
):
    sys.path.insert(0, str(p))
OUT = ROOT / (
    "docs/paper1_scale25/theory/real_stack_mc.csv"
    if len(sys.argv) == 1
    else "docs/paper1_scale25/theory/real_stack_mc_extra.csv"
)


def specs(T, lam, gamma, kind, cut_frac, look, hor, hz):
    H = round(cut_frac * T)
    e48 = {"id": "E48", "params": {"arrival_discount": 0.5, "lookahead": look, "hazard": hz}}
    f60 = {"id": "F60", "params": {"bundle": 2, "horizon": hor, "hazard": hz}}
    par = {"kind": kind, "lam": lam, "gamma": gamma, "cutoff": H}
    nocut = {**par, "cutoff": None}
    return {
        "nocut": {"parent": nocut, "modules": []},
        "cut": {"parent": par, "modules": []},
        "cut+E48": {"parent": par, "modules": [e48]},
        "cut+F60": {"parent": par, "modules": [f60]},
        "cut+E48+F60": {"parent": par, "modules": [e48, f60]},
    }


def make_stream(rng, T, env):
    """Per-step probability that the challenger is correct, one path."""
    if env["kind"] == "stationary":
        return (
            np.full(T, rng.beta(1, 1))
            if env.get("prior", "flat") == "flat"
            else np.full(T, rng.choice([env["p_lo"], env["p_hi"]]))
        )
    z = rng.random() < 0.5
    out = np.empty(T)
    for t in range(T):
        out[t] = env["p_hi"] if z else env["p_lo"]
        if rng.random() < env["h"]:
            z = not z
    return out


def job(a):
    import compositor as comp
    from simulator import policy_rng, run_episode

    inst, env, name, spec, seed0, n = a
    T, B, d, cs, cq = inst
    f = comp.make_factory(spec, name)
    nets = []
    for e in range(n):
        rng = np.random.default_rng([seed0, e])  # common random numbers across controllers
        pc = make_stream(rng, T, env)
        l0 = (rng.random(T) < pc).astype(int)
        labels = rng.integers(0, 2, T)
        preds = np.stack([labels ^ l0, labels ^ (1 - l0)], 1)

        def r(nm, _e=e):
            return policy_rng(seed0 + 17, _e, nm)

        pol = f(T, B, cs, cq, 0.05, d, r)
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=labels,
            delay=d,
            budget=B,
            label_price=cq,
            switch_cost=cs,
            trace=False,
        )
        nets.append(res.net_cost)
    return name, env["name"], np.array(nets)


def main(n_ep=6000, chunks=12):
    inst = (160, 24, 8, 2.0, 0.05)
    envs = [
        {"kind": "stationary", "name": "stationary_flat"},
        {"kind": "hazard", "name": "hazard_h0.02", "h": 0.02, "p_lo": 0.35, "p_hi": 0.65},
        {"kind": "hazard", "name": "hazard_h0.05", "h": 0.05, "p_lo": 0.35, "p_hi": 0.65},
        {"kind": "hazard", "name": "hazard_h0.01_strong", "h": 0.01, "p_lo": 0.2, "p_hi": 0.8},
    ]
    if len(sys.argv) > 1:  # run only the named environments (output file gets a suffix)
        envs = [e for e in envs if e["name"] in sys.argv[1:]]
    jobs = []
    for env in envs:
        lam_env = (
            1.0 if env["kind"] == "stationary" else 0.95
        )  # lambda = 1 matches the (k, n) tables exactly
        for kind, lam in (("eqsdp", lam_env), ("wald", lam_env)):
            for nm, sp in specs(inst[0], lam, 0.3, kind, 0.55, 4, 8, 0.025).items():
                for c in range(chunks):
                    jobs.append((inst, env, f"{kind}:{nm}", sp, 1000 + c, n_ep // chunks))
    res: dict = {}
    with ProcessPoolExecutor(max_workers=14) as ex:
        for name, env, nets in ex.map(job, jobs):
            res.setdefault((env, name), []).append(nets)
    rows = []
    for (env, name), L in res.items():
        x = np.concatenate(L)
        parent = np.concatenate(
            res[(env, name.split(":")[0] + ":cut")]
        )  # paired by construction (common random numbers)
        dlt = x - parent
        rows.append(
            {
                "env": env,
                "controller": name,
                "n_episodes": len(x),
                "J_mean": round(x.mean(), 4),
                "J_se": round(x.std(ddof=1) / np.sqrt(len(x)), 4),
                "delta_vs_cut_mean": round(dlt.mean(), 4),
                "delta_vs_cut_se": round(dlt.std(ddof=1) / np.sqrt(len(x)), 4),
            }
        )
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["env"], r["controller"])))
    for r in sorted(rows, key=lambda r: (r["env"], r["controller"])):
        print(r)


if __name__ == "__main__":
    main()
