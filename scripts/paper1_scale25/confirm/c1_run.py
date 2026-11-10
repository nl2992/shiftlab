"""Protocol C1 policy runner (docs/paper1_scale25/07a_PROTOCOL_C1_V1_22.md section 4).

    python c1_run.py --reg REG.json --root ROOT --out DIR [--parts core,panel,cut,ports]
                     [--workers 8] [--seeds 10] [--only ds ...] [--max-ep N]

One sealed array per dataset; sha256 of l0+l1+starts is verified against the registration before any
policy runs. Rows are the eval60/trace_run rows (same rng derivation as sota_nine). Resumable at
(dataset, episode, seed) level. Progress: DIR/progress.txt (mtime watched by c1_watch.py).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/paper1_eqsdp"))
sys.path.insert(0, str(ROOT / "scripts/paper1_eqsdp/search60"))
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/algo"))

import c1_registry as c1r  # patches trace_run.registry
import compositor as comp
import eval60 as e60
import numpy as np
import run_phase12 as r12
import stage2_eval as ev

EQ_PAIR, W_PAIR = "P2_K2__E48_F60", "P4W__P2_K2__E48_F60"
EQ_CUT, W_CUT, ARM_R = "s2armr_H1100", "s2wald_l0.98_g0.3_H1100", "EQSDp_l0.98_g0.3"
WALD_PARENT = {"kind": "wald", "lam": 0.98, "gamma": 0.3, "cutoff": 1100}


def pair_specs():
    mods = [r12.mod_spec("E48", 0), r12.mod_spec("F60", 0)]
    return [
        {"modules": mods, "name": EQ_PAIR},
        {"modules": mods, "name": W_PAIR, "parent": WALD_PARENT},
    ]


def policy_names(parts):
    names = []
    if "core" in parts:
        names += [EQ_CUT, W_CUT, ARM_R]
    if "panel" in parts:
        names += c1r.SOTA
    if "cut" in parts:
        names += c1r.CUT_NAMES
    if "ports" in parts:
        names += c1r.PORT_NAMES
    return names


def sealed_from_reg(reg_path, root, only=None):
    reg = json.loads(Path(reg_path).read_text(encoding="utf-8"))
    out, sb = {}, reg["seed_base"]
    for d in reg["datasets"]:
        if not d.get("eligibility", {}).get("eligible", d.get("eligible", True)):
            continue
        if only and d["name"] not in only:
            continue
        p = Path(root) / d["sealed_path"]
        z = np.load(p)
        h = hashlib.sha256(z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes())
        if h.hexdigest() != d["array_content_sha256"]:
            raise SystemExit(f"checksum mismatch for {d['name']}")
        assert int(z["l0"].shape[0]) == d["episodes"], d["name"]
        out[d["name"]] = (str(p), int(z["delay"]), sb, d["episodes"])
    return out


def _init():
    ev._warm()
    import c1_registry  # noqa: F401
    import s25_modules  # noqa: F401  (compositor modules used by the pair specs)


def _job(a):
    return e60._job(a)


def read_done(f, n_pol):
    seen = {}
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            seen.setdefault((r["ep"], r["seed"]), set()).add(r["config_id"])
    return {k for k, v in seen.items() if len(v) >= n_pol}


def run_dataset(ds, info, specs, extra, out, seeds, workers, sha, log):
    path, delay, sb, n_ep = info
    d = out / ds
    d.mkdir(parents=True, exist_ok=True)
    if (d / "DONE").exists():
        log(f"{ds}: DONE already")
        return
    names = [comp.config_id(s) for s in specs] + list(extra)
    reg = {comp.config_id(s): s for s in specs}
    key = hashlib.sha256(json.dumps(reg, sort_keys=True, default=str).encode()).hexdigest()
    done = read_done(d / "records.jsonl", len(names))
    todo = [(e, s) for e in range(n_ep) for s in seeds if (e, s) not in done]
    jobs = [((ds, path, delay, e, s, sb, names, 200, ()), reg, key) for e, s in todo]
    (d / "meta.json").write_text(
        json.dumps({"sha": sha, "seed_base": sb, "policies": names, "episodes": n_ep,
                    "seeds": list(seeds), "n_jobs_total": n_ep * len(seeds)}, indent=1)
    )  # fmt: skip
    log(f"{ds}: {len(jobs)} jobs to run ({len(done)} done) x {len(names)} policies")
    t0 = time.perf_counter()
    if jobs:
        pool = mp.Pool(workers, initializer=_init)
        try:
            with open(d / "records.jsonl", "a", encoding="utf-8") as f:
                for i, rs in enumerate(pool.imap_unordered(_job, jobs, chunksize=2)):
                    for r in rs:
                        rec = {k: r[k] for k in e60.KEEP if k in r}
                        rec |= {"config_id": r["policy"], "sha": sha}
                        f.write(json.dumps(rec) + "\n")
                    if i % 20 == 0:
                        f.flush()
                        (out / "progress.txt").write_text(f"{ds} {i + 1}/{len(jobs)}")
        finally:
            pool.terminate()
    n_done = len(read_done(d / "records.jsonl", len(names)))
    assert n_done == n_ep * len(seeds), (ds, n_done, n_ep * len(seeds))
    (d / "DONE").write_text(f"ok {time.perf_counter() - t0:.0f}s")
    (out / "progress.txt").write_text(f"{ds} done")
    log(f"{ds}: finished in {time.perf_counter() - t0:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reg", required=True)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--out", required=True)
    ap.add_argument("--parts", default="core,panel,cut,ports")
    ap.add_argument("--no-pairs", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--max-ep", type=int, help="smoke: only the first N episodes")
    a = ap.parse_args()
    parts = a.parts.split(",")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    sealed = sealed_from_reg(a.reg, a.root, a.only)
    (out / "checksums_ok.json").write_text(json.dumps({k: True for k in sealed}))
    specs = [] if a.no_pairs else pair_specs()
    extra = policy_names(parts)
    comp.register_specs(specs)
    sha = e60.code_sha()
    (out / "policies.txt").write_text("\n".join([comp.config_id(s) for s in specs] + extra))

    def log(m):
        line = f"{time.strftime('%H:%M:%S')} {m}"
        print(line, flush=True)
        with open(out / "run.log", "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    for ds, info in sealed.items():
        if a.max_ep:
            info = (*info[:3], min(a.max_ep, info[3]))
        run_dataset(ds, info, specs, extra, out, tuple(range(a.seeds)), a.workers, sha, log)
    (out / "DONE").write_text("ok")
    log("ALL DONE")


if __name__ == "__main__":
    main()
