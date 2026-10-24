import json
from hashlib import sha256

import numpy as np

from shiftlab.dive.intervention_sensitivity import run_grid, scenario_schedules


def test_reversal_schedules_have_registered_phase_means():
    horizon = 100
    schedules = scenario_schedules(horizon)
    reversal = schedules["reversal_onset_0.1_harm_0.2"]
    assert np.all(reversal[:horizon] == 0.30)
    assert np.all(reversal[horizon : horizon + 10] == 0.30)
    assert np.all(reversal[horizon + 10 :] == -0.20)


def test_cpu_sensitivity_smoke_writes_reproducible_outputs(tmp_path):
    metrics, summary, contrasts, macro, manifest = run_grid(
        tmp_path,
        seeds=2,
        seed_offset=987_654,
        horizon=100,
        device="cpu",
        bootstrap_replicates=100,
    )
    assert manifest["development_cells"] == 220
    assert manifest["metric_rows"] == 1760
    assert metrics.budget_respected.all()
    assert len(summary) == 220 * 4
    assert len(contrasts) == 220 * 3
    assert len(macro) == 36
    assert metrics.seed.nunique() == 20
    data = (tmp_path / "metrics.parquet").read_bytes()
    assert manifest["metrics_sha256"] == sha256(data).hexdigest()
    assert json.loads((tmp_path / "manifest.json").read_text())["metric_rows"] == 1760
