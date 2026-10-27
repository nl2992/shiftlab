"""Independently verify the Molitor OPI calibration artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/molitor_opi_calibration_v1"
EXPECTED_SCENARIOS = {"all_policies_tied_null", "unique_best_action_1"}
EXPECTED_ALLOCATIONS = {
    "familywise_two_tail",
    "source_style_alpha_over_m_each_tail",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def interval(events: int, n: int) -> tuple[float, float]:
    q = 0.025
    return (
        0.0 if events == 0 else float(beta.ppf(q, events, n - events + 1)),
        1.0 if events == n else float(beta.ppf(1.0 - q, events + 1, n - events)),
    )


def main() -> None:
    manifest = json.loads((OUTPUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "complete"
    assert manifest["seeds_per_scenario"] == 1_000
    assert manifest["horizon"] == 2_000
    for relative_path, expected_hash in manifest["source_sha256"].items():
        assert sha256(ROOT / relative_path) == expected_hash, relative_path
    metrics_path = OUTPUT / "per_stream_metrics.parquet"
    summary_path = OUTPUT / "summary.parquet"
    assert sha256(metrics_path) == manifest["output_sha256"][metrics_path.name]
    assert sha256(summary_path) == manifest["output_sha256"][summary_path.name]
    metrics = pd.read_parquet(metrics_path)
    saved_summary = pd.read_parquet(summary_path)
    csv_metrics = pd.read_csv(OUTPUT / "per_stream_metrics.csv")
    csv_summary = pd.read_csv(OUTPUT / "summary.csv")
    pd.testing.assert_frame_equal(metrics, csv_metrics, check_dtype=False)
    pd.testing.assert_frame_equal(saved_summary, csv_summary, check_dtype=False)
    assert len(metrics) == 4_000
    assert set(metrics["scenario"]) == EXPECTED_SCENARIOS
    assert set(metrics["allocation"]) == EXPECTED_ALLOCATIONS
    assert metrics.groupby(["scenario", "allocation"]).size().eq(1_000).all()
    assert metrics.groupby(["scenario", "allocation"])["replication_id"].nunique().eq(1_000).all()
    assert metrics["stopping_time_censored"].between(1, 2_001).all()
    assert metrics["final_candidate_set_size"].between(1, 3).all()

    for row in saved_summary.itertuples(index=False):
        cell = metrics[
            (metrics["scenario"] == row.scenario) & (metrics["allocation"] == row.allocation)
        ]
        false_eliminations = int(cell["false_optimal_elimination"].sum())
        false_ci = interval(false_eliminations, len(cell))
        assert row.streams == len(cell)
        assert row.false_optimal_eliminations == false_eliminations
        assert np.isclose(row.false_elimination_ci95_low, false_ci[0])
        assert np.isclose(row.false_elimination_ci95_high, false_ci[1])
        unique_stops = int(cell["unique_policy_stopped"].sum())
        assert row.unique_stops == unique_stops
        stop_ci = interval(unique_stops, len(cell))
        assert np.isclose(row.unique_stop_ci95_low, stop_ci[0])
        assert np.isclose(row.unique_stop_ci95_high, stop_ci[1])
        correct = int(cell["correct_identification_at_horizon"].sum())
        assert row.correct_identifications_at_horizon == correct
        assert np.isclose(row.correct_identification_rate, correct / len(cell))

    null = metrics[metrics["scenario"] == "all_policies_tied_null"]
    assert not null["unique_policy_stopped"].any()
    print(
        "Verified 4,000 stream-allocation rows, 4 summary cells, scenario and "
        "replication coverage, exact confidence intervals, and Parquet hashes."
    )


if __name__ == "__main__":
    main()
