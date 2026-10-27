"""Verify and summarize the frozen PPE paired-cost confirmation run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import numpy as np
import pandas as pd

from shiftlab.decision_harm_experiment import SCENARIOS
from shiftlab.dive.risk_proxy_monitor_grid import RiskProxyMonitorGridConfig, _run_stream

BOOTSTRAP_REPLICATES = 10_000
ANALYSIS_SEED = 2_026_102_701
ALTERNATIVES = (
    "boundary_local_harm",
    "residual_variance",
    "recurring_regimes",
    "harmful_adaptation",
)
METHODS = (
    "ppe_fixed_stake",
    "fixed_mixture",
    "predictable_kelly",
    "plug_in_empirical_bernstein",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _interval(values: np.ndarray, rng: np.random.Generator, alpha: float) -> list[float]:
    sample_count = values.size
    indices = rng.integers(0, sample_count, size=(BOOTSTRAP_REPLICATES, sample_count))
    means = values[indices].mean(axis=1)
    return [float(x) for x in np.quantile(means, [alpha / 2, 1 - alpha / 2])]


def _same_value(expected: object, actual: object) -> bool:
    if pd.isna(expected) and pd.isna(actual):
        return True
    if isinstance(expected, (bool, np.bool_)) or isinstance(actual, (bool, np.bool_)):
        return bool(expected) == bool(actual)
    return bool(
        np.isclose(
            float(cast(Any, expected)),
            float(cast(Any, actual)),
            rtol=0,
            atol=1e-10,
        )
    )


def _replay_ppe(manifest: dict[str, Any], metrics: pd.DataFrame) -> tuple[int, list[str]]:
    config_data = manifest["config"]
    assert isinstance(config_data, dict)
    config = RiskProxyMonitorGridConfig(**config_data).validate()
    scenarios = {scenario.name: scenario for scenario in SCENARIOS}
    key_fields = (
        "labels_queried",
        "events_processed",
        "realized_label_spend",
        "alarm_time",
        "detection_delay",
        "detected",
        "false_alarm",
        "estimator_rmse",
        "expected_excess_cost_mean",
        "budget_respected",
    )
    errors: list[str] = []
    replayed = 0
    scenario_ranges = cast(dict[str, list[int]], manifest["seed_ranges"])
    scenario_names = cast(list[str], manifest["null_scenarios"]) + cast(
        list[str], manifest["alternative_scenarios"]
    )
    query_rates = cast(list[float], manifest["query_rates"])
    expected_total = sum(
        int(scenario_ranges[name][1]) - int(scenario_ranges[name][0]) + 1 for name in scenario_names
    ) * len(query_rates)
    print(f"replaying all {expected_total} PPE scenario/seed/query streams", flush=True)
    for scenario_name in scenario_names:
        start, stop = scenario_ranges[scenario_name]
        for seed in range(int(start), int(stop) + 1):
            for query_rate in query_rates:
                observed = metrics.loc[
                    metrics.scenario.eq(scenario_name)
                    & metrics.seed.eq(seed)
                    & metrics.query_rate.eq(query_rate)
                    & metrics.method.eq("ppe_fixed_stake")
                ]
                if len(observed) != 1:
                    errors.append(
                        f"expected one saved PPE row for {scenario_name}/{seed}/{query_rate}"
                    )
                    continue
                replay = _run_stream(
                    scenarios[scenario_name],
                    seed,
                    float(query_rate),
                    config,
                    methods=("ppe_fixed_stake",),
                )[0]
                saved = observed.iloc[0]
                for field in key_fields:
                    if not _same_value(saved[field], replay[field]):
                        errors.append(
                            f"replay mismatch for {scenario_name}/{seed}/{query_rate}/{field}"
                        )
                        break
                replayed += 1
                if replayed % 400 == 0:
                    print(f"replayed {replayed}/{expected_total}", flush=True)
    return replayed, errors


def analyze(run_dir: Path, output_dir: Path) -> dict[str, object]:
    manifest_path = run_dir / "manifest.json"
    metrics_path = run_dir / "metrics.parquet"
    null_path = run_dir / "null_calibration.csv"
    protocol_path = run_dir / "experiment_protocol.md"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    metrics = pd.read_parquet(metrics_path)
    nulls = pd.read_csv(null_path)
    errors: list[str] = []

    if manifest["metric_rows"] != len(metrics):
        errors.append("manifest metric row count mismatch")
    if sha256(metrics_path) != manifest["metrics_sha256"]:
        errors.append("metrics Parquet hash mismatch")
    if not protocol_path.exists():
        errors.append("frozen experiment protocol snapshot is missing")
    config = manifest["config"]
    if config["null_seeds"] != 1000 or config["alternative_seeds"] != 300:
        errors.append("seed counts do not match the frozen confirmation protocol")
    if config["seed_offset"] != 2026102700 or config["device"] != "cuda":
        errors.append("seed offset or execution device differs from frozen protocol")
    if set(metrics.method.unique()) != set(METHODS):
        errors.append("method set mismatch")
    if not bool(metrics.groupby(["scenario", "query_rate", "seed"]).size().eq(len(METHODS)).all()):
        errors.append("methods are not complete in every scenario/query/seed cell")
    path_columns = ["labels_queried", "events_processed", "realized_label_spend"]
    if (
        metrics.groupby(["scenario", "query_rate", "seed"])[path_columns].nunique().to_numpy().max()
        != 1
    ):
        errors.append("methods do not share acquisition paths and spend")
    if not bool(metrics.budget_respected.all()):
        errors.append("one or more streams exceeded the hard label budget")
    if not bool(metrics.false_alarm.isin([True, False]).all()):
        errors.append("false alarm field contains invalid values")

    calibration_cells = len(nulls)
    if calibration_cells != 16:
        errors.append(f"expected 16 null cells, found {calibration_cells}")
    if not bool(nulls.calibration_pass.all()):
        errors.append("at least one simultaneous null calibration cell failed")

    replayed_streams, replay_errors = _replay_ppe(manifest, metrics)
    errors.extend(replay_errors)

    alternative = metrics[metrics.scenario.isin(ALTERNATIVES)].copy()
    expected_cells = len(ALTERNATIVES) * 2
    per_seed = alternative.groupby(["seed", "method"]).detected.mean().unstack("method")
    if per_seed.shape[0] != 300 or not np.isfinite(per_seed[list(METHODS)].to_numpy()).all():
        errors.append(f"expected 300 complete alternative seeds, found {per_seed.shape[0]}")
    seed_cell_counts = alternative.groupby("seed")[["scenario", "query_rate"]].apply(
        lambda frame: len(frame.drop_duplicates())
    )
    if not bool((seed_cell_counts == expected_cells).all()):
        errors.append("alternative streams do not contain all 8 profile/query cells per seed")

    rng = np.random.default_rng(ANALYSIS_SEED)
    comparisons: dict[str, dict[str, object]] = {}
    for name in METHODS[1:]:
        differences = (per_seed["ppe_fixed_stake"] - per_seed[name]).to_numpy(dtype=float)
        alpha = 0.05 if name == "fixed_mixture" else 0.05 / 3
        comparisons[f"ppe_minus_{name}"] = {
            "mean_seed_averaged_detection_difference": float(differences.mean()),
            "bootstrap_interval": _interval(differences, rng, alpha),
            "interval_family_alpha": alpha,
            "seed_count": int(differences.size),
        }

    report: dict[str, object] = {
        "verified": not errors,
        "errors": errors,
        "run_dir": str(run_dir),
        "metric_rows": len(metrics),
        "null_calibration_cells": int(calibration_cells),
        "null_false_alarms": int(nulls.false_alarms.sum()),
        "null_calibration_passed": bool(nulls.calibration_pass.all()),
        "ppe_replay_streams": replayed_streams,
        "ppe_replay_matches": not replay_errors,
        "alternative_seed_count": int(per_seed.shape[0]),
        "alternative_profiles": list(ALTERNATIVES),
        "profiles_per_seed": int(expected_cells),
        "primary_comparison": "ppe_fixed_stake minus fixed_mixture",
        "secondary_comparisons": comparisons,
        "analysis_seed": ANALYSIS_SEED,
        "bootstrap_replicates": BOOTSTRAP_REPLICATES,
        "input_hashes": {
            "manifest.json": sha256(manifest_path),
            "metrics.parquet": sha256(metrics_path),
            "null_calibration.csv": sha256(null_path),
        },
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    repository = Path(__file__).resolve().parents[1]
    source_paths = {
        "risk_proxy_monitor_grid.py": repository / "src/shiftlab/dive/risk_proxy_monitor_grid.py",
        "prediction_powered_evalues.py": repository
        / "src/shiftlab/dive/prediction_powered_evalues.py",
        "analysis_script.py": Path(__file__).resolve(),
    }
    if protocol_path.exists():
        source_paths["experiment_protocol.md"] = protocol_path
    report["source_hashes"] = {name: sha256(path) for name, path in source_paths.items()}
    (output_dir / "verification.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    result = analyze(args.run_dir, args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["verified"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
