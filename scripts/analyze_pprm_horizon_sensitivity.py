"""Summarize fixed-monitor horizon development results."""

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

HORIZONS = (1600, 3200, 6400)
METHODS = ("pprm_block_adaptive", "uniform_proxy_frozen", "uniform_proxy")


def _load(root: Path) -> pd.DataFrame:
    frames = []
    for n in HORIZONS:
        path = root / f"n_{n}" / "metrics" / "hard_budget_comparison.parquet"
        if not path.is_file():
            raise FileNotFoundError(f"missing completed horizon run: {path}")
        frame = pd.read_parquet(path)
        if set(frame.method) != set(METHODS):
            raise ValueError(f"unexpected methods in {path}: {sorted(frame.method.unique())}")
        pprm = frame.loc[frame.method.eq("pprm_block_adaptive")]
        if not pprm.pprm_max_reliance.eq(0.1).all():
            raise ValueError(f"reliance cap mismatch in {path}")
        frame["horizon_n"] = n
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_horizon_development_v1")
    )
    args = parser.parse_args()
    metrics = _load(args.output_root)
    summary = (
        metrics.groupby(["horizon_n", "scenario", "method"], dropna=False)
        .agg(
            streams=("seed", "nunique"),
            harmful_streams=("material_harm", "sum"),
            harm_reached=("harm_reached_before_budget_stop", "sum"),
            detections=("single_e_detected", "sum"),
            false_escalations=("single_e_false_escalation", "sum"),
            stream_mean_rmse=("stream_mean_estimation_error", lambda x: np.sqrt(np.mean(x**2))),
            mean_expected_harm=("mean_expected_decision_harm", "mean"),
            mean_spend=("realized_label_spend", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events=("processed_events", "mean"),
            mean_lower_bound=("pprm_confidence_lower_bound", "mean"),
        )
        .reset_index()
    )
    analysis = args.output_root / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    summary.to_csv(analysis / "horizon_summary.csv", index=False)
    scenarios = sorted(summary.scenario.unique())
    fig, axes = plt.subplots(2, len(scenarios), figsize=(4 * len(scenarios), 8), squeeze=False)
    for column, scenario in enumerate(scenarios):
        subset = summary.loc[summary.scenario.eq(scenario)]
        for method in METHODS:
            values = subset.loc[subset.method.eq(method)].sort_values("horizon_n")
            label = {
                "pprm_block_adaptive": "Block PPI (eta cap .1)",
                "uniform_proxy_frozen": "Eventwise, frozen proxy",
                "uniform_proxy": "Eventwise, updating proxy",
            }[method]
            axes[0, column].plot(values.horizon_n, values.stream_mean_rmse, marker="o", label=label)
            rate = values.detections / values.harmful_streams.replace(0, np.nan)
            axes[1, column].plot(values.horizon_n, rate, marker="o", label=label)
        axes[0, column].set_title(scenario)
        axes[0, column].set_xscale("log", base=2)
        axes[0, column].set_xticks(HORIZONS, labels=[str(x) for x in HORIZONS])
        axes[1, column].set_xscale("log", base=2)
        axes[1, column].set_xticks(HORIZONS, labels=[str(x) for x in HORIZONS])
        axes[1, column].set_ylim(0, 1)
        axes[0, column].grid(alpha=0.2)
        axes[1, column].grid(alpha=0.2)
    axes[0, 0].set_ylabel("RMSE of stream-mean cost estimate")
    axes[1, 0].set_ylabel("Detection rate in harmful scenarios")
    axes[0, -1].legend(fontsize=7, loc="best")
    fig.suptitle("Fixed reliance cap; independent development seed block")
    fig.tight_layout()
    figure = analysis / "horizon_sensitivity.png"
    fig.savefig(figure, dpi=180)
    plt.close(fig)

    lines = [
        "# PPI horizon sensitivity",
        "",
        "Development-only experiment on a seed block disjoint from the earlier block-size and reliance-cap screens. The block PPI configuration is held at B=20, 4 labels per block, max/initial reliance 0.1, alpha 0.05, and a nominal 20% label-dollar budget. The eventwise frozen and updating proxy controls run on the same seed/scenario streams. These results do not calibrate false alarms or establish confirmatory power.",
        "",
        "|Horizon n|Scenario|Method|Streams|Harm reached|Detected|False escalations|RMSE|Mean true harm|Mean CS lower bound|Mean events|",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lower = "n/a" if pd.isna(row["mean_lower_bound"]) else f"{row['mean_lower_bound']:.3f}"
        lines.append(
            f"|{row['horizon_n']}|{row['scenario']}|{row['method']}|{row['streams']}|{row['harm_reached']}/{row['harmful_streams']}|{row['detections']}/{row['harmful_streams']}|{row['false_escalations']}/{row['streams']}|{row['stream_mean_rmse']:.4f}|{row['mean_expected_harm']:.4f}|{lower}|{row['mean_events']:.1f}|"
        )
    lines.extend(["", "![Horizon sensitivity](horizon_sensitivity.png)", ""])
    report = analysis / "horizon_analysis.md"
    report.write_text("\n".join(lines), encoding="utf-8")

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    inputs = [
        args.output_root / f"n_{n}" / "metrics" / "hard_budget_comparison.parquet" for n in HORIZONS
    ]
    outputs = [analysis / "horizon_summary.csv", figure, report]
    manifest = {
        "analysis": "pprm_horizon_sensitivity",
        "classification": "development_only_disjoint_seed_block",
        "seed_offset": 20372123,
        "horizons": list(HORIZONS),
        "fixed_block_size": 20,
        "fixed_labels_per_block": 4,
        "fixed_max_and_initial_reliance": 0.1,
        "sha256": {
            "source_files": {
                "scripts/analyze_pprm_horizon_sensitivity.py": sha256(Path(__file__)),
                "scripts/run_pprm_horizon_sensitivity.py": sha256(
                    Path(__file__).with_name("run_pprm_horizon_sensitivity.py")
                ),
            },
            "inputs": {path.as_posix(): sha256(path) for path in inputs},
            "artifacts": {path.name: sha256(path) for path in outputs},
        },
    }
    (analysis / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
