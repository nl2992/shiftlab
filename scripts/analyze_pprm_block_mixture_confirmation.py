"""Analyze a pre-fixed 10% PPRM mixture on an independent seed block."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy.stats import binomtest

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HARM_SCENARIOS = ("boundary_local_harm", "recurring_regimes", "harmful_adaptation")
EXPLORATORY_HARM_SCENARIOS = ("residual_variance",)
CONTROL_SCENARIOS = ("stationary", "benign_nuisance")
PLOT_HARM_SCENARIOS = (*HARM_SCENARIOS, *EXPLORATORY_HARM_SCENARIOS)
METHODS = ("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive")
MIXTURE_COLUMN = "pprm_mix_w0p1_detected"
MIXTURE_FALSE_COLUMN = "pprm_mix_w0p1_false_escalation"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paired_rows(frame: pd.DataFrame, scenario: str) -> pd.DataFrame:
    subset = frame.loc[frame.scenario.eq(scenario)]
    if set(subset.method.unique()) != set(METHODS):
        raise ValueError(f"{scenario}: expected exactly {METHODS}, got {subset.method.unique()}")
    wide = subset.pivot(index="seed", columns="method", values="single_e_detected")
    pprm = subset.loc[subset.method.eq("pprm_block_adaptive")].set_index("seed")
    wide["mixture_w0p1"] = pprm[MIXTURE_COLUMN].astype(bool)
    wide["mixture_w0p1_false"] = pprm[MIXTURE_FALSE_COLUMN].astype(bool)
    wide["pprm_false"] = pprm["single_e_false_escalation"].astype(bool)
    if wide.isna().any().any():
        raise ValueError(f"{scenario}: incomplete paired seed rows")
    return wide.sort_index()


def _paired_summary(candidate: np.ndarray, comparator: np.ndarray) -> dict[str, float | int]:
    candidate, comparator = candidate.astype(bool), comparator.astype(bool)
    candidate_only = int(np.sum(candidate & ~comparator))
    comparator_only = int(np.sum(~candidate & comparator))
    discordant = candidate_only + comparator_only
    p_value = float(binomtest(candidate_only, discordant).pvalue) if discordant else 1.0
    rng = np.random.default_rng(20373001)
    draws = rng.integers(0, len(candidate), size=(20_000, len(candidate)))
    paired_differences = (
        candidate[draws].astype(np.int8) - comparator[draws].astype(np.int8)
    ).mean(axis=1)
    return {
        "streams": len(candidate),
        "mixture_detections": int(candidate.sum()),
        "mixture_rate": float(candidate.mean()),
        "comparator_detections": int(comparator.sum()),
        "comparator_rate": float(comparator.mean()),
        "mixture_only": candidate_only,
        "comparator_only": comparator_only,
        "rate_difference_mixture_minus_comparator": float(candidate.mean() - comparator.mean()),
        "difference_bootstrap_95_low": float(np.quantile(paired_differences, 0.025)),
        "difference_bootstrap_95_high": float(np.quantile(paired_differences, 0.975)),
        "mcnemar_exact_p": p_value,
    }


def _holm(p_values: list[float]) -> list[float]:
    order = np.argsort(p_values)
    adjusted = np.empty(len(p_values), dtype=float)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, (len(p_values) - rank) * p_values[index])
        adjusted[index] = min(1.0, running)
    return adjusted.tolist()


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials == 0:
        return float("nan"), float("nan")
    p = successes / trials
    denominator = 1 + z * z / trials
    center = (p + z * z / (2 * trials)) / denominator
    radius = z * np.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    lower = 0.0 if successes == 0 else max(0.0, center - radius)
    upper = 1.0 if successes == trials else min(1.0, center + radius)
    return float(lower), float(upper)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir", type=Path, default=Path("outputs/pprm_block_mixture_independent_v1/block_20")
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/pprm_block_mixture_independent_v1/analysis"),
    )
    parser.add_argument("--expected-seeds", type=int, default=200)
    parser.add_argument("--expected-seed-offset", type=int, default=20373000)
    args = parser.parse_args()

    metrics_path = args.run_dir / "metrics" / "hard_budget_comparison.parquet"
    frame = pd.read_parquet(metrics_path)
    manifest_path = args.run_dir / "reports" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    config = manifest["configuration"]
    for relative_path, expected_hash in manifest["sha256"]["artifacts"].items():
        artifact = args.run_dir / Path(relative_path)
        if not artifact.is_file() or _sha256(artifact) != expected_hash:
            raise ValueError(f"run artifact hash mismatch: {artifact}")
    if len(frame.seed.unique()) != args.expected_seeds:
        raise ValueError("unexpected number of independent seeds")
    seeds = sorted(frame.seed.unique())
    expected_seeds = list(
        range(args.expected_seed_offset, args.expected_seed_offset + args.expected_seeds)
    )
    if seeds != expected_seeds:
        raise ValueError("seed block does not match the predeclared independent range")
    pprm = frame.loc[frame.method.eq("pprm_block_adaptive")]
    if not pprm.pprm_max_reliance.eq(0.1).all():
        raise ValueError("reliance cap changed from the predeclared value")
    expected_config = {
        "n": 6400,
        "d": 16,
        "seeds": args.expected_seeds,
        "seed_offset": args.expected_seed_offset,
        "budget_rate": 0.2,
        "q_min": 0.1,
        "q_max": 0.8,
        "common_eprocess_bound": True,
        "pprm_block_size": 20,
        "pprm_labels_per_block": 4,
        "pprm_max_reliance": 0.1,
        "pprm_initial_reliance": 0.1,
        "device": "cuda",
        "scenario_subset": [
            "stationary",
            "benign_nuisance",
            "boundary_local_harm",
            "residual_variance",
            "recurring_regimes",
            "harmful_adaptation",
        ],
        "method_subset": list(METHODS),
    }
    for key, expected in expected_config.items():
        if config.get(key) != expected:
            raise ValueError(f"manifest configuration mismatch for {key}: {config.get(key)!r}")
    if not frame.budget_respected.astype(bool).all():
        raise ValueError("at least one method exceeded the realized hard label budget")

    primary_rows: list[dict[str, object]] = []
    for scenario in HARM_SCENARIOS:
        wide = _paired_rows(frame, scenario)
        pprm_rows = frame.loc[
            frame.scenario.eq(scenario) & frame.method.eq("pprm_block_adaptive")
        ].set_index("seed")
        if not pprm_rows.material_harm.astype(bool).all():
            raise ValueError(f"{scenario}: expected every stream to be materially harmful")
        if not pprm_rows.harm_reached_before_budget_stop.astype(bool).all():
            raise ValueError(f"{scenario}: a material-harm onset was not reached")
        for comparator in ("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"):
            baseline = (
                wide[comparator].astype(bool).to_numpy()
                if comparator != "pprm_block_adaptive"
                else pprm_rows.single_e_detected.astype(bool).to_numpy()
            )
            primary_rows.append(
                {
                    "scenario": scenario,
                    "comparator": comparator,
                    **_paired_summary(wide.mixture_w0p1.to_numpy(), baseline),
                }
            )
    primary = pd.DataFrame(primary_rows)
    mask = primary.comparator.eq("uniform_proxy")
    primary.loc[mask, "holm_adjusted_p"] = _holm(primary.loc[mask, "mcnemar_exact_p"].tolist())
    primary.loc[~mask, "holm_adjusted_p"] = np.nan

    exploratory_rows = []
    for scenario in EXPLORATORY_HARM_SCENARIOS:
        wide = _paired_rows(frame, scenario)
        block_rows = frame.loc[
            frame.scenario.eq(scenario) & frame.method.eq("pprm_block_adaptive")
        ].set_index("seed")
        if not block_rows.material_harm.astype(bool).all():
            raise ValueError(f"{scenario}: evaluator metadata does not mark all streams harmful")
        if not block_rows.harm_reached_before_budget_stop.astype(bool).all():
            raise ValueError(f"{scenario}: a material-harm onset was not reached")
        for comparator in ("uniform_proxy", "uniform_proxy_frozen", "pprm_block_adaptive"):
            baseline = (
                wide[comparator].astype(bool).to_numpy()
                if comparator != "pprm_block_adaptive"
                else block_rows.single_e_detected.astype(bool).to_numpy()
            )
            exploratory_rows.append(
                {
                    "scenario": scenario,
                    "comparator": comparator,
                    **_paired_summary(wide.mixture_w0p1.to_numpy(), baseline),
                }
            )

    control_rows = []
    for scenario in CONTROL_SCENARIOS:
        _paired_rows(frame, scenario)
        subset = frame.loc[frame.scenario.eq(scenario)]
        monitor_columns = (
            ("fixed_mixture_w0p1", "pprm_block_adaptive", MIXTURE_FALSE_COLUMN),
            ("cm_eb", "pprm_block_adaptive", "single_e_false_escalation"),
            ("eventwise_updating", "uniform_proxy", "single_e_false_escalation"),
            ("eventwise_frozen", "uniform_proxy_frozen", "single_e_false_escalation"),
        )
        for name, method, column in monitor_columns:
            monitor_rows = subset.loc[subset.method.eq(method)]
            count, n = int(monitor_rows[column].astype(bool).sum()), len(monitor_rows)
            low, high = _wilson(count, n)
            control_rows.append(
                {
                    "scenario": scenario,
                    "monitor": name,
                    "streams": n,
                    "false_escalations": count,
                    "rate": count / n,
                    "wilson_95_low": low,
                    "wilson_95_high": high,
                }
            )

    cost_rows = []
    for scenario in (*HARM_SCENARIOS, *EXPLORATORY_HARM_SCENARIOS, *CONTROL_SCENARIOS):
        subset = frame.loc[frame.scenario.eq(scenario)]
        for method, group in subset.groupby("method"):
            error = group.stream_mean_estimation_error.to_numpy(dtype=float)
            cost_rows.append(
                {
                    "scenario": scenario,
                    "method": method,
                    "streams": group.seed.nunique(),
                    "stream_mean_rmse": float(np.sqrt(np.mean(error**2))),
                    "mean_label_spend": float(group.realized_label_spend.mean()),
                    "mean_labels_queried": float(group.labels_queried.mean()),
                }
            )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    primary.to_csv(args.output_dir / "primary_detection_comparisons.csv", index=False)
    exploratory = pd.DataFrame(exploratory_rows)
    exploratory.to_csv(args.output_dir / "exploratory_residual_variance_harm.csv", index=False)
    pd.DataFrame(control_rows).to_csv(
        args.output_dir / "null_control_false_escalations.csv", index=False
    )
    pd.DataFrame(cost_rows).to_csv(args.output_dir / "estimation_and_costs.csv", index=False)
    colors = {
        "fixed 10% mixture": "#4472C4",
        "eventwise updating": "#ED7D31",
        "eventwise frozen": "#70AD47",
        "block CM-EB": "#A5A5A5",
    }
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    x = np.arange(len(PLOT_HARM_SCENARIOS))
    series = {
        "fixed 10% mixture": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("pprm_block_adaptive"), MIXTURE_COLUMN
            ]
            .astype(bool)
            .mean()
            for s in PLOT_HARM_SCENARIOS
        ],
        "eventwise updating": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("uniform_proxy"), "single_e_detected"
            ]
            .astype(bool)
            .mean()
            for s in PLOT_HARM_SCENARIOS
        ],
        "eventwise frozen": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("uniform_proxy_frozen"),
                "single_e_detected",
            ]
            .astype(bool)
            .mean()
            for s in PLOT_HARM_SCENARIOS
        ],
        "block CM-EB": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("pprm_block_adaptive"), "single_e_detected"
            ]
            .astype(bool)
            .mean()
            for s in PLOT_HARM_SCENARIOS
        ],
    }
    width = 0.19
    for index, (name, rates) in enumerate(series.items()):
        axes[0].bar(x + (index - 1.5) * width, rates, width, label=name, color=colors[name])
    axes[0].set_xticks(
        x, ["Boundary-local", "Recurring", "Harmful adaptation", "Residual variance*"]
    )
    axes[0].set_ylim(0, 1.05)
    axes[0].set_ylabel("Fraction of streams detecting harm")
    axes[0].set_title("Harm detection (200 matched streams per scenario)")
    axes[0].legend(frameon=False, fontsize=8)
    control_series = {
        "fixed 10% mixture": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("pprm_block_adaptive"),
                MIXTURE_FALSE_COLUMN,
            ]
            .astype(bool)
            .mean()
            for s in CONTROL_SCENARIOS
        ],
        "eventwise updating": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("uniform_proxy"),
                "single_e_false_escalation",
            ]
            .astype(bool)
            .mean()
            for s in CONTROL_SCENARIOS
        ],
        "eventwise frozen": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("uniform_proxy_frozen"),
                "single_e_false_escalation",
            ]
            .astype(bool)
            .mean()
            for s in CONTROL_SCENARIOS
        ],
        "block CM-EB": [
            frame.loc[
                (frame.scenario.eq(s)) & frame.method.eq("pprm_block_adaptive"),
                "single_e_false_escalation",
            ]
            .astype(bool)
            .mean()
            for s in CONTROL_SCENARIOS
        ],
    }
    x_control = np.arange(len(CONTROL_SCENARIOS))
    for index, (name, rates) in enumerate(control_series.items()):
        positions = x_control + (index - 1.5) * width
        axes[1].bar(positions, rates, width, label=name, color=colors[name])
        axes[1].errorbar(
            positions,
            rates,
            yerr=[np.zeros(len(rates)), np.full(len(rates), _wilson(0, args.expected_seeds)[1])],
            fmt="o",
            color=colors[name],
            capsize=2,
            markersize=3,
            linewidth=1,
        )
    axes[1].set_xticks(x_control, ["Stationary", "Benign nuisance"])
    axes[1].set_ylim(0, 0.025)
    axes[1].set_ylabel("False-escalation fraction")
    axes[1].set_title("False escalations: 0/200 each; dots show Wilson upper limits")
    figure.savefig(args.output_dir / "independent_mixture_detection.png", dpi=180)
    plt.close(figure)
    lines = [
        "# Independent fixed-mixture validation",
        "",
        "This evaluates the development-selected 10% CM-EB / positive-betting mixture on a fresh seed block. The mixture weight, horizon, block size, reliance cap, scenarios, and seed range were fixed before these streams. This tests the selected candidate; it is not an algorithm discovery experiment.",
        "",
        f"- Streams per scenario: {args.expected_seeds}",
        f"- Seed range: {seeds[0]}–{seeds[-1]}",
        f"- Configuration manifest: {manifest_path.as_posix()}",
        "- Primary endpoint: stream-level harm detection. Exact paired McNemar tests compare the fixed mixture with eventwise updating PPI in three harm scenarios, with Holm adjustment.",
        "- Population-null controls: stationary and benign nuisance. False escalations have Wilson intervals.",
        "- The monitor is not a candidate-promotion certificate. Validity remains conditional on the documented boundedness, predictability, and feedback assumptions.",
        "",
        "## Primary detection results",
        "",
        "| Scenario | Mixture | Eventwise updating PPI | Difference (paired bootstrap 95% CI) | Discordant (mixture only / eventwise only) | Exact p | Holm p |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in primary.loc[primary.comparator.eq("uniform_proxy")].itertuples(index=False):
        lines.append(
            f"| {row.scenario} | {row.mixture_rate:.3f} | {row.comparator_rate:.3f} | {row.rate_difference_mixture_minus_comparator:+.3f} [{row.difference_bootstrap_95_low:+.3f}, {row.difference_bootstrap_95_high:+.3f}] | {row.mixture_only} / {row.comparator_only} | {row.mcnemar_exact_p:.4g} | {row.holm_adjusted_p:.4g} |"
        )
    lines += [
        "",
        "## Exploratory residual-variance harm (reclassified after metadata audit)",
        "",
        "The scenario documentation calls this a residual-variance shift, but the evaluator's population-harm metadata marks all streams as materially harmful and provides a harm onset. It was mistakenly described as a null control in the initial protocol. These results are excluded from the three-scenario primary multiplicity family and are shown descriptively only.",
        "",
        "| Monitor | Harm detections / streams | Rate |",
        "|---|---:|---:|",
    ]
    labels = {
        "uniform_proxy": "eventwise updating PPI",
        "uniform_proxy_frozen": "eventwise frozen PPI",
        "pprm_block_adaptive": "block CM-EB",
    }
    for row in exploratory.itertuples(index=False):
        lines.append(
            f"| {labels[row.comparator]} | {row.comparator_detections} / {row.streams} | {row.comparator_rate:.3f} |"
        )
    mixture_count = int(
        frame.loc[
            frame.scenario.eq("residual_variance") & frame.method.eq("pprm_block_adaptive"),
            MIXTURE_COLUMN,
        ]
        .astype(bool)
        .sum()
    )
    lines.append(
        f"| fixed 10% mixture | {mixture_count} / {args.expected_seeds} | {mixture_count / args.expected_seeds:.3f} |"
    )
    lines += [
        "",
        "## Control false escalations",
        "",
        "| Scenario | Monitor | Errors / streams | Rate | Wilson 95% interval |",
        "|---|---|---:|---:|---:|",
    ]
    for row in control_rows:
        lines.append(
            f"| {row['scenario']} | {row['monitor']} | {row['false_escalations']} / {row['streams']} | {row['rate']:.3f} | [{row['wilson_95_low']:.3f}, {row['wilson_95_high']:.3f}] |"
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "These results assess one fixed candidate and registered synthetic designs. They do not establish error control under arbitrary serial dependence, adaptive label selection, delayed feedback, or real-world shift. Interpret them as evidence for the declared generator and feedback protocol only.",
        "",
    ]
    (args.output_dir / "independent_mixture_validation.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    protocol_path = Path("docs/pprm_block_mixture_confirmation_protocol.md")
    analysis_outputs = (
        "primary_detection_comparisons.csv",
        "exploratory_residual_variance_harm.csv",
        "null_control_false_escalations.csv",
        "estimation_and_costs.csv",
        "independent_mixture_validation.md",
        "independent_mixture_detection.png",
    )
    analysis_manifest = {
        "analysis": "independent_fixed_pprm_block_mixture_validation",
        "candidate_mixture_weight": 0.1,
        "seed_range": [int(seeds[0]), int(seeds[-1])],
        "run_manifest_sha256": _sha256(manifest_path),
        "input_metrics_sha256": _sha256(metrics_path),
        "protocol_sha256": _sha256(protocol_path),
        "analysis_script_sha256": _sha256(Path(__file__)),
        "outputs_sha256": {name: _sha256(args.output_dir / name) for name in analysis_outputs},
    }
    (args.output_dir / "analysis_manifest.json").write_text(
        json.dumps(analysis_manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(args.output_dir / "independent_mixture_validation.md")


if __name__ == "__main__":
    main()
