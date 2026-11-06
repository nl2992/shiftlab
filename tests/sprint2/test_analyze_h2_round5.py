import pandas as pd
import pytest

from scripts.sota_sprint.analyze_h2_round5 import frame, t_summary, wilson


def test_wilson_intervals_cover_boundary_cases():
    lo0, hi0 = wilson(0, 1000)
    lo1, hi1 = wilson(1000, 1000)
    assert lo0 == 0
    assert 0 < hi0 < 0.01
    assert 0.99 < lo1 < 1
    assert hi1 == 1


def test_paired_t_summary_reports_mean_and_interval():
    result = t_summary([1, 2, 3])
    assert result["n"] == 3
    assert result["mean"] == 2
    assert result["ci95"][0] < 2 < result["ci95"][1]


def test_frame_requires_complete_unique_policy_seed_cells(tmp_path):
    rows = [
        {"regime": regime, "ep": 0, "seed": seed, "policy": policy}
        for regime in ("r1", "r2")
        for seed in (0, 1)
        for policy in ("H2", "D2")
    ]
    path = tmp_path / "records.jsonl"
    pd.DataFrame(rows).to_json(path, orient="records", lines=True)
    assert len(frame(path, ["H2", "D2"], 2, datasets=["r1", "r2"])) == 8
    pd.DataFrame(rows[:-1]).to_json(path, orient="records", lines=True)
    with pytest.raises(ValueError, match="coverage mismatch|incomplete or duplicate"):
        frame(path, ["H2", "D2"], 2, datasets=["r1", "r2"])
