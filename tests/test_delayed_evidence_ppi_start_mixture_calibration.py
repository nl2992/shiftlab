import json
from pathlib import Path

import pandas as pd

from shiftlab.dive.delayed_evidence_directed_ppi import Config
from shiftlab.dive.delayed_evidence_ppi_start_mixture_calibration import run


def test_start_mixture_calibration_smoke_checks_null_and_matched_paths(tmp_path: Path):
    root = Path(__file__).parents[1]
    output = tmp_path / "start_mixture_calibration_smoke"
    run(
        Config(seeds=2, seed_offset=20321000, device="cpu"),
        output,
        protocol=root / "docs/delayed_evidence_ppi_start_mixture_calibration_protocol.md",
    )
    metrics = pd.read_parquet(output / "metrics.parquet")
    summary = pd.read_parquet(output / "calibration_summary.parquet")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert len(metrics) == 4
    assert len(summary) == 2
    assert manifest["invariants_pass"]
    assert manifest["matched_query_paths_pass"]
    assert not metrics.duplicated(["seed", "method", "monitor_variant"]).any()
    paired = metrics.pivot(
        index=["seed", "method"],
        columns="monitor_variant",
        values=["query_schedule_sha256", "labels_queried", "events_updated"],
    )
    for field in ("query_schedule_sha256", "labels_queried", "events_updated"):
        assert (paired[field]["full_stream"] == paired[field]["fixed_start_mixture"]).all()
