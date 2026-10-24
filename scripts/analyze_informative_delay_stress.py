"""Reproducible paired analysis for the informative-delay development screen."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

PROFILES = ("fixed", "positive_fast", "positive_slow")
HARM_SCENARIOS = tuple(f"high_cost_local_harm_d{dose:.2f}" for dose in (0.04, 0.20, 0.40, 0.60))
NULL_SCENARIOS = ("mixed_sign_exact_marginal_null", "strict_negative_control")
ROOT = Path("outputs")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paired_bootstrap(
    frame: pd.DataFrame,
    *,
    profile_a: str,
    profile_b: str,
    bound_mode: str,
    metric: str,
    rng: np.random.Generator,
    replicates: int = 20_000,
) -> tuple[float, float, float]:
    by_profile = {
        profile: frame[
            (frame["delay_profile"] == profile)
            & (frame["bound_mode"] == bound_mode)
            & frame["scenario"].isin(HARM_SCENARIOS)
        ]
        for profile in (profile_a, profile_b)
    }
    arrays = {}
    for profile, subset in by_profile.items():
        pivot = subset.pivot(index="scenario", columns="stream_id", values=metric)
        pivot = pivot.loc[list(HARM_SCENARIOS)].sort_index(axis=1)
        arrays[profile] = pivot.to_numpy(dtype=np.float64)
    if arrays[profile_a].shape != arrays[profile_b].shape or arrays[profile_a].shape != (4, 30):
        raise ValueError("paired profile cells must contain 30 matched streams for four harm doses")
    differences = arrays[profile_a] - arrays[profile_b]
    observed = float(differences.mean())
    # Resample independently within each registered harm-dose stratum while
    # retaining profile pairing for each underlying stream.
    indices = rng.integers(0, differences.shape[1], size=(replicates, 4, 30))
    sampled = np.take_along_axis(differences[None, :, :], indices, axis=2).mean(axis=(1, 2))
    lower, upper = np.quantile(sampled, [0.025, 0.975])
    return observed, float(lower), float(upper)


def analyze(output: Path) -> Path:
    frames = []
    source_manifests = {}
    for profile in PROFILES:
        folder = ROOT / f"informative_delay_{profile}_30"
        manifest_path = folder / "reports/manifest.json"
        metrics_path = folder / "metrics/stream_metrics.parquet"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["configuration"]["delay_profile"] != profile:
            raise ValueError(f"manifest profile mismatch: {manifest_path}")
        if manifest["configuration"]["seed_root"] != 27804027:
            raise ValueError(f"unexpected seed root: {manifest_path}")
        frame = pd.read_parquet(metrics_path)
        if len(frame) != 360 or frame["delay_profile"].ne(profile).any():
            raise ValueError(f"incomplete or mislabeled metrics: {metrics_path}")
        if not frame["budget_respected"].all():
            raise ValueError(f"a hard label cap was violated: {metrics_path}")
        frames.append(frame)
        source_manifests[profile] = {
            "manifest": str(manifest_path),
            "manifest_sha256": sha256(manifest_path),
            "metrics": str(metrics_path),
            "metrics_sha256": sha256(metrics_path),
            "source_git_commit": manifest["git_commit"],
        }
    all_metrics = pd.concat(frames, ignore_index=True)
    keys = ["delay_profile", "scenario", "bound_mode", "stream_id"]
    if all_metrics.duplicated(keys).any() or len(all_metrics) != 1080:
        raise ValueError("combined stream records are incomplete or duplicated")

    output.mkdir(parents=True, exist_ok=False)
    (output / "metrics").mkdir()
    (output / "reports").mkdir()
    combined_path = output / "metrics/stream_metrics.parquet"
    all_metrics.to_parquet(combined_path, index=False)
    summary = (
        all_metrics.groupby(["delay_profile", "scenario", "bound_mode"], sort=True)
        .agg(
            streams=("stream_id", "size"),
            false_escalations=("false_escalation", "sum"),
            detections=("post_onset_detection", "sum"),
            detection_rate=("post_onset_detection", "mean"),
            onset_reach_rate=("onset_reached", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_events_processed=("events_processed", "mean"),
            detected_mean_event_delay=("detection_delay_event_time", "mean"),
            detected_mean_wall_delay=("detection_delay_wall_time", "mean"),
            mean_feedback_delay=("mean_feedback_delay", "mean"),
            mean_positive_contrast_delay=("mean_positive_contrast_delay", "mean"),
            mean_negative_contrast_delay=("mean_negative_contrast_delay", "mean"),
            mean_exposed_harm=("evaluator_cumulative_expected_harm_cost", "mean"),
        )
        .reset_index()
    )
    summary_path = output / "metrics/summary.csv"
    summary.to_csv(summary_path, index=False)

    rng = np.random.default_rng(27804119)
    contrast_rows = []
    harmful = all_metrics[all_metrics["scenario"].isin(HARM_SCENARIOS)]
    for bound_mode in ("fixed", "predictable"):
        for profile_a, profile_b in (
            ("positive_fast", "fixed"),
            ("positive_slow", "fixed"),
            ("positive_slow", "positive_fast"),
        ):
            for metric in (
                "post_onset_detection",
                "labels_queried",
                "evaluator_cumulative_expected_harm_cost",
            ):
                estimate, low, high = _paired_bootstrap(
                    harmful,
                    profile_a=profile_a,
                    profile_b=profile_b,
                    bound_mode=bound_mode,
                    metric=metric,
                    rng=rng,
                )
                contrast_rows.append(
                    {
                        "bound_mode": bound_mode,
                        "profile_a": profile_a,
                        "profile_b": profile_b,
                        "metric": metric,
                        "difference_a_minus_b": estimate,
                        "paired_seed_stratified_bootstrap_95_low": low,
                        "paired_seed_stratified_bootstrap_95_high": high,
                        "replicates": 20_000,
                        "seed_root": 27804119,
                    }
                )
    contrast_path = output / "metrics/paired_profile_contrasts.csv"
    pd.DataFrame(contrast_rows).to_csv(contrast_path, index=False)

    report_path = output / "reports/informative_delay_stress_results.md"
    report = [
        "# Informative-delay stress screen: results",
        "",
        "**Status:** 30-seed development screen only. The null counts below are not an estimate or certification of a 5% false-alarm rate. No method novelty or general power claim is made.",
        "",
        "All 1,080 stream records are complete, uniquely keyed, and within the hard query cap. Stream data were generated on CUDA; sequential replay used NumPy on CPU. Each delay profile used the same seed root, and each scenario reused query and outcome uniforms across profiles and bound modes.",
        "",
        "## Harm detection",
        "",
        "The fixed-global-bound arm detected 0/120 harmful streams in each delay profile. The predictable eventwise-bound arm detected 3/120 under fixed 12-event delay, 6/120 when positive cost contrasts arrived after one event, and 7/120 when positive contrasts arrived after 12 events. All harmful onsets were reached. Detections were sparse and concentrated in the strongest dose, so these counts are exploratory.",
        "",
        "## Full cell summaries",
        "",
        summary.to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Paired comparisons",
        "",
        "Profile contrasts use a stratified seed bootstrap: 20,000 replicates, resampling 30 paired seeds independently within each of the four harm-dose scenarios. Positive values mean profile A exceeds profile B. These exploratory intervals are not multiplicity-adjusted and do not upgrade this screen to confirmation.",
        "",
        pd.DataFrame(contrast_rows).to_markdown(index=False, floatfmt=".4f"),
        "",
        "## Null diagnostics and limitations",
        "",
    ]
    nulls = summary[summary["scenario"].isin(NULL_SCENARIOS)]
    report.append(nulls.to_markdown(index=False, floatfmt=".4f"))
    report.extend(
        [
            "",
            "The exact-marginal-null control had 0/30 alarms in every cell. The strict-negative control had one pre-onset alarm in the predictable-bound fixed-delay cell and none elsewhere. These small counts are diagnostics only. The event-prefix argument requires the stated conditional-mean null and predictable support bound given the full history used by querying. This experiment studies latency and power under iid event generation; it does not validate Markov dependence, adaptive policies, missing labels, or using latency as evidence.",
            "",
            "No figure was generated; the project requires PaperBanana for visuals, and no visual is needed for this report.",
            "",
            "See [the frozen protocol](../../../docs/informative_delay_stress_protocol.md), [event-prefix validity note](../../../docs/delayed_event_prefix_validity.md), and each profile's source manifest under `outputs/informative_delay_*_30/reports/manifest.json`.",
        ]
    )
    report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    manifest_path = output / "reports/manifest.json"
    manifest = {
        "experiment": "informative_delay_stress_analysis",
        "created_utc": datetime.now(UTC).isoformat(),
        "git_commit": __import__("subprocess")
        .run(["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
        .stdout.strip(),
        "sources": source_manifests,
        "configuration": {
            "seed_root": 27804027,
            "streams_per_scenario": 30,
            "horizon": 2400,
            "harm_scenarios": HARM_SCENARIOS,
            "null_scenarios": NULL_SCENARIOS,
            "profiles": PROFILES,
            "arms": ("fixed", "predictable"),
            "bootstrap_replicates": 20_000,
            "bootstrap_seed": 27804119,
        },
        "rows": len(all_metrics),
        "sha256": {
            "analysis_script": sha256(Path(__file__)),
            "protocol": sha256(Path("docs/informative_delay_stress_protocol.md")),
            "metrics/stream_metrics.parquet": sha256(combined_path),
            "metrics/summary.csv": sha256(summary_path),
            "metrics/paired_profile_contrasts.csv": sha256(contrast_path),
            "reports/informative_delay_stress_results.md": sha256(report_path),
        },
        "artifacts": {
            "metrics/stream_metrics.parquet": str(combined_path),
            "metrics/summary.csv": str(summary_path),
            "metrics/paired_profile_contrasts.csv": str(contrast_path),
            "reports/informative_delay_stress_results.md": str(report_path),
        },
        "limitations": [
            "development screen only; no null calibration or confirmation",
            "iid event generation, frozen policy pair, complete queried labels",
            "outcome-dependent delays assigned by the evaluator; latency not a model feature",
            "findings limited to registered synthetic DGP and seed block",
            "no visuals generated; PaperBanana required for future visuals",
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return report_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / "informative_delay_stress_grid_30_final"
    )
    args = parser.parse_args()
    result = analyze(args.output)
    print(result)
