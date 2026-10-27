from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
import torch

from shiftlab.dive import eia_paired_reserve as mod
from shiftlab.dive.eia_paired_reserve import StreamWindows

H = 3600
T0 = 1_546_300_800  # 2019-01-01T00Z
N_HOURS = 1000
WINDOWS = StreamWindows(
    fit_full_start=T0,
    fit_full_end=T0 + 699 * H,
    fit_rehearsal_end=T0 + 499 * H,
    rehearsal_start=T0 + 500 * H,
    rehearsal_end=T0 + 699 * H,
    development_start=T0 + 700 * H,
    development_end=T0 + 949 * H,
    split_2026=T0 + 820 * H,
)


def make_series(seed: int = 0, bump_dev: bool = False) -> dict:
    rng = np.random.default_rng(seed)
    hours = np.arange(N_HOURS + 2)
    base = 100 + 20 * np.sin(hours * 2 * np.pi / 24) + rng.normal(0, 3, len(hours))
    series: dict = {}
    for r in ("CISO", "ERCO"):
        d = base + (5 if r == "ERCO" else 0)
        d = d + np.where(hours >= 850, 25, 0)  # shifted regime late in development
        if bump_dev:
            d[800] += 500.0
        ng = 0.5 * d + rng.normal(0, 2, len(hours))
        series[f"EBA.{r}-ALL.D.H"] = {T0 + int(i) * H: float(d[i]) for i in hours}
        series[f"EBA.{r}-ALL.DF.H"] = {T0 + int(i) * H: float(d[i] + 2) for i in hours}
        series[f"EBA.{r}-ALL.NG.H"] = {T0 + int(i) * H: float(ng[i]) for i in hours}
        series[f"EBA.{r}-ALL.TI.H"] = {T0 + int(i) * H: float(d[i] - ng[i]) for i in hours}
    return series


@pytest.fixture(scope="module")
def streams() -> list:
    return mod.build_respondent_streams(make_series(), "CISO", torch.device("cpu"), WINDOWS)


def test_invariants(streams):
    assert [s.window for s in streams] == ["rehearsal_2024", "2025", "2026"]
    for s in streams:
        assert np.all(np.abs(s.paired_cost) <= 5)
        assert np.all(s.paired_cost[~s.disagreement] == 0)
        assert np.array_equal(s.disagreement, s.deployed_action != s.reference_action)
        assert np.array_equal(s.frozen_margin, s.deployed_prediction - s.tau)
        assert np.all(np.diff(s.event_time) > 0)
        assert s.x.shape == (len(s.demand), 4)
        assert s.event_time.dtype == np.float64


def test_calendar_split_exact(streams):
    a, b = streams[1], streams[2]
    assert a.event_time.max() < WINDOWS.split_2026 <= b.event_time.min()
    assert a.event_time.min() == WINDOWS.development_start
    assert b.event_time.max() == WINDOWS.development_end
    assert len(a.event_time) + len(b.event_time) == 250
    assert b.event_time.min() - a.event_time.max() == H


def test_tau_from_fit_rows_only(streams):
    series = make_series()
    fit_y = [series["EBA.CISO-ALL.D.H"][T0 + (i + 1) * H] for i in range(700)]
    assert streams[0].tau == pytest.approx(float(np.quantile(fit_y, 0.9)))
    other = mod.build_respondent_streams(
        make_series(bump_dev=True), "CISO", torch.device("cpu"), WINDOWS
    )
    assert other[0].tau == streams[0].tau
    for name in ("deployed_prediction", "reference_prediction", "paired_cost", "demand"):
        assert np.array_equal(getattr(other[0], name), getattr(streams[0], name))
    assert other[1].tau == streams[1].tau


def test_sha_mismatch_raises(tmp_path: Path):
    archive = tmp_path / "x.zip"
    archive.write_bytes(b"not the archive")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        mod.load_series(archive, expected_sha256="0" * 64)


def test_roundtrip(tmp_path: Path, streams):
    out = tmp_path / "out"
    mod.write_streams(streams, out, device=torch.device("cpu"), archive_path=tmp_path / "none.zip")
    back = mod.read_streams(out)
    assert [(s.respondent, s.window) for s in back] == [(s.respondent, s.window) for s in streams]
    names = ("event_time", "x", "demand", "paired_cost", "deployed_action", "frozen_margin")
    for a, b in zip(streams, back, strict=True):
        assert a.tau == b.tau
        for name in names:
            assert np.array_equal(getattr(a, name), getattr(b, name))
        assert np.array_equal(a.disagreement, b.disagreement)
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["n_per_window"]["CISO"]["2026"] == len(streams[2].event_time)
    with pytest.raises(FileExistsError):
        mod.write_streams(streams, out)
    (out / "streams.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="does not match manifest"):
        mod.read_streams(out)
