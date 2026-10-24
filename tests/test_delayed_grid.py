import hashlib
import json
from pathlib import Path

import pandas as pd
import pytest

from shiftlab.dive.delayed_grid import DelayedGridConfig, run_grid


def _config(**changes):
    values = {
        "seeds": 2,
        "seed_offset": 500,
        "n_source": 120,
        "n_target": 120,
        "query_rates": (0.25, 0.5),
        "harm_onset_fractions": (0.25, 0.6),
        "harm_contrast_increases": (0.12,),
        "delay_schemes": ("fixed_3", "uniform_0_6"),
        "device": "cpu",
    }
    values.update(changes)
    return DelayedGridConfig(**values)


def test_grid_runs_factorial_cells_and_checks_event_order_invariance(tmp_path):
    frame, manifest = run_grid(_config(), tmp_path)

    # Per seed: 8 null cells plus 8 harm cells, each with three method rows.
    assert manifest["stream_cells"] == 32
    assert len(frame) == 96
    assert manifest["event_time_invariance_across_delays"] is True
    assert (
        frame.groupby(
            [
                "scenario",
                "seed",
                "query_rate",
                "harm_onset_fraction",
                "harm_contrast_increase",
                "method",
            ],
            dropna=False,
        )
        .alarm_event.nunique(dropna=False)
        .max()
        == 1
    )
    assert pd.read_parquet(tmp_path / "delayed_feedback_grid.parquet").shape[0] == 96
    assert (tmp_path / "event_summary.csv").is_file()
    assert (tmp_path / "wall_delay_summary.csv").is_file()
    manifest_file = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest_file["config_validated"] is True
    source_root = Path(__file__).parents[1] / "src" / "shiftlab" / "dive"
    assert all(
        hashlib.sha256((source_root / name).read_bytes()).hexdigest() == digest
        for name, digest in manifest_file["code_sha256"].items()
    )
    assert (
        hashlib.sha256((tmp_path / "delayed_feedback_grid.parquet").read_bytes()).hexdigest()
        == manifest_file["metrics_sha256"]
    )


def test_grid_config_rejects_duplicate_rates_and_single_delay_scheme():
    with pytest.raises(ValueError, match="unique"):
        _config(query_rates=(0.25, 0.25)).validate()
    with pytest.raises(ValueError, match="at least two delay"):
        _config(delay_schemes=("fixed_3",)).validate()
