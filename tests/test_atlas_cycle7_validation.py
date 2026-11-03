import json

import numpy as np
import pytest

from scripts import run_atlas_cycle7_validation_v1 as c7
from shiftlab.dive.atlas_dependence_baselines import MarkovLREProcess
from shiftlab.dive.eprocess import VectorizedStartedMixtureEProcess


@pytest.mark.parametrize("name", (*c7.BASELINES, *c7.VARIANTS))
def test_alarm_cache_preserves_full_trajectory(name, monkeypatch):
    cell = c7.fa.Family3CellSpec(0.8, 0.3, 0.6, "strong", "harmful", 3, 0.25, T=120)
    cfg, stream = cell.config(180123), c7.fa.make_stream(cell, 180123)
    cached = c7.fa.run_for(cell, stream, c7.make_method(name, cfg), cfg)
    with monkeypatch.context() as patch:
        for cls in (VectorizedStartedMixtureEProcess, MarkovLREProcess):
            patch.setattr(cls, "alarm", property(lambda ep: ep.log_e_value >= -np.log(ep.alpha)))
        original = c7.fa.run_for(cell, stream, c7.make_method(name, cfg), cfg)
    assert np.array_equal(cached.actions, original.actions)
    assert np.array_equal(cached.query_mask, original.query_mask)
    assert cached.cost == original.cost


def synthetic_records():
    seeds = [1, 2, 3, 4]
    jobs = [
        {"key": k, "kind": "cost", "methods": (*c7.BASELINES, *c7.VARIANTS)} for k in ("one", "two")
    ]
    plan = {
        "smoke": False,
        "seeds": seeds,
        "primary": ["one", "two"],
        "neighbours": {"one": ["two"], "two": ["one"]},
        "jobs": jobs,
    }
    records = {}
    for key, delta in (("one", [-0.1, -0.2, -0.1, -0.2]), ("two", [-0.2, -0.1, -0.2, -0.1])):
        values = {}
        for name in (*c7.BASELINES, *c7.VARIANTS):
            costs = (
                0.5 + np.array(delta)
                if name != "uniform" and name in c7.VARIANTS
                else np.full(4, 0.5)
            )
            values[name] = [
                {"cost": float(v), "fp": 0, "queries": 10, "promoted": 1, "correct": 1}
                for v in costs
            ]
        records[(key, tuple(seeds))] = {"key": key, "seeds": seeds, "values": values}
    return plan, records


def test_acceptance_aggregates_cells_within_seed_and_preserves_ablation_roles():
    plan, records = synthetic_records()
    result = c7.analyse(plan, records)
    # Opposite fluctuations cancel within seed. Treating cells as independent would
    # invent uncertainty for an aggregate that is constant on these streams.
    assert result["A1"]["aggregate"] == pytest.approx([-0.15, -0.15, -0.15])
    assert result["A1"]["pass"] and result["A2"]["pass"]
    assert result["A4"]["uniform"]["fraction_removed"] == pytest.approx(1)
    assert result["A4"]["uniform"]["pass"]
    assert not result["A4"]["gap1"]["pass"]
    assert not result["A4"]["no_delay_switch"]["pass"]


def test_incomplete_seeds_and_duplicate_chunks_are_rejected(tmp_path):
    plan, records = synthetic_records()
    records[("one", (1, 2, 3, 4))]["seeds"] = [1, 2, 3]
    with pytest.raises(ValueError, match="incomplete seed"):
        c7.analyse(plan, records)
    row = {"key": "one", "seeds": [1], "manifest_digest": "abc"}
    path = tmp_path / "records.jsonl"
    path.write_text(json.dumps(row) + "\n" + json.dumps(row) + "\n")
    with pytest.raises(ValueError, match="duplicate"):
        c7.load_records(path, "abc")
    with pytest.raises(ValueError, match="another manifest"):
        c7.load_records(path, "other")
