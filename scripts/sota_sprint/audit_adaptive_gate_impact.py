#!/usr/bin/env python3
"""Inventory Sprint 2 runs whose policy pools include adaptive gated-range code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ADAPTIVE = "gated_adaptive_range"
GATED_C_EXACT = {"C1", "C1-uniformbase", "C2", "C2-noadapt", "C2-floorskip", "C5", "C6",
                 "C6-no_deadline", "C6-no_shadow", "C6-no_two_stage", "Cchk:gated_uniform",
                 "Cchk:gated_front"}


def _affected(policy: str) -> bool:
    return (
        ADAPTIVE in policy
        or policy in GATED_C_EXACT
        or policy.startswith(("C1-k", "C2-g", "C6-f"))
        or policy.startswith("M_RMMSUI_gar")
        or policy.startswith("T2:gated")
        or (policy.startswith("T6:") and ("xC2" in policy or "xC6" in policy))
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("outputs"))
    parser.add_argument("--json", type=Path, default=Path("outputs/sprint2/adaptive_gate_impact.json"))
    parser.add_argument("--markdown", type=Path, default=Path("docs/sprint2/adaptive_gate_impact.md"))
    args = parser.parse_args()

    rows = []
    corrected_runs = []
    manifest_dirs = set()
    for manifest_path in sorted(args.root.rglob("manifest.json")):
        try:
            manifest = json.loads(manifest_path.read_text())
            manifest_dirs.add(manifest_path.parent.resolve())
            if "_wmaxfix_20261105" in str(manifest_path.parent):
                corrected_runs.append({"run": str(manifest_path.parent), "jobs": manifest.get("n_jobs"),
                                       "policies": manifest.get("argv", {}).get("policies", [])
                                       if isinstance(manifest.get("argv"), dict) else manifest.get("policies", [])})
                continue
            argv = manifest.get("argv", {})
            aggregate = False
            if isinstance(argv, dict):
                raw_policies = argv.get("policies", "")
                get_arg = argv.get
            elif isinstance(argv, list):
                parsed_argv = {}
                for i, arg in enumerate(argv[:-1]):
                    if arg.startswith("--"):
                        parsed_argv[arg[2:].replace("-", "_")] = argv[i + 1]
                raw_policies = parsed_argv.get("policies", "")
                get_arg = parsed_argv.get
            else:
                raw_policies = manifest.get("policies", "")
                aggregate = bool(manifest.get("constituent_runs"))
                get_arg = lambda key, default=None: manifest.get(key, default)
            if not raw_policies:
                raw_policies = manifest.get("policies", "")
                aggregate = bool(manifest.get("constituent_runs"))
            base_get_arg = get_arg
            get_arg = lambda key, default=None: base_get_arg(key, manifest.get(key, default))
            if isinstance(raw_policies, list):
                policies = [str(x).strip() for x in raw_policies if str(x).strip()]
            else:
                policies = [x.strip() for x in str(raw_policies).split(",") if x.strip()]
            affected = [p for p in policies if _affected(p)]
            if not affected:
                continue
            rows.append({
                "run": str(manifest_path.parent),
                "aggregate": aggregate,
                "constituent_runs": manifest.get("constituent_runs", []),
                "policies": affected,
                "seeds": get_arg("seeds"),
                "seed_base": get_arg("seed_base"),
                "episodes": get_arg("episodes"),
                "jobs": manifest.get("n_jobs"),
                "git": manifest.get("git"),
                "argv": argv,
                "manifest_sources": manifest.get("sources", {}),
                "adaptive": [p for p in affected if "+front" not in p],
                "front": [p for p in affected if "+front" in p],
                "aliases": [p for p in affected if ADAPTIVE not in p],
            })
        except (OSError, json.JSONDecodeError, TypeError):
            continue

    unmanifested = []
    for records_path in sorted(args.root.rglob("records.jsonl")):
        if records_path.parent.resolve() in manifest_dirs:
            continue
        affected_policies = set()
        record_count = 0
        try:
            with records_path.open() as f:
                for line in f:
                    record_count += 1
                    try:
                        policy = str(json.loads(line).get("policy", ""))
                        if _affected(policy):
                            affected_policies.add(policy)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
        if affected_policies:
            unmanifested.append({
                "run": str(records_path.parent),
                "record_count": record_count,
                "policies": sorted(affected_policies),
                "state_hint": "corrected-output-partial-or-complete" if "wmaxfix" in str(records_path.parent) else "historical-output-needs-run-provenance",
            })

    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.markdown.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source_root": str(args.root), "run_count": len(rows), "runs": rows,
               "corrected_run_count": len(corrected_runs), "corrected_runs": corrected_runs,
               "unmanifested_run_count": len(unmanifested), "unmanifested_runs": unmanifested}
    args.json.write_text(json.dumps(payload, indent=2) + "\n")
    execution_rows = [r for r in rows if not r["aggregate"]]
    aggregate_rows = [r for r in rows if r["aggregate"]]
    adaptive_count = sum(sum(ADAPTIVE in p and "+front" not in p for p in r["policies"]) for r in execution_rows)
    front_count = sum(sum(ADAPTIVE in p and "+front" in p for p in r["policies"]) for r in execution_rows)
    alias_count = sum(len(r["aliases"]) for r in execution_rows)
    historical_orphans = sum("wmaxfix" not in r["run"] for r in unmanifested)
    lines = [
        "# Adaptive gated-range replay impact inventory", "",
        "Generated from saved `manifest.json` files under `outputs/`. The inventory is a replay schedule, not a claim that every affected result changes.", "",
        "The bug fixed in the shared `GatedAdaptiveRange` hook selected/updated the bet range after the current query draw or flush. Direct adaptive-range, `+front`, and wrapper rows require corrected same-seed replay. The semantic alias scan includes M_RMMSUI_gar, T2 gated-host transfers, T6 gated-controller transfers, and fam_c GatedC variants (C1/C2/C5/C6), whose old query range was stored after the query coin.", "",
        f"- Execution manifests with an affected policy: **{len(execution_rows)}**",
        f"- Aggregate manifests affected through their constituents: **{len(aggregate_rows)}**",
        f"- Direct adaptive-range policy entries: **{adaptive_count}**",
        f"- `+front` policy entries: **{front_count}**",
        f"- Hidden host-alias policy entries: **{alias_count}**",
        f"- Total affected policy entries requiring replay (including aliases): **{sum(len(r['policies']) for r in execution_rows)}**",
        f"- Record directories without manifests that contain affected policies: **{len(unmanifested)}**",
        f"- Historical record-only directories needing provenance recovery: **{historical_orphans}**",
        f"- Corrected replay manifests already produced: **{len(corrected_runs)}**",
        "- See `outputs/sprint2/adaptive_gate_impact.json` for paths, seeds, job counts, and policy names.", "",
        "| Run | Seeds | Seed base | Jobs | Affected policies |", "|---|---:|---:|---:|---|",
    ]
    for r in rows:
        suffix = " (aggregate: " + ", ".join(r["constituent_runs"]) + ")" if r["aggregate"] else ""
        lines.append(f"| `{r['run']}`{suffix} | {r['seeds']} | {r['seed_base']} | {r['jobs']} | {', '.join(r['policies'])} |")
    if unmanifested:
        lines += ["", "## Record directories without a run manifest", "",
                  "These directories require provenance reconstruction before a corrected replay can be tied to exact original arguments. `wmaxfix` paths are corrected runs, not pre-fix source runs.", "",
                  "| Run | Records | State hint | Policies |", "|---|---:|---|---|"]
        for r in unmanifested:
            lines.append(f"| `{r['run']}` | {r['record_count']} | {r['state_hint']} | {', '.join(r['policies'])} |")
    if corrected_runs:
        lines += ["", "## Corrected replay manifests already produced", "",
                  "These are outputs of the corrected runner and are excluded from the historical replay schedule.", "",
                  "| Run | Jobs | Policies |", "|---|---:|---|"]
        for r in corrected_runs:
            lines.append(f"| `{r['run']}` | {r['jobs']} | {r['policies']} |")
    args.markdown.write_text("\n".join(lines) + "\n")
    print(f"execution manifests={len(execution_rows)} aggregate manifests={len(aggregate_rows)} adaptive entries={adaptive_count} +front entries={front_count}")


if __name__ == "__main__":
    main()
