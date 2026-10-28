"""E3 analysis guards (grid completeness, duplicates, bands, decomposition) and the freeze gate."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from shiftlab import freeze
from shiftlab.dive import e3_intervention_factorial as e3

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


an = _load("analyze_e3_mod", "scripts/analyze_e3.py")
runner = _load("run_e3_mod", "scripts/run_e3_intervention_factorial.py")


def synthetic_rows(n_seeds: int = 40, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    out = []
    for s in range(n_seeds):
        noise = rng.normal() * 5
        for onset in an.ONSETS:
            for cov in an.COVERAGES:
                for rb in an.ROLLBACKS:
                    for dose in an.DOSES:
                        for resp in an.RESPONSES:
                            base = {
                                "continue": 0.0,
                                "revert": 100 - 300 * dose,
                                "certify_promote": 20.0,
                                "revert_while_certifying": 90 - 280 * dose,
                                "wait_revert": 60 - 250 * dose,
                            }[resp]
                            out.append(
                                {
                                    "seed": s,
                                    "onset": onset,
                                    "coverage": cov,
                                    "rollback": rb,
                                    "dose": dose,
                                    "response": resp,
                                    an.UTILITY: base + noise + rng.normal(),
                                    "realized_net_gain_vs_incumbent": base,
                                }
                            )
    return pd.DataFrame(out)


def test_analysis_constants_match_the_implementation() -> None:
    assert an.DOSES == e3.DOSES
    assert tuple(an.ONSETS) == tuple(e3.ONSETS)
    assert tuple(an.COVERAGES) == tuple(e3.COVERAGE_END)
    assert tuple(an.ROLLBACKS) == e3.ROLLBACKS
    assert an.RESPONSES == e3.RESPONSES


def test_complete_grid_validates_and_bands_find_the_crossover() -> None:
    curves = an.stratum_curves(an.wide_utility(synthetic_rows()))
    primary = an.dose_tables(curves)["D_revert_minus_promote"]
    cross = an.crossover(primary)
    assert cross["crossover_found"]
    assert cross["bracket"][1] == cross["threshold_dose"]
    # D = (100 - 300 d) - 20 changes sign near d = 0.267, so the first promote-side dose is 0.3
    assert cross["threshold_dose"] == pytest.approx(0.3)
    assert an.verdict(cross).startswith("crossover_located")


def test_decomposition_identity_is_exact() -> None:
    curves = an.stratum_curves(an.wide_utility(synthetic_rows(20, seed=1)))
    advantage = curves["certify_promote"] - curves["revert"]
    abstention = 0.0 - curves["revert"]
    promotion = curves["certify_promote"] - 0.0
    assert np.allclose(advantage, abstention + promotion)


def test_no_crossover_is_not_reported_as_timing_and_rollback_only() -> None:
    band = pd.DataFrame(
        {
            "dose": an.DOSES,
            "mean": 50.0,
            "sd": 1.0,
            "se": 0.1,
            "crit": 3.0,
            "band_low": 49.0,
            "band_high": 51.0,
        }
    )
    verdict = an.verdict(an.crossover(band))
    assert verdict == "no_crossover_detected_on_grid_at_this_n"
    assert "timing" not in verdict


def test_incomplete_grid_and_duplicates_are_rejected() -> None:
    rows = synthetic_rows(10)
    an.validate_grid(rows)
    with pytest.raises(ValueError, match="incomplete grid"):
        an.validate_grid(rows.iloc[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        an.validate_grid(pd.concat([rows, rows.iloc[[0]]], ignore_index=True))
    bad = rows.copy()
    bad.loc[0, an.UTILITY] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        an.validate_grid(bad)
    with pytest.raises(ValueError, match="dose levels"):
        an.validate_grid(rows[rows.dose != 1.0])


def test_trend_test_detects_decreasing_curve() -> None:
    curves = an.stratum_curves(an.wide_utility(synthetic_rows(30, seed=2)))
    matrix = an.curve_matrix(curves, lambda c: c["revert"] - c["certify_promote"])
    assert an.trend_test(matrix)["p_one_sided_negative"] < 1e-6


def test_registered_config_file_matches_code() -> None:
    registered = json.loads((ROOT / "configs/e3_intervention_config.json").read_text("utf-8"))
    assert registered == json.loads(json.dumps(runner.config_dict()))


def test_confirmation_refuses_without_a_freeze_record(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "FREEZE_RECORD", tmp_path / "missing_freeze.json")
    with pytest.raises(SystemExit, match="confirmation refused"):
        runner.require_confirmation_freeze()


def test_freeze_gate_uses_shiftlab_freeze_and_detects_changes(tmp_path: Path, monkeypatch) -> None:
    def git(*args: str) -> None:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    (tmp_path / "a.txt").write_text("alpha\n", encoding="utf-8")
    git("init")
    git("config", "user.email", "t@example.com")
    git("config", "user.name", "t")
    git("add", "a.txt")
    git("commit", "-m", "x")
    record = tmp_path / "freeze.json"
    freeze.write_freeze(
        record,
        experiment="e3",
        protocol="a.txt",
        files=[],
        seed_blocks=["e3_confirmation"],
        repo_root=tmp_path,
    )
    assert freeze.check_freeze(record, tmp_path) == []
    (tmp_path / "a.txt").write_text("beta\n", encoding="utf-8")
    assert any("changed since freeze" in p for p in freeze.check_freeze(record, tmp_path))
    monkeypatch.setattr(runner, "FREEZE_RECORD", record)
    monkeypatch.setattr(
        runner, "require_freeze", lambda path: freeze.require_freeze(path, tmp_path)
    )
    with pytest.raises(SystemExit, match="confirmation refused"):
        runner.require_confirmation_freeze()


def test_promotion_supported_doses_separate_abstention_from_promotion() -> None:
    curves = an.stratum_curves(an.wide_utility(synthetic_rows(30, seed=3)))
    tables = an.dose_tables(curves)
    supported = an.promotion_supported_doses(tables)
    # synthetic promote utility is a constant +20 (> continue = 0), so every promote-side dose
    # is promotion-supported; flipping promote to 0 must remove them (pure abstention).
    assert supported and min(supported) >= 0.3
    rows = synthetic_rows(30, seed=3)
    rows.loc[rows.response == "certify_promote", an.UTILITY] = rng_zero(rows)
    tables0 = an.dose_tables(an.stratum_curves(an.wide_utility(rows)))
    assert an.promotion_supported_doses(tables0) == []


def rng_zero(rows: pd.DataFrame) -> pd.Series:
    return pd.Series(0.0, index=rows.index[rows.response == "certify_promote"])


def _band(low_high: list[tuple[float, float]]) -> pd.DataFrame:
    low = [lo for lo, _ in low_high]
    high = [hi for _, hi in low_high]
    return pd.DataFrame(
        {
            "dose": an.DOSES,
            "mean": [(lo + hi) / 2 for lo, hi in low_high],
            "sd": 1.0,
            "se": 0.1,
            "crit": 3.0,
            "band_low": low,
            "band_high": high,
        }
    )


def test_bracket_uses_last_resolved_revert_dose_and_lists_unresolved() -> None:
    # revert side at 0, 0.15; unresolved at 0.3 and 0.45; promote side from 0.6
    bands = [(5, 9), (5, 9), (-2, 4), (-3, 3), (-9, -5), (-9, -5), (-9, -5)]
    cross = an.crossover(_band(bands))
    assert cross["crossover_found"]
    assert cross["bracket"] == (0.15, 0.6)  # not (0.45, 0.6]: 0.45 is unresolved
    assert cross["bracket_adjacent"] is False
    assert cross["unresolved_doses_inside_bracket"] == [0.3, 0.45]
    assert cross["unresolved_doses"] == [0.3, 0.45]


def test_adjacent_bracket_and_no_resolved_revert_side() -> None:
    adjacent = an.crossover(_band([(5, 9)] * 4 + [(-9, -5)] * 3))
    assert adjacent["bracket"] == (0.45, 0.6) and adjacent["bracket_adjacent"]
    none = an.crossover(_band([(-1, 4)] * 4 + [(-9, -5)] * 3))  # no dose resolved on revert side
    assert not none["crossover_found"] and none["bracket"] is None


def test_confirmation_seed_set_must_be_exact() -> None:
    first = an.CONFIRMATION_FIRST_SEED
    exact = pd.DataFrame({"seed": range(first, first + an.CONFIRMATION_N)})
    an.validate_confirmation_seeds(exact)
    with pytest.raises(ValueError, match="1 missing"):
        an.validate_confirmation_seeds(exact.iloc[:-1])
    with pytest.raises(ValueError, match="1 extra"):
        an.validate_confirmation_seeds(pd.concat([exact, pd.DataFrame({"seed": [first + 5000]})]))
    with pytest.raises(ValueError, match="extra"):
        an.validate_confirmation_seeds(pd.DataFrame({"seed": range(first + 1, first + 1001)}))
    assert an.is_confirmation(exact, {}, False)
    assert not an.is_confirmation(pd.DataFrame({"seed": [100200200]}), {"block": "dev"}, False)
    assert an.is_confirmation(pd.DataFrame({"seed": [1]}), {"block": "confirmation"}, False)


def test_runner_enforces_confirmation_n_and_seed_start(monkeypatch) -> None:
    for argv in (
        ["--block", "confirmation", "--n-per-cell", "999", "--out", "x"],
        [
            "--block",
            "confirmation",
            "--n-per-cell",
            "1000",
            "--first-seed-index",
            "1",
            "--out",
            "x",
        ],
    ):
        monkeypatch.setattr(sys, "argv", ["run", *argv])
        with pytest.raises(SystemExit, match="requires --n-per-cell 1000"):
            runner.main()
    assert runner.CONFIRMATION_N == an.CONFIRMATION_N == 1000
