"""Execute independent checks of target-shift generator mechanisms."""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks


def _generate(scenario: str, seed: int, n: int = 30000, severity: float = 1.0):
    config = SyntheticConfig(n=n, scenario=scenario, seed=seed, severity=severity, noise=0.3)
    parts = list(generate_chunks(config))
    frame = pd.concat([part[0] for part in parts], ignore_index=True)
    oracle = pd.concat([part[1] for part in parts], ignore_index=True)
    return config, frame, oracle


def evaluate() -> dict:
    rows = []
    for scenario in ["prior_shift", "imbalance"]:
        for severity in [0.0, 0.5, 1.0, 2.0]:
            observed_priors, expected_priors, class_means = [], [], []
            base_logit = np.log(0.1 / 0.9) if scenario == "imbalance" else 0.0
            for seed in [11, 23, 37, 53, 71]:
                config, frame, oracle = _generate(scenario, seed, severity=severity)
                X = np.stack(frame.features.to_numpy())
                weight = oracle.weight.to_numpy()
                selected = weight == (0 if severity == 0 else 1)
                y = frame.target.to_numpy()
                expected = float(expit(base_logit + config.severity))
                observed_priors.append(float(y[selected].mean()))
                expected_priors.append(expected)
                class_means.append(
                    {
                        "negative_mean_x0": float(X[selected & (y == 0), 0].mean()),
                        "positive_mean_x0": float(X[selected & (y == 1), 0].mean()),
                    }
                )
            observed = float(np.mean(observed_priors))
            expected = float(np.mean(expected_priors))
            class_summary = {
                key: float(np.mean([record[key] for record in class_means]))
                for key in class_means[0]
            }
            class_mean_error = max(
                abs(class_summary["negative_mean_x0"] + 1),
                abs(class_summary["positive_mean_x0"] - 1),
            )
            rows.append(
                {
                    "scenario": scenario,
                    "severity": severity,
                    "n_per_seed": 30000,
                    "property": "class prior and P(X0|Y) means",
                    "observed_prior_mean_over_seeds": observed,
                    "expected_prior": expected,
                    "prior_absolute_error": abs(observed - expected),
                    "prior_tolerance": 0.015,
                    "mean_class_conditional_x0_over_seeds": class_summary,
                    "expected_class_conditional_x0": {"negative": -1.0, "positive": 1.0},
                    "class_conditional_mean_max_error": class_mean_error,
                    "class_conditional_mean_tolerance": 0.05,
                    "passes": abs(observed - expected) < 0.015 and class_mean_error < 0.05,
                }
            )

    for severity in [0.0, 0.5, 1.0, 2.0]:
        corruption_errors = []
        label_rate_errors = []
        for seed in [11, 23, 37, 53, 71]:
            config, frame, oracle = _generate("label_corruption", seed, n=50000, severity=severity)
            X = np.stack(frame.features.to_numpy())
            w = oracle.weight.to_numpy()
            rate = np.minimum(0.45, config.severity * w / 5)
            clean = expit(X[:, 0] + X[:, 1] ** 2 - 1)
            expected_p = rate + (1 - 2 * rate) * clean
            observed_p = oracle.probability_positive.to_numpy()
            corruption_errors.append(float(np.max(np.abs(observed_p - expected_p))))
            for regime in [0] if severity == 0 else [0, 1]:
                selected = w == regime
                standard_error = np.sqrt(
                    np.mean(expected_p[selected] * (1 - expected_p[selected])) / selected.sum()
                )
                label_rate_errors.append(
                    abs(
                        float(frame.target.to_numpy()[selected].mean())
                        - expected_p[selected].mean()
                    )
                    / standard_error
                )
        rows.append(
            {
                "scenario": "label_corruption",
                "severity": severity,
                "n_per_seed": 50000,
                "property": "symmetric label-flip posterior and empirical label rate",
                "max_absolute_probability_formula_error": max(corruption_errors),
                "max_empirical_label_rate_standard_error_ratio": max(label_rate_errors),
                "empirical_label_rate_tolerance_standard_errors": 4,
                "formula_tolerance": 1e-12,
                "passes": bool(max(corruption_errors) < 1e-12 and max(label_rate_errors) < 4),
            }
        )

    for scenario in ["target_level", "target_variance", "tail_frequency"]:
        for severity in [0.0, 0.5, 1.0, 2.0]:
            regime_values = {"baseline": []}
            if severity > 0:
                regime_values["shifted"] = []
            for seed in [11, 23, 37, 53, 71]:
                config, frame, oracle = _generate(scenario, seed, severity=severity)
                X = np.stack(frame.features.to_numpy())
                y = frame.target.to_numpy()
                weight = oracle.weight.to_numpy()
                s = config.severity * weight
                residual = y - (X[:, 0] - 0.9 * X[:, 1])
                regimes = [("baseline", weight == 0)]
                if severity > 0:
                    regimes.append(("shifted", weight == 1))
                for name, condition in regimes:
                    regime_values[name].append(
                        {
                            "mean": float(residual[condition].mean()),
                            "variance": float(residual[condition].var(ddof=1)),
                            "expected_mean": float(s[condition][0])
                            if scenario == "target_level"
                            else 0.0,
                            "expected_variance": (
                                config.noise**2 * (1 + s[condition][0]) ** 2
                                if scenario == "target_variance"
                                else config.noise**2
                                * (
                                    1
                                    + 63
                                    * (
                                        0.01
                                        + 0.1
                                        * np.tanh(config.severity)
                                        * float(weight[condition][0])
                                    )
                                )
                                if scenario == "tail_frequency"
                                else config.noise**2
                            ),
                        }
                    )
            aggregate = {}
            for regime, samples in regime_values.items():
                observed_mean = float(np.mean([item["mean"] for item in samples]))
                observed_variance = float(np.mean([item["variance"] for item in samples]))
                expected_mean = float(np.mean([item["expected_mean"] for item in samples]))
                expected_variance = float(np.mean([item["expected_variance"] for item in samples]))
                aggregate[regime] = {
                    "observed_mean": observed_mean,
                    "expected_mean": expected_mean,
                    "mean_absolute_error": abs(observed_mean - expected_mean),
                    "observed_variance": observed_variance,
                    "expected_variance": expected_variance,
                    "variance_relative_error": abs(observed_variance - expected_variance)
                    / expected_variance,
                }
            tolerance = 0.06 if scenario == "tail_frequency" else 0.025
            rows.append(
                {
                    "scenario": scenario,
                    "severity": severity,
                    "n_per_seed": 30000,
                    "property": "conditional residual mean/variance by regime",
                    "regimes": aggregate,
                    "replicates": 5,
                    "mean_absolute_error_tolerance": 0.02,
                    "variance_relative_error_tolerance": tolerance,
                    "passes": all(
                        item["mean_absolute_error"] < 0.02
                        and item["variance_relative_error"] < tolerance
                        for item in aggregate.values()
                    ),
                }
            )
    return {
        "description": "Five-seed independent mechanism checks for class-prior, label-corruption, and regression target shifts across severity 0, 0.5, 1 and 2.",
        "n_per_seed": 30000,
        "seeds": [11, 23, 37, 53, 71],
        "evidence": rows,
        "interpretation": "Replicate means are descriptive. The formulas are derived from the documented DGP and do not establish real-world shift classifications.",
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
    }


def main() -> None:
    report = evaluate()
    output = Path("data/reports/target_shift_validation.json")
    write_json(output, report)
    for row in report["evidence"]:
        print(row["scenario"], row["property"])
    failures = [row for row in report["evidence"] if not row["passes"]]
    print(f"records={len(report['evidence'])} failures={len(failures)}")
    print(output)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
