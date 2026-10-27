import hashlib
import json

import numpy as np
import pandas as pd
import pytest

import scripts.run_gated_monitor_comparison as runner


def historic_schema_fixture(tmp_path, monkeypatch):
    # Synthetic zero increments exercise the historical file schema, not the DGP.
    directory = tmp_path / "historic"
    (directory / "metrics").mkdir(parents=True)
    (directory / "reports").mkdir()
    path = directory / "metrics/event_traces.parquet"
    pd.DataFrame(
        {
            "seed": np.arange(20373024, 20373084),
            "event_offset": 0,
            "method": "uniform_proxy",
            "scenario": "boundary_local_harm",
            "propensity": 0.2,
            "ppi_increment": 0.0,
            "learner_log_e": 0.0,
        }
    ).to_parquet(path, index=False)
    receipt = {
        "sha256": {
            "artifacts": {
                "metrics\\event_traces.parquet": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        }
    }
    (directory / "reports/manifest.json").write_text(json.dumps(receipt), encoding="utf-8")
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "HISTORIC", directory)
    return path


def test_fidelity_replays_historic_ppi_schema_and_does_not_weaken_count_gate(tmp_path, monkeypatch):
    historic_schema_fixture(tmp_path, monkeypatch)
    rows, result = runner.fidelity()
    assert len(rows) == 120
    assert result["counts"] == {"uniform_ppi": 0, "uniform_ppi_common96p9": 0}
    assert not result["passes"]


def test_fidelity_refuses_tampered_source_before_reading_increments(tmp_path, monkeypatch):
    path = historic_schema_fixture(tmp_path, monkeypatch)
    with path.open("ab") as stream:
        stream.write(b"tampered")
    with pytest.raises(RuntimeError, match="checksum"):
        runner.fidelity()
