"""Finalize registered PPRM confirmation report and plot from completed metrics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/pprm_predictive_risk_confirmation_v1"
PROTOCOL = ROOT / "papers/shiftguard_unified/pprm_predictive_risk_confirmation_protocol.md"
EXPECTED_CONFIG = {
    "seeds": 300,
    "seed_offset": 71_000_000,
    "device_resolved": "cuda",
    "rounds": 1200,
    "onset": 400,
    "predictive_tolerance": 0.05,
    "decision_margin": 0.05,
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_interval(events: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    lower = 0.0 if events == 0 else float(beta.ppf(alpha / 2, events, n - events + 1))
    upper = 1.0 if events == n else float(beta.ppf(1 - alpha / 2, events + 1, n - events))
    return lower, upper


def main() -> None:
    manifest_path = OUTPUT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest["config"]
    for key, expected in EXPECTED_CONFIG.items():
        if config.get(key) != expected:
            raise ValueError(f"Frozen confirmation mismatch for {key}: {config.get(key)!r}")

    summary = pd.read_csv(OUTPUT / "summary.csv")
    metrics = pd.read_csv(OUTPUT / "metrics.csv")
    if len(metrics) != 3600 or summary["streams"].ne(300).any():
        raise ValueError("Unexpected stream or summary row count")

    # The pre-run runner labels every non-30-seed invocation as a smoke. Restore
    # the actual registered protocol status and preserve the runner's hash.
    manifest["experiment"] = "pprm_predictive_risk_independent_confirmation"
    manifest["status"] = "frozen_independent_confirmation_300_seed"
    manifest["protocol"] = str(PROTOCOL.relative_to(ROOT))
    manifest["source_hashes"]["confirmation_protocol"] = sha256(PROTOCOL)
    manifest["limitations"] = [
        "Three hundred streams per cell confirm only this frozen synthetic operating point and do not prove type-I control or validity under other feedback/dependence processes.",
        "PPRM/SRM predictive-risk and DIVE paired-cost nulls differ; their alarm rates are not interchangeable.",
        "Synthetic decision costs are imposed and do not represent application revenue or observed operational utility.",
        "The experiment does not evaluate candidate promotion, adaptation, or delayed feedback.",
    ]

    intervals: list[dict[str, object]] = []
    for row in summary.to_dict(orient="records"):
        for metric_name in ("alarms", "post_onset_detections"):
            count = int(row[metric_name])
            n = int(row["streams"])
            low, high = exact_interval(count, n)
            intervals.append(
                {
                    "scenario": row["scenario"],
                    "method": row["method"],
                    "metric": metric_name,
                    "events": count,
                    "streams": n,
                    "rate": count / n,
                    "ci95_exact": [low, high],
                }
            )
    manifest["rate_confidence_intervals"] = intervals

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    time = range(config["rounds"])
    scenario_truth = summary.drop_duplicates("scenario").set_index("scenario")
    baseline_risk = float(scenario_truth.loc["stationary", "predictive_risk_truth"])
    for scenario in config["scenarios"]:
        post_risk = float(scenario_truth.loc[scenario, "predictive_risk_truth"])
        path = [baseline_risk if i < config["onset"] else post_risk for i in time]
        axes[0].plot(list(time), path, label=scenario)
    axes[0].axvline(config["onset"], color="black", linestyle="--", linewidth=1)
    axes[0].set(title="Evaluator-known 0–1 risk", xlabel="Round", ylabel="Expected risk")
    axes[0].legend(frameon=False, fontsize=8)

    pivot = summary.pivot(index="scenario", columns="method", values="alarm_rate")
    pivot.plot(kind="bar", ax=axes[1], width=0.78)
    axes[1].set(
        title="Independent confirmation alarm rates (300 seeds)",
        xlabel="Scenario",
        ylabel="Fraction of streams with an alarm",
        ylim=(0, 1),
    )
    axes[1].tick_params(axis="x", rotation=20)
    axes[1].legend(frameon=False, fontsize=8)
    fig.tight_layout()
    figure_path = OUTPUT / "pprm_predictive_risk_confirmation.png"
    fig.savefig(figure_path, dpi=180)
    plt.close(fig)
    (OUTPUT / "pprm_predictive_risk_development.png").unlink(missing_ok=True)

    results = summary.to_markdown(index=False)
    report = [
        "# PPRM predictive-risk independent confirmation",
        "",
        "**Status:** frozen 300-seed-per-cell independent synthetic confirmation; not proof of type-I control or general superiority.",
        "",
        "The seed block (offset 71,000,000) was disjoint from development. PPRM and SRM monitor running predictive risk; DIVE monitors paired decision cost. Their nulls differ, so alarm rates are not head-to-head comparisons.",
        "",
        results,
        "",
        "Exact two-sided 95% Clopper–Pearson intervals for alarm and post-onset detection proportions:",
        "",
        "| Scenario | Method | Outcome | Events / streams | Rate | Exact 95% interval |",
        "|---|---|---|---:|---:|---:|",
    ]
    for item in intervals:
        low, high = cast(list[float], item["ci95_exact"])
        report.append(
            f"| {item['scenario']} | {item['method']} | {item['metric']} | "
            f"{item['events']}/{item['streams']} | {item['rate']:.2%} | [{low:.2%}, {high:.2%}] |"
        )
    report.extend(
        [
            "",
            "The predictive-harm detections were 7/300 for PPRM (2.33%; exact 95% interval [0.94%, 4.75%]) and 19/300 for SRM (6.33%; [3.86%, 9.71%]); mean detected delays were 720.6 and 705.6 rounds. Both predictive-risk methods had 0/300 alarms in stationary and benign-nuisance controls (each exact 95% upper bound 1.22%). DIVE detected decision-cost-only harm in 70/300 streams (23.33%; [18.67%, 28.54%]). These are low detection rates under this fixed design, and differences do not establish a statistically significant method advantage.",
            "",
            "![PPRM independent confirmation](pprm_predictive_risk_confirmation.png)",
            "",
            "Protocol, source hashes, environment, per-seed metrics, Parquet files, and checksums are recorded alongside this report.",
        ]
    )
    report_path = OUTPUT / "results.md"
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")

    # Record the post-processor without replacing the hash of the runner that
    # generated the per-seed metrics.
    manifest["source_hashes"]["artifact_finalizer"] = sha256(Path(__file__).resolve())
    manifest["artifact_sha256"] = {}
    for name in (
        "metrics.csv",
        "metrics.parquet",
        "summary.csv",
        "summary.parquet",
        figure_path.name,
        "results.md",
    ):
        manifest["artifact_sha256"][name] = sha256(OUTPUT / name)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
