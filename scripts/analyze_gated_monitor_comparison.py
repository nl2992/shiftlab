"""Registered WP1 calibration and paired development summaries; no figures."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import beta, binomtest

ROOT = Path(__file__).resolve().parents[1]


def exact_upper(alarms: int, streams: int, cells: int) -> float:
    if streams <= 0 or cells < 1 or not 0 <= alarms <= streams:
        raise ValueError("invalid binomial counts/family size")
    return (
        1.0
        if alarms == streams
        else float(beta.ppf(1 - 0.05 / cells, alarms + 1, streams - alarms))
    )


def paired_bootstrap(first, second, *, ratio=False) -> dict:
    a, b = np.asarray(first, dtype=float), np.asarray(second, dtype=float)
    if a.ndim != 1 or a.shape != b.shape or not len(a) or not np.isfinite(a + b).all():
        raise ValueError("paired endpoints must be finite matching vectors")
    rng = np.random.default_rng(20261027)
    indices = rng.integers(len(a), size=(10000, len(a)))
    numerator, denominator = a[indices].mean(axis=1), b[indices].mean(axis=1)
    if ratio:
        if b.mean() <= 0:
            return {
                "estimate": None,
                "lower_97p5_one_sided": None,
                "difference": float(np.mean(a - b)),
                "ratio_defined": False,
            }
        # Resamples with nonpositive denominators cannot support a positive ratio bound.
        if float(np.mean(denominator <= 0)) >= 0.025:
            return {
                "estimate": float(a.mean() / b.mean()),
                "lower_97p5_one_sided": None,
                "ratio_defined": True,
                "uncertainty_defined": False,
                "reason": "at least 2.5% of paired bootstrap denominators are nonpositive",
            }
        draws = np.full(len(indices), -np.inf)
        np.divide(numerator, denominator, out=draws, where=denominator > 0)
        estimate = float(a.mean() / b.mean())
    else:
        draws = numerator - denominator
        estimate = float(np.mean(a - b))
    return {
        "estimate": estimate,
        "lower_97p5_one_sided": float(np.quantile(draws, 0.025)),
        "lower_95_two_sided": float(np.quantile(draws, 0.025)),
        "upper_95_two_sided": float(np.quantile(draws, 0.975)),
        "ratio_defined": ratio,
    }


def calibrate(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    frame = frame.copy()
    sentinel = frame.arm.eq("feature_adwin")
    frame = frame[~sentinel | frame.scenario.eq("stationary")].copy()
    if "feature_false_alarm" in frame:
        frame.loc[frame.arm.eq("feature_adwin"), "false_alarm"] = frame.loc[
            frame.arm.eq("feature_adwin"), "feature_false_alarm"
        ]
    for _, group in frame.groupby(["arm", "scenario", "budget_rate"]):
        if set(group.seed) != set(range(58500000, 58502000)):
            raise ValueError("calibration seed block mismatch")
    keys = ["arm", "scenario", "budget_rate"]
    table = (
        frame.groupby(keys, sort=True)
        .agg(
            alarms=("false_alarm", "sum"),
            streams=("seed", "nunique"),
            rows=("seed", "size"),
        )
        .reset_index()
    )
    if not (table.streams.eq(2000) & table.rows.eq(2000)).all():
        raise ValueError("calibration requires exactly 2000 unique streams per registered cell")
    per_arm = table.groupby("arm").size().to_dict()
    for arm, cells in per_arm.items():
        expected_cells = (
            4 if arm == "feature_adwin" else (2 if arm.startswith("uniform_ppi_common96p9") else 8)
        )
        if cells != expected_cells:
            raise ValueError(f"incomplete registered calibration cells for {arm}")
    table["family_cells"] = table.arm.map(per_arm)
    table["simultaneous_exact_upper"] = [
        exact_upper(int(row.alarms), int(row.streams), int(row.family_cells))
        for row in table.itertuples()
    ]
    passed = table.groupby("arm").simultaneous_exact_upper.max().le(0.05).to_dict()
    return table, {
        "primary_passes": bool(passed.get("gated_ht_paced", False)),
        "arm_passes": passed,
        "confidence_family": "scenario x budget within each arm",
        "comparison_allowed": bool(passed.get("gated_ht_paced", False)),
    }


def compare(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    if frame.duplicated(["scenario", "budget_rate", "seed", "arm"]).any():
        raise ValueError("duplicate paired stream rows")
    primary = frame[frame.scenario.eq("boundary_local_harm")]
    growth = primary[primary.budget_rate.eq(0.2) & primary.arm.eq("gated_ht_paced")].sort_values(
        "seed"
    )
    if len(growth) != 100:
        raise ValueError("P1 requires 100 registered paired seeds")
    p1 = paired_bootstrap(
        growth.growth_vs_uniform_ppi, growth.comparator_growth_uniform_ppi, ratio=True
    )
    detection = primary[primary.budget_rate.eq(0.05)].pivot(
        index="seed", columns="arm", values="detected"
    )
    if set(detection.index) != set(range(58400000, 58400100)):
        raise ValueError("P2 seed block mismatch")
    a, b = detection.gated_ht_paced.astype(int), detection.uniform_ppi.astype(int)
    p2 = paired_bootstrap(a, b)
    wins, losses = int(((a == 1) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum())
    p2["mcnemar_one_sided_p"] = (
        float(binomtest(wins, wins + losses, 0.5, alternative="greater").pvalue)
        if wins + losses
        else 1.0
    )
    p2["discordant_wins"], p2["discordant_losses"] = wins, losses
    p1_pass = (
        p1["estimate"] is not None
        and p1["lower_97p5_one_sided"] is not None
        and p1["lower_97p5_one_sided"] >= 2
    )
    p2_pass = p2["lower_97p5_one_sided"] > 0 and p2["mcnemar_one_sided_p"] < 0.025
    predictions = {0.02: 18.0, 0.05: 18.0, 0.1: 15.0, 0.2: 7.5}
    ratios = []
    for budget, prediction in predictions.items():
        cell = primary[primary.budget_rate.eq(budget) & primary.arm.eq("gated_ht_paced")]
        numerator, denominator = (
            cell.growth_vs_uniform_ppi.mean(),
            cell.comparator_growth_uniform_ppi.mean(),
        )
        measured = float(numerator / denominator) if denominator > 0 else None
        ratios.append(
            {
                "budget": budget,
                "predicted": prediction,
                "measured": measured,
                "within_factor_two": measured is not None and 0.5 <= measured / prediction <= 2,
            }
        )
    summary = (
        frame.groupby(["scenario", "budget_rate", "arm", "engine"], sort=True)
        .agg(
            streams=("seed", "nunique"),
            detection=("detected", "mean"),
            false_alarm=("false_alarm", "mean"),
            censored_delay=("censored_delay", "mean"),
            labels=("labels", "mean"),
            dollars=("dollars", "mean"),
            processed=("processed", "mean"),
        )
        .reset_index()
    )
    summary["detection_lower_95"] = [
        0.0
        if row.detection == 0
        else beta.ppf(
            0.025,
            round(row.detection * row.streams),
            row.streams - round(row.detection * row.streams) + 1,
        )
        for row in summary.itertuples()
    ]
    summary["detection_upper_95"] = [
        1.0
        if row.detection == 1
        else beta.ppf(
            0.975,
            round(row.detection * row.streams) + 1,
            row.streams - round(row.detection * row.streams),
        )
        for row in summary.itertuples()
    ]
    return summary, {
        "p1": p1,
        "p2": p2,
        "p1_passes": p1_pass,
        "p2_passes": p2_pass,
        "gating_material_before_calibration_guard": p1_pass and p2_pass,
        "prediction_matches": all(row["within_factor_two"] for row in ratios),
        "growth_prediction_table": ratios,
        "evidence_stage": "fresh development comparison",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["null", "compare"], required=True)
    args = parser.parse_args()
    directory = ROOT / f"outputs/gated_monitor_{args.stage}"
    source = directory / "streams.parquet"
    manifest = json.loads((directory / "manifest.json").read_text())
    actual = hashlib.sha256(source.read_bytes()).hexdigest()
    if actual != manifest["outputs_sha256"]["streams.parquet"]:
        raise ValueError("input checksum mismatch")
    frame = pd.read_parquet(source)
    table, decision = calibrate(frame) if args.stage == "null" else compare(frame)
    if args.stage == "compare":
        calibration = json.loads(
            (ROOT / "outputs/gated_monitor_null/analysis/decision.json").read_text()
        )
        decision["gating_material"] = calibration["primary_passes"] and decision.pop(
            "gating_material_before_calibration_guard"
        )
        decision["excluded_failed_calibration"] = [
            arm for arm, passed in calibration["arm_passes"].items() if not passed
        ]
    output = directory / "analysis"
    if output.exists() and any(output.iterdir()):
        raise FileExistsError("refusing to overwrite analysis")
    output.mkdir(exist_ok=True)
    table.to_csv(output / "summary.csv", index=False)
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    provenance = {
        "input_sha256": actual,
        "analysis_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir()
        },
    }
    (output / "manifest.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(decision, indent=2))


if __name__ == "__main__":
    main()
