"""Reproduce pooled paired contrasts from the residual-variance start-prior grid."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

METHODS = ("fixed_mixture", "uniform_start_mixture", "late_start_mixture")
CONTRASTS = (
    ("uniform_start_mixture", "fixed_mixture"),
    ("late_start_mixture", "fixed_mixture"),
    ("uniform_start_mixture", "late_start_mixture"),
)


def analyze(
    metrics_path: str | Path,
    output_dir: str | Path,
    *,
    bootstrap_replicates: int = 10_000,
    bootstrap_seed: int = 31_202_026,
) -> tuple[pd.DataFrame, dict]:
    metrics_path = Path(metrics_path)
    metrics = pd.read_parquet(metrics_path)
    required = {"seed", "severity", "query_rate", "method", "detected"}
    if not required.issubset(metrics.columns):
        raise ValueError(
            f"metrics missing required columns: {sorted(required - set(metrics.columns))}"
        )
    if set(metrics.method.unique()) != set(METHODS):
        raise ValueError("metrics do not contain exactly the registered monitor methods")
    index = ["seed", "severity", "query_rate"]
    wide = metrics.pivot(index=index, columns="method", values="detected").astype(bool)
    if wide.isna().any().any():
        raise ValueError("paired grid has missing method outcomes")
    if (
        len(wide)
        != metrics.seed.nunique() * metrics.severity.nunique() * metrics.query_rate.nunique()
    ):
        raise ValueError("paired grid has duplicate or missing method outcomes")

    per_seed_rates = wide.groupby(level="seed").mean()
    rng = np.random.default_rng(bootstrap_seed)
    rows = []
    for first, second in CONTRASTS:
        differences = (per_seed_rates[first] - per_seed_rates[second]).to_numpy(dtype=float)
        sample = rng.integers(
            0,
            len(differences),
            size=(bootstrap_replicates, len(differences)),
        )
        interval = np.quantile(differences[sample].mean(axis=1), [0.025, 0.975])
        rows.append(
            {
                "first_method": first,
                "second_method": second,
                "first_macro_detection_rate": float(per_seed_rates[first].mean()),
                "second_macro_detection_rate": float(per_seed_rates[second].mean()),
                "paired_macro_difference": float(differences.mean()),
                "seed_cluster_ci95_low": float(interval[0]),
                "seed_cluster_ci95_high": float(interval[1]),
                "seed_clusters": len(differences),
                "cells_per_seed": len(wide) // len(differences),
                "bootstrap_replicates": bootstrap_replicates,
            }
        )
    contrasts = pd.DataFrame(rows)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    contrast_path = output / "macro_paired_contrasts.csv"
    contrasts.to_csv(contrast_path, index=False)
    audit = {
        "metric_rows": len(metrics),
        "unique_seeds": int(metrics.seed.nunique()),
        "severity_cells": int(metrics.severity.nunique()),
        "query_rate_cells": int(metrics.query_rate.nunique()),
        "material_harm_streams": int(metrics.material_harm.sum()),
        "harm_onsets_reached": int((metrics.harm_onset_relative < metrics.events_processed).sum()),
        "budget_violations": int((~metrics.budget_respected).sum()),
        "pre_onset_false_escalations": int(metrics.false_alarm.sum()),
    }
    audit_path = output / "analysis_audit.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    script = Path(__file__)
    analysis_manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_metrics": str(metrics_path),
        "input_metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
        "analysis_script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(),
        "contrasts_sha256": hashlib.sha256(contrast_path.read_bytes()).hexdigest(),
        "bootstrap_replicates": bootstrap_replicates,
        "bootstrap_seed": bootstrap_seed,
        "resampling_unit": "independent stream seed; all 12 severity/rate cells retained per sampled seed",
        "multiplicity": "descriptive intervals; no familywise adjustment",
    }
    (output / "analysis_manifest.json").write_text(
        json.dumps(analysis_manifest, indent=2), encoding="utf-8"
    )
    return contrasts, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--metrics", default="outputs/residual_variance_start_prior/metrics.parquet"
    )
    parser.add_argument("--output-dir", default="outputs/residual_variance_start_prior")
    parser.add_argument("--bootstrap-replicates", type=int, default=10_000)
    parser.add_argument("--bootstrap-seed", type=int, default=31_202_026)
    args = parser.parse_args()
    contrasts, audit = analyze(
        args.metrics,
        args.output_dir,
        bootstrap_replicates=args.bootstrap_replicates,
        bootstrap_seed=args.bootstrap_seed,
    )
    print(contrasts.to_string(index=False))
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
