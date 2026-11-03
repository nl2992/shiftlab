"""Reconcile B1/B2 Q1 point-effect gates from archived summary cells."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/promising_directions/results"
DEST = ROOT / "docs/retrospective_audit_2026_11_01/B1B2_GATE_RECONCILIATION.json"


def close(actual: float, expected: float, label: str) -> None:
    if abs(actual - expected) > 1e-10:
        raise ValueError(f"{label}: {actual} != {expected}")


def run(source: Path = SOURCE) -> dict[str, object]:
    result = {"status": "ARCHIVED_EXPOSED_GATE_ARITHMETIC_ONLY", "rounds": {}}
    for round_name, candidate in (("b1", "P3"), ("b2", "P3b")):
        path = source / round_name / "summary.json"
        summary = json.loads(path.read_text(encoding="utf-8"))
        output = []
        for setting, claim in summary["q1_settings"].items():
            best = claim["best"]
            if best not in {"P0", "P1", "P2", "P2b"}:
                raise ValueError("selected BEST is outside registered deployable set")
            means = {world: summary["cells"][setting][world] for world in ("W1", "W2", "W3", "W4")}
            avg_candidate = sum(float(cell[candidate]["mean_cost"]) for cell in means.values()) / 4
            avg_best = sum(float(cell[best]["mean_cost"]) for cell in means.values()) / 4
            diff = avg_candidate - avg_best
            reduction = -diff / avg_best
            stored_diff = claim["p3_minus_best" if round_name == "b1" else "p3b_minus_best"]
            stored_reduction = claim[
                "p3_relative_reduction" if round_name == "b1" else "p3b_relative_reduction"
            ]
            stored_world = claim[
                "p3_worse_than_best_by_world"
                if round_name == "b1"
                else "p3b_worse_than_best_by_world"
            ]
            close(diff, stored_diff["mean"], f"{round_name}/{setting}/difference")
            close(reduction, stored_reduction, f"{round_name}/{setting}/reduction")
            deviations = {}
            for world, cell in means.items():
                deviation = (
                    float(cell[candidate]["mean_cost"]) - float(cell[best]["mean_cost"])
                ) / float(cell[best]["mean_cost"])
                close(deviation, stored_world[world], f"{round_name}/{setting}/{world}")
                deviations[world] = deviation
            ten = reduction >= 0.1 - 1e-12
            ci = float(stored_diff["hi"]) < 0
            world_rule = max(deviations.values()) <= 0.1 + 1e-12
            if (ten, ci, world_rule) != (
                claim["pass_10pct"],
                claim["pass_ci_excludes_0"],
                claim["pass_no_world_over_10pct_worse"],
            ):
                raise ValueError(f"{round_name}/{setting} gate flags mismatch")
            output.append(
                {
                    "setting": setting,
                    "selected_best": best,
                    "relative_reduction_percent": reduction * 100,
                    "percentage_points_from_10_percent": (reduction - 0.1) * 100,
                    "paired_mean_cost_difference": diff,
                    "stored_paired_interval": [stored_diff["lo"], stored_diff["hi"]],
                    "maximum_world_worsening_percent": max(deviations.values()) * 100,
                    "passes_10pct": ten,
                    "passes_stored_ci": ci,
                    "passes_world_rule": world_rule,
                    "all_three": ten and ci and world_rule,
                }
            )
        if len(output) != 4:
            raise ValueError("four setting panel incomplete")
        positive = all(row["all_three"] for row in output)
        negative = sum(row["paired_mean_cost_difference"] >= 0 for row in output) >= 2
        verdict = "POSITIVE" if positive else "NEGATIVE" if negative else "MIXED"
        if verdict != summary["decisions"]["Q1"]:
            raise ValueError("Q1 verdict mismatch")
        result["rounds"][round_name] = {
            "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "candidate": candidate,
            "settings": output,
            "registered_verdict": verdict,
            "gate_arithmetic_mismatches": 0,
        }
    result["limitations"] = (
        "B1 uses archived summary arithmetic only; B2 raw seed/bootstrap arithmetic is separately checked in B2_RECOMPUTATION.json. Stored intervals here are not independently recomputed, and BEST is selected on evaluation seeds. P5 is oracle headroom, not an eligible deployable BEST."
    )
    return result


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("B1/B2: eight setting gates reconciled; both Q1 MIXED")
