"""Calibrate an independent OPI implementation on stationary logged bandits.

Synthetic-only benchmark of bounded DR pseudo-outcomes and Molitor's finite
policy elimination rule. PyTorch generates streams on CUDA when available;
confidence-sequence inversion is evaluated with the independent NumPy module.
"""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import torch
from scipy.stats import beta

from shiftlab.dive.anytime_policy_identification import (
    bounded_dr_pseudo_outcomes,
    lil_value_bounds,
    optimal_policy_set,
    optimal_policy_stopping_time,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/shiftguard_unified/sota_reproductions/molitor_opi_calibration_v1"
ALPHA = 0.05
N_SEEDS = 1_000
HORIZON = 2_000
TRUNCATION = 1.0
POLICY_TREATMENT_PROBABILITIES = np.array([0.0, 0.5, 1.0])
METHODS = {
    "familywise_two_tail": ALPHA / (2.0 * len(POLICY_TREATMENT_PROBABILITIES)),
    # The author simulations use alpha/m for each one-sided bound. This row is
    # a multiplicity-only diagnostic, not a reproduction of their full code.
    "source_style_alpha_over_m_each_tail": ALPHA / len(POLICY_TREATMENT_PROBABILITIES),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def binomial_interval(events: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    tail = (1.0 - confidence) / 2.0
    lower = 0.0 if events == 0 else float(beta.ppf(tail, events, trials - events + 1))
    upper = 1.0 if events == trials else float(beta.ppf(1.0 - tail, events + 1, trials - events))
    return lower, upper


def generate_streams(
    *,
    device: torch.device,
    seed: int,
    mu_zero: float,
    mu_one: float,
) -> tuple[torch.Tensor, torch.Tensor]:
    generator = torch.Generator(device=device)
    generator.manual_seed(seed)
    shape = (N_SEEDS, HORIZON)
    actions = torch.bernoulli(
        torch.full(shape, 0.5, dtype=torch.float32, device=device),
        generator=generator,
    ).to(torch.int64)
    uniforms = torch.rand(shape, dtype=torch.float32, device=device, generator=generator)
    conditional_mean = torch.where(actions == 1, mu_one, mu_zero)
    rewards = (uniforms < conditional_mean).to(torch.float32)
    return actions, rewards


def evaluate_stream(
    actions: np.ndarray,
    rewards: np.ndarray,
    *,
    one_sided_alpha: float,
    optimal_indices: np.ndarray,
) -> dict[str, int | float | bool]:
    n = len(actions)
    h = np.full((n, 2), 0.5, dtype=np.float64)
    policies = np.stack(
        [1.0 - POLICY_TREATMENT_PROBABILITIES, POLICY_TREATMENT_PROBABILITIES],
        axis=-1,
    )
    # Constant reward prediction is fixed before the stream and predictable.
    rhat = np.full((n, 2), 0.5, dtype=np.float64)
    lower_phi, upper_phi = bounded_dr_pseudo_outcomes(
        actions=actions,
        rewards=rewards,
        logging_probabilities=h,
        target_policies=policies,
        reward_predictions=rhat,
        truncation=TRUNCATION,
    )
    lower = np.stack(
        [lil_value_bounds(lower_phi[:, i], one_sided_alpha, TRUNCATION) for i in range(3)]
    )
    upper = np.stack(
        [1.0 - lil_value_bounds(upper_phi[:, i], one_sided_alpha, TRUNCATION) for i in range(3)]
    )
    candidate_set = optimal_policy_set(lower, upper)
    stopping_time = optimal_policy_stopping_time(lower, upper)
    retained = bool(candidate_set[optimal_indices].all())
    final_size = int(candidate_set[:, -1].sum())
    unique_identified = bool(stopping_time <= HORIZON)
    correct_at_horizon = bool(
        len(optimal_indices) == 1 and final_size == 1 and candidate_set[int(optimal_indices[0]), -1]
    )
    return {
        "false_optimal_elimination": not retained,
        "unique_policy_stopped": unique_identified,
        "correct_identification_at_horizon": correct_at_horizon,
        "stopping_time_censored": min(stopping_time, HORIZON + 1),
        "final_candidate_set_size": final_size,
    }


def run_scenario(
    name: str,
    *,
    mu_zero: float,
    mu_one: float,
    seed_base: int,
    device: torch.device,
) -> list[dict[str, object]]:
    actions_gpu, rewards_gpu = generate_streams(
        device=device,
        seed=seed_base,
        mu_zero=mu_zero,
        mu_one=mu_one,
    )
    actions_cpu = actions_gpu.cpu().numpy()
    rewards_cpu = rewards_gpu.cpu().numpy().astype(np.float64)
    true_values = (
        1.0 - POLICY_TREATMENT_PROBABILITIES
    ) * mu_zero + POLICY_TREATMENT_PROBABILITIES * mu_one
    optimal_indices = np.flatnonzero(true_values == true_values.max())

    rows: list[dict[str, object]] = []
    for seed_index, (actions, rewards) in enumerate(zip(actions_cpu, rewards_cpu, strict=True)):
        for allocation, one_sided_alpha in METHODS.items():
            result = evaluate_stream(
                actions,
                rewards,
                one_sided_alpha=one_sided_alpha,
                optimal_indices=optimal_indices,
            )
            rows.append(
                {
                    "scenario": name,
                    "replication_id": seed_index,
                    "allocation": allocation,
                    "one_sided_alpha": one_sided_alpha,
                    "mu_action_0": mu_zero,
                    "mu_action_1": mu_one,
                    "true_policy_values": json.dumps(true_values.tolist()),
                    **result,
                }
            )
    return rows


def summarize(metrics: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (scenario, allocation), group in metrics.groupby(["scenario", "allocation"], sort=True):
        n = len(group)
        events = int(group["false_optimal_elimination"].sum())
        lo, hi = binomial_interval(events, n)
        stop_events = int(group["unique_policy_stopped"].sum())
        stop_lo, stop_hi = binomial_interval(stop_events, n)
        rows.append(
            {
                "scenario": scenario,
                "allocation": allocation,
                "streams": n,
                "false_optimal_eliminations": events,
                "false_elimination_rate": events / n,
                "false_elimination_ci95_low": lo,
                "false_elimination_ci95_high": hi,
                "unique_stops": stop_events,
                "unique_stop_rate": stop_events / n,
                "unique_stop_ci95_low": stop_lo,
                "unique_stop_ci95_high": stop_hi,
                "correct_identifications_at_horizon": int(
                    group["correct_identification_at_horizon"].sum()
                ),
                "correct_identification_rate": float(
                    group["correct_identification_at_horizon"].mean()
                ),
                "mean_censored_stopping_time": float(group["stopping_time_censored"].mean()),
                "horizon": HORIZON,
                "nominal_alpha": ALPHA,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    run_started = datetime.now(UTC).isoformat()
    rows = run_scenario(
        "all_policies_tied_null",
        mu_zero=0.55,
        mu_one=0.55,
        seed_base=10_000,
        device=device,
    )
    rows.extend(
        run_scenario(
            "unique_best_action_1",
            mu_zero=0.40,
            mu_one=0.70,
            seed_base=20_000,
            device=device,
        )
    )
    metrics = pd.DataFrame(rows)
    summary = summarize(metrics)
    metrics_path = OUTPUT / "per_stream_metrics.parquet"
    summary_path = OUTPUT / "summary.parquet"
    metrics.to_parquet(metrics_path, index=False)
    summary.to_parquet(summary_path, index=False)
    metrics.to_csv(OUTPUT / "per_stream_metrics.csv", index=False)
    summary.to_csv(OUTPUT / "summary.csv", index=False)

    module_path = ROOT / "src/shiftlab/dive/anytime_policy_identification.py"
    script_path = Path(__file__).resolve()
    manifest = {
        "experiment": "molitor_opi_stationary_logged_bandit_calibration_v1",
        "status": "complete",
        "run_started_utc": run_started,
        "run_finished_utc": datetime.now(UTC).isoformat(),
        "source_commit": "6385218f57aaf5a2ad3d9bd02145c6c3125fd593",
        "implementation": "independent ShiftLab implementation of published OPI and LIL formulas",
        "alpha": ALPHA,
        "seeds_per_scenario": N_SEEDS,
        "horizon": HORIZON,
        "policy_treatment_probabilities": POLICY_TREATMENT_PROBABILITIES.tolist(),
        "logger_action_probabilities": [0.5, 0.5],
        "reward_model": "fixed predictable rhat(x,a)=0.5",
        "truncation": TRUNCATION,
        "error_allocations": METHODS,
        "scenarios": {
            "all_policies_tied_null": {"mu_action_0": 0.55, "mu_action_1": 0.55},
            "unique_best_action_1": {"mu_action_0": 0.40, "mu_action_1": 0.70},
        },
        "learner_information": [
            "past logged events",
            "current action and known logger probabilities",
            "fixed candidate class",
        ],
        "evaluator_only": ["true reward means", "true best policy", "potential reward law"],
        "limitations": [
            "stationary two-action synthetic contextual-bandit special case; no contexts",
            "Bernoulli rewards, fixed logger and fixed predictable reward model",
            "source-style alpha/m-per-tail condition is a multiplicity-only diagnostic, not a full author-code reproduction",
            "synthetic calibration does not qualify OBD real-data assumptions",
        ],
        "device": str(device),
        "gpu_name": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "torch_version": torch.__version__,
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scipy_version": scipy.__version__,
        "python_version": platform.python_version(),
        "run_seeds": {"all_policies_tied_null": 10_000, "unique_best_action_1": 20_000},
        "source_sha256": {
            str(script_path.relative_to(ROOT)): sha256(script_path),
            str(module_path.relative_to(ROOT)): sha256(module_path),
        },
        "output_sha256": {
            metrics_path.name: sha256(metrics_path),
            summary_path.name: sha256(summary_path),
        },
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (OUTPUT / "report.md").write_text(build_report(summary, manifest), encoding="utf-8")
    print(summary.to_string(index=False))
    print("Wrote OPI calibration metrics and manifest.")


def build_report(summary: pd.DataFrame, manifest: dict[str, object]) -> str:
    table = summary.to_markdown(index=False, floatfmt=".4f")
    return f"""# Molitor OPI stationary logged-bandit calibration

**Status:** completed independent synthetic calibration; not a real-data result or reproduction of the paper's full figures.  
**Device:** {manifest["device"]} ({manifest["gpu_name"] or "CPU"}).  
**Design:** {N_SEEDS:,} streams per scenario, horizon {HORIZON:,}, three fixed policies, Bernoulli rewards, logger `h=(0.5, 0.5)`, predictable constant reward model `rhat=0.5`, truncation `k=1`, global nominal `alpha={ALPHA}`.

The null gives all three policies value 0.55. The alternative gives values 0.40, 0.55, and 0.70, making action 1 uniquely optimal. Streams were generated with PyTorch on the recorded device; all policy selection and confidence bounds use the independent NumPy implementation. Evaluator-only reward means and optimal policy are not passed to the learner.

The `familywise_two_tail` row allocates `alpha/(2m)` to each one-sided bound. The `source_style_alpha_over_m_each_tail` row is only a paired multiplicity-allocation diagnostic, reflecting the author simulation's one-sided calls; it is not an execution of their full implementation and its nominal familywise guarantee is at most `2 alpha` by a direct union bound. Null outcomes are judged by whether any truly optimal policy ever leaves the candidate set. Alternative outcomes include false elimination and unique-best stopping.

## Results

{table}

Monte Carlo confidence intervals are exact 95% Clopper-Pearson intervals. They describe this registered two-action stationary DGP only and do not prove the mathematical guarantee. In particular, the observed null false-elimination rate must be interpreted alongside the theorem and the verified assumptions.

## Reproducibility and limitations

The per-stream and summary tables are in Parquet and CSV; `manifest.json` records seed ranges, source hashes, versions, device and output hashes. The run has no contexts, drift, delayed feedback, intervention cost, or slate structure. It cannot establish OBD eligibility or any ShiftGuard end-to-end advantage. The next benchmark should compare this familywise-correct OPI implementation against matched fixed-horizon and candidate-versus-incumbent methods on an explicitly shared logged-bandit task.
"""


if __name__ == "__main__":
    main()
