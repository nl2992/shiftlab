"""Analyze the development sensitivity to the PPI maximum reliance bound."""

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

RELIANCE_CAPS = (0.1, 0.25, 0.5, 1.0)
METHODS = ("pprm_block_adaptive", "uniform_proxy_frozen", "uniform_proxy")


def _load(root: Path) -> pd.DataFrame:
    frames = []
    for cap in RELIANCE_CAPS:
        folder = f"eta_{cap:.2f}".replace(".", "p")
        path = root / folder / "metrics" / "hard_budget_comparison.parquet"
        if not path.is_file():
            raise FileNotFoundError(f"missing completed reliance-cap run: {path}")
        frame = pd.read_parquet(path)
        if set(frame.method) != set(METHODS):
            raise ValueError(f"unexpected methods in {path}: {sorted(frame.method.unique())}")
        pprm_cap = frame.loc[frame.method.eq("pprm_block_adaptive"), "pprm_max_reliance"]
        if not pprm_cap.eq(cap).all():
            raise ValueError(f"reliance-cap metadata mismatch in {path}")
        frame["reliance_cap"] = cap
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    return (
        metrics.groupby(["reliance_cap", "scenario", "method"], dropna=False)
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
            mean_reliance=("pprm_reliance_mean", "mean"),
            mean_lower_bound=("pprm_confidence_lower_bound", "mean"),
        )
        .reset_index()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root", type=Path, default=Path("outputs/pprm_reliance_bound_development_v1")
    )
    args = parser.parse_args()
    metrics = _load(args.output_root)
    summary = _summarize(metrics)
    analysis = args.output_root / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    summary.to_csv(analysis / "reliance_bound_summary.csv", index=False)

    scenarios = sorted(summary.scenario.unique())
    fig, axes = plt.subplots(2, len(scenarios), figsize=(4 * len(scenarios), 8), squeeze=False)
    for column, scenario in enumerate(scenarios):
        subset = summary.loc[summary.scenario.eq(scenario)]
        for method in METHODS:
            values = subset.loc[subset.method.eq(method)].sort_values("reliance_cap")
            label = {
                "pprm_block_adaptive": "Block PPI",
                "uniform_proxy_frozen": "Eventwise, frozen proxy",
                "uniform_proxy": "Eventwise, updating proxy",
            }[method]
            axes[0, column].plot(
                values.reliance_cap, values.stream_mean_rmse, marker="o", label=label
            )
            rate = values.detections / values.harmful_streams.replace(0, np.nan)
            axes[1, column].plot(values.reliance_cap, rate, marker="o", label=label)
        axes[0, column].set_title(scenario)
        axes[0, column].set_xscale("log", base=2)
        axes[0, column].set_xticks(RELIANCE_CAPS, labels=[str(x) for x in RELIANCE_CAPS])
        axes[1, column].set_xscale("log", base=2)
        axes[1, column].set_xticks(RELIANCE_CAPS, labels=[str(x) for x in RELIANCE_CAPS])
        axes[1, column].set_ylim(0, 1)
        axes[0, column].grid(alpha=0.2)
        axes[1, column].grid(alpha=0.2)
    axes[0, 0].set_ylabel("RMSE of stream-mean cost estimate")
    axes[1, 0].set_ylabel("Detection rate in harmful scenarios")
    axes[0, -1].legend(fontsize=7, loc="best")
    fig.suptitle("PPI reliance-bound sensitivity; development seeds only")
    fig.tight_layout()
    figure = analysis / "reliance_bound_sensitivity.png"
    fig.savefig(figure, dpi=180)
    plt.close(fig)

    readme = [
        "# PPI reliance-bound sensitivity",
        "",
        "Development-only sensitivity on the same 30 seeds used for block-size development. Block size is 20 with 4 labels per block; scenarios, budget, alpha, predictor, and eventwise controls are held fixed. The reliance cap and initial reliance are both set to each listed value. These repeated seeds support debugging and comparison only; they are not an independent confirmation set.",
        "",
        "|Cap|Scenario|Method|Streams|Harm reached|Detected|False escalations|RMSE|Mean true harm|Mean CS lower bound|Mean eta|",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        eta = "n/a" if pd.isna(row["mean_reliance"]) else f"{row['mean_reliance']:.3f}"
        lower = "n/a" if pd.isna(row["mean_lower_bound"]) else f"{row['mean_lower_bound']:.3f}"
        readme.append(
            f"|{row['reliance_cap']:.2f}|{row['scenario']}|{row['method']}|{row['streams']}|{row['harm_reached']}/{row['harmful_streams']}|{row['detections']}/{row['harmful_streams']}|{row['false_escalations']}/{row['streams']}|{row['stream_mean_rmse']:.4f}|{row['mean_expected_harm']:.4f}|{lower}|{eta}|"
        )
    readme.extend(["", "![Reliance-cap sensitivity](reliance_bound_sensitivity.png)", ""])
    report = analysis / "reliance_bound_analysis.md"
    report.write_text("\n".join(readme), encoding="utf-8")

    def sha256(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    inputs = [
        args.output_root
        / f"eta_{cap:.2f}".replace(".", "p")
        / "metrics"
        / "hard_budget_comparison.parquet"
        for cap in RELIANCE_CAPS
    ]
    outputs = [analysis / "reliance_bound_summary.csv", figure, report]
    manifest = {
        "analysis": "pprm_reliance_bound_sensitivity",
        "classification": "development_only_reused_seed_block",
        "reliance_caps": list(RELIANCE_CAPS),
        "fixed_block_size": 20,
        "fixed_labels_per_block": 4,
        "sha256": {
            "source_files": {
                "scripts/analyze_pprm_reliance_bound_sensitivity.py": sha256(Path(__file__)),
                "scripts/run_pprm_reliance_bound_sensitivity.py": sha256(
                    Path(__file__).with_name("run_pprm_reliance_bound_sensitivity.py")
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
