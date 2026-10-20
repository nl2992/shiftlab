"""Replicate analytic stability and innovation checks for the performative process."""

from pathlib import Path

import numpy as np
from scipy.stats import norm

from shiftlab.data.provenance import commit, sha256, source_hash, utc_now, write_json
from shiftlab.data.synthetic.performative import PerformativeEnvironment

SEEDS = [11, 23, 37, 53, 71]
N = 20000
BURN_IN = 1000
RHO = 0.4
STRENGTH = 0.2
NOISE = 0.1
ACTIONS = np.array([0.3, 0.1, 0.5])


def evaluate() -> dict:
    rows = []
    action_mean = float(ACTIONS.mean())
    expected_state_mean = STRENGTH * action_mean / (1 - RHO)
    expected_state_variance = NOISE**2 / (1 - RHO**2)
    for seed in SEEDS:
        env = PerformativeEnvironment(
            seed=seed, rho=RHO, strength=STRENGTH, noise=NOISE, action_bound=1.0
        )
        states, target_residuals, state_innovations = [], [], []
        for _ in range(N):
            old_state = env.state
            new_state, target = env.step(ACTIONS)
            influence = STRENGTH * action_mean
            target_residuals.append(target - old_state - influence)
            state_innovations.append(new_state - RHO * old_state - influence)
            states.append(new_state)
        states = np.asarray(states[BURN_IN:])
        target_residuals = np.asarray(target_residuals[BURN_IN:])
        state_innovations = np.asarray(state_innovations[BURN_IN:])
        coverage = float(np.mean(np.abs(target_residuals) <= norm.ppf(0.95) * NOISE))
        rows.append(
            {
                "seed": seed,
                "sample_state_mean": float(states.mean()),
                "expected_stationary_state_mean": expected_state_mean,
                "sample_state_variance": float(states.var(ddof=1)),
                "expected_stationary_state_variance": expected_state_variance,
                "target_innovation_mean": float(target_residuals.mean()),
                "target_innovation_variance": float(target_residuals.var(ddof=1)),
                "state_innovation_mean": float(state_innovations.mean()),
                "state_innovation_variance": float(state_innovations.var(ddof=1)),
                "target_innovation_90pct_coverage": coverage,
                "target_state_innovation_correlation": float(
                    np.corrcoef(target_residuals, state_innovations)[0, 1]
                ),
            }
        )
    n_eval = N - BURN_IN
    mean_tolerance = 4 * NOISE / np.sqrt(n_eval)
    coverage_tolerance = 4 * np.sqrt(0.9 * 0.1 / n_eval)
    variance_relative_tolerance = 0.045
    state_variance_relative_tolerance = 0.07
    correlation_tolerance = 4 / np.sqrt(n_eval)
    for row in rows:
        row["passes"] = bool(
            abs(row["sample_state_mean"] - expected_state_mean)
            < 4 * np.sqrt(expected_state_variance / n_eval) * np.sqrt((1 + RHO) / (1 - RHO))
            and abs(row["sample_state_variance"] - expected_state_variance)
            < state_variance_relative_tolerance * expected_state_variance
            and abs(row["target_innovation_mean"]) < mean_tolerance
            and abs(row["state_innovation_mean"]) < mean_tolerance
            and abs(row["target_innovation_variance"] - NOISE**2)
            < variance_relative_tolerance * NOISE**2
            and abs(row["state_innovation_variance"] - NOISE**2)
            < variance_relative_tolerance * NOISE**2
            and abs(row["target_innovation_90pct_coverage"] - 0.9) < coverage_tolerance
            and abs(row["target_state_innovation_correlation"]) < correlation_tolerance
        )
    return {
        "description": "Five-seed Monte Carlo checks of the stable performative process against its analytic stationary Gaussian state and independent target/state innovations.",
        "parameters": {
            "n": N,
            "burn_in": BURN_IN,
            "rho": RHO,
            "strength": STRENGTH,
            "noise": NOISE,
            "joint_actions": ACTIONS.tolist(),
            "mean_action": action_mean,
            "expected_stationary_state_mean": expected_state_mean,
            "expected_stationary_state_variance": expected_state_variance,
            "expected_innovation_variance": NOISE**2,
        },
        "tolerances": {
            "target_and_state_innovation_mean": mean_tolerance,
            "innovation_variance_relative": variance_relative_tolerance,
            "state_variance_relative": state_variance_relative_tolerance,
            "90pct_coverage_absolute": coverage_tolerance,
            "innovation_correlation_absolute": correlation_tolerance,
        },
        "replicates": rows,
        "checks_pass": all(row["passes"] for row in rows),
        "interpretation": "Synthetic controlled process validation; action effects are imposed and are not evidence about real-world performative systems.",
        "processing_commit": commit(),
        "source_hash": source_hash(),
        "script_sha256": sha256(Path(__file__)),
        "executed_at": utc_now(),
    }


def main() -> None:
    report = evaluate()
    output = Path("data/reports/performative_validation.json")
    write_json(output, report)
    print(
        f"replicates={len(report['replicates'])} failures={sum(not row['passes'] for row in report['replicates'])}"
    )
    print(output)
    if not report["checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
