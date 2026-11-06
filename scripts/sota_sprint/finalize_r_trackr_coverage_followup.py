#!/usr/bin/env python3
"""Validate and index the registered Family-R Track-R coverage evaluation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "outputs/sprint2/R/trackR_coverage_followup"
ALPHAS = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5]
REGIMES = ["F0_null", "F0_worse", "F5_dep_null_r8", "F5_dep_null_r95", "F0_better",
           "F7_near_better", "F9_bursty_better", "F1_late_800", "F5_dep_better_r8",
           "S_dep_better_r95"]
POLICIES = ["A5b", "C6", "CONTROL_never_switch", "D2", "H1-iid1", "H2", "R2",
            "R2-floor25", "R2-qc", "R3-alloc", "R3-base", "R3-near", "R3-plugin",
            "R3-plugnear", "R4-both", "R4-comb", "R5", "R6:D2-always", "R6:D2-floor25",
            "R:economic_stop", "R:xu_acquisition_only@alpha", "SMCS+retain-incumbent",
            "choe_ramdas_eb+front", "gated_adaptive_range+front", "gated_deployment",
            "xu_acquisition_only"]
REGIME_ARG = ",".join(REGIMES)
POLICY_ARG = ",".join(POLICIES)
SEED_BASE = 2026111311


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def main() -> int:
    all_sources = None
    code_revisions = set()
    run_index = []
    expected_rows = len(REGIMES) * 20 * len(POLICIES)
    total_rows = 0
    for alpha in ALPHAS:
        run_dir = RUN_ROOT / f"eval_a{alpha}"
        manifest_path, records_path = run_dir / "manifest.json", run_dir / "records.jsonl"
        if not manifest_path.is_file() or not records_path.is_file():
            raise SystemExit(f"missing run output: {run_dir}")
        manifest = json.loads(manifest_path.read_text())
        expected_argv = {"kind": "synthetic", "regimes": REGIME_ARG, "policies": POLICY_ARG,
                         "seeds": 20, "seed_base": SEED_BASE, "workers": 4,
                         "alpha": alpha, "out": str(run_dir.relative_to(ROOT))}
        if manifest.get("argv") != expected_argv:
            raise SystemExit(f"argv mismatch in {manifest_path}: {manifest.get('argv')}")
        if manifest.get("n_jobs") != len(REGIMES) * 20:
            raise SystemExit(f"job-count mismatch in {manifest_path}")
        if all_sources is None:
            all_sources = manifest.get("sources")
        elif manifest.get("sources") != all_sources:
            raise SystemExit(f"source hash mismatch in {manifest_path}")
        code_revisions.add(manifest.get("git"))
        seen = set()
        with records_path.open() as records:
            for line in records:
                if not line.strip():
                    continue
                row = json.loads(line)
                key = (row["regime"], row["seed"], row["policy"], round(row["alpha"], 6))
                if key in seen:
                    raise SystemExit(f"duplicate record {key} in {records_path}")
                seen.add(key)
        expected = {(regime, seed, policy, round(alpha, 6))
                    for regime in REGIMES for seed in range(20) for policy in POLICIES}
        if seen != expected:
            raise SystemExit(f"coverage mismatch in {records_path}: rows={len(seen)}, "
                             f"missing={len(expected - seen)}, extra={len(seen - expected)}")
        total_rows += len(seen)
        run_index.append({"alpha": alpha, "seed_base": SEED_BASE, "jobs": manifest["n_jobs"],
                          "rows": len(seen), "seconds": manifest["seconds"],
                          "manifest": file_record(manifest_path), "records": file_record(records_path)})
    if len(code_revisions) != 1:
        raise SystemExit(f"runs do not share one code revision: {sorted(map(str, code_revisions))}")
    if total_rows != len(ALPHAS) * expected_rows:
        raise SystemExit(f"unexpected total row count: {total_rows}")
    result_json = ROOT / "outputs/sprint2/R/analysis/trackR_coverage_followup_risk_curves.json"
    result_md = result_json.with_suffix(".md")
    for path in (result_json, result_md):
        if not path.is_file():
            raise SystemExit(f"missing derived result: {path}")
    out = ROOT / "docs/sprint2/family_r/R_trackR_coverage_followup_manifests.json"
    report = {"protocol": "docs/sprint2/family_r/R_trackR_coverage_followup_protocol.md",
              "runner": "scripts/sota_sprint/run_r_trackr_coverage_followup.sh",
              "finalizer": "scripts/sota_sprint/finalize_r_trackr_coverage_followup.py",
              "finalizer_sha256": sha256(Path(__file__)), "code_revision": next(iter(code_revisions)),
              "contract": {"alpha_grid": ALPHAS, "regimes": REGIMES, "policies": POLICIES,
                           "seed_base": SEED_BASE, "seeds_per_regime": 20},
              "run_count": len(run_index), "jobs": sum(r["jobs"] for r in run_index),
              "rows": total_rows, "rows_per_run": expected_rows, "source_hashes": all_sources,
              "runs": run_index, "result_json": file_record(result_json),
              "result_markdown": file_record(result_md)}
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "run_count": len(run_index), "jobs": report["jobs"],
                      "rows": total_rows, "code_revision": report["code_revision"],
                      "manifest_index": str(out.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
