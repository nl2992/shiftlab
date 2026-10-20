from shiftlab.data.replication import replicate_grid_integrity


def test_replication_grid_accepts_exact_preset_seed_coverage():
    records = [
        {"preset": preset, "seed": seed} for preset in ["alpha", "beta"] for seed in [11, 23]
    ]
    result = replicate_grid_integrity(records, ["alpha", "beta"], [11, 23])
    assert result["passes"]
    assert result["expected_records"] == result["observed_records"] == 4


def test_replication_grid_reports_missing_duplicate_and_unexpected_pairs():
    records = [
        {"preset": "alpha", "seed": 11},
        {"preset": "alpha", "seed": 11},
        {"preset": "beta", "seed": 11},
        {"preset": "unknown", "seed": 23},
    ]
    result = replicate_grid_integrity(records, ["alpha", "beta"], [11, 23])
    assert not result["passes"]
    assert result["missing_pairs"] == [
        {"preset": "alpha", "seed": 23},
        {"preset": "beta", "seed": 23},
    ]
    assert result["duplicate_pairs"] == [{"preset": "alpha", "seed": 11}]
    assert result["unexpected_pairs"] == [{"preset": "unknown", "seed": 23}]
