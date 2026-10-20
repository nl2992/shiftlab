"""Replicate concept-mechanism residual, oracle and unchanged-feature-law checks."""

from pathlib import Path

import numpy as np

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import conditional_mean, conditional_scale, generate_chunks

SCENARIOS = [
    "concept",
    "sign_reversal",
    "nonlinear_response",
    "interaction",
    "latent_state",
    "conditional_variance",
    "boundary_local",
    "boundary_rotation",
]
SEEDS = [11, 23, 37, 53, 71]
SEVERITIES = [0.0, 0.5, 1.0, 2.0]
N = 20000


def evaluate() -> dict:
    evidence = []
    for scenario in SCENARIOS:
        for severity in SEVERITIES:
            per_regime = {"baseline": [], "shifted": []} if severity > 0 else {"baseline": []}
            feature_mean_errors, feature_covariance_errors = [], []
            mean_formula_errors, scale_formula_errors = [], []
            classification_z_scores = []
            for seed in SEEDS:
                config = SyntheticConfig(
                    n=N,
                    d=3,
                    seed=seed,
                    scenario=scenario,
                    severity=severity,
                    chunk_size=5000,
                )
                frames, oracles = [], []
                for frame, oracle in generate_chunks(config):
                    frames.append(frame)
                    oracles.append(oracle)
                features = np.concatenate([np.stack(frame.features.to_numpy()) for frame in frames])
                target = np.concatenate([frame.target.to_numpy() for frame in frames])
                weight = np.concatenate([oracle.weight.to_numpy() for oracle in oracles])
                mean = np.concatenate([oracle.conditional_mean.to_numpy() for oracle in oracles])
                sigma = np.concatenate([oracle.sigma.to_numpy() for oracle in oracles])
                q90 = np.concatenate([oracle.radius_90.to_numpy() for oracle in oracles])
                independent_mean = conditional_mean(config, features, weight)
                independent_sigma = conditional_scale(config, features, weight)
                mean_formula_errors.append(float(np.max(np.abs(independent_mean - mean))))
                scale_formula_errors.append(float(np.max(np.abs(independent_sigma - sigma))))
                if severity > 0:
                    x0, x1 = features[weight == 0], features[weight == 1]
                    feature_mean_errors.append(float(np.max(np.abs(x0.mean(0) - x1.mean(0)))))
                    feature_covariance_errors.append(
                        float(np.max(np.abs(np.cov(x0.T) - np.cov(x1.T))))
                    )
                for name, selected in [("baseline", weight == 0)]:
                    if severity == 0:
                        selected = np.ones(len(weight), dtype=bool)
                    residual = target[selected] - mean[selected]
                    scale = sigma[selected]
                    if scenario == "boundary_rotation":
                        probability = np.concatenate(
                            [oracle.probability_positive.to_numpy() for oracle in oracles]
                        )[selected]
                        standard_error = np.sqrt(
                            np.mean(probability * (1 - probability)) / selected.sum()
                        )
                        classification_z_scores.append(
                            abs(
                                float(target[selected].mean() - probability.mean()) / standard_error
                            )
                        )
                        per_regime[name].append({"classification": True})
                    else:
                        covered = np.abs(residual) <= q90[selected]
                        per_regime[name].append(
                            {
                                "residual": residual,
                                "sigma": scale,
                                "coverage": float(covered.mean()),
                            }
                        )
                if severity > 0:
                    selected = weight == 1
                    residual = target[selected] - mean[selected]
                    scale = sigma[selected]
                    if scenario == "boundary_rotation":
                        probability = np.concatenate(
                            [oracle.probability_positive.to_numpy() for oracle in oracles]
                        )[selected]
                        standard_error = np.sqrt(
                            np.mean(probability * (1 - probability)) / selected.sum()
                        )
                        classification_z_scores.append(
                            abs(
                                float(target[selected].mean() - probability.mean()) / standard_error
                            )
                        )
                        per_regime["shifted"].append({"classification": True})
                    else:
                        covered = np.abs(residual) <= q90[selected]
                        per_regime["shifted"].append(
                            {
                                "residual": residual,
                                "sigma": scale,
                                "coverage": float(covered.mean()),
                            }
                        )
            for regime, replicates in per_regime.items():
                row = {
                    "scenario": scenario,
                    "severity": severity,
                    "regime": regime,
                    "seeds": SEEDS,
                    "n_per_seed": N,
                    "max_conditional_mean_formula_error": max(mean_formula_errors),
                    "max_conditional_scale_formula_error": max(scale_formula_errors),
                }
                passed = max(mean_formula_errors) < 1e-10 and max(scale_formula_errors) < 1e-10
                if scenario == "boundary_rotation":
                    z = max(classification_z_scores)
                    row.update(
                        label_rate_max_standard_error_ratio=z,
                        label_rate_tolerance_standard_errors=4.0,
                    )
                    passed = passed and z < 4
                else:
                    residual = np.concatenate([item["residual"] for item in replicates])
                    scale = np.concatenate([item["sigma"] for item in replicates])
                    coverage = float(np.mean([item["coverage"] for item in replicates]))
                    standardized = residual / scale
                    variance_relative_error = abs(
                        float(np.mean(residual**2) / np.mean(scale**2)) - 1.0
                    )
                    row.update(
                        residual_mean=float(residual.mean()),
                        residual_mean_tolerance=0.01,
                        standardized_residual_variance=float(standardized.var(ddof=1)),
                        standardized_variance_tolerance=0.02,
                        raw_variance_relative_error=variance_relative_error,
                        raw_variance_relative_tolerance=0.025,
                        empirical_oracle_90_interval_coverage=coverage,
                        coverage_tolerance=0.015,
                    )
                    passed = passed and abs(float(residual.mean())) < 0.01
                    passed = passed and abs(float(standardized.var(ddof=1)) - 1) < 0.02
                    passed = passed and variance_relative_error < 0.025
                    passed = passed and abs(coverage - 0.9) < 0.015
                if severity > 0:
                    mean_error = float(np.mean(feature_mean_errors))
                    covariance_error = float(np.mean(feature_covariance_errors))
                    row.update(
                        feature_mean_difference_max_over_replicates=mean_error,
                        feature_mean_tolerance=0.06,
                        feature_covariance_difference_max_over_replicates=covariance_error,
                        feature_covariance_tolerance=0.08,
                    )
                    passed = passed and mean_error < 0.06 and covariance_error < 0.08
                row["passes"] = bool(passed)
                evidence.append(row)
    return {
        "description": "Five-seed concept mechanism checks across four severities, including independent conditional formulas and residual-law coverage.",
        "scenarios": SCENARIOS,
        "seeds": SEEDS,
        "severities": SEVERITIES,
        "evidence": evidence,
        "interpretation": "Monte Carlo residual checks validate the declared synthetic laws only; they do not establish empirical conditional coverage or a real-world drift classification.",
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
    }


def main() -> None:
    report = evaluate()
    output = Path("data/reports/concept_residual_validation.json")
    write_json(output, report)
    failures = [row for row in report["evidence"] if not row["passes"]]
    print(f"records={len(report['evidence'])} failures={len(failures)}")
    print(output)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
