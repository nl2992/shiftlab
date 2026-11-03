"""Failure Atlas v2 sweep: every competitor x every regime under the v2 contract.

Contract (primary): T=2000, B=200, c_q=.05, c_s=5, alpha=.05, 100 paired seeds. Synthetic seed
``s`` of regime ``R`` draws one loss stream from ``SeedSequence([seed_base, hash(R), s])``; every
policy then replays that same stream with its own private generator, so comparisons are paired on
streams. Real datasets replay cached per-episode loss streams (``data/atlas_v2_losses``); their
seeds vary only the policies' randomness and the balanced label draw.

Usage::

    uv run python scripts/failure_atlas_v2/run_atlas_v2.py --kind synthetic --seeds 100 \
        --seed-base 2026110301 --out outputs/failure_atlas_v2/discovery_synth
    uv run python scripts/failure_atlas_v2/run_atlas_v2.py --kind real --seeds 20 \
        --out outputs/failure_atlas_v2/discovery_real
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from regimes import ALL_REGIMES, REGIMES, T, expected_oracle_path, hindsight_oracle_cost  # noqa: E402
from suite import build_suite, run_metrics  # noqa: E402

ROOT = HERE.parents[1]
LOSS_DIR = ROOT / "data/atlas_v2_losses"
REAL_DELAYS = {"rialto": 100, "spam": 50, "weather": 1, "openml_ldpa": 100, "uci_occupancy": 100,
               "airlines": 100, "bank": 100, "elec2": 48, "criteo": 100}
CFG = dict(budget=200, cq=0.05, cs=5.0, alpha=0.05)


def _h(s: str) -> int:
    return int.from_bytes(hashlib.sha256(s.encode()).digest()[:4], "big")


def _job(args):
    kind, name, ep, seed, seed_base, names, extra_mod, cfg = args
    CFG.update(cfg)
    extra = None
    if extra_mod:
        import importlib

        extra = importlib.import_module(extra_mod).EXTRA
    if kind == "synthetic":
        R = ALL_REGIMES[name]
        stream_ss = np.random.SeedSequence([seed_base, _h(name), seed])
        losses = R.sample(np.random.default_rng(stream_ss))
        gain, delay = R.truth_gain(), R.delay
    else:
        z = np.load(LOSS_DIR / f"{name}.npz")
        losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
        # real data: no causal truth; use the episode's realised mean advantage as a constant
        # evaluator-side descriptor (not a change-point label)
        gain = np.full(losses.shape[0], float((losses[:, 0].astype(int) - losses[:, 1]).mean()))
        delay = REAL_DELAYS[name]
    oc = hindsight_oracle_cost(losses, CFG["cs"])
    ep_path = expected_oracle_path(gain, CFG["cs"])
    rows = []
    run_ep = ep * 100_000 + seed
    for pol in build_suite(losses.shape[0], CFG["budget"], CFG["cs"], CFG["cq"], CFG["alpha"],
                           delay, run_ep, seed_base + _h(name) % 1000, names=names, extra=extra):
        stream_rng = np.random.default_rng([seed_base, _h(name), ep, seed, 7])
        m = run_metrics(pol, losses, gain, delay=delay, budget=CFG["budget"], cq=CFG["cq"],
                        cs=CFG["cs"], stream_rng=stream_rng, oracle_cost=oc, exp_path=ep_path)
        rows.append({"kind": kind, "regime": name, "ep": ep, "seed": seed, "policy": pol.name,
                     "delay": delay, **m})
    return rows


def jobs_for(kind, seeds, seed_base, regimes, names, extra_mod, cfg):
    out = []
    if kind == "synthetic":
        for r in regimes or REGIMES:
            out += [(kind, r, 0, s, seed_base, names, extra_mod, cfg) for s in range(seeds)]
    else:
        for r in regimes or REAL_DELAYS:
            K = np.load(LOSS_DIR / f"{r}.npz")["l0"].shape[0]
            out += [(kind, r, e, s, seed_base, names, extra_mod, cfg)
                    for e in range(K) for s in range(seeds)]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kind", choices=("synthetic", "real"), required=True)
    ap.add_argument("--seeds", type=int, default=100)
    ap.add_argument("--seed-base", type=int, default=2026110301)
    ap.add_argument("--regimes", default="")
    ap.add_argument("--policies", default="")
    ap.add_argument("--extra", default="", help="module exposing EXTRA = {name: factory}")
    ap.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--cs", type=float, default=5.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    CFG["budget"], CFG["cs"] = a.budget, a.cs
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    regimes = [x for x in a.regimes.split(",") if x]
    names = [x for x in a.policies.split(",") if x] or None
    jobs = jobs_for(a.kind, a.seeds, a.seed_base, regimes, names, a.extra or None, dict(CFG))
    t0 = time.time()
    n = 0
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for rows in pool.imap_unordered(_job, jobs, chunksize=4):
            for r in rows:
                f.write(json.dumps(r) + "\n")
            n += 1
            if n % 200 == 0:
                print(f"{n}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
    manifest = {"argv": vars(a), "config": CFG, "T": T, "n_jobs": len(jobs),
                "seconds": round(time.time() - t0, 1)}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"done {len(jobs)} jobs in {time.time() - t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
