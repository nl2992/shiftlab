import json
from pathlib import Path

import pandas as pd

from shiftlab.dive.delayed_evidence_directed_ppi import Config, _simulate_method
from shiftlab.dive.delayed_evidence_directed_ppi_markov_calibration import generate
from shiftlab.dive.delayed_evidence_ppi_markov_confirmation import _harm_outcomes
from shiftlab.dive.delayed_evidence_ppi_start_mixture import STARTS
from shiftlab.dive.delayed_evidence_ppi_start_mixture_confirmation import run, simulate_pair


def test_paired_monitor_simulation_matches_separate_reference_runs():
    config = Config(seeds=2, seed_offset=20322000, device="cpu")
    seed = config.seed_offset
    onset = config.n_target // 2
    x_source, z_source, x_target, _, delays, _, regimes, _ = generate(config, seed=seed)
    z_target = _harm_outcomes(config, seed=seed, regimes=regimes, onset=onset)
    paired = simulate_pair(
        config,
        seed=seed,
        x_source=x_source,
        z_source=z_source,
        x_target=x_target,
        z_target=z_target,
        delays=delays,
        onset=onset,
    )
    separate = [
        _simulate_method(
            config,
            seed=seed,
            scenario="boundary_harm",
            method="evidence_a0p025_p0p5_eventwise",
            x_source=x_source,
            z_source=z_source,
            x_target=x_target,
            z_target=z_target,
            delays=delays,
            onset=onset,
            monitor_variant=monitor,
            monitor_starts=STARTS if monitor == "fixed_start_mixture" else (),
            query_driver_variant="full_stream",
            continue_after_alarm=True,
        )
        for monitor in ("full_stream", "fixed_start_mixture")
    ]
    paired_by_monitor = {row["monitor_variant"]: row for row in paired}
    for monitor, row in zip(("full_stream", "fixed_start_mixture"), separate, strict=True):
        matched = paired_by_monitor[monitor]
        for field in (
            "alarm_event",
            "alarm_wall_time",
            "alarm_after_onset",
            "labels_queried",
            "events_registered",
            "events_updated",
            "query_schedule_sha256",
        ):
            assert matched[field] == row[field]


def test_start_mixture_confirmation_smoke_requires_passing_calibration(tmp_path: Path):
    root = Path(__file__).parents[1]
    output = tmp_path / "start_mixture_confirmation_smoke"
    run(
        Config(seeds=2, seed_offset=20322000, device="cpu"),
        output,
        protocol=root / "docs/delayed_evidence_ppi_start_mixture_confirmation_protocol.md",
        calibration_manifest=root
        / "outputs/delayed_evidence_ppi_start_mixture_calibration_500/manifest.json",
    )
    metrics = pd.read_parquet(output / "metrics.parquet")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert len(metrics) == 12
    assert manifest["invariants_pass"]
    assert manifest["result"]["matched_query_paths_pass"]
    assert not metrics.duplicated(["seed", "onset_fraction", "monitor_variant"]).any()
