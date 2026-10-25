import json

import numpy as np

from shiftlab.dive.contextual_weighted_alpha_grid import generate_proxy_streams
from shiftlab.dive.contextual_weighted_alpha_validation import (
    CALIBRATION_CELLS,
    _cp_upper,
    _generate_calibration_gains,
    run_calibration,
    run_confirmation,
)


def test_simultaneous_calibration_family_and_exact_upper_bound():
    assert CALIBRATION_CELLS == 54
    assert 0 < _cp_upper(0, 2_000, 0.05 / 54) < 0.01
    assert _cp_upper(1, 2_000, 0.05 / 54) > _cp_upper(0, 2_000, 0.05 / 54)


def test_calibration_boundary_generator_has_registered_group_means():
    _, _, _, contexts, _ = generate_proxy_streams(
        scenario="heterogeneous_reversal",
        seeds=1,
        horizon=200,
        true_harmful_prevalence=0.25,
        proxy_error_rate=0.05,
        seed=71,
        device="cpu",
    )
    gains = _generate_calibration_gains(
        contexts=contexts,
        seeds=1_000,
        horizon=200,
        calibration_type="rollback_boundary",
        rollback_cost=0.05,
        seed=72,
        device="cpu",
    )
    for group in range(2):
        indices = np.flatnonzero(contexts == group)
        n_group = len(indices) // 2
        assert np.isclose(gains[:, indices[:n_group]].mean(), 2.0, atol=0.06)
        assert np.isclose(gains[:, indices[n_group:]].mean(), -0.05 / n_group, atol=0.04)


def test_calibration_cpu_smoke_writes_all_cells(tmp_path):
    table, manifest = run_calibration(
        tmp_path,
        seeds=2,
        seed_offset=103_102_024,
        horizon=200,
        device="cpu",
    )
    assert len(table) == CALIBRATION_CELLS
    assert manifest["status"] == "failed"  # two streams cannot satisfy the registered risk-set gate
    assert (tmp_path / "calibration.csv").is_file()
    assert (tmp_path / "manifest.json").is_file()


def test_confirmation_cpu_smoke_requires_calibration_and_writes_primary(tmp_path):
    calibration = {
        "status": "passed",
        "seed_offset": 103_102_024,
        "seeds_per_cell": 2,
        "horizon_per_phase": 200,
    }
    calibration_path = tmp_path / "calibration.json"
    calibration_path.write_text(json.dumps(calibration), encoding="utf-8")
    primary, manifest = run_confirmation(
        tmp_path / "confirmation",
        calibration_path,
        seeds=2,
        seed_offset=113_102_024,
        horizon=200,
        bootstrap_replicates=100,
        device="cpu",
    )
    assert len(primary) == 1
    assert manifest["profile_count"] == 9
    assert manifest["settings_per_profile"] == 12
    assert manifest["all_label_caps_respected"]
    assert (tmp_path / "confirmation" / "metrics.parquet").is_file()
