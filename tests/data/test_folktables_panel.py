import json
import zipfile

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.folktables import TASKS, acquire, comparison_plan
from shiftlab.data.validation import validate_dataset


def test_comparison_plan_domains_are_disjoint_and_coarse():
    plan = comparison_plan(["CA", "NJ"], [2018, 2019])
    assert {p["kind"] for p in plan["comparisons"]} == {
        "within_state_cross_year",
        "cross_state_same_year",
        "pooled_cross_year",
        "cross_state_cross_year",
    }
    for comparison in plan["comparisons"]:
        assert not set(comparison["train_domains"]) & set(comparison["test_domains"])
    assert comparison_plan(["NJ"], [2018])["comparisons"] == []


def fixtures(tmp_path, monkeypatch):
    package = pytest.importorskip("folktables")
    required = {"PWGTP", "HISP", "ST", "WKHP", "ESR"}
    for name in TASKS:
        task = getattr(package, name)
        required.update(task.features)
        required.add(task.target)
    paths = {}
    for year in [2018, 2019]:
        for state, code in [("CA", "06"), ("NJ", "34")]:
            n = 40
            source = pd.DataFrame({c: np.ones(n) for c in sorted(required)})
            source["AGEP"] = np.arange(n) % 20 + 20
            source["PINCP"] = np.where(np.arange(n) % 2, 60000, 20000)
            source["PWGTP"] = 100 + np.arange(n)
            source["WKHP"] = 40
            source["ESR"] = np.where(np.arange(n) % 2, 3, 1)
            source["RAC1P"] = 1 + np.arange(n) % 2
            source["ST"] = int(code)
            source.loc[0, "SCHL"] = np.nan
            if year == 2019:
                source["RELSHIPP"] = source["RELP"]
                source["JWTRNS"] = source["JWTR"]
                source = source.drop(columns=["RELP", "JWTR"])
            path = tmp_path / f"{state}-{year}.zip"
            with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(f"psam_p{code}.csv", source.to_csv(index=False))
            paths[state, year] = path

    def fetch(url, *args, **kwargs):
        year = int(url.split("/")[-3])
        state = url.rsplit("/", 1)[-1][5:7].upper()
        return paths[state, year]

    monkeypatch.setattr("shiftlab.data.real.folktables.download", fetch)
    return package


@pytest.mark.parametrize("task_name", sorted(TASKS))
def test_all_official_tasks_weights_groups_and_protocol(tmp_path, monkeypatch, task_name):
    fixtures(tmp_path, monkeypatch)
    config = {"states": ["CA", "NJ"], "years": [2018, 2019], "tasks": [task_name], "chunk_size": 7}
    output = acquire(config, tmp_path / "out")
    frame = pd.read_parquet(output / "observations.parquet")
    metadata = [json.loads(v) for v in frame.metadata]
    assert set(frame.domain_id) == {"CA-2018", "NJ-2018", "CA-2019", "NJ-2019"}
    assert frame.sample_id.is_unique
    assert frame.prediction_time.isna().all() and frame.event_time.isna().all()
    assert frame.split.eq("unassigned").all()
    np.testing.assert_array_equal(frame.sample_weight, [100 + m["source_row"] for m in metadata])
    assert all(m["demographic_group"] == m["demographics"]["RAC1P"] for m in metadata)
    expected_aliases = {}
    if task_name in {"ACSIncome", "ACSEmployment", "ACSMobility", "ACSTravelTime"}:
        expected_aliases["RELP"] = "RELSHIPP"
    if task_name == "ACSTravelTime":
        expected_aliases["JWTR"] = "JWTRNS"
    assert all(
        m["source_field_aliases"] == (expected_aliases if m["survey_year"] == 2019 else {})
        for m in metadata
    )
    assert all(
        "RELP" not in m["source_feature_names"] for m in metadata if m["survey_year"] == 2019
    )
    assert all(
        "RELSHIPP" in m["source_feature_names"]
        for m in metadata
        if m["survey_year"] == 2019
        and task_name in {"ACSIncome", "ACSEmployment", "ACSMobility", "ACSTravelTime"}
    )
    if task_name == "ACSTravelTime":
        assert all(
            "JWTRNS" in m["source_feature_names"] for m in metadata if m["survey_year"] == 2019
        )
    if task_name != "ACSPublicCoverage":
        assert "SCHL" in metadata[0]["original_missing_feature_columns"]
    manifest = json.loads((output / "dataset_manifest.json").read_text())
    assert len(manifest["raw_checksums"]) == 4
    assert (output / "acs_protocol.json").exists()
    assert len(manifest["task_specs"]) == 1
    assert manifest["task_specs"][0]["task_kind"] == "binary_classification"
    assert np.isfinite(frame.target.to_numpy(dtype=float)).all()
    assert validate_dataset(output)["rows"] == len(frame)


def test_sampling_is_reproducible_across_chunk_boundaries(tmp_path, monkeypatch):
    fixtures(tmp_path, monkeypatch)
    config = {
        "states": ["CA"],
        "years": [2018],
        "tasks": ["ACSEmployment"],
        "density": 0.5,
        "sampling_seed": 12,
    }
    first = acquire({**config, "chunk_size": 7}, tmp_path / "out")
    second = acquire({**config, "chunk_size": 13}, tmp_path / "out")
    a = pd.read_parquet(first / "observations.parquet")
    b = pd.read_parquet(second / "observations.parquet")
    assert 0 < len(a) < 40
    assert a.sample_id.tolist() == b.sample_id.tolist()
    np.testing.assert_array_equal(np.stack(a.features), np.stack(b.features))
    np.testing.assert_array_equal(a.target, b.target)


@pytest.mark.parametrize(
    "field,value",
    [
        ("density", True),
        ("density", "0.5"),
        ("density", float("nan")),
        ("density", 1.1),
        ("sampling_seed", True),
        ("sampling_seed", 1.5),
        ("sampling_seed", "12"),
        ("chunk_size", False),
        ("chunk_size", 1.5),
        ("chunk_size", "7"),
    ],
)
def test_invalid_sampling_parameters_are_rejected_before_download(
    tmp_path, monkeypatch, field, value
):
    pytest.importorskip("folktables")

    def unexpected_download(*args, **kwargs):
        pytest.fail("invalid Folktables configuration reached network download")

    monkeypatch.setattr("shiftlab.data.real.folktables.download", unexpected_download)
    config = {"states": ["CA"], "years": [2018], "tasks": ["ACSEmployment"], field: value}
    with pytest.raises((TypeError, ValueError)):
        acquire(config, tmp_path / "out")


def test_missing_source_schema_rejected_before_dataset_publication(tmp_path, monkeypatch):
    fixtures(tmp_path, monkeypatch)
    path = tmp_path / "CA-2019.zip"
    with zipfile.ZipFile(path) as archive:
        source = pd.read_csv(archive.open("psam_p06.csv"))
    source = source.drop(columns=["RELSHIPP"])
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("psam_p06.csv", source.to_csv(index=False))
    with pytest.raises(ValueError, match="missing.*RELSHIPP"):
        acquire({"states": ["CA"], "years": [2019], "tasks": ["ACSIncome"]}, tmp_path / "out")
    assert not (tmp_path / "out/processed").exists()
