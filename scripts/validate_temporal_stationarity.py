"""Replicate stationary variance and dependence checks for temporal DGPs."""

import json
from pathlib import Path

import numpy as np

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now
from shiftlab.data.schemas import SyntheticConfig
from shiftlab.data.synthetic import generate_chunks


def main() -> None:
    rho, theta, noise = 0.65, 0.3, 0.3
    seeds = [11, 23, 37, 53, 71]
    expected = {
        "ar1": 1.0,
        "arma": (1 + theta**2 + 2 * rho * theta) / (1 - rho**2),
        "garch": 0.05 / (1 - 0.1 - 0.8),
    }
    rows = []
    for scenario, expected_variance in expected.items():
        for seed in seeds:
            config = SyntheticConfig(n=30000, scenario=scenario, rho=rho, noise=noise, seed=seed)
            frame, oracle = next(generate_chunks(config))
            raw_error = frame.target.to_numpy() - oracle.conditional_mean.to_numpy()
            values = (
                np.stack(frame.features.to_numpy())[:, 0]
                if scenario in {"ar1", "arma"}
                else raw_error / noise
            )[1000:]
            squared = values**2
            rows.append(
                {
                    "scenario": scenario,
                    "seed": seed,
                    "sample_variance": float(np.var(values, ddof=1)),
                    "expected_stationary_variance": expected_variance,
                    "lag1_autocorrelation": float(np.corrcoef(values[:-1], values[1:])[0, 1]),
                    "squared_lag1_autocorrelation": float(
                        np.corrcoef(squared[:-1], squared[1:])[0, 1]
                    ),
                }
            )
    summaries = {}
    expected_lag1 = {
        "ar1": rho,
        "arma": (rho + theta) * (1 + rho * theta) / (1 + theta**2 + 2 * rho * theta),
        "garch": 0.0,
    }
    for scenario, variance in expected.items():
        group = [row for row in rows if row["scenario"] == scenario]
        observed_variance = float(np.mean([r["sample_variance"] for r in group]))
        observed_lag1 = float(np.mean([r["lag1_autocorrelation"] for r in group]))
        observed_squared_lag1 = float(np.mean([r["squared_lag1_autocorrelation"] for r in group]))
        summaries[scenario] = {
            "replicates": len(group),
            "expected_stationary_variance": variance,
            "mean_sample_variance": observed_variance,
            "variance_relative_tolerance": 0.035,
            "variance_check_pass": bool(abs(observed_variance - variance) < 0.035 * variance),
            "expected_lag1_autocorrelation": expected_lag1[scenario],
            "mean_lag1_autocorrelation": observed_lag1,
            "lag1_absolute_tolerance": 0.025,
            "lag1_check_pass": bool(abs(observed_lag1 - expected_lag1[scenario]) < 0.025),
            "mean_squared_lag1_autocorrelation": observed_squared_lag1,
            "garch_squared_lag1_minimum": 0.05 if scenario == "garch" else None,
            "squared_lag1_check_pass": bool(
                observed_squared_lag1 > 0.05 if scenario == "garch" else True
            ),
        }
    report = {
        "description": "Descriptive five-seed checks after 1,000 observations are discarded.",
        "parameters": {"rho": rho, "arma_theta": theta, "noise": noise, "n": 30000},
        "replicates": rows,
        "summary": summaries,
        "checks_pass": all(
            row["variance_check_pass"] and row["lag1_check_pass"] and row["squared_lag1_check_pass"]
            for row in summaries.values()
        ),
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
        "limitations": [
            "Replicate ranges are descriptive checks, not confidence intervals.",
            "GARCH residuals are standardized by configured noise for the variance check.",
        ],
    }
    output = Path("data/reports/temporal_stationarity_validation.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for scenario, summary in summaries.items():
        print(
            f"{scenario}: variance={summary['mean_sample_variance']:.4f} "
            f"(expected {summary['expected_stationary_variance']:.4f}), "
            f"lag1={summary['mean_lag1_autocorrelation']:.4f}, "
            f"squared_lag1={summary['mean_squared_lag1_autocorrelation']:.4f}"
        )
    print(output)
    if not report["checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
