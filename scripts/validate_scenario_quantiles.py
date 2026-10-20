"""Validate exact oracle radii and replicated residual coverage for every scenario."""

from pathlib import Path

import numpy as np
from scipy.stats import norm
from scipy.stats import t as student_t

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import SCENARIOS, generate_chunks

SEEDS = [101, 202, 303]
N = 12000
SEVERITY = 2.0
Z90 = norm.ppf(0.95)


def _absolute_cdf(kind, radius, scale, severity, weight):
    standardized = radius / scale
    if kind in {"normal", "marginal_normal_dependent"}:
        return 2 * norm.cdf(standardized) - 1
    if kind == "student_t5":
        return 2 * student_t.cdf(standardized * np.sqrt(5 / 3), df=5) - 1
    if kind == "centered_lognormal":
        center = np.exp(0.5)
        standardizer = np.sqrt((np.e - 1) * np.e)
        upper = np.log(center + standardizer * standardized)
        lower_argument = center - standardizer * standardized
        lower = np.where(lower_argument > 0, np.log(np.maximum(lower_argument, 1e-300)), -np.inf)
        return norm.cdf(upper) - norm.cdf(lower)
    if kind == "normal_mixture":
        rate = 0.01 + 0.1 * np.tanh(severity) * weight
        return (1 - rate) * (2 * norm.cdf(standardized) - 1) + rate * (
            2 * norm.cdf(standardized / 8) - 1
        )
    raise ValueError(f"Unvalidated residual law: {kind}")


def evaluate() -> dict:
    evidence = []
    for scenario in SCENARIOS:
        replicate_coverages = []
        exact_cdf_errors = []
        quantile_kinds = set()
        regression_rows = 0
        for seed in SEEDS:
            coverage_count = covered_count = 0
            config = SyntheticConfig(
                n=N,
                scenario=scenario,
                seed=seed,
                severity=SEVERITY,
                chunk_size=4000,
            )
            for frame, oracle in generate_chunks(config):
                kind = str(oracle.quantile_kind.iloc[0])
                quantile_kinds.add(kind)
                radius = oracle.radius_90.to_numpy(dtype=float)
                scale = oracle.sigma.to_numpy(dtype=float)
                valid = np.isfinite(radius)
                if not valid.any():
                    continue
                weight = oracle.weight.to_numpy(dtype=float)[valid]
                mass = _absolute_cdf(kind, radius[valid], scale[valid], SEVERITY, weight)
                exact_cdf_errors.append(float(np.max(np.abs(mass - 0.9))))
                conditional_radius = oracle.conditional_radius_90.to_numpy(dtype=float)
                conditional_mean = oracle.conditional_mean_given_history.to_numpy(dtype=float)
                target = frame.target.to_numpy(dtype=float)
                covered = (
                    np.abs(target[valid] - conditional_mean[valid]) <= conditional_radius[valid]
                )
                covered_count += int(covered.sum())
                coverage_count += int(valid.sum())
            if coverage_count:
                replicate_coverages.append(covered_count / coverage_count)
                regression_rows += coverage_count

        if regression_rows:
            pooled_coverage = float(
                np.average(replicate_coverages, weights=[N] * len(replicate_coverages))
            )
            max_seed_error = max(abs(value - 0.9) for value in replicate_coverages)
            max_exact_error = max(exact_cdf_errors)
            passed = (
                max_exact_error < 1e-8
                and max_seed_error < 0.025
                and abs(pooled_coverage - 0.9) < 0.015
            )
            evidence.append(
                {
                    "scenario": scenario,
                    "status": "validated_regression_quantile",
                    "quantile_kinds": sorted(quantile_kinds),
                    "severity": SEVERITY,
                    "seeds": SEEDS,
                    "n_per_seed": N,
                    "regression_rows": regression_rows,
                    "max_exact_cdf_error": max_exact_error,
                    "coverage_by_seed": replicate_coverages,
                    "pooled_empirical_coverage": pooled_coverage,
                    "max_seed_coverage_error": max_seed_error,
                    "passes": bool(passed),
                }
            )
        else:
            evidence.append(
                {
                    "scenario": scenario,
                    "status": "classification_without_residual_quantile",
                    "quantile_kinds": sorted(quantile_kinds),
                    "severity": SEVERITY,
                    "seeds": SEEDS,
                    "n_per_seed": N,
                    "regression_rows": 0,
                    "max_exact_cdf_error": None,
                    "coverage_by_seed": [],
                    "pooled_empirical_coverage": None,
                    "max_seed_coverage_error": None,
                    "passes": True,
                }
            )
    return {
        "description": "Independent exact CDF-mass calculations and three-seed Monte Carlo coverage for every registered synthetic scenario at severity 2. Exact CDF checks cover each finite oracle-radius row, including marginal dependent-error radii; empirical coverage uses the declared history-conditional mean and radius.",
        "scenarios": list(SCENARIOS),
        "seeds": SEEDS,
        "n_per_seed": N,
        "severity": SEVERITY,
        "evidence": evidence,
        "interpretation": "This validates the simulator's declared oracle residual laws. Monte Carlo coverage is descriptive and does not imply fitted-model or real-world coverage guarantees.",
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
    }


def main() -> None:
    report = evaluate()
    output = Path("data/reports/scenario_quantile_validation.json")
    write_json(output, report)
    failures = [row for row in report["evidence"] if not row["passes"]]
    print(f"records={len(report['evidence'])} failures={len(failures)}")
    print(output)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
