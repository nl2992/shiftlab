"""Evaluation runner for the Paper 1 60-module search.

Reuses the stage-2/stage-5 machinery (``stage2_eval._warm``, ``trace_run.job`` decomposition rows,
sealed per-dataset arrays with checksum validation). Episode index keeps its place in the seed
derivation, so an episode has the same seeds in any subset.

    python eval60.py --specs specs.json --split odd --n-eps 4 --seeds 2 --workers 16 --out DIR
    python eval60.py --controls --split odd ...            # matched references only

A specs file is a JSON list (or JSONL) of
    {"modules": [{"id": "A01", "setting": 1, "params": {...}}, ...], "parent": {"kind": "eqsdp"}}
or of catalogue-manifest rows ({"combo_id": ..., "modules": ["A01", "B13"]}; ``--setting`` picks the
parameter preset, ``--wald-parent`` re-targets every spec to the Wald parent). Unsupported
combinations are written to ``status.jsonl`` as UNSUPPORTED_COMBO / NOT_IMPLEMENTED, never dropped.

Output: <out>/records.jsonl (one row per stream, ep, seed, config_id), meta.json, status.jsonl.
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compositor as comp
import numpy as np
import stage2_eval as ev
import trace_run as tr

ROOT = HERE.parents[2]
CONTROLS = [
    "s2armr_H1100",
    "s2wald_l0.98_g0.3_H1100",
    "s2wald_l0.97_g0.2_H1100",
    "EQSDp_l0.98_g0.3",  # arm R without cutoff
    "wald_l0.97_g0.2",  # Wald without cutoff
]
KEEP = ["stream", "ep", "seed", "config_id", "net", "loss", "labels", "switches", "late_adoption",
        "false_promotion", "reversal_churn", "label_spend", "residual", "regret", "first_deploy",
        "better", "secs"]  # fmt: skip


def code_sha() -> str:
    def git(*args):
        return subprocess.run(
            ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
        ).stdout.strip()

    try:
        sha = git("rev-parse", "HEAD")
        return sha + ("+dirty" if git("status", "--porcelain", "--", "scripts") else "")
    except OSError:
        return "unknown"


def load_specs(path, setting=None, wald_parent=False) -> list[dict]:
    txt = Path(path).read_text(encoding="utf-8").strip()
    rows = (
        json.loads(txt) if txt.startswith("[") else [json.loads(x) for x in txt.splitlines() if x]
    )
    out = []
    for r in rows:
        s = dict(r)
        s["modules"] = [
            ({"id": m} if isinstance(m, str) else dict(m)) for m in r.get("modules", [])
        ]
        if setting is not None:
            for m in s["modules"]:
                m.setdefault("setting", setting)
        if wald_parent:
            s["parent"] = {**s.get("parent", {}), "kind": "wald"}
        if "combo_id" in s and "name" not in s:
            s["name"] = s["combo_id"] + ("__W" if wald_parent else "")
        out.append(s)
    return out


def select_episodes(split, episodes=None, n_sub=None):
    """Return {dataset: [episode indices]}; ``episodes`` {dataset: [...]} overrides the split."""
    out = {}
    for ds, (p, _, _) in tr.sealed_paths().items():
        n = int(np.load(p)["l0"].shape[0])
        if episodes is not None:
            eps = [e for e in episodes.get(ds, []) if 0 <= e < n]
        else:
            eps = list(range({"even": 0, "odd": 1, "all": 0}[split], n, 1 if split == "all" else 2))
        if n_sub and len(eps) > n_sub:
            idx = np.unique(np.linspace(0, len(eps) - 1, n_sub).round().astype(int))
            eps = [eps[i] for i in idx]
        out[ds] = eps
    return out


def make_jobs(names, episodes, seeds, budget=200, datasets=None):
    jobs = []
    for ds, (p, delay, sb) in tr.sealed_paths().items():
        if datasets and ds not in datasets:
            continue
        jobs += [(ds, p, delay, e, s, sb, list(names), budget, ())
                 for e in episodes.get(ds, []) for s in seeds]  # fmt: skip
    return jobs


def _job(args):
    base, specs = args
    comp.register_specs(list(specs.values()))
    return tr.job(base)


def run_eval(specs, out: Path, split="odd", episodes=None, n_sub=None, seeds=(0, 1), workers=8,
             controls=False, budget=200, datasets=None, extra_names=()):  # fmt: skip
    """Run specs (+ controls) and write records.jsonl; returns the list of rows."""
    out.mkdir(parents=True, exist_ok=True)
    ok, status = [], []
    for s in specs:
        cid = comp.config_id(s)
        try:
            comp.validate_spec(s)
            ok.append(s)
            status.append({"config_id": cid, "status": "OK"})
        except (comp.UnsupportedCombo, comp.NotImplementedModule) as e:
            status.append({"config_id": cid, "status": e.status, "reason": str(e)})
    names = [comp.config_id(s) for s in ok] + (CONTROLS if controls else []) + list(extra_names)
    sha = code_sha()
    eps = select_episodes(split, episodes, n_sub)
    jobs = make_jobs(names, eps, seeds, budget, datasets)
    (out / "status.jsonl").write_text("\n".join(json.dumps(x) for x in status) + "\n")
    (out / "meta.json").write_text(json.dumps({
        "sha": sha, "split": split, "n_sub": n_sub, "seeds": list(seeds), "budget": budget,
        "policies": names, "specs": {comp.config_id(s): s for s in ok}, "jobs": len(jobs),
        "episodes": eps if episodes is not None or n_sub else "all-of-split"}, indent=1,
        default=str))  # fmt: skip
    reg = {comp.config_id(s): s for s in ok}
    jobs = [(j, reg) for j in jobs]
    rows = []
    t0 = time.perf_counter()
    with open(out / "records.jsonl", "w") as f:
        if workers <= 1:
            it = map(_job, jobs)
            pool = None
        else:
            pool = mp.Pool(min(workers, 16), initializer=ev._warm)
            it = pool.imap_unordered(_job, jobs, chunksize=2)
        for i, rs in enumerate(it):
            for r in rs:
                rec = {k: r[k] for k in KEEP if k in r} | {"config_id": r["policy"], "sha": sha}
                rows.append(rec)
                f.write(json.dumps(rec) + "\n")
            if i % 50 == 0:
                f.flush()
                (out / "progress.txt").write_text(f"{i + 1}/{len(jobs)}")
        if pool:
            pool.close()
            pool.join()
    (out / "progress.txt").write_text(
        f"done {len(jobs)}/{len(jobs)} in {time.perf_counter() - t0:.0f}s"
    )
    return rows


def trace_episode(spec, dataset, ep, seed, log=2):
    """Diagnostic: run one spec on one (dataset, ep, seed) with the per-event log; returns
    (summary row, log records). Same rng derivation as trace_run.run_policies."""
    import hashlib

    import c4_pilot
    from suite import build_suite, run_episode, stream_from_losses

    spec = {**spec, "log": log}
    name = comp.config_id(spec)
    comp.register_specs([spec])
    p, delay, sb = tr.sealed_paths()[dataset]
    z = np.load(p)
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    cfg = c4_pilot.CFG
    h = int.from_bytes(hashlib.sha256(dataset.encode()).digest()[:4], "big")
    T = losses.shape[0]
    (pol,) = build_suite(T, 200, cfg["cs"], cfg["cq"], cfg["alpha"], delay, ep * 100_000 + seed,
                         sb + h % 1000, names=[name], extra=tr.registry())  # fmt: skip
    rng = np.random.default_rng([sb, h, ep, seed, 7])
    preds, labels = stream_from_losses(losses, rng)
    res = run_episode(pol, model_predictions=preds, labels=labels, delay=delay, budget=200,
                      label_price=cfg["cq"], switch_cost=cfg["cs"], trace=True)  # fmt: skip
    dep = np.fromiter((r["deployed_model"] for r in res.records), int, T)
    summ = {"stream": dataset, "ep": ep, "seed": seed, "config_id": name, "net": res.net_cost,
            "loss": res.prediction_loss, "labels": res.requested_labels,
            "switches": res.deployment_switches,
            "first_deploy": int(np.argmax(dep == 1)) if (dep == 1).any() else -1}  # fmt: skip
    return summ, pol.log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--specs")
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", default="odd", choices=["even", "odd", "all"])
    ap.add_argument("--episodes", help='JSON {"kc_311": [37, 39]}')
    ap.add_argument("--n-eps", type=int, help="evenly spaced subset per dataset")
    ap.add_argument("--seeds", type=int, default=2, help="first N of the 10 policy seeds")
    ap.add_argument("--datasets", nargs="*")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--controls", action="store_true")
    ap.add_argument("--setting", type=int, choices=[0, 1])
    ap.add_argument("--wald-parent", action="store_true")
    a = ap.parse_args()
    specs = load_specs(a.specs, a.setting, a.wald_parent) if a.specs else []
    run_eval(specs, Path(a.out), a.split, json.loads(a.episodes) if a.episodes else None, a.n_eps,
             tuple(range(a.seeds)), a.workers, a.controls, datasets=a.datasets)  # fmt: skip


if __name__ == "__main__":
    main()
