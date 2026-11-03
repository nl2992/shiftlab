"""Deterministic artifact checks, not an independent scientific integrity verdict."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
import numpy as np
import run_atlas_cycle7_validation_v1 as c7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    out = (
        ROOT
        / "outputs/failure_atlas_v1_cycle7"
        / ("validation_smoke" if args.smoke else "validation")
    )
    manifest = json.loads((out / "manifest.json").read_text("utf-8"))
    plan, md = manifest["design"], manifest["digest"]
    assert c7.digest(plan) == md == c7.digest(c7.design(args.smoke)), "source or design drift"
    records = c7.load_records(out / "records.jsonl", md)
    jobs = {j["key"]: j for j in plan["jobs"]}
    seen = set()
    checked = 0
    for r in records.values():
        job = jobs[r["key"]]
        assert set(r["values"]) == set(job["methods"])
        cell = c7.unpack(job["cell"])
        for name, values in r["values"].items():
            assert len(values) == len(r["seeds"])
            for seed, row in zip(r["seeds"], values, strict=True):
                key = (r["key"], name, seed)
                assert key not in seen, "duplicated method/seed"
                seen.add(key)
                assert all(np.isfinite(v) for v in row.values())
                assert 0 <= row["queries"] <= cell.B
                assert abs(row["query_cost"] - cell.c * row["queries"] / cell.T) < 1e-12
                assert abs(row["switch_cost"] - cell.s * row["switches"] / cell.T) < 1e-12
                assert (
                    abs(row["cost"] - row["loss"] - row["query_cost"] - row["switch_cost"]) < 1e-12
                )
                assert all(row[k] in (0, 1) for k in ("fp", "promoted", "correct"))
                assert row["fp"] <= row["promoted"] and row["correct"] <= row["promoted"]
                if job["kind"] == "null":
                    assert row["correct"] == 0 and row["promoted"] == row["fp"]
                checked += 1
    regenerated = c7.analyse(plan, records)
    saved = json.loads((out / "results.json").read_text("utf-8"))
    assert saved.pop("manifest_digest") == md
    assert regenerated == saved, "results differ from checkpoint recomputation"
    assert checked == regenerated["unique_method_runs"]
    if not args.smoke:
        assert (ROOT / "docs/failure_atlas_cycle7_validation_results_v1.md").read_bytes() == (
            out / "summary.md"
        ).read_bytes(), "tracked table differs from generated summary"
    result = {
        "status": "DETERMINISTIC_CHECKS_PASS",
        "scope": "artifact consistency, completeness, budget, accounting, metric ranges and exact analysis recomputation; not independent experiment integrity or novelty audit",
        "manifest_digest": md,
        "checked_method_runs": checked,
        "seed_range": [min(plan["seeds"]), max(plan["seeds"]) + 1],
        "confirmation_seeds_used": False,
        "verdicts_recomputed": regenerated["verdicts"],
        "sha256": {
            name: hashlib.sha256((out / name).read_bytes()).hexdigest()
            for name in ("manifest.json", "records.jsonl", "results.json", "summary.md")
        },
    }
    (out / "deterministic_audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
