import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("analysis_draft", Path(__file__).with_name("sota_screen_analysis.py"))
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def records():
    output = []
    for track in analysis.PRIMARY:
        for family in ("G1", "G2", "G3", "G4"):
            for scenario in ("stationary", "benign_covariate", *sorted(analysis.ALTERNATIVES)):
                for index in range(9):
                    output.append({
                        "configuration_hash": f"{track}:{family}:{scenario}:{index}",
                        "execution_status": "completed",
                        "hyperparameters": {"track": track, "method": f"method{index}", "query": "uniform"},
                        "generator_family": family, "shift_type": scenario, "random_seed": 1,
                        "secondary_metrics": {analysis.PRIMARY[track]: index},
                    })
    return output


def test_selection_refuses_partial_or_duplicate_archives():
    rows = records()
    assert len(rows) == 540
    with pytest.raises(ValueError, match="complete"):
        analysis.select(rows[:-1])
    rows[-1] = rows[0]
    with pytest.raises(ValueError, match="duplicated"):
        analysis.select(rows)


def test_ranking_directions_and_mandatory_controls():
    result = analysis.select(records())["tracks"]
    assert result["Q1"]["ranking"][0]["variant"] == ("method0", "uniform")
    assert result["Q2"]["ranking"][0]["variant"] == ("method8", "uniform")
    assert result["Q3"]["ranking"][0]["variant"] == ("method0", "uniform")
    for track in result:
        assert analysis.PARENTS[track] <= set(result[track]["survivors"])


def test_failed_world_cannot_improve_rank_by_disappearing():
    rows = records()
    row = next(r for r in rows if r["shift_type"] in analysis.ALTERNATIVES)
    row["execution_status"] = "resource_limit"
    result = analysis.select(rows)
    assert row["configuration_hash"] in result["failed_configuration_hashes"]
    assert ("method0", "uniform") not in [r["variant"] for r in result["tracks"]["Q1"]["ranking"]]
