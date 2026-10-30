import importlib.util
import json
from pathlib import Path

import pytest

from shiftlab.sota_search.adapters import AdapterConfig
from shiftlab.sota_search.generators import WorldConfig

spec = importlib.util.spec_from_file_location("replication_draft", Path(__file__).with_name("sota_replication_draft.py"))
draft = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draft)


def test_replications_preserve_per_world_costs_source_usage_and_unique_snapshots(tmp_path):
    world = WorldConfig(horizon=100)
    adapter = AdapterConfig(track="Q3", method="frozen")
    root = tmp_path / "replications"
    result = draft.replicate(root, world, adapter, seeds=[51, 52])
    rows = [json.loads(line) for line in (root / "per_world.jsonl").read_text().splitlines()]
    assert len(rows) == result["independent_worlds"] == 2
    assert result["source_labels"] == 200
    assert result["labels_used"] == 0
    assert all((root / row["trajectory"]).exists() for row in rows)
    assert result["mean_expected_net_cost"] == pytest.approx(
        sum(row["metrics"]["expected_net_cost"] for row in rows) / 2
    )
    with pytest.raises(FileExistsError):
        draft.replicate(root, world, adapter, seeds=[51, 52])


def test_duplicate_worlds_cannot_masquerade_as_independent_replications(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        draft.replicate(tmp_path / "duplicate", WorldConfig(horizon=100), AdapterConfig(), seeds=[51, 51])
