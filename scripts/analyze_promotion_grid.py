"""Summarize a completed promotion-grid run using independent streams as units."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm, t


def _mean_t_interval(values: np.ndarray) -> tuple[float, float, float]:
    values = np.asarray(values, dtype=float)
    mean = float(values.mean())
    if len(values) < 2:
        return mean, mean, mean
    half_width = float(t.ppf(0.975, len(values) - 1) * values.std(ddof=1) / np.sqrt(len(values)))
    return mean, mean - half_width, mean + half_width


def _wilson(successes: int, total: int) -> tuple[float, float]:
    if total < 1 or not 0 <= successes <= total:
        raise ValueError("Wilson interval needs 0 <= successes <= positive total")
    z = float(norm.ppf(0.975))
    rate = successes / total
    denominator = 1 + z**2 / total
    center = (rate + z**2 / (2 * total)) / denominator
    radius = z * np.sqrt(rate * (1 - rate) / total + z**2 / (4 * total**2)) / denominator
    return max(0.0, center - radius), min(1.0, center + radius)


def summarize(input_dir: Path, output_path: Path) -> Path:
    frame = pd.read_parquet(input_dir / "metrics/promotion_grid_strategies.parquet")
    required = {
        "scenario",
        "seed",
        "strategy",
        "promoted",
        "post_expected_net_gain_total",
        "post_realized_net_gain_total",
        "false_promotion_post_nongain",
    }
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"strategy metrics are missing columns: {sorted(missing)}")

    lines = [
        "# Promotion-grid uncertainty analysis",
        "",
        "The independent simulation stream (seed) is the replication unit. Mean intervals are two-sided 95% Student-t intervals across seeds; rate intervals are 95% Wilson intervals. These are descriptive intervals and are not adjusted for selecting among scenarios or strategies.",
        "",
        "| Scenario | Strategy | Promotion rate (Wilson 95% CI) | Expected net gain (t 95% CI) | Realized net gain (t 95% CI) | Post-deployment nongain (Wilson 95% CI) |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for (scenario, strategy), group in frame.groupby(["scenario", "strategy"], sort=True):
        n = group.seed.nunique()
        if n != len(group):
            raise ValueError(f"duplicate stream rows for {scenario}/{strategy}")
        promotion_count = int(group.promoted.sum())
        promotion_ci = _wilson(promotion_count, n)
        expected = _mean_t_interval(group.post_expected_net_gain_total.to_numpy())
        realized = _mean_t_interval(group.post_realized_net_gain_total.to_numpy())
        nongain_count = int(group.false_promotion_post_nongain.sum())
        nongain_ci = _wilson(nongain_count, n)
        lines.append(
            f"| {scenario} | {strategy} | {promotion_count}/{n} "
            f"[{promotion_ci[0]:.3f}, {promotion_ci[1]:.3f}] | "
            f"{expected[0]:.3f} [{expected[1]:.3f}, {expected[2]:.3f}] | "
            f"{realized[0]:.3f} [{realized[1]:.3f}, {realized[2]:.3f}] | "
            f"{nongain_count}/{n} [{nongain_ci[0]:.3f}, {nongain_ci[1]:.3f}] |"
        )

    lines.extend(
        [
            "",
            "## Paired policy differences",
            "",
            "Expected deployment net-gain differences are paired by scenario and seed. Positive sequential-minus-always values favor sequential certification. Intervals are unadjusted 95% Student-t intervals.",
            "",
            "| Scenario | Comparison | Mean paired difference (95% CI) |",
            "|---|---|---:|",
        ]
    )
    for scenario, scenario_frame in frame.groupby("scenario", sort=True):
        indexed = scenario_frame.set_index(["seed", "strategy"])
        for left, right, label in [
            ("sequential_grid_gate", "never_promote", "sequential − never"),
            ("sequential_grid_gate", "validation_always_promote", "sequential − always"),
        ]:
            left_values = indexed.xs(left, level="strategy").post_expected_net_gain_total
            right_values = indexed.xs(right, level="strategy").post_expected_net_gain_total
            joined = pd.concat([left_values, right_values], axis=1, join="inner").dropna()
            difference = _mean_t_interval((joined.iloc[:, 0] - joined.iloc[:, 1]).to_numpy())
            lines.append(
                f"| {scenario} | {label} | {difference[0]:.3f} "
                f"[{difference[1]:.3f}, {difference[2]:.3f}] |"
            )

    lines.extend(
        [
            "",
            "The certificate's shadow-period statistical guarantee does not guarantee later deployment benefit. `false_promotion_post_nongain` is an out-of-period reversal diagnostic, not a test type-I error. See `promotion_grid_comparison.md` for the experiment protocol and assumptions.",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("outputs/promotion_grid_corrected"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/promotion_grid_corrected/reports/strategy_uncertainty.md"),
    )
    args = parser.parse_args()
    print(summarize(args.input, args.output))


if __name__ == "__main__":
    main()
