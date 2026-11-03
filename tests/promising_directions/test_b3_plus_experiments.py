"""Acceptance tests for the B3+ runner: it must reproduce the saved B3 numbers (rialto, cached)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts/promising_directions"
B3 = ROOT / "docs/promising_directions/results/b3"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


exp = _load("b3_plus_experiments")
ana = _load("b3_plus_analysis")
BASE = ["P0", "P1", "P2", "P3b", "P6"]


def read(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


@pytest.fixture(scope="module")
def rialto_run(tmp_path_factory):
    out = tmp_path_factory.mktemp("b3plus")
    exp.main(
        ["--streams", "rialto", "--variants", ",".join(BASE), "--config", "S0", "--out", str(out)]
    )
    return out


def test_reproduces_saved_b3_rialto_means(rialto_run):
    rows = read(rialto_run / "rialto__S0__h2000.jsonl")
    assert len(rows) == 16
    saved = json.loads((B3 / "summary.json").read_text())["streams"]["rialto"]["primary"][
        "mean_cost"
    ]
    for v in BASE:
        got = np.mean([r["variants"][v]["mean_cost"] for r in rows])
        assert got == pytest.approx(saved[v], abs=1e-6), v
    assert saved["P0"] == pytest.approx(202.0625, abs=1e-9)
    assert saved["P3b"] == pytest.approx(103.728, abs=1e-3)


def test_matches_b3_per_episode_rows_exactly(rialto_run):
    new = {r["episode"]: r for r in read(rialto_run / "rialto__S0__h2000.jsonl")}
    old = [r for r in read(B3 / "rialto.jsonl") if r["setting"] == "B200_cs5"]
    assert len(old) == 16
    for r in old:
        for v in BASE:
            assert new[r["episode"]]["variants"][v]["cost_seeds"] == r["policies"][v]["cost_seeds"]


def test_resume_skips_existing_rows_and_p1_is_flagged_hindsight(rialto_run):
    path = rialto_run / "rialto__S0__h2000.jsonl"
    before = path.read_text()
    exp.main(
        [
            "--streams",
            "rialto",
            "--variants",
            ",".join(BASE),
            "--config",
            "S0",
            "--out",
            str(rialto_run),
            "--resume",
        ]
    )
    assert path.read_text() == before
    assert json.loads(before.splitlines()[0])["variant_meta"]["P1"]["deployable"] is False
    assert (rialto_run / "SHA256SUMS.txt").exists() and (rialto_run / "provenance.json").exists()


def test_pct_runs_with_baseline_schema_and_analysis_tables(tmp_path):
    out = tmp_path / "o"
    exp.main(
        [
            "--streams",
            "rialto",
            "--variants",
            "P0,P1,P3b,PCT",
            "--n-seeds",
            "8",
            "--max-episodes",
            "5",
            "--out",
            str(out),
        ]
    )
    r = read(out / "rialto__S0__h2000.jsonl")[0]
    assert {
        "mean_cost",
        "mean_labels",
        "mean_switches",
        "mean_rollbacks",
        "promotion_rate",
        "cost_seeds",
    } <= set(r["variants"]["PCT"])
    assert len(r["variants"]["PCT"]["cost_seeds"]) == 8
    ana.build(out, "PCT", "S0")
    main = json.loads((out / "tables/main_results.json").read_text())["rialto"]
    assert main["episodes"] == 5 and main["main_minus_P3b"]["bootstrap_level"] == "episode"


def test_horizon_1000_splits_episodes_and_scales_budget(tmp_path):
    out = tmp_path / "o"
    exp.main(
        [
            "--streams",
            "spam",
            "--variants",
            "P0,P3b",
            "--n-seeds",
            "4",
            "--horizon",
            "1000",
            "--out",
            str(out),
        ]
    )
    rows = read(out / "spam__S0__h1000.jsonl")
    assert [x["budget"] for x in rows] == [100, 100] and [x["episode"] for x in rows] == [0, 1]
    assert not (out / "spam__S0__h2000.jsonl").exists()


def test_s5_without_alt_losses_exits_clearly(tmp_path):
    with pytest.raises(SystemExit) as e:
        exp.main(
            ["--streams", "spam", "--variants", "P0", "--config", "S5", "--out", str(tmp_path)]
        )
    assert "S5" in str(e.value) and "raw data" in str(e.value)
