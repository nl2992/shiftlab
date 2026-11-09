"""Run the doc-19 fresh confirmation: 4 frozen arms + arm R + 25 comparators on the fresh builds.

    python fresh_confirm_run.py --out DIR [--workers 20] [--reg PATH] [--seeds 10] [--smoke-old]

Checksums of every sealed array are verified against the registration before any policy runs.
Seeds/rng derivation are those of ``trace_run.run_policies`` (== sota_nine). Records:
<out>/records.jsonl (one row per stream, ep, seed, config_id).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / "search60"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts/qsg_methods_search"))

import eval60 as e60
import run_phase12 as r12
import trace_run as tr
from analyze_all import ADAPTERS, CONTROLS

REG = ROOT / "docs/paper1_eqsdp/fresh_registration.json"
WALD_PARENT = {"kind": "wald", "lam": 0.98, "gamma": 0.3, "cutoff": 1100}
EQ_PAIR = "P2_K2__E48_F60"
W_PAIR = "P4W__P2_K2__E48_F60"
EQ_CUT = "s2armr_H1100"
W_CUT = "s2wald_l0.98_g0.3_H1100"
ARM_R = "EQSDp_l0.98_g0.3"
SOTA = ADAPTERS + CONTROLS


def pair_specs():
    mods = [r12.mod_spec("E48", 0), r12.mod_spec("F60", 0)]
    return [
        {"modules": mods, "name": EQ_PAIR},
        {"modules": mods, "name": W_PAIR, "parent": WALD_PARENT},
    ]


def check_against_ledger():
    """The frozen specs must resolve to exactly the ledger parameters (doc 19 section 1)."""
    rows = {}
    for line in r12.LEDGER.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("config_id") in (f"P3F__{EQ_PAIR}", f"P4F__{W_PAIR}") and r.get("modules"):
            rows[r["config_id"]] = r
    for sp, key in zip(pair_specs(), (f"P3F__{EQ_PAIR}", f"P4F__{W_PAIR}")):
        got = [g["params"] for g in r12.resolved(sp)]
        want = [m["params"] for m in rows[key]["modules"]]
        assert got == want, (key, got, want)
        if sp.get("parent"):
            assert rows[key]["parent"] == sp["parent"], key
    return True


def fresh_sealed(reg_path, only=None):
    reg = json.loads(Path(reg_path).read_text(encoding="utf-8"))
    out, sb = {}, reg["seed_base"]
    for d in reg["datasets"]:
        if not d.get("eligibility", {}).get("eligible", d.get("eligible", True)):
            continue
        if only and d["name"] not in only:
            continue
        p = ROOT / d["sealed_path"]
        z = np.load(p)
        h = hashlib.sha256(z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes())
        if h.hexdigest() != d["array_content_sha256"]:
            raise SystemExit(f"checksum mismatch for {d['name']}")
        assert int(z["l0"].shape[0]) == d["episodes"], d["name"]
        out[d["name"]] = (str(p), int(z["delay"]), sb)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--reg", default=str(REG))
    ap.add_argument(
        "--part",
        choices=["all", "core", "panel"],
        default="all",
        help="core = 2 pair specs + 2 cutoff arms + arm R; panel = the 25 comparators",
    )
    ap.add_argument("--only", nargs="*", help="restrict to these datasets (resume after a stall)")
    ap.add_argument(
        "--smoke-old", action="store_true", help="old data / old seeds; code check only"
    )
    a = ap.parse_args()
    check_against_ledger()
    if a.smoke_old:
        sealed = {k: v for k, v in tr.sealed_paths().items() if k == "sf_311"}
    else:
        sealed = fresh_sealed(a.reg, a.only)
    tr.sealed_paths = lambda *args, **kw: sealed
    extra = [EQ_CUT, W_CUT, ARM_R, *SOTA]
    specs = pair_specs()
    if a.part == "core":
        extra = extra[:3]
    elif a.part == "panel":
        extra, specs = SOTA, []
    out = Path(a.out)
    (out).mkdir(parents=True, exist_ok=True)
    (out / "checksums_ok.json").write_text(json.dumps({k: True for k in sealed}))
    (out / "policies.txt").write_text("\n".join([sp["name"] for sp in specs] + extra))
    kw = {"episodes": {"sf_311": [0, 1]}} if a.smoke_old else {}
    e60.run_eval(specs, out, split="all", seeds=tuple(range(a.seeds if not a.smoke_old else 2)),
                 workers=a.workers, controls=False, extra_names=extra, **kw)  # fmt: skip


if __name__ == "__main__":
    main()
