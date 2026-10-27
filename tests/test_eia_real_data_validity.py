from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from shiftlab.dive.eia_paired_reserve import PairedReserveStream
from shiftlab.dive.eia_validity_analysis import (
    BUDGETS,
    GATED_AND_HT,
    PATHS,
    classify_alarms,
    clopper_pearson_upper,
    collect_paths,
    injected_analysis,
    injection_coins,
    null_analysis,
    orientation_coins,
    registered_cells,
    rerun_coins,
    unmodified_analysis,
    unmodified_coins,
)
from shiftlab.dive.reserve_costs import paired_cost, reserve_actions

_RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "run_eia_real_data_validity.py"
_spec = importlib.util.spec_from_file_location("run_eia_real_data_validity", _RUNNER)
assert _spec is not None and _spec.loader is not None
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


def _stream(respondent: str, window: str, n: int, seed: int) -> PairedReserveStream:
    rng = np.random.default_rng(seed)
    tau = 0.0
    margin = rng.normal(size=n) * 2
    ref_pred = margin + rng.normal(size=n) * 1.5
    demand = margin + rng.normal(size=n)
    da, ra = reserve_actions(margin, tau), reserve_actions(ref_pred, tau)
    return PairedReserveStream(
        respondent=respondent,
        window=window,
        event_time=3600.0 * np.arange(n) + 1.7e9,
        x=np.zeros((n, 4)),
        demand=demand,
        tau=tau,
        deployed_prediction=margin,
        reference_prediction=ref_pred,
        deployed_action=da,
        reference_action=ra,
        paired_cost=paired_cost(da, ra, demand, tau),
        disagreement=da != ra,
        frozen_margin=margin - tau,
    )


def _synthetic(n: int = 150) -> list[PairedReserveStream]:
    streams = []
    for i, (respondent, window) in enumerate(PATHS):
        streams.append(_stream(respondent, window, n, 10 + i))
    streams.append(_stream("CISO", "rehearsal_2024", 300, 98))
    streams.append(_stream("ERCO", "rehearsal_2024", 300, 99))
    return streams


def test_cells_order_and_length():
    cells = registered_cells()
    assert len(cells) == 17
    assert cells[0] == ("full_feedback", None)
    assert cells[1] == ("ungated_ht", 0.02)
    assert cells[4] == ("ungated_ht", 0.20)
    assert cells[5] == ("gated_ht_fixed", 0.02)
    assert cells[-1] == ("gated_eb_paced", 0.20)
    assert [c[0] for c in cells[1:]] == [a for a in GATED_AND_HT for _ in BUDGETS]


def test_coins_use_exact_seed_formulas():
    n = 7
    signs, uniforms = orientation_coins(2, n, 5)
    rng = np.random.default_rng(59200002)
    np.testing.assert_array_equal(signs, 2 * rng.integers(0, 2, size=(5, n)) - 1)
    np.testing.assert_array_equal(uniforms, rng.random((5, n)))
    s2, u2 = rerun_coins(3, 11, n, 6)
    rng = np.random.default_rng(59230000 + 311)
    np.testing.assert_array_equal(s2, 2 * rng.integers(0, 2, size=(6, n)) - 1)
    np.testing.assert_array_equal(u2, rng.random((6, n)))
    np.testing.assert_array_equal(
        unmodified_coins(1, n, 4), np.random.default_rng(59220001).random((4, n))
    )
    np.testing.assert_array_equal(
        injection_coins(3, 2, n, 4), np.random.default_rng(59210032).random((4, n))
    )
    a, _ = orientation_coins(0, n, 5)
    b, _ = orientation_coins(0, n, 5)
    np.testing.assert_array_equal(a, b)
    assert orientation_coins(0, 3)[0].shape == (1000, 3)
    assert rerun_coins(0, 0, 3)[0].shape == (4000, 3)
    assert unmodified_coins(0, 3).shape == (200, 3)
    assert injection_coins(0, 0, 3).shape == (200, 3)


def test_clopper_pearson_upper():
    assert clopper_pearson_upper(0, 1000) == pytest.approx(0.002991, abs=1e-6)
    assert clopper_pearson_upper(1000, 1000) == 1.0
    assert clopper_pearson_upper(50, 1000) > 0.05


def _write_frozen(root: Path) -> Path:
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    files = {
        runner.PROTOCOL_REL: b"protocol",
        runner.STREAMS_REL: b"streams",
        "src/a.py": b"code a",
        "scripts/b.py": b"code b",
    }
    for rel, data in files.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    freeze = {
        "protocol_sha256": sha(root / runner.PROTOCOL_REL),
        "code_sha256": {rel: sha(root / rel) for rel in ("src/a.py", "scripts/b.py")},
        "streams_sha256": sha(root / runner.STREAMS_REL),
        "freeze_utc": "2026-10-27T00:00:00Z",
    }
    path = root / runner.FREEZE_REL
    path.write_text(json.dumps(freeze), encoding="utf-8")
    return path


def test_freeze_check_ok_missing_and_mismatch(tmp_path):
    with pytest.raises(FileNotFoundError):
        runner.check_freeze(tmp_path)
    _write_frozen(tmp_path)
    assert runner.check_freeze(tmp_path)["freeze_utc"] == "2026-10-27T00:00:00Z"
    (tmp_path / "src/a.py").write_bytes(b"changed")
    with pytest.raises(ValueError, match="src/a.py"):
        runner.check_freeze(tmp_path)


@pytest.mark.parametrize("rel", [runner.PROTOCOL_REL, runner.STREAMS_REL])
def test_freeze_check_protocol_and_streams_mismatch(tmp_path, rel):
    _write_frozen(tmp_path)
    (tmp_path / rel).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash mismatch"):
        runner.check_freeze(tmp_path)


def test_output_dir_refusal(tmp_path):
    runner.check_output_dir(tmp_path / "absent")
    runner.check_output_dir(tmp_path)  # exists but empty
    (tmp_path / "x").write_text("1")
    with pytest.raises(FileExistsError):
        runner.check_output_dir(tmp_path)


def test_classify_alarms_pre_onset_never_detection():
    et = 3600.0 * np.arange(10)
    first = np.array([-1, 1, 5, 7])
    out = classify_alarms(first, onset=4, n=10, event_time=et)
    assert out["detection_rate"] == 0.5
    assert out["pre_onset_rate"] == 0.25
    # delays: censored 6 (none), censored 6 (pre-onset), 1, 3
    assert out["mean_delay_events"] == pytest.approx((6 + 6 + 1 + 3) / 4)
    assert out["median_delay_events"] == pytest.approx(4.5)
    assert out["mean_delay_hours"] == pytest.approx((5 + 5 + 1 + 3) / 4)


def test_end_to_end_mini_run():
    paths = collect_paths(_synthetic())
    reps = {"null": 20, "rerun": 30, "unmodified": 10, "injected": 10}
    null_df, decision = null_analysis(paths, reps["null"], reps["rerun"])
    cols = [
        "path",
        "respondent",
        "window",
        "n",
        "disagreements",
        "arm",
        "budget",
        "epsilon",
        "replicates",
        "alarms",
        "rate",
        "cp_upper",
        "passes",
        "stage",
        "mean_labels",
        "mean_dollars",
        "mean_processed",
    ]
    assert list(null_df.columns) == cols
    original = null_df[null_df.stage == "original"]
    assert len(original) == 4 * 17 * 2
    assert set(original.epsilon) == {0.1, 0.0}
    # With 20 replicates the CP bound exceeds 0.05 unless there are zero alarms,
    # but even then 0 alarms gives 0.139 > 0.05, so every primary cell is re-run.
    assert set(null_df.stage) == {"original", "rerun"}
    assert (null_df[null_df.stage == "rerun"].replicates == 30).all()
    assert len(decision["reruns"]) == 4 * 17
    assert decision["null_passes"] is False
    assert len(decision["failing_cells"]) == 4 * 17

    un = unmodified_analysis(paths, reps["unmodified"])
    assert len(un) == 4 * 4 * 4
    assert {"alarm_probability", "agreement_with_fullfeedback", "mean_labels"} <= set(un.columns)
    assert un.alarm_probability.between(0, 1).all()

    inj = injected_analysis(paths, reps["injected"])
    assert len(inj) == 4 * 3 * 17
    for col in (
        "detection_rate",
        "pre_onset_rate",
        "mean_delay_events",
        "median_delay_events",
        "mean_delay_hours",
        "median_delay_hours",
        "mean_labels",
        "mean_dollars",
        "band_low",
        "band_high",
        "flipped_events",
        "injected_post_onset_mean_excess",
    ):
        assert col in inj.columns
    assert (inj.detection_rate + inj.pre_onset_rate <= 1 + 1e-12).all()
    assert (inj.flipped_events > 0).all()


def test_run_analyses_wiring():
    result = runner.run_analyses(
        _synthetic(), {"null": 10, "rerun": 10, "unmodified": 5, "injected": 5}
    )
    assert set(result) == {"null_cells", "unmodified", "injected", "decision"}
