"""Failure Atlas v2: run the competitor suite over synthetic regimes and/or real loss streams.

Contract (v2 primary): T=2000, B=200, c_q=.05, c_s=5, alpha=.05, 100 paired seeds. Each seed is
one sampled stream (synthetic) or one (episode, seed) replay (real); every policy faces the same
stream and draws from its own private generator, so differences are paired.

Writes one JSONL row per (source, episode, seed, policy) to ``--out``/records.jsonl and a
manifest with code hashes. Raw outputs go under ``outputs/`` (git-ignored); summaries are made by
``summarise_atlas_v2.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from regimes import REGIMES, VALIDATION_REGIMES, expected_oracle_path, hindsight_oracle_cost  # noqa: E402
from suite import ROOT, build_suite, run_metrics  # noqa: E402

REAL_DELAYS = {"rialto": 100, "spam": 50, "weather": 1, "openml_ldpa": 100,
               "uci_occupancy": 100, "airlines": 100, "bank": 100, "elec2": 48, "criteo": 100}
LOSS_ROOT = ROOT / "data/atlas_v2_losses"
EXTRA_FACTORIES: dict = {}  # name -> factory(T, B, cs, cq, alpha, delay, rng_fn); set by importers


def _job(args):
    (kind, src, ep, seeds, cfg, names, extra_mod) = args
    extra = None
    if extra_mod:
        import importlib
        extra = importlib.import_module(extra_mod).FACTORIES
    rows = []
    for s in seeds:
        if kind == "syn":
            R = {**REGIMES, **VALIDATION_REGIMES}[src]
            rng = np.random.default_rng([cfg["seed_base"], s, int(hashlib.sha256(src.encode()).hexdigest()[:8], 16)])
            losses = R.sample(rng)
            gain = R.truth_gain()
            delay = cfg.get("delay_override") or R.delay
            ekey = s
        else:
            z = np.load(LOSS_ROOT / f"{src}.npz")
            losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1)
            # real streams: no causal truth; use the episode's own mean difference as the
            # evaluator-side descriptive gain (constant), never shown to a policy
            gain = np.full(losses.shape[0], float((losses[:, 0] - losses[:, 1]).mean()))
            delay = REAL_DELAYS.get(src, 100)
            ekey = ep * 10_000 + s
        oc = hindsight_oracle_cost(losses, cfg["cs"])
        ep_path = expected_oracle_path(gain, cfg["cs"])
        T = losses.shape[0]
        for pol in build_suite(T, cfg["budget"], cfg["cs"], cfg["cq"], cfg["alpha"], delay, ekey,
                               cfg["seed_base"], names=names, extra=extra):
            m = run_metrics(pol, losses, gain, delay=delay, budget=cfg["budget"], cq=cfg["cq"],
                            cs=cfg["cs"], stream_rng=np.random.default_rng([cfg["seed_base"], ekey, 7]),
                            oracle_cost=oc, exp_path=ep_path)
            rows.append({"source": src, "kind": kind, "episode": ep, "seed": s,
                         "policy": pol.name, "delay": delay, **m})
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--regimes", default="all")
    ap.add_argument("--real", default="")
    ap.add_argument("--n-seeds", type=int, default=100)
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--real-seeds", type=int, default=20)
    ap.add_argument("--seed-base", type=int, default=20261103)
    ap.add_argument("--budget", type=int, default=200)
    ap.add_argument("--cq", type=float, default=0.05)
    ap.add_argument("--cs", type=float, default=5.0)
    ap.add_argument("--alpha", type=float, default=0.05)
    ap.add_argument("--policies", default="")
    ap.add_argument("--extra-module", default="", help="module exposing FACTORIES for new policies")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    cfg = {k: getattr(a, k) for k in ("budget", "cq", "cs", "alpha", "seed_base")}
    names = [x for x in a.policies.split(",") if x] or None
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    seeds = list(range(a.seed_offset, a.seed_offset + a.n_seeds))
    jobs = []
    named = {"none": [], "all": list(REGIMES), "validation": list(VALIDATION_REGIMES)}
    regs = named.get(a.regimes, a.regimes.split(","))
    for r in regs:
        for chunk in np.array_split(seeds, max(1, len(seeds) // 10)):
            jobs.append(("syn", r, 0, [int(x) for x in chunk], cfg, names, a.extra_module))
    for src in [x for x in a.real.split(",") if x]:
        K = np.load(LOSS_ROOT / f"{src}.npz")["l0"].shape[0]
        rs = list(range(a.seed_offset, a.seed_offset + a.real_seeds))
        for ep in range(K):
            jobs.append(("real", src, ep, rs, cfg, names, a.extra_module))

    code = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(HERE.glob("*.py"))}
    data = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(LOSS_ROOT.glob("*.npz"))}
    manifest = {"config": cfg, "seeds": [seeds[0], seeds[-1]], "regimes": regs, "real": a.real,
                "real_seeds": a.real_seeds, "policies": names, "extra_module": a.extra_module,
                "code_sha256": code, "data_sha256": data,
                "started": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    t0 = time.time()
    n = 0
    with open(out / "records.jsonl", "w") as fh, ProcessPoolExecutor(a.workers) as ex:
        for rows in ex.map(_job, jobs, chunksize=1):
            for row in rows:
                fh.write(json.dumps(row) + "\n")
            n += 1
            if n % 20 == 0:
                print(f"{n}/{len(jobs)} jobs, {time.time() - t0:.0f}s", flush=True)
    manifest["seconds"] = round(time.time() - t0, 1)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"done {len(jobs)} jobs in {manifest['seconds']}s -> {out}")


if __name__ == "__main__":
    main()
