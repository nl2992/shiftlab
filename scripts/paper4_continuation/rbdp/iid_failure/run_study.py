"""Main study (PROTOCOL.md). Usage:
    PYTHONPATH=src python run_study.py [--extra-chains extra.json] [--workers 6] [--synthetic-only|--real-only]
extra.json: list of {"id": str, "solver_params": {t01,t10,e0,e1,prior1}, "stream": "<path to stream.csv, optional>"}.
Outputs (results/): settings.jsonl, skipped.jsonl, shuffle_fits.json. Resumable (settings keyed by setting id).
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
OUT = os.path.join(ROOT, "docs/paper4_continuation/rbdp/iid_failure/results")
RD = os.path.join(ROOT, "docs/paper4_continuation/rbdp/real_data/results")
RAW = os.path.join(ROOT, "data/raw/real_chains")

ALPHAS, BS, TS, E0S = (0.05, 0.1), (2, 3, 4), (12, 20), (0.1, 0.2)
ANTI, PERS = (0.6, 0.75, 0.9), (0.1, 0.25)
REAL = ["c01_faithful", "p23_faithful_waiting", "p24_geyser_waiting"]
N_SHUF, SHUF_SEED0 = 5, 20261117


def chain_type(t01, t10):
    lam = 1.0 - t01 - t10
    return "anti-persistent" if lam < -1e-9 else ("persistent" if lam > 1e-9 else "neutral")


def synthetic_chains():
    out = []
    for grp, vals in (("anti", ANTI), ("pers", PERS)):
        for t01, t10 in itertools.product(vals, vals):
            for e0 in E0S:
                out.append(dict(group="synthetic", chain_id=f"syn_{grp}_t01={t01}_t10={t10}_e0={e0}", t01=t01, t10=t10,
                                e0=e0, e1=1 - e0, prior1=t01 / (t01 + t10)))
    return out


def real_chains(extra):
    out = []
    for cid in REAL:
        sp = json.load(open(os.path.join(RD, cid + ".json")))["solver_params"]
        out.append(dict(group="real", chain_id=cid, stream=os.path.join(RAW, cid, "stream.csv"), **sp))
    for e in extra:
        out.append(dict(group="real", chain_id=e["id"], stream=e.get("stream"), **e["solver_params"]))
    return out


def fit_shuffles(real):
    """5 time-shuffles per real chain, refit with real_data/fit.py fit_hmm (imported unchanged)."""
    sys.path.insert(0, os.path.join(ROOT, "scripts/paper4_continuation/rbdp/real_data"))
    from fit import fit_hmm, solver_params

    path = os.path.join(OUT, "shuffle_fits.json")
    cache = json.load(open(path)) if os.path.exists(path) else {}
    for ch in real:
        if not ch.get("stream"):
            continue
        x = np.loadtxt(ch["stream"], skiprows=1, dtype=int)
        for k in range(N_SHUF):
            key = f"{ch['chain_id']}__shuf{k}"
            if key in cache:
                continue
            seed = SHUF_SEED0 + k
            xp = np.random.default_rng(seed).permutation(x)
            t0 = time.time()
            f = fit_hmm(xp)
            cache[key] = dict(chain_id=key, parent=ch["chain_id"], shuffle_seed=seed, n=int(len(x)), fit=f,
                              solver_params=solver_params(f), fit_time_s=time.time() - t0)
            json.dump(cache, open(path, "w"), indent=1)
            print("fit", key, cache[key]["solver_params"], f"{time.time()-t0:.1f}s", flush=True)
    return cache


def shuffled_chains(cache):
    out, skipped = [], []
    for key, v in cache.items():
        sp = v["solver_params"]
        if not (0 < sp["e0"] < 0.5 < sp["e1"] < 1):
            skipped.append(dict(chain_id=key, reason="refit emissions do not straddle 1/2; solver requires it", solver_params=sp))
            continue
        out.append(dict(group="shuffled", chain_id=key, parent=v["parent"], shuffle_seed=v["shuffle_seed"], **sp))
    return out, skipped


def tasks_for(chains):
    tasks = []
    for ch in chains:
        for alpha, B, T in itertools.product(ALPHAS, BS, TS):
            sid = f"{ch['chain_id']}|a={alpha}|B={B}|T={T}"
            tasks.append((sid, ch, alpha, B, T))
    return tasks


def work(task):
    sid, ch, alpha, B, T = task
    from iidlib import Chain
    from runner import run_setting

    t0 = time.time()
    c = Chain(ch["t01"], ch["t10"], ch["e0"], ch["e1"], ch["prior1"], T, B)
    tag = dict(setting_id=sid, group=ch["group"], chain_id=ch["chain_id"], parent=ch.get("parent"),
               t01=ch["t01"], t10=ch["t10"], e0=ch["e0"], e1=ch["e1"], prior1=ch["prior1"],
               lam=1.0 - ch["t01"] - ch["t10"], chain_type=chain_type(ch["t01"], ch["t10"]))
    try:
        rows = run_setting(c, alpha, tag)
        for r in rows:
            r["setting_time_s"] = time.time() - t0
        return sid, rows, None
    except Exception as e:  # report, never hide
        import traceback

        return sid, None, traceback.format_exc()[-1500:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--extra-chains")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--synthetic-only", action="store_true")
    ap.add_argument("--real-only", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    extra = json.load(open(a.extra_chains)) if a.extra_chains else []
    chains = []
    skipped = []
    if not a.real_only:
        chains += synthetic_chains()
    if not a.synthetic_only:
        real = real_chains(extra)
        chains += real
        shuf, skipped = shuffled_chains(fit_shuffles(real))
        chains += shuf
    tasks = tasks_for(chains)
    path = os.path.join(OUT, "settings.jsonl")
    done = set()
    if os.path.exists(path):
        done = {json.loads(l)["setting_id"] for l in open(path)}
    todo = [t for t in tasks if t[0] not in done]
    print(f"{len(tasks)} settings, {len(todo)} to run", flush=True)
    json.dump(skipped, open(os.path.join(OUT, "skipped.jsonl"), "w"), indent=1)
    import multiprocessing as mp

    t0 = time.time()
    n = 0
    with mp.Pool(a.workers) as pool, open(path, "a") as fh, open(os.path.join(OUT, "errors.log"), "a") as eh:
        for sid, rows, err in pool.imap_unordered(work, todo, chunksize=1):
            n += 1
            if err:
                eh.write(json.dumps(dict(setting_id=sid, error=err)) + "\n")
                eh.flush()
            else:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
                fh.flush()
            if n % 10 == 0:
                print(f"{n}/{len(todo)} {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
