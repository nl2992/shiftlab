"""Independently verify hashes and matched-budget summaries for an ASI run."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(run_dir: Path, *, compare_run: Path | None = None) -> dict[str, object]:
    run_dir = run_dir.resolve()
    manifest_path = run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    detail_path = run_dir / "asi_paired_cost_streams.parquet"
    summary_path = run_dir / "asi_paired_cost_summary.csv"
    contrasts_path = run_dir / "asi_paired_contrasts.csv"
    report_path = run_dir / "results.md"
    protocol_path = run_dir / "protocol_snapshot.md"
    expected_hashes = {
        "metrics": (detail_path, manifest["metrics_sha256"]),
        "summary": (summary_path, manifest["summary_sha256"]),
        "paired contrasts": (contrasts_path, manifest["paired_contrasts_sha256"]),
        "report": (report_path, manifest["report_sha256"]),
        "protocol": (protocol_path, manifest["protocol_snapshot_sha256"]),
    }
    for name, (path, expected) in expected_hashes.items():
        if not path.is_file() or _sha256(path) != expected:
            raise ValueError(f"{name} artifact missing or hash mismatch")
    for relative, expected in manifest["source_sha256"].items():
        snapshot_path = run_dir / manifest["source_snapshot_directory"] / relative
        if _sha256(snapshot_path) != expected:
            raise ValueError(f"execution source snapshot mismatch: {relative}")
    if "verifier_sha256" in manifest and "verifier_snapshot_path" in manifest:
        verifier_snapshot = run_dir / manifest["verifier_snapshot_path"]
        if (
            verifier_snapshot.is_file()
            and _sha256(verifier_snapshot) != manifest["verifier_sha256"]
        ):
            raise ValueError("verifier source snapshot hash mismatch")
    verification_path = run_dir / "verification.json"
    if "verification_sha256" in manifest and (
        not verification_path.is_file()
        or manifest["verification_sha256"] != _sha256(verification_path)
    ):
        raise ValueError("verification record hash mismatch")

    detail = pd.read_parquet(detail_path)
    expected_methods = {
        "asi_residual_scale",
        "oracle_asi",
        "uniform_ppi_matched",
        "uniform_ppi_full_budget",
    }
    if len(detail) != manifest["seeds"]["count"] * len(expected_methods):
        raise ValueError("unexpected stream row count")
    if set(detail["method"]) != expected_methods:
        raise ValueError("unexpected method set")
    if detail.groupby(["seed", "method"]).size().ne(1).any():
        raise ValueError("duplicate or missing seed-method rows")
    wide_budget = detail.pivot(index="seed", columns="method", values="expected_labels")
    matched_difference = (
        wide_budget["asi_residual_scale"] - wide_budget["uniform_ppi_matched"]
    ).abs()
    if float(matched_difference.max()) > 1e-8:
        raise ValueError("primary ASI and uniform methods do not match expected labels")
    if not (wide_budget["uniform_ppi_full_budget"].sub(640.0).abs() < 1e-8).all():
        raise ValueError("full-budget uniform arm is not calibrated to 640 expected labels")

    recomputed = (
        detail.groupby("method")
        .agg(
            streams=("seed", "count"),
            mean_absolute_error=("error", lambda x: float(x.abs().mean())),
            rmse=("error", lambda x: float(math.sqrt((x**2).mean()))),
            mean_ci_width=("ci_width", "mean"),
            empirical_95_ci_coverage=("ci_covered", "mean"),
            mean_labels=("labels_queried", "mean"),
            mean_expected_labels=("expected_labels", "mean"),
            median_effective_sample_size=("propensity_ess", "median"),
        )
        .reset_index()
    )
    reported = pd.read_csv(summary_path).sort_values("method").reset_index(drop=True)
    recomputed = recomputed.sort_values("method").reset_index(drop=True)
    if list(reported["method"]) != list(recomputed["method"]):
        raise ValueError("summary method order/set mismatch")
    numeric_columns = [column for column in recomputed.columns if column != "method"]
    for column in numeric_columns:
        if not (reported[column] - recomputed[column]).abs().max() < 1e-10:
            raise ValueError(f"summary metric mismatch: {column}")
    contrasts = pd.read_csv(contrasts_path)
    if len(contrasts) != 8:
        raise ValueError("unexpected paired contrast count")
    for _, row in contrasts.iterrows():
        method = row["reference"]
        metric = row["metric"]
        if metric == "abs_error":
            treatment_values = (
                detail.loc[detail.method.eq("asi_residual_scale")].set_index("seed")["error"].abs()
            )
            reference_values = detail.loc[detail.method.eq(method)].set_index("seed")["error"].abs()
        elif metric == "mean_squared_error":
            treatment_values = (
                detail.loc[detail.method.eq("asi_residual_scale")].set_index("seed")["error"] ** 2
            )
            reference_values = detail.loc[detail.method.eq(method)].set_index("seed")["error"] ** 2
        else:
            treatment_values = detail.loc[detail.method.eq("asi_residual_scale")].set_index("seed")[
                metric
            ]
            reference_values = detail.loc[detail.method.eq(method)].set_index("seed")[metric]
        if metric == "ci_covered":
            treatment_values = treatment_values.astype(float)
            reference_values = reference_values.astype(float)
        expected_difference = float((treatment_values - reference_values).mean())
        if not math.isclose(
            expected_difference, float(row["mean_paired_difference"]), abs_tol=1e-10
        ):
            raise ValueError(f"paired contrast mismatch: {metric} vs {method}")

    reproducibility: dict[str, object] = {"compared": False}
    if compare_run is not None:
        comparison_path = compare_run.resolve() / "asi_paired_cost_streams.parquet"
        if not comparison_path.is_file():
            raise FileNotFoundError(comparison_path)
        comparison = pd.read_parquet(comparison_path)
        stable_columns = [
            "seed",
            "method",
            "true_target_gain",
            "estimate",
            "expected_labels",
            "labels_queried",
        ]
        current_values = (
            detail[stable_columns].sort_values(["seed", "method"]).reset_index(drop=True)
        )
        comparison_values = (
            comparison[stable_columns].sort_values(["seed", "method"]).reset_index(drop=True)
        )
        exact_match = current_values.equals(comparison_values)
        if not exact_match:
            raise ValueError("same-seed stream metrics differ from comparison run")
        reproducibility = {
            "compared": True,
            "run_directory": str(compare_run.resolve()),
            "exact_stream_metric_match": True,
            "comparison_rows": len(comparison_values),
        }

    return {
        "verified": True,
        "verified_utc": datetime.now(UTC).isoformat(),
        "stream_rows": len(detail),
        "seed_count": int(detail["seed"].nunique()),
        "methods": sorted(expected_methods),
        "maximum_primary_expected_budget_mismatch": float(matched_difference.max()),
        "mean_asi_expected_labels": float(wide_budget["asi_residual_scale"].mean()),
        "same_seed_reproducibility": reproducibility,
        "recomputed_summary": recomputed.to_dict(orient="records"),
        "checks": [
            "metrics, summary, report and protocol hashes match manifest",
            "execution-time runner and estimator source snapshots match manifest",
            "all seed-method rows are unique and complete",
            "ASI and primary uniform expected label totals match per seed",
            "full-budget uniform is calibrated to 640 expected labels per seed",
            "reported summary metrics reproduce from stream-level Parquet",
            "paired mean contrasts reproduce from stream-level Parquet",
            "same-seed stream metrics match the comparison run exactly when requested",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--compare-run", type=Path)
    args = parser.parse_args()
    result = verify(args.run_dir, compare_run=args.compare_run)
    path = args.run_dir / "verification.json"
    path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    verifier_snapshot = args.run_dir / "execution_sources" / "scripts" / "verify_asi_paired_cost.py"
    verifier_snapshot.parent.mkdir(parents=True, exist_ok=True)
    verifier_snapshot.write_bytes(Path(__file__).read_bytes())
    manifest_path = args.run_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["verifier_sha256"] = _sha256(verifier_snapshot)
    manifest["verifier_snapshot_path"] = str(verifier_snapshot.relative_to(args.run_dir))
    manifest["verification_sha256"] = _sha256(path)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"verified {result['stream_rows']} stream rows; wrote {path}")


if __name__ == "__main__":
    main()
