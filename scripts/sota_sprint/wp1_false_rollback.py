#!/usr/bin/env python3
"""Replay WP1 E_rb policies with traces and classify rollbacks against frozen segment means.

This evaluator-side diagnostic uses the already frozen outcome-blind WP1 classifier and the
registered primary-run seed/stream contract. It does not alter the policy or primary results.
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
ROOT = HERE.parents[1]
for path in (ROOT / "scripts/failure_atlas_v2_flq", HERE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

POLICIES = ["E_rb:gated_deployment", "E_rb:discern_style",
            "E_rb:SMCS+retain-incumbent", "E_rb:gated_adaptive_range"]
CLASSES = ROOT / "outputs/sprint2/WP1/classes.json"
PRIMARY = ROOT / "outputs/sprint2/WP1/primary/manifest.json"


def _h(value: str) -> int:
    return int.from_bytes(hashlib.sha256(value.encode()).digest()[:4], "big")


def _job(args):
    stream, ep, seed, seed_base, alpha, delay, budget, cs, file_path, cluster, c = args
    import screen
    from registry import EXTRA
    from simulator import run_episode
    from suite import build_suite, stream_from_losses

    z = np.load(file_path)
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    t = np.arange(len(losses))
    gain = np.where(t < c["tau"], c["m1"], c["m2"])
    run_ep = ep * 100_000 + seed
    rows = []
    for policy in build_suite(len(losses), budget, cs, screen.CONTRACT["cq"], alpha, delay,
                              run_ep, seed_base + _h(stream) % 1000, names=POLICIES, extra=EXTRA):
        rng = np.random.default_rng([seed_base, _h(stream), ep, seed, 7])
        preds, labels = stream_from_losses(losses, rng)
        result = run_episode(policy, model_predictions=preds, labels=labels, delay=delay,
                             budget=budget, label_price=screen.CONTRACT["cq"], switch_cost=cs,
                             trace=True)
        deployed = np.fromiter((r["deployed_model"] for r in result.records), dtype=int)
        changes = np.diff(np.r_[0, deployed])
        times = np.flatnonzero(changes == -1)
        events = [{"t": int(i), "segment_mean_gain": float(gain[i]),
                   "false_rollback": bool(gain[i] >= 0)} for i in times]
        rows.append({"stream": stream, "cluster": cluster, "ep": ep, "class": c["class"],
                     "seed": seed, "policy": policy.name, "rollback_events": events,
                     "n_rollbacks": len(events), "false_rollbacks": sum(x["false_rollback"] for x in events),
                     "correct_rollbacks": sum(not x["false_rollback"] for x in events)})
    return rows


def _summarize(rows, n_boot=5000, seed=20261104):
    rng = np.random.default_rng(seed)
    result = {}
    keys = sorted({(r["policy"], r["class"]) for r in rows})
    for policy, cls in keys:
        selected = [r for r in rows if r["policy"] == policy and r["class"] == cls]
        clusters = sorted({r["cluster"] for r in selected})
        false_n = sum(r["false_rollbacks"] for r in selected)
        total = sum(r["n_rollbacks"] for r in selected)
        per_cluster = {cl: (sum(r["false_rollbacks"] for r in selected if r["cluster"] == cl),
                            sum(r["n_rollbacks"] for r in selected if r["cluster"] == cl)) for cl in clusters}
        draws = []
        if total:
            for _ in range(n_boot):
                sampled = rng.choice(clusters, len(clusters), replace=True)
                f = sum(per_cluster[x][0] for x in sampled)
                n = sum(per_cluster[x][1] for x in sampled)
                if n:
                    draws.append(f / n)
        result[f"{policy}|{cls}"] = {
            "false_rollbacks": false_n, "rollbacks": total,
            "false_rate": (false_n / total if total else None),
            "cluster_bootstrap_95ci": ([float(np.quantile(draws, .025)), float(np.quantile(draws, .975))]
                                        if draws else None),
            "episodes": len({(r["stream"], r["ep"]) for r in selected}),
            "source_clusters": len(clusters),
        }
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", type=Path, default=Path("docs/sprint2/wp1/false_rollback_audit.json"))
    args = ap.parse_args()
    manifest = json.loads(PRIMARY.read_text())
    classes = json.loads(CLASSES.read_text())
    import late_real
    class_map = {(r["stream"], int(r["ep"])): r for r in classes}
    stream_specs = late_real.streams()
    jobs = []
    for stream in manifest["streams"]:
        spec = stream_specs[stream]
        delay = max(1, int(round(spec["delay"] * float(manifest["delay_mult"]))))
        for ep in spec["rows"]:
            for seed in range(int(manifest["seeds"])):
                jobs.append((stream, int(ep), int(seed), int(manifest["seed_base"]),
                             float(manifest["alpha"]), delay, int(manifest["budget"]),
                             float(manifest["cs"]), str(spec["file"]), spec["cluster"],
                             class_map[(stream, int(ep))]))
    with mp.Pool(args.workers) as pool:
        rows = [row for group in pool.imap_unordered(_job, jobs, chunksize=2) for row in group]
    rows.sort(key=lambda r: (r["stream"], r["ep"], r["seed"], r["policy"]))
    payload = {"protocol": "WP1 primary stream/seed manifest; E_rb trace replay",
               "source_manifest": str(PRIMARY.relative_to(ROOT)), "seed_base": manifest["seed_base"],
               "seeds": manifest["seeds"], "workers": args.workers,
               "primary_manifest_sha256": hashlib.sha256(PRIMARY.read_bytes()).hexdigest(),
               "false_rollback_definition": "rollback at t is false if frozen outcome-blind segment mean gain at t is >= 0; correct otherwise",
               "limitations": ["Evaluator-side retrospective diagnostic; realized segment means are not available to the policy.",
                               "Episodes and clusters were already used for WP1 development; this is not independent confirmation.",
                               "Cluster bootstrap is descriptive and conditions on observed rollback events."],
               "run_count": len(jobs), "rows": rows, "summary": _summarize(rows)}
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({"run_count": len(jobs), "row_count": len(rows), "out": str(out)}, indent=2))


if __name__ == "__main__":
    main()
