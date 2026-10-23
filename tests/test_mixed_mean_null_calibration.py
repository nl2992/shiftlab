import torch

from scripts.calibrate_mixed_mean_null_local_bounds import _simulate_cell


def test_mixed_sign_calibration_has_zero_aggregate_gain_and_respects_query_cap():
    rows = _simulate_cell(
        streams=120,
        horizon=120,
        high_cost=5.0,
        query_rate=0.2,
        seed=42,
        device=torch.device("cpu"),
    )

    assert {row["bound_mode"] for row in rows} == {"global", "decision_local"}
    assert all(row["aggregate_expected_gain"] == 0.0 for row in rows)
    assert all(row["labels_queried"] <= row["label_cap"] for row in rows)
    by_mode = {
        mode: {row["stream"]: row["labels_queried"] for row in rows if row["bound_mode"] == mode}
        for mode in ("global", "decision_local")
    }
    assert by_mode["global"] == by_mode["decision_local"]
