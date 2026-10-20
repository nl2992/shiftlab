"""Replicate analytic distribution checks for stationary IID control generators."""

import json
from itertools import pairwise
from pathlib import Path

import numpy as np
from scipy.special import expit

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks

SCENARIOS = ("iid_regression", "nonlinear_classification", "heteroskedastic", "heavy_tailed")
SEEDS = (11, 23, 37, 53, 71)


def _collect(scenario: str, seed: int, n: int) -> tuple[np.ndarray, ...]:
    features, targets, means, scales, radii, probabilities, weights = [], [], [], [], [], [], []
    config = SyntheticConfig(
        n=n,
        d=4,
        scenario=scenario,
        severity=0.0,
        noise=0.3,
        seed=seed,
        chunk_size=5000,
    )
    for frame, oracle in generate_chunks(config):
        features.append(np.stack(frame.features.to_numpy()))
        targets.append(frame.target.to_numpy())
        means.append(oracle.conditional_mean.to_numpy())
        scales.append(oracle.sigma.to_numpy())
        radii.append(oracle.radius_90.to_numpy())
        probabilities.append(oracle.probability_positive.to_numpy())
        weights.append(oracle.weight.to_numpy())
    return tuple(
        np.concatenate(values)
        for values in (features, targets, means, scales, radii, probabilities, weights)
    )


def validate_stationary_controls(*, seeds: tuple[int, ...] = SEEDS, n: int = 30000) -> dict:
    records: list[dict] = []
    for scenario in SCENARIOS:
        for seed in seeds:
            features, targets, mean, scale, radius, probability, weight = _collect(
                scenario, seed, n
            )
            residual = targets - mean
            standardized = residual / scale
            record: dict[str, float | int | str | bool] = {
                "scenario": scenario,
                "seed": seed,
                "n": n,
                "maximum_absolute_regime_weight": float(np.max(np.abs(weight))),
            }
            if scenario != "nonlinear_classification":
                record.update(
                    standardized_residual_mean=float(np.mean(standardized)),
                    standardized_residual_variance=float(np.var(standardized, ddof=1)),
                    central_oracle_90_coverage=float(np.mean(np.abs(residual) <= radius)),
                )
            if scenario in {"iid_regression", "nonlinear_classification", "heteroskedastic"}:
                record["feature_mean_max_abs"] = float(np.max(np.abs(features.mean(axis=0))))
                record["feature_variance_max_abs_error"] = float(
                    np.max(np.abs(features.var(axis=0, ddof=1) - 1))
                )
                corr = np.corrcoef(features, rowvar=False) - np.eye(features.shape[1])
                record["feature_correlation_max_abs"] = float(np.max(np.abs(corr)))
            if scenario == "nonlinear_classification":
                formula = expit(features[:, 0] + features[:, 1] ** 2 - 1)
                record["probability_formula_max_abs_error"] = float(
                    np.max(np.abs(probability - formula))
                )
                record["bernoulli_score_z"] = float(
                    np.abs(targets.sum() - formula.sum()) / np.sqrt(np.sum(formula * (1 - formula)))
                )
            if scenario == "heteroskedastic":
                formula_scale = 0.3 * (1 + 0.5 * np.abs(features[:, 0]))
                record["conditional_scale_formula_max_abs_error"] = float(
                    np.max(np.abs(scale - formula_scale))
                )
                bins = np.quantile(np.abs(features[:, 0]), np.linspace(0, 1, 11))
                edges = np.unique(bins)
                calibration_errors = []
                for bin_index, (lower, upper) in enumerate(pairwise(edges)):
                    absolute_feature = np.abs(features[:, 0])
                    upper_bound = (
                        absolute_feature <= upper
                        if bin_index == len(edges) - 2
                        else absolute_feature < upper
                    )
                    selected = (absolute_feature >= lower) & upper_bound
                    if selected.sum() > 100:
                        calibration_errors.append(abs(np.mean(standardized[selected] ** 2) - 1))
                record["conditional_variance_decile_max_abs_error"] = float(max(calibration_errors))
            records.append(record)

    summaries = {}
    for scenario in SCENARIOS:
        group = [record for record in records if record["scenario"] == scenario]
        checks: dict[str, bool] = {
            "zero_severity_null_pass": all(
                record["maximum_absolute_regime_weight"] == 0 for record in group
            ),
        }
        if scenario != "nonlinear_classification":
            mean_residual = float(
                np.mean([record["standardized_residual_mean"] for record in group])
            )
            variance = float(
                np.mean([record["standardized_residual_variance"] for record in group])
            )
            coverage = float(np.mean([record["central_oracle_90_coverage"] for record in group]))
            checks.update(
                standardized_residual_mean_pass=abs(mean_residual) < 0.012,
                standardized_residual_variance_pass=abs(variance - 1)
                < (0.04 if scenario == "heavy_tailed" else 0.02),
                central_oracle_90_coverage_pass=abs(coverage - 0.9) < 0.006,
            )
        else:
            mean_residual = variance = coverage = None
        if scenario in {"iid_regression", "nonlinear_classification", "heteroskedastic"}:
            checks["feature_marginal_pass"] = (
                max(record["feature_mean_max_abs"] for record in group) < 0.025
                and max(record["feature_variance_max_abs_error"] for record in group) < 0.035
                and max(record["feature_correlation_max_abs"] for record in group) < 0.025
            )
        if scenario == "nonlinear_classification":
            checks["conditional_probability_pass"] = (
                max(record["probability_formula_max_abs_error"] for record in group) < 1e-12
                and max(record["bernoulli_score_z"] for record in group) < 5
            )
        if scenario == "heteroskedastic":
            checks["conditional_scale_pass"] = (
                max(record["conditional_scale_formula_max_abs_error"] for record in group) < 1e-12
                and max(record["conditional_variance_decile_max_abs_error"] for record in group)
                < 0.08
            )
        summaries[scenario] = {
            "replicates": len(group),
            "mean_standardized_residual_mean": mean_residual,
            "mean_standardized_residual_variance": variance,
            "mean_central_oracle_90_coverage": coverage,
            "checks": checks,
            "conditional_variance_decile_absolute_tolerance": 0.08
            if scenario == "heteroskedastic"
            else None,
            "passed": all(checks.values()),
        }

    return {
        "description": "Five-seed stationary-null checks against independently specified feature, Bernoulli, conditional-scale and residual-law formulas.",
        "configuration": {"n_per_seed": n, "d": 4, "noise": 0.3, "severity": 0.0},
        "scenarios": list(SCENARIOS),
        "replicates": records,
        "summary": summaries,
        "checks_pass": all(summary["passed"] for summary in summaries.values()),
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
        "limitations": [
            "Replicate ranges are descriptive validation gates, not confidence intervals or power guarantees.",
            "These checks cover the named stationary controls only; they do not replace mechanism-specific validation of all synthetic scenarios.",
            "The heteroskedastic conditional-variance decile check uses an 8% finite-sample tolerance per seed.",
        ],
    }


def main() -> None:
    report = validate_stationary_controls()
    output = Path("data/reports/stationary_control_validation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    for scenario, summary in report["summary"].items():
        if scenario == "nonlinear_classification":
            print(
                f"{scenario}: max Bernoulli score z="
                f"{max(row['bernoulli_score_z'] for row in report['replicates'] if row['scenario'] == scenario):.3f}, "
                f"passed={summary['passed']}"
            )
        else:
            print(
                f"{scenario}: standardized variance="
                f"{summary['mean_standardized_residual_variance']:.4f}, "
                f"90% coverage={summary['mean_central_oracle_90_coverage']:.4f}, "
                f"passed={summary['passed']}"
            )
    print(output)
    if not report["checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
