"""Reconcile the archived WP2 analytic screen from its raw learner-slice rows."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT.parent / "shift-research-starter" / "outputs" / "stratified_growth_prescreen_20"
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "WP2_RAW_RECOMPUTATION.json"
MATCHED = (
    "chugg_subgroup_composition",
    "stratified_common_bound",
    "stratified_proportional_query",
    "pooled_same_query_global_bound",
    "pooled_uniform_correct_bound_U1",
    "gated_pooled_HT_G1f",
)


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def near(actual: float, expected: float, label: str, tolerance: float = 1e-12) -> None:
    if abs(actual - expected) > tolerance:
        raise ValueError(f"mismatch for {label}: {actual} versus {expected}")


def run(source: Path = SOURCE) -> dict[str, object]:
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest["outputs_sha256"].items():
        if sha256(source / name) != expected:
            raise ValueError(f"manifest hash mismatch: {name}")

    scalar: dict[tuple[int, float, int, str, str, str], dict[str, object]] = {}
    with (source / "rows.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            key = (
                int(row["seed"]),
                float(row["budget_rate"]),
                int(row["K"]),
                str(row["allocation"]),
                str(row["working_law"]),
                str(row["arm"]),
            )
            if key in scalar:
                raise ValueError(f"duplicate raw row: {key}")
            scalar[key] = {
                name: row[name]
                for name in (
                    "feasible",
                    "pooled_centered_mean",
                    "max_component_growth",
                    "expected_spend",
                    "target_spend",
                )
            }
            scalar[key]["identity_error"] = row.get("identity_error", 0.0)
    if len(scalar) != 19_440 or len(scalar) != int(manifest["rows"]):
        raise ValueError("raw row count mismatch")

    with (source / "stream_summary.csv").open(newline="", encoding="utf-8") as stream:
        stream_rows = list(csv.DictReader(stream))
    if len(stream_rows) != len(scalar):
        raise ValueError("stream summary row count mismatch")
    for row in stream_rows:
        key = (
            int(row["seed"]),
            float(row["budget_rate"]),
            int(row["K"]),
            row["allocation"],
            row["working_law"],
            row["arm"],
        )
        original = scalar[key]
        if (row["feasible"] == "True") != original["feasible"]:
            raise ValueError(f"feasibility mismatch: {key}")
        for field in (
            "pooled_centered_mean",
            "max_component_growth",
            "expected_spend",
            "target_spend",
        ):
            near(float(row[field]), float(original[field]), f"{key}/{field}")

    groups: dict[tuple[float, int, str, str, str], list[dict[str, object]]] = defaultdict(list)
    for key, row in scalar.items():
        groups[key[1:]].append(row)
    with (source / "summary.csv").open(newline="", encoding="utf-8") as stream:
        archived_summary = {
            (
                float(row["budget_rate"]),
                int(row["K"]),
                row["allocation"],
                row["working_law"],
                row["arm"],
            ): row
            for row in csv.DictReader(stream)
        }
    if set(groups) != set(archived_summary):
        raise ValueError("summary key coverage mismatch")
    means: dict[tuple[float, int, str, str, str], dict[str, float | bool]] = {}
    for key, rows in groups.items():
        if len(rows) != 20 or int(archived_summary[key]["seeds"]) != 20:
            raise ValueError(f"incomplete seed block: {key}")
        values = {
            "mean_growth": sum(float(r["max_component_growth"]) for r in rows) / 20,
            "mean_pooled_centered_mean": sum(float(r["pooled_centered_mean"]) for r in rows) / 20,
            "mean_expected_spend": sum(float(r["expected_spend"]) for r in rows) / 20,
            "mean_target_spend": sum(float(r["target_spend"]) for r in rows) / 20,
            "all_feasible": all(bool(r["feasible"]) for r in rows),
        }
        for field, value in values.items():
            if field == "all_feasible":
                if value != (archived_summary[key][field] == "True"):
                    raise ValueError(f"summary feasibility mismatch: {key}")
            else:
                near(float(value), float(archived_summary[key][field]), f"{key}/{field}")
        means[key] = values

    maximum_pair_difference = 0.0
    matched_pairs = 0
    for key, row in scalar.items():
        if key[-1] != "stratified_candidate":
            continue
        counterpart = scalar[(*key[:-1], "chugg_subgroup_composition")]
        difference = abs(
            float(row["max_component_growth"]) - float(counterpart["max_component_growth"])
        )
        maximum_pair_difference = max(maximum_pair_difference, difference)
        matched_pairs += 1
    if matched_pairs != 2160:
        raise ValueError("candidate/subgroup pair coverage mismatch")

    decision = json.loads((source / "decision.json").read_text(encoding="utf-8"))
    if decision["gate"] != "G1" or len(decision["trials"]) != 36:
        raise ValueError("decision trial panel mismatch")
    trial_rows = []
    for trial in decision["trials"]:
        base = (float(trial["budget_rate"]), int(trial["K"]), trial["allocation"])
        local = (*base, "localized_harm")
        homogeneous = (*base, "homogeneous_harm")
        candidate = means[(*local, "stratified_candidate")]
        strongest = max(float(means[(*local, arm)]["mean_growth"]) for arm in MATCHED)
        reported_strongest = float(means[(*local, trial["strongest_incumbent"])]["mean_growth"])
        near(reported_strongest, strongest, f"strongest incumbent {base}")
        ratio = float(candidate["mean_growth"]) / strongest if strongest > 0 else None
        gated = float(means[(*homogeneous, "gated_pooled_HT_G1f")]["mean_growth"])
        homogeneous_ratio = (
            float(means[(*homogeneous, "stratified_candidate")]["mean_growth"]) / gated
            if gated > 0
            else None
        )
        eligible = bool(
            candidate["all_feasible"] and float(candidate["mean_pooled_centered_mean"]) > 0
        )
        if eligible != trial["positive_pooled_eligible"]:
            raise ValueError(f"eligibility mismatch: {base}")
        near(
            float(candidate["mean_growth"]),
            float(trial["candidate_mean_growth"]),
            f"candidate {base}",
        )
        near(strongest, trial["strongest_mean_growth"], f"strongest {base}")
        if ratio is not None:
            near(ratio, trial["growth_ratio"], f"growth ratio {base}")
        if homogeneous_ratio is not None:
            near(homogeneous_ratio, trial["homogeneous_over_gated"], f"homogeneous ratio {base}")
        passed = bool(
            eligible
            and ratio is not None
            and ratio >= 1.5
            and homogeneous_ratio is not None
            and homogeneous_ratio >= 0.8
        )
        if passed != trial["passes"]:
            raise ValueError(f"gate decision mismatch: {base}")
        trial_rows.append(
            {
                "budget_rate": base[0],
                "K": base[1],
                "allocation": base[2],
                "growth_ratio": ratio,
                "homogeneous_over_gated": homogeneous_ratio,
                "passes": passed,
            }
        )
    if any(row["passes"] for row in trial_rows) != decision["passes"]:
        raise ValueError("overall gate decision mismatch")
    maximum_identity_error = max(float(row["identity_error"]) for row in scalar.values())
    near(
        maximum_identity_error, float(decision["maximum_identity_error"]), "maximum identity error"
    )
    return {
        "status": "ARCHIVED_EXPOSED_ANALYTIC_SCREEN_ONLY",
        "source_manifest_sha256": sha256(manifest_path),
        "source_commit_claimed_by_manifest": manifest["git_head"],
        "raw_rows": len(scalar),
        "stream_rows_checked": len(stream_rows),
        "summary_groups_checked": len(groups),
        "candidate_chugg_pairs_checked": matched_pairs,
        "maximum_candidate_chugg_growth_difference": maximum_pair_difference,
        "maximum_archived_identity_error": maximum_identity_error,
        "decision_trials_checked": len(trial_rows),
        "decision_passes": decision["passes"],
        "minimum_eligible_growth_ratio": min(
            row["growth_ratio"] for row in trial_rows if row["growth_ratio"] is not None
        ),
        "maximum_eligible_growth_ratio": max(
            row["growth_ratio"] for row in trial_rows if row["growth_ratio"] is not None
        ),
        "aggregate_mismatches": 0,
        "limitations": "Recomputes archived scalar rows, aggregates, and gate arithmetic; does not regenerate learner slices or independently derive outcome/query expectations from the generator.",
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"{result['raw_rows']} raw rows; {result['decision_trials_checked']} gate trials; zero aggregate mismatches"
    )
