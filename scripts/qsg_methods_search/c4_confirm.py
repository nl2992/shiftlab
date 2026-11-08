"""C4 single opening: replay the registered sealed datasets (c4_registration.json).

Run ONLY after the registration commit. Usage:
  python c4_confirm.py run --out ../../outputs/qsg_methods_search/c4_confirm --workers 12
Policies: arm B (frozen since 10ba0237), primary comparator gongT_w100_m10 (Amendment A1),
pooled secondary qiu_delayed_movement, and descriptive arms. 10 policy seeds per episode.
"""

import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path

import c4_pilot
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
import os

REG = Path(os.environ.get("C4_REG", ROOT / "docs/qsg_methods_search/c4_registration.json"))
c4_pilot.POLICIES[:] = [
    "EQSDp_l0.9_g0.2",
    "gongT_w100_m10",
    "qiu_delayed_movement",
    "EQSDp_l0.95_g0.2",
    "wald_l0.9_g0.2",
    "econF_mo5_m5",
    "CONTROL_never_switch",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=12)
    a = ap.parse_args()
    reg = json.loads(REG.read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    jobs, checks = [], {}
    for d in reg["datasets"]:
        p = ROOT / d["sealed_path"]
        z = np.load(p)
        h = hashlib.sha256(z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes())
        checks[d["name"]] = h.hexdigest() == d["array_content_sha256"]
        k = z["l0"].shape[0]
        jobs += [
            (d["name"], str(p), int(z["delay"]), e, s, reg["seed_base"])
            for e in range(k)
            for s in range(reg["policy_seeds"])
        ]
    (out / "checksums.json").write_text(json.dumps(checks, indent=1))
    if not all(checks.values()):
        raise SystemExit(f"sealed hash mismatch: {checks}")
    with open(out / "records.jsonl", "w") as f, mp.Pool(a.workers) as pool:
        for rows in pool.imap_unordered(c4_pilot._job, jobs, chunksize=4):
            f.writelines(json.dumps(r) + "\n" for r in rows)
    print(f"done {len(jobs)} jobs -> {out}")


if __name__ == "__main__":
    main()
