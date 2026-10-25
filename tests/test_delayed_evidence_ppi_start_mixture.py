import json
from pathlib import Path

import pandas as pd

from shiftlab.dive.delayed_evidence_directed_ppi import Config
from shiftlab.dive.delayed_evidence_ppi_start_mixture import run


def test_delayed_ppi_start_mixture_smoke_has_complete_matched_grid(tmp_path: Path):
    root = Path(__file__).parents[1]
    output = tmp_path / "start_mixture_smoke"
    run(
        Config(seeds=2, seed_offset=20310000, device="cpu"),
        output,
        protocol=root / "docs/delayed_evidence_ppi_matched_shadow_grid_protocol.md",
        matched_shadow=True,
    )
    metrics = pd.read_parquet(output / "metrics.parquet")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert len(metrics) == 24
    assert not metrics.duplicated(["seed", "onset_fraction", "method", "monitor_variant"]).any()
    assert manifest["invariants_pass"]
    assert manifest["matched_shadow"]
    assert set(metrics.monitor_variant) == {"full_stream", "fixed_start_mixture"}
    assert metrics.budget_respected.all()
    paired = metrics.pivot(
        index=["seed", "onset_fraction", "method"],
        columns="monitor_variant",
        values=["query_schedule_sha256", "labels_queried", "events_updated"],
    )
    assert (
        paired["labels_queried"]["full_stream"] == paired["labels_queried"]["fixed_start_mixture"]
    ).all()
    assert (
        paired["events_updated"]["full_stream"] == paired["events_updated"]["fixed_start_mixture"]
    ).all()
    assert (
        paired["query_schedule_sha256"]["full_stream"]
        == paired["query_schedule_sha256"]["fixed_start_mixture"]
    ).all()
