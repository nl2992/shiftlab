"""Add a transparent onset-eligibility note to the completed Q1 artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT / "outputs/shiftguard_unified/sota_reproductions/comparecast_paired_cost_confirmation_v1"
)
MANIFEST_PATH = OUTPUT / "manifest.json"
METRICS_PATH = OUTPUT / "metrics.parquet"
RESULTS_PATH = OUTPUT / "results.md"
ELIGIBILITY_PATH = OUTPUT / "onset_eligibility.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    for name, expected in manifest["artifact_sha256"].items():
        path = OUTPUT / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(f"refusing to amend artifact with a hash mismatch: {name}")

    metrics = pd.read_parquet(METRICS_PATH)
    eligibility: dict[str, dict[str, object]] = {}
    alternatives = (
        "boundary_local_harm",
        "residual_variance",
        "recurring_regimes",
        "harmful_adaptation",
    )
    for scenario in alternatives:
        group = metrics.loc[metrics["scenario"].eq(scenario)]
        unique_seeds = group.drop_duplicates("seed")
        eligible = set(unique_seeds.loc[unique_seeds["harm_onset_relative"].notna(), "seed"])
        scenario_result: dict[str, Any] = {
            "registered_streams": len(unique_seeds),
            "streams_with_evaluator_defined_material_harm_onset": len(eligible),
            "streams_without_realized_material_harm_onset": int(len(unique_seeds) - len(eligible)),
            "methods": {},
        }
        for method, method_group in group.groupby("method", sort=True):
            detected = set(
                method_group.loc[method_group["post_onset_detection"].astype(bool), "seed"]
            )
            scenario_result["methods"][str(method)] = {
                "post_onset_detections_among_all_300": len(detected),
                "joint_rate_over_all_300": float(len(detected) / len(unique_seeds)),
                "post_onset_detections_among_onset_eligible": len(detected & eligible),
                "conditional_descriptive_rate_among_onset_eligible": (
                    float(len(detected & eligible) / len(eligible)) if eligible else None
                ),
            }
        eligibility[scenario] = scenario_result

    expected = {
        "boundary_local_harm": (300, 0),
        "residual_variance": (299, 1),
        "recurring_regimes": (300, 0),
        "harmful_adaptation": (300, 0),
    }
    for scenario, values in eligibility.items():
        actual = (
            values["streams_with_evaluator_defined_material_harm_onset"],
            values["streams_without_realized_material_harm_onset"],
        )
        if actual != expected[scenario]:
            raise RuntimeError(f"unexpected onset eligibility for {scenario}: {actual}")

    ELIGIBILITY_PATH.write_text(json.dumps(eligibility, indent=2) + "\n", encoding="utf-8")
    note = (
        "\n\n**Onset-eligibility clarification (post-run audit):** all registered cells contain 300 seeds. "
        "In residual-variance shift, 299 seeds had an evaluator-defined material-harm onset and one did not. "
        "The table's pre-registered joint per-run counts and exact intervals use all 300 seeds, counting a "
        "stream without a realized onset as no post-onset detection. Conditional descriptive counts among "
        "the 299 onset-eligible seeds are 0/299 for Comparecast and 17/299 for the ShiftLab process; "
        "these conditional rates are not the registered interval endpoint. Full counts are in "
        "`onset_eligibility.json` and are checked by the independent verifier."
    )
    results = RESULTS_PATH.read_text(encoding="utf-8")
    if "Onset-eligibility clarification (post-run audit)" not in results:
        RESULTS_PATH.write_text(results.rstrip() + note + "\n", encoding="utf-8")

    manifest["post_run_interpretation"] = {
        "note": "One residual-variance stream had no evaluator-defined material-harm onset. Registered joint counts retain all 300 seeds; conditional rates among onset-eligible streams are descriptive only.",
        "onset_eligibility_sha256": sha256(ELIGIBILITY_PATH),
        "finalizer_sha256": sha256(Path(__file__).resolve()),
    }
    manifest["experiment"] = "comparecast_paired_cost_independent_confirmation"
    manifest["artifact_sha256"]["onset_eligibility.json"] = sha256(ELIGIBILITY_PATH)
    manifest["artifact_sha256"]["results.md"] = sha256(RESULTS_PATH)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(eligibility, indent=2))


if __name__ == "__main__":
    main()
