"""SOTA comparator expansion runner (sota_expansion/03_EXPERIMENT_PROTOCOL.md).

  dev  : 14 exposed C4-0 pilot streams (development only; all tunable families' grids)
  nine : the original nine-dataset C4 batch (c4_registration.json), retrospective comparison

Usage:
  python sota_nine.py dev  --out DIR --workers 20 [--seeds 5]
  python sota_nine.py nine --out DIR --workers 20 --policies FILE
The nine run uses the registered seed base 2026111201 and 10 policy seeds, so arm B, tuned GZ and
Qiu reproduce the C4 records exactly (same rng derivation as c4_pilot._job).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/qsg_methods_search", ROOT / "scripts/failure_atlas_v2_flq"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import c4_pilot

REG = ROOT / "docs/qsg_methods_search/c4_registration.json"
DEV_SEED_BASE = 2026111401
POLICIES: list[str] = []


def _job(args):
    name, path, delay, ep, seed, seed_base, policies = args
    from sota_extra import EXTRA
    from suite import build_suite, run_metrics

    z = np.load(path)
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    gain = np.full(losses.shape[0], float((losses[:, 0].astype(int) - losses[:, 1]).mean()))
    h = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "big")
    cfg = c4_pilot.CFG
    rows = []
    for pol in build_suite(
        losses.shape[0],
        cfg["budget"],
        cfg["cs"],
        cfg["cq"],
        cfg["alpha"],
        delay,
        ep * 100_000 + seed,
        seed_base + h % 1000,
        names=policies,
        extra=EXTRA,
    ):
        rng = np.random.default_rng([seed_base, h, ep, seed, 7])
        m = run_metrics(
            pol,
            losses,
            gain,
            delay=delay,
            budget=cfg["budget"],
            cq=cfg["cq"],
            cs=cfg["cs"],
            stream_rng=rng,
        )
        rows.append(
            {
                "stream": name,
                "ep": ep,
                "seed": seed,
                "policy": pol.name,
                "delay": delay,
                "net": m["net"],
                "loss": m["loss"],
                "switches": m["switches"],
                "labels": m["labels"],
                "ever_promote": m["ever_promote"],
                "first_deploy": m["first_deploy"],
                "final": m["final"],
                "frac_on_wrong": m["frac_on_wrong"],
                "mean_gain": float(gain[0]),
            }
        )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dev", "nine"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--policies", default=None, help="file with one policy per line")
    ap.add_argument("--reg", default=str(REG), help="registration JSON (default: C4 batch 1)")
    a = ap.parse_args()
    from sota_extra import DEV_POLICIES

    pols = Path(a.policies).read_text().split() if a.policies else DEV_POLICIES
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs = []
    if a.cmd == "dev":
        ok = c4_pilot.verify()
        seeds, sb = a.seeds or 5, DEV_SEED_BASE
        for d, delays in (
            (c4_pilot.ATLAS, c4_pilot.ATLAS_DELAYS),
            (c4_pilot.SPRINT, c4_pilot.SPRINT_DELAYS),
        ):
            for name, delay in delays.items():
                k = np.load(d / f"{name}.npz")["l0"].shape[0]
                jobs += [
                    (name, str(d / f"{name}.npz"), delay, e, s, sb, pols)
                    for e in range(k)
                    for s in range(seeds)
                ]
    else:
        reg = json.loads(Path(a.reg).read_text())
        seeds, sb = a.seeds or reg["policy_seeds"], reg["seed_base"]
        ok = {}
        for d in reg["datasets"]:
            p = ROOT / d["sealed_path"]
            z = np.load(p)
            hsh = hashlib.sha256(z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes())
            ok[d["name"]] = hsh.hexdigest() == d["array_content_sha256"]
            jobs += [
                (d["name"], str(p), int(z["delay"]), e, s, sb, pols)
                for e in range(z["l0"].shape[0])
                for s in range(seeds)
            ]
    (out / "checksums.json").write_text(json.dumps(ok, indent=1))
    (out / "policies.txt").write_text("\n".join(pols))
    if not all(ok.values()):
        raise SystemExit(f"checksum mismatch: {ok}")
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for i, rows in enumerate(pool.imap_unordered(_job, jobs, chunksize=2)):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            if i % 200 == 0:
                f.flush()
                (out / "progress.txt").write_text(f"{i + 1}/{len(jobs)}")
    (out / "progress.txt").write_text(f"done {len(jobs)}/{len(jobs)}")
    print(f"done {len(jobs)} jobs -> {out}")


if __name__ == "__main__":
    main()
