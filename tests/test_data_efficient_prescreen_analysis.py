import hashlib
import json

import pandas as pd
import pytest

from scripts import analyze_data_efficient_prescreen as analysis

SEEDS = tuple(range(59000000, 59000020))
CELLS = [(onset, budget) for onset in (0.5, 0.75) for budget in (0.02, 0.05, 0.10, 0.20)]


def _make_streams(*, identity=False, resource_failure=False):
    rows = []
    for onset, budget_rate in CELLS:
        onset_index = round(onset * analysis.HORIZON)
        censor = analysis.HORIZON - onset_index
        for arm, engine, detector in sorted(analysis._expected_panel_combinations(budget_rate)):
            same_null = arm not in analysis.FULL_FEEDBACK_ARMS
            canonical = arm == "optional_candidate" and engine == "fixed1" and detector == "sr"
            for i, seed in enumerate(SEEDS):
                primary = (onset, budget_rate) == analysis.PRIMARY_CELL
                if identity or not primary:
                    detected = i < 10
                elif canonical:
                    detected = 1 <= i <= 14
                else:
                    detected = i < 10

                if i == 0:
                    first_alarm = onset_index - 1  # pre-onset alarm is a failure
                    detected = False
                    delay = censor
                elif detected:
                    delay_from_onset = 30 if canonical or identity else 60
                    first_alarm = onset_index + delay_from_onset
                    delay = first_alarm - onset_index
                else:
                    first_alarm = None
                    delay = censor

                labels = 12.0 if canonical else 13.0
                dollars = 40.0 if canonical else 42.0
                if resource_failure and canonical:
                    labels = 14.0
                    dollars = 43.0
                rows.append(
                    {
                        "seed": seed,
                        "onset_fraction": onset,
                        "budget_rate": budget_rate,
                        "arm": arm,
                        "engine": engine,
                        "detector": detector,
                        "first_alarm": first_alarm,
                        "detected": detected,
                        "delay_censored": delay,
                        "labels": labels,
                        "dollars": dollars,
                        "budget": None if arm == "full_feedback" else 100.0,
                        "same_null_harm_comparator": same_null,
                    }
                )
    return pd.DataFrame(rows)


def test_compare_summarizes_wilson_paired_bootstrap_and_applies_all_cell_gates():
    summary, paired, decision = analysis.compare(_make_streams())

    assert len(summary) == len(
        _make_streams().drop_duplicates(
            ["onset_fraction", "budget_rate", "arm", "engine", "detector"]
        )
    )
    expected_pairs = sum(
        sum(
            arm not in analysis.FULL_FEEDBACK_ARMS and arm != analysis.CANDIDATE_ARM
            for arm, _, _ in analysis._expected_panel_combinations(budget)
        )
        for _, budget in CELLS
    )
    assert len(paired) == expected_pairs
    assert decision["outcome"] == "advance_prescreen_only"
    assert not decision["calibration_established"]
    assert not decision["confirmation_claim"]
    assert paired["detection_difference_bootstrap_95_low"].notna().all()
    assert summary["detection_wilson_95_low"].between(0, 1).all()
    assert summary["detection_wilson_95_high"].between(0, 1).all()
    primary = paired.loc[
        paired.onset_fraction.eq(0.75)
        & paired.budget_rate.eq(0.05)
        & paired.incumbent_arm.eq("uniform_ppi")
        & paired.incumbent_engine.eq("fixed1")
        & paired.incumbent_detector.eq("sr")
    ].iloc[0]
    assert primary.detection_difference == pytest.approx(0.25)
    assert primary.mean_labels_difference == pytest.approx(-1.0)
    assert primary.mean_dollars_difference == pytest.approx(-2.0)


def test_pre_onset_alarm_and_nondetection_both_receive_full_censored_delay():
    streams = _make_streams()
    row = streams.loc[
        streams.arm.eq("optional_candidate")
        & streams.engine.eq("fixed1")
        & streams.onset_fraction.eq(0.75)
        & streams.budget_rate.eq(0.05)
        & streams.seed.eq(SEEDS[0])
    ].iloc[0]
    assert row.first_alarm == 1799
    assert not row.detected
    assert row.delay_censored == 600

    bad = streams.copy()
    bad.loc[bad.seed.eq(SEEDS[19]) & bad.arm.eq("gated_ht_paced"), "delay_censored"] = 0
    with pytest.raises(ValueError, match="delay_censored"):
        analysis.compare(bad)


def test_missing_seed_block_is_rejected():
    streams = _make_streams()
    keep = ~(
        streams.arm.eq("optional_candidate")
        & streams.engine.eq("fixed1")
        & streams.onset_fraction.eq(0.75)
        & streams.budget_rate.eq(0.05)
        & streams.seed.isin(SEEDS[-2:])
    )
    with pytest.raises(ValueError, match="panel seed block mismatch"):
        analysis.compare(streams.loc[keep])


def test_candidate_resource_failure_stops_even_with_detection_gain():
    _, paired, decision = analysis.compare(_make_streams(resource_failure=True))
    primary = paired.loc[
        paired.onset_fraction.eq(0.75)
        & paired.budget_rate.eq(0.05)
        & paired.incumbent_arm.eq("uniform_ppi")
        & paired.incumbent_engine.eq("fixed1")
        & paired.incumbent_detector.eq("sr")
    ].iloc[0]
    assert primary.detection_margin_pass
    assert not primary.resources_pass
    assert not primary.passes_comparison
    assert decision["outcome"] == "stop_prescreen"


def test_identity_tie_fails_primary_win_gate():
    _, paired, decision = analysis.compare(_make_streams(identity=True))
    primary = paired.loc[
        paired.onset_fraction.eq(0.75)
        & paired.budget_rate.eq(0.05)
        & paired.incumbent_arm.eq("uniform_ppi")
        & paired.incumbent_engine.eq("fixed1")
        & paired.incumbent_detector.eq("sr")
    ].iloc[0]
    assert primary.detection_difference == 0
    assert primary.delay_ratio_incumbent_over_candidate == pytest.approx(1)
    assert not primary.passes_comparison
    assert decision["outcome"] == "stop_prescreen"


def test_exact_two_of_twenty_detection_gain_meets_primary_threshold():
    streams = _make_streams(identity=True)
    candidate = (
        streams.arm.eq("optional_candidate")
        & streams.engine.eq("fixed1")
        & streams.detector.eq("sr")
        & streams.onset_fraction.eq(0.75)
        & streams.budget_rate.eq(0.05)
        & streams.seed.isin(SEEDS[-2:])
    )
    onset_index = round(0.75 * analysis.HORIZON)
    streams.loc[candidate, "first_alarm"] = onset_index + 30
    streams.loc[candidate, "detected"] = True
    streams.loc[candidate, "delay_censored"] = 30

    _, paired, _ = analysis.compare(streams)
    row = paired.loc[
        paired.onset_fraction.eq(0.75)
        & paired.budget_rate.eq(0.05)
        & paired.incumbent_arm.eq("uniform_ppi")
        & paired.incumbent_engine.eq("fixed1")
        & paired.incumbent_detector.eq("sr")
    ].iloc[0]
    assert row.detection_difference == pytest.approx(0.10)
    assert row.detection_margin_pass
    assert row.passes_comparison


def test_cli_verifies_input_manifest_and_refuses_analysis_overwrite(tmp_path, monkeypatch):
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    streams_path = input_dir / "streams.csv"
    _make_streams().to_csv(streams_path, index=False)
    streams_hash = hashlib.sha256(streams_path.read_bytes()).hexdigest()
    (input_dir / "manifest.json").write_text(
        json.dumps({"outputs_sha256": {"streams.csv": streams_hash}}), encoding="utf-8"
    )
    monkeypatch.setattr(
        "sys.argv", ["analyze_data_efficient_prescreen.py", "--input-dir", str(input_dir)]
    )
    analysis.main()
    output = input_dir / "analysis"
    output_manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert output_manifest["input_streams_sha256"] == streams_hash
    assert set(output_manifest["outputs_sha256"]) == {
        "summary.csv",
        "paired.csv",
        "decision.json",
    }
    with pytest.raises(FileExistsError):
        analysis.main()


def test_common96_arm_is_applicable_only_at_budget_point_two():
    streams = _make_streams()
    _, paired, _ = analysis.compare(streams)
    common = paired.loc[paired.incumbent_arm.eq("uniform_ppi_common96p9")]
    assert len(common) == 2 * len(analysis.BASE_ENGINES) * len(analysis.DETECTORS)
    assert common.budget_rate.eq(0.20).all()

    malformed = streams.loc[
        ~(streams.arm.eq("uniform_ppi_common96p9") & streams.budget_rate.eq(0.02))
    ].copy()
    row = streams.loc[
        streams.arm.eq("uniform_ppi_common96p9")
        & streams.budget_rate.eq(0.20)
        & streams.onset_fraction.eq(0.50)
    ].copy()
    row["budget_rate"] = 0.02
    malformed = pd.concat([malformed, row], ignore_index=True)
    with pytest.raises(ValueError, match="coverage mismatch"):
        analysis.compare(malformed)
