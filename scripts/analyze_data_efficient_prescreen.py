"""Analyze the frozen WP3 20-seed prescreen without confirmation claims."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SEEDS = tuple(range(59000000, 59000020))
ONSETS = (0.50, 0.75)
BUDGETS = (0.02, 0.05, 0.10, 0.20)
PRIMARY_CELL = (0.75, 0.05)
HORIZON = 2400
FULL_FEEDBACK_ARMS = {"full_feedback", "feature_adwin"}
CANDIDATE_ARM = "optional_candidate"
CANDIDATE_ENGINE = "fixed1"
CANDIDATE_DETECTOR = "sr"
BASE_ENGINES = ("fixed1", "plugin", "timans_approx_grapa", "timans_grapa")
DETECTORS = ("fixed_start", "started", "sr", "cusum")
REQUIRED_BASE_ARMS = (
    "uniform_ppi",
    "variance_ppi",
    "uniform_ppi_common96p9",
    "gated_ht_fixed",
    "gated_ht_paced",
    "gated_ppi_paced",
    "gated_eb_paced",
    "ppe_uniform",
    "xu_active",
    "ppe_gated",
    "optional_uniform",
    "optional_paced",
    "optional_temporal",
    CANDIDATE_ARM,
    "full_feedback",
    "feature_adwin",
)
SOURCE_ENGINE_BY_ARM = {
    "ppe_uniform": "source_fixed0p9",
    "xu_active": "source_fixed0p9",
    "ppe_gated": "source_fixed0p9",
    "gated_eb_paced": "source_pm_eb",
}
REQUIRED_COLUMNS = {
    "seed",
    "onset_fraction",
    "budget_rate",
    "arm",
    "engine",
    "detector",
    "first_alarm",
    "detected",
    "delay_censored",
    "labels",
    "dollars",
    "budget",
    "same_null_harm_comparator",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bool_column(values: pd.Series, name: str) -> pd.Series:
    def parse(value: Any) -> bool:
        if isinstance(value, (bool, np.bool_)):
            return bool(value)
        if isinstance(value, (int, np.integer)) and value in (0, 1):
            return bool(value)
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
        raise ValueError(f"{name} must contain only booleans")

    return values.map(parse).astype(bool)


def _validate_and_normalize(streams: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(streams.columns)
    if missing:
        raise ValueError(f"streams table is missing required columns: {sorted(missing)}")
    frame = streams.copy()
    seed_values = pd.to_numeric(frame.seed, errors="raise")
    if not np.isfinite(seed_values).all() or not np.equal(seed_values, np.floor(seed_values)).all():
        raise ValueError("seed values must be finite integers")
    frame["seed"] = seed_values.astype(int)
    frame["onset_fraction"] = pd.to_numeric(frame.onset_fraction, errors="raise")
    frame["budget_rate"] = pd.to_numeric(frame.budget_rate, errors="raise")
    frame["detected"] = _bool_column(frame.detected, "detected")
    frame["same_null_harm_comparator"] = _bool_column(
        frame.same_null_harm_comparator, "same_null_harm_comparator"
    )
    for column in ("delay_censored", "labels", "dollars", "budget"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in ("arm", "engine", "detector"):
        if frame[column].isna().any():
            raise ValueError(f"{column} cannot be missing")
        frame[column] = frame[column].astype(str)

    if not np.isfinite(frame.seed).all():
        raise ValueError("seed must be finite")
    if not np.isfinite(frame.onset_fraction).all() or not np.isfinite(frame.budget_rate).all():
        raise ValueError("onset_fraction and budget_rate must be finite")
    if not frame.onset_fraction.map(
        lambda x: any(np.isclose(x, v, rtol=0, atol=1e-12) for v in ONSETS)
    ).all():
        raise ValueError("unregistered onset_fraction")
    if not frame.budget_rate.map(
        lambda x: any(np.isclose(x, v, rtol=0, atol=1e-12) for v in BUDGETS)
    ).all():
        raise ValueError("unregistered budget_rate")
    if not np.isfinite(frame.delay_censored).all() or (frame.delay_censored < 0).any():
        raise ValueError("delay_censored must be finite and nonnegative")
    if not np.isfinite(frame.labels).all() or (frame.labels < 0).any():
        raise ValueError("labels must be finite and nonnegative")
    if not np.isfinite(frame.dollars).all() or (frame.dollars < 0).any():
        raise ValueError("dollars must be finite and nonnegative")
    if (frame.budget.dropna() < 0).any():
        raise ValueError("finite budgets must be nonnegative")

    alarms = pd.to_numeric(frame.first_alarm, errors="coerce")
    if alarms.notna().any() and ((alarms.dropna() < 0).any() or (alarms.dropna() >= HORIZON).any()):
        raise ValueError("first_alarm must be a zero-based index within the 2400-event horizon")
    frame["first_alarm"] = alarms
    onset_index = np.rint(frame.onset_fraction.to_numpy(dtype=float) * HORIZON).astype(int)
    expected_detected = frame.first_alarm.notna().to_numpy() & (
        frame.first_alarm.fillna(-1).to_numpy(dtype=float) >= onset_index
    )
    if not np.array_equal(frame.detected.to_numpy(dtype=bool), expected_detected):
        raise ValueError("detected must count only alarms at or after the registered onset")
    expected_delay = np.where(
        expected_detected,
        frame.first_alarm.fillna(-1).to_numpy(dtype=float) - onset_index,
        HORIZON - onset_index,
    )
    if not np.allclose(frame.delay_censored, expected_delay, rtol=0, atol=1e-9):
        raise ValueError("delay_censored mishandles pre-onset alarms or nondetections")

    keys = ["seed", "onset_fraction", "budget_rate", "arm", "engine", "detector"]
    if frame.duplicated(keys).any():
        raise ValueError("duplicate stream row for seed/cell/arm/engine/detector")
    return frame


def _registered_cells() -> set[tuple[float, float]]:
    return {(onset, budget) for onset in ONSETS for budget in BUDGETS}


def _expected_panel_combinations(budget_rate: float) -> set[tuple[str, str, str]]:
    combinations: set[tuple[str, str, str]] = set()
    for arm in REQUIRED_BASE_ARMS:
        if arm == "uniform_ppi_common96p9" and not np.isclose(
            budget_rate, 0.20, rtol=0, atol=1e-12
        ):
            continue
        if arm == "feature_adwin":
            combinations.add((arm, "ADWIN", "feature_sentinel"))
            continue
        combinations.update(
            (arm, engine, detector) for engine in BASE_ENGINES for detector in DETECTORS
        )
        source_engine = SOURCE_ENGINE_BY_ARM.get(arm)
        if source_engine is not None:
            combinations.update((arm, source_engine, detector) for detector in DETECTORS)
    return combinations


def _validate_panel_coverage(frame: pd.DataFrame) -> None:
    actual_arms = set(frame.arm.unique())
    unexpected_arms = actual_arms - set(REQUIRED_BASE_ARMS)
    if unexpected_arms:
        raise ValueError(f"unregistered panel arms: {sorted(unexpected_arms)}")
    missing_arms = set(REQUIRED_BASE_ARMS) - actual_arms
    if missing_arms:
        raise ValueError(f"required panel arms are missing: {sorted(missing_arms)}")

    expected_flag = ~frame.arm.isin(FULL_FEEDBACK_ARMS)
    if not frame.same_null_harm_comparator.eq(expected_flag).all():
        raise ValueError("same_null_harm_comparator flags disagree with the registered panel")

    for onset, budget_rate in sorted(_registered_cells()):
        cell = frame.loc[
            np.isclose(frame.onset_fraction, onset, rtol=0, atol=1e-12)
            & np.isclose(frame.budget_rate, budget_rate, rtol=0, atol=1e-12)
        ]
        actual = set(cell[["arm", "engine", "detector"]].itertuples(index=False, name=None))
        expected = _expected_panel_combinations(budget_rate)
        missing = expected - actual
        extra = actual - expected
        if missing or extra:
            raise ValueError(
                f"panel engine/detector coverage mismatch at onset={onset}, budget={budget_rate}; "
                f"missing={sorted(missing)}, extra={sorted(extra)}"
            )
        for arm, engine, detector in sorted(expected):
            member = cell.loc[
                cell.arm.eq(arm) & cell.engine.eq(engine) & cell.detector.eq(detector)
            ]
            if set(member.seed.astype(int)) != set(SEEDS) or len(member) != len(SEEDS):
                raise ValueError(
                    f"panel seed block mismatch for {arm}/{engine}/{detector} "
                    f"at onset={onset}, budget={budget_rate}"
                )


def _assert_complete_block(frame: pd.DataFrame, *, label: str) -> None:
    for (onset, budget), cell in frame.groupby(["onset_fraction", "budget_rate"]):
        seeds = set(cell.seed.astype(int))
        if seeds != set(SEEDS) or len(cell) != len(SEEDS):
            raise ValueError(f"{label} seed block mismatch at onset={onset}, budget={budget}")
    cells = {
        (float(onset), float(budget))
        for onset, budget in frame[["onset_fraction", "budget_rate"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    }
    if cells != _registered_cells():
        raise ValueError(f"{label} must cover all eight registered cells")


def _wilson(detections: int, trials: int) -> tuple[float, float]:
    if trials <= 0 or not 0 <= detections <= trials:
        raise ValueError("invalid detection count")
    z = 1.959963984540054
    rate = detections / trials
    denominator = 1 + z * z / trials
    center = (rate + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / trials + z * z / (4 * trials**2)) / denominator
    return max(0.0, float(center - radius)), min(1.0, float(center + radius))


def _summary_table(frame: pd.DataFrame) -> pd.DataFrame:
    keys = [
        "onset_fraction",
        "budget_rate",
        "arm",
        "engine",
        "detector",
        "same_null_harm_comparator",
    ]
    rows: list[dict[str, Any]] = []
    for key, group in frame.groupby(keys, sort=True, dropna=False):
        onset, budget_rate, arm, engine, detector, same_null = key
        detections = int(group.detected.sum())
        low, high = _wilson(detections, len(group))
        finite_budget = group.budget.dropna()
        rows.append(
            {
                "onset_fraction": float(onset),
                "budget_rate": float(budget_rate),
                "arm": arm,
                "engine": engine,
                "detector": detector,
                "same_null_harm_comparator": bool(same_null),
                "streams": int(group.seed.nunique()),
                "detections": detections,
                "detection_rate": detections / len(group),
                "detection_wilson_95_low": low,
                "detection_wilson_95_high": high,
                "mean_delay_censored": float(group.delay_censored.mean()),
                "mean_labels": float(group.labels.mean()),
                "mean_dollars": float(group.dollars.mean()),
                "mean_budget": float(finite_budget.mean()) if len(finite_budget) else np.nan,
                "budget_violations": int(
                    (group.budget.notna() & (group.dollars > group.budget + 1e-9)).sum()
                ),
            }
        )
    return pd.DataFrame(rows)


def _bootstrap_detection_difference(
    candidate: np.ndarray, incumbent: np.ndarray, rng: np.random.Generator
) -> tuple[float, float]:
    differences = candidate.astype(float) - incumbent.astype(float)
    indices = rng.integers(0, len(differences), size=(10_000, len(differences)))
    draws = differences[indices].mean(axis=1)
    return float(np.quantile(draws, 0.025)), float(np.quantile(draws, 0.975))


def compare(streams: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Validate the complete panel and apply all frozen prescreen comparisons."""
    frame = _validate_and_normalize(streams)
    _validate_panel_coverage(frame)
    candidate_rows = frame.loc[
        frame.arm.eq(CANDIDATE_ARM)
        & frame.engine.eq(CANDIDATE_ENGINE)
        & frame.detector.eq(CANDIDATE_DETECTOR)
    ].copy()
    if candidate_rows.empty:
        raise ValueError("canonical optional_candidate/fixed1/sr arm is missing")
    _assert_complete_block(candidate_rows, label="canonical candidate")
    if candidate_rows.budget.isna().any():
        raise ValueError("canonical candidate has missing budget")

    incumbents = frame.loc[
        frame.same_null_harm_comparator
        & ~frame.arm.isin(FULL_FEEDBACK_ARMS)
        & ~frame.arm.eq(CANDIDATE_ARM)
    ].copy()
    summary = _summary_table(frame)
    rng = np.random.default_rng(123456)
    paired_rows: list[dict[str, Any]] = []
    compared_ids: set[tuple[str, str, str]] = set()
    for onset, budget_rate in sorted(_registered_cells()):
        candidate = candidate_rows.loc[
            np.isclose(candidate_rows.onset_fraction, onset, rtol=0, atol=1e-12)
            & np.isclose(candidate_rows.budget_rate, budget_rate, rtol=0, atol=1e-12)
        ].sort_values("seed")
        cell_comparisons = []
        cell_incumbents = incumbents.loc[
            np.isclose(incumbents.onset_fraction, onset, rtol=0, atol=1e-12)
            & np.isclose(incumbents.budget_rate, budget_rate, rtol=0, atol=1e-12)
        ]
        cell_comparator_ids = sorted(
            cell_incumbents[["arm", "engine", "detector"]]
            .drop_duplicates()
            .itertuples(index=False, name=None)
        )
        if not cell_comparator_ids:
            raise ValueError(f"no applicable incumbents at onset={onset}, budget={budget_rate}")
        for arm, engine, detector in cell_comparator_ids:
            compared_ids.add((arm, engine, detector))
            incumbent = cell_incumbents.loc[
                cell_incumbents.arm.eq(arm)
                & cell_incumbents.engine.eq(engine)
                & cell_incumbents.detector.eq(detector)
            ].sort_values("seed")
            if incumbent.budget.isna().any():
                raise ValueError(f"incumbent {arm}/{engine}/{detector} has missing budget")
            if not np.array_equal(candidate.seed.to_numpy(), incumbent.seed.to_numpy()):
                raise ValueError(f"paired seed mismatch for {arm}/{engine}/{detector}")
            budget_delta = candidate.budget.to_numpy(dtype=float) - incumbent.budget.to_numpy(
                dtype=float
            )
            if np.any(np.abs(budget_delta) > 1e-9):
                raise ValueError(f"hard budgets are not matched for {arm}/{engine}/{detector}")

            detection_difference = float(candidate.detected.mean() - incumbent.detected.mean())
            ci_low, ci_high = _bootstrap_detection_difference(
                candidate.detected.to_numpy(dtype=bool),
                incumbent.detected.to_numpy(dtype=bool),
                rng,
            )
            candidate_delay = float(candidate.delay_censored.mean())
            incumbent_delay = float(incumbent.delay_censored.mean())
            delay_ratio = incumbent_delay / candidate_delay if candidate_delay > 0 else None
            labels_delta = float(candidate.labels.mean() - incumbent.labels.mean())
            dollars_delta = float(candidate.dollars.mean() - incumbent.dollars.mean())
            resources_pass = labels_delta <= 1e-9 and dollars_delta <= 1e-9
            primary_cell = (onset, budget_rate) == PRIMARY_CELL
            if primary_cell:
                detection_pass = detection_difference >= 0.10 - 1e-12
                delay_pass = delay_ratio is not None and delay_ratio >= 1.5 - 1e-12
                effect_pass = detection_pass or delay_pass
                criterion = "primary_plus_10pp_or_1p5x_delay"
            else:
                detection_pass = detection_difference >= -0.03 - 1e-12
                delay_pass = None
                effect_pass = detection_pass
                criterion = "secondary_noninferiority_minus_3pp"
            passed = bool(effect_pass and resources_pass)
            row = {
                "onset_fraction": onset,
                "budget_rate": budget_rate,
                "candidate_arm": CANDIDATE_ARM,
                "candidate_engine": CANDIDATE_ENGINE,
                "candidate_detector": CANDIDATE_DETECTOR,
                "incumbent_arm": arm,
                "incumbent_engine": engine,
                "incumbent_detector": detector,
                "streams": len(candidate),
                "candidate_detection_rate": float(candidate.detected.mean()),
                "incumbent_detection_rate": float(incumbent.detected.mean()),
                "detection_difference": detection_difference,
                "detection_difference_bootstrap_95_low": ci_low,
                "detection_difference_bootstrap_95_high": ci_high,
                "candidate_mean_delay_censored": candidate_delay,
                "incumbent_mean_delay_censored": incumbent_delay,
                "delay_ratio_incumbent_over_candidate": delay_ratio,
                "candidate_mean_labels": float(candidate.labels.mean()),
                "incumbent_mean_labels": float(incumbent.labels.mean()),
                "mean_labels_difference": labels_delta,
                "candidate_mean_dollars": float(candidate.dollars.mean()),
                "incumbent_mean_dollars": float(incumbent.dollars.mean()),
                "mean_dollars_difference": dollars_delta,
                "mean_budget_difference": float(budget_delta.mean()),
                "resources_pass": resources_pass,
                "detection_margin_pass": bool(detection_pass),
                "delay_margin_pass": delay_pass,
                "criterion": criterion,
                "passes_comparison": passed,
            }
            paired_rows.append(row)
            cell_comparisons.append(passed)

    paired = pd.DataFrame(paired_rows)
    cell_decisions: list[dict[str, Any]] = []
    for (onset, budget_rate), group in paired.groupby(["onset_fraction", "budget_rate"], sort=True):
        cell_decisions.append(
            {
                "onset_fraction": float(onset),
                "budget_rate": float(budget_rate),
                "comparators": len(group),
                "all_comparisons_pass": bool(group.passes_comparison.all()),
            }
        )
    primary_decision = next(
        row for row in cell_decisions if (row["onset_fraction"], row["budget_rate"]) == PRIMARY_CELL
    )
    secondary_decisions = [
        row for row in cell_decisions if (row["onset_fraction"], row["budget_rate"]) != PRIMARY_CELL
    ]
    advance = bool(
        primary_decision["all_comparisons_pass"]
        and all(row["all_comparisons_pass"] for row in secondary_decisions)
    )
    decision = {
        "evidence_stage": "20-seed WP3 prescreen only",
        "calibration_established": False,
        "confirmation_claim": False,
        "primary_cell": {
            "onset_fraction": PRIMARY_CELL[0],
            "budget_rate": PRIMARY_CELL[1],
            **primary_decision,
        },
        "secondary_cells": secondary_decisions,
        "all_registered_cells_pass": advance,
        "outcome": "advance_prescreen_only" if advance else "stop_prescreen",
        "incumbents_compared": [
            {"arm": arm, "engine": engine, "detector": detector}
            for arm, engine, detector in sorted(compared_ids)
        ],
        "bootstrap": {"replicates": 10000, "seed": 123456, "interval": "percentile 95%"},
    }
    return summary, paired, decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir", type=Path, default=ROOT / "outputs/data_efficient_prescreen_20"
    )
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    input_dir = args.input_dir.resolve()
    streams_path = input_dir / "streams.csv"
    input_manifest_path = input_dir / "manifest.json"
    output_dir = (args.output_dir or (input_dir / "analysis")).resolve()
    if output_dir.exists():
        raise FileExistsError(f"refusing to overwrite analysis directory: {output_dir}")
    manifest = json.loads(input_manifest_path.read_text(encoding="utf-8"))
    actual_input_hash = sha256(streams_path)
    expected_input_hash = manifest.get("outputs_sha256", {}).get("streams.csv")
    if expected_input_hash is None or expected_input_hash != actual_input_hash:
        raise ValueError(
            "streams.csv checksum is missing from or disagrees with the input manifest"
        )
    streams = pd.read_csv(streams_path)
    summary, paired, decision = compare(streams)

    output_dir.mkdir(parents=True, exist_ok=False)
    summary_path = output_dir / "summary.csv"
    paired_path = output_dir / "paired.csv"
    decision_path = output_dir / "decision.json"
    summary.to_csv(summary_path, index=False)
    paired.to_csv(paired_path, index=False)
    decision_path.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    output_manifest = {
        "input_streams_sha256": actual_input_hash,
        "input_manifest_sha256": sha256(input_manifest_path),
        "analysis_source_sha256": sha256(Path(__file__).resolve()),
        "outputs_sha256": {
            path.name: sha256(path) for path in (summary_path, paired_path, decision_path)
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(output_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
