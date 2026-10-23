"""Combine paired CUDA cost-stability tolerance runs into a reproducible report."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    0.01: Path("outputs/cost_tolerance_001_30"),
    0.025: Path("outputs/cost_tolerance_0025_exploratory_10"),
    0.05: Path("outputs/cost_stabilized_pilot_30"),
    0.1: Path("outputs/cost_tolerance_01_exploratory_10"),
}
OUTPUT = ROOT / "outputs/cost_tolerance_grid_exploratory"
SCENARIOS = ("stationary", "benign_nuisance", "boundary_local_harm")
SEED_BLOCK = set(range(20_361_022, 20_361_032))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bootstrap_rmse_difference(
    stabilized: np.ndarray, uniform: np.ndarray, *, seed: int
) -> tuple[float, float, float]:
    """Paired stream bootstrap CI for RMSE(stabilized)-RMSE(uniform)."""
    rng = np.random.default_rng(seed)
    n = len(stabilized)
    indices = rng.integers(0, n, size=(20_000, n))
    draws = np.sqrt(np.mean(stabilized[indices] ** 2, axis=1)) - np.sqrt(
        np.mean(uniform[indices] ** 2, axis=1)
    )
    estimate = float(np.sqrt(np.mean(stabilized**2)) - np.sqrt(np.mean(uniform**2)))
    lower, upper = np.quantile(draws, [0.025, 0.975])
    return estimate, float(lower), float(upper)


def main() -> None:
    pieces: list[pd.DataFrame] = []
    input_hashes: dict[str, str] = {}
    for delta, run_dir in RUNS.items():
        manifest_path = ROOT / run_dir / "reports" / "manifest.json"
        metrics_path = ROOT / run_dir / "metrics" / "method_comparison.parquet"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["resolved_device"] == "cuda"
        assert manifest["configuration"]["cost_stability_tolerance"] == delta
        input_hashes[str(manifest_path.relative_to(ROOT))] = sha256(manifest_path)
        input_hashes[str(metrics_path.relative_to(ROOT))] = sha256(metrics_path)
        data = pd.read_parquet(metrics_path)
        data = data.loc[data.seed.isin(SEED_BLOCK)].copy()
        assert set(data.seed.unique()) == SEED_BLOCK
        data["cost_stability_tolerance"] = delta
        pieces.append(data)

    combined = pd.concat(pieces, ignore_index=True)
    rows: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        for delta in RUNS:
            cell = combined.loc[
                combined.scenario.eq(scenario) & combined.cost_stability_tolerance.eq(delta)
            ]
            stable = cell.loc[cell.method.eq("cost_stabilized_proxy")].sort_values("seed")
            uniform = cell.loc[cell.method.eq("uniform_proxy")].sort_values("seed")
            assert len(stable) == len(uniform) == len(SEED_BLOCK)
            assert stable.seed.tolist() == uniform.seed.tolist()
            n_eval = stable.n_stream.to_numpy() - stable.monitor_start.to_numpy()
            realized_drift = (
                np.abs(
                    stable.expected_label_spend.to_numpy()
                    - n_eval * stable.cost_budget_per_event.to_numpy()
                )
                / n_eval
            )
            assert np.all(realized_drift <= delta + 1e-10)
            rmse, rmse_lo, rmse_hi = bootstrap_rmse_difference(
                stable.stream_mean_estimation_error.to_numpy(),
                uniform.stream_mean_estimation_error.to_numpy(),
                seed=711_000 + int(delta * 1_000_000) + SCENARIOS.index(scenario),
            )
            rows.append(
                {
                    "scenario": scenario,
                    "tolerance": delta,
                    "n_seeds": len(SEED_BLOCK),
                    "mix_weight_mean": stable.cost_stability_mix.mean(),
                    "expected_spend_drift_per_event_max": realized_drift.max(),
                    "stable_mean_labels": stable.labels_queried.mean(),
                    "uniform_mean_labels": uniform.labels_queried.mean(),
                    "stable_mean_realized_spend": stable.realized_label_spend.mean(),
                    "uniform_mean_realized_spend": uniform.realized_label_spend.mean(),
                    "stable_rmse_stream_mean": np.sqrt(
                        np.mean(stable.stream_mean_estimation_error.to_numpy() ** 2)
                    ),
                    "uniform_rmse_stream_mean": np.sqrt(
                        np.mean(uniform.stream_mean_estimation_error.to_numpy() ** 2)
                    ),
                    "paired_rmse_difference": rmse,
                    "paired_rmse_ci_low": rmse_lo,
                    "paired_rmse_ci_high": rmse_hi,
                    "stable_detection_rate": stable.single_e_detected.mean(),
                    "uniform_detection_rate": uniform.single_e_detected.mean(),
                    "stable_false_escalation_rate": stable.single_e_false_escalation.mean(),
                    "uniform_false_escalation_rate": uniform.single_e_false_escalation.mean(),
                }
            )

    summary = pd.DataFrame(rows)
    metrics_dir = OUTPUT / "metrics"
    reports_dir = OUTPUT / "reports"
    figures_dir = OUTPUT / "figures"
    for directory in (metrics_dir, reports_dir, figures_dir):
        directory.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(metrics_dir / "tolerance_grid.parquet", index=False)
    summary.to_csv(metrics_dir / "tolerance_summary.csv", index=False)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), constrained_layout=True)
    for scenario in SCENARIOS:
        part = summary.loc[summary.scenario.eq(scenario)].sort_values("tolerance")
        axes[0].plot(
            part.tolerance,
            part.stable_mean_realized_spend - part.uniform_mean_realized_spend,
            marker="o",
            label=scenario,
        )
        axes[1].plot(
            part.tolerance,
            part.paired_rmse_difference,
            marker="o",
            label=scenario,
        )
        axes[1].fill_between(
            part.tolerance,
            part.paired_rmse_ci_low,
            part.paired_rmse_ci_high,
            alpha=0.15,
        )
    axes[0].axhline(0, color="black", linewidth=0.8)
    axes[0].set(
        xlabel="Expected-spend drift tolerance δ", ylabel="Realized spend difference vs uniform"
    )
    axes[1].axhline(0, color="black", linewidth=0.8)
    axes[1].set(
        xlabel="Expected-spend drift tolerance δ", ylabel="Paired stream-mean RMSE difference"
    )
    axes[0].legend(frameon=False)
    axes[1].legend(frameon=False)
    fig.suptitle("Cost-stability tolerance: exploratory paired-seed sweep")
    fig.savefig(figures_dir / "cost_tolerance_tradeoff.png", dpi=180)
    plt.close(fig)

    report = """# Exploratory cost-stability tolerance sweep

This analysis combines CUDA runs at expected-spend drift tolerances δ = 0.01, 0.025, 0.05, and 0.1. It compares the stabilized cost-aware query policy with uniform prediction-powered querying on the same ten streams per scenario (seed IDs 20361022–20361031). The δ=0.01 and δ=0.05 source runs each contain 30 seeds; this report filters both to the same ten-seed block. The 30-seed δ=0.05 pilot is therefore paired with this grid for these ten seeds, and must not be counted as an independent replication.

The RMSE interval is a percentile bootstrap over paired stream seeds (20,000 resamples); it is descriptive at n=10 and is not confirmatory. The expected-spend drift check verifies the implementation of the configured mixture bound on these streams. Realized spend is stochastic and not hard-capped.

|Scenario|δ|Mean spend stabilized|Mean spend uniform|Paired RMSE difference (stabilized − uniform)|95% seed-bootstrap CI|Harm detection stabilized / uniform|Max expected-spend drift / event|
|---|---:|---:|---:|---:|---:|---:|
""" + "\n".join(
        "|{scenario}|{tolerance:.3f}|{stable_mean_realized_spend:.2f}|{uniform_mean_realized_spend:.2f}|{paired_rmse_difference:.4f}|[{paired_rmse_ci_low:.4f}, {paired_rmse_ci_high:.4f}]|{stable_detection_rate:.2f} / {uniform_detection_rate:.2f}|{expected_spend_drift_per_event_max:.5f}|".format(
            **row
        )
        for row in summary.to_dict("records")
    )
    report += """

## Interpretation

This grid assesses a budget-control parameter; it does not test a new monitoring theorem. The configured tolerance bounds expected tariff-weighted spend drift per event under the stated support and feasibility assumptions, while realized totals still vary due to Bernoulli queries. Compare RMSE and harm detection alongside spend: a policy that spends less can lose estimation precision, and small differences at ten seeds should not drive a method choice. The boundary-harm detection rates are especially imprecise at this sample size. No novelty or broad performance claim follows from this exploratory grid.

Reproduce the δ=0.025 and δ=0.1 runs with `uv run shiftlab-dive --seeds 10 --n 3200 --heterogeneous-label-costs --cost-stability-tolerance <delta> --scenarios stationary benign_nuisance boundary_local_harm --methods uniform_proxy cost_stabilized_proxy --device cuda --output outputs/cost_tolerance_<delta>`. The existing δ=0.01 and δ=0.05 runs each used 30 seeds; both are filtered to their shared first ten-seed block for this paired analysis.

![Tolerance tradeoff](../figures/cost_tolerance_tradeoff.png)

"""
    (reports_dir / "tolerance_grid.md").write_text(report, encoding="utf-8")

    artifact_hashes = {
        str(path.relative_to(OUTPUT)): sha256(path)
        for path in sorted(OUTPUT.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    source_path = Path(__file__).resolve()
    manifest = {
        "experiment": "cost_stability_tolerance_sweep",
        "design": {
            "seed_block": sorted(SEED_BLOCK),
            "scenarios": list(SCENARIOS),
            "tolerances": list(RUNS),
            "methods": ["uniform_proxy", "cost_stabilized_proxy"],
            "device": "cuda",
            "n_per_cell": 10,
        },
        "input_sha256": input_hashes,
        "source_sha256": sha256(source_path),
        "artifact_sha256": artifact_hashes,
    }
    (reports_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote tolerance grid to {OUTPUT.relative_to(ROOT)}")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.4f}"))


if __name__ == "__main__":
    main()
