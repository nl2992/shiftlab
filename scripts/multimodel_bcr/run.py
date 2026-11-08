"""BCR pilot runner: envs x seeds x policies on the shared simulator (paired streams).

usage: python run.py --envs E1_persist,... --seeds 40 --seed-base 2026111101 --out DIR [--policies a,b]
Per (env, seed) the stream is drawn once and replayed for every policy; each policy has its own
RNG (simulator.policy_rng). Records: net cost, loss, labels, switches, expected-oracle regret,
fraction of events on the expected-best model, and post-change decision delay.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "scripts/promising_directions/sota"))

B, CS, CQ = 200, 5.0, 0.05


def _h(s):
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big")


def job(args):
    env_name, seed, seed_base, names, B, CQ = args
    from envs import ENVS, oracle_cost
    from policies import registry
    from simulator import policy_rng, run_episode

    env = ENVS[env_name]
    rng = np.random.default_rng([seed_base, _h(env_name), seed])
    preds, y, x = env.sample(rng)
    el = env.expected_loss()
    orc = oracle_cost(el, CS)
    best = el.argmin(0)
    reg = registry()
    rows = []
    for nm in names:
        pol = reg[nm](
            len(y), B, CS, env.K, policy_rng(seed_base, seed * 1000 + _h(env_name) % 997, nm)
        )
        res = run_episode(
            pol,
            model_predictions=preds,
            labels=y,
            delay=env.delay,
            budget=B,
            label_price=CQ,
            switch_cost=CS,
            contexts=x,
            trace=True,
        )
        dep = np.array([r["deployed_model"] for r in res.records])
        exp_cost = (
            el[dep, np.arange(len(dep))].sum()
            + CQ * res.requested_labels
            + CS * res.deployment_switches
        )
        rows.append(
            {
                "env": env_name,
                "seed": seed,
                "policy": nm,
                "net": res.net_cost,
                "labels": res.requested_labels,
                "switches": res.deployment_switches,
                "exp_cost": float(exp_cost),
                "regret": float(exp_cost - orc),
                "frac_best": float((dep == best).mean()),
                "B": B,
                "cq": CQ,
            }
        )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--envs", required=True)
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--seed-base", type=int, required=True)
    ap.add_argument("--policies", default="")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--out", required=True)
    ap.add_argument("--budget", type=int, default=B)
    ap.add_argument("--cq", type=float, default=CQ)
    a = ap.parse_args()
    from policies import registry

    names = a.policies.split(",") if a.policies else list(registry())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = [
        (e, s, a.seed_base, names, a.budget, a.cq)
        for e in a.envs.split(",")
        for s in range(a.seeds)
    ]
    (out / "manifest.json").write_text(json.dumps({**vars(a), "n_policies": len(names)}, indent=1))
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for rows in pool.imap_unordered(job, jobs):
            f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"done {len(jobs)} jobs -> {out}", flush=True)


if __name__ == "__main__":
    main()
