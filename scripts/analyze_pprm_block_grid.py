"""Summarize matched adaptive-PPI block-size development runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

BLOCK_SIZES = (5, 10, 20, 40)
METHODS = ("pprm_block_adaptive", "uniform_proxy_frozen", "uniform_proxy")


def _load_runs(root: Path, block_sizes: tuple[int, ...]) -> pd.DataFrame:
    frames = []
    for block_size in block_sizes:
        path = root / f"block_{block_size:02d}" / "metrics" / "hard_budget_comparison.parquet"
        if not path.is_file():
            raise FileNotFoundError(f"missing completed block-grid run: {path}")
        frame = pd.read_parquet(path)
        if set(frame.method) != set(METHODS):
            raise ValueError(f"unexpected methods in {path}: {sorted(frame.method.unique())}")
        if (
            not frame.pprm_block_size.loc[frame.method.eq("pprm_block_adaptive")]
            .eq(block_size)
            .all()
        ):
            raise ValueError(f"block-size metadata mismatch in {path}")
        # Eventwise controls do not use PPRM block size; pair their rows with
        # the block-size run that generated the same seed/scenario stream.
        frame["grid_block_size"] = block_size
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _summarize(metrics: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary = (
        metrics.groupby(["grid_block_size", "scenario", "method"], dropna=False)
        .agg(
            streams=("seed", "nunique"),
            mean_budget=("hard_budget", "mean"),
            mean_spend=("realized_label_spend", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events=("processed_events", "mean"),
            mean_monitor_fraction=("monitor_fraction_processed", "mean"),
            stream_mean_rmse=("stream_mean_estimation_error", lambda x: np.sqrt(np.mean(x**2))),
            detections=("single_e_detected", "sum"),
            false_escalations=("single_e_false_escalation", "sum"),
            harm_reached=("harm_reached_before_budget_stop", "sum"),
            harmful_streams=("material_harm", "sum"),
            mean_eta=("pprm_reliance_mean", "mean"),
        )
        .reset_index()
        .rename(columns={"grid_block_size": "pprm_block_size"})
    )
    rng = np.random.default_rng(20372099)
    paired_rows = []
    for (block_size, scenario), group in metrics.groupby(["grid_block_size", "scenario"]):
        pprm = group.loc[group.method.eq("pprm_block_adaptive")].sort_values("seed")
        frozen = group.loc[group.method.eq("uniform_proxy_frozen")].sort_values("seed")
        matched = pprm.merge(frozen, on=["scenario", "seed"], suffixes=("_pprm", "_frozen"))
        if len(matched) != len(pprm) or len(matched) != len(frozen):
            raise ValueError("matched methods do not have identical seed sets")
        pprm_error = matched.stream_mean_estimation_error_pprm.to_numpy()
        frozen_error = matched.stream_mean_estimation_error_frozen.to_numpy()
        n = len(matched)
        draws = rng.integers(0, n, size=(20_000, n))
        rmse_delta = np.sqrt(np.mean(pprm_error[draws] ** 2, axis=1)) - np.sqrt(
            np.mean(frozen_error[draws] ** 2, axis=1)
        )
        pprm_detected = matched.single_e_detected_pprm.astype(bool).to_numpy()
        frozen_detected = matched.single_e_detected_frozen.astype(bool).to_numpy()
        pprm_false = matched.single_e_false_escalation_pprm.astype(bool).to_numpy()
        frozen_false = matched.single_e_false_escalation_frozen.astype(bool).to_numpy()
        paired_rows.append(
            {
                "pprm_block_size": block_size,
                "scenario": scenario,
                "seeds": n,
                "pprm_rmse": float(np.sqrt(np.mean(pprm_error**2))),
                "frozen_eventwise_rmse": float(np.sqrt(np.mean(frozen_error**2))),
                "rmse_difference_pprm_minus_frozen": float(
                    np.sqrt(np.mean(pprm_error**2)) - np.sqrt(np.mean(frozen_error**2))
                ),
                "rmse_difference_ci_low": float(np.quantile(rmse_delta, 0.025)),
                "rmse_difference_ci_high": float(np.quantile(rmse_delta, 0.975)),
                "pprm_only_detections": int(np.sum(pprm_detected & ~frozen_detected)),
                "frozen_only_detections": int(np.sum(frozen_detected & ~pprm_detected)),
                "pprm_false_escalations": int(pprm_false.sum()),
                "frozen_false_escalations": int(frozen_false.sum()),
                "harm_reached": int(matched.harm_reached_before_budget_stop_pprm.sum()),
                "harmful_streams": int(matched.material_harm_pprm.sum()),
                "mean_spend_difference": float(
                    matched.realized_label_spend_pprm.mean()
                    - matched.realized_label_spend_frozen.mean()
                ),
                "mean_label_difference": float(
                    matched.labels_queried_pprm.mean() - matched.labels_queried_frozen.mean()
                ),
                "mean_event_difference": float(
                    matched.processed_events_pprm.mean() - matched.processed_events_frozen.mean()
                ),
            }
        )
    return summary, pd.DataFrame(paired_rows)


def _plot(summary: pd.DataFrame, path: Path, block_sizes: tuple[int, ...]) -> None:
    scenarios = sorted(summary.scenario.unique())
    fig, axes = plt.subplots(2, len(scenarios), figsize=(4 * len(scenarios), 8), squeeze=False)
    for column, scenario in enumerate(scenarios):
        subset = summary.loc[summary.scenario.eq(scenario)]
        for method in METHODS:
            method_data = subset.loc[subset.method.eq(method)].sort_values("pprm_block_size")
            label = {
                "pprm_block_adaptive": "Adaptive block PPI",
                "uniform_proxy_frozen": "Eventwise, frozen proxy",
                "uniform_proxy": "Eventwise, updating proxy",
            }[method]
            axes[0, column].plot(
                method_data.pprm_block_size,
                method_data.stream_mean_rmse,
                marker="o",
                label=label,
            )
            harm_rate = method_data.detections / method_data.harmful_streams.replace(0, np.nan)
            axes[1, column].plot(
                method_data.pprm_block_size,
                harm_rate,
                marker="o",
                label=label,
            )
        axes[0, column].set_title(scenario)
        axes[0, column].set_xscale("log", base=2)
        axes[0, column].set_xticks(block_sizes, labels=block_sizes)
        axes[1, column].set_xscale("log", base=2)
        axes[1, column].set_xticks(block_sizes, labels=block_sizes)
        axes[1, column].set_ylim(0, 1)
        axes[0, column].grid(alpha=0.2)
        axes[1, column].grid(alpha=0.2)
    axes[0, 0].set_ylabel("RMSE of stream-mean cost estimate")
    axes[1, 0].set_ylabel("Detection rate (harmful scenarios)")
    axes[0, -1].legend(fontsize=7, loc="best")
    fig.suptitle("Adaptive block PPI development screen; 30 paired seeds per cell")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_block_grid_development")
    )
    parser.add_argument(
        "--block-sizes", nargs="+", type=int, choices=BLOCK_SIZES, default=BLOCK_SIZES
    )
    args = parser.parse_args()
    block_sizes = tuple(args.block_sizes)
    metrics = _load_runs(args.output_root, block_sizes)
    summary, paired = _summarize(metrics)
    analysis = args.output_root / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    summary.to_csv(analysis / "block_grid_summary.csv", index=False)
    paired.to_csv(analysis / "paired_vs_frozen_eventwise.csv", index=False)
    figure = analysis / "block_grid_tradeoffs.png"
    _plot(summary, figure, block_sizes)
    lines = [
        "# Adaptive PPI block-size development screen",
        "",
        "This is a development-only comparison with 30 paired seeds per scenario and block size. The null controls and four harm scenarios use the same synthetic streams, nominal 20% label-dollar budget, and frozen-proxy eventwise comparator. The eventwise updating-proxy control is included to show the effect of online proxy refitting. The percentile intervals below are paired seed-bootstrap intervals for stream-mean RMSE differences; they are exploratory and unadjusted across cells.",
        "",
        "No method selection, false-alarm guarantee, or confirmatory conclusion should be based on this screen. Use disjoint streams for the 2,000-per-cell null calibration and separate power study.",
        "",
        "|Block size|Scenario|Method|Streams|RMSE|Detections|False escalations|Mean spend|Mean labels|Mean events|Mean eta|",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        eta = "n/a" if pd.isna(row["mean_eta"]) else f"{row['mean_eta']:.3f}"
        lines.append(
            f"|{row['pprm_block_size']}|{row['scenario']}|{row['method']}|{row['streams']}|{row['stream_mean_rmse']:.4f}|{row['detections']}/{row['harmful_streams']}|{row['false_escalations']}/{row['streams']}|{row['mean_spend']:.2f}|{row['mean_labels']:.1f}|{row['mean_events']:.1f}|{eta}|"
        )
    lines.extend(
        [
            "",
            "## Paired block PPI versus frozen eventwise PPI",
            "",
            "|Block size|Scenario|RMSE difference (95% bootstrap CI)|PPRM-only detections|Frozen-only detections|Harm reached|Spend difference|Label difference|Event difference|",
            "|---:|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in paired.to_dict("records"):
        lines.append(
            f"|{row['pprm_block_size']}|{row['scenario']}|{row['rmse_difference_pprm_minus_frozen']:.4f} [{row['rmse_difference_ci_low']:.4f}, {row['rmse_difference_ci_high']:.4f}]|{row['pprm_only_detections']}|{row['frozen_only_detections']}|{row['harm_reached']}/{row['harmful_streams']}|{row['mean_spend_difference']:.2f}|{row['mean_label_difference']:.1f}|{row['mean_event_difference']:.1f}|"
        )
    lines.extend(["", "![Block-size tradeoffs](block_grid_tradeoffs.png)", ""])
    (analysis / "block_grid_analysis.md").write_text("\n".join(lines), encoding="utf-8")

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    input_paths = [
        args.output_root / f"block_{block_size:02d}" / "metrics" / "hard_budget_comparison.parquet"
        for block_size in block_sizes
    ]
    output_paths = [
        analysis / "block_grid_summary.csv",
        analysis / "paired_vs_frozen_eventwise.csv",
        figure,
        analysis / "block_grid_analysis.md",
    ]
    manifest = {
        "analysis": "pprm_block_size_development_screen",
        "classification": "development_only_unadjusted",
        "block_sizes": list(block_sizes),
        "paired_seed_bootstrap": {
            "resamples": 20_000,
            "seed": 20372099,
            "interval": "percentile 95%",
        },
        "sha256": {
            "source_files": {
                "scripts/analyze_pprm_block_grid.py": sha256(Path(__file__)),
                "scripts/run_pprm_block_grid.py": sha256(
                    Path(__file__).with_name("run_pprm_block_grid.py")
                ),
            },
            "inputs": {path.as_posix(): sha256(path) for path in input_paths},
            "artifacts": {str(path.relative_to(analysis)): sha256(path) for path in output_paths},
        },
    }
    (analysis / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(analysis / "block_grid_analysis.md")


if __name__ == "__main__":
    main()
