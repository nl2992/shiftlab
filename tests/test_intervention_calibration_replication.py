import json
from hashlib import sha256

from shiftlab.dive.intervention_calibration_replication import (
    FROZEN_DESIGN,
    run_calibration_replication,
)


def test_cpu_calibration_replication_smoke_keeps_frozen_nine_cell_family(tmp_path):
    metrics, summary, calibration, manifest = run_calibration_replication(
        tmp_path,
        seeds=2,
        seed_offset=789_123,
        horizon=100,
        device="cpu",
    )
    assert manifest["frozen_design"] == FROZEN_DESIGN
    assert manifest["calibration_family_cells"] == 9
    assert manifest["metric_rows"] == 40
    assert len(summary) == 5 * 4
    assert len(calibration) == 9
    assert metrics.budget_respected.all()
    assert (
        manifest["metrics_sha256"]
        == sha256((tmp_path / "metrics.parquet").read_bytes()).hexdigest()
    )
    assert json.loads((tmp_path / "manifest.json").read_text())["seed_offset"] == 789_123
