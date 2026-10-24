"""Summarize the frozen radius-grid fallback-exposure development replay."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _paired_interval(values: np.ndarray, indices: np.ndarray) -> tuple[float, float, float]:
    draws = values[indices].mean(axis=1)
    low, high = np.quantile(draws, [0.025, 0.975])
    return float(values.mean()), float(low), float(high)


def analyze(input_path: Path, output_dir: Path, *, bootstrap_replicates: int, seed: int) -> None:
    frame = pd.read_parquet(input_path)
    keys = ["scenario", "seed", "method"]
    if frame.empty or frame.duplicated(keys).any():
        raise ValueError("input metrics must contain unique nonempty scenario/seed/method rows")
    if not frame["budget_respected"].all():
        raise ValueError("input includes a hard label-dollar budget violation")
    if frame.groupby(["scenario", "method"]).size().nunique() != 1:
        raise ValueError("scenario/method cells have unequal seed counts")
    required = {
        "evaluator_cumulative_excess_cost_until_fallback",
        "evaluator_full_horizon_excess_cost_after_harm_onset",
        "evaluator_excess_cost_avoided_by_fallback",
        "stream_mean_estimation_error",
    }
    if not required <= set(frame.columns):
        raise ValueError(
            f"missing required evaluator metrics: {sorted(required - set(frame.columns))}"
        )
    if not np.allclose(
        frame["evaluator_excess_cost_avoided_by_fallback"],
        frame["evaluator_full_horizon_excess_cost_after_harm_onset"]
        - frame["evaluator_cumulative_excess_cost_until_fallback"],
    ):
        raise ValueError("avoided exposure does not equal full-horizon minus fallback exposure")
    frame["exposure_if_alarm_only_fallback"] = np.where(
        frame["single_e_alarm_time"].notna(),
        frame["evaluator_cumulative_excess_cost_until_fallback"],
        frame["evaluator_full_horizon_excess_cost_after_harm_onset"],
    )
    if (
        frame.groupby(["scenario", "seed"])["evaluator_full_horizon_excess_cost_after_harm_onset"]
        .nunique(dropna=False)
        .max()
        != 1
    ):
        raise ValueError("full-horizon evaluator exposure should be method-invariant per stream")

    methods = sorted(frame["method"].unique())
    scenarios = sorted(frame["scenario"].unique())
    seeds = np.sort(frame["seed"].unique())
    if "uniform_proxy" not in methods or "boundary_local_harm" not in scenarios:
        raise ValueError("comparison requires uniform_proxy and boundary_local_harm")
    if bootstrap_replicates < 1000:
        raise ValueError("use at least 1,000 paired seed bootstrap replicates")

    summary_rows: list[dict[str, object]] = []
    for (scenario, method), group in frame.groupby(["scenario", "method"], sort=True):
        harmful = group[group["material_harm"]]
        errors = group["stream_mean_estimation_error"].to_numpy(dtype=float)
        summary_rows.append(
            {
                "scenario": scenario,
                "method": method,
                "streams": len(group),
                "stream_mean_rmse": float(np.sqrt(np.mean(errors**2))),
                "mean_fallback_exposure": float(
                    group["evaluator_cumulative_excess_cost_until_fallback"].mean()
                ),
                "mean_exposure_if_alarm_only_fallback": float(
                    group["exposure_if_alarm_only_fallback"].mean()
                ),
                "mean_full_horizon_exposure": float(
                    group["evaluator_full_horizon_excess_cost_after_harm_onset"].mean()
                ),
                "mean_excess_cost_avoided": float(
                    group["evaluator_excess_cost_avoided_by_fallback"].mean()
                ),
                "harmful_streams": len(harmful),
                "harm_onsets_reached": int(harmful["harm_reached_before_budget_stop"].sum()),
                "harm_detections": int(harmful["single_e_detected"].sum()),
                "false_escalations": int(group["single_e_false_escalation"].sum()),
                "fallback_events": int(group["evaluator_fallback_event"].notna().sum()),
                "alarm_triggered_fallbacks": int(group["single_e_alarm_time"].notna().sum()),
                "budget_stop_fallbacks": int(
                    (
                        group["single_e_alarm_time"].isna()
                        & group["evaluator_fallback_event"].notna()
                    ).sum()
                ),
                "mean_label_spend": float(group["realized_label_spend"].mean()),
                "mean_labels": float(group["labels_queried"].mean()),
                "mean_processed_events": float(group["processed_events"].mean()),
            }
        )
    summary = pd.DataFrame(summary_rows)

    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(seeds), size=(bootstrap_replicates, len(seeds)))
    error_wide = frame.pivot(
        index=["seed", "scenario"], columns="method", values="stream_mean_estimation_error"
    )
    error_by_method = {
        method: error_wide[method].unstack("scenario").loc[seeds, scenarios].to_numpy(dtype=float)
        for method in methods
    }
    base_errors = error_by_method["uniform_proxy"]
    base_rmse = float(np.sqrt(np.mean(base_errors**2)))
    harmful = frame[frame["scenario"].eq("boundary_local_harm")]
    harmful_wide = harmful.pivot(
        index="seed", columns="method", values="evaluator_cumulative_excess_cost_until_fallback"
    ).loc[seeds]
    alarm_exposure_wide = harmful.pivot(
        index="seed", columns="method", values="exposure_if_alarm_only_fallback"
    ).loc[seeds]
    detection_wide = harmful.pivot(index="seed", columns="method", values="single_e_detected").loc[
        seeds
    ]
    label_wide = harmful.pivot(index="seed", columns="method", values="labels_queried").loc[seeds]
    spend_wide = harmful.pivot(index="seed", columns="method", values="realized_label_spend").loc[
        seeds
    ]
    horizon_wide = harmful.pivot(index="seed", columns="method", values="processed_events").loc[
        seeds
    ]

    paired_rows: list[dict[str, object]] = []
    for method in methods:
        if method == "uniform_proxy":
            continue
        method_rmse = float(np.sqrt(np.mean(error_by_method[method] ** 2)))
        boot_method_rmse = np.sqrt(np.mean(error_by_method[method][indices] ** 2, axis=(1, 2)))
        boot_base_rmse = np.sqrt(np.mean(base_errors[indices] ** 2, axis=(1, 2)))
        rmse_delta = method_rmse - base_rmse
        rmse_ci = np.quantile(boot_method_rmse - boot_base_rmse, [0.025, 0.975])

        outcomes = {
            "exposure": harmful_wide[method].to_numpy(dtype=float)
            - harmful_wide["uniform_proxy"].to_numpy(dtype=float),
            "alarm_only_exposure": alarm_exposure_wide[method].to_numpy(dtype=float)
            - alarm_exposure_wide["uniform_proxy"].to_numpy(dtype=float),
            "detection": detection_wide[method].astype(float).to_numpy()
            - detection_wide["uniform_proxy"].astype(float).to_numpy(),
            "labels": label_wide[method].to_numpy(dtype=float)
            - label_wide["uniform_proxy"].to_numpy(dtype=float),
            "label_spend": spend_wide[method].to_numpy(dtype=float)
            - spend_wide["uniform_proxy"].to_numpy(dtype=float),
            "processed_events": horizon_wide[method].to_numpy(dtype=float)
            - horizon_wide["uniform_proxy"].to_numpy(dtype=float),
        }
        row: dict[str, object] = {
            "method": method,
            "macro_stream_mean_rmse": method_rmse,
            "macro_rmse_difference_vs_uniform": rmse_delta,
            "macro_rmse_ci_low": float(rmse_ci[0]),
            "macro_rmse_ci_high": float(rmse_ci[1]),
        }
        for outcome, values in outcomes.items():
            mean, low, high = _paired_interval(values, indices)
            row[f"{outcome}_difference_vs_uniform"] = mean
            row[f"{outcome}_ci_low"] = low
            row[f"{outcome}_ci_high"] = high
        paired_rows.append(row)
    paired = pd.DataFrame(paired_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "scenario_method_summary.csv"
    paired_path = output_dir / "paired_contrasts_vs_uniform.csv"
    summary.to_csv(summary_path, index=False)
    paired.to_csv(paired_path, index=False)
    manifest = {
        "analysis": "radius_grid_decision_harm_exposure_development",
        "input_path": str(input_path),
        "input_sha256": _sha256(input_path),
        "analysis_script_sha256": _sha256(Path(__file__)),
        "seed_count": len(seeds),
        "methods": methods,
        "scenarios": scenarios,
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": seed,
        "intervals": "paired percentile bootstrap over matched seed clusters; descriptive and unadjusted",
        "outputs": {
            summary_path.name: _sha256(summary_path),
            paired_path.name: _sha256(paired_path),
        },
    }
    (output_dir / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {summary_path}")
    print(f"Wrote {paired_path}")
    print(f"Wrote {output_dir / 'analysis_manifest.json'}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(
            "outputs/robust_active_inference_radius_exposure_development/metrics/"
            "hard_budget_comparison.parquet"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/robust_active_inference_radius_exposure_development/analysis"),
    )
    parser.add_argument("--bootstrap-replicates", type=int, default=20_000)
    parser.add_argument("--seed", type=int, default=20261024)
    args = parser.parse_args()
    analyze(
        args.input,
        args.output_dir,
        bootstrap_replicates=args.bootstrap_replicates,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
