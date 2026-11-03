"""Reconcile integrated efficacy seed means and predeclared contrasts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT.parent
    / "shift-research-starter"
    / "outputs"
    / "shiftguard_unified"
    / "integrated_confirmation"
    / "efficacy_100_v1"
)
DEST = ROOT / "docs" / "retrospective_audit_2026_11_01" / "INTEGRATED_EFFICACY_SEED_AUDIT.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run() -> dict[str, object]:
    verification = json.loads(
        (SOURCE / "analysis_v3/verification.json").read_text(encoding="utf-8")
    )
    checked = 0
    for raw_name, expected in {
        **verification["artifact_sha256"],
        **verification["analysis_outputs_sha256"],
    }.items():
        relative = raw_name.replace("\\", "/").split("efficacy_100_v1/", 1)[1]
        if sha256(SOURCE / relative) != expected:
            raise AssertionError(f"Archived hash mismatch: {relative}")
        checked += 1
    frame = pd.read_parquet(SOURCE / "integrated_pipeline_seed_metrics.parquet")
    summary = pd.read_csv(SOURCE / "integrated_pipeline_summary.csv")
    primary = pd.read_csv(SOURCE / "analysis_v3/primary_contrasts.csv")
    if len(frame) != 7200 or len(summary) != 72 or len(primary) != 22:
        raise AssertionError("Unexpected integrated panel dimensions")
    for (scenario, method), group in frame.groupby(["scenario", "method"]):
        if len(group) != 100 or group.seed.nunique() != 100:
            raise AssertionError(f"Incomplete integrated cell: {scenario}/{method}")
        archived = summary[(summary.scenario == scenario) & (summary.method == method)].iloc[0]
        for field, source_field in (
            ("mean_expected_gain", "expected_incremental_utility"),
            ("mean_realized_gain", "realized_incremental_utility"),
            ("mean_labels", "total_labels"),
        ):
            if abs(float(archived[field]) - float(group[source_field].mean())) > 1e-9:
                raise AssertionError(f"Integrated summary mismatch: {scenario}/{method}/{field}")
    contrasts = []
    for row in primary.itertuples(index=False):
        treatment = frame[(frame.scenario == row.profile) & (frame.method == row.treatment)]
        reference = frame[(frame.scenario == row.profile) & (frame.method == row.reference)]
        paired = (
            treatment.set_index("seed")["expected_incremental_utility"]
            - reference.set_index("seed")["expected_incremental_utility"]
        )
        if (
            len(paired) != 100
            or abs(float(paired.mean()) - row.mean_paired_expected_utility_difference) > 1e-9
        ):
            raise AssertionError(f"Primary contrast mismatch: {row.profile}/{row.reference}")
        contrasts.append(
            {
                "profile": row.profile,
                "treatment": row.treatment,
                "reference": row.reference,
                "mean_difference": float(paired.mean()),
            }
        )
    full = summary[summary.method == "full_pipeline"].set_index("scenario")
    return {
        "scope": "Stored seed metrics, summary and primary contrast arithmetic; no simulator/event-log replay or inference resampling",
        "archived_hashes_checked": checked,
        "seed_metric_rows": len(frame),
        "profile_method_cells": len(summary),
        "primary_contrasts_checked": len(contrasts),
        "all_hard_caps_respected": bool((frame.total_labels <= frame.hard_label_cap).all()),
        "max_labels": int(frame.total_labels.max()),
        "full_pipeline_profile_expected_gain": {
            str(key): float(value) for key, value in full.mean_expected_gain.items()
        },
        "contrasts": contrasts,
    }


if __name__ == "__main__":
    result = run()
    DEST.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(result["archived_hashes_checked"], result["primary_contrasts_checked"])
