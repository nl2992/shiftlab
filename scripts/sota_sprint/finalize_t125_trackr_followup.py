#!/usr/bin/env python3
"""Validate and index the registered T1/T2/T5 Track-R follow-up runs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = ROOT / "outputs/sprint2/T/T125_trackR"
ALPHAS = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5]
REGIMES = ["F0_null", "F0_worse", "F5_dep_null_r8", "F5_dep_null_r95", "F0_better",
           "F7_near_better", "F9_bursty_better", "F1_late_800", "F5_dep_better_r8",
           "S_dep_better_r95"]
POLICIES = ["T:mp/a5b", "T:mp/a5b+ad", "T:mp/a5b+ad+rb", "model_picker_adapter", "D1",
            "D6:mp", "D2", "A5b", "T2:gated/a5b", "T2:gated/a5b+front", "T2:gated/env8",
            "T2:gated/env8+front", "gated_deployment", "gated_adaptive_range+front", "T:ms/a5b",
            "model_selector_causal", "T:cams/a5b"]
POLICY_ARG = ",".join(POLICIES)
REGIME_ARG = ",".join(REGIMES)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_record(path: Path) -> dict:
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--result-json", type=Path,
                        default=Path("docs/sprint2/family_t/T1_T2_T5_trackR_followup.json"))
    parser.add_argument("--result-md", type=Path,
                        default=Path("docs/sprint2/family_t/T1_T2_T5_trackR_followup.md"))
    parser.add_argument("--out", type=Path,
                        default=Path("docs/sprint2/family_t/T1_T2_T5_trackR_manifests.json"))
    args = parser.parse_args()

    run_index = []
    all_sources = None
    code_revisions = set()
    total_rows = 0
    expected_rows_per_run = len(REGIMES) * 20 * len(POLICIES)
    for split, seed_base in (("dev", 2026111201), ("eval", 2026111211)):
        for alpha in ALPHAS:
            alpha_text = str(alpha)
            run_dir = RUN_ROOT / f"{split}_a{alpha_text}"
            manifest_path, records_path = run_dir / "manifest.json", run_dir / "records.jsonl"
            if not manifest_path.is_file() or not records_path.is_file():
                raise SystemExit(f"missing run output: {run_dir}")
            manifest = json.loads(manifest_path.read_text())
            argv = manifest["argv"]
            expected_argv = {"kind": "synthetic", "regimes": REGIME_ARG, "policies": POLICY_ARG,
                             "seeds": 20, "seed_base": seed_base, "workers": 4,
                             "alpha": alpha, "out": str(run_dir.relative_to(ROOT))}
            if argv != expected_argv:
                raise SystemExit(f"argv mismatch in {manifest_path}: {argv}")
            if manifest.get("n_jobs") != len(REGIMES) * 20:
                raise SystemExit(f"job-count mismatch in {manifest_path}")
            if all_sources is None:
                all_sources = manifest.get("sources")
            elif manifest.get("sources") != all_sources:
                raise SystemExit(f"source hash mismatch in {manifest_path}")
            code_revisions.add(manifest.get("git"))

            seen = set()
            row_count = 0
            with records_path.open() as records:
                for line in records:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    key = (row["regime"], row["seed"], row["policy"], round(row["alpha"], 6))
                    if key in seen:
                        raise SystemExit(f"duplicate record {key} in {records_path}")
                    seen.add(key)
                    row_count += 1
            expected = {(regime, seed, policy, round(alpha, 6))
                        for regime in REGIMES for seed in range(20) for policy in POLICIES}
            if seen != expected or row_count != expected_rows_per_run:
                missing, extra = expected - seen, seen - expected
                raise SystemExit(f"coverage mismatch in {records_path}: rows={row_count}, "
                                 f"missing={len(missing)}, extra={len(extra)}")
            total_rows += row_count
            run_index.append({"split": split, "alpha": alpha, "seed_base": seed_base,
                              "jobs": manifest["n_jobs"], "rows": row_count,
                              "seconds": manifest["seconds"], "manifest": file_record(manifest_path),
                              "records": file_record(records_path)})

    if len(code_revisions) != 1:
        raise SystemExit(f"runs do not share one code revision: {sorted(str(x) for x in code_revisions)}")
    if total_rows != 8 * 2 * expected_rows_per_run:
        raise SystemExit(f"unexpected total row count: {total_rows}")
    result_json = args.result_json if args.result_json.is_absolute() else ROOT / args.result_json
    result_md = args.result_md if args.result_md.is_absolute() else ROOT / args.result_md
    for path in (result_json, result_md):
        if not path.is_file():
            raise SystemExit(f"missing derived result: {path}")
    out = args.out if args.out.is_absolute() else ROOT / args.out
    report = {
        "protocol": "docs/sprint2/family_t/T1_T2_T5_trackR_followup_protocol.md",
        "runner": "scripts/sota_sprint/run_t125_trackr_followup.sh",
        "finalizer": "scripts/sota_sprint/finalize_t125_trackr_followup.py",
        "finalizer_sha256": sha256(ROOT / "scripts/sota_sprint/finalize_t125_trackr_followup.py"),
        "code_revision": next(iter(code_revisions)),
        "contract": {"T": 2000, "budget": 200, "cq": 0.05, "cs": 5.0,
                     "alpha_grid": ALPHAS, "regimes": REGIMES, "policies": POLICIES,
                     "dev_seed_base": 2026111201, "eval_seed_base": 2026111211},
        "run_count": len(run_index), "jobs": sum(x["jobs"] for x in run_index),
        "rows": total_rows, "rows_per_run": expected_rows_per_run,
        "source_hashes": all_sources, "runs": run_index,
        "result_json": file_record(result_json), "result_markdown": file_record(result_md),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "run_count": len(run_index), "jobs": report["jobs"],
                      "rows": total_rows, "code_revision": report["code_revision"],
                      "manifest_index": str(out.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
