import json
from hashlib import sha256

from shiftlab.dive.intervention_confirmation import FROZEN_DESIGN, run_confirmation


def test_cpu_confirmation_smoke_is_frozen_and_has_phase_specific_calibration(tmp_path):
    metrics, summary, contrasts, macro, calibration, manifest = run_confirmation(
        tmp_path,
        seeds=2,
        seed_offset=123_456,
        horizon=100,
        device="cpu",
        bootstrap_replicates=100,
    )
    assert manifest["frozen_design"] == FROZEN_DESIGN
    assert manifest["metric_rows"] == 88
    assert len(summary) == 11 * 4
    assert len(contrasts) == 11 * 3
    assert len(macro) == 2
    assert len(calibration) == 9
    assert metrics.budget_respected.all()
    assert metrics.seed.nunique() == 22
    assert (
        manifest["metrics_sha256"]
        == sha256((tmp_path / "metrics.parquet").read_bytes()).hexdigest()
    )
    assert json.loads((tmp_path / "manifest.json").read_text())["calibration_family_cells"] == 9
