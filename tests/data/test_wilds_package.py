"""Exercise the genuine optional WILDS package with a local generated fixture, no remote data."""

import json

import numpy as np
import pandas as pd
import pytest

from shiftlab.data.real.wilds import IDENTITIES, evaluate_official, from_official, official_dataset


def test_real_official_civilcomments_package(tmp_path):
    torch = pytest.importorskip("torch")
    pytest.importorskip("wilds")
    directory = tmp_path / "raw/wilds/civilcomments_v1.0"
    directory.mkdir(parents=True)
    auxiliary = [
        "identity_any",
        "severe_toxicity",
        "obscene",
        "threat",
        "insult",
        "identity_attack",
        "sexual_explicit",
    ]
    original = pd.DataFrame(
        {
            "comment_text": ["local fixture"] * 6,
            "toxicity": [0, 1, 0, 1, 0, 1],
            "split": ["train", "train", "val", "val", "test", "test"],
            **{field: np.ones(6) for field in [*IDENTITIES, *auxiliary]},
        }
    )
    original.to_csv(directory / "all_data_with_identities.csv")
    (directory / "RELEASE_v1.0.txt").touch()
    config = {"dataset": "civilcomments", "version": "1.0", "max_per_split": 2}
    dataset = official_dataset(config, tmp_path, download_data=False)
    path = from_official(dataset, config, tmp_path)
    frame = pd.read_parquet(path / "observations.parquet")
    assert len(frame) == 6
    assert json.loads(frame.metadata.iloc[0])["official_split"] == "train"
    y = torch.tensor([0, 1, 0, 1, 0, 1])
    result, _ = evaluate_official(dataset, y, y, dataset.metadata_array)
    assert result["acc_avg"] == 1


def test_native_group_reduction_matches_explicit_group_means():
    torch = pytest.importorskip("torch")
    from shiftlab.data.real.wilds_metrics import native_group_average

    values = torch.tensor([1.0, 3.0, 4.0, 8.0, 2.0], dtype=torch.float64)
    groups = torch.tensor([0, 0, 2, 2, 2])
    means, counts = native_group_average(values, groups, 4)
    assert torch.allclose(means, torch.tensor([2.0, 0.0, 14 / 3, 0.0], dtype=torch.float64))
    assert counts.tolist() == [2, 0, 3, 0]
