"""C4-0 transfer pilot on exposed real loss streams (c4_plan.md, "C4-0 pilot rule").

Usage: python c4_pilot.py run --out DIR [--seeds 10] [--workers 12]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import multiprocessing as mp
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT / "scripts/qsg_methods_search", ROOT / "scripts/failure_atlas_v2_flq"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

ATLAS = ROOT / "data/atlas_v2_losses"
SPRINT = ROOT / "data/sprint_fresh_losses"
ATLAS_DELAYS = {
    "rialto": 100,
    "spam": 50,
    "weather": 1,
    "openml_ldpa": 100,
    "uci_occupancy": 100,
    "airlines": 100,
    "bank": 100,
    "elec2": 48,
    "criteo": 100,
}
SPRINT_DELAYS = {
    "metro": 24,
    "beijing_pm25": 24,
    "bike_hour": 24,
    "appliances": 144,
    "household_power": 144,
}
POLICIES = [
    "EQSDp_l0.9_g0.2",
    "EQSDp_l0.95_g0.2",
    "gongT_w100_m10",
    "qiu_delayed_movement",
    "wald_l0.9_g0.2",
    "smarg_l0.9_k0.2",
    "dwell_l0.9_s5",
    "econF_mo5_m5",
    "CONTROL_never_switch",
]
CFG = {"budget": 200, "cq": 0.05, "cs": 5.0, "alpha": 0.05}


def verify():
    """Check every file against its README hash (file sha256 for Atlas, array hash for Sprint)."""
    ok = {}
    txt = (ATLAS / "README.md").read_text(encoding="utf-8")
    for name in ATLAS_DELAYS:
        want = re.search(r"([0-9a-f]{64})\s+" + re.escape(name) + r"\.npz", txt).group(1)
        got = hashlib.sha256((ATLAS / f"{name}.npz").read_bytes()).hexdigest()
        ok[name] = got == want
    txt = (SPRINT / "README.md").read_text(encoding="utf-8")
    for name in SPRINT_DELAYS:
        want = re.search(re.escape(name) + r"\.npz \| [0-9a-f]{64} \| ([0-9a-f]{64})", txt).group(1)
        z = np.load(SPRINT / f"{name}.npz")
        got = hashlib.sha256(
            z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes()
        ).hexdigest()
        ok[name] = got == want
    return ok


def _extra():
    from c3_extra import EXTRA as C3
    from p1_extra import EXTRA as P1

    return {**P1, **{k: v for k, v in C3.items() if k not in P1}}


def _job(args):
    name, path, delay, ep, seed, seed_base = args
    from suite import build_suite, run_metrics

    z = np.load(path)
    losses = np.stack([z["l0"][ep], z["l1"][ep]], axis=1).astype(np.int8)
    gain = np.full(losses.shape[0], float((losses[:, 0].astype(int) - losses[:, 1]).mean()))
    h = int.from_bytes(hashlib.sha256(name.encode()).digest()[:4], "big")
    rows = []
    for pol in build_suite(
        losses.shape[0],
        CFG["budget"],
        CFG["cs"],
        CFG["cq"],
        CFG["alpha"],
        delay,
        ep * 100_000 + seed,
        seed_base + h % 1000,
        names=POLICIES,
        extra=_extra(),
    ):
        rng = np.random.default_rng([seed_base, h, ep, seed, 7])
        m = run_metrics(
            pol,
            losses,
            gain,
            delay=delay,
            budget=CFG["budget"],
            cq=CFG["cq"],
            cs=CFG["cs"],
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
                "switches": m["switches"],
                "labels": m["labels"],
                "ever_promote": m["ever_promote"],
            }
        )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--seed-base", type=int, default=2026110901)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    ok = verify()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "checksums.json").write_text(json.dumps(ok, indent=1))
    if not all(ok.values()):
        raise SystemExit(f"checksum mismatch: {ok}")
    jobs = []
    for d, delays in ((ATLAS, ATLAS_DELAYS), (SPRINT, SPRINT_DELAYS)):
        for name, delay in delays.items():
            k = np.load(d / f"{name}.npz")["l0"].shape[0]
            jobs += [
                (name, str(d / f"{name}.npz"), delay, e, s, a.seed_base)
                for e in range(k)
                for s in range(a.seeds)
            ]
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for i, rows in enumerate(pool.imap_unordered(_job, jobs, chunksize=4), 1):
            f.writelines(json.dumps(r) + "\n" for r in rows)
            if i % 300 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    print(f"done {len(jobs)} jobs -> {out}")


if __name__ == "__main__":
    main()
