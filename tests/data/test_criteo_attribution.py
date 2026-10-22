import gzip
import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from shiftlab.data.real import criteo_attribution as adapter
from shiftlab.data.real.adapters import acquire
from shiftlab.data.real.wilds import load_input
from shiftlab.data.validation import validate_dataset


def _source(path: Path):
    rows = [
        [0, "u1", "c1", 0, -1, -1, 0, 0, -1, -1, 0.1, -1, -1, *[f"a{i}" for i in range(1, 10)]],
        [
            3600,
            "u1",
            "c1",
            1,
            7200,
            11,
            1,
            1,
            0,
            1,
            0.2,
            0.4,
            3600,
            *[f"b{i}" for i in range(1, 10)],
        ],
        [86400, "u2", "c2", 0, -1, -1, 0, 0, -1, -1, 0.1, -1, 10, *[f"c{i}" for i in range(1, 10)]],
        [
            172800,
            "u3",
            "c2",
            1,
            172800 + 600,
            12,
            1,
            1,
            0,
            1,
            0.3,
            0.5,
            20,
            *[f"d{i}" for i in range(1, 10)],
        ],
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write("\t".join(adapter.FIELDS) + "\n")
        for row in rows:
            handle.write("\t".join(map(str, row)) + "\n")
    return path


def test_official_attribution_import_preserves_delayed_labels_and_hides_outcomes(
    tmp_path, monkeypatch
):
    raw = _source(tmp_path / "fixture.tsv.gz")
    readme = tmp_path / "README.md"
    readme.write_text("pinned Criteo test fixture", encoding="utf-8")
    monkeypatch.setattr(adapter, "FILE_BYTES", raw.stat().st_size)
    monkeypatch.setattr(adapter, "FILE_SHA256", hashlib.sha256(raw.read_bytes()).hexdigest())

    def local_file(url, destination, **kwargs):
        return readme if str(destination).endswith("README.md") else raw

    monkeypatch.setattr(adapter, "download", local_file)
    version = acquire("criteo_attribution", {"chunk_size": 2}, tmp_path / "study")
    observations = pd.read_parquet(version / "observations.parquet")
    assert len(observations) == 4
    assert observations.sample_id.is_unique
    assert observations.target.tolist() == [0, 1, 0, 1]
    assert observations.event_time.tolist() == [0.0, 3600.0, 86400.0, 172800.0]
    assert observations.label_available_time.tolist() == [
        adapter.WINDOW_SECONDS,
        3600.0 + adapter.WINDOW_SECONDS,
        86400.0 + adapter.WINDOW_SECONDS,
        172800.0 + adapter.WINDOW_SECONDS,
    ]
    assert "feature_reference" in observations
    assert observations.features.map(len).eq(0).all()

    first_input = load_input(version, observations.feature_reference.iloc[0])
    assert set(first_input) == set(adapter.INPUT_FIELDS)
    assert first_input["campaign"] == "c1"
    assert "conversion" not in first_input
    assert "cost" not in first_input
    oracle = pd.read_parquet(version / "evaluator_only" / "oracle.parquet")
    assert oracle.click.tolist() == ["0", "1", "0", "1"]
    assert oracle.cpo.tolist() == ["-1", "0.4", "-1", "0.5"]
    assert validate_dataset(version)["rows"] == 4
    manifest = json.loads((version / "dataset_manifest.json").read_text())
    assert manifest["n_observations"] == 4
    assert manifest["feature_kind"] == "structured_reference"
    assert manifest["retrieval_parameters"]["revision"] == adapter.REVISION


@pytest.mark.parametrize(
    "config",
    [{"chunk_size": True}, {"chunk_size": 0}, {"max_download_bytes": 100}],
)
def test_invalid_configuration_is_rejected_before_download(tmp_path, monkeypatch, config):
    def no_download(*args, **kwargs):
        pytest.fail("invalid configuration attempted a download")

    monkeypatch.setattr(adapter, "download", no_download)
    with pytest.raises(ValueError):
        acquire("criteo_attribution", config, tmp_path / "data")
