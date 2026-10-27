"""Verify and analyze a frozen integrated synthetic efficacy confirmation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/integrated_efficacy_confirmation_protocol_v1.md"
PROFILES = (
    "stationary",
    "benign_nuisance",
    "boundary_local_harm",
    "post_promotion_reversal",
    "recurring_regimes",
    "residual_variance",
    "harmful_adaptation_at_monitor",
    "harmful_adaptation_native",
)
METHODS = (
    "continue",
    "scheduled_promote",
    "two_gate",
    "two_gate_controller",
    "q1_fallback",
    "full_pipeline",
    "full_pipeline_controller",
    "fixed_candidate_certification",
    "full_pipeline_fixed_certification",
)
PRIMARY_COMPARISONS = tuple(
    [("full_pipeline", "continue", profile) for profile in PROFILES[2:]]
    + [("full_pipeline", "two_gate", profile) for profile in PROFILES]
    + [("full_pipeline", "full_pipeline_fixed_certification", profile) for profile in PROFILES]
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _holm(p_values: np.ndarray) -> np.ndarray:
    order = np.argsort(p_values)
    adjusted = np.empty_like(p_values, dtype=np.float64)
    running = 0.0
    count = len(p_values)
    for rank, index in enumerate(order):
        running = max(running, (count - rank) * float(p_values[index]))
        adjusted[index] = min(1.0, running)
    return adjusted


def analyze(run_dir: Path, analysis_dir: Path) -> Path:
    run_dir = run_dir.resolve()
    analysis_dir = analysis_dir.resolve()
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "independent_efficacy_confirmation":
        raise ValueError("run manifest is not marked as independent efficacy confirmation")
    if manifest.get("seeds") != {"offset": 2026104000, "count_per_scenario": 100}:
        raise ValueError("seed block differs from the frozen confirmation protocol")
    if manifest.get("scenarios") != list(PROFILES) or manifest.get("methods") != list(METHODS):
        raise ValueError("scenario or method family differs from the frozen protocol")
    protocol_snapshot = run_dir / "protocol_snapshot.md"
    if protocol_snapshot.read_bytes() != PROTOCOL.read_bytes():
        raise ValueError("protocol snapshot does not match the frozen protocol")
    if manifest.get("protocol_snapshot_sha256") != sha256(protocol_snapshot):
        raise ValueError("protocol snapshot hash mismatch")

    metrics_path = run_dir / "integrated_pipeline_seed_metrics.parquet"
    summary_path = run_dir / "integrated_pipeline_summary.csv"
    contrasts_path = run_dir / "integrated_pipeline_paired_contrasts.csv"
    learner_path = run_dir / "learner_event_log.parquet"
    evaluator_path = run_dir / "evaluator_event_log.parquet"
    detail = pd.read_parquet(metrics_path)
    expected_rows = len(PROFILES) * len(METHODS) * 100
    if len(detail) != expected_rows:
        raise ValueError(f"expected {expected_rows} seed metrics, got {len(detail)}")
    if detail.duplicated(["scenario", "method", "seed"]).any():
        raise ValueError("duplicate scenario-method-seed metric key")
    if set(detail["scenario"]) != set(PROFILES) or set(detail["method"]) != set(METHODS):
        raise ValueError("metric rows have missing or unexpected scenarios/methods")
    counts = detail.groupby(["scenario", "method"], observed=True).size()
    if not (counts == 100).all() or len(counts) != 72:
        raise ValueError("one or more profile-method cells are incomplete")
    expected_seeds = set(range(2026104000, 2026104100))
    for profile, profile_rows in detail.groupby("scenario", observed=True):
        if set(profile_rows["seed"].unique()) != expected_seeds:
            raise ValueError(f"seed block differs from protocol in {profile}")
    if detail["total_labels"].max() > 640 or (detail["total_labels"] < 0).any():
        raise ValueError("pathwise label cap violation or invalid count")
    if not np.isfinite(
        detail[["expected_incremental_utility", "realized_incremental_utility"]].to_numpy(
            dtype=float
        )
    ).all():
        raise ValueError("non-finite utility endpoint")

    expected_event_rows = expected_rows * 3200
    learner_pf = pq.ParquetFile(learner_path)
    evaluator_pf = pq.ParquetFile(evaluator_path)
    for name, parquet_file, metadata in (
        ("learner", learner_pf, manifest["learner_event_log"]),
        ("evaluator", evaluator_pf, manifest["evaluator_event_log"]),
    ):
        if parquet_file.metadata.num_rows != expected_event_rows:
            raise ValueError(f"{name} event log has an unexpected row count")
        if metadata.get("rows") != expected_event_rows:
            raise ValueError(f"{name} event row count differs from manifest")
    learner_columns = set(learner_pf.schema_arrow.names)
    evaluator_columns = set(evaluator_pf.schema_arrow.names)
    forbidden_learner = {
        "true_label",
        "true_positive_probability",
        "incumbent_cost",
        "reference_cost",
        "deployed_cost",
        "realized_incumbent_minus_deployed_gain",
        "expected_incumbent_minus_deployed_gain",
    }
    if learner_columns & forbidden_learner:
        raise ValueError("evaluator-only values appear in the learner event schema")
    if "true_label" not in evaluator_columns or "observed_label" not in learner_columns:
        raise ValueError("learner/evaluator event schemas are incomplete")

    # Validate source snapshots and all outputs covered by the run manifest.
    for rel_path, expected_hash in manifest["source_sha256"].items():
        source_snapshot = run_dir / "execution_sources" / Path(rel_path)
        if sha256(source_snapshot) != expected_hash:
            raise ValueError(f"source snapshot hash mismatch: {rel_path}")
    if sha256(metrics_path) != manifest["metrics_sha256"]:
        raise ValueError("seed-metrics hash mismatch")
    if sha256(summary_path) != manifest["summary_sha256"]:
        raise ValueError("summary hash mismatch")
    if sha256(contrasts_path) != manifest["paired_contrasts_sha256"]:
        raise ValueError("paired-contrast hash mismatch")
    for path, key in (
        (learner_path, "learner_event_log"),
        (evaluator_path, "evaluator_event_log"),
    ):
        if sha256(path) != manifest[key]["sha256"]:
            raise ValueError(f"{key} hash mismatch")

    # Check that the retained aggregate CSV is exactly derived from seed rows.
    summary = pd.read_csv(summary_path)
    recomputed = detail.groupby(["scenario", "method"], as_index=False).agg(
        streams=("seed", "count"),
        monitor_trigger_rate=("monitor_triggered", "mean"),
        promotion_rate=("candidate_promoted", "mean"),
        rollback_rate=("rollback_event", lambda x: x.notna().mean()),
        mean_labels=("total_labels", "mean"),
        mean_expected_gain=("expected_incremental_utility", "mean"),
        mean_realized_gain=("realized_incremental_utility", "mean"),
    )
    summary = summary.sort_values(["scenario", "method"]).reset_index(drop=True)
    recomputed = recomputed.sort_values(["scenario", "method"]).reset_index(drop=True)
    if list(summary.columns) != list(recomputed.columns):
        raise ValueError("saved summary has unexpected columns")
    for col in summary.columns:
        if pd.api.types.is_numeric_dtype(summary[col]):
            if not np.allclose(summary[col], recomputed[col], rtol=0, atol=1e-10):
                raise ValueError(f"saved summary differs from seed metrics in {col}")
        elif not summary[col].equals(recomputed[col]):
            raise ValueError(f"saved summary differs from seed metrics in {col}")

    wide = detail.pivot(
        index=["scenario", "seed"], columns="method", values="expected_incremental_utility"
    )
    p_values: list[float] = []
    primary_rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(2026104101)
    bootstrap_draws = 20_000
    for treatment, reference, profile in PRIMARY_COMPARISONS:
        paired = (wide.loc[profile, treatment] - wide.loc[profile, reference]).to_numpy(
            dtype=np.float64
        )
        test = stats.ttest_1samp(paired, popmean=0.0, alternative="greater")
        p_values.append(float(test.pvalue))
        sample_index = rng.integers(0, len(paired), size=(bootstrap_draws, len(paired)))
        bootstrap = paired[sample_index].mean(axis=1)
        primary_rows.append(
            {
                "profile": profile,
                "treatment": treatment,
                "reference": reference,
                "streams": len(paired),
                "mean_paired_expected_utility_difference": float(paired.mean()),
                "paired_sd": float(paired.std(ddof=1)),
                "one_sided_p_raw": float(test.pvalue),
                "bootstrap_ci_low_95_descriptive": float(np.quantile(bootstrap, 0.025)),
                "bootstrap_ci_high_95_descriptive": float(np.quantile(bootstrap, 0.975)),
                "bootstrap_draws": bootstrap_draws,
                "bootstrap_seed": 2026104101,
            }
        )
    p_array = np.asarray(p_values, dtype=np.float64)
    adjusted = _holm(p_array)
    simultaneous_critical = float(stats.t.ppf(1 - 0.05 / len(p_array), df=99))
    for row, p_adj in zip(primary_rows, adjusted, strict=True):
        row["holm_adjusted_p"] = float(p_adj)
        row["holm_reject_at_0_05"] = bool(p_adj < 0.05)
        row["bonferroni_simultaneous_lower_95"] = float(
            row["mean_paired_expected_utility_difference"]
            - simultaneous_critical * row["paired_sd"] / np.sqrt(100)
        )

    analysis_dir.mkdir(parents=True, exist_ok=False)
    primary_path = analysis_dir / "primary_contrasts.csv"
    pd.DataFrame(primary_rows).to_csv(primary_path, index=False)
    report_path = analysis_dir / "confirmation_report.md"
    text = [
        "# Integrated Q1–Q3 efficacy confirmation results",
        "",
        "**Status:** independently seeded synthetic confirmation; no real-data transfer or novelty claim.",
        "",
        f"The run contains {len(detail):,} seed-method rows across eight profiles and nine methods. Each of the two event logs contains {expected_event_rows:,} rows. The maximum label use was {int(detail['total_labels'].max())}/640. The independent checks confirmed all 72 profile-method cells, learner/evaluator schema separation, and exact aggregate summaries.",
        "",
        "Primary endpoint: evaluator-expected cumulative paired-cost reduction net of declared intervention charges. The 22 one-sided stream-level paired t tests target positive mean differences; Holm correction controls the family at 0.05. Simultaneous lower bounds use Bonferroni alpha/22. Bootstrap intervals are descriptive.",
        "",
        "| Profile | Treatment | Comparator | Mean paired gain | Holm p | Simultaneous lower 95% |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in primary_rows:
        text.append(
            f"| {row['profile']} | {row['treatment']} | {row['reference']} | "
            f"{row['mean_paired_expected_utility_difference']:.4f} | "
            f"{row['holm_adjusted_p']:.4g} | "
            f"{row['bonferroni_simultaneous_lower_95']:.4f} |"
        )
    controls = summary[summary["scenario"].isin(["stationary", "benign_nuisance"])]
    text.extend(
        [
            "",
            "## Control behavior",
            "",
            "| Profile | Method | Promotion rate | Rollback rate | Mean expected utility | Mean labels |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in controls.to_dict(orient="records"):
        text.append(
            f"| {row['scenario']} | {row['method']} | {row['promotion_rate']:.3f} | "
            f"{row['rollback_rate']:.3f} | {row['mean_expected_gain']:.4f} | {row['mean_labels']:.1f} |"
        )
    text.extend(
        [
            "",
            "## Full profile-by-method summary",
            "",
            "All nine arms are shown. The full machine-readable table is `integrated_pipeline_summary.csv` in the run directory.",
            "",
            "| Profile | Method | Expected utility | Realized utility | Promote | Rollback | Mean labels |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in summary.to_dict(orient="records"):
        text.append(
            f"| {row['scenario']} | {row['method']} | {row['mean_expected_gain']:.4f} | "
            f"{row['mean_realized_gain']:.4f} | {row['promotion_rate']:.3f} | "
            f"{row['rollback_rate']:.3f} | {row['mean_labels']:.1f} |"
        )
    text.extend(
        [
            "",
            "Empirical results are conditional on the registered synthetic stream family and its immediate, non-performative feedback. The null calibration is separate. No inference is made about dependent or delayed real deployments.",
            "",
        ]
    )
    report_path.write_text("\n".join(text), encoding="utf-8")

    paths = [
        manifest_path,
        protocol_snapshot,
        metrics_path,
        summary_path,
        contrasts_path,
        learner_path,
        evaluator_path,
    ]
    artifact_hashes = {str(p.relative_to(ROOT)): sha256(p) for p in paths}
    verification = {
        "status": "passed",
        "protocol_sha256": sha256(PROTOCOL),
        "analysis_source": str(Path(__file__).relative_to(ROOT)),
        "analysis_source_sha256": sha256(Path(__file__).resolve()),
        "run_manifest_sha256": sha256(manifest_path),
        "metric_rows": len(detail),
        "profile_method_cells": len(counts),
        "learner_event_rows": learner_pf.metadata.num_rows,
        "evaluator_event_rows": evaluator_pf.metadata.num_rows,
        "max_label_use": int(detail["total_labels"].max()),
        "primary_contrasts": len(primary_rows),
        "source_sha256_verified": manifest["source_sha256"],
        "artifact_sha256": artifact_hashes,
        "analysis_outputs_sha256": {
            str(p.relative_to(ROOT)): sha256(p) for p in (primary_path, report_path)
        },
        "limits": [
            "All inference is over independent synthetic stream seeds within the frozen DGP family.",
            "No real-data confirmation or novelty claim is established.",
        ],
    }
    verification_path = analysis_dir / "verification.json"
    verification_path.write_text(json.dumps(verification, indent=2) + "\n", encoding="utf-8")
    return verification_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "outputs/shiftguard_unified/integrated_confirmation/efficacy_100_v1",
    )
    parser.add_argument("--analysis-dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    analysis_dir = args.analysis_dir or (run_dir / "analysis_v1")
    result = analyze(run_dir, analysis_dir)
    print(f"verified confirmation and wrote {result.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
