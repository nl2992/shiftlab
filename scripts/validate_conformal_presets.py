"""Execute oracle-residual split-conformal diagnostics for named stress presets."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from shiftlab.data.synthetic import conformal_stress_catalogue, generate_chunks
from shiftlab.methods import weighted_conformal_quantile


def evaluate(root: Path, seeds: tuple[int, ...] = (42, 43, 44, 45, 46)) -> dict:
    rows: list[dict] = []
    regimes: list[dict] = []
    for preset in conformal_stress_catalogue(n=12000):
        for seed in seeds:
            config = preset.config.model_copy(update={"seed": seed})
            generated = list(generate_chunks(config))
            frame = pd.concat([item[0] for item in generated], ignore_index=True)
            oracle = pd.concat([item[1] for item in generated], ignore_index=True)
            target = frame.target.to_numpy()
            residual = target - oracle.conditional_mean.to_numpy()
            history_residual = target - oracle.conditional_mean_given_history.to_numpy()
            calibration_start = float(frame.loc[frame.split == "test", "prediction_time"].min())
            calibration = (
                (frame.split == "calibration").to_numpy()
                & frame.label_available_time.notna().to_numpy()
                & (frame.label_available_time.to_numpy() < calibration_start)
                & np.isfinite(residual)
            )
            test = (frame.split == "test").to_numpy() & np.isfinite(residual)
            if calibration.sum() < 20 or test.sum() < 20:
                raise ValueError(f"Insufficient usable calibration/test labels for {preset.name}")
            marginal_radius = weighted_conformal_quantile(np.abs(residual[calibration]), alpha=0.1)
            history_marginal_radius = weighted_conformal_quantile(
                np.abs(history_residual[calibration]), alpha=0.1
            )
            oracle_radius = oracle.radius_90.to_numpy()
            history_radius = oracle.conditional_radius_90.to_numpy()
            pointwise = test & np.isfinite(oracle_radius)
            history_pointwise = test & np.isfinite(history_radius)
            marginal_covered = np.abs(residual[test]) <= marginal_radius
            oracle_covered = np.abs(residual[pointwise]) <= oracle_radius[pointwise]
            history_marginal_covered = np.abs(history_residual[test]) <= history_marginal_radius
            history_oracle_covered = (
                np.abs(history_residual[history_pointwise]) <= history_radius[history_pointwise]
            )
            rows.append(
                {
                    "preset": preset.name,
                    "seed": seed,
                    "scenario": config.scenario,
                    "pattern": config.pattern,
                    "calibration_target_scope": preset.calibration_target_scope,
                    "oracle_radius_scope": preset.oracle_radius_scope,
                    "residual_law": preset.residual_law,
                    "calibration_n": int(calibration.sum()),
                    "test_n": int(test.sum()),
                    "marginal_calibration_radius": marginal_radius,
                    "test_marginal_coverage": float(marginal_covered.mean()),
                    "test_oracle_radius_coverage": float(oracle_covered.mean()),
                    "history_marginal_calibration_radius": history_marginal_radius,
                    "test_history_marginal_coverage": float(history_marginal_covered.mean()),
                    "test_history_conditional_radius_coverage": float(
                        history_oracle_covered.mean()
                    ),
                    "oracle_radius_n": int(pointwise.sum()),
                    "history_oracle_radius_n": int(history_pointwise.sum()),
                    "uncertainty": "descriptive replicate range; no confidence interval or IID claim",
                    "predictor": "known evaluator conditional mean; history-conditional mean used for history metrics",
                }
            )
            regime_ids = oracle.regime_id.astype(str).to_numpy()
            for regime in sorted(set(regime_ids[test])):
                group = test & (regime_ids == regime)
                group_pointwise = group & np.isfinite(oracle_radius)
                regimes.append(
                    {
                        "preset": preset.name,
                        "seed": seed,
                        "oracle_regime": regime,
                        "n": int(group.sum()),
                        "test_marginal_coverage": float(
                            (np.abs(residual[group]) <= marginal_radius).mean()
                        ),
                        "test_history_marginal_coverage": float(
                            (np.abs(history_residual[group]) <= history_marginal_radius).mean()
                        ),
                        "test_oracle_radius_coverage": float(
                            (
                                np.abs(residual[group_pointwise]) <= oracle_radius[group_pointwise]
                            ).mean()
                        ),
                        "test_history_conditional_radius_coverage": float(
                            (
                                np.abs(history_residual[group_pointwise])
                                <= history_radius[group_pointwise]
                            ).mean()
                        ),
                    }
                )
    input_spec = json.dumps(
        {"seeds": seeds, "cases": len(conformal_stress_catalogue()), "n_per_case": 12000},
        sort_keys=True,
    )
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
    ).stdout.strip()
    return {
        "protocol": "Marginal and history-conditional calibration quantiles use only finite labels available before the test boundary. Both use known evaluator means to isolate residual-quantile behavior rather than fitted-model error.",
        "targets": "Each case reports marginal and history-conditional split calibration and oracle-radius coverage, with evaluator-regime breakdowns.",
        "limitations": "Five independently seeded streams are descriptive; no confidence interval, online validity, fitted-predictor guarantee, or IID claim is made. Temporal cases need dependence-aware inference.",
        "input_sha256": hashlib.sha256(input_spec.encode()).hexdigest(),
        "script_sha256": script_hash,
        "processing_commit": commit,
        "replicates": rows,
        "by_oracle_regime": regimes,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    result = evaluate(root)
    output = root / "data/reports/conformal_stress_validation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    for preset in sorted({row["preset"] for row in result["replicates"]}):
        rows = [row for row in result["replicates"] if row["preset"] == preset]
        print(
            preset,
            f"marginal={np.mean([row['test_marginal_coverage'] for row in rows]):.3f}",
            f"oracle={np.mean([row['test_oracle_radius_coverage'] for row in rows]):.3f}",
            f"history_oracle={np.mean([row['test_history_conditional_radius_coverage'] for row in rows]):.3f}",
        )


if __name__ == "__main__":
    main()
