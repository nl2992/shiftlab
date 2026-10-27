"""Compute preregistered paired development contrasts from an integrated run."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "papers/shiftguard_unified/integrated_matched_development_protocol_v1.md"
COMPARISONS = (
    ("full_pipeline", "full_pipeline_fixed_certification"),
    ("full_pipeline", "two_gate"),
    ("full_pipeline_controller", "full_pipeline"),
    ("two_gate_controller", "two_gate"),
    ("full_pipeline", "q1_fallback"),
    ("fixed_candidate_certification", "scheduled_promote"),
)
METRICS = ("expected_incremental_utility", "realized_incremental_utility")
DRAWS = 10_000
BOOTSTRAP_SEED = 2026102701


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(*, input_dir: Path, output_dir: Path) -> Path:
    input_dir = input_dir.resolve()
    output_dir = output_dir.resolve()
    metrics_path = input_dir / "integrated_pipeline_seed_metrics.parquet"
    if not metrics_path.is_file():
        raise FileNotFoundError(metrics_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite nonempty output directory: {output_dir}")
    detail = pd.read_parquet(metrics_path)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows: list[dict[str, Any]] = []
    for scenario, group in detail.groupby("scenario", sort=True):
        wide = group.pivot(index="seed", columns="method", values=list(METRICS)).sort_index()
        for metric in METRICS:
            for treatment, reference in COMPARISONS:
                if (metric, treatment) not in wide or (metric, reference) not in wide:
                    raise ValueError(f"missing registered method pair {treatment}/{reference}")
                paired = (wide[(metric, treatment)] - wide[(metric, reference)]).to_numpy()
                sample_indices = rng.integers(0, len(paired), size=(DRAWS, len(paired)))
                boot = paired[sample_indices].mean(axis=1)
                rows.append(
                    {
                        "scenario": scenario,
                        "metric": metric,
                        "treatment": treatment,
                        "reference": reference,
                        "streams": len(paired),
                        "mean_paired_difference": float(paired.mean()),
                        "bootstrap_ci_level": 0.95,
                        "bootstrap_ci_low": float(np.quantile(boot, 0.025)),
                        "bootstrap_ci_high": float(np.quantile(boot, 0.975)),
                        "bootstrap_draws": DRAWS,
                        "bootstrap_seed": BOOTSTRAP_SEED,
                        "multiplicity_adjusted": False,
                        "status": "exploratory_development",
                    }
                )
    result = pd.DataFrame(rows)
    contrasts_path = output_dir / "additional_paired_contrasts.csv"
    result.to_csv(contrasts_path, index=False)
    manifest = {
        "analysis": "integrated_matched_development_additional_paired_contrasts_v1",
        "created_utc": datetime.now(UTC).isoformat(),
        "protocol": str(PROTOCOL.relative_to(ROOT)),
        "protocol_sha256": _sha256(PROTOCOL),
        "analysis_source": str(Path(__file__).relative_to(ROOT)),
        "analysis_source_sha256": _sha256(Path(__file__).resolve()),
        "input_metrics": str(metrics_path.relative_to(ROOT)),
        "input_metrics_sha256": _sha256(metrics_path),
        "contrasts_sha256": _sha256(contrasts_path),
        "comparisons": [list(pair) for pair in COMPARISONS],
        "metrics": list(METRICS),
        "bootstrap_draws": DRAWS,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "confidence_level": 0.95,
        "multiplicity_adjusted": False,
        "rows": len(result),
        "limitations": [
            "These are descriptive intervals from development streams, not confirmatory inference.",
            "The intervals are not multiplicity-adjusted and support no general superiority claim.",
        ],
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = analyze(input_dir=args.input, output_dir=args.output)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(result)


if __name__ == "__main__":
    main()
