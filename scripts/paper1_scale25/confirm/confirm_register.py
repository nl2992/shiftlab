"""Protocol C1 step 3: write confirm_registration_C1.json and register ledger attempts (BEFORE any policy run).

Eligible datasets get ledger indices in protocol order (from 8). Ineligible/failed builds are listed with the
reason and get no index. Usage: python confirm_register.py [--dry]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/data"))
sys.path.insert(0, str(ROOT / "scripts/paper1_scale25/stats"))
import confirm_build as cb
import ledger as lg
import numpy as np

LEDGER = ROOT / "docs/paper1_scale25/confirmation_attempts.csv"
PROTOCOL_ID = "P1-SCALE25-C1-V1-22"
CONTRAST = "v1 (P2_K2__E48_F60) vs W+cut (s2wald_l0.98_g0.3_H1100), 07a"
REGISTRY = json.loads(
    (ROOT / "docs/paper1_scale25/DATASET_SOURCE_REGISTRY.json").read_text(encoding="utf-8")
)
META = {d["dataset_id"]: d for d in REGISTRY["datasets"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    ds, order = [], 0
    for name, w0, w1 in cb.ORDER:
        order += 1
        m = META[name]
        d = {"protocol_order": order, "name": name, "org": m["org_id"], "parent_source_id": m["parent_source_id"],
             "domain": m["domain"], "window": [w0, w1]}  # fmt: skip
        p = cb.OUT_REC / f"{name}.json"
        if not p.exists():
            d["eligibility"] = {
                "eligible": False,
                "reason": "build did not complete: see FAILED records",
            }
            fails = sorted(cb.OUT_REC.glob(f"{name}.FAILED*.json"))
            if fails:
                d["eligibility"]["failure"] = json.loads(fails[-1].read_text())["error"]
            ds.append(d)
            continue
        r = json.loads(p.read_text())
        d |= {"episodes": r["episodes"], "delay": r["meta"]["delay"], "built_utc": r["built_utc"],
              "n_after_filter": r["n_after_filter"], "subsample": r["subsample"]}  # fmt: skip
        d["eligibility"] = {
            "eligible": r["eligible"],
            "gates": r["gates"],
            "validation": r["validation"],
        }
        if not r["eligible"]:
            d["eligibility"]["reason"] = "failed C4 gate(s): " + ",".join(
                k for k, v in r["gates"].items() if not v
            )
        else:
            d["sealed_path"] = r["sealed"]["path"]
            d["array_content_sha256"] = r["sealed"]["array_content_sha256"]
            z = np.load(ROOT / d["sealed_path"])
            import hashlib

            h = hashlib.sha256(
                z["l0"].tobytes() + z["l1"].tobytes() + z["starts"].tobytes()
            ).hexdigest()
            assert h == d["array_content_sha256"], name
            assert int(z["delay"]) == d["delay"]
        ds.append(d)
    nxt = lg.next_index(lg.read(LEDGER))
    for d in ds:
        if d["eligibility"]["eligible"]:
            d["ledger_index"] = nxt
            nxt += 1
    reg = {"registered_utc": None, "batch": "C1", "protocol": "docs/paper1_scale25/07a_PROTOCOL_C1_V1_22.md",
           "protocol_id": PROTOCOL_ID, "contract": {"budget": 200, "cq": 0.05, "cs": 5.0, "T_episode": 2000},
           "policy_seeds": 10, "seed_base": 2026111001, "datasets": ds}  # fmt: skip
    print(
        [
            (d["name"], d.get("episodes"), d["eligibility"]["eligible"], d.get("ledger_index"))
            for d in ds
        ]
    )
    if a.dry:
        return
    from datetime import UTC, datetime

    reg["registered_utc"] = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    for d in ds:
        if d["eligibility"]["eligible"]:
            row = lg.register_attempt(
                LEDGER, f"{d['name']}@C1_{d['window'][0]}_{d['window'][1]}", d["parent_source_id"], PROTOCOL_ID,
                CONTRAST, note="registered before any policy run on this window (07a)",
            )  # fmt: skip
            assert int(row["attempt_index"]) == d["ledger_index"], (d["name"], row["attempt_index"])
    (ROOT / "docs/paper1_scale25/confirm_registration_C1.json").write_text(
        json.dumps(reg, indent=1) + "\n"
    )
    print("problems:", lg.validate(LEDGER))


if __name__ == "__main__":
    main()
