from shiftlab.dive.delayed_evidence_directed_ppi import METHODS, Config, simulate_seed
from shiftlab.dive.delayed_evidence_directed_ppi_calibration import exact_upper
from shiftlab.dive.delayed_evidence_directed_ppi_confirmation import run as run_confirmation


def test_delayed_history_directed_ppi_grid_respects_budget_and_resolves_prefix():
    config = Config(
        seeds=2,
        n_source=120,
        n_target=240,
        budget_rate=0.2,
        max_delay=5,
        device="cpu",
    )
    rows = simulate_seed(config, seed=43, scenario="boundary_harm")
    assert {row["method"] for row in rows} == set(METHODS)
    for row in rows:
        assert row["budget_respected"]
        assert row["labels_queried"] <= row["hard_label_cap"]
        assert row["events_registered"] == row["events_updated"]
        assert row["pending_labels"] == 0
        assert row["events_registered"] <= config.n_target


def test_matched_grid_uses_registered_method_family_and_outcome_free_source_proxy():
    config = Config(n_source=180, n_target=300, max_delay=0, device="cpu")
    rows = simulate_seed(config, seed=107, scenario="benign_variance_shift")
    assert len(rows) == len(METHODS)
    assert len({row["proxy_source_slope"] for row in rows}) == 1
    assert len({row["proxy_source_intercept"] for row in rows}) == 1
    assert all(row["events_registered"] == row["events_updated"] for row in rows)


def test_calibration_uses_one_sided_exact_upper_limits():
    alpha = 0.05 / 4
    upper_zero = exact_upper(0, 1000, cell_alpha=alpha)
    upper_one = exact_upper(1, 1000, cell_alpha=alpha)
    assert 0 < upper_zero < 0.005
    assert upper_one > upper_zero


def test_confirmation_refuses_to_run_without_a_passing_calibration(tmp_path):
    import json

    import pytest

    calibration = tmp_path / "calibration.json"
    calibration.write_text(
        json.dumps(
            {
                "gate_pass": False,
                "invariants_pass": True,
                "methods": ["evidence_a0p025_p0p5_eventwise"],
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="requires a passing calibration"):
        run_confirmation(
            Config(n_source=120, n_target=240, device="cpu"),
            tmp_path / "confirmation",
            calibration_manifest=calibration,
        )
