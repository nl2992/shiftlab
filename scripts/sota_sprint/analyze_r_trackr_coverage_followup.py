#!/usr/bin/env python3
"""Render a scoped interpretation of the Family-R held-out coverage follow-up."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--curves", type=Path, default=Path("docs/sprint2/family_r/R_trackR_coverage_followup.json")
    )
    ap.add_argument(
        "--manifests",
        type=Path,
        default=Path("docs/sprint2/family_r/R_trackR_coverage_followup_manifests.json"),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("docs/sprint2/family_r/R_trackR_coverage_followup_report.md"),
    )
    args = ap.parse_args()
    curves_path = args.curves if args.curves.is_absolute() else ROOT / args.curves
    manifests_path = args.manifests if args.manifests.is_absolute() else ROOT / args.manifests
    out = args.out if args.out.is_absolute() else ROOT / args.out
    curves = json.loads(curves_path.read_text())
    provenance = json.loads(manifests_path.read_text())
    data = curves["curves"]
    common = []
    prior_path = ROOT / "outputs/sprint2/R/analysis/risk_curves.json"
    prior = json.loads(prior_path.read_text())["curves"]
    for target, points in data.items():
        for policy, point in points.items():
            old = prior.get(target, {}).get(policy)
            if old is not None:
                common.append((point["risk"] - old["risk"], point["cost"] - old["cost"]))

    lines = [
        "# Family R Track-R coverage follow-up",
        "",
        "This is a new simulator replicate on reused synthetic regimes, evaluated on one common seed",
        "block. The development-selected alpha map is frozen to the original Family-R development",
        "runs; the finalizer verified that the regenerated map matches the existing map. The run is",
        "post-development descriptive evidence, not independent real-data confirmation or a formal",
        "risk guarantee.",
        "",
        "## Coverage and calibration",
        "",
        f"- {provenance['run_count']} evaluation alpha runs; {provenance['jobs']:,} episode jobs;",
        f"  {provenance['rows']:,} policy records ({provenance['rows_per_run']:,} per run).",
        f"- {len(provenance['contract']['policies'])} policies with at least one development-feasible",
        "  operating point; four policies with no feasible development alpha remain without a point.",
        f"- Held-out points by target: {', '.join(f'{t}={len(points)}' for t, points in data.items())}.",
        "- The registered target is calibrated from a development point estimate. Held-out rates and",
        "  their Wilson intervals can exceed the target; these are empirical operating points only.",
        "",
        "## Cost-risk Pareto points",
        "",
        "The frontier is local to this 26-policy panel. Costs are mean alternative net costs with",
        "95% Student-t intervals over per-seed means; risk is pooled over the four null regimes with Wilson",
        "95% intervals.",
        "",
        "| Target | Policy | Alpha | Held-out risk (95% CI) | Alternative net cost (95% CI) |",
        "|---|---|---:|---:|---:|",
    ]
    for target, points in data.items():
        for policy, point in sorted(
            points.items(), key=lambda item: (item[1]["risk"], item[1]["cost"])
        ):
            if not point["pareto"]:
                continue
            lines.append(
                f"| {target} | `{policy}` | {point['alpha']:g} | "
                f"{point['risk']:.3f} [{point['risk_ci'][0]:.3f}, {point['risk_ci'][1]:.3f}] | "
                f"{point['cost']:.1f} [{point['cost_ci'][0]:.1f}, {point['cost_ci'][1]:.1f}] |"
            )
    lines.extend(["", "## Repeat-block comparison", ""])
    if common:
        abs_risk = [abs(row[0]) for row in common]
        abs_cost = [abs(row[1]) for row in common]
        lines.extend(
            [
                f"Across {len(common)} policy-target cells also present in the earlier Family-R held-out",
                f"report, the median absolute difference was {statistics.median(abs_risk):.3f} in risk",
                f"and {statistics.median(abs_cost):.1f} in alternative net cost; maxima were",
                f"{max(abs_risk):.3f} and {max(abs_cost):.1f}, respectively. This is descriptive",
                "between-block variation on the same simulator regimes, not a significance test.",
            ]
        )
    else:
        lines.append("No policy-target cells overlapped the previous held-out report.")
    lines.extend(
        [
            "",
            "## Interpretation limits",
            "",
            "The results fill held-out operating-point coverage for policies that were calibrated on",
            "development data but omitted from earlier evaluation screens. They do not show general",
            "superiority: R3-alloc reaches zero observed promotions at high alternative cost, while some",
            "development-selected thresholds (including R2-floor25 at R10) exceed their nominal target",
            "on evaluation. Reused generators and policies exposed during development limit claims to",
            "this post-development simulator replicate. No application utility or causal shift label is",
            "provided by these synthetic regimes.",
            "",
            "Machine-readable operating points: `R_trackR_coverage_followup.json`. Per-run configs,",
            "code revisions, source hashes, and output checksums: `R_trackR_coverage_followup_manifests.json`.",
        ]
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    try:
        report_path = str(out.relative_to(ROOT))
    except ValueError:
        report_path = str(out)
    print(
        json.dumps(
            {
                "report": report_path,
                "targets": len(data),
                "frontier_rows": sum(
                    sum(bool(p["pareto"]) for p in points.values()) for points in data.values()
                ),
                "repeat_block_cells": len(common),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
