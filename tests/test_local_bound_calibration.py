from torch import device

from scripts.calibrate_decision_local_bounds import _cell


def test_calibration_cell_respects_pathwise_cap_and_records_both_bounds():
    rows = _cell(
        streams=100,
        horizon=100,
        query_rate=0.2,
        high_cost=5.0,
        outcome_probability=0.5,
        seed=12,
        device=device("cpu"),
    )
    assert len(rows) == 200
    assert {row["bound_mode"] for row in rows} == {"global", "decision_local"}
    assert all(row["labels_queried"] <= row["label_cap"] == 20 for row in rows)
    assert all(row["horizon_processed"] <= 100 for row in rows)
